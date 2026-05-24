from __future__ import annotations

from django.contrib import admin

from .models import CashflowEntry


@admin.register(CashflowEntry)
class CashflowEntryAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "direction", "amount", "description", "category", "company")
    list_filter = ("direction", "category", "company")
    search_fields = ("description",)
    autocomplete_fields = ("company", "payment")
    date_hierarchy = "occurred_at"

    def get_queryset(self, request):
        return self.model.all_objects.all().select_related("company", "payment")
