"""Fixtures globais disponíveis em todos os testes."""
from __future__ import annotations

import pytest

from apps.core.tenant import set_current_company


@pytest.fixture(autouse=True)
def _reset_tenant_between_tests():
    """Garante que nenhum teste vaze tenant ativo pro próximo."""
    set_current_company(None)
    yield
    set_current_company(None)


@pytest.fixture
def user(db):
    from apps.accounts.models import User

    return User.objects.create_user(
        email="paulo@example.com",
        password="Senha-Forte-123",
        first_name="Paulo",
    )


@pytest.fixture
def niche(db):
    from apps.companies.models import NichePreset

    return NichePreset.objects.create(
        slug="fotografo",
        name="Fotógrafo",
        ticket_label="Ensaio",
        is_active=True,
    )


@pytest.fixture
def company(db, niche):
    from apps.companies.models import Company

    return Company.objects.create(name="Estúdio Bruno", niche=niche)


@pytest.fixture
def membership(db, user, company):
    from apps.companies.models import Membership, Role

    return Membership.objects.create(
        company=company,
        user=user,
        role=Role.OWNER,
    )


@pytest.fixture
def tenant_scope(company):
    """Define o tenant ativo durante o teste."""
    from apps.core.tenant import company_scope

    with company_scope(company):
        yield company
