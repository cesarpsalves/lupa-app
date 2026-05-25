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

STEPS = [
    {
        "number": "01",
        "title": "Agende",
        "body": "Cadastre cliente, serviço e horário em menos de 1 minuto.",
    },
    {
        "number": "02",
        "title": "Cobre o sinal",
        "body": "Defina a porcentagem padrão. Saldo registrado pra cobrar depois.",
    },
    {
        "number": "03",
        "title": "Atenda",
        "body": "Marque como concluído, receba o saldo, gere o cupom em PDF.",
    },
    {
        "number": "04",
        "title": "Acompanhe",
        "body": "Caixa atualizado em tempo real. Lucro do mês num toque.",
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
        "steps": STEPS,
        "waitlist_top": _waitlist_counters(),
        "waitlist_form": WaitlistForm(),
    }
    return render(request, "public/landing.html", context)


@require_http_methods(["POST"])
def waitlist_subscribe(request: HttpRequest) -> HttpResponse:
    form = WaitlistForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        # Idempotente: se já estiver na lista, não tenta inserir novamente
        # (evita IntegrityError dentro de ATOMIC_REQUESTS).
        already_exists = WaitlistEntry.objects.filter(
            niche_slug=instance.niche_slug,
            email=instance.email,
        ).exists()
        if already_exists:
            messages.info(
                request,
                "Esse email já está na lista — vamos te avisar assim que estiver disponível.",
            )
        else:
            instance.save()
            messages.success(
                request,
                "Tudo certo! Avisamos por email quando abrirmos pro seu nicho.",
            )
        if request.htmx:  # type: ignore[attr-defined]
            return render(request, "public/_waitlist_success.html")
        return landing(request)

    if request.htmx:  # type: ignore[attr-defined]
        return render(
            request,
            "public/_waitlist_form.html",
            {"waitlist_form": form},
            status=422,
        )
    return landing(request)
