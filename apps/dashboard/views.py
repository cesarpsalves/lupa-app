"""Dashboard interno + onboarding."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.cashflow.models import CashflowDirection, CashflowEntry
from apps.catalog.models import Service
from apps.clients.models import Client
from apps.companies.models import Membership, NichePreset, Role
from apps.core.tenant import set_current_company
from apps.payments.models import Payment, PaymentStatus
from apps.scheduling.models import ScheduleEvent
from apps.tickets.models import Ticket, TicketStatus

from .forms import OnboardingCompanyForm


def _has_company(user) -> bool:
    return Membership.objects.filter(user=user, is_active=True).exists()


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    if not _has_company(request.user):
        return redirect("app:onboarding")

    company = request.company  # type: ignore[attr-defined]
    today = timezone.localdate()
    month_start = today.replace(day=1)
    week_end = today + timedelta(days=6)

    # Faturamento do mês: entradas do caixa.
    revenue_month = CashflowEntry.objects.filter(
        occurred_at__gte=month_start,
        direction=CashflowDirection.IN,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # A receber: pagamentos pendentes.
    pending_aggregate = Payment.objects.filter(status=PaymentStatus.PENDING).aggregate(
        total=Sum("amount"), count=Count("id")
    )
    receivable_total = pending_aggregate["total"] or Decimal("0.00")
    receivable_count = pending_aggregate["count"] or 0

    # Tickets de hoje.
    today_tickets = (
        Ticket.objects.filter(
            scheduled_at__date=today,
        )
        .exclude(status=TicketStatus.CANCELLED)
        .select_related("client")
        .order_by("scheduled_at")[:10]
    )

    # Quantidade por dia da semana (próximos 7 dias).
    week_events = (
        ScheduleEvent.objects.filter(
            starts_at__date__gte=today,
            starts_at__date__lte=week_end,
        )
        .annotate(day=models_trunc_date("starts_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    week_counts = {row["day"]: row["total"] for row in week_events}
    week = []
    for offset in range(7):
        d = today + timedelta(days=offset)
        week.append({"date": d, "count": week_counts.get(d, 0)})

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "company": company,
            "revenue_month": revenue_month,
            "receivable_total": receivable_total,
            "receivable_count": receivable_count,
            "today_tickets": today_tickets,
            "week": week,
            "upcoming_features": [
                "Agenda",
                "Atendimentos",
                "Caixa",
                "Cupom PDF",
            ],
            "has_clients": Client.objects.exists(),
            "has_services": Service.objects.exists(),
        },
    )


def models_trunc_date(field: str):
    """Helper portátil pra `Trunc('day')` sem importar em cima."""
    from django.db.models.functions import TruncDate

    return TruncDate(field)


@login_required
def more_menu(request: HttpRequest) -> HttpResponse:
    """Menu 'Mais' do app — agrega navegação para áreas secundárias."""
    if not _has_company(request.user):
        return redirect("app:onboarding")
    return render(request, "dashboard/more.html")


@login_required
def onboarding(request: HttpRequest) -> HttpResponse:
    """Onboarding em 1 página: cria Company + Membership(owner) +
    NichePreset padrão (fotógrafo). Posteriormente vira wizard de 3 passos."""
    if _has_company(request.user):
        return redirect("app:dashboard")

    if request.method == "POST":
        form = OnboardingCompanyForm(request.POST)
        if form.is_valid():
            niche = NichePreset.objects.filter(is_active=True).first()
            if niche is None:
                niche = NichePreset.objects.create(
                    slug="fotografo",
                    name="Fotógrafo",
                    ticket_label="Ensaio",
                    is_active=True,
                )
            company = form.save(commit=False)
            company.niche = niche
            company.save()
            Membership.objects.create(
                company=company,
                user=request.user,
                role=Role.OWNER,
            )
            request.session["active_company_id"] = company.pk
            set_current_company(company)

            # Pré-popula serviços sugeridos do nicho, se houver.
            from apps.catalog.models import Service

            for service_data in niche.suggested_services or []:
                Service.objects.create(
                    company=company,
                    name=service_data.get("name", "Serviço"),
                    base_price=service_data.get("base_price", "0.00"),
                    duration_minutes=service_data.get("duration_minutes", 60),
                )

            messages.success(
                request,
                f"Tudo pronto, {request.user.display_name}! Bem-vindo ao LUPA.",
            )
            return redirect("app:dashboard")
    else:
        form = OnboardingCompanyForm()

    return render(request, "dashboard/onboarding.html", {"form": form})
