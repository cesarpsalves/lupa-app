# Runbook: Deploy do LUPA em produção (VPS com Traefik existente)

> **Quem executa:** Claude (eu), após você confirmar o hardening.
> **Pré-requisito:** [01-vps-hardening.md](./01-vps-hardening.md) ✅
> **Tempo estimado:** 10–15 minutos.

---

## Contexto

O VPS `31.97.26.125` hospeda ~30 projetos via **Traefik** (em `/opt/traefik/`) que termina TLS e roteia por Host header. Cada projeto vive em `/opt/<nome>` com seu próprio `docker-compose.yml` e se conecta à network externa `traefik-public`. Labels Docker definem a rota; Traefik emite certs Let's Encrypt automaticamente (resolver `le`, HTTP-01 challenge).

LUPA segue o mesmo padrão dos outros projetos (referência: `/opt/pauloalves`).

```
Internet → Traefik :80/:443 → lupa-web:8000 → gunicorn → Django
                              ↓
                              db (postgres)
                              redis
```

Sem nginx próprio. Estáticos servidos por WhiteNoise (já no middleware), media servida pelo Django (`django.conf.urls.static`).

**Convenções de path:**
- Código: `/opt/lupa`
- Env de prod: `/etc/lupa/lupa.env` (chmod 600, fora do repo)
- Backups: `/var/backups/lupa/`
- Dados: volumes Docker nomeados (`lupa-pgdata`, `lupa-static`, `lupa-media`)

---

## Pré-deploy

- [ ] Hardening completo (paulo no sudo, SSH key, UFW, fail2ban) ✅
- [ ] Resend API key (`re_xxxxx`) na mão
- [ ] Email pro superuser do admin definido
- [ ] DKIM TXT `resend._domainkey` adicionado no DNS ✅
- [ ] (Opcional) Sentry DSN

---

## Etapa 1 — Docker

Já instalado no VPS (parte da stack existente). `paulo` adicionado ao grupo `docker`.

---

## Etapa 2 — Estrutura

```bash
sudo mkdir -p /opt/lupa /etc/lupa /var/backups/lupa
sudo chown paulo:paulo /opt/lupa /etc/lupa /var/backups/lupa
sudo chmod 700 /etc/lupa
```

---

## Etapa 3 — Clonar repo

```bash
cd /opt/lupa
git clone https://github.com/cesarpsalves/lupa-app.git .
```

Repo é público; sem token necessário.

---

## Etapa 4 — Gerar `/etc/lupa/lupa.env`

```bash
# Secrets aleatórios
SECRET_KEY=$(python3 -c 'from secrets import token_urlsafe; print(token_urlsafe(50))')
DB_PASS=$(python3 -c 'from secrets import token_urlsafe; print(token_urlsafe(32))')

# Escreve o env (chmod 600)
sudo install -m 600 -o paulo -g paulo /dev/null /etc/lupa/lupa.env
nano /etc/lupa/lupa.env
```

Conteúdo:

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<SECRET_KEY gerado>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=lupasolucoes.com,www.lupasolucoes.com,lupa-web
DJANGO_CSRF_TRUSTED_ORIGINS=https://lupasolucoes.com,https://www.lupasolucoes.com

# Postgres (container interno)
DATABASE_URL=postgres://lupa_app:<DB_PASS gerado>@db:5432/lupa_v2
POSTGRES_DB=lupa_v2
POSTGRES_USER=lupa_app
POSTGRES_PASSWORD=<DB_PASS gerado>

REDIS_URL=redis://redis:6379/0

# Email (Resend)
EMAIL_BACKEND=anymail.backends.resend.EmailBackend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=LUPA Soluções <nao-responda@lupasolucoes.com>

# HTTPS (Traefik termina TLS, mas redireciona e seta X-Forwarded-Proto=https)
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Aplicação
LUPA_DEFAULT_SIGNAL_PCT=50
LUPA_WAITLIST_THRESHOLD=15

