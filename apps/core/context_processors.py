"""Context processors disponíveis em todos os templates."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest


def current_company(request: HttpRequest) -> dict:
    """Expõe a empresa ativa pros templates como `{{ current_company }}`."""
    return {"current_company": getattr(request, "company", None)}


def analytics(request: HttpRequest) -> dict:
    """Expõe credenciais do Umami pros templates.

    Se UMAMI_WEBSITE_ID estiver vazio, o snippet não é renderizado no base.html
    (zero overhead). Em dev/test mantemos vazio pra não poluir as métricas.
    """
    return {
        "UMAMI_WEBSITE_ID": getattr(settings, "UMAMI_WEBSITE_ID", ""),
        "UMAMI_HOST": getattr(settings, "UMAMI_HOST", ""),
    }
