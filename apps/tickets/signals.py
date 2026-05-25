"""Signals do Atendimento.

Quando o ticket vira `finalized`, dispara geração automática do cupom PDF.
"""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket, TicketStatus

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Ticket)
def on_ticket_saved(sender, instance: Ticket, created: bool, **kwargs) -> None:
    """Auto-gera cupom PDF quando o ticket transita pra `finalized`."""
    if instance.status != TicketStatus.FINALIZED:
        return

    from apps.documents.models import Document, DocumentKind
    from apps.documents.services import generate_receipt_pdf

    # Idempotente: se já existe cupom, não regenera.
    has_receipt = Document.all_objects.filter(ticket=instance, kind=DocumentKind.RECEIPT).exists()
    if has_receipt:
        return

    try:
        generate_receipt_pdf(instance)
        logger.info("Cupom gerado automaticamente para %s", instance.code)
    except Exception:
        logger.exception("Falha ao gerar cupom para %s", instance.code)
