from __future__ import annotations

from django.contrib import admin

from .models import WaitlistEntry


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ("email", "niche_slug", "name", "source", "created_at")
    list_filter = ("niche_slug", "source")
    search_fields = ("email", "name")
    readonly_fields = ("created_at", "updated_at")
