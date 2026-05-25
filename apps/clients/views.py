"""CRUD HTMX de Clientes — list + busca + create + update + detail + delete (soft)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.core.validators import format_phone, normalize_document

from .forms import ClientForm
from .models import Client


def _format_for_display(client: Client) -> None:
    """Anota campos formatados pra exibição (não persiste)."""
    client.display_phone = format_phone(client.phone) if client.phone else ""  # type: ignore[attr-defined]
    client.display_document = normalize_document(client.document) if client.document else ""  # type: ignore[attr-defined]


@login_required
@require_http_methods(["GET"])
def client_list(request: HttpRequest) -> HttpResponse:
    """Lista paginada com busca."""
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")

    q = (request.GET.get("q") or "").strip()
    qs = Client.objects.filter(is_active=True)
    if q:
        digits = "".join(c for c in q if c.isdigit())
        filters = Q(name__icontains=q) | Q(email__icontains=q)
        if digits:
            filters |= Q(phone__icontains=digits) | Q(document__icontains=digits)
        qs = qs.filter(filters)

    clients = list(qs.order_by("name")[:50])
    for c in clients:
        _format_for_display(c)

    template = "clients/_results.html" if request.htmx else "clients/list.html"  # type: ignore[attr-defined]
    return render(
        request,
        template,
        {"clients": clients, "q": q, "total": len(clients)},
    )


@login_required
@require_http_methods(["GET", "POST"])
def client_create(request: HttpRequest) -> HttpResponse:
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")

    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.company = request.company  # type: ignore[attr-defined]
            client.save()
            messages.success(request, f"Cliente {client.name} criado.")
            return redirect("clients:detail", pk=client.pk)
    else:
        form = ClientForm()
    return render(request, "clients/form.html", {"form": form, "mode": "create"})


@login_required
@require_http_methods(["GET"])
def client_detail(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")
    client = get_object_or_404(Client, pk=pk, is_active=True)
    _format_for_display(client)
    tickets = client.tickets.order_by("-created_at")[:20]
    return render(
        request,
        "clients/detail.html",
        {"client": client, "tickets": tickets},
    )


@login_required
@require_http_methods(["GET", "POST"])
def client_update(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")
    client = get_object_or_404(Client, pk=pk, is_active=True)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Alterações salvas.")
            return redirect("clients:detail", pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(
        request,
        "clients/form.html",
        {"form": form, "mode": "update", "client": client},
    )


@login_required
@require_http_methods(["POST"])
def client_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft delete — marca como inativo, preserva histórico financeiro."""
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")
    client = get_object_or_404(Client, pk=pk, is_active=True)
    client.is_active = False
    client.save(update_fields=["is_active", "updated_at"])
    messages.info(request, f"Cliente {client.name} arquivado.")
    if request.htmx:  # type: ignore[attr-defined]
        return HttpResponse(status=204, headers={"HX-Redirect": reverse("clients:list")})
    return redirect("clients:list")
