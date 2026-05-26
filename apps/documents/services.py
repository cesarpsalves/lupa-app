"""Geração de cupom em PDF via WeasyPrint.

Side-effect simples: dado um Ticket finalizado, renderiza um cupom HTML e
salva como PDF no FileField do Document. Sem dependência de browser.
"""

from __future__ import annotations

from io import BytesIO

from django.contrib.staticfiles.finders import find as find_static
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone

from apps.core.validators import format_phone, normalize_document

from .models import Document, DocumentKind


def _file_uri(path: str | None) -> str | None:
    """Converte path absoluto em file:// URI que WeasyPrint resolve."""
    if not path:
        return None
    return f"file://{path}"


def render_receipt_html(ticket) -> str:
    """Renderiza o HTML do cupom (pode ser servido como preview também)."""
    # Logo da empresa (ImageField — pode estar vazio se onboarding pulou)
    company_logo = (
        _file_uri(ticket.company.logo.path) if ticket.company.logo else None
    )
    # Logo do LUPA (asset estático — sempre presente)
    lupa_logo = _file_uri(find_static("img/logo.svg"))

    return render_to_string(
        "documents/receipt.html",
        {
            "ticket": ticket,
            "company": ticket.company,
            "client": ticket.client,
            "items": list(ticket.items.all()),
            "payments": list(ticket.payments.all()),
            "issued_at": timezone.now(),
            "company_logo": company_logo,
            "lupa_logo": lupa_logo,
            "company_document_display": normalize_document(ticket.company.document)
            if ticket.company.document
            else "",
            "client_document_display": normalize_document(ticket.client.document)
            if ticket.client.document
            else "",
            "client_phone_display": format_phone(ticket.client.phone)
            if ticket.client.phone
            else "",
        },
    )


def generate_receipt_pdf(ticket) -> Document:
    """Gera (ou atualiza) o Document do tipo `receipt` para o ticket."""
    # Import lazy: WeasyPrint exige libs do sistema (pango/cairo/gobject)
    # que podem não estar instaladas em desktops (macOS sem brew install
    # pango cairo). No CI Linux e no Docker prod elas estão presentes.
    from weasyprint import CSS, HTML

    html = render_receipt_html(ticket)
    buf = BytesIO()
    HTML(string=html).write_pdf(
        target=buf,
        stylesheets=[CSS(string="@page { size: A5; margin: 16mm; }")],
    )
    buf.seek(0)

    doc, _ = Document.objects.get_or_create(
        ticket=ticket,
        kind=DocumentKind.RECEIPT,
        defaults={"company": ticket.company},
    )
    filename = f"{ticket.code}-cupom.pdf"
    doc.file.save(filename, ContentFile(buf.read()), save=True)
    return doc
