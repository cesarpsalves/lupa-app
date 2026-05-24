from __future__ import annotations

from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "phone", "email", "is_active", "created_at")
    list_filter = ("is_active", "company")
    search_fields = ("name", "phone", "email", "document")
    autocomplete_fields = ("company",)
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return self.model.all_objects.all().select_related("company")
