from __future__ import annotations

from django import forms

from apps.companies.models import Company, ProfileLevel


class OnboardingCompanyForm(forms.ModelForm):
    profile_level = forms.ChoiceField(
        label="Como você atende?",
        choices=ProfileLevel.choices,
        widget=forms.RadioSelect,
        initial=ProfileLevel.L1,
    )

    class Meta:
        model = Company
        fields = ("name", "profile_level", "document")
        labels = {
            "name": "Nome do negócio",
            "document": "CPF/CNPJ (opcional)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex.: Estúdio Bruno Foto"}),
            "document": forms.TextInput(attrs={"placeholder": "Só números"}),
        }
