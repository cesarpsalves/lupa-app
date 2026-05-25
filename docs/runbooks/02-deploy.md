# Runbook: Deploy do LUPA em produção

> **Quem executa:** Claude (eu), após você confirmar o hardening.
> **Pré-requisito:** [01-vps-hardening.md](./01-vps-hardening.md) ✅
> **Tempo estimado:** 20–30 minutos.

---

## Visão geral

```
Você: ✅ hardening pronto + SSH key + Resend API key + email superuser
  ↓
1. Instalo Docker + Compose no VPS
2. Crio /opt/lupa e /etc/lupa/lupa.env (com SECRET_KEY gerado)
3. Subo db + redis + web (Postgres lupa_v2 isolado do legado)
4. Migrate + collectstatic + superuser
5. Subo nginx em BOOTSTRAP (HTTP-only, sem SSL) — smoke test pelo IP
  ↓
Você troca DNS lupasolucoes.com → 31.97.26.125 (Fase 4 do runbook 00)
  ↓
6. Certbot --webroot emite cert TLS
7. Switch nginx pra config HTTPS final + reload
8. Setup backup diário + GitHub Actions deploy
9. Smoke test público
  ↓
🚀 https://lupasolucoes.com
```

**Convenções de path no VPS:**
- Código: `/opt/lupa` (clone do repo)
- Env de prod: `/etc/lupa/lupa.env` (chmod 600, fora do repo)
- Backups: `/var/backups/lupa/`
- Cert TLS: `/etc/letsencrypt/` (gerenciado pelo Certbot do host)
- Dados do Postgres/static/media: **volumes Docker nomeados** (`lupa-pgdata`, `lupa-static`, `lupa-media`) — ficam em `/var/lib/docker/volumes/`. Não criar `/var/lib/lupa/` manualmente.

---

## Pré-deploy (você confirma)

- [ ] DNS `lupasolucoes.com` ainda aponta pro servidor antigo (`2.24.107.203`) — vamos trocar SÓ depois da Fase 5
- [ ] Resend: conta criada, domínio adicionado, API key (`re_xxxxx`) anotada
- [ ] Email pro superuser do admin definido
- [ ] (Opcional) Sentry: DSN anotado

---

## Etapa 1 — Instalar Docker + Compose

Como `paulo` no VPS:

```bash
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker paulo
# Relogar ou: newgrp docker
docker compose version
```

---

## Etapa 2 — Estrutura no VPS

```bash
sudo mkdir -p /opt/lupa
sudo chown paulo:paulo /opt/lupa

sudo mkdir -p /etc/lupa
sudo chown paulo:paulo /etc/lupa
sudo chmod 700 /etc/lupa

# Webroot pro ACME challenge do Certbot
sudo mkdir -p /var/www/certbot
sudo chown -R paulo:paulo /var/www/certbot

# Diretório de backups
sudo mkdir -p /var/backups/lupa
sudo chown paulo:paulo /var/backups/lupa
```

---

## Etapa 3 — Clonar o repo

```bash
cd /opt/lupa
git clone https://github.com/cesarpsalves/lupa-app.git .
```

---

## Etapa 4 — Gerar `/etc/lupa/lupa.env`

```bash
# SECRET_KEY forte
python3 -c 'from secrets import token_urlsafe; print(token_urlsafe(50))'
# senha do Postgres
python3 -c 'from secrets import token_urlsafe; print(token_urlsafe(32))'

nano /etc/lupa/lupa.env
chmod 600 /etc/lupa/lupa.env
```

Conteúdo (substituir `<...>`):

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<gerado-acima>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=lupasolucoes.com,www.lupasolucoes.com,31.97.26.125
DJANGO_CSRF_TRUSTED_ORIGINS=https://lupasolucoes.com,https://www.lupasolucoes.com

# Postgres (container)
DATABASE_URL=postgres://lupa_app:<senha-db>@db:5432/lupa_v2
POSTGRES_DB=lupa_v2
POSTGRES_USER=lupa_app
POSTGRES_PASSWORD=<senha-db>

REDIS_URL=redis://redis:6379/0

# Email
EMAIL_BACKEND=anymail.backends.resend.EmailBackend
RESEND_API_KEY=<do Resend>
DEFAULT_FROM_EMAIL=LUPA Soluções <nao-responda@lupasolucoes.com>

# ⚠ HTTPS — DESLIGADO no bootstrap pra primeira subida HTTP-only funcionar.
# Vou ligar pra True/31536000 depois do Certbot emitir o cert (Etapa 8).
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Nginx config: bootstrap usa nginx.bootstrap.conf (HTTP-only).
# Vou trocar pra nginx.conf depois do Certbot.
NGINX_CONF=nginx.bootstrap.conf

# Aplicação
LUPA_DEFAULT_SIGNAL_PCT=50
LUPA_WAITLIST_THRESHOLD=15

# Observabilidade
SENTRY_DSN=
SENTRY_ENVIRONMENT=production

# Tag da imagem Docker (CI publica em ghcr.io/cesarpsalves/lupa)
LUPA_TAG=latest
```

---

## Etapa 5 — Subir db + redis + web

```bash
cd /opt/lupa
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env pull
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d db redis

# Espera Postgres ficar healthy (~10s)
docker compose -f docker/docker-compose.prod.yml ps

docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d web
```

O entrypoint do container `web` roda `migrate` + `collectstatic` automaticamente. Os estáticos são gravados no volume `lupa-static` (montado em `/app/staticfiles` no web, lido pelo nginx em `/var/www/static`).

---

## Etapa 6 — Superuser

```bash
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env \
  exec web python manage.py createsuperuser
```

Email pego do que você me passou (Pré-deploy).

---

## Etapa 7 — Subir nginx em modo bootstrap (HTTP-only) + smoke test pelo IP

```bash
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d nginx

# Smoke test pelo IP (DNS ainda aponta pro app antigo)
curl -sS -o /dev/null -w "Landing:    HTTP %{http_code}\n" -H "Host: lupasolucoes.com" http://31.97.26.125/
curl -sS -o /dev/null -w "Healthz:    HTTP %{http_code}\n" -H "Host: lupasolucoes.com" http://31.97.26.125/healthz
curl -sS -o /dev/null -w "Admin:      HTTP %{http_code}\n" -H "Host: lupasolucoes.com" http://31.97.26.125/admin/
```

Esperado: `200 / 200 / 302`. Se OK → **aviso você** pra fazer a Fase 4 do runbook 00 (trocar DNS).

---

## ⏸ Aguarda você trocar o DNS (runbook 00, Fase 4)

Eu confirmo propagação:

```bash
dig +short lupasolucoes.com @8.8.8.8
dig +short lupasolucoes.com @1.1.1.1
# Espero ambos retornarem 31.97.26.125
```

---

## Etapa 8 — Certbot emite cert TLS (--webroot)

```bash
sudo apt install certbot -y

# Cria cert via challenge HTTP-01 servido pelo nginx bootstrap em /.well-known/acme-challenge/
sudo certbot certonly --webroot -w /var/www/certbot \
  -d lupasolucoes.com -d www.lupasolucoes.com \
  --non-interactive --agree-tos -m contato@lupasolucoes.com

# Cron de renovação (--webroot funciona sem reload do nginx)
sudo systemctl status certbot.timer
```

---

## Etapa 9 — Switch pra HTTPS

Editar `/etc/lupa/lupa.env`:

```env
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
NGINX_CONF=nginx.conf
```

Recriar nginx e web pra pegar a nova config:

```bash
cd /opt/lupa
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d --force-recreate web nginx
```

---

## Etapa 10 — Smoke test público

```bash
curl -sSI https://lupasolucoes.com/ | head -1            # 200
curl -sSI https://lupasolucoes.com/healthz | head -1     # 200
curl -sSI https://lupasolucoes.com/admin/ | head -1      # 302
curl -sSI http://lupasolucoes.com/ | head -1             # 301 → https
```

---

## Etapa 11 — Backup diário no cron

```bash
crontab -e
# Adiciona:
0 3 * * * /opt/lupa/scripts/backup.sh >> /var/log/lupa-backup.log 2>&1
```

Teste manual:

```bash
/opt/lupa/scripts/backup.sh
ls -lh /var/backups/lupa/
```

---

## Etapa 12 — GitHub Actions deploy contínuo

No GitHub (`Settings → Secrets and variables → Actions`):

**Aba "Secrets" (na environment "production"):**

| Secret | Valor |
|---|---|
| `VPS_HOST` | `31.97.26.125` |
| `VPS_USER` | `paulo` |
| `VPS_PORT` | `22` |
| `VPS_SSH_KEY` | conteúdo de `~/.ssh/lupa_vps` (privada, gerada por você) |

**Aba "Variables" (Repository Variables, não Environment):**

| Variable | Valor |
|---|---|
| `DEPLOY_ENABLED` | `true` |

⚠ O `deploy.yml` tem uma guarda `vars.DEPLOY_ENABLED == 'true'` — sem essa variável, o job é pulado em vez de falhar. Isso evita o erro `missing server host` que rolaria a cada push enquanto os secrets ainda não existem.

Daí cada push em `main` que passa no CI dispara `deploy.yml` automaticamente.

---

## ✅ Checklist final

- [ ] Docker + Compose instalados
- [ ] `/opt/lupa` clonado
- [ ] `/etc/lupa/lupa.env` com secrets reais (chmod 600)
- [ ] Postgres `lupa_v2` rodando isolado do legado
- [ ] Migrate + collectstatic OK (rodam no entrypoint)
- [ ] Superuser criado
- [ ] Nginx bootstrap respondendo HTTP pelo IP
- [ ] DNS trocado e propagado
- [ ] Certbot emitiu cert TLS
- [ ] Nginx switched pra `nginx.conf` (HTTPS)
- [ ] `https://lupasolucoes.com/healthz` retorna 200
- [ ] Redirect HTTP → HTTPS funcionando
- [ ] Backup diário no cron
- [ ] GitHub Actions deploy configurado
- [ ] (Opcional) Sentry recebendo eventos

---

## 🆘 Rollback

```bash
# Volta pra tag anterior
cd /opt/lupa
export LUPA_TAG=<sha-anterior>
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env up -d

# Reverter migration (se a nova quebrou algo)
docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env \
  exec web python manage.py migrate <app> <migration_anterior>

# Restaurar último backup
gunzip -c /var/backups/lupa/lupa_<data>.sql.gz | \
  docker compose -f docker/docker-compose.prod.yml --env-file /etc/lupa/lupa.env \
  exec -T db pg_restore -U lupa_app -d lupa_v2 --clean --if-exists
```
