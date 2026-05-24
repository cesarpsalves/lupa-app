"""Modelos públicos — não pertencem a tenant.

`WaitlistEntry` registra interesse de prestadores em nichos ainda não
ativados. Quando atinge `LUPA_WAITLIST_THRESHOLD`, o nicho entra no roadmap.
"""
from __future__ import annotations

from django.db import models

from apps.core.models import TimestampedModel


class WaitlistEntry(TimestampedModel):
    niche_slug = models.SlugField(db_index=True)
    email = models.EmailField()
    name = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=40, blank=True, help_text="utm_source ou referrer")

    class Meta:
        unique_together = [("niche_slug", "email")]
        ordering = ["-created_at"]
        verbose_name = "interesse na waitlist"
        verbose_name_plural = "interesses na waitlist"

    def __str__(self) -> str:
        return f"{self.email} → {self.niche_slug}"
