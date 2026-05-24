from __future__ import annotations

from django import forms
from django.utils.text import slugify

from .models import WaitlistEntry


class WaitlistForm(forms.ModelForm):
    niche_label = forms.CharField(
        label="Qual sua profissão?",
        max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "ex.: barbeiro, personal trainer"}),
    )

    class Meta:
        model = WaitlistEntry
        fields = ("email", "name")
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "seu@email.com"}),
            "name": forms.TextInput(attrs={"placeholder": "Seu nome (opcional)"}),
        }
        labels = {
            "email": "Email",
            "name": "Nome",
        }

    def save(self, commit: bool = True) -> WaitlistEntry:
        instance: WaitlistEntry = super().save(commit=False)
        instance.niche_slug = slugify(self.cleaned_data["niche_label"])[:50]
        if commit:
            instance.save()
        return instance
