"""Catálogo: serviços (e produtos a partir do L3)."""
from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantModel


class Service(TenantModel):
    name = models.CharField("nome", max_length=120)
    description = models.TextField("descrição", blank=True)
    base_price = models.DecimalField(
        "preço base",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    duration_minutes = models.PositiveIntegerField("duração (min)", default=60)
    is_active = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "serviço"
        verbose_name_plural = "serviços"
        ordering = ["name"]
        indexes = [models.Index(fields=["company", "is_active"])]

    def __str__(self) -> str:
        return self.name


class Product(TenantModel):
    """Produto vendido pela empresa (L3 — loja). Implementação básica desde o
    dia 0 pra não migrar schema depois."""

    name = models.CharField("nome", max_length=120)
    sku = models.CharField("SKU", max_length=40, blank=True)
    price = models.DecimalField("preço", max_digits=10, decimal_places=2)
    stock = models.IntegerField("estoque", default=0)
    is_active = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["name"]
        indexes = [models.Index(fields=["company", "sku"])]

    def __str__(self) -> str:
        return self.name
