"""Popula a empresa do user com clientes, serviços e atendimentos fake.

Uso:
    python manage.py seed_demo --email admin@lupasolucoes.com
    python manage.py seed_demo --email admin@lupasolucoes.com --clean
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.cashflow.models import CashflowEntry
from apps.catalog.models import Service
from apps.clients.models import Client
from apps.companies.models import Company, Membership
from apps.core.tenant import company_scope
from apps.payments.models import Payment, PaymentKind, PaymentMethod, PaymentStatus
from apps.scheduling.models import ScheduleEvent
from apps.tickets.models import Ticket, TicketItem, TicketStatus

CLIENT_NAMES = [
    "Maria Silva",
    "João Pereira",
    "Ana Beatriz Costa",
    "Pedro Henrique Almeida",
    "Júlia Ferreira",
    "Rafael Souza",
    "Larissa Martins",
    "Lucas Oliveira",
    "Camila Rodrigues",
    "Bruno Santos",
    "Mariana Lima",
    "Carlos Eduardo",
]

CLIENT_NOTES = [
    "Prefere ensaio fim de tarde, luz dourada.",
    "Cuidado com pet do cliente (gato no estúdio).",
    "Aniversário em 12/06 — possível ensaio comemorativo.",
    "Cliente indicada pela Maria Silva.",
    "",
    "Trabalha em horário comercial, melhor agendar à noite.",
]

SERVICE_TEMPLATES = [
    {"name": "Ensaio individual", "base_price": "450.00", "duration_minutes": 90},
    {"name": "Ensaio gestante", "base_price": "650.00", "duration_minutes": 120},
    {"name": "Ensaio newborn", "base_price": "800.00", "duration_minutes": 180},
    {"name": "Cobertura de evento (até 4h)", "base_price": "1200.00", "duration_minutes": 240},
    {"name": "Book profissional", "base_price": "350.00", "duration_minutes": 60},
]


def _random_phone() -> str:
    """11 dígitos válidos: DD entre 11-21 + 9 + 8 dígitos."""
    ddd = random.choice([11, 12, 13, 21, 31, 41, 51, 61, 71, 81])
    return f"{ddd}9{random.randint(1000_0000, 9999_9999)}"


def _email_for(name: str) -> str:
    base = name.lower().split()[0]
    return f"{base}.{random.randint(100, 999)}@example.com"


class Command(BaseCommand):
    help = "Popula a empresa de um usuário com dados fake pra demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", required=True, help="Email do usuário (deve ter empresa criada)."
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Apaga clientes/serviços/tickets/pagamentos/caixa da empresa antes de popular.",
        )

    def handle(self, *args, **options):
        email = options["email"]
        clean = options["clean"]

        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist as e:
            raise CommandError(f"Usuário não encontrado: {email}") from e

        membership = (
            Membership.objects.filter(user=user, is_active=True).select_related("company").first()
        )
        if membership is None:
            raise CommandError(f"{email} não tem empresa. Faça o onboarding primeiro.")
        company: Company = membership.company
        self.stdout.write(f"Empresa: {company.name} (#{company.pk})")

        with company_scope(company):
            if clean:
                self.stdout.write(self.style.WARNING("Limpando dados anteriores…"))
                Ticket.all_objects.filter(company=company).delete()
                Client.all_objects.filter(company=company).delete()
                Service.all_objects.filter(company=company).delete()
                CashflowEntry.all_objects.filter(company=company).delete()
                ScheduleEvent.all_objects.filter(company=company).delete()

            # ── Serviços ──────────────────────────────────────
            services = []
            for tpl in SERVICE_TEMPLATES:
                svc, _ = Service.all_objects.get_or_create(
                    company=company,
                    name=tpl["name"],
                    defaults={
                        "base_price": Decimal(tpl["base_price"]),
                        "duration_minutes": tpl["duration_minutes"],
                    },
                )
                services.append(svc)
            self.stdout.write(f"  ✓ {len(services)} serviços")

            # ── Clientes ─────────────────────────────────────
            clients = []
            for name in random.sample(CLIENT_NAMES, 10):
                client = Client.all_objects.create(
                    company=company,
                    name=name,
                    phone=_random_phone(),
                    email=_email_for(name) if random.random() > 0.4 else "",
                    notes=random.choice(CLIENT_NOTES),
                )
                clients.append(client)
            self.stdout.write(f"  ✓ {len(clients)} clientes")

            # ── Atendimentos: distribuídos no passado/futuro próximos ──
            now = timezone.now()
            tickets_created = 0
            for _ in range(12):
                client = random.choice(clients)
                service = random.choice(services)
                # data: -20 a +14 dias
                offset_days = random.randint(-20, 14)
                hour = random.choice([9, 10, 11, 14, 15, 16, 17])
                scheduled = (now + timedelta(days=offset_days)).replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                # status conforme passado/futuro
                if offset_days < -5:
                    status = random.choice(
                        [TicketStatus.FINALIZED, TicketStatus.FINALIZED, TicketStatus.CANCELLED]
                    )
                elif offset_days < 0:
                    status = random.choice(
                        [TicketStatus.COMPLETED, TicketStatus.FINALIZED, TicketStatus.IN_PROGRESS]
                    )
                else:
                    status = random.choice(
                        [TicketStatus.DRAFT, TicketStatus.CONFIRMED, TicketStatus.CONFIRMED]
                    )

                ticket = Ticket.all_objects.create(
                    company=company,
                    client=client,
                    status=status,
                    scheduled_at=scheduled,
                    duration_minutes=service.duration_minutes,
                )
                TicketItem.all_objects.create(
                    company=company,
                    ticket=ticket,
                    service=service,
                    description=service.name,
                    unit_price=service.base_price,
                    quantity=1,
                    total=service.base_price,
                )
                ticket.recalculate_totals()

                # cria evento na agenda também
                ScheduleEvent.all_objects.create(
                    company=company,
                    title=f"{service.name} — {client.name}",
                    starts_at=scheduled,
                    ends_at=scheduled + timedelta(minutes=service.duration_minutes),
                    ticket=ticket,
                )

                # pagamentos conforme status
                if status in (
                    TicketStatus.CONFIRMED,
                    TicketStatus.IN_PROGRESS,
                    TicketStatus.COMPLETED,
                ):
                    Payment.all_objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.DEPOSIT,
                        status=PaymentStatus.PAID,
                        amount=ticket.total / 2,
                        paid_at=scheduled - timedelta(days=2),
                        method=PaymentMethod.PIX,
                    )
                    Payment.all_objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.BALANCE,
                        status=PaymentStatus.PENDING,
                        amount=ticket.total / 2,
                        due_date=scheduled.date(),
                    )
                elif status == TicketStatus.FINALIZED:
                    Payment.all_objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.DEPOSIT,
                        status=PaymentStatus.PAID,
                        amount=ticket.total / 2,
                        paid_at=scheduled - timedelta(days=2),
                        method=PaymentMethod.PIX,
                    )
                    Payment.all_objects.create(
                        company=company,
                        ticket=ticket,
                        kind=PaymentKind.BALANCE,
                        status=PaymentStatus.PAID,
                        amount=ticket.total / 2,
                        paid_at=scheduled + timedelta(hours=2),
                        method=PaymentMethod.PIX,
                    )
                tickets_created += 1

            self.stdout.write(f"  ✓ {tickets_created} atendimentos com pagamentos e eventos")

            # ── Movimentos manuais de caixa (saídas comuns) ──
            extras = [
                ("Combustível", "-150.00", "operacional"),
                ("Material de escritório", "-89.90", "operacional"),
                ("Mensalidade software de edição", "-79.90", "operacional"),
            ]
            for desc, amount, category in extras:
                CashflowEntry.all_objects.create(
                    company=company,
                    direction="out",
                    amount=Decimal(amount.lstrip("-")),
                    occurred_at=(now - timedelta(days=random.randint(1, 15))).date(),
                    description=desc,
                    category=category,
                )
            self.stdout.write(f"  ✓ {len(extras)} saídas manuais de caixa")

        self.stdout.write(self.style.SUCCESS("✓ Seed concluído."))
