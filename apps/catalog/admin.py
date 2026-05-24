from __future__ import annotations

from django.contrib import admin

from .models import Product, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "base_price", "duration_minutes", "is_active")
    list_filter = ("is_active", "company")
    search_fields = ("name",)
    autocomplete_fields = ("company",)

    def get_queryset(self, request):
        return self.model.all_objects.all().select_related("company")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "sku", "price", "stock", "is_active")
    list_filter = ("is_active", "company")
    search_fields = ("name", "sku")
    autocomplete_fields = ("company",)

    def get_queryset(self, request):
        return self.model.all_objects.all().select_related("company")
