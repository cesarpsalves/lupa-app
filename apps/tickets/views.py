"""Atendimentos — lista, detalhe, wizard de criação, transições."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.catalog.models import Service
from apps.clients.models import Client
from apps.payments.models import Payment, PaymentKind, PaymentStatus
from apps.scheduling.models import ScheduleEvent

from .forms import (
    TicketWizardStepClient,
    TicketWizardStepPayment,
    TicketWizardStepSchedule,
    TicketWizardStepServices,
)
from .models import Ticket, TicketItem, TicketStatus
from .state_machine import InvalidTransition, transition


# ─────────────────────────────────────────────────────────
# Lista + detalhe
# ─────────────────────────────────────────────────────────
@login_required
@require_http_methods(["GET"])
def ticket_list(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")

    status = request.GET.get("status") or "all"
    q = (request.GET.get("q") or "").strip()

    qs = Ticket.objects.select_related("client").order_by("-scheduled_at", "-created_at")
    if status != "all" and status in dict(TicketStatus.choices):
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(client__name__icontains=q))

    tickets = list(qs[:100])

    return render(
        request,
        "tickets/list.html",
        {
            "tickets": tickets,
            "status": status,
            "q": q,
            "statuses": TicketStatus.choices,
        },
    )


@login_required
@require_http_methods(["GET"])
def ticket_detail(request: HttpRequest, pk: int) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    ticket = get_object_or_404(
        Ticket.objects.select_related("client").prefetch_related(
            "items", "payments", "status_logs"
        ),
        pk=pk,
    )

    # transições permitidas (pra render dos botões)
    from .state_machine import TRANSITIONS

    allowed = sorted(TRANSITIONS.get(ticket.status, set()))

    # Cupom gerado (se já finalizou) — pra mostrar o link público pro cliente
    receipt = ticket.documents.filter(kind="receipt").first()

    return render(
        request,
        "tickets/detail.html",
        {
            "ticket": ticket,
            "receipt": receipt,
            "allowed_transitions": allowed,
            "TicketStatus": TicketStatus,
            "is_editable": ticket.status in _EDITABLE_STATUSES,
        },
    )


# Estados em que data/hora/local/notas ainda podem ser editados. Depois de
# concluído/finalizado/cancelado o atendimento é imutável (cupom já emitido).
_EDITABLE_STATUSES = frozenset(
    {TicketStatus.DRAFT, TicketStatus.CONFIRMED, TicketStatus.IN_PROGRESS}
)


@login_required
@require_http_methods(["GET", "POST"])
def ticket_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edita data/hora/duração/local/observações de um atendimento.

    Cliente, serviços e pagamentos NÃO mudam aqui (têm invariantes de
    cashflow/cupom) — pra isso, cancela e recria.
    """
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    ticket = get_object_or_404(Ticket.objects.select_related("client"), pk=pk)

    if ticket.status not in _EDITABLE_STATUSES:
        messages.error(
            request,
            "Este atendimento não pode mais ser editado (já concluído ou cancelado).",
        )
        return redirect("tickets:detail", pk=ticket.pk)

    if request.method == "POST":
        form = TicketWizardStepSchedule(request.POST)
        if form.is_valid():
            ticket.scheduled_at = form.cleaned_data["scheduled_at"]
            ticket.duration_minutes = form.cleaned_data["duration_minutes"]
            ticket.location = form.cleaned_data.get("location", "")
            ticket.notes = form.cleaned_data.get("notes", "")
            ticket.save(
                update_fields=[
                    "scheduled_at",
                    "duration_minutes",
                    "location",
                    "notes",
                    "updated_at",
                ]
            )
            messages.success(request, "Atendimento atualizado.")
            return redirect("tickets:detail", pk=ticket.pk)
    else:
        initial: dict = {
            "duration_minutes": ticket.duration_minutes,
            "location": ticket.location,
            "notes": ticket.notes,
        }
        if ticket.scheduled_at:
            local = timezone.localtime(ticket.scheduled_at)
            initial["scheduled_date"] = local.date()
            initial["scheduled_time"] = local.time()
        form = TicketWizardStepSchedule(initial=initial)

    return render(request, "tickets/edit.html", {"ticket": ticket, "form": form})


