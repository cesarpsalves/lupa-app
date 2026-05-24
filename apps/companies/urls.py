from __future__ import annotations

from django.urls import path

from . import views

app_name = "companies"

urlpatterns = [
    path("", views.company_settings, name="settings"),
    path("logo/remover/", views.company_remove_logo, name="remove_logo"),
]
