"""Agenda — visualizações dia e semana."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import ScheduleEvent


def _parse_date(value: str | None, default: date) -> date:
    if not value:
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return default


@login_required
@require_http_methods(["GET"])
def agenda_day(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")

    today = timezone.localdate()
    selected = _parse_date(request.GET.get("d"), today)

    events = (
        ScheduleEvent.objects.filter(starts_at__date=selected)
        .select_related("ticket", "ticket__client")
        .order_by("starts_at")
    )

    # Hours grid: 7h às 22h.
    hour_blocks = []
    for h in range(7, 23):
        hour_blocks.append(
            {
                "hour": h,
                "label": f"{h:02d}:00",
                "events": [e for e in events if timezone.localtime(e.starts_at).hour == h],
            }
        )

    return render(
        request,
        "scheduling/day.html",
        {
            "selected": selected,
            "today": today,
            "prev_day": selected - timedelta(days=1),
            "next_day": selected + timedelta(days=1),
            "hour_blocks": hour_blocks,
            "total_events": len(events),
        },
    )


@login_required
@require_http_methods(["GET"])
def agenda_week(request: HttpRequest) -> HttpResponse:
    if not getattr(request, "company", None):
        return redirect("app:onboarding")

    today = timezone.localdate()
    selected = _parse_date(request.GET.get("d"), today)
    # Inicio da semana = segunda-feira (weekday 0)
    start = selected - timedelta(days=selected.weekday())
    end = start + timedelta(days=6)

    events = (
        ScheduleEvent.objects.filter(starts_at__date__gte=start, starts_at__date__lte=end)
        .select_related("ticket", "ticket__client")
        .order_by("starts_at")
    )

    days = []
    for offset in range(7):
        d = start + timedelta(days=offset)
        day_events = [
            {
                "event": e,
                "local_time": timezone.localtime(e.starts_at),
            }
            for e in events
            if timezone.localtime(e.starts_at).date() == d
        ]
        days.append(
            {
                "date": d,
                "is_today": d == today,
                "events": day_events,
            }
        )

    return render(
        request,
        "scheduling/week.html",
        {
            "start": start,
            "end": end,
            "today": today,
            "days": days,
            "prev_week": start - timedelta(days=7),
            "next_week": start + timedelta(days=7),
        },
    )
