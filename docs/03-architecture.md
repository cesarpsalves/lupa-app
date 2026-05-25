# LUPA — Arquitetura Técnica

**Status:** Draft v1 — aguardando validação.
**Última atualização:** 2026-05-24

---

## 1. Visão geral em 1 parágrafo

Monolito Django **server-rendered** com **HTMX + Alpine.js** pra interatividade, **Postgres** como único banco de estado, **Redis** pra cache e fila leve, **Gunicorn** atrás de **Nginx** com **Certbot**, tudo orquestrado por **docker-compose** em um VPS. Deploy via GitHub Actions com SSH. Sem Supabase, sem React, sem microserviços, sem Kubernetes — escolhas alinhadas com "produto pequeno feito direito > produto enorme feito errado".

## 2. Diagrama de alto nível

```
┌─────────────┐
│  Navegador  │
│ (PWA/Mobile)│
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐    ┌─────────────┐
│    Nginx    │───▶│  Certbot    │
│  (proxy)    │    │  (renew)    │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│   Gunicorn  │───▶│  Django App │
│  (3 workers)│    │  (HTMX)     │
└──────┬──────┘    └──────┬──────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  Postgres   │    │   Redis     │
│  (lupa_v2)  │    │ (cache+lock)│
└─────────────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│  pg_dump    │
│  → S3/R2    │
│  (backup)   │
└─────────────┘
```

## 3. Stack

| Camada | Tecnologia | Por quê |
|---|---|---|
| **Linguagem** | Python 3.12 | Maturidade, ecossistema, tipagem estática viável |
| **Framework** | Django 5.x LTS | Batteries-included, ORM, admin, auth, migrations |
| **Frontend** | Templates + HTMX 2 + Alpine.js | Sem build complexa, full-stack idiomático |
| **CSS** | Tailwind via CLI standalone | Sem Node em produção, build simples |
| **Banco** | PostgreSQL 16 | Tipagem rica (JSONB), full-text, confiável |
| **Cache/fila** | Redis 7 | django-redis, futuro RQ ou Celery |
| **Templates PDF** | WeasyPrint | HTML→PDF nativo Python, sem headless browser |
| **Forms** | django-crispy-forms + Tailwind | Forms acessíveis sem boilerplate |
| **Auth extras** | django-allauth, django-otp, django-axes | Padrão de mercado, testados |
| **Permissões** | Django built-in + custom mixins por tenant | Suficiente, sem `guardian` (overkill) |
| **Tasks** | django-q2 inicialmente (futuro: Celery) | Roda no mesmo processo, simples |
| **Email** | Anymail + Resend (ou SES) | Decisão pendente |
| **Storage** | django-storages + S3-compatible (R2) | Portátil; local em dev |
| **Server** | Gunicorn + Uvicorn workers (ASGI) | ASGI permite HTMX SSE futuro |
| **Proxy** | Nginx | Padrão, rate limit, TLS, static |
| **Containers** | Docker + docker-compose | Suficiente pra 1 VPS |
| **CI/CD** | GitHub Actions | Free pra repo público, integração nativa |
| **Observabilidade** | Sentry + journald + Healthchecks.io | MVP barato |

## 4. Estrutura do repositório

```
lupa/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # lint + type + test on PR
│       └── deploy.yml             # SSH deploy on main
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/                      # mixins, utils, base models
│   │   ├── models.py              # TimestampedModel, TenantModel
│   │   ├── middleware.py          # TenantMiddleware
│   │   ├── permissions.py         # role decorators
│   │   ├── managers.py            # TenantManager
│   │   └── tests/
│   ├── accounts/                  # User, autenticação, convite
│   │   ├── models.py              # User, Invitation
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── templates/accounts/
│   ├── companies/                 # Empresa (tenant), nicho, config
│   │   ├── models.py              # Company, NichePreset, Membership
│   │   ├── views.py
│   │   └── templates/companies/
│   ├── clients/                   # Clientes da empresa
│   ├── catalog/                   # Serviços e produtos
│   ├── scheduling/                # Agenda, eventos
│   ├── tickets/                   # Atendimentos (núcleo)
│   │   ├── models.py              # Ticket, TicketItem, TicketStatusLog
│   │   ├── state_machine.py       # transições + guards
│   │   ├── services.py            # lógica de negócio (não em views)
│   │   └── ...
│   ├── payments/                  # Pagamentos, sinal, saldo
│   ├── cashflow/                  # Caixa, movimentos
│   ├── documents/                 # Cupom PDF, templates
│   ├── public/                    # Landing, waitlist, sobre, privacidade
│   └── audit/                     # Audit log centralizado
├── templates/                     # base.html, components reutilizáveis
│   ├── base.html
│   ├── components/
│   └── partials/                  # fragmentos HTMX
├── static/
│   ├── css/
│   ├── js/
│   │   ├── htmx.min.js
│   │   └── alpine.min.js
│   └── img/
├── tests/
│   ├── conftest.py
│   ├── factories.py               # factory-boy
│   └── e2e/                       # Playwright (futuro)
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx.conf
│   └── entrypoint.sh
├── scripts/
│   ├── backup.sh                  # pg_dump → S3
│   └── deploy.sh
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml                 # ruff, black, mypy, pytest config
├── requirements/
│   ├── base.in / base.txt
│   ├── dev.in  / dev.txt
│   └── prod.in / prod.txt
├── manage.py
├── Makefile                       # comandos comuns
└── README.md
```

