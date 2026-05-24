from __future__ import annotations

from django import forms

from apps.core.validators import (
    normalize_document,
    only_digits,
    validate_cpf_or_cnpj,
)

from .models import Company


class CompanyForm(forms.ModelForm):
    """Edição da empresa (workspace) — perfil, logo, documento."""

    document = forms.CharField(
        label="CPF/CNPJ",
        required=False,
        max_length=18,
        widget=forms.TextInput(
            attrs={
                "data-mask": "doc",
                "inputmode": "numeric",
                "autocomplete": "off",
                "placeholder": "000.000.000-00 ou 00.000.000/0000-00",
            }
        ),
    )

    class Meta:
        model = Company
        fields = ("name", "document", "logo")
        labels = {"name": "Nome do negócio"}
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Ex.: Estúdio Bruno Foto", "autocomplete": "organization"}
            ),
        }

    def clean_document(self) -> str:
        raw = self.cleaned_data.get("document", "")
        if not raw:
            return ""
        validate_cpf_or_cnpj(raw)
        return only_digits(raw)

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo and hasattr(logo, "size"):
            # 2 MB max
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Logo muito grande. Máximo 2 MB.")
            valid_content_types = {"image/png", "image/jpeg", "image/webp"}
            if hasattr(logo, "content_type") and logo.content_type not in valid_content_types:
                raise forms.ValidationError("Formato não suportado. Use PNG, JPG ou WebP.")
        return logo

    @property
    def document_display(self) -> str:
        raw = self.initial.get("document") or self["document"].value() or ""
        return normalize_document(raw) if raw else ""
