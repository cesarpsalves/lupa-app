"""Views da empresa (workspace) — settings, edição de logo."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CompanyForm
from .models import Company


@login_required
@require_http_methods(["GET", "POST"])
def company_settings(request: HttpRequest) -> HttpResponse:
    company: Company | None = getattr(request, "company", None)
    if company is None:
        return redirect("app:onboarding")

    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Alterações salvas.")
            return redirect("companies:settings")
    else:
        form = CompanyForm(instance=company)

    return render(
        request,
        "companies/settings.html",
        {"form": form, "company": company},
    )


@login_required
@require_http_methods(["POST"])
def company_remove_logo(request: HttpRequest) -> HttpResponse:
    company: Company | None = getattr(request, "company", None)
    if company is None:
        return redirect("app:onboarding")
    if company.logo:
        company.logo.delete(save=False)
        company.logo = None
        company.save(update_fields=["logo", "updated_at"])
        messages.info(request, "Logo removida.")
    return redirect("companies:settings")
