from __future__ import annotations

from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    path("", views.agenda_day, name="day"),
    path("semana/", views.agenda_week, name="week"),
]
