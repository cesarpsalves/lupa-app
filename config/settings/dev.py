"""Configurações de desenvolvimento."""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

DEBUG = True

INSTALLED_APPS = [
    *INSTALLED_APPS,
    "debug_toolbar",
    "django_extensions",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    *MIDDLEWARE,
]

INTERNAL_IPS = ["127.0.0.1"]

# Email vai pro console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Sem HTTPS em dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Debug Toolbar
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# Logging verboso em dev
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "apps": {"level": "DEBUG"},
        "django.db.backends": {
            "level": env("DJANGO_SQL_LOG_LEVEL", default="WARNING"),
        },
    },
}
