from __future__ import annotations

from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("waitlist/", views.waitlist_subscribe, name="waitlist_subscribe"),
    path("app/", views.dashboard_placeholder, name="dashboard_placeholder"),
]
