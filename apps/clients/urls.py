from __future__ import annotations

from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="list"),
    path("novo/", views.client_create, name="create"),
    path("<int:pk>/", views.client_detail, name="detail"),
    path("<int:pk>/editar/", views.client_update, name="update"),
    path("<int:pk>/arquivar/", views.client_delete, name="delete"),
]
