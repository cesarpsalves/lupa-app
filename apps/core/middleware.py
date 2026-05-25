"""Middleware que resolve o tenant ativo a partir do user logado."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse

from apps.core.tenant import set_current_company

if TYPE_CHECKING:
    from apps.companies.models import Company


class TenantMiddleware:
    """Resolve `request.company` e armazena na ContextVar.

    Ordem de resolução:
    1. `request.session["active_company_id"]` (escolha explícita do user)
    2. Primeira `Membership` ativa do user (fallback)
    3. None → todas as queries multi-tenant retornam vazio
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        company = self._resolve(request)
        request.company = company  # type: ignore[attr-defined]
        set_current_company(company)
        try:
            return self.get_response(request)
        finally:
            set_current_company(None)

    @staticmethod
    def _resolve(request: HttpRequest) -> Company | None:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None

        # Import local para evitar ciclo (companies → core → companies).
        from apps.companies.models import Company, Membership

        company_id = request.session.get("active_company_id")
        if company_id:
            company = Company.objects.filter(pk=company_id).first()
            if (
                company
                and Membership.all_objects.filter(
                    company=company, user=user, is_active=True
                ).exists()
            ):
                return company

        membership = (
            Membership.all_objects.filter(user=user, is_active=True)
            .select_related("company")
            .order_by("created_at")
            .first()
        )
        if membership:
            request.session["active_company_id"] = membership.company_id
            return membership.company
        return None
