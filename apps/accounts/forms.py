from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )


class SignupForm(UserCreationForm):
    first_name = forms.CharField(label="Como podemos te chamar?", max_length=120)
    accept_terms = forms.BooleanField(
        label="Li e aceito os termos de uso e a política de privacidade.",
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "password1", "password2")