# ─────────────────────────────────────────────────────────
# Transições de status
# ─────────────────────────────────────────────────────────
@login_required
@require_http_methods(["POST"])
def ticket_transition(request: HttpRequest, pk: int) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    ticket = get_object_or_404(Ticket, pk=pk)
    to = request.POST.get("to", "").strip()
    try:
        transition(ticket, to=to, user=request.user)
        messages.success(request, f"Atendimento → {ticket.get_status_display()}.")
    except InvalidTransition as e:
        messages.error(request, str(e))
    return redirect("tickets:detail", pk=ticket.pk)


@login_required
@require_http_methods(["POST"])
def payment_mark_paid(request: HttpRequest, pk: int) -> HttpResponse:
    """Marca pagamento como pago (signal cria entrada no caixa)."""
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    payment = get_object_or_404(Payment, pk=pk)
    if payment.status != PaymentStatus.PAID:
        payment.status = PaymentStatus.PAID
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at", "updated_at"])
        messages.success(request, f"{payment.get_kind_display()} marcado como pago.")
    return redirect("tickets:detail", pk=payment.ticket_id)


# ─────────────────────────────────────────────────────────
# Wizard de criação (4 passos, sessão guarda estado parcial)
# ─────────────────────────────────────────────────────────
_WIZ_KEY = "lupa_ticket_wizard"


def _wizard_state(request: HttpRequest) -> dict:
    return request.session.setdefault(_WIZ_KEY, {})


def _wizard_save(request: HttpRequest, state: dict) -> None:
    request.session[_WIZ_KEY] = state
    request.session.modified = True


def _wizard_clear(request: HttpRequest) -> None:
    request.session.pop(_WIZ_KEY, None)


