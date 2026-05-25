"""Caixa — lista, criação manual, resumo do mês."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import CashflowEntryForm
from .models import CashflowDirection, CashflowEntry


def _parse_date(value: str | None, default: date) -> date:
    if not value:
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return default


@login_required
@require_http_methods(["GET"])
def cashflow_list(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")

    today = timezone.localdate()
    # Default: mês atual
    month_start = today.replace(day=1)
    start = _parse_date(request.GET.get("from"), month_start)
    end = _parse_date(request.GET.get("to"), today)

    qs = CashflowEntry.objects.filter(occurred_at__gte=start, occurred_at__lte=end)
    direction_filter = request.GET.get("direction")
    if direction_filter in {CashflowDirection.IN, CashflowDirection.OUT}:
        qs = qs.filter(direction=direction_filter)

    entries = list(qs.order_by("-occurred_at", "-created_at")[:200])

    # Resumo do período filtrado
    totals = CashflowEntry.objects.filter(occurred_at__gte=start, occurred_at__lte=end).aggregate(
        income=Sum("amount", filter=models_q_in()),
        expense=Sum("amount", filter=models_q_out()),
    )
    income = totals["income"] or Decimal("0.00")
    expense = totals["expense"] or Decimal("0.00")
    balance = income - expense

    # Atalhos de período
    quick_periods = [
        ("Hoje", today, today),
        ("Esta semana", today - timedelta(days=today.weekday()), today),
        ("Este mês", month_start, today),
        ("Últimos 30 dias", today - timedelta(days=30), today),
    ]

    return render(
        request,
        "cashflow/list.html",
        {
            "entries": entries,
            "start": start,
            "end": end,
            "income": income,
            "expense": expense,
            "balance": balance,
            "direction_filter": direction_filter or "all",
            "quick_periods": quick_periods,
        },
    )


def models_q_in():
    from django.db.models import Q

    return Q(direction=CashflowDirection.IN)


def models_q_out():
    from django.db.models import Q

    return Q(direction=CashflowDirection.OUT)


@login_required
@require_http_methods(["GET", "POST"])
def cashflow_create(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    company = request.company  # type: ignore[attr-defined]

    if request.method == "POST":
        form = CashflowEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.company = company
            entry.save()
            messages.success(request, "Movimento registrado.")
            return redirect("cashflow:list")
    else:
        form = CashflowEntryForm(initial={"occurred_at": timezone.localdate()})

    return render(request, "cashflow/form.html", {"form": form})


@login_required
@require_http_methods(["POST"])
def cashflow_delete(request: HttpRequest, pk: int) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    entry = get_object_or_404(CashflowEntry, pk=pk)
    if entry.payment_id is not None:
        messages.error(
            request,
            "Esse movimento vem de um pagamento. Edite no atendimento correspondente.",
        )
    else:
        entry.delete()
        messages.info(request, "Movimento removido.")
    return redirect("cashflow:list")
