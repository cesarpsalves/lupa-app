from __future__ import annotations

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.service_list, name="list"),
    path("novo/", views.service_create, name="create"),
    path("<int:pk>/editar/", views.service_update, name="update"),
    path("<int:pk>/arquivar/", views.service_toggle_active, name="toggle_active"),
]
