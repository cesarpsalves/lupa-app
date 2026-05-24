"""Quando um Payment vira `paid`, registra automaticamente entrada no caixa."""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Payment, PaymentKind, PaymentStatus


@receiver(post_save, sender=Payment)
def sync_cashflow_on_payment_paid(sender, instance: Payment, **kwargs) -> None:  # noqa: ARG001
    """Cria/atualiza CashflowEntry quando o pagamento muda para `paid`.

    Devolução (`refund`) gera saída. Demais kinds geram entrada.
    Pendente/cancelado removem o movimento (caso exista).
    """
    from apps.cashflow.models import CashflowDirection, CashflowEntry

    is_paid = instance.status == PaymentStatus.PAID

    existing = CashflowEntry.all_objects.filter(payment=instance).first()

    if not is_paid:
        if existing:
            existing.delete()
        return

    direction = (
        CashflowDirection.OUT
        if instance.kind == PaymentKind.REFUND
        else CashflowDirection.IN
    )
    description = f"{instance.get_kind_display()} — {instance.ticket.code}"
    occurred_at = (instance.paid_at or timezone.now()).date()
    category = instance.kind

    if existing:
        existing.direction = direction
        existing.amount = instance.amount
        existing.occurred_at = occurred_at
        existing.description = description
        existing.category = category
        existing.save()
    else:
        CashflowEntry.all_objects.create(
            company=instance.company,
            payment=instance,
            direction=direction,
            amount=instance.amount,
            occurred_at=occurred_at,
            description=description,
            category=category,
        )
