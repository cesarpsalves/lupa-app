"""Context processors disponíveis em todos os templates."""

from __future__ import annotations

from django.http import HttpRequest


def current_company(request: HttpRequest) -> dict:
    """Expõe a empresa ativa pros templates como `{{ current_company }}`."""
    return {"current_company": getattr(request, "company", None)}
