# Runbook: Deploy do LUPA em produção

> **Quem executa:** Claude (eu), após você confirmar o hardening.
> **Pré-requisito:** [01-vps-hardening.md](./01-vps-hardening.md) ✅
> **Tempo estimado:** 20–30 minutos.

---

## Visão geral do que vou fazer

```
Você: ✅ hardening pronto (VPS endurecido)
  ↓
1. Instalo Docker + Compose no VPS
2. Crio diretório do app e .env de produção (com SECRET_KEY gerado)
3. Setup do Postgres (container, database lupa_v2 isolada do legado)
4. Clone do repo, build do container, migrate
5. Nginx + Certbot (HTTPS em lupasolucoes.com)
6. Setup do GitHub Actions deploy (SSH key como secret)
7. Backup automático diário (cron + pg_dump → R2/local)
8. Smoke test público
  ↓
🚀 https://lupasolucoes.com
```

---

## Pré-deploy (você decide)

### Domínio
- Confirmado: `lupasolucoes.com` (já existe DNS apontando pra Hostinger)
- Verificar antes: `dig lupasolucoes.com +short` deve retornar `31.97.26.125`

### Resend (email transacional)
- Criar conta em https://resend.com (gratuito até 3k emails/mês)
- Pegar API key (formato `re_xxxxx`)
- Adicionar domínio `lupasolucoes.com` no Resend e configurar DNS (SPF + DKIM)
- Me passar a API key quando me autorizar o deploy (via canal seguro)

### Storage de uploads
- Por ora: **local** no VPS (`/var/lib/lupa/media/`)
- Quando bater limite (~1GB), migra pra Cloudflare R2 (decisão futura)

---

## Etapa 1 — Instalar Docker + Compose

Comandos que vou rodar como `paulo` no VPS:

```bash
# Docker oficial
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Permitir paulo usar docker sem sudo
sudo usermod -aG docker paulo
# (precisa relogar ou newgrp docker)

# Docker compose plugin (vem com docker recente)
docker compose version
```

---

## Etapa 2 — Estrutura no VPS

```bash
# Diretório do app
sudo mkdir -p /opt/lupa
sudo chown paulo:paulo /opt/lupa
cd /opt/lupa

# Diretórios persistentes (volumes)
sudo mkdir -p /var/lib/lupa/{postgres,media,backups,redis}
sudo chown -R paulo:paulo /var/lib/lupa

# Pasta do .env (separada do código, permissão 700)
sudo mkdir -p /etc/lupa
sudo chown paulo:paulo /etc/lupa
sudo chmod 700 /etc/lupa
```

---

## Etapa 3 — Clonar repo

```bash
cd /opt/lupa
git clone https://github.com/cesarpsalves/lupa-app.git .
```

---

## Etapa 4 — Configurar `.env` de produção

```bash
sudo nano /etc/lupa/lupa.env
chmod 600 /etc/lupa/lupa.env
```

Conteúdo (vou gerar os secrets):

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<gerado-via-python -c 'from secrets import token_urlsafe; print(token_urlsafe(50))'>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=lupasolucoes.com,www.lupasolucoes.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://lupasolucoes.com,https://www.lupasolucoes.com

# Postgres (container interno do compose)
DATABASE_URL=postgres://lupa_app:<senha-forte-gerada>@db:5432/lupa_v2
POSTGRES_DB=lupa_v2
POSTGRES_USER=lupa_app
POSTGRES_PASSWORD=<senha-forte-gerada>

REDIS_URL=redis://redis:6379/0

# Email
EMAIL_BACKEND=anymail.backends.resend.EmailBackend
RESEND_API_KEY=<do Resend>
DEFAULT_FROM_EMAIL=LUPA Soluções <nao-responda@lupasolucoes.com>

# Segurança
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000

# Aplicação
LUPA_DEFAULT_SIGNAL_PCT=50
LUPA_WAITLIST_THRESHOLD=15

# Observabilidade (opcional, mas recomendado)
SENTRY_DSN=
SENTRY_ENVIRONMENT=production

LUPA_TAG=latest
```

---

## Etapa 5 — Subir o stack

```bash
cd /opt/lupa
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env pull
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d db redis

# Espera Postgres ficar healthy
sleep 10
docker compose -f docker/docker-compose.prod.yml ps

# Sobe a app
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d web
```

---

## Etapa 6 — Migrate + estáticos + superuser

```bash
# Migrate
docker compose -f docker/docker-compose.prod.yml exec web python manage.py migrate

# Coletar estáticos
docker compose -f docker/docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Criar superuser (interativo)
docker compose -f docker/docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Etapa 7 — Nginx + Certbot (HTTPS)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Sobe Nginx (já no compose)
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d nginx

# Gera certificado (HTTP-01 challenge via Nginx)
sudo certbot --nginx -d lupasolucoes.com -d www.lupasolucoes.com \
  --non-interactive --agree-tos -m contato@lupasolucoes.com --redirect

# Renovação automática (cron já configurado pelo apt)
sudo certbot renew --dry-run
```

---

## Etapa 8 — Smoke test público

```bash
curl -sS -o /dev/null -w "Landing:    HTTP %{http_code}\n" https://lupasolucoes.com/
curl -sS -o /dev/null -w "Healthz:    HTTP %{http_code}\n" https://lupasolucoes.com/healthz
curl -sS -o /dev/null -w "Admin:      HTTP %{http_code}\n" https://lupasolucoes.com/admin/
curl -sS -o /dev/null -w "Static SVG: HTTP %{http_code}\n" https://lupasolucoes.com/static/img/logo.svg
```

Espero `200/200/302/200` (admin redireciona pra login).

---

## Etapa 9 — Backup automático

```bash
# Edita o script /opt/lupa/scripts/backup.sh já existe
# Adiciona ao cron do paulo:
crontab -e
# Adiciona a linha:
# 0 3 * * * /opt/lupa/scripts/backup.sh >> /var/log/lupa-backup.log 2>&1
```

---

## Etapa 10 — GitHub Actions deploy (CI/CD contínuo)

No GitHub, em `Settings → Secrets and variables → Actions`, criar:

| Secret | Valor |
|---|---|
| `VPS_HOST` | `31.97.26.125` |
| `VPS_USER` | `paulo` |
| `VPS_PORT` | `22` |
| `VPS_SSH_KEY` | conteúdo de `~/.ssh/lupa_vps` (privada) |

Daí o workflow `deploy.yml` (já existe) faz auto-deploy a cada push em `main` que passa no CI.

---

## ✅ Checklist final

- [ ] Docker + compose instalados
- [ ] `/opt/lupa` clonado
- [ ] `/etc/lupa/lupa.env` com secrets reais (chmod 600)
- [ ] Postgres `lupa_v2` rodando isolado do legado
- [ ] Migrate + collectstatic OK
- [ ] Superuser criado
- [ ] Nginx + Certbot com HTTPS válido
- [ ] `https://lupasolucoes.com/healthz` retorna 200
- [ ] Backup diário no cron
- [ ] GitHub Actions deploy configurado
- [ ] Sentry recebendo eventos (se configurado)

---

## 🆘 Rollback

Se o deploy quebrar:

```bash
# Volta pra tag anterior
cd /opt/lupa
LUPA_TAG=<sha-anterior> docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d

# Rollback de migration (se a nova quebrou)
docker compose exec web python manage.py migrate <app> <migration_anterior>

# Restaurar backup
gunzip -c /var/backups/lupa/lupa_<data>.sql.gz | docker compose exec -T db pg_restore -U lupa_app -d lupa_v2
```
