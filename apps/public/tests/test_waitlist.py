from __future__ import annotations

import pytest
from django.urls import reverse

from apps.public.models import WaitlistEntry


@pytest.mark.django_db
def test_landing_renders(client):
    resp = client.get(reverse("public:landing"))
    assert resp.status_code == 200
    assert b"LUPA" in resp.content


@pytest.mark.django_db
def test_waitlist_subscribe_creates_entry(client):
    resp = client.post(
        reverse("public:waitlist_subscribe"),
        {"email": "barbeiro@example.com", "niche_label": "Barbeiro"},
        follow=True,
    )
    assert resp.status_code == 200
    assert WaitlistEntry.objects.filter(
        email="barbeiro@example.com",
        niche_slug="barbeiro",
    ).exists()


@pytest.mark.django_db
def test_waitlist_subscribe_duplicate_is_idempotent(client):
    WaitlistEntry.objects.create(email="x@example.com", niche_slug="barbeiro")
    resp = client.post(
        reverse("public:waitlist_subscribe"),
        {"email": "x@example.com", "niche_label": "Barbeiro"},
        follow=True,
    )
    assert resp.status_code == 200
    assert WaitlistEntry.objects.filter(email="x@example.com").count() == 1
