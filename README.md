<div align="center">

# LUPA Soluções

**Sistema multi-tenant de gestão para prestadores de serviço autônomos.**
Agenda, atendimentos, cupons em PDF e caixa — conectados num só app, mobile-first.

[![CI](https://github.com/cesarpsalves/lupa-app/actions/workflows/ci.yml/badge.svg)](https://github.com/cesarpsalves/lupa-app/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django 5.1](https://img.shields.io/badge/Django-5.1-092E20.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/tests-51%20passing-brightgreen)](https://github.com/cesarpsalves/lupa-app/actions)

</div>

---

## 🎯 O problema

Prestadores de serviço autônomos no Brasil orquestram o próprio negócio com **5+ ferramentas desconectadas**: caderno, WhatsApp, Google Agenda, planilha, calculadora, gerador de PDF online. Resultado: retrabalho, esquecimento de cobranças e falta de visibilidade sobre o faturamento real.

## 💡 A solução

Um app **server-rendered, mobile-first** que cobre o ciclo completo:

```
agendar → cobrar sinal → atender → cobrar saldo → emitir cupom → registrar no caixa
```

Construído sobre um **schema genérico** que se adapta ao nicho via configuração (terminologia, campos, presets) — sem refatoração. Hoje atende **fotógrafos**; outros nichos entram via **waitlist pública** com threshold transparente.

---

## ✨ O que está implementado

### Fluxo público
- **Landing** com hero, mockup do dashboard, "como funciona" e **waitlist por nicho** (HTMX, prova social com contador público)
- **Signup** com validação real de telefone (algoritmo de DDD + 9)
- **Login** com Argon2id + lockout de brute-force (django-axes)

### App interno (`/app/`)
- **Onboarding** em 1 tela: perfil (L1 Freelancer / L2 Estúdio / L3 Loja) + nome + CPF/CNPJ opcional com **validação real dos dígitos verificadores**
- **Dashboard** com cards dinâmicos (Este mês, A receber, Hoje, Próximo passo contextual) + lista de atendimentos do dia + grade dos próximos 7 dias com dia atual destacado
- **Workspace switcher** (padrão Slack/Linear/Notion): logo do produto fica nas áreas públicas, avatar da empresa do cliente nas internas. Avatar fallback gerado deterministicamente com iniciais + cor derivada do slug (md5 → palette de 8 cores)
- **Empresa**: upload de logo (PNG/JPG/WebP até 2MB), CPF/CNPJ com máscara
- **Clientes** (CRUD): lista com busca HTMX em tempo real (nome, telefone, email, doc), criar/editar/detalhe com histórico de atendimentos, **soft delete** preservando financeiro
- **Serviços** (CRUD): grid 2 colunas, filtro arquivados, toggle ativo/inativo inline
- **Agenda**: timeline dia (7h-22h) e visão semana (grid 7 colunas, dia atual destacado), eventos linkam pro detalhe do atendimento
- **Atendimentos**:
  - Lista com filtros por status (chips) + busca
  - **Wizard de criação** em 4 passos com estado em sessão: cliente → serviços+desconto → data/hora/duração/local → pagamento (sinal+saldo / único / já pago)
  - **Detalhe** com cards de itens/totais, **máquina de estado clicável** (botões contextuais: Confirmar/Iniciar/Concluir/Finalizar/Cancelar — só os permitidos aparecem), histórico de status logs
  - "Marcar pago" nos pagamentos pendentes → entrada automática no caixa
- **Caixa**: 3 cards coloridos (Entradas verde / Saídas vermelho / Saldo), filtros de período por chips (Hoje/Semana/Mês/30d), criação manual de movimentos (entrada ou saída), automáticos vindo de pagamentos
- **Cupom PDF** via WeasyPrint: gerado automaticamente quando atendimento vira `finalized` (via signal). Botões "Baixar PDF" e "Preview" no detalhe. **Link público** `/p/cupom/<token>/` pra entregar ao cliente final via WhatsApp/email sem login

### Acessibilidade & UX
- **Dark/light mode** com persistência em localStorage + respect a `prefers-color-scheme`
- **Mobile-first**: bottom nav fixo com 5 itens, tap targets ≥44px, safe-area-inset-bottom
- **Animações sutis** (`fade-up` stagger, `card-lift`, `btn-press`, `theme-toggle rotate`, indicador animado no bottom nav)
- **Princípio "idoso-friendly"**: fluxos lineares, texto ≥16px, copy em PT-BR claro, confirmações antes de ações destrutivas
- Páginas **404 e 500** customizadas
- `prefers-reduced-motion` respeitado

### Backend
- **Multi-tenant** shared-schema com `company_id` em toda tabela. `TenantManager` **fail-closed** (sem tenant ativo, manager retorna `none()` — testado)
- **Máquina de estado** do Atendimento (`tickets/state_machine.py`) com transições estritas
- **Signals automáticos**:
  - Payment marcado como `paid` → cria/atualiza `CashflowEntry`
  - Payment volta a pending/cancelled → entrada some
  - Refund → vira saída
  - Ticket finalizado → gera cupom PDF
- **Validators de CPF/CNPJ/telefone BR** com algoritmo oficial dos dígitos verificadores, espelhados em backend (Python) e frontend (`masks.js`)

---

## 🧱 Stack

| Camada | Tecnologia | Por quê |
|---|---|---|
| **Backend** | Python 3.12 + Django 5.1 | Batteries-included, ORM, admin, auth, migrations |
| **Frontend** | Templates + [HTMX 2](https://htmx.org/) + [Alpine.js](https://alpinejs.dev/) | Server-rendered idiomático, sem build JS complexa |
| **CSS** | [Tailwind CSS](https://tailwindcss.com/) | Utility-first, design system consistente |
| **Banco** | PostgreSQL 16 | Tipagem rica, JSONB, full-text |
| **Cache** | Redis 7 | django-redis, locks, fila |
| **PDF** | [WeasyPrint](https://weasyprint.org/) | HTML→PDF nativo Python, sem headless browser |
| **Tasks** | django-q2 | Simples no MVP, evoluível |
| **Auth** | Argon2id + django-axes + django-otp | Brute-force lockout + TOTP 2FA |
| **Email** | [Resend](https://resend.com/) via django-anymail | DX moderna, deliverability sólida |
| **Imagens** | Pillow 12+ | Uploads de logo da empresa |
| **Server** | Gunicorn + Uvicorn workers | ASGI pra futuro SSE/WebSocket |
| **Proxy** | Nginx + Certbot | TLS, rate limit, HTTP/2 |
| **Deploy** | Docker Compose + GHA + SSH | Simples, portátil, reversível |
| **Obs** | Sentry + healthcheck + Healthchecks.io | MVP barato e funcional |

→ Detalhes e tradeoffs em [docs/06-adr/](docs/06-adr/).

---

## 🏗 Arquitetura

```
┌─────────────┐   HTTPS    ┌─────────┐    ┌────────────┐
│   Browser   │ ─────────▶│  Nginx  │───▶│  Gunicorn  │
│  (PWA/Web)  │            │  +TLS   │    │  +Uvicorn  │
└─────────────┘            └─────────┘    └─────┬──────┘
                                                │
                                       ┌────────┴────────┐
                                       │   Django App    │
                                       │     (HTMX)      │
                                       └────────┬────────┘
                                                │
                                ┌───────────────┼───────────────┐
                                ▼               ▼               ▼
                         ┌────────────┐  ┌──────────┐    ┌──────────┐
                         │ PostgreSQL │  │  Redis   │    │  Sentry  │
                         │   lupa_v2  │  │  cache   │    │ (errors) │
                         └────────────┘  └──────────┘    └──────────┘
```

### Multi-tenancy fail-closed

Shared database, shared schema com `company_id` em toda tabela de tenant. Enforcement em **3 camadas**:

1. **`TenantManager`** filtra `Model.objects` automaticamente pela empresa ativa (thread-local `ContextVar` definida pelo middleware)
2. **`TenantMiddleware`** resolve a empresa a partir do user logado (sessão → fallback pra primeiro membership ativo)
3. **Sem tenant ativo, manager retorna `none()`.** Cross-tenant access devolve 404 (não 403 — não vaza existência)

Testado em [`apps/core/tests/test_tenant_isolation.py`](apps/core/tests/test_tenant_isolation.py) e [`apps/clients/tests/test_clients.py`](apps/clients/tests/test_clients.py).

→ ADR completo: [docs/06-adr/0002-multitenant-shared-schema.md](docs/06-adr/0002-multitenant-shared-schema.md).

---

## 📁 Estrutura

```
lupa/
├── apps/
│   ├── core/          # TenantModel, manager, middleware, RBAC, validators BR
│   ├── accounts/      # User custom (email), signup, login, invitations
│   ├── companies/     # Company (tenant), NichePreset, Membership, logo upload
│   ├── clients/       # CRUD de clientes
│   ├── catalog/       # Service + Product
│   ├── scheduling/    # ScheduleEvent + agenda dia/semana
│   ├── tickets/       # Ticket, TicketItem, state machine + wizard
│   ├── payments/      # Payment com signal pro caixa
│   ├── cashflow/      # CashflowEntry (auto + manual)
│   ├── documents/     # Cupom PDF (WeasyPrint) + link público
│   ├── dashboard/     # Onboarding + dashboard + "Mais"
│   └── public/        # Landing + waitlist
├── config/
│   ├── settings/      # base / dev / prod / test (split)
│   └── urls.py
├── templates/         # base.html + componentes reutilizáveis
├── docker/            # Dockerfile, compose dev/prod, nginx, entrypoint
├── .github/workflows/ # CI (lint+type+test+build) + Deploy (SSH)
└── tests/conftest.py
```

---

## 🚀 Rodando localmente

### Pré-requisitos
- Python 3.12+
- Docker / Podman (pra Postgres e Redis em dev)
- `make`

### Setup

```bash
git clone https://github.com/cesarpsalves/lupa-app.git
cd lupa-app

# Variáveis de ambiente
cp .env.example .env
# Edite SECRET_KEY — gere com:
# python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Subir Postgres + Redis + mailpit (email local em http://localhost:8025)
make up

# Setup Python e dependências
make install
source .venv/bin/activate

# Migrations + superuser
make migrate
make superuser

# (opcional) seed com 10 clientes, 5 serviços, 12 atendimentos
python manage.py seed_demo --email seu@email.com --clean

# Rodar
make run            # → http://localhost:8000
```

### Comandos comuns

```bash
make help           # Lista todos os comandos
make test           # Testes
make testcov        # Testes com coverage HTML
make check          # Lint + mypy + audit + bandit (tudo)
make fmt            # Formata código (ruff)
make shell          # Django shell_plus
```

---

## 🧪 Qualidade

| Camada | Ferramenta | Status |
|---|---|---|
| Lint | **Ruff** (pyflakes, pycodestyle, pyupgrade, bugbear, django, security) | ✅ Limpo |
| Format | **Ruff format** | ✅ Limpo |
| Type-check | **mypy + django-stubs** | ✅ Sem issues em 114 arquivos |
| Security lint | **Bandit** | ✅ 0 Medium + 0 High |
| CVE scan | **pip-audit** | ✅ 0 known vulnerabilities |
| Pre-commit | **gitleaks + ruff + mypy + bandit** | ✅ Configurado |
| Testes | **pytest + pytest-django + factory-boy** | ✅ 51/51 passing |
| Tenant isolation | Bateria dedicada | ✅ Cross-tenant 404 garantido |

---

## 🔐 Segurança

- **Zero segredos no repo.** `.env` no `.gitignore` desde o commit 0. Gitleaks no pre-commit
- **Argon2id** como hasher principal de senhas
- **django-axes** — 5 falhas em 5min = lockout de 30min
- **django-otp** — TOTP 2FA opcional pro usuário, obrigatório pra owner em produção
- **HSTS + CSP + X-Frame-Options + Referrer-Policy** em produção
- **Multi-tenant fail-closed** (manager retorna `none()` sem tenant ativo)
- **LGPD** — endpoints de exportar e excluir dados pessoais ([docs/04-security.md §7](docs/04-security.md))
- **Validação real de CPF/CNPJ** — algoritmo oficial dos dígitos verificadores, espelhado backend+frontend

→ Plano completo: [docs/04-security.md](docs/04-security.md).

---

## ♿ Acessibilidade — princípio fixo

> *Um idoso deve conseguir usar sem dificuldade — sem que isso signifique remover recursos.*

Regras concretas aplicadas em todo template:
- Fluxos lineares, sem dead-end
- Alvo de toque ≥ 44px
- Texto ≥ 16px no corpo
- Estados sempre com cor + ícone + texto (nunca só cor)
- Erros associados a campos via `aria-describedby`
- Confirmação antes de ação destrutiva
- Copy em português claro, sem jargão
- `prefers-reduced-motion` respeitado nas animações

---

## 🗺 Roadmap

| Versão | Conteúdo | Status |
|---|---|---|
| **v1 (MVP)** | Auth, multi-tenant, agenda, atendimento, sinal/saldo, cupom PDF, caixa, landing+waitlist | ✅ **Implementado** |
| **v1.5** | Galeria de entrega, contrato com assinatura simples, agenda multiusuário (L2), relatórios financeiros | 🚧 Em planejamento |
| **v2** | Loja/PDV (L3), WhatsApp bot escopo fechado, NFS-e SP, 2º nicho ativo | 📅 Mês 6-9 |

→ Detalhe em [docs/05-roadmap.md](docs/05-roadmap.md) *(em construção)*.

---

## 📚 Documentação

| Doc | Resumo |
|---|---|
| [PRD](docs/01-prd.md) | Visão, escopo v1, princípios, anti-escopo |
| [User Journey](docs/02-user-journey.md) | Fluxo de telas do fotógrafo L1 ponta a ponta |
| [Arquitetura](docs/03-architecture.md) | Stack, modelo de dados, multi-tenant, deploy |
| [Segurança](docs/04-security.md) | Threat model, secrets, hardening, LGPD |
| [ADRs](docs/06-adr/) | Decisões técnicas com tradeoffs registrados |

---

## 👤 Autor

**Paulo Alves** — Engenheiro de Software (Brasil)
[GitHub](https://github.com/cesarpsalves) · [LinkedIn](https://www.linkedin.com/in/pauloalvesdev/) · contato@lupasolucoes.com

Esse projeto é uma vitrine de engenharia: **um produto pequeno feito bem feito vale mais do que um produto enorme feito errado**. É uma lição que aprendi do jeito difícil refazendo este app — a história completa está em [docs/01-prd.md §10](docs/01-prd.md#10-riscos-e-mitigações).

## 📄 Licença

[MIT](LICENSE) — use, modifique, distribua. Atribuição agradecida.
