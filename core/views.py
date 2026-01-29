from calendar import month_name, monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import logging
import os
import random
import re

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .models import (
    Adventurer,
    DirectorApplication,
    MonthlyFee,
    PasswordRecovery,
    PixCharge,
    Responsible,
    SEX_CHOICES,
)
from pagamento import criar_pix, consultar_pagamento, extrair_copia_cola, is_aprovado

MONTHLY_FEE_DUE_DAY = 10

WAPI_INSTANCE = os.getenv("WAPI_INSTANCE", "LITE-F75JN4-FWW3NA")
WAPI_TOKEN = os.getenv("WAPI_TOKEN", "o8bWQDnlomrsOaBF2CqnlHguBKIbX87By")
WAPI_URL = os.getenv(
    "WAPI_URL", f"https://api.w-api.app/v1/message/send-text?instanceId={WAPI_INSTANCE}"
)
WAPI_TIMEOUT = int(os.getenv("WAPI_TIMEOUT", "10"))


DAY_OPTIONS = [str(day) for day in range(1, 32)]
MONTHLY_NAMES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

MONTH_OPTIONS = [
    ("1", "Jan"),
    ("2", "Fev"),
    ("3", "Mar"),
    ("4", "Abr"),
    ("5", "Mai"),
    ("6", "Jun"),
    ("7", "Jul"),
    ("8", "Ago"),
    ("9", "Set"),
    ("10", "Out"),
    ("11", "Nov"),
    ("12", "Dez"),
]
YEAR_OPTIONS = [str(year) for year in range(2026, 1979, -1)]

CLASS_OPTIONS = [
    ("abelhinhas", "Abelhinhas"),
    ("luminares", "Luminares"),
    ("edificadores", "Edificadores"),
    ("maos", "Mãos Ajudadoras"),
]

MEDICAL_CONDITIONS = [
    ("catapora", "Catapora"),
    ("meningite", "Meningite"),
    ("hepatite", "Hepatite"),
    ("dengue", "Dengue"),
    ("pneumonia", "Pneumonia"),
    ("malaria", "Malária"),
    ("febre_amarela", "Febre Amarela"),
    ("rubeola", "Rubéola"),
    ("sarampo", "Sarampo"),
    ("tetano", "Tétano"),
    ("variola", "Varíola"),
    ("coqueluche", "Coqueluche"),
    ("difteria", "Difteria"),
    ("caxumba", "Caxumba"),
    ("rinite", "Rinite"),
    ("bronquite", "Bronquite"),
]

BLOOD_TYPES = ["A+", "A-", "AB+", "AB-", "B+", "B-", "O+", "O-", "Não sabe"]

EDUCATION_CHOICES = [
    ("fundamental", "Ensino Fundamental"),
    ("medio", "Ensino Médio"),
    ("faculdade", "Faculdade"),
]

MONTHLY_FEE_DUE_DAY = 10

logger = logging.getLogger(__name__)



def _create_monthly_fees(responsible, adventurer, start_date=None):
    start = start_date or timezone.localdate()
    year = start.year
    for month in range(start.month, 13):
        MonthlyFee.objects.get_or_create(
            responsible=responsible,
            adventurer=adventurer,
            month=month,
            year=year,
            defaults={"amount": Decimal("1.50"), "due_day": MONTHLY_FEE_DUE_DAY},
        )


def _build_finance_periods(fees_qs):
    periods = {}
    for fee in fees_qs:
        key = (fee.year, fee.month)
        if key not in periods:
            day = min(fee.due_day, monthrange(fee.year, fee.month)[1])
            periods[key] = {
                "year": fee.year,
                "month": fee.month,
                "label": f"{MONTHLY_NAMES_PT.get(fee.month, month_name[fee.month])} {fee.year}",
                "due_day": day,
                "items": [],
                "total": Decimal("0.00"),
                "has_pending": False,
                "has_overdue": False,
            }
        period = periods[key]
        period["items"].append(
            {
                "adventurer_name": f"{fee.adventurer.first_name} {fee.adventurer.last_name}",
                "status": fee.status,
                "status_label": fee.get_status_display(),
                "amount": fee.amount,
            }
        )
        period["total"] += fee.amount
        if fee.status == MonthlyFee.PENDING:
            period["has_pending"] = True
            due_date = date(fee.year, fee.month, period["due_day"])
            if due_date < timezone.localdate():
                period["has_overdue"] = True
    ordered = sorted(periods.values(), key=lambda item: (item["year"], item["month"]))
    return ordered


def _attach_pix_charges(periods, responsible):
    if not responsible:
        return
    charges = PixCharge.objects.filter(responsible=responsible)
    charge_map = {(c.year, c.month): c for c in charges}
    for period in periods:
        period["pix_charge"] = charge_map.get((period["year"], period["month"]))


def _clean_phone(phone):
    digits = re.sub(r"\D+", "", phone or "")
    if digits.startswith("0"):
        digits = digits.lstrip("0")
    if not digits.startswith("55"):
        digits = f"55{digits}"
    return digits


def _send_whatsapp_code(phone, code):
    payload = {
        "phone": phone,
        "message": f"Código de recuperação: {code}",
    }
    headers = {
        "Authorization": f"Bearer {WAPI_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(WAPI_URL, json=payload, headers=headers, timeout=WAPI_TIMEOUT)
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        logger.warning(
            "Falha HTTP ao enviar código WhatsApp para %s: %s", phone, detail, exc_info=True
        )
        return False, str(detail or "").strip()
    except requests.RequestException as exc:
        detail = str(exc)
        logger.warning(
            "Erro de requisição ao enviar código WhatsApp para %s: %s",
            phone,
            detail,
            exc_info=True,
        )
        return False, str(detail or "").strip()

    detail = ""
    try:
        data = response.json()
        detail = data.get("message") or data.get("error") or data.get("status") or ""
    except ValueError:
        detail = response.text or ""

    return True, str(detail or "").strip()

def _build_adventurer_records(adventurers_qs):
    records = []
    for adventurer in adventurers_qs:
        birth_date = adventurer.birth_date
        records.append(
            {
                "id": adventurer.id,
                "first_name": adventurer.first_name,
                "last_name": adventurer.last_name,
                "document": adventurer.document,
                "birth_day": str(birth_date.day),
                "birth_month": str(birth_date.month),
                "birth_year": str(birth_date.year),
                "allergies": adventurer.allergies,
                "medication": adventurer.medication,
                "observation": adventurer.observation,
                "emergency_name": adventurer.emergency_name,
                "emergency_phone": adventurer.emergency_phone,
                "emergency_whatsapp": adventurer.emergency_whatsapp,
                "sexo": adventurer.sexo,
                "photo_url": adventurer.photo.url if adventurer.photo else "",
            }
        )
    return records


def login_screen(request):
    """Render the playful login screen and handle authentication."""

    context = {"already_authenticated": request.user.is_authenticated}

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            messages.success(request, "Bem-vindo ao painel!")
            return redirect("dashboard")
        messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "core/login.html", context)


