

import os

# === W-API ===
WAPI_TOKEN    = os.getenv("WAPI_TOKEN",    "o8bWQDnlomrsOaBF2CqnlHguBKIbX87By")
WAPI_INSTANCE = os.getenv("WAPI_INSTANCE", "LITE-F75JN4-FWW3NA")
WAPI_URL      = f"https://api.w-api.app/v1/message/send-text?instanceId={WAPI_INSTANCE}"

# === Mercado Pago ===
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "APP_USR-2137855357051440-092207-707409999b7b088b2b514fa3529c8d53-53350581")
MP_API_BASE     = os.getenv("MP_API_BASE", "https://api.mercadopago.com")

