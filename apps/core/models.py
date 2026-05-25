"""Modelos abstratos compartilhados por todas as apps de tenant.

`TimestampedModel` → `created_at` / `updated_at` automáticos.
`TenantModel` → herda `Timestamped` + FK obrigatória pra Company + manager filtrado.
"""

from __future__ import annotations

from django.db import models

from apps.core.managers import AllObjectsManager, TenantManager


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = "created_at"


class TenantModel(TimestampedModel):
    """Modelo base para tudo que pertence a uma empresa (tenant).

    Subclasses ganham:
    - FK `company` (PROTECT — não apagar empresa com dados ativos)
    - Manager `objects` filtrado pelo tenant ativo
    - Manager `all_objects` sem filtro (uso restrito a admin/jobs)
    """

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.PROTECT,
        db_index=True,
        related_name="+",
    )

    objects = TenantManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
