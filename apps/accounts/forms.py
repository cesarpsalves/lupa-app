from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from apps.core.validators import only_digits, validate_phone_br

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )


class SignupForm(UserCreationForm):
    first_name = forms.CharField(
        label="Como podemos te chamar?",
        max_length=120,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    phone = forms.CharField(
        label="WhatsApp",
        required=False,
        max_length=20,
        help_text="Opcional. Pra avisos importantes do app.",
        widget=forms.TextInput(
            attrs={
                "data-mask": "phone",
                "inputmode": "numeric",
                "autocomplete": "tel-national",
                "placeholder": "(11) 91234-5678",
            }
        ),
    )
    accept_terms = forms.BooleanField(
        label="Li e aceito os termos de uso e a política de privacidade.",
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "phone", "password1", "password2")

    def clean_phone(self) -> str:
        raw = self.cleaned_data.get("phone", "")
        if not raw:
            return ""
        validate_phone_br(raw)
        return only_digits(raw)
