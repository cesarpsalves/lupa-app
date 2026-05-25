from __future__ import annotations

from decimal import Decimal

from django import forms

from .models import CashflowDirection, CashflowEntry


class CashflowEntryForm(forms.ModelForm):
    """Movimento manual de caixa — entrada/saída sem ligação com Payment."""

    class Meta:
        model = CashflowEntry
        fields = ("direction", "amount", "occurred_at", "description", "category")
        labels = {
            "direction": "Tipo",
            "amount": "Valor (R$)",
            "occurred_at": "Data",
            "description": "Descrição",
            "category": "Categoria",
        }
        widgets = {
            "direction": forms.RadioSelect,
            "amount": forms.NumberInput(
                attrs={"step": "0.01", "inputmode": "decimal", "placeholder": "0,00"}
            ),
            "occurred_at": forms.DateInput(attrs={"type": "date"}),
            "description": forms.TextInput(attrs={"placeholder": "Ex.: Combustível"}),
            "category": forms.TextInput(attrs={"placeholder": "Ex.: operacional, equipamento"}),
        }

    def clean_amount(self) -> Decimal:
        amount = self.cleaned_data["amount"]
        if amount <= Decimal("0"):
            raise forms.ValidationError("Valor deve ser maior que zero.")
        return amount

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["direction"].initial = CashflowDirection.OUT
