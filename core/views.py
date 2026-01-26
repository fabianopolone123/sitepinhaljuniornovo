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

from .models import (
    Adventurer,
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

MONTHLY_FEE_DUE_DAY = 10

logger = logging.getLogger(__name__)


def _empty_adventurer_data():
    return {
        "nome": "",
        "sobrenome": "",
        "documento": "",
        "dia": "",
        "mes": "",
        "ano": "",
        "alergias": "",
        "medicacao": "",
        "observacao": "",
        "contato_nome": "",
        "contato_telefone": "",
        "contato_whatsapp": "",
        "sexo": "",
    }


def _build_adventurers_data(post):
    if not post:
        return [_empty_adventurer_data()]

    lists = {
        "nome": post.getlist("aventureiro_nome[]"),
        "sobrenome": post.getlist("aventureiro_sobrenome[]"),
        "documento": post.getlist("aventureiro_documento[]"),
        "dia": post.getlist("aventureiro_dia[]"),
        "mes": post.getlist("aventureiro_mes[]"),
        "ano": post.getlist("aventureiro_ano[]"),
        "alergias": post.getlist("aventureiro_alergias[]"),
        "medicacao": post.getlist("aventureiro_medicacao[]"),
        "observacao": post.getlist("aventureiro_observacao[]"),
        "contato_nome": post.getlist("emergencia_nome[]"),
        "contato_telefone": post.getlist("emergencia_telefone[]"),
        "contato_whatsapp": post.getlist("emergencia_whatsapp[]"),
        "sexo": post.getlist("aventureiro_sexo[]"),
    }

    max_len = max(len(values) for values in lists.values())
    if max_len == 0:
        return [_empty_adventurer_data()]

    data = []
    for idx in range(max_len):
        data.append(
            {
                key: lists[key][idx] if idx < len(lists[key]) else ""
                for key in lists
            }
        )
    return data


def _create_monthly_fees(responsible, adventurer, start_date=None):
    start = start_date or timezone.localdate()
    year = start.year
    for month in range(start.month, 13):
        MonthlyFee.objects.get_or_create(
            responsible=responsible,
            adventurer=adventurer,
            month=month,
            year=year,
            defaults={"amount": Decimal("1.00"), "due_day": MONTHLY_FEE_DUE_DAY},
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

    total = sum(fee.amount for fee in pending_fees)
    amount_centavos = int(
        (total * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    external_reference = f"mensalidades-{responsible.id}-{year}-{month}"
    pix_charge, created = PixCharge.objects.get_or_create(
        responsible=responsible,
        year=year,
        month=month,
        defaults={
            "amount": total,
            "external_reference": external_reference,
        },
    )
    if pix_charge.amount != total and pix_charge.status == PixCharge.PENDING:
        pix_charge.amount = total
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

    context = {
        "charge": pix_charge,
        "pending_fees": pending_fees,
        "total": total,
        "error_message": error_message,
    }
    return render(request, "core/finance_pix.html", context)


@csrf_exempt
def mp_webhook(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest("payload inválido")

    resource = payload.get("data") or payload.get("transaction") or {}
    payment_id = str(resource.get("id") or payload.get("data_id") or payload.get("resource_id") or "")
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
def register(request):
    """Render the registration workflow for responsáveis e aventureiros."""

    field_errors = {}
    form_values = {}
    success_message = ""
    adventurers_data = _build_adventurers_data(request.POST if request.method == "POST" else None)

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

        if User.objects.filter(username=responsible_username).exists():
            field_errors["responsavel_username"] = "Nome de usuário indisponível."
        if Responsible.objects.filter(cpf=cpf).exists():
            field_errors["responsavel_cpf"] = "Esse CPF já está cadastrado."

        adventurer_photos = request.FILES.getlist("aventureiro_foto[]")
        adventurer_entries = []
        for idx, adventurer in enumerate(adventurers_data):
            errors_required = []
            for key in ("nome", "sobrenome", "documento", "alergias", "medicacao", "observacao", "contato_nome", "contato_telefone", "contato_whatsapp"):
                if not adventurer.get(key):
                    errors_required.append(key)
            if not adventurer.get("dia") or not adventurer.get("mes") or not adventurer.get("ano"):
                errors_required.append("nascimento")
            if not adventurer.get("sexo"):
                errors_required.append("sexo")

            if errors_required:
                field_errors["adventurer"] = "Preencha todos os campos de cada aventureiro."
                break

            if idx >= len(adventurer_photos) or not adventurer_photos[idx]:
                field_errors["adventurer_photo"] = "Anexe a foto 3x4 de cada aventureiro."
                break

            try:
                birth_date = date(int(adventurer["ano"]), int(adventurer["mes"]), int(adventurer["dia"]))
            except (ValueError, TypeError):
                field_errors["adventurer_date"] = "Selecione uma data de nascimento válida."
                break

            adventurer_entries.append(
                {
                    "first_name": adventurer["nome"],
                    "last_name": adventurer["sobrenome"],
                    "document": adventurer["documento"],
                    "birth_date": birth_date,
                    "allergies": adventurer["alergias"],
                    "medication": adventurer["medicacao"],
                    "observation": adventurer["observacao"],
                    "emergency_name": adventurer["contato_nome"],
                    "emergency_phone": adventurer["contato_telefone"],
                    "emergency_whatsapp": adventurer["contato_whatsapp"],
                    "sexo": adventurer["sexo"],
                    "photo": adventurer_photos[idx],
                }
            )

        if not field_errors and adventurer_entries:
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
                    for entry in adventurer_entries:
                        sexo_val = entry.pop("sexo")
                        adventurer = Adventurer.objects.create(responsible=responsible, sexo=sexo_val, **entry)
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
        "adventurers_data": adventurers_data,
        "sex_choices": SEX_CHOICES,
    }
    return render(request, "core/register.html", context)


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