@login_required
@require_http_methods(["GET", "POST"])
def ticket_new_client(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    company = request.company  # type: ignore[attr-defined]

    if request.method == "POST":
        form = TicketWizardStepClient(request.POST, company=company)
        if form.is_valid():
            state = _wizard_state(request)
            state["client_id"] = form.cleaned_data["client"].pk
            _wizard_save(request, state)
            return redirect("tickets:new_services")
    else:
        state = _wizard_state(request)
        initial = {"client": state.get("client_id")} if state.get("client_id") else {}
        form = TicketWizardStepClient(initial=initial, company=company)

    return render(
        request,
        "tickets/wizard_step.html",
        {"form": form, "step": 1, "step_title": "Quem é o cliente?", "back_url": None},
    )


@login_required
@require_http_methods(["GET", "POST"])
def ticket_new_services(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    company = request.company  # type: ignore[attr-defined]

    state = _wizard_state(request)
    if "client_id" not in state:
        return redirect("tickets:new_client")

    if request.method == "POST":
        form = TicketWizardStepServices(request.POST, company=company)
        if form.is_valid():
            state["service_ids"] = [s.pk for s in form.cleaned_data["services"]]
            state["discount"] = str(form.cleaned_data.get("discount") or "0")
            _wizard_save(request, state)
            return redirect("tickets:new_schedule")
    else:
        initial = {"services": state.get("service_ids", []), "discount": state.get("discount", "0")}
        form = TicketWizardStepServices(initial=initial, company=company)

    return render(
        request,
        "tickets/wizard_step.html",
        {
            "form": form,
            "step": 2,
            "step_title": "Quais serviços?",
            "back_url": "tickets:new_client",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def ticket_new_schedule(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")

    state = _wizard_state(request)
    if "service_ids" not in state:
        return redirect("tickets:new_services")

    # Pré-popula duração com soma das services
    total_duration = Service.objects.filter(pk__in=state["service_ids"]).values_list(
        "duration_minutes", flat=True
    )
    duration_default = sum(total_duration) or 60

    if request.method == "POST":
        form = TicketWizardStepSchedule(request.POST)
        if form.is_valid():
            state["scheduled_at"] = form.cleaned_data["scheduled_at"].isoformat()
            state["duration_minutes"] = form.cleaned_data["duration_minutes"]
            state["location"] = form.cleaned_data.get("location", "")
            state["notes"] = form.cleaned_data.get("notes", "")
            _wizard_save(request, state)
            return redirect("tickets:new_payment")
    else:
        today = timezone.localdate()
        initial = {
            "scheduled_date": state.get("scheduled_at", today.isoformat())[:10]
            if state.get("scheduled_at")
            else today.isoformat(),
            "duration_minutes": state.get("duration_minutes", duration_default),
            "location": state.get("location", ""),
            "notes": state.get("notes", ""),
        }
        form = TicketWizardStepSchedule(initial=initial)

    return render(
        request,
        "tickets/wizard_step.html",
        {
            "form": form,
            "step": 3,
            "step_title": "Quando vai acontecer?",
            "back_url": "tickets:new_services",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def ticket_new_payment(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    company = request.company  # type: ignore[attr-defined]

    state = _wizard_state(request)
    if "scheduled_at" not in state:
        return redirect("tickets:new_schedule")

    # Calcula total pra mostrar
    services = list(Service.objects.filter(pk__in=state.get("service_ids", [])))
    subtotal = sum((s.base_price for s in services), Decimal("0"))
    discount = Decimal(state.get("discount", "0"))
    total = max(subtotal - discount, Decimal("0"))

    if request.method == "POST":
        form = TicketWizardStepPayment(request.POST)
        if form.is_valid():
            mode = form.cleaned_data["mode"]
            deposit_pct = form.cleaned_data.get("deposit_pct") or company.default_signal_pct
            scheduled_at = datetime.fromisoformat(state["scheduled_at"])

            with transaction.atomic():
                ticket = Ticket.objects.create(
                    company=company,
                    client_id=state["client_id"],
                    status=TicketStatus.CONFIRMED,
                    scheduled_at=scheduled_at,
                    duration_minutes=state.get("duration_minutes", 60),
                    location=state.get("location", ""),
                    notes=state.get("notes", ""),
                    discount=discount,
                )
                for svc in services:
                    TicketItem.objects.create(
                        company=company,
                        ticket=ticket,
                        service=svc,
                        description=svc.name,
                        unit_price=svc.base_price,
                        quantity=1,
                        total=svc.base_price,
                    )
                ticket.recalculate_totals()

                # Agenda
                ScheduleEvent.objects.create(
                    company=company,
                    title=f"{services[0].name if services else 'Atendimento'} — {ticket.client.name}",
                    starts_at=scheduled_at,
                    ends_at=scheduled_at + timedelta(minutes=ticket.duration_minutes),
                    ticket=ticket,
                )

                # Pagamentos
                if mode == "deposit_balance":
                    deposit_amount = (ticket.total * Decimal(deposit_pct) / Decimal(100)).quantize(
                        Decimal("0.01")
                    )
                    balance_amount = (ticket.total - deposit_amount).quantize(Decimal("0.01"))
                    Payment.objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.DEPOSIT,
                        status=PaymentStatus.PENDING,
                        amount=deposit_amount,
                        due_date=timezone.localdate(),
                    )
                    Payment.objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.BALANCE,
                        status=PaymentStatus.PENDING,
                        amount=balance_amount,
                        due_date=scheduled_at.date(),
                    )
                elif mode == "full":
                    Payment.objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.FULL,
                        status=PaymentStatus.PENDING,
                        amount=ticket.total,
                        due_date=scheduled_at.date(),
                    )
                elif mode == "paid":
                    Payment.objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.FULL,
                        status=PaymentStatus.PAID,
                        amount=ticket.total,
                        paid_at=timezone.now(),
                    )

            _wizard_clear(request)
            messages.success(request, f"Atendimento {ticket.code} criado.")
            return redirect("tickets:detail", pk=ticket.pk)
    else:
        form = TicketWizardStepPayment(initial={"deposit_pct": company.default_signal_pct})

    client = Client.objects.get(pk=state["client_id"])

    return render(
        request,
        "tickets/wizard_step.html",
        {
            "form": form,
            "step": 4,
            "step_title": "Como vai cobrar?",
            "back_url": "tickets:new_schedule",
            "preview": {
                "client": client,
                "services": services,
                "subtotal": subtotal,
                "discount": discount,
                "total": total,
                "scheduled_at": datetime.fromisoformat(state["scheduled_at"]),
            },
        },
    )


@login_required
@require_http_methods(["POST"])
def ticket_wizard_cancel(request: HttpRequest) -> HttpResponse:
    _wizard_clear(request)
    return redirect("tickets:list")
