from __future__ import annotations

from django.urls import path

from . import views

app_name = "cashflow"

urlpatterns = [
    path("", views.cashflow_list, name="list"),
    path("novo/", views.cashflow_create, name="create"),
    path("<int:pk>/excluir/", views.cashflow_delete, name="delete"),
]
