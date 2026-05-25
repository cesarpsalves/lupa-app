"""Configurações de produção. Falha fechado em segredos ausentes."""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import env

DEBUG = False

# ── HTTPS ───────────────────────────────────────────────────
# SECURE_SSL_REDIRECT e SECURE_HSTS_SECONDS já vêm de env() via base.py.
# Em prod o env-file setta True/31536000. Durante o bootstrap do primeiro
# deploy (HTTP-only, antes do Certbot), o env-file de bootstrap setta False/0.
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)

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
