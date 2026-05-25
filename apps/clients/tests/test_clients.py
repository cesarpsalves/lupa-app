"""CRUD + isolamento multi-tenant + máscara/validação."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.clients.models import Client
from apps.companies.models import Company, Membership, NichePreset, Role


@pytest.fixture
def niche(db):
    return NichePreset.objects.create(
        slug="fotografo", name="Fotógrafo", ticket_label="Ensaio", is_active=True
    )


@pytest.fixture
def setup_two_tenants(db, niche):
    from apps.accounts.models import User

    paulo = User.objects.create_user(
        email="paulo@x.com", password="Senha-Forte-12", first_name="Paulo"
    )
    maria = User.objects.create_user(
        email="maria@x.com", password="Senha-Forte-12", first_name="Maria"
    )
    company_a = Company.objects.create(name="Estúdio A", niche=niche)
    company_b = Company.objects.create(name="Estúdio B", niche=niche)
    Membership.objects.create(company=company_a, user=paulo, role=Role.OWNER)
    Membership.objects.create(company=company_b, user=maria, role=Role.OWNER)
    return {"paulo": paulo, "maria": maria, "company_a": company_a, "company_b": company_b}


@pytest.mark.django_db
def test_create_client_assigns_active_company(client, setup_two_tenants, settings):
    settings.ALLOWED_HOSTS = ["*"]
    client.force_login(setup_two_tenants["paulo"])
    resp = client.post(
        reverse("clients:create"),
        {"name": "Maria Silva", "phone": "11912345678", "document": "", "email": "", "notes": ""},
        follow=True,
    )
    assert resp.status_code == 200
    created = Client.all_objects.first()
    assert created is not None
    assert created.company_id == setup_two_tenants["company_a"].pk
    assert created.phone == "11912345678"  # apenas dígitos persistidos


@pytest.mark.django_db
def test_client_isolation_between_tenants(client, setup_two_tenants, settings):
    settings.ALLOWED_HOSTS = ["*"]
    Client.all_objects.create(company=setup_two_tenants["company_a"], name="Da Paulo")
    Client.all_objects.create(company=setup_two_tenants["company_b"], name="Da Maria")

    client.force_login(setup_two_tenants["paulo"])
    resp = client.get(reverse("clients:list"))
    content = resp.content.decode()
    assert "Da Paulo" in content
    assert "Da Maria" not in content


@pytest.mark.django_db
def test_create_client_rejects_invalid_document(client, setup_two_tenants, settings):
    settings.ALLOWED_HOSTS = ["*"]
    client.force_login(setup_two_tenants["paulo"])
    resp = client.post(
        reverse("clients:create"),
        {"name": "X", "document": "00000000000"},  # CPF inválido
        follow=False,
    )
    assert resp.status_code == 200  # rerender form
    # form deve ter erros
    form = resp.context["form"]
    assert form.errors.get("document")


@pytest.mark.django_db
def test_soft_delete_keeps_history(client, setup_two_tenants, settings):
    settings.ALLOWED_HOSTS = ["*"]
    client.force_login(setup_two_tenants["paulo"])
    target = Client.all_objects.create(company=setup_two_tenants["company_a"], name="Vai sair")
    resp = client.post(reverse("clients:delete", args=[target.pk]))
    assert resp.status_code in (302, 204)
    target.refresh_from_db()
    assert target.is_active is False
    # ainda existe no banco
    assert Client.all_objects.filter(pk=target.pk).exists()
