from __future__ import annotations

from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "kind", "status", "amount", "due_date", "paid_at")
    list_filter = ("kind", "status", "method", "company")
    search_fields = ("ticket__code",)
    autocomplete_fields = ("company", "ticket")
    date_hierarchy = "due_date"

    def get_queryset(self, request):
        return self.model.all_objects.all().select_related("company", "ticket")
