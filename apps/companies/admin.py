from __future__ import annotations

from django.contrib import admin

from .models import Company, Membership, NichePreset


@admin.register(NichePreset)
class NichePresetAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "ticket_label", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "niche", "profile_level", "is_active", "created_at")
    list_filter = ("niche", "profile_level", "is_active")
    search_fields = ("name", "slug", "document")
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "company")
    search_fields = ("user__email", "company__name")
    autocomplete_fields = ("user", "company")
