from __future__ import annotations
"""
Pagamentos (Mercado Pago) — PIX com 'payer.email' obrigatório (fallback)
-----------------------------------------------------------------------
- criar_pix(...): cria a cobrança PIX SEMPRE incluindo 'payer.email' sintaticamente válido,
  gerado a partir do telefone (ex.: cliente.5514999999999@example.com.br)
- consultar_pagamento(id): verifica o pagamento
- is_aprovado(json): True se pago
- extrair_copia_cola(json): retorna o código copia e cola

Retornos: (ok: bool, info: str, data: dict|None)
Depende de MP_ACCESS_TOKEN e MP_API_BASE definidos em config.py.
"""

import uuid
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests
from config import MP_ACCESS_TOKEN, MP_API_BASE

_DEF_TIMEOUT = 20


# =========================
# Helpers (fallback & refs)
# =========================
def _digits(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\D+", "", str(s))

def _email_fallback(tel: str | None) -> str:
    # Gera um e-mail "válido" para o MP a partir do telefone
    d = _digits(tel)
    if not d:
        d = "00000000000"
    return f"cliente.{d}@example.com.br"

def _centavos_para_reais(v: int | float | None) -> float:
    try:
        return round((v or 0) / 100.0, 2)
    except Exception:
        return 0.0

def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h

def extrair_copia_cola(resp: Dict[str, Any]) -> Optional[str]:
    pio = (resp or {}).get("point_of_interaction") or {}
    td = (pio.get("transaction_data") or {}) if isinstance(pio, dict) else {}
    return td.get("qr_code")

def is_aprovado(payment_json: Dict[str, Any]) -> bool:
    st = (payment_json or {}).get("status")
    return str(st).lower() == "approved"

def resumo_status(payment_json: Dict[str, Any]) -> str:
    st = str((payment_json or {}).get("status") or "").lower()
    det = str((payment_json or {}).get("status_detail") or "").lower()
    return f"status={st} detail={det}"


# =========================
# API Mercado Pago
# =========================
def criar_pix(
    valor_centavos: int,
    descricao: Optional[str] = None,
    external_reference: Optional[str] = None,
    notification_url: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    timeout: int = _DEF_TIMEOUT,
    *,
    tel: Optional[str] = None,             # <-- telefone para gerar payer/extref/idempotência
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Cria uma cobrança PIX no Mercado Pago, SEMPRE incluindo um 'payer.email' de fallback.
    - 'tel' é usado para gerar o e-mail do pagador (ex.: cliente.<digits>@example.com.br),
      external_reference padrão e uma chave de idempotência se não forem fornecidos.
    """
    try:
        # Normalizações básicas
        base = MP_API_BASE.rstrip("/")
        assert MP_ACCESS_TOKEN, "MP_ACCESS_TOKEN não definido"
        assert base.startswith("https://"), "MP_API_BASE inválida"

        tel_digits = _digits(tel)
        payer_email = _email_fallback(tel)

        # Defaults convenientes
        if not descricao:
            descricao = f"Pedido Gelinho - {tel_digits or 'cliente'}"
        if not external_reference:
            external_reference = f"carrinho_{tel_digits or 's_telefone'}_{int(datetime.now().timestamp())}"
        if not idempotency_key:
            # ✅ ID de idempotência baseado na reference (evita duplicar cobranças)
            idempotency_key = f"pix:{external_reference}"

        url = f"{base}/v1/payments"
        body = {
            "transaction_amount": _centavos_para_reais(valor_centavos),
            "description": descricao,
            "payment_method_id": "pix",
            "external_reference": external_reference,
            "payer": {
                "email": payer_email
            },
        }
        if notification_url:
            body["notification_url"] = notification_url

        hdrs = _headers({"X-Idempotency-Key": idempotency_key})

        # --- DEBUG SEGURO (não imprime token):
        print("[MP DEBUG] body:", {**body, "payer": {"email": body["payer"]["email"]}})
        print("[MP DEBUG] headers:", {k: v for k, v in hdrs.items() if k != "Authorization"})

        r = requests.post(url, headers=hdrs, json=body, timeout=timeout)
        try:
            data = r.json()
        except Exception:
            data = None

        if 200 <= r.status_code < 300:
            return True, f"OK {r.status_code}", data
        return False, f"HTTP {r.status_code}: {r.text}", data

    except Exception as e:
        return False, f"excecao: {type(e).__name__}: {e}", None


def consultar_pagamento(payment_id: str, timeout: int = _DEF_TIMEOUT) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    try:
        base = MP_API_BASE.rstrip("/")
        url = f"{base}/v1/payments/{payment_id}"
        r = requests.get(url, headers=_headers(), timeout=timeout)
        try:
            data = r.json()
        except Exception:
            data = None

        if 200 <= r.status_code < 300:
            return True, f"OK {r.status_code}", data
        return False, f"HTTP {r.status_code}: {r.text}", data
    except Exception as e:
        return False, f"excecao: {type(e).__name__}: {e}", None