## 5. Modelo de dados (essência)

> Todo modelo de tenant herda de `TenantModel` (que tem `company` FK + manager filtrado).

### 5.1. Diagrama

```
User ──┐
       │
       ▼
   Membership ──▶ Company ──▶ NichePreset
                     │
       ┌─────────────┼──────────────┐
       ▼             ▼              ▼
    Client      ServiceCatalog   CompanySettings
       │             │
       └─────┬───────┘
             ▼
          Ticket ──▶ TicketItem (n×)
             │
             ├──▶ TicketStatusLog (n×)
             ├──▶ Payment (n×) ─────────▶ CashflowEntry
             ├──▶ ScheduleEvent (1)
             └──▶ Document (cupom PDF)

CashflowEntry (entrada/saída — também avulsa)
AuditLog (eventos globais)
WaitlistEntry (público)
```

### 5.2. Modelos principais (resumo)

```python
# apps/core/models.py
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class TenantModel(TimestampedModel):
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, db_index=True)
    objects = TenantManager()       # filtra automaticamente pelo tenant atual
    all_objects = models.Manager()  # acesso sem filtro (apenas para tasks/admin)
    class Meta: abstract = True
```

```python
# apps/accounts/models.py
class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]
```

```python
# apps/companies/models.py
class Company(TimestampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    niche = models.ForeignKey("NichePreset", on_delete=models.PROTECT)
    profile_level = models.CharField(
        max_length=2, choices=[("L1","Freelancer"), ("L2","Estúdio"), ("L3","Loja")],
        default="L1",
    )
    document = models.CharField(max_length=20, blank=True)  # CPF/CNPJ
    settings = models.JSONField(default=dict)  # default_signal_pct, etc.

class NichePreset(TimestampedModel):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    ticket_label = models.CharField(max_length=40, default="Atendimento")
    suggested_services = models.JSONField(default=list)
    is_active = models.BooleanField(default=False)  # gated by threshold

class Membership(TenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ("owner","Owner"), ("manager","Manager"),
        ("employee","Funcionário"), ("viewer","Visualizador"),
    ])
    is_active = models.BooleanField(default=True)
    class Meta:
        unique_together = [("company","user")]
```

```python
# apps/clients/models.py
class Client(TenantModel):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    document = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
```

```python
# apps/catalog/models.py
class Service(TenantModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
```

```python
# apps/tickets/models.py
class TicketStatus(models.TextChoices):
    DRAFT = "draft", "Orçamento"
    CONFIRMED = "confirmed", "Confirmado"
    IN_PROGRESS = "in_progress", "Em execução"
    COMPLETED = "completed", "Concluído"
    FINALIZED = "finalized", "Finalizado"
    CANCELLED = "cancelled", "Cancelado"

class Ticket(TenantModel):
    code = models.CharField(max_length=12, unique=True)   # gerado: LUPA-2026-000123
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.DRAFT)
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict)   # campos custom por nicho

class TicketItem(TenantModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey("catalog.Service", on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=200)  # cópia ou avulso
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class TicketStatusLog(TenantModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    note = models.CharField(max_length=200, blank=True)
```

```python
# apps/payments/models.py
class PaymentKind(models.TextChoices):
    DEPOSIT = "deposit", "Sinal"
    BALANCE = "balance", "Saldo"
    FULL = "full", "Pagamento único"
    REFUND = "refund", "Devolução"

class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    PAID = "paid", "Pago"
    CANCELLED = "cancelled", "Cancelado"

class Payment(TenantModel):
    ticket = models.ForeignKey("tickets.Ticket", on_delete=models.CASCADE, related_name="payments")
    kind = models.CharField(max_length=10, choices=PaymentKind.choices)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    method = models.CharField(max_length=20, blank=True)  # pix, dinheiro, cartao
```

```python
# apps/cashflow/models.py
class CashflowEntry(TenantModel):
    direction = models.CharField(max_length=3, choices=[("in","Entrada"), ("out","Saída")])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    occurred_at = models.DateField(db_index=True)
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=40, blank=True)
    payment = models.OneToOneField(
        "payments.Payment", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cashflow_entry",
    )
    # se payment != null → entrada automática vinda do fluxo
    # se payment == null → entrada/saída manual
```

