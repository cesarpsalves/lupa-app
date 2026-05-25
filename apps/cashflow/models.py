"""Caixa — movimentos de entrada e saída.

Movimentos automáticos (vindos de Payment marcado como `paid`) e manuais
(saídas tipo combustível, equipamento) coexistem aqui.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantModel


class CashflowDirection(models.TextChoices):
    IN = "in", "Entrada"
    OUT = "out", "Saída"


class CashflowEntry(TenantModel):
    direction = models.CharField(
        "tipo", max_length=3, choices=CashflowDirection.choices, db_index=True
    )
    amount = models.DecimalField("valor", max_digits=10, decimal_places=2, default=Decimal("0.00"))
    occurred_at = models.DateField("data", db_index=True)
    description = models.CharField("descrição", max_length=200)
    category = models.CharField(
        "categoria",
        max_length=40,
        blank=True,
        help_text="Ex.: combustível, equipamento, sinal, saldo",
    )
    payment = models.OneToOneField(
        "payments.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cashflow_entry",
        help_text="Preenchido em movimentos automáticos. Vazio em manuais.",
    )

    class Meta:
        verbose_name = "movimento de caixa"
        verbose_name_plural = "movimentos de caixa"
        ordering = ["-occurred_at", "-created_at"]
        indexes = [
            models.Index(fields=["company", "occurred_at"]),
            models.Index(fields=["company", "direction", "occurred_at"]),
        ]

    def __str__(self) -> str:
        sign = "+" if self.direction == CashflowDirection.IN else "-"
        return f"{sign}R$ {self.amount} {self.description}"

    @property
    def is_manual(self) -> bool:
        return self.payment_id is None
