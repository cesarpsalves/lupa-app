from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.catalog.models import Service
from apps.clients.models import Client


class TicketWizardStepClient(forms.Form):
    client = forms.ModelChoiceField(
        label="Cliente",
        queryset=Client.objects.none(),
        empty_label="— selecionar —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields["client"].queryset = Client.objects.filter(is_active=True).order_by("name")


class TicketWizardStepServices(forms.Form):
    services = forms.ModelMultipleChoiceField(
        label="Serviços",
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    discount = forms.DecimalField(
        label="Desconto (R$)",
        min_value=Decimal("0"),
        required=False,
        initial=Decimal("0"),
        widget=forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields["services"].queryset = Service.objects.filter(is_active=True).order_by(
                "name"
            )


class TicketWizardStepSchedule(forms.Form):
    scheduled_date = forms.DateField(
        label="Data",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
    )
    scheduled_time = forms.TimeField(
        label="Hora",
        widget=forms.TimeInput(attrs={"type": "time"}),
        required=True,
    )
    duration_minutes = forms.IntegerField(
        label="Duração (min)",
        min_value=15,
        max_value=24 * 60,
        initial=60,
        widget=forms.NumberInput(attrs={"step": 15, "inputmode": "numeric"}),
    )
    location = forms.CharField(
        label="Local",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Ex.: Estúdio, ou endereço do cliente"}),
    )
    notes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self) -> dict:
        cleaned = super().clean() or {}
        d = cleaned.get("scheduled_date")
        t = cleaned.get("scheduled_time")
        if d and t:
            dt = timezone.make_aware(datetime.combine(d, t), timezone.get_current_timezone())
            cleaned["scheduled_at"] = dt
        return cleaned


class TicketWizardStepPayment(forms.Form):
    PAYMENT_MODE_CHOICES = [
        ("deposit_balance", "Sinal + Saldo"),
        ("full", "Pagamento único no final"),
        ("paid", "Já recebi tudo"),
    ]
    mode = forms.ChoiceField(
        label="Como vai cobrar?",
        choices=PAYMENT_MODE_CHOICES,
        widget=forms.RadioSelect,
        initial="deposit_balance",
    )
    deposit_pct = forms.IntegerField(
        label="% sinal",
        min_value=10,
        max_value=100,
        initial=50,
        required=False,
    )