def logout_view(request):
    auth_logout(request)
    messages.info(request, "Sessão encerrada. Faça login novamente.")
    return redirect("login")


@login_required
def update_responsible(request):
    if request.method != "POST":
        return redirect("dashboard")

    if not hasattr(request.user, "responsavel"):
        messages.error(request, "Você precisa ser responsável para editar os dados.")
        return redirect("dashboard")

    responsible = request.user.responsavel
    errors = []
    nome = request.POST.get("responsavel_nome", "").strip()
    sobrenome = request.POST.get("responsavel_sobrenome", "").strip()
    sexo = request.POST.get("responsavel_sexo", "").strip()
    cpf = request.POST.get("responsavel_cpf", "").strip()
    telefone = request.POST.get("responsavel_telefone", "").strip()
    whatsapp = request.POST.get("responsavel_whatsapp", "").strip()
    endereco = request.POST.get("responsavel_endereco", "").strip()
    password1 = request.POST.get("responsavel_password1", "")
    password2 = request.POST.get("responsavel_password2", "")

    if not nome:
        errors.append("Informe o nome do responsável.")
    if not sobrenome:
        errors.append("Informe o sobrenome.")
    if sexo not in dict(SEX_CHOICES):
        errors.append("Informe o sexo do responsável.")
    if not cpf:
        errors.append("Informe o CPF.")
    if not telefone:
        errors.append("Informe o telefone.")
    if not whatsapp:
        errors.append("Informe o WhatsApp.")
    if not endereco:
        errors.append("Informe o endereço.")

    if password1 or password2:
        if password1 != password2:
            errors.append("As senhas não conferem.")
        elif len(password1) != 4 or not password1.isdigit():
            errors.append("A senha precisa ter 4 dígitos numéricos.")

    if errors:
        for err in errors:
            messages.error(request, err)
        return redirect("dashboard")

    user = responsible.user
    user.first_name = nome
    user.last_name = sobrenome
    if password1:
        user.set_password(password1)
    user.save()

    responsible.cpf = cpf
    responsible.telefone = telefone
    responsible.whatsapp = whatsapp
    responsible.endereco = endereco
    responsible.sexo = sexo
    responsible.save()
    messages.success(request, "Dados do responsável atualizados com sucesso.")
    return redirect("dashboard")


@login_required
def update_adventurer(request, pk):
    if request.method != "POST":
        return redirect("dashboard")

    if not hasattr(request.user, "responsavel"):
        messages.error(request, "Você precisa ser responsável para editar aventureiros.")
        return redirect("dashboard")

    adventurer = get_object_or_404(Adventurer, pk=pk, responsible=request.user.responsavel)
    errors = []
    nome = request.POST.get("aventureiro_nome", "").strip()
    sobrenome = request.POST.get("aventureiro_sobrenome", "").strip()
    documento = request.POST.get("aventureiro_documento", "").strip()
    dia = request.POST.get("aventureiro_dia", "").strip()
    mes = request.POST.get("aventureiro_mes", "").strip()
    ano = request.POST.get("aventureiro_ano", "").strip()
    alergias = request.POST.get("aventureiro_alergias", "").strip()
    medicacao = request.POST.get("aventureiro_medicacao", "").strip()
    observacao = request.POST.get("aventureiro_observacao", "").strip()
    emergencia_nome = request.POST.get("emergencia_nome", "").strip()
    emergencia_telefone = request.POST.get("emergencia_telefone", "").strip()
    emergencia_whatsapp = request.POST.get("emergencia_whatsapp", "").strip()
    sexo = request.POST.get("aventureiro_sexo", "").strip()

    for label, value in (
        ("nome do aventureiro", nome),
        ("sobrenome do aventureiro", sobrenome),
        ("documento", documento),
        ("alergias", alergias),
        ("medicação contínua", medicacao),
        ("observações", observacao),
        ("contato de emergência", emergencia_nome),
        ("telefone de emergência", emergencia_telefone),
        ("WhatsApp de emergência", emergencia_whatsapp),
        ("sexo do aventureiro", sexo),
    ):
        if not value:
            errors.append(f"Informe o {label}.")

    if not dia or not mes or not ano:
        errors.append("Informe a data de nascimento completa.")
    else:
        try:
            birth_date = date(int(ano), int(mes), int(dia))
        except (ValueError, TypeError):
            errors.append("Informe uma data de nascimento válida.")
    if errors:
        for err in errors:
            messages.error(request, err)
        return redirect("dashboard")

    if "aventureiro_foto" in request.FILES:
        adventurer.photo = request.FILES["aventureiro_foto"]

    adventurer.first_name = nome
    adventurer.last_name = sobrenome
    adventurer.document = documento
    adventurer.birth_date = birth_date
    adventurer.allergies = alergias
    adventurer.medication = medicacao
    adventurer.observation = observacao
    adventurer.emergency_name = emergencia_nome
    adventurer.emergency_phone = emergencia_telefone
    adventurer.emergency_whatsapp = emergencia_whatsapp
    adventurer.sexo = sexo
    adventurer.save()

    messages.success(request, "Dados do aventureiro atualizados.")
    return redirect("dashboard")


def forgot_password(request):
    error = ""
    success = ""
    error_detail = ""
    if request.method == "POST":
        cpf = request.POST.get("cpf", "").strip()
        try:
            responsible = Responsible.objects.get(cpf=cpf)
        except Responsible.DoesNotExist:
            error = "CPF não encontrado."
        else:
            code = f"{random.randint(0, 9999):04d}"
            recovery = PasswordRecovery.objects.create(
                responsible=responsible,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10),
            )
            phone = _clean_phone(responsible.whatsapp)
            request.session["recovery_id"] = recovery.id
            sent, detail = _send_whatsapp_code(phone, code)
            if sent:
                messages.success(request, "Código enviado pelo WhatsApp.")
                return redirect("verify_code", recovery_id=recovery.id)
            if settings.DEBUG:
                request.session["recovery_debug_code"] = {"id": recovery.id, "code": code}
                messages.success(request, "Código gerado (modo debug).")
                return redirect("verify_code", recovery_id=recovery.id)
            error = "Não foi possível enviar o código via WhatsApp no momento."
            error_detail = detail

    return render(
        request,
        "core/forgot_password.html",
        {"error": error, "success": success, "error_detail": error_detail},
    )


