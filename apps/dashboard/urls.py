from __future__ import annotations

from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("mais/", views.more_menu, name="more"),
]
