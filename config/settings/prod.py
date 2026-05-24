"""Configurações de produção. Falha fechado em segredos ausentes."""
from __future__ import annotations

from .base import *  # noqa: F403
from .base import env

DEBUG = False

# ── HTTPS obrigatório ───────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS", default=31_536_000)  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ── Email via Resend ────────────────────────────────────────
EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"

# ── Validações de boot ──────────────────────────────────────
# Forçar variáveis críticas em produção. Se faltar, app não sobe.
_required = [
    "DJANGO_SECRET_KEY",
    "DATABASE_URL",
    "DJANGO_ALLOWED_HOSTS",
    "RESEND_API_KEY",
]
for _key in _required:
    if not env(_key, default=""):
        raise RuntimeError(f"Variável obrigatória em produção: {_key}")
