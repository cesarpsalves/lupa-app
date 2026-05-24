from __future__ import annotations

import pytest

from apps.accounts.models import User
from apps.companies.models import Company, Membership, NichePreset, Role


@pytest.fixture
def niche_fotografo(db):
    return NichePreset.objects.create(
        slug="fotografo",
        name="Fotógrafo",
        ticket_label="Ensaio",
        is_active=True,
    )


@pytest.mark.django_db
def test_company_slug_is_auto_generated(niche_fotografo):
    company = Company.objects.create(name="Estúdio Bruno", niche=niche_fotografo)
    assert company.slug == "estudio-bruno"


@pytest.mark.django_db
def test_company_slug_collision_is_resolved(niche_fotografo):
    Company.objects.create(name="Estúdio", niche=niche_fotografo)
    second = Company.objects.create(name="Estúdio", niche=niche_fotografo)
    assert second.slug == "estudio-2"


@pytest.mark.django_db
def test_default_signal_pct_falls_back_to_settings(niche_fotografo, settings):
    settings.LUPA_DEFAULT_SIGNAL_PCT = 40
    company = Company.objects.create(name="X", niche=niche_fotografo)
    assert company.default_signal_pct == 40


@pytest.mark.django_db
def test_membership_unique_per_user_company(niche_fotografo):
    company = Company.objects.create(name="X", niche=niche_fotografo)
    user = User.objects.create_user(email="u@example.com", password="Senha-Forte-123")
    Membership.objects.create(company=company, user=user, role=Role.OWNER)
    with pytest.raises(Exception):  # noqa: B017 — IntegrityError varia entre dbs
        Membership.objects.create(company=company, user=user, role=Role.MANAGER)
