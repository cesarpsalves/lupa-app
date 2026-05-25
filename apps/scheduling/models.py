"""Agenda — eventos vinculados (ou não) a atendimentos."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantModel


class ScheduleEvent(TenantModel):
    """Slot de agenda. Pode estar vinculado a um Ticket (caso comum) ou
    ser um bloqueio (almoço, folga, treinamento)."""

    title = models.CharField("título", max_length=120, blank=True)
    starts_at = models.DateTimeField("início", db_index=True)
    ends_at = models.DateTimeField("fim")
    is_blocking = models.BooleanField(
        "bloqueia agenda",
        default=False,
        help_text="True para folga/almoço/indisponibilidade.",
    )
    notes = models.TextField("notas", blank=True)

    ticket = models.OneToOneField(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="schedule_event",
    )

    class Meta:
        verbose_name = "evento na agenda"
        verbose_name_plural = "eventos na agenda"
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["company", "starts_at"]),
            models.Index(fields=["company", "starts_at", "ends_at"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Evento #{self.pk}"
