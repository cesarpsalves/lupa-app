"""Signals do Atendimento.

Side-effects de transição (gerar cupom, criar movimentos) ficam aqui pra
manter views finas. Importado por `apps.ready()`.
"""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket


@receiver(post_save, sender=Ticket)
def on_ticket_saved(sender, instance: Ticket, created: bool, **kwargs) -> None:  # noqa: ARG001
    """Placeholder pra hooks futuros (auto-gerar cupom no `finalized`,
    notificar cliente, etc.). Por enquanto, no-op."""
    return None
