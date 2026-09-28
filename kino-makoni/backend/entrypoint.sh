#!/usr/bin/env sh
set -e

# Bazani so'nggi holatga keltirish (yangi ustun/jadval qo'shilganda ham xavfsiz)
alembic upgrade head

# DIQQAT: BITTA worker — Telegram MTProto sessiya fayli (TG_SESSION_DIR)
# jarayonlar orasida ulashilmaydi. Bir nechta worker bir xil sessiyani ochsa
# Telegram uni bloklashi yoki sessiya faylini buzishi mumkin.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips='*' \
  --workers 1
