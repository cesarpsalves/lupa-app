from __future__ import annotations

from decimal import Decimal

from django import forms

from .models import Service


class ServiceForm(forms.ModelForm):
    base_price = forms.DecimalField(
        label="Preço base",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        localize=True,  # parseia/formata no locale pt-BR (vírgula decimal)
        widget=forms.TextInput(
            attrs={
                "placeholder": "0,00",
                "inputmode": "decimal",
            }
        ),
    )
    duration_minutes = forms.IntegerField(
        label="Duração estimada",
        min_value=1,
        max_value=24 * 60,
        widget=forms.NumberInput(attrs={"placeholder": "60", "inputmode": "numeric"}),
        help_text="Em minutos. Ajuda a sugerir intervalos na agenda.",
    )

    class Meta:
        model = Service
        fields = ("name", "base_price", "duration_minutes", "description")
        labels = {
            "name": "Nome do serviço",
            "description": "Descrição",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex.: Ensaio fotográfico individual"}),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "O que está incluso: tempo, fotos entregues, número de looks...",
                }
            ),
        }