# Observabilidade
SENTRY_DSN=
SENTRY_ENVIRONMENT=production

# Tag da imagem
LUPA_TAG=latest
```

---

## Etapa 5 — Garantir network `traefik-public` + login GHCR

```bash
docker network inspect traefik-public >/dev/null 2>&1 || docker network create traefik-public

# Imagem do LUPA é privada? Verificar visibilidade do package no GHCR.
# Se for pública: pull funciona sem login.
# Se for privada: docker login ghcr.io -u cesarpsalves
```

---

## Etapa 6 — Pull + up

```bash
cd /opt/lupa
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env pull
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env ps
```

O entrypoint do container `web` roda `migrate` + `collectstatic --clear` automaticamente. WhiteNoise serve estáticos via gunicorn. Traefik detecta o container pelas labels e emite cert TLS no primeiro request HTTPS (Let's Encrypt HTTP-01 challenge).

---

## Etapa 7 — Superuser

```bash
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env \
  exec web python manage.py createsuperuser
```

---

## Etapa 8 — Smoke test público

```bash
curl -sSI https://lupasolucoes.com/ | head -1            # 200
curl -sSI https://lupasolucoes.com/healthz | head -1     # 200
curl -sSI https://lupasolucoes.com/admin/ | head -1      # 302
curl -sSI http://lupasolucoes.com/ | head -1             # 301 → https
```

Se HTTPS falhar (`SSL handshake error`), Traefik ainda está negociando o cert com Let's Encrypt. Aguardar 30–60s e tentar de novo. Logs:

```bash
docker logs traefik 2>&1 | grep -i "lupa\|acme\|certificate" | tail -20
```

---

## Etapa 9 — Backup diário

```bash
crontab -e
# Adicionar:
0 3 * * * /opt/lupa/scripts/backup.sh >> /var/log/lupa-backup.log 2>&1

# Teste manual
/opt/lupa/scripts/backup.sh
ls -lh /var/backups/lupa/
```

---

## Etapa 10 — GitHub Actions deploy contínuo

No GitHub (`Settings → Secrets and variables → Actions`):

**Aba "Secrets" (environment "production"):**

| Secret | Valor |
|---|---|
| `VPS_HOST` | `31.97.26.125` |
| `VPS_USER` | `paulo` |
| `VPS_PORT` | `22` |
| `VPS_SSH_KEY` | conteúdo de `~/.ssh/hostinger_antigravity` (privada) |

**Aba "Variables" (Repository Variables):**

| Variable | Valor |
|---|---|
| `DEPLOY_ENABLED` | `true` |

A guarda `vars.DEPLOY_ENABLED == 'true'` no `deploy.yml` evita que pushs sem secrets configurados falhem.

---

## ✅ Checklist final

- [ ] Docker disponível pra paulo ✅
- [ ] `/opt/lupa` clonado
- [ ] `/etc/lupa/lupa.env` com secrets reais (chmod 600)
- [ ] Network `traefik-public` existe
- [ ] Postgres + Redis + Web no ar
- [ ] Migrate + collectstatic OK (rodam no entrypoint)
- [ ] Superuser criado
- [ ] Traefik emitiu cert TLS (logs sem erro)
- [ ] `https://lupasolucoes.com/healthz` → 200
- [ ] Redirect HTTP → HTTPS funciona
- [ ] Backup diário no cron
- [ ] GitHub Actions deploy configurado

---

## 🆘 Rollback

```bash
cd /opt/lupa
export LUPA_TAG=<sha-anterior>
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d --force-recreate web

# Migration anterior (se a nova quebrou)
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env \
  exec web python manage.py migrate <app> <migration_anterior>

# Restaurar backup
gunzip -c /var/backups/lupa/lupa_<data>.sql.gz | \
  docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env \
  exec -T db pg_restore -U lupa_app -d lupa_v2 --clean --if-exists
```
