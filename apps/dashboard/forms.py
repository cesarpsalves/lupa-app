from __future__ import annotations

from django import forms

from apps.companies.models import Company, ProfileLevel
from apps.core.validators import (
    normalize_document,
    only_digits,
    validate_cpf_or_cnpj,
)


class OnboardingCompanyForm(forms.ModelForm):
    profile_level = forms.ChoiceField(
        label="Como você atende?",
        choices=ProfileLevel.choices,
        widget=forms.RadioSelect,
        initial=ProfileLevel.L1,
    )
    document = forms.CharField(
        label="CPF/CNPJ",
        required=False,
        max_length=18,
        help_text="Opcional agora — você pode preencher depois nas configurações.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "000.000.000-00 ou 00.000.000/0000-00",
                "data-mask": "doc",
                "inputmode": "numeric",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = Company
        fields = ("name", "profile_level", "document")
        labels = {"name": "Nome do negócio"}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Estúdio Bruno Foto",
                    "autocomplete": "organization",
                }
            ),
        }

    def clean_document(self) -> str:
        raw = self.cleaned_data.get("document", "")
        if not raw:
            return ""
        # Valida (CPF ou CNPJ). Lança ValidationError com mensagem amigável.
        validate_cpf_or_cnpj(raw)
        # Persiste apenas dígitos — o display formatado vem do helper de view.
        return only_digits(raw)


def display_document(value: str) -> str:
    return normalize_document(value) if value else ""
