# LUPA — Gestão para prestadores de serviço

> **Sistema multi-tenant para prestadores de serviço autônomos**, começando por fotógrafos. Agenda, atendimentos, cupons em PDF e fluxo de caixa — conectados num só app, mobile-first.

[![CI](https://github.com/pauloalves/lupa/actions/workflows/ci.yml/badge.svg)](https://github.com/pauloalves/lupa/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django 5.1](https://img.shields.io/badge/Django-5.1-092E20.svg)](https://www.djangoproject.com/)

---

## 🎯 O problema

Prestadores de serviço autônomos no Brasil orquestram o próprio negócio com **5+ ferramentas desconectadas**: caderno, WhatsApp, Google Agenda, planilha, calculadora, gerador de PDF. O resultado é retrabalho, esquecimento de cobranças e falta de visibilidade sobre o faturamento real.

## 💡 A solução

Um app **server-rendered, mobile-first** que cobre o ciclo completo:

```
agendar → cobrar sinal → atender → cobrar saldo → emitir cupom → registrar no caixa
```

Construído sobre um schema **genérico** que se adapta ao nicho via configuração (terminologia, campos, presets) — sem refatoração. Hoje atende fotógrafos; outros nichos entram via **waitlist pública** com threshold transparente.

## 🧱 Stack

| Camada | Escolha | Por quê |
|---|---|---|
| Backend | **Python 3.12 + Django 5.1** | Batteries-included, ORM, admin, auth, migrations |
| Frontend | **Templates + HTMX 2 + Alpine.js** | Server-rendered idiomático, sem build JS complexa |
| CSS | **Tailwind** | Utility-first, design system consistente |
| Banco | **PostgreSQL 16** | Tipagem rica, JSONB, full-text |
| Cache | **Redis 7** | django-redis, locks, fila |
| PDF | **WeasyPrint** | HTML→PDF nativo Python |
| Tasks | **django-q2** → Celery quando precisar | Simples no MVP, evoluível |
| Auth | **django-axes + django-otp** | Brute-force lockout + TOTP 2FA |
| Email | **Resend via Anymail** | DX moderna, deliverability sólida |
| Server | **Gunicorn + Uvicorn workers** | ASGI pra futuro SSE/WebSocket |
| Proxy | **Nginx + Certbot** | TLS, rate limit, HTTP/2 |
| Deploy | **Docker Compose + GHA + SSH** | Simples, portátil, reversível |
| Obs | **Sentry + healthcheck** | MVP barato e funcional |

→ Detalhes e tradeoffs em [docs/06-adr/](../docs/06-adr/).

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

### Multi-tenancy

**Shared database, shared schema** com `company_id` em toda tabela de tenant. Enforcement em 3 camadas:

1. **`TenantManager`** filtra `Model.objects` automaticamente pela empresa ativa (thread-local definida pelo middleware).
2. **`TenantMiddleware`** resolve a empresa a partir do user logado (sessão → fallback pra primeiro membership).
3. **Falha fechado**: sem tenant ativo, todo queryset retorna `none()`. Cross-tenant returns 404, never 403.

Testado em [`apps/core/tests/test_tenant_isolation.py`](apps/core/tests/test_tenant_isolation.py).

→ ADR completo: [docs/06-adr/0002-multitenant-shared-schema.md](../docs/06-adr/0002-multitenant-shared-schema.md).

## 📁 Estrutura

```
lupa/
├── apps/
│   ├── core/        # TenantModel, manager, middleware, RBAC
│   ├── accounts/    # User custom (email), signup, login, invitations
│   ├── companies/   # Company (tenant), NichePreset, Membership
│   └── public/      # Landing, waitlist por nicho
├── config/
│   ├── settings/    # base / dev / prod / test (split)
│   └── urls.py
├── templates/       # base.html + componentes reutilizáveis
├── docker/          # Dockerfile, compose dev/prod, nginx, entrypoint
├── .github/workflows/  # CI (lint+type+test+build) e Deploy (SSH)
├── tests/conftest.py
└── pyproject.toml
```

## 🚀 Rodando localmente

### Pré-requisitos
- Python 3.12+
- Docker + Docker Compose (pra Postgres e Redis)
- `make`

### Setup

```bash
git clone https://github.com/pauloalves/lupa.git
cd lupa

# Variáveis de ambiente
cp .env.example .env
# editar SECRET_KEY (use: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Subir banco + Redis + mailpit (email local em http://localhost:8025)
make up

# Setup Python e dependências
make install
source .venv/bin/activate

# Migrations + superuser
make migrate
make superuser

# Rodar
make run            # → http://localhost:8000
```

### Comandos comuns

```bash
make help           # Lista todos os comandos
make test           # Testes rápidos
make testcov        # Testes com coverage HTML
make check          # Lint + mypy + audit + bandit
make fmt            # Formata código (ruff)
make shell          # Django shell_plus
```

## 🧪 Qualidade

| Camada | Ferramenta |
|---|---|
| Lint | **Ruff** — pyflakes, pycodestyle, pyupgrade, bugbear, django, security |
| Format | **Ruff format** |
| Type-check | **mypy + django-stubs** (gradual) |
| Security lint | **Bandit** |
| CVE check | **pip-audit** no CI |
| Pre-commit | **pre-commit** + gitleaks (detecta segredos antes do commit) |
| Testes | **pytest + pytest-django + factory-boy** |
| Coverage mínimo | **70%** (CI falha abaixo) |
| Multi-tenant | Bateria específica garante isolamento cross-company |

## 🔐 Segurança

- **Zero segredos no repo.** `.env` no `.gitignore` desde o commit 0. Gitleaks no pre-commit.
- **Argon2id** como hasher principal de senhas.
- **django-axes** — 5 falhas em 5min = lockout de 30min.
- **django-otp** — TOTP 2FA opcional pro usuário, obrigatório pra owner em produção.
- **HSTS + CSP + X-Frame-Options + Referrer-Policy** em produção.
- **Multi-tenant fail-closed** (manager retorna `none()` sem tenant ativo).
- **Audit log** centralizado para ações sensíveis.
- **LGPD** — endpoints de exportar e excluir dados pessoais ([docs/04-security.md §7](../docs/04-security.md)).

→ Plano completo: [docs/04-security.md](../docs/04-security.md).

## ♿ Acessibilidade — princípio fixo

> *Um idoso deve conseguir usar sem dificuldade — sem que isso signifique remover recursos.*

Regras concretas aplicadas em todo template:
- Fluxos lineares, sem dead-end
- Alvo de toque ≥ 44px
- Texto ≥ 16px no corpo
- Estados sempre com cor + ícone + texto (nunca só cor)
- Erros associados a campos via `aria-describedby`
- Confirmação antes de ação destrutiva
- Copy em português claro

Auditado com [axe-core](https://github.com/dequelabs/axe-core) por release.

## 🗺 Roadmap

| Versão | Conteúdo | Prazo |
|---|---|---|
| **v1 (MVP)** | Auth, multi-tenant, agenda, atendimento, sinal/saldo, cupom PDF, caixa, landing+waitlist | 3 meses |
| **v1.5** | Galeria de entrega, contrato com assinatura simples, agenda multiusuário (L2) | mês 4-5 |
| **v2** | Loja/PDV (L3), WhatsApp bot escopo fechado, NFS-e SP, 2º nicho ativo | mês 6-9 |

→ Detalhe em [docs/05-roadmap.md](../docs/05-roadmap.md) *(em construção)*.

## 📚 Documentação

| Doc | Resumo |
|---|---|
| [PRD](../docs/01-prd.md) | Visão, escopo v1, princípios, anti-escopo (o que NÃO faremos) |
| [User Journey](../docs/02-user-journey.md) | Fluxo de telas do fotógrafo L1 ponta a ponta |
| [Arquitetura](../docs/03-architecture.md) | Stack, modelo de dados, multi-tenant, deploy |
| [Segurança](../docs/04-security.md) | Threat model, secrets, hardening, LGPD |
| [ADRs](../docs/06-adr/) | Decisões técnicas registradas com tradeoffs |

## 👤 Autor

**Paulo Alves** — Engenheiro de Software (Brasil)
[GitHub](https://github.com/pauloalves) · [LinkedIn](https://www.linkedin.com/in/pauloalvesti/) · contato@lupasolucoes.com

Esse projeto é uma vitrine de engenharia: **um produto pequeno feito bem feito vale mais do que um produto enorme feito errado** — uma lição que eu aprendi do jeito difícil refazendo este app. Veja a história completa em [docs/01-prd.md §10](../docs/01-prd.md#10-riscos-e-mitigações).

## 📄 Licença

[MIT](LICENSE) — use, modifique, distribua. Atribuição agradecida.
