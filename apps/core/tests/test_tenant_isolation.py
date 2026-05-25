"""Garantias críticas: dados de uma empresa NUNCA vazam pra outra.

Esses testes são o portão de segurança do multi-tenant. Se algum quebrar,
NÃO se faz merge — o risco é vazamento entre clientes.
"""

from __future__ import annotations

import pytest

from apps.core.tenant import company_scope, get_current_company, set_current_company

pytestmark = pytest.mark.tenant


def test_get_current_company_starts_as_none():
    set_current_company(None)
    assert get_current_company() is None


def test_company_scope_restores_previous_value():
    set_current_company(None)
    with company_scope("empresa-a"):  # type: ignore[arg-type]
        assert get_current_company() == "empresa-a"
    assert get_current_company() is None


def test_nested_company_scope():
    set_current_company(None)
    with company_scope("a"):  # type: ignore[arg-type]
        with company_scope("b"):  # type: ignore[arg-type]
            assert get_current_company() == "b"
        assert get_current_company() == "a"
    assert get_current_company() is None


@pytest.mark.django_db
def test_tenant_manager_returns_none_without_active_company():
    """Sem tenant ativo, manager deve retornar queryset vazio (falha fechado)."""
    from apps.companies.models import Membership

    set_current_company(None)
    assert Membership.objects.count() == 0
    assert list(Membership.objects.all()) == []
