from __future__ import annotations

from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("kind", "ticket", "company", "created_at")
    list_filter = ("kind", "company")
    search_fields = ("ticket__code",)
    autocomplete_fields = ("company", "ticket")
    readonly_fields = ("public_token", "created_at", "updated_at")

    def get_queryset(self, request):
        return self.model.all_objects.all().select_related("company", "ticket")
