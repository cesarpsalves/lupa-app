from __future__ import annotations

from django.contrib import admin

from .models import Ticket, TicketItem, TicketStatusLog


class TicketItemInline(admin.TabularInline):
    model = TicketItem
    extra = 0
    autocomplete_fields = ("service",)
    fields = ("description", "service", "unit_price", "quantity", "total")
    readonly_fields = ("total",)


class TicketStatusLogInline(admin.TabularInline):
    model = TicketStatusLog
    extra = 0
    readonly_fields = ("from_status", "to_status", "user", "note", "created_at")
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("code", "company", "client", "status", "total", "scheduled_at")
    list_filter = ("status", "company")
    search_fields = ("code", "client__name")
    autocomplete_fields = ("company", "client")
    readonly_fields = ("code", "subtotal", "total", "created_at", "updated_at")
    inlines = [TicketItemInline, TicketStatusLogInline]

    def get_queryset(self, request):
        return (
            self.model.all_objects.all()
            .select_related("company", "client")
            .prefetch_related("items", "payments")
        )