```python
# apps/documents/models.py
class Document(TenantModel):
    ticket = models.ForeignKey("tickets.Ticket", on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(max_length=20, choices=[("receipt","Cupom"), ("contract","Contrato")])
    file = models.FileField(upload_to="documents/%Y/%m/")
    public_token = models.CharField(max_length=40, unique=True)  # acesso público
    public_expires_at = models.DateTimeField(null=True, blank=True)
```

```python
# apps/audit/models.py
class AuditLog(TimestampedModel):
    company = models.ForeignKey("companies.Company", on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=80)        # 'ticket.cancelled'
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=40)
    ip = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
```

```python
# apps/public/models.py
class WaitlistEntry(TimestampedModel):
    niche_slug = models.SlugField(db_index=True)
    email = models.EmailField()
    name = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=40, blank=True)
    class Meta:
        unique_together = [("niche_slug", "email")]
```

### 5.3. Índices críticos

```python
# tickets
Meta.indexes = [
    models.Index(fields=["company", "status", "scheduled_at"]),
    models.Index(fields=["company", "client"]),
    models.Index(fields=["company", "-created_at"]),
]

# payments
Meta.indexes = [
    models.Index(fields=["company", "status", "due_date"]),
]

# cashflow
Meta.indexes = [
    models.Index(fields=["company", "occurred_at"]),
]
```

## 6. Multi-tenant — implementação

### 6.1. Resolução de tenant

```python
# apps/core/middleware.py
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None
        if request.user.is_authenticated:
            active = (request.session.get("active_company_id")
                      or Membership.objects.filter(user=request.user, is_active=True).values_list("company_id", flat=True).first())
            if active:
                request.company = Company.objects.filter(pk=active).first()
                set_current_company(request.company)   # thread-local
        try:
            return self.get_response(request)
        finally:
            set_current_company(None)
```

### 6.2. Manager filtrado

```python
# apps/core/managers.py
class TenantQuerySet(models.QuerySet):
    def for_company(self, company):
        return self.filter(company=company)

class TenantManager(models.Manager):
    def get_queryset(self):
        company = get_current_company()
        if company is None:
            # Falha fechado: sem tenant ativo, NENHUMA query retorna dado.
            return TenantQuerySet(self.model, using=self._db).none()
        return TenantQuerySet(self.model, using=self._db).filter(company=company)
```

### 6.3. Garantias de teste

- Test obrigatório: criar 2 empresas, garantir que user da empresa A não vê dado da B (status 404, não 403).
- Test obrigatório: chamar manager sem `set_current_company` retorna `none()`.

## 7. Máquina de estado do Atendimento

```python
# apps/tickets/state_machine.py
TRANSITIONS = {
    "draft":       ["confirmed", "cancelled"],
    "confirmed":   ["in_progress", "cancelled"],
    "in_progress": ["completed", "cancelled"],
    "completed":   ["finalized"],
    "finalized":   [],
    "cancelled":   [],
}

def transition(ticket, *, to, user, note=""):
    if to not in TRANSITIONS[ticket.status]:
        raise InvalidTransition(f"{ticket.status} → {to}")
    with transaction.atomic():
        from_status = ticket.status
        ticket.status = to
        ticket.save(update_fields=["status", "updated_at"])
        TicketStatusLog.objects.create(
            company=ticket.company, ticket=ticket,
            from_status=from_status, to_status=to,
            user=user, note=note,
        )
        # side-effects (gerar cupom, marcar pagamento, etc.) ficam em signals/services
```

## 8. Geração de cupom PDF

- `WeasyPrint` renderiza `templates/documents/receipt.html` → PDF.
- Trigger: signal `post_save` em `Ticket` quando `status` muda pra `finalized`.
- Armazena em `Document.file` (S3-compatible) e gera `public_token` UUID4.
- Link público: `/p/recibo/<token>/` (sem auth, validade configurável).

## 9. Permissões (RBAC simples)

```python
# apps/core/permissions.py
def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.company:
                raise PermissionDenied
            membership = Membership.objects.filter(
                company=request.company, user=request.user, is_active=True
            ).first()
            if not membership or membership.role not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator

# uso:
@role_required("owner", "manager")
def delete_ticket(request, pk): ...
```

## 10. Frontend — HTMX patterns

- **Submit de form sem reload:** `hx-post` retorna fragmento, faz `hx-swap="outerHTML"` no card.
- **Modal:** `hx-get` retorna partial, injeta em container `#modal-root`.
- **Validação inline:** `hx-trigger="blur"` no campo, retorna `<span>` com erro.
- **Wizard de criação:** rota por passo (`/atendimentos/novo/<step>/`), sessão ou URL params guardam estado parcial.
- **Long-running task:** retorna `<div hx-get="/poll/<task>" hx-trigger="every 2s">`.

