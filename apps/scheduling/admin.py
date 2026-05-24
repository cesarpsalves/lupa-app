from __future__ import annotations

from django.contrib import admin

from .models import ScheduleEvent


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ("__str__", "company", "starts_at", "ends_at", "is_blocking")
    list_filter = ("is_blocking", "company")
    autocomplete_fields = ("company", "ticket")
    date_hierarchy = "starts_at"

    def get_queryset(self, request):
        return self.model.all_objects.all().select_related("company", "ticket")
