"""Decorators e helpers de RBAC por papel dentro da empresa."""
from __future__ import annotations

from functools import wraps
from typing import Callable

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse


def role_required(*allowed_roles: str) -> Callable:
    """View decorator: exige que o user tenha um dos roles na empresa ativa.

    Uso:
        @role_required("owner", "manager")
        def edit_billing(request): ...
    """

    def decorator(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
        @wraps(view)
        @login_required
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            company = getattr(request, "company", None)
            if company is None:
                raise PermissionDenied("Sem empresa ativa.")

            from apps.companies.models import Membership

            membership = Membership.all_objects.filter(
                company=company,
                user=request.user,
                is_active=True,
            ).first()
            if not membership or membership.role not in allowed_roles:
                raise PermissionDenied("Você não tem permissão para esta ação.")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