Alpine.js só pra estado **puramente local** (dropdowns, toggle de menu mobile).

## 11. Testes

| Tipo | Ferramenta | Cobertura mínima |
|---|---|---|
| Unit | pytest + pytest-django | 80% nas pastas `services/`, `models.py`, `state_machine.py` |
| Integration | pytest-django + factories | Fluxo de criar ticket → pagar → finalizar → cupom |
| Tenant isolation | pytest | Bateria específica: cross-tenant deve falhar |
| Security | pytest + bandit + pip-audit | Bandit no CI, audit em deps |
| E2E | Playwright | v1.5+ (após deploy estável) |
| Accessibility | axe-core (manual) + checklist | A11y do PRD por release |

## 12. Deploy

### 12.1. Topologia

VPS único (`lupa.pauloalves.dev` ou domínio definitivo):

```
docker-compose.prod.yml
├── nginx (host network ou bridge + portas 80/443)
├── web   (gunicorn, 3 workers)
├── db    (postgres 16) — ou conexão externa ao Postgres do VPS, decidir
├── redis (cache + locks)
└── (cron host) backup.sh diário às 03h
```

### 12.2. Pipeline

```
push main
  └─▶ CI (lint, type, test, build image)
       └─▶ push image (ghcr.io/pauloalves/lupa:sha-xxx)
            └─▶ deploy job (ssh paulo@vps + docker compose pull && up -d)
                 └─▶ smoke test (curl /healthz)
                      └─▶ if fail: rollback (compose up -d com tag anterior)
```

### 12.3. Banco

- Database **`lupa_v2`** criada no Postgres do VPS (mesmo instance do Supabase atual).
- Usuário Postgres **`lupa_app`** com privilégios apenas em `lupa_v2`.
- Banco antigo (`postgres` default + schemas Supabase) **intocado** até cutover validado.
- Migrações Django via `manage.py migrate` no `entrypoint.sh`.

### 12.4. Backup

```bash
# scripts/backup.sh (cron diário 03h)
pg_dump -Fc lupa_v2 | gzip > /var/backups/lupa_v2_$(date +%F).sql.gz
aws s3 cp /var/backups/lupa_v2_$(date +%F).sql.gz s3://lupa-backups/ --endpoint-url=https://...
find /var/backups -name 'lupa_v2_*.sql.gz' -mtime +14 -delete
```

Restore testado **antes do primeiro deploy de produção** (não depois).

## 13. Observabilidade

- **Sentry** capturando exceptions (Django + JS).
- **`/healthz`** retorna 200 se Postgres ping + Redis ping OK.
- **Healthchecks.io** pinga `/healthz` a cada 5 min; alerta em email se falhar 2x.
- **Logs:** Django → stdout → docker → journald → rotação 14 dias.

## 14. ADRs (decisões registradas)

Pasta `docs/06-adr/`. Template:

```
# ADR-NNNN: <Título>
- Data: YYYY-MM-DD
- Status: proposed | accepted | superseded by ADR-XXXX

## Contexto
## Decisão
## Consequências (positivas e negativas)
## Alternativas consideradas
```

ADRs planejados pro dia 1:
- ADR-0001: Django + HTMX (em vez de FastAPI + SPA)
- ADR-0002: Multi-tenant shared-schema com `company_id`
- ADR-0003: Postgres direto, sem Supabase
- ADR-0004: Monolito em VPS único (sem K8s/microserviços)

## 15. Roadmap técnico v1 (sequência de implementação)

1. **Bootstrap repo:** Django 5, settings split, ruff/black/mypy, pytest, pre-commit, CI básico
2. **`accounts` + `companies`:** User custom, signup, login, Company, Membership, TenantMiddleware
3. **`core`:** TenantModel, TenantManager, role_required, audit log básico
4. **`clients` + `catalog`:** CRUD simples com HTMX
5. **`scheduling` + `tickets`:** modelo + state machine + criação wizard
6. **`payments` + `cashflow`:** sinal + saldo + entrada automática no caixa
7. **`documents`:** cupom PDF via WeasyPrint
8. **`public`:** landing + waitlist
9. **Polimento:** acessibilidade, copy, micro-interações, vazios
10. **Deploy:** docker-compose prod, Nginx, Certbot, backup, healthcheck
11. **README portfolio-grade + screenshots + link**

Cada item = 1 sprint ≈ 1 semana. Total: ~11 semanas (3 meses).

## 16. Decisões em aberto (pra resolver com ADR antes de implementar)

- [ ] Postgres dentro do compose vs Postgres do VPS (atual)
- [ ] Email provider (Resend / SES / Postmark)
- [ ] Storage (R2 / S3 / local)
- [ ] Pricing model (free + 1 plano? trial?)
- [ ] Domínio definitivo
