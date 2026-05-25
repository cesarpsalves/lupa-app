"""Views de documentos — preview HTML e download PDF, com link público
acessível por token (sem login) pra entregar ao cliente."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.tickets.models import Ticket

from .models import Document, DocumentKind
from .services import generate_receipt_pdf, render_receipt_html


@login_required
@require_http_methods(["GET"])
def receipt_preview(request: HttpRequest, ticket_pk: int) -> HttpResponse:
    """Preview HTML do cupom (pra ver antes de baixar)."""
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    ticket = get_object_or_404(
        Ticket.objects.select_related("client").prefetch_related("items", "payments"),
        pk=ticket_pk,
    )
    return HttpResponse(render_receipt_html(ticket))


@login_required
@require_http_methods(["GET"])
def receipt_download(request: HttpRequest, ticket_pk: int) -> FileResponse | HttpResponse:
    """Gera (ou recupera) o PDF do cupom e devolve pra download."""
    if not getattr(request, "company", None):
        return redirect("app:onboarding")
    ticket = get_object_or_404(
        Ticket.objects.select_related("client").prefetch_related("items", "payments"),
        pk=ticket_pk,
    )
    doc = (
        Document.objects.filter(ticket=ticket, kind=DocumentKind.RECEIPT)
        .order_by("-created_at")
        .first()
    )
    if doc is None or not doc.file:
        doc = generate_receipt_pdf(ticket)
    return FileResponse(
        doc.file.open("rb"),
        as_attachment=True,
        filename=f"{ticket.code}-cupom.pdf",
        content_type="application/pdf",
    )


@require_http_methods(["GET"])
def receipt_public(request: HttpRequest, token: str) -> HttpResponse:
    """Link público (sem auth) — entrega ao cliente final via WhatsApp/email."""
    try:
        doc = Document.all_objects.select_related("ticket").get(
            public_token=token,
            kind=DocumentKind.RECEIPT,
        )
    except Document.DoesNotExist as e:
        raise Http404("Documento não encontrado.") from e
    if not doc.file:
        doc = generate_receipt_pdf(doc.ticket)
    return render(
        request,
        "documents/public_receipt.html",
        {"document": doc, "ticket": doc.ticket},
    )


@require_http_methods(["GET"])
def receipt_public_download(request: HttpRequest, token: str) -> FileResponse | HttpResponse:
    """Download direto do PDF via link público."""
    try:
        doc = Document.all_objects.select_related("ticket").get(
            public_token=token,
            kind=DocumentKind.RECEIPT,
        )
    except Document.DoesNotExist as e:
        raise Http404("Documento não encontrado.") from e
    if not doc.file:
        doc = generate_receipt_pdf(doc.ticket)
    return FileResponse(
        doc.file.open("rb"),
        as_attachment=True,
        filename=f"{doc.ticket.code}-cupom.pdf",
        content_type="application/pdf",
    )
