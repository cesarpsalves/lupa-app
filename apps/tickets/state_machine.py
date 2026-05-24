"""Máquina de estado do Atendimento.

Transições legítimas. Tentativas inválidas levantam `InvalidTransition`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from .models import TicketStatus, TicketStatusLog

if TYPE_CHECKING:
    from apps.accounts.models import User

    from .models import Ticket


TRANSITIONS: dict[str, set[str]] = {
    TicketStatus.DRAFT: {TicketStatus.CONFIRMED, TicketStatus.CANCELLED},
    TicketStatus.CONFIRMED: {TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED},
    TicketStatus.IN_PROGRESS: {TicketStatus.COMPLETED, TicketStatus.CANCELLED},
    TicketStatus.COMPLETED: {TicketStatus.FINALIZED},
    TicketStatus.FINALIZED: set(),
    TicketStatus.CANCELLED: set(),
}


class InvalidTransition(Exception):
    """Tentativa de mudar pra um status não permitido a partir do atual."""


@transaction.atomic
def transition(
    ticket: "Ticket",
    *,
    to: str,
    user: "User | None" = None,
    note: str = "",
) -> "Ticket":
    """Move o ticket para o novo status, registra no log e retorna o ticket
    atualizado. Side-effects (criar cupom, marcar pagamento) ficam em signals."""
    allowed = TRANSITIONS.get(ticket.status, set())
    if to not in allowed:
        raise InvalidTransition(
            f"Transição inválida: {ticket.status} → {to}. "
            f"Permitidas a partir de {ticket.status}: {sorted(allowed) or '(nenhuma)'}"
        )

    from_status = ticket.status
    ticket.status = to
    ticket.save(update_fields=["status", "updated_at"])

    TicketStatusLog.objects.create(
        company=ticket.company,
        ticket=ticket,
        from_status=from_status,
        to_status=to,
        user=user,
        note=note,
    )
    return ticket
