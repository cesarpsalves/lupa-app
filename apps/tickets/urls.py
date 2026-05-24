from __future__ import annotations

from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.ticket_list, name="list"),
    path("novo/", views.ticket_new_client, name="new_client"),
    path("novo/servicos/", views.ticket_new_services, name="new_services"),
    path("novo/agenda/", views.ticket_new_schedule, name="new_schedule"),
    path("novo/pagamento/", views.ticket_new_payment, name="new_payment"),
    path("novo/cancelar/", views.ticket_wizard_cancel, name="wizard_cancel"),
    path("<int:pk>/", views.ticket_detail, name="detail"),
    path("<int:pk>/transicao/", views.ticket_transition, name="transition"),
    path("pagamentos/<int:pk>/marcar-pago/", views.payment_mark_paid, name="payment_mark_paid"),
]