def verify_code(request, recovery_id):
    recovery = get_object_or_404(PasswordRecovery, pk=recovery_id)
    if recovery.used or recovery.is_expired():
        messages.error(request, "Este código expirou ou já foi utilizado.")
        return redirect("forgot_password")

    verified = request.session.get("recovery_verified") == recovery.id
    debug_info = request.session.get("recovery_debug_code")
    debug_code = None
    if debug_info and debug_info.get("id") == recovery.id:
        debug_code = debug_info.get("code")

    if request.method == "POST":
        if "new_password1" in request.POST:
            if not verified:
                messages.error(request, "Confirme o código antes de redefinir.")
                return redirect("verify_code", recovery_id=recovery.id)
            password1 = request.POST.get("new_password1", "")
            password2 = request.POST.get("new_password2", "")
            if not password1 or not password2:
                messages.error(request, "Informe e confirme a nova senha.")
            elif password1 != password2:
                messages.error(request, "As senhas não conferem.")
            elif len(password1) != 4 or not password1.isdigit():
                messages.error(request, "A senha precisa ter 4 dígitos numéricos.")
            else:
                user = recovery.responsible.user
                user.set_password(password1)
                user.save()
                recovery.mark_used()
                request.session.pop("recovery_verified", None)
                messages.success(
                    request,
                    "Senha redefinida com sucesso. Use o código enviado para entrar.",
                )
                return redirect("login")
        else:
            code = request.POST.get("code", "").strip()
            if code != recovery.code:
                messages.error(request, "Código inválido.")
            else:
                request.session["recovery_verified"] = recovery.id
                verified = True
                messages.success(request, "Código confirmado. Agora informe a nova senha.")

    return render(
        request,
        "core/verify_code.html",
        {
            "recovery": recovery,
            "verified": verified,
            "username": recovery.responsible.user.username,
            "debug_code": debug_code,
        },
    )


@login_required
def pay_monthly_fees(request, year, month):
    if request.method != "POST":
        return redirect("dashboard")

    if not hasattr(request.user, "responsavel"):
        messages.error(request, "Você precisa ser responsável para pagar mensalidades.")
        return redirect("dashboard")

    responsible = request.user.responsavel
    fees = MonthlyFee.objects.filter(
        responsible=responsible, year=year, month=month, status=MonthlyFee.PENDING
    )
    if not fees.exists():
        messages.info(request, "Não há mensalidades pendentes para este período.")
        return redirect("dashboard")

    for fee in fees:
        fee.status = MonthlyFee.PAID
        fee.paid_at = timezone.now()
        fee.save()

    messages.success(request, "Mensalidades pagas com sucesso.")
    return redirect("dashboard")


