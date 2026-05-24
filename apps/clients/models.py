"""Clientes da empresa."""
from __future__ import annotations

from django.db import models

from apps.core.models import TenantModel


class Client(TenantModel):
    name = models.CharField("nome", max_length=120)
    phone = models.CharField("telefone", max_length=20, blank=True, db_index=True)
    email = models.EmailField("email", blank=True)
    document = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    notes = models.TextField("observações", blank=True)
    is_active = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["company", "name"]),
            models.Index(fields=["company", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name
