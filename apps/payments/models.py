"""Pagamentos — sinal, saldo, pagamento único."""
from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantModel


class PaymentKind(models.TextChoices):
    DEPOSIT = "deposit", "Sinal"
    BALANCE = "balance", "Saldo"
    FULL = "full", "Pagamento único"
    REFUND = "refund", "Devolução"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    PAID = "paid", "Pago"
    CANCELLED = "cancelled", "Cancelado"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Dinheiro"
    PIX = "pix", "PIX"
    CARD = "card", "Cartão"
    TRANSFER = "transfer", "Transferência"
    OTHER = "other", "Outro"


class Payment(TenantModel):
    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="atendimento",
    )
    kind = models.CharField("tipo", max_length=10, choices=PaymentKind.choices)
    status = models.CharField(
        "status",
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    amount = models.DecimalField(
        "valor", max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    due_date = models.DateField("vence em", null=True, blank=True)
    paid_at = models.DateTimeField("pago em", null=True, blank=True)
    method = models.CharField(
        "método",
        max_length=10,
        choices=PaymentMethod.choices,
        blank=True,
    )

    class Meta:
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"
        ordering = ["due_date", "created_at"]
        indexes = [
            models.Index(fields=["company", "status", "due_date"]),
            models.Index(fields=["company", "ticket"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} R$ {self.amount}"
