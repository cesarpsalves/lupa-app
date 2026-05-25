"""Managers e QuerySets multi-tenant.

`TenantManager` aplica `.filter(company=current_company)` automaticamente em
todo `Model.objects` que herda de `TenantModel`. Se nenhum tenant estiver
ativo, retorna `none()` — **falha fechado**, nunca exibindo dados de outros.

Para casos legítimos sem tenant ativo (admin Django, jobs cross-tenant), use
`Model.all_objects` (manager paralelo sem filtro).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from apps.core.tenant import get_current_company

if TYPE_CHECKING:
    from apps.companies.models import Company


class TenantQuerySet(models.QuerySet):
    """QuerySet com helper explícito para escolher empresa."""

    def for_company(self, company: Company) -> TenantQuerySet:
        return self.filter(company=company)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):  # type: ignore[misc]
    """Manager padrão que filtra por tenant ativo na thread-local.

    - Com tenant ativo: retorna apenas registros daquela empresa.
    - Sem tenant ativo: retorna `none()` para evitar vazamento.
    """

    use_in_migrations = False

    def get_queryset(self) -> TenantQuerySet:  # type: ignore[override]
        qs: TenantQuerySet = super().get_queryset()  # type: ignore[assignment]
        company = get_current_company()
        if company is None:
            return qs.none()
        return qs.filter(company=company)


class AllObjectsManager(models.Manager):
    """Manager sem filtro de tenant — para uso em admin e jobs globais."""

    use_in_migrations = True
