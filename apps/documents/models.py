"""Documentos gerados — cupons, contratos."""
from __future__ import annotations

import secrets

from django.db import models

from apps.core.models import TenantModel


class DocumentKind(models.TextChoices):
    RECEIPT = "receipt", "Cupom de serviço"
    CONTRACT = "contract", "Contrato"


def _new_public_token() -> str:
    return secrets.token_urlsafe(24)


class Document(TenantModel):
    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="atendimento",
    )
    kind = models.CharField("tipo", max_length=20, choices=DocumentKind.choices)
    file = models.FileField("arquivo", upload_to="documents/%Y/%m/", blank=True)
    public_token = models.CharField(
        "token público",
        max_length=48,
        unique=True,
        default=_new_public_token,
        editable=False,
    )
    public_expires_at = models.DateTimeField("expira em", null=True, blank=True)

    class Meta:
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["company", "kind"])]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} — {self.ticket.code}"
