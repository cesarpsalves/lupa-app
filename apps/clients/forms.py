from __future__ import annotations

from django import forms

from apps.core.validators import (
    only_digits,
    validate_cpf_or_cnpj,
    validate_phone_br,
)

from .models import Client


class ClientForm(forms.ModelForm):
    """Formulário com máscaras + validação real de telefone e documento."""

    phone = forms.CharField(
        label="Telefone / WhatsApp",
        required=False,
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "data-mask": "phone",
                "inputmode": "numeric",
                "autocomplete": "tel-national",
                "placeholder": "(11) 91234-5678",
            }
        ),
    )
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
        model = Client
        fields = ("name", "phone", "email", "document", "notes")
        labels = {
            "name": "Nome",
            "email": "Email",
            "notes": "Observações",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Como o cliente quer ser chamado", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "opcional@email.com", "autocomplete": "email"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Preferências, restrições, ponto de referência...",
                }
            ),
        }

    def clean_phone(self) -> str:
        raw = self.cleaned_data.get("phone", "")
        if not raw:
            return ""
        validate_phone_br(raw)
        return only_digits(raw)

    def clean_document(self) -> str:
        raw = self.cleaned_data.get("document", "")
        if not raw:
            return ""
        validate_cpf_or_cnpj(raw)
        return only_digits(raw)
