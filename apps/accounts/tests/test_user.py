from __future__ import annotations

import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_create_user_normalizes_email():
    user = User.objects.create_user(email="PAULO@EXAMPLE.com", password="Senha-Forte-123")
    assert user.email == "PAULO@example.com"
    assert user.check_password("Senha-Forte-123")
    assert not user.is_staff


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x")


@pytest.mark.django_db
def test_superuser_flags_enforced():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin@example.com",
            password="x",
            is_staff=False,
        )


@pytest.mark.django_db
def test_display_name_falls_back_to_email_local():
    user = User.objects.create_user(email="paulo@example.com", password="Senha-Forte-123")
    assert user.display_name == "paulo"
    user.first_name = "Paulo"
    assert user.display_name == "Paulo"
