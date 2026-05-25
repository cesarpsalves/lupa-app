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

**Convenções de path** (mesmas dos outros projetos do VPS, ex: `/opt/.env.carsena`, `/opt/update-carsena.sh`):
- Código: `/opt/lupa/`
- Env de prod: `/opt/.env.lupa` (root:root, chmod 600)
- Script de deploy: `/opt/update-lupa.sh` → symlink pra `/opt/lupa/scripts/deploy-vps.sh`
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
sudo mkdir -p /opt/lupa /var/backups/lupa
sudo chown paulo:paulo /opt/lupa /var/backups/lupa
```

---

## Etapa 3 — Clonar repo

```bash
cd /opt/lupa
git clone https://github.com/cesarpsalves/lupa-app.git .
```

Repo é público; sem token necessário.

---

## Etapa 4 — Gerar `/opt/.env.lupa`

```bash
SECRET_KEY=$(python3 -c 'from secrets import token_urlsafe; print(token_urlsafe(50))')
DB_PASS=$(python3 -c 'from secrets import token_urlsafe; print(token_urlsafe(32))')

# root:root chmod 600 (padrão dos outros /opt/.env.*)
sudo install -m 600 -o root -g root /dev/null /opt/.env.lupa
sudo nano /opt/.env.lupa
```

Conteúdo:

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<SECRET_KEY gerado>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=lupasolucoes.com,www.lupasolucoes.com,lupa-web
DJANGO_CSRF_TRUSTED_ORIGINS=https://lupasolucoes.com,https://www.lupasolucoes.com

DATABASE_URL=postgres://lupa_app:<DB_PASS gerado>@db:5432/lupa_v2
POSTGRES_DB=lupa_v2
POSTGRES_USER=lupa_app
POSTGRES_PASSWORD=<DB_PASS gerado>

REDIS_URL=redis://redis:6379/0

EMAIL_BACKEND=anymail.backends.resend.EmailBackend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=LUPA Soluções <nao-responda@lupasolucoes.com>

SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

LUPA_DEFAULT_SIGNAL_PCT=50
LUPA_WAITLIST_THRESHOLD=15

SENTRY_DSN=
SENTRY_ENVIRONMENT=production

LUPA_TAG=latest
```

---

## Etapa 5 — Instalar script de deploy + GHCR

```bash
# Symlink no padrão dos outros /opt/update-*.sh
sudo ln -sf /opt/lupa/scripts/deploy-vps.sh /opt/update-lupa.sh
sudo chmod +x /opt/lupa/scripts/deploy-vps.sh

# Network do Traefik (idempotente)
docker network inspect traefik-public >/dev/null 2>&1 || docker network create traefik-public

# Imagem GHCR: tornar package público em
#   https://github.com/users/cesarpsalves/packages/container/lupa/settings
# (alternativa: docker login ghcr.io -u cesarpsalves com PAT read:packages)
```

---

## Etapa 6 — Deploy

```bash
sudo /opt/update-lupa.sh
```

O script faz:
1. `git fetch + reset --hard origin/main`
2. `docker compose pull web` (puxa imagem do GHCR)
3. `docker compose up -d --remove-orphans`
4. Espera `lupa-web` ficar healthy (até 60s)
5. Smoke test interno em `/healthz`

O entrypoint do container roda migrate + collectstatic. WhiteNoise serve estáticos. Traefik emite cert TLS Let's Encrypt no primeiro request HTTPS.

---

## Etapa 7 — Superuser

```bash
docker compose -p lupa -f /opt/lupa/docker/docker-compose.prod.yml --env-file /opt/.env.lupa \
  exec web python manage.py createsuperuser
# Email: paulo.agoravai@gmail.com
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

⚠ O `deploy.yml` precisa rodar `sudo /opt/update-lupa.sh` no VPS (em vez de comandos docker diretamente como está hoje). TODO depois do MVP no ar: atualizar `.github/workflows/deploy.yml` pra invocar o script.

Por enquanto, no GitHub (`Settings → Secrets and variables → Actions`):

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
- [ ] `/opt/.env.lupa` (root:root chmod 600) com secrets reais
- [ ] `/opt/update-lupa.sh` symlink criado
- [ ] Network `traefik-public` existe
- [ ] Imagem GHCR pública (ou `docker login` feito)
- [ ] Postgres + Redis + Web no ar
- [ ] Migrate + collectstatic OK (rodam no entrypoint)
- [ ] Superuser criado
- [ ] Traefik emitiu cert TLS (logs sem erro)
- [ ] `https://lupasolucoes.com/healthz` → 200
- [ ] Redirect HTTP → HTTPS funciona
- [ ] Backup diário no cron
- [ ] GitHub Actions deploy configurado (após atualizar deploy.yml pra usar script)

---

## 🆘 Rollback

```bash
cd /opt/lupa
export LUPA_TAG=<sha-anterior>
docker compose -p lupa -f docker/docker-compose.prod.yml --env-file /opt/.env.lupa up -d --force-recreate web

# Migration anterior (se a nova quebrou)
docker compose -p lupa -f docker/docker-compose.prod.yml --env-file /opt/.env.lupa \
  exec web python manage.py migrate <app> <migration_anterior>

# Restaurar backup
gunzip -c /var/backups/lupa/lupa_<data>.sql.gz | \
  docker compose -p lupa -f docker/docker-compose.prod.yml --env-file /opt/.env.lupa \
  exec -T db pg_restore -U lupa_app -d lupa_v2 --clean --if-exists
```
