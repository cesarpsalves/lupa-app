"""CRUD HTMX do Catálogo de Serviços."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import ServiceForm
from .models import Service


@login_required
@require_http_methods(["GET"])
def service_list(request: HttpRequest) -> HttpResponse:
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")

    show_archived = request.GET.get("archived") == "1"
    qs = Service.objects.all()
    if not show_archived:
        qs = qs.filter(is_active=True)

    services = list(qs.order_by("name"))
    return render(
        request,
        "catalog/list.html",
        {
            "services": services,
            "show_archived": show_archived,
            "total": len(services),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def service_create(request: HttpRequest) -> HttpResponse:
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")

    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.company = request.company  # type: ignore[attr-defined]
            service.save()
            messages.success(request, f"Serviço {service.name} criado.")
            return redirect("catalog:list")
    else:
        form = ServiceForm()
    return render(request, "catalog/form.html", {"form": form, "mode": "create"})


@login_required
@require_http_methods(["GET", "POST"])
def service_update(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")

    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado.")
            return redirect("catalog:list")
    else:
        form = ServiceForm(instance=service)
    return render(
        request,
        "catalog/form.html",
        {"form": form, "mode": "update", "service": service},
    )


@login_required
@require_http_methods(["POST"])
def service_toggle_active(request: HttpRequest, pk: int) -> HttpResponse:
    """Arquivar (soft) ou reativar serviço."""
    if not request.company:  # type: ignore[attr-defined]
        return redirect("app:onboarding")

    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save(update_fields=["is_active", "updated_at"])
    label = "arquivado" if not service.is_active else "reativado"
    messages.info(request, f"Serviço {service.name} {label}.")
    if request.htmx:  # type: ignore[attr-defined]
        return HttpResponse(status=204, headers={"HX-Redirect": reverse("catalog:list")})
    return redirect("catalog:list")