@login_required
def finance_pix(request, year, month):
    if request.GET.get("poll") == "1":
        charge = get_object_or_404(
            PixCharge,
            responsible=request.user.responsavel,
            year=year,
            month=month,
        )
        return JsonResponse(
            {
                "status": charge.status,
                "paid": charge.status == PixCharge.PAID,
                "approved_at": charge.approved_at.isoformat()
                if charge.approved_at
                else "",
            }
        )
    if not hasattr(request.user, "responsavel"):
        messages.error(request, "Você precisa ser responsável para gerar o PIX.")
        return redirect("dashboard")

    responsible = request.user.responsavel
    pending_fees = list(
        MonthlyFee.objects.filter(
            responsible=responsible, year=year, month=month, status=MonthlyFee.PENDING
        )
    )
    if not pending_fees:
        messages.info(request, "Não há mensalidades pendentes nesse período.")
        return redirect("dashboard")

    random_amount = Decimal(random.randint(100, 300)) / Decimal("100")
    random_amount = random_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    amount_centavos = int(
        (random_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    external_reference = f"mensalidades-{responsible.id}-{year}-{month}"
    pix_charge, created = PixCharge.objects.get_or_create(
        responsible=responsible,
        year=year,
        month=month,
        defaults={
            "amount": random_amount,
            "external_reference": external_reference,
        },
    )
    if pix_charge.amount != random_amount and pix_charge.status == PixCharge.PENDING:
        pix_charge.amount = random_amount
        pix_charge.save(update_fields=("amount", "updated_at"))

    error_message = None
    if created or not pix_charge.qr_code:
        notification_url = request.build_absolute_uri(reverse("mp_webhook"))
        ok, info, data = criar_pix(
            valor_centavos=amount_centavos,
            descricao=f"Mensalidades {month:02d}/{year}",
            external_reference=external_reference,
            notification_url=notification_url,
            tel=responsible.whatsapp,
        )
        if not ok:
            error_message = f"Não foi possível gerar o PIX: {info}"
        else:
            transaction_data = (
                (data or {}).get("point_of_interaction") or {}
            ).get("transaction_data", {})
            qr_code = transaction_data.get("qr_code")
            qr_code_b64 = transaction_data.get("qr_code_base64")
            pix_charge.qr_code = qr_code
            pix_charge.qr_code_base64 = qr_code_b64
            pix_charge.copy_text = extrair_copia_cola(data) or qr_code
            pix_charge.raw_response = data
            pix_charge.mp_payment_id = str(data.get("id")) if data else None
            pix_charge.status = PixCharge.PENDING
            pix_charge.save()

    total = pix_charge.amount
    context = {
        "charge": pix_charge,
        "pending_fees": pending_fees,
        "total": total,
        "error_message": error_message,
        "is_staff": request.user.is_staff,
    }
    return render(request, "core/finance_pix.html", context)


@csrf_exempt
def mp_webhook(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    payload = {}
    raw_body = request.body.strip()
    if raw_body:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = {}

    if not payload:
        if request.POST:
            payload = {key: value for key, value in request.POST.items()}
        elif request.GET:
            payload = {key: value for key, value in request.GET.items()}

    if not payload:
        return HttpResponseBadRequest("payload inválido")

    resource = payload.get("data") or payload.get("transaction") or {}
    fallback_ids = (
        payload.get("resource_id") or payload.get("data_id") or payload.get("id") or payload.get("data.id")
    )
    payment_id = str(resource.get("id") or fallback_ids or "")
    if not payment_id:
        return HttpResponseBadRequest("payment id ausente")

    success, info, payment_data = consultar_pagamento(payment_id)
    if not success:
        logger.warning("Webhook MP: consulta falhou para %s (%s)", payment_id, info)
        return JsonResponse({"status": "error", "detail": info}, status=400)

    external_reference = str(payment_data.get("external_reference") or "")
    charge = PixCharge.objects.filter(external_reference=external_reference).first()
    if not charge:
        charge = PixCharge.objects.filter(mp_payment_id=payment_id).first()
    if not charge:
        logger.warning("Webhook MP sem cobrança conhecida (%s)", external_reference)
        return JsonResponse({"status": "charge_not_found"}, status=404)

    charge.raw_response = payment_data
    charge.mp_payment_id = str(payment_data.get("id") or payment_id)
    charge.last_notification = json.dumps(payload)
    charge.last_notification_at = timezone.now()
    charge.updated_at = timezone.now()
    charge.save(
        update_fields=(
            "mp_payment_id",
            "raw_response",
            "updated_at",
            "last_notification",
            "last_notification_at",
        )
    )

    if is_aprovado(payment_data):
        charge.mark_paid()
        MonthlyFee.objects.filter(
            responsible=charge.responsible, year=charge.year, month=charge.month, status=MonthlyFee.PENDING
        ).update(status=MonthlyFee.PAID, paid_at=timezone.now())
        logger.info(
            "PIX %s confirmado, mensalidades %d/%d marcadas como pagas",
            charge.responsible,
            charge.month,
            charge.year,
        )
        return JsonResponse({"status": "paid"})

    return JsonResponse({"status": "pending"})
def register_adventurer(request):
    """Render the registration workflow para responsáveis e aventureiros."""

    field_errors = {}
    form_values = {}
    success_message = ""

    if request.method == "POST":
        form_values = request.POST.dict()
        responsible_username = form_values.get("responsavel_username", "").strip()
        password1 = form_values.get("responsavel_password1", "")
        password2 = form_values.get("responsavel_password2", "")
        responsavel_nome = form_values.get("responsavel_nome", "").strip()
        responsavel_sobrenome = form_values.get("responsavel_sobrenome", "").strip()
        responsavel_sexo = form_values.get("responsavel_sexo", "").strip()
        cpf = form_values.get("responsavel_cpf", "").strip()
        telefone = form_values.get("responsavel_telefone", "").strip()
        whatsapp = form_values.get("responsavel_whatsapp", "").strip()
        endereco = form_values.get("responsavel_endereco", "").strip()

        pai_data = {
            "nome": form_values.get("pai_nome", "").strip(),
            "email": form_values.get("pai_email", "").strip(),
            "cpf": form_values.get("pai_cpf", "").strip(),
            "telefone": form_values.get("pai_telefone", "").strip(),
            "celular": form_values.get("pai_celular", "").strip(),
        }
        mae_data = {
            "nome": form_values.get("mae_nome", "").strip(),
            "email": form_values.get("mae_email", "").strip(),
            "cpf": form_values.get("mae_cpf", "").strip(),
            "telefone": form_values.get("mae_telefone", "").strip(),
            "celular": form_values.get("mae_celular", "").strip(),
        }
        parent_signature = form_values.get("parent_signature", "").strip()
        parent_data_truth = request.POST.get("parent_data_truth") == "on"
        form_values["parent_data_truth"] = parent_data_truth
        medical_plan = form_values.get("medical_plan", "").strip()
        medical_plan_name = form_values.get("medical_plan_name", "").strip()
        medical_plan_number = form_values.get("medical_plan_number", "").strip()
        medical_sus = form_values.get("medical_sus", "").strip()
        medical_allergy_skin = form_values.get("medical_allergy_skin", "").strip()
        medical_allergy_food = form_values.get("medical_allergy_food", "").strip()
        medical_allergy_food_detail = form_values.get("medical_allergy_food_detail", "").strip()
        medical_allergy_med = form_values.get("medical_allergy_med", "").strip()
        medical_allergy_med_detail = form_values.get("medical_allergy_med_detail", "").strip()
        medical_other = form_values.get("medical_other", "").strip()
        medical_recent_medicines = form_values.get("medical_recent_medicines", "").strip()
        medical_recent_fractures = form_values.get("medical_recent_fractures", "").strip()
        medical_surgeries = form_values.get("medical_surgeries", "").strip()
        medical_hospitalization = form_values.get("medical_hospitalization", "").strip()
        medical_heart = form_values.get("medical_heart", "").strip()
        medical_heart_meds = form_values.get("medical_heart_meds", "").strip()
        medical_heart_meds_detail = form_values.get("medical_heart_meds_detail", "").strip()
        medical_diabetic = form_values.get("medical_diabetic", "").strip()
        medical_diabetic_meds = form_values.get("medical_diabetic_meds", "").strip()
        medical_diabetic_meds_detail = form_values.get("medical_diabetic_meds_detail", "").strip()
        medical_kidney = form_values.get("medical_kidney", "").strip()
        medical_kidney_meds = form_values.get("medical_kidney_meds", "").strip()
        medical_kidney_meds_detail = form_values.get("medical_kidney_meds_detail", "").strip()
        medical_psychological = form_values.get("medical_psychological", "").strip()
        medical_blood_type = form_values.get("medical_blood_type", "").strip()
        medical_signature = form_values.get("medical_signature", "").strip()
        medical_data_truth = request.POST.get("medical_data_truth") == "on"
        form_values["medical_data_truth"] = medical_data_truth

        adventure_full_name = form_values.get("adventure_full_name", "").strip()
        adventure_sexo = form_values.get("adventure_sexo", "").strip()
        adventure_birth_day = form_values.get("adventure_birth_day", "").strip()
        adventure_birth_month = form_values.get("adventure_birth_month", "").strip()
        adventure_birth_year = form_values.get("adventure_birth_year", "").strip()
        adventure_school = form_values.get("adventure_school", "").strip()
        adventure_grade = form_values.get("adventure_grade", "").strip()
        adventure_bolsa = form_values.get("adventure_bolsa", "").strip()
        adventure_street = form_values.get("adventure_street", "").strip()
        adventure_number = form_values.get("adventure_number", "").strip()
        adventure_neighborhood = form_values.get("adventure_neighborhood", "").strip()
        adventure_postal_code = form_values.get("adventure_postal_code", "").strip()
        adventure_city = form_values.get("adventure_city", "").strip()
        adventure_state = form_values.get("adventure_state", "").strip()
        adventure_certidao = form_values.get("adventure_certidao", "").strip()
        adventure_rg = form_values.get("adventure_rg", "").strip()
        adventure_rg_issuer = form_values.get("adventure_rg_issuer", "").strip()
        adventure_cpf = form_values.get("adventure_cpf", "").strip()
        adventure_parent_whatsapp_phone = form_values.get("adventure_parent_whatsapp_phone", "").strip()
        adventure_shirt_size = form_values.get("adventure_shirt_size", "").strip()
        adventure_data_signature = form_values.get("adventure_data_signature", "").strip()
        adventure_data_truth = request.POST.get("adventure_data_truth") == "on"
        form_values["adventure_data_truth"] = adventure_data_truth

        term_responsible = form_values.get("term_responsible", "").strip()
        term_nationality = form_values.get("term_nationality", "").strip()
        term_child = form_values.get("term_child", "").strip()
        term_local = form_values.get("term_local", "").strip()
        term_signature = form_values.get("term_signature", "").strip()
        term_child_name = form_values.get("term_child_name", "").strip()
        term_contact_phone = form_values.get("term_contact_phone", "").strip()
        term_data_truth = request.POST.get("term_data_truth") == "on"
        form_values["term_data_truth"] = term_data_truth

        for slug, _ in CLASS_OPTIONS:
            if request.POST.get(f"adventure_class_{slug}"):
                form_values[f"adventure_class_{slug}"] = "on"

        conditions_list = []
        for slug, label in MEDICAL_CONDITIONS:
            if request.POST.get(f"medical_condition_{slug}"):
                form_values[f"medical_condition_{slug}"] = "on"
                conditions_list.append(label)

        deficiency_slugs = [
            ("cadeirante", "Cadeirante"),
            ("visual", "Visual"),
            ("auditivo", "Auditivo"),
            ("fala", "Fala - mudo ou dificuldade"),
        ]
        deficiencies = []
        for slug, label in deficiency_slugs:
            key = f"medical_deficiente_{slug}"
            if request.POST.get(key):
                form_values[key] = "on"
                deficiencies.append(label)

        class_selected = [label for slug, label in CLASS_OPTIONS if form_values.get(f"adventure_class_{slug}")]
        medical_confirmation = request.POST.get("medical_confirmation")
        term_confirmation = request.POST.get("term_confirmation")
        form_values["medical_confirmation"] = medical_confirmation
        form_values["term_confirmation"] = term_confirmation

        if not responsible_username:
            field_errors["responsavel_username"] = "Informe um nome de usuário."
        if not password1 or not password2:
            field_errors["responsavel_password1"] = "Informe e confirme a senha."
        elif password1 != password2:
            field_errors["responsavel_password2"] = "As senhas não conferem."
        elif len(password1) != 4 or not password1.isdigit():
            field_errors["responsavel_password1"] = "A senha precisa ter 4 dígitos."

        if not responsavel_nome:
            field_errors["responsavel_nome"] = "Informe o nome do responsável."
        if not responsavel_sobrenome:
            field_errors["responsavel_sobrenome"] = "Informe o sobrenome."
        if not responsavel_sexo:
            field_errors["responsavel_sexo"] = "Informe o sexo do responsável."
        if not cpf:
            field_errors["responsavel_cpf"] = "Informe o CPF."
        if not telefone:
            field_errors["responsavel_telefone"] = "Informe o telefone."
        if not whatsapp:
            field_errors["responsavel_whatsapp"] = "Informe o WhatsApp."
        if not endereco:
            field_errors["responsavel_endereco"] = "Informe o endereço."

        for parent, prefix in ((pai_data, "pai"), (mae_data, "mae")):
            if not parent["nome"]:
                field_errors[f"{prefix}_nome"] = f"Informe o nome do {prefix}."
            if not parent["email"]:
                field_errors[f"{prefix}_email"] = f"Informe o e-mail do {prefix}."
            if not parent["cpf"]:
                field_errors[f"{prefix}_cpf"] = f"Informe o CPF do {prefix}."
            if not parent["telefone"]:
                field_errors[f"{prefix}_telefone"] = f"Informe o telefone do {prefix}."
            if not parent["celular"]:
                field_errors[f"{prefix}_celular"] = f"Informe o celular do {prefix}."

        adventure_required = {
            "adventure_full_name": adventure_full_name,
            "adventure_sexo": adventure_sexo,
            "adventure_birth_day": adventure_birth_day,
            "adventure_birth_month": adventure_birth_month,
            "adventure_birth_year": adventure_birth_year,
            "adventure_school": adventure_school,
            "adventure_grade": adventure_grade,
            "adventure_bolsa": adventure_bolsa,
            "adventure_street": adventure_street,
            "adventure_number": adventure_number,
            "adventure_neighborhood": adventure_neighborhood,
            "adventure_postal_code": adventure_postal_code,
            "adventure_city": adventure_city,
            "adventure_state": adventure_state,
            "adventure_certidao": adventure_certidao,
            "adventure_rg": adventure_rg,
            "adventure_cpf": adventure_cpf,
            "adventure_parent_whatsapp_phone": adventure_parent_whatsapp_phone,
            "adventure_shirt_size": adventure_shirt_size,
        }
        for key, value in adventure_required.items():
            if not value:
                field_errors[key] = "Campo obrigatório."

        if not adventure_parent_whatsapp_phone:
            field_errors["adventure_parent_whatsapp_phone"] = "Informe o WhatsApp do responsável."
        if not adventure_shirt_size:
            field_errors["adventure_shirt_size"] = "Informe o tamanho da camiseta."
        if not parent_signature:
            field_errors["parent_signature"] = "Assine os dados dos pais."
        if not parent_data_truth:
            field_errors["parent_data_truth"] = "Confirme que os dados dos pais são verdadeiros."
        if not adventure_data_signature:
            field_errors["adventure_data_signature"] = "Assine os dados do aventureiro."
        if not adventure_data_truth:
            field_errors["adventure_data_truth"] = "Confirme que os dados do aventureiro são verdadeiros."

        if not medical_plan:
            field_errors["medical_plan"] = "Informe se possui plano de saúde."
        if medical_plan == "sim" and not medical_plan_number:
            field_errors["medical_plan_number"] = "Informe o número da carteirinha do plano de saúde."
        if not medical_sus:
            field_errors["medical_sus"] = "Informe o número do SUS."
        if not medical_allergy_skin:
            field_errors["medical_allergy_skin"] = "Informe se possui alergia cutânea."
        if not medical_allergy_food:
            field_errors["medical_allergy_food"] = "Informe se possui alergia alimentar."
        if not medical_allergy_med:
            field_errors["medical_allergy_med"] = "Informe se possui alergia a medicamentos."
        if not medical_heart:
            field_errors["medical_heart"] = "Informe se possui problemas cardíacos."
        if not medical_heart_meds:
            field_errors["medical_heart_meds"] = "Informe o uso de remédios cardíacos."
        if not medical_diabetic:
            field_errors["medical_diabetic"] = "Informe se é diabético."
        if not medical_diabetic_meds:
            field_errors["medical_diabetic_meds"] = "Informe o uso de remédios para diabetes."
        if not medical_kidney:
            field_errors["medical_kidney"] = "Informe se possui problemas renais."
        if not medical_kidney_meds:
            field_errors["medical_kidney_meds"] = "Informe o uso de remédios renais."
        if not medical_psychological:
            field_errors["medical_psychological"] = "Informe se possui problemas psicológicos."
        if not medical_recent_fractures:
            field_errors["medical_recent_fractures"] = "Informe se houve fraturas recentes."
        if not medical_surgeries:
            field_errors["medical_surgeries"] = "Informe se passou por cirurgias."
        if not medical_blood_type:
            field_errors["medical_blood_type"] = "Informe o tipo sanguíneo."
        if not medical_confirmation:
            field_errors["medical_confirmation"] = "Confirme as informações médicas."
        if not medical_signature:
            field_errors["medical_signature"] = "Assine a ficha médica."
        if not medical_data_truth:
            field_errors["medical_data_truth"] = "Confirme que os dados médicos são verdadeiros."

        if not term_responsible:
            field_errors["term_responsible"] = "Informe o responsável do termo."
        if not term_nationality:
            field_errors["term_nationality"] = "Informe a nacionalidade."
        if not term_child:
            field_errors["term_child"] = "Informe o nome do menor."
        if not term_local:
            field_errors["term_local"] = "Informe o local e data."
        if not term_signature:
            field_errors["term_signature"] = "Informe a assinatura do responsável."
        if not term_child_name:
            field_errors["term_child_name"] = "Informe o nome da criança."
        if not term_contact_phone:
            field_errors["term_contact_phone"] = "Informe um telefone para contato."
        if not term_confirmation:
            field_errors["term_confirmation"] = "Confirme o termo."
        if not term_data_truth:
            field_errors["term_data_truth"] = "Confirme que os dados do termo são verdadeiros."

        if User.objects.filter(username=responsible_username).exists():
            field_errors["responsavel_username"] = "Nome de usuário indisponível."
        if Responsible.objects.filter(cpf=cpf).exists():
            field_errors["responsavel_cpf"] = "Esse CPF já está cadastrado."

        file_photo = request.FILES.get("adventure_photo")
        if not file_photo:
            field_errors["adventure_photo"] = "Anexe a foto 3x4."

        try:
            birth_date = date(int(adventure_birth_year), int(adventure_birth_month), int(adventure_birth_day))
        except (ValueError, TypeError):
            field_errors["adventure_birth_date"] = "Selecione uma data de nascimento válida."

        if not field_errors:
            allergies_summary = []
            if form_values.get("medical_allergy_skin") == "sim":
                allergies_summary.append("Alergia cutânea")
            if form_values.get("medical_allergy_food") == "sim":
                allergies_summary.append(f"Alergia alimentar: {form_values.get('medical_allergy_food_detail','')}")
            if form_values.get("medical_allergy_med") == "sim":
                allergies_summary.append(f"Alergia a remédios: {form_values.get('medical_allergy_med_detail','')}")

            medication_text = medical_other or ""
            observation_text = medical_recent_medicines

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=responsible_username,
                        password=password1,
                        first_name=responsavel_nome,
                        last_name=responsavel_sobrenome,
                    )
                    responsible = Responsible.objects.create(
                        user=user,
                        cpf=cpf,
                        telefone=telefone,
                        whatsapp=whatsapp,
                        endereco=endereco,
                        sexo=responsavel_sexo,
                    )
                    names = adventure_full_name.split()
                    first_name = names[0] if names else adventure_full_name
                    last_name = " ".join(names[1:]) if len(names) > 1 else ""
                    adventurer = Adventurer.objects.create(
                        responsible=responsible,
                        first_name=first_name,
                        last_name=last_name or first_name,
                        document=adventure_certidao,
                        birth_date=birth_date,
                        allergies="; ".join(allergies_summary) or "Nenhuma",
                        medication=medication_text,
                        observation=observation_text,
                        emergency_name=pai_data["nome"],
                        emergency_phone=pai_data["telefone"],
                        emergency_whatsapp=pai_data["celular"],
                        photo=file_photo,
                        sexo=adventure_sexo or "M",
                        school=adventure_school,
                        grade=adventure_grade,
                        bolsa_familia=adventure_bolsa == "sim",
                        classes_investidas=", ".join(class_selected),
                        address=adventure_street,
                        neighborhood=adventure_neighborhood,
                        city=adventure_city,
                        postal_code=adventure_postal_code,
                        state=adventure_state,
                        certidao=adventure_certidao,
                        rg=adventure_rg,
                        rg_issuer=adventure_rg_issuer,
                        cpf_number=adventure_cpf,
                        parent_whatsapp=bool(adventure_parent_whatsapp_phone),
                        shirt_size=adventure_shirt_size,
                        blood_type=form_values.get("medical_blood_type", ""),
                        family_data={
                            "pai": pai_data,
                            "mae": mae_data,
                            "assinatura_dados_iniciais": responsavel_signature,
                            "dados_iniciais_verdadeiros": responsavel_data_truth,
                            "assinatura_pais": parent_signature,
                            "dados_pais_verdadeiros": parent_data_truth,
                            "assinatura_dados_aventureiro": adventure_data_signature,
                            "dados_aventureiro_verdadeiros": adventure_data_truth,
                        },
                        medical_data={
                            "plano": medical_plan,
                            "plano_nome": medical_plan_name,
                            "plano_numero": medical_plan_number,
                            "sus": medical_sus,
                            "alergia_cutanea": medical_allergy_skin,
                            "alergia_alimentar": medical_allergy_food,
                            "alergia_alimento": medical_allergy_food_detail,
                            "alergia_medicamento": medical_allergy_med,
                            "alergia_remedio": medical_allergy_med_detail,
                            "condicoes": conditions_list,
                            "deficientes": deficiencies,
                            "problema_cardiaco": medical_heart,
                            "medicacao_cardiaca": medical_heart_meds,
                            "medicacao_cardiaca_det": medical_heart_meds_detail,
                            "diabetico": medical_diabetic,
                            "medicacao_diabetica": medical_diabetic_meds,
                            "medicacao_diabetica_det": medical_diabetic_meds_detail,
                            "problema_renal": medical_kidney,
                            "medicacao_renal": medical_kidney_meds,
                            "medicacao_renal_det": medical_kidney_meds_detail,
                            "psicologico": medical_psychological,
                            "medicamentos_recentes": medical_recent_medicines,
                            "fraturas_recentes": medical_recent_fractures,
                            "cirurgias": medical_surgeries,
                            "internacao": medical_hospitalization,
                            "assinatura": medical_signature,
                            "dados_verdadeiros": medical_data_truth,
                            "tipo_sanguineo": medical_blood_type,
                        },
                        term_data={
                            "responsavel": term_responsible,
                            "nacionalidade": term_nationality,
                            "crianca": term_child,
                            "local": term_local,
                            "assinatura": term_signature,
                            "nome_crianca": term_child_name,
                            "telefone": term_contact_phone,
                            "confirmacao": bool(term_confirmation),
                            "dados_verdadeiros": term_data_truth,
                        },
                    )
                    _create_monthly_fees(responsible, adventurer)
                messages.success(request, "Cadastro enviado! Faça login para acessar o painel.")
                return redirect("login")
            except IntegrityError:
                field_errors["responsavel_username"] = "Erro ao criar usuário; tente um nome diferente."

    context = {
        "form_values": form_values,
        "field_errors": field_errors,
        "success_message": success_message,
        "days": DAY_OPTIONS,
        "months": MONTH_OPTIONS,
        "years": YEAR_OPTIONS,
        "sex_choices": SEX_CHOICES,
        "class_options": CLASS_OPTIONS,
        "medical_conditions": MEDICAL_CONDITIONS,
        "blood_types": BLOOD_TYPES,
    }
    return render(request, "core/register.html", context)


def registration_choice(request):
    """Tela intermediária para escolher o tipo de cadastro desejado."""

    return render(request, "core/register_choice.html")


def register_director(request):
    field_errors = {}
    form_values = {}
    success_message = ""

    if request.method == "POST":
        form_values = request.POST.dict()
        responsible_username = form_values.get("responsavel_username", "").strip()
        password1 = form_values.get("responsavel_password1", "")
        password2 = form_values.get("responsavel_password2", "")
        responsavel_nome = form_values.get("responsavel_nome", "").strip()
        responsavel_sobrenome = form_values.get("responsavel_sobrenome", "").strip()
        responsavel_sexo = form_values.get("responsavel_sexo", "").strip()
        cpf = form_values.get("responsavel_cpf", "").strip()
        telefone = form_values.get("responsavel_telefone", "").strip()
        whatsapp = form_values.get("responsavel_whatsapp", "").strip()
        responsavel_street = form_values.get("responsavel_street", "").strip()
        responsavel_house_number = form_values.get("responsavel_house_number", "").strip()
        responsavel_neighborhood = form_values.get("responsavel_neighborhood", "").strip()
        responsavel_postal_code = form_values.get("responsavel_postal_code", "").strip()
        responsavel_city = form_values.get("responsavel_city", "").strip()
        responsavel_state = form_values.get("responsavel_state", "").strip()
        director_initial_signature = form_values.get("director_initial_signature", "").strip()
        director_initial_data_truth = request.POST.get("director_initial_data_truth") == "on"
        form_values["director_initial_data_truth"] = director_initial_data_truth
        responsavel_signature = form_values.get("responsavel_signature", "").strip()
        responsavel_data_truth = request.POST.get("responsavel_data_truth") == "on"
        form_values["responsavel_data_truth"] = responsavel_data_truth

        for field_key, error_label in (
            ("responsavel_username", "Informe um nome de usuário."),
            ("responsavel_password1", "Informe e confirme a senha."),
            ("responsavel_nome", "Informe o nome do responsável."),
            ("responsavel_sobrenome", "Informe o sobrenome."),
            ("responsavel_sexo", "Informe o sexo do responsável."),
            ("responsavel_cpf", "Informe o CPF."),
            ("responsavel_telefone", "Informe o telefone."),
            ("responsavel_whatsapp", "Informe o WhatsApp."),
            ("responsavel_street", "Informe a Av/Rua."),
            ("responsavel_house_number", "Informe o número."),
            ("responsavel_neighborhood", "Informe o bairro."),
            ("responsavel_postal_code", "Informe o CEP."),
            ("responsavel_city", "Informe a cidade."),
            ("responsavel_state", "Informe o estado."),
        ):
            if not form_values.get(field_key, "").strip():
                field_errors[field_key] = error_label

        if not responsavel_signature:
            field_errors["responsavel_signature"] = "Assine os dados iniciais."
        if not responsavel_data_truth:
            field_errors["responsavel_data_truth"] = "Confirme que os dados iniciais são verdadeiros."

        if password1 or password2:
            if password1 != password2:
                field_errors["responsavel_password2"] = "As senhas não conferem."
            elif len(password1) != 4 or not password1.isdigit():
                field_errors["responsavel_password1"] = "A senha precisa ter 4 dígitos."
        else:
            field_errors["responsavel_password1"] = "Informe e confirme a senha."

        if User.objects.filter(username=responsible_username).exists():
            field_errors["responsavel_username"] = "Nome de usuário indisponível."
        if Responsible.objects.filter(cpf=cpf).exists():
            field_errors["responsavel_cpf"] = "Esse CPF já está cadastrado."

        term_nationality = form_values.get("term_nationality", "").strip()
        term_marital_status = form_values.get("term_marital_status", "").strip()
        term_rg_number = form_values.get("term_rg_number", "").strip()
        term_residence = form_values.get("term_residence", "").strip()
        term_number = form_values.get("term_number", "").strip()
        term_neighborhood = form_values.get("term_neighborhood", "").strip()
        term_postal_code = form_values.get("term_postal_code", "").strip()
        term_municipality = form_values.get("term_municipality", "").strip()
        term_state = form_values.get("term_state", "").strip()
        term_cpf = form_values.get("term_cpf", "").strip()
        term_signature = form_values.get("term_signature", "").strip()
        term_accept = request.POST.get("term_accept") == "on"
        form_values["term_accept"] = term_accept
        director_data_truth = request.POST.get("director_data_truth") == "on"
        form_values["director_data_truth"] = director_data_truth
        director_photo = request.FILES.get("director_photo")
        volunteer_acceptance = request.POST.get("volunteer_acceptance") == "on"
        form_values["volunteer_acceptance"] = volunteer_acceptance
        director_volunteer_signature = form_values.get("director_volunteer_signature", "").strip()
        director_volunteer_data_truth = request.POST.get("director_volunteer_data_truth") == "on"
        form_values["director_volunteer_data_truth"] = director_volunteer_data_truth

        for field_key, message in (
            ("term_nationality", "Informe sua nacionalidade."),
            ("term_marital_status", "Informe o estado civil."),
            ("term_rg_number", "Informe o número do RG."),
            ("term_residence", "Informe a Av/Rua."),
            ("term_number", "Informe o número."),
            ("term_neighborhood", "Informe o bairro."),
            ("term_postal_code", "Informe o CEP."),
            ("term_municipality", "Informe o município."),
            ("term_state", "Informe o estado."),
            ("term_cpf", "Informe o CPF."),
        ):
            if not form_values.get(field_key, "").strip():
                field_errors[field_key] = message

        if not term_accept:
            field_errors["term_accept"] = "Você precisa aceitar o termo de autorização."
        if not term_signature:
            field_errors["term_signature"] = "Informe a assinatura do responsável."
        if not director_photo:
            field_errors["director_photo"] = "Anexe a foto 3x4 do voluntário."
        if not volunteer_acceptance:
            field_errors["volunteer_acceptance"] = "Você precisa aceitar o compromisso."
        if not director_data_truth:
            field_errors["director_data_truth"] = "Confirme que todas as informações fornecidas são verdadeiras."
        if not director_initial_signature:
            field_errors["director_initial_signature"] = "Assine os dados iniciais."
        if not director_initial_data_truth:
            field_errors["director_initial_data_truth"] = "Confirme que os dados iniciais são verdadeiros."
        if not director_volunteer_signature:
            field_errors["director_volunteer_signature"] = "Assine o compromisso voluntário."
        if not director_volunteer_data_truth:
            field_errors["director_volunteer_data_truth"] = "Confirme que os dados do compromisso são verdadeiros."

        director_full_name = form_values.get("director_full_name", "").strip()
        director_church = form_values.get("director_church", "").strip()
        director_district = form_values.get("director_district", "").strip()
        director_street = form_values.get("director_street_address", "").strip()
        director_house_number = form_values.get("director_house_number", "").strip()
        director_neighborhood = form_values.get("director_neighborhood", "").strip()
        director_postal_code = form_values.get("director_postal_code", "").strip()
        director_city = form_values.get("director_city", "").strip()
        director_state = form_values.get("director_state", "").strip()
        director_email = form_values.get("director_email", "").strip()
        director_cellphone = form_values.get("director_cellphone", "").strip()
        director_home_phone = form_values.get("director_home_phone", "").strip()
        director_work_phone = form_values.get("director_work_phone", "").strip()
        director_birth_day = form_values.get("director_birth_day", "").strip()
        director_birth_month = form_values.get("director_birth_month", "").strip()
        director_birth_year = form_values.get("director_birth_year", "").strip()
        director_marital_status = form_values.get("director_marital_status", "").strip()
        director_cpf = form_values.get("director_cpf", "").strip()
        director_rg = form_values.get("director_rg", "").strip()
        director_spouse = form_values.get("director_spouse", "").strip()
        director_child_one = form_values.get("director_child_one", "").strip()
        director_child_two = form_values.get("director_child_two", "").strip()
        health_limitation = request.POST.get("director_health_limitation") == "on"
        form_values["director_health_limitation"] = health_limitation
        health_description = form_values.get("director_health_description", "").strip()
        education_level = form_values.get("director_education_level", "").strip()

        for field_key, message in (
            ("director_full_name", "Informe o nome completo."),
            ("director_church", "Informe o nome da igreja."),
            ("director_district", "Informe o distrito."),
            ("director_street_address", "Informe o endereço completo."),
            ("director_city", "Informe a cidade."),
            ("director_state", "Informe o estado."),
            ("director_email", "Informe o e-mail."),
            ("director_cellphone", "Informe o celular."),
            ("director_marital_status", "Informe o estado civil."),
            ("director_cpf", "Informe o CPF."),
            ("director_rg", "Informe o RG."),
            ("director_education_level", "Informe a escolaridade."),
        ):
            if not form_values.get(field_key, "").strip():
                field_errors[field_key] = message

        birth_date = None
        if director_birth_day and director_birth_month and director_birth_year:
            try:
                birth_date = date(
                    int(director_birth_year), int(director_birth_month), int(director_birth_day)
                )
            except (ValueError, TypeError):
                field_errors["director_birth_date"] = "Informe uma data de nascimento válida."
        else:
            field_errors["director_birth_date"] = "Informe a data de nascimento completa."

        if education_level not in dict(EDUCATION_CHOICES):
            field_errors["director_education_level"] = "Escolha um nível de escolaridade."

        if not field_errors:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=responsible_username,
                        password=password1,
                        first_name=responsavel_nome,
                        last_name=responsavel_sobrenome,
                    )
                    responsible_address = (
                        f"{responsavel_street}, {responsavel_house_number} - {responsavel_neighborhood}, "
                        f"CEP {responsavel_postal_code}, {responsavel_city} - {responsavel_state}"
                    )
                    responsible = Responsible.objects.create(
                        user=user,
                        cpf=cpf,
                        telefone=telefone,
                        whatsapp=whatsapp,
                        endereco=responsible_address,
                        sexo=responsavel_sexo,
                    )
                    DirectorApplication.objects.create(
                        responsible=responsible,
                        term_nationality=term_nationality,
                        term_marital_status=term_marital_status,
                        term_rg_number=term_rg_number,
                        term_residence=term_residence,
                        term_number=term_number,
                        term_neighborhood=term_neighborhood,
                        term_postal_code=term_postal_code,
                        term_municipality=term_municipality,
                        term_state=term_state,
                        term_cpf=term_cpf,
                        term_accepted=term_accept,
                        term_signature=term_signature,
                        term_data_truth=director_data_truth,
                        initial_signature=director_initial_signature,
                        initial_data_truth=director_initial_data_truth,
                        church=director_church,
                        district=director_district,
                        full_name=director_full_name,
                        street_address=director_street,
                        house_number=director_house_number,
                        neighborhood=director_neighborhood,
                        postal_code=director_postal_code,
                        city=director_city,
                        state=director_state,
                        email=director_email,
                        cellphone=director_cellphone,
                        home_phone=director_home_phone,
                        work_phone=director_work_phone,
                        birth_date=birth_date,
                        volunteer_marital_status=director_marital_status,
                        director_cpf=director_cpf,
                        director_rg=director_rg,
                        spouse=director_spouse,
                        child_one=director_child_one,
                        child_two=director_child_two,
                        health_limitation=health_limitation,
                        health_description=health_description,
                        education_level=education_level,
                        photo=director_photo,
                        volunteer_signature=director_volunteer_signature,
                        volunteer_data_truth=director_volunteer_data_truth,
                        volunteer_acceptance=volunteer_acceptance,
                    )
                messages.success(
                    request,
                    "Cadastro da diretoria enviado! Um membro da coordenação entrará em contato.",
                )
                return redirect("login")
            except IntegrityError:
                field_errors["responsavel_username"] = "Erro ao criar usuário; tente um nome diferente."

    context = {
        "form_values": form_values,
        "field_errors": field_errors,
        "sex_choices": SEX_CHOICES,
        "days": DAY_OPTIONS,
        "months": MONTH_OPTIONS,
        "years": YEAR_OPTIONS,
        "education_choices": EDUCATION_CHOICES,
    }
    return render(request, "core/register_director.html", context)


@login_required
def dashboard(request):
    roles = []
    adventurers = []
    adventurers_records = []
    if hasattr(request.user, "responsavel"):
        roles.append("responsavel")
        responsible = request.user.responsavel
        adventurers = list(
            responsible.adventureiros.values(
                "id",
                "first_name",
                "last_name",
                "document",
                "birth_date",
                "allergies",
                "medication",
                "observation",
                "emergency_name",
                "emergency_phone",
                "emergency_whatsapp",
            )
        )
        adventurer_qs = responsible.adventureiros.all()
        adventurers_records = _build_adventurer_records(adventurer_qs)
        for adventurer in adventurer_qs:
            _create_monthly_fees(responsible, adventurer)
        monthly_fees = MonthlyFee.objects.filter(responsible=responsible).order_by("year", "month")
        finance_periods = _build_finance_periods(monthly_fees)
        _attach_pix_charges(finance_periods, responsible)
    else:
        responsible = None
        finance_periods = []

    menu_items = [
        {"key": "initial", "label": "Inicial"},
        {
            "key": "cadastros",
            "label": "Cadastros",
            "requires": "responsavel",
        },
        {
            "key": "financeiro",
            "label": "Financeiro",
            "requires": "responsavel",
        },
    ]

    return render(
        request,
        "core/dashboard.html",
        {
            "roles": roles,
            "responsible": responsible,
            "adventurers": adventurers,
            "adventurers_records": adventurers_records,
            "menu_items": menu_items,
            "sex_choices": SEX_CHOICES,
            "days": DAY_OPTIONS,
        "months": MONTH_OPTIONS,
        "years": YEAR_OPTIONS,
        "finance_periods": finance_periods,
        },
    )
