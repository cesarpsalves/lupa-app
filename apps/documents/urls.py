from __future__ import annotations

from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("cupom/<int:ticket_pk>/preview/", views.receipt_preview, name="receipt_preview"),
    path("cupom/<int:ticket_pk>/download/", views.receipt_download, name="receipt_download"),
]


# URLs públicas (sem prefixo /app/), incluídas em config/urls.py separadamente
public_urlpatterns = [
    path("p/cupom/<str:token>/", views.receipt_public, name="receipt_public"),
    path("p/cupom/<str:token>/pdf/", views.receipt_public_download, name="receipt_public_download"),
]
