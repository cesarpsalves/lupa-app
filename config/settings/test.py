"""Configurações de teste. Banco SQLite em memória, sem rede, sem Redis real."""
from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

from .base import *  # noqa: E402, F403

DEBUG = False

# ── Banco rápido ────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    }
}

# ── Cache em memória local (não exige Redis nos testes) ─────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "lupa-test",
    }
}

# ── Email no locmem ─────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Hash de senha rápido (segurança não importa em teste) ───
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# ── Desliga Axes em testes ──────────────────────────────────
AXES_ENABLED = False

# ── Templates sem debug overhead ────────────────────────────
TEMPLATES[0]["OPTIONS"]["debug"] = False  # noqa: F405

# ── Sem HTTPS em testes ─────────────────────────────────────
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ── Logging silencioso ──────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {"level": "ERROR"},
}
