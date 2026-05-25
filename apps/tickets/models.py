"""Atendimentos — núcleo do app.

Um atendimento agrega cliente + serviços + agendamento + pagamentos.
Estado controlado por máquina de estado (ver state_machine.py).
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import TenantModel


class TicketStatus(models.TextChoices):
    DRAFT = "draft", "Orçamento"
    CONFIRMED = "confirmed", "Confirmado"
    IN_PROGRESS = "in_progress", "Em execução"
    COMPLETED = "completed", "Concluído"
    FINALIZED = "finalized", "Finalizado"
    CANCELLED = "cancelled", "Cancelado"


def _generate_ticket_code() -> str:
    """Código humano para o ticket. Formato: LUPA-YYYY-NNNNNN.

    Implementação segura contra race: usa transaction + select_for_update no
    pivot. Pra MVP, dá pra usar contador simples por tenant; aqui usamos
    timestamp + random como fallback portátil.
    """
    import secrets

    year = timezone.now().year
    suffix = secrets.token_hex(3).upper()  # 6 hex chars
    return f"LUPA-{year}-{suffix}"


class Ticket(TenantModel):
    code = models.CharField(
        "código",
        max_length=20,
        unique=True,
        default=_generate_ticket_code,
        editable=False,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="cliente",
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.DRAFT,
        db_index=True,
    )
    scheduled_at = models.DateTimeField("agendado para", null=True, blank=True, db_index=True)
    duration_minutes = models.PositiveIntegerField("duração (min)", default=60)
    location = models.CharField("local", max_length=200, blank=True)
    notes = models.TextField("observações", blank=True)

    subtotal = models.DecimalField(
        "subtotal", max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    discount = models.DecimalField(
        "desconto", max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField("total", max_digits=10, decimal_places=2, default=Decimal("0.00"))

    metadata = models.JSONField("dados extras", default=dict, blank=True)

    class Meta:
        verbose_name = "atendimento"
        verbose_name_plural = "atendimentos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "status", "scheduled_at"]),
            models.Index(fields=["company", "client"]),
            models.Index(fields=["company", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.code

    @transaction.atomic
    def recalculate_totals(self) -> None:
        items = self.items.aggregate(total=models.Sum("total"))["total"] or Decimal("0.00")
        self.subtotal = items
        self.total = max(items - self.discount, Decimal("0.00"))
        self.save(update_fields=["subtotal", "total", "updated_at"])


class TicketItem(TenantModel):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="items", verbose_name="atendimento"
    )
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ticket_items",
    )
    description = models.CharField("descrição", max_length=200)
    unit_price = models.DecimalField("preço unitário", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("quantidade", default=1)
    total = models.DecimalField("total", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "item do atendimento"
        verbose_name_plural = "itens do atendimento"

    def save(self, *args, **kwargs) -> None:
        self.total = (self.unit_price or Decimal("0")) * self.quantity
        super().save(*args, **kwargs)


class TicketStatusLog(TenantModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_transitions",
    )
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "histórico de status"
        verbose_name_plural = "históricos de status"
        ordering = ["-created_at"]
