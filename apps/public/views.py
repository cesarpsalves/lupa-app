from __future__ import annotations

from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import WaitlistForm
from .models import WaitlistEntry

ACTIVE_NICHES = [
    {
        "slug": "fotografo",
        "label": "Fotógrafo",
        "icon": "📸",
        "tagline": "Agenda, ensaios, sinal e cupom — tudo num lugar.",
    },
]


def _waitlist_counters(min_count: int = 1) -> list[dict]:
    """Top nichos com mais interessados (para prova social na landing)."""
    rows = (
        WaitlistEntry.objects.values(niche=Lower("niche_slug"))
        .annotate(total=Count("id"))
        .filter(total__gte=min_count)
        .order_by("-total")[:6]
    )
    return [{"slug": row["niche"], "count": row["total"]} for row in rows]


def landing(request: HttpRequest) -> HttpResponse:
    context = {
        "active_niches": ACTIVE_NICHES,
        "waitlist_top": _waitlist_counters(),
        "waitlist_form": WaitlistForm(),
    }
    return render(request, "public/landing.html", context)


@require_http_methods(["POST"])
def waitlist_subscribe(request: HttpRequest) -> HttpResponse:
    form = WaitlistForm(request.POST)
    if form.is_valid():
        try:
            form.save()
            messages.success(
                request,
                "Tudo certo! Avisamos por email quando abrirmos pro seu nicho.",
            )
        except Exception:  # noqa: BLE001 — unique_together: já cadastrado
            messages.info(
                request,
                "Esse email já está na lista — vamos te avisar assim que estiver disponível.",
            )
        # HTMX devolve só o fragmento; navegação normal volta pra landing.
        if request.htmx:  # type: ignore[attr-defined]
            return render(request, "public/_waitlist_success.html")
    else:
        if request.htmx:  # type: ignore[attr-defined]
            return render(
                request,
                "public/_waitlist_form.html",
                {"waitlist_form": form},
                status=422,
            )
    return landing(request)
