# Runbook: Migração para produção (Opção B — troca direta)

> Plano consolidado. ~30 min de trabalho ativo + ~4h aguardando propagação DNS.
> Aceita-se downtime do `lupasolucoes.com` durante a propagação.

## Estado atual (auditado em 25/05/2026)

| | Servidor antigo (que vai ser desligado) | Seu VPS pessoal (destino) |
|---|---|---|
| Hostname | `srv1682631.hstgr.cloud` (conta KFP) | `srv851630.hstgr.cloud` (sua conta) |
| IP | `2.24.107.203` | `31.97.26.125` |
| O que roda | `pixel-perfect-match` (LUPA v1) | Supabase legado + porta 80/443 retornando 404 |
| Domínio | `lupasolucoes.com` aponta aqui hoje | Sem domínio apontado |

**Registrar:** GoDaddy. **DNS gerenciado em:** painel Hostinger (nameservers `dns-parking.com`). **TTL atual:** 14332s (~4h).

---

## Sequência

### 🟡 Fase 1 — Hardening (você, ~10 min)

Executa o [01-vps-hardening.md](./01-vps-hardening.md). Resumo:

1. Trocar senha root (`passwd root`)
2. Criar usuário `paulo` + SSH key
3. `PermitRootLogin no` + `PasswordAuthentication no`
4. UFW + fail2ban

✅ Confirma com **"hardening pronto"** + me passa o conteúdo da **chave pública** `~/.ssh/lupa_vps.pub`.

### 🟡 Fase 2 — Pré-requisitos externos (você, ~10 min)

1. **Resend**: criar conta em https://resend.com/signup
   - Adicionar domínio `lupasolucoes.com` no painel
   - Configurar SPF + DKIM (eles dão os registros DNS — guarda eles, vai usar na Fase 4)
   - Pegar API key (formato `re_xxxxx`) — me passa
2. **Email do superuser de produção** — qual email você quer pra logar no admin? (geralmente o seu de trabalho)
3. **(Opcional) Sentry**: criar projeto Django em https://sentry.io — me passa o DSN

### 🟢 Fase 3 — Deploy (eu, ~15 min)

Executo o [02-deploy.md](./02-deploy.md):
1. Instalar Docker + Compose no VPS
2. Clone do repo em `/opt/lupa`
3. Gerar `.env` com secrets em `/etc/lupa/lupa.env` (modo bootstrap: HTTPS off)
4. Subir Postgres `lupa_v2` (isolado do Supabase legado), Redis e web
5. Migrate + collectstatic (rodam no entrypoint) + criar superuser
6. Subir Nginx em **modo bootstrap** (HTTP-only, sem SSL — pra Certbot poder fazer ACME challenge depois)
7. Smoke test pelo IP: `curl -H "Host: lupasolucoes.com" http://31.97.26.125/healthz` → 200

✅ Aviso quando estiver pronto.

### 🟡 Fase 4 — Trocar DNS (você, ~5 min) — **AQUI COMEÇA O DOWNTIME**

No painel Hostinger (gerenciamento de DNS do domínio):
1. Login em https://hpanel.hostinger.com
2. **Domínios → lupasolucoes.com → DNS / Nameservers**
3. **Editar zona DNS**:
   - `A` record raiz: `2.24.107.203` → **`31.97.26.125`**
   - `A` record `www`: `2.24.107.203` → **`31.97.26.125`**
4. (Opcional) Baixar TTL pra `300s` antes da troca pra propagar mais rápido — só ajuda se for feito ANTES, com tempo
5. **Adicionar registros do Resend** (SPF + DKIM da Fase 2)

✅ Avisa quando trocar.

### 🟢 Fase 5 — Certbot HTTPS + switch (eu, ~5 min)

Quando o DNS já estiver propagado pra alguns nodes (testo com `dig @8.8.8.8` e `dig @1.1.1.1`):
```
sudo certbot certonly --webroot -w /var/www/certbot \
  -d lupasolucoes.com -d www.lupasolucoes.com
```
Cert emitido via challenge HTTP-01 servido pelo nginx bootstrap. Daí edito `/etc/lupa/lupa.env` ligando `SECURE_SSL_REDIRECT=True`, `NGINX_CONF=nginx.conf` e faço `docker compose up -d --force-recreate web nginx`. HTTPS no ar + redirect HTTP → HTTPS automático.

### 🟢 Fase 6 — Smoke test público (eu)

```
curl -sI https://lupasolucoes.com → 200
curl -sI https://lupasolucoes.com/healthz → 200
curl -sI https://lupasolucoes.com/admin/ → 302
```

Confirma que o LUPA v2 está respondendo no domínio.

### 🟡 Fase 7 — Desligar o app antigo (você, ~5 min)

No painel Hostinger da **conta KFP** (que hospeda `srv1682631.hstgr.cloud`):
1. Acessa o servidor
2. Para o serviço do `pixel-perfect-match` (provavelmente `docker compose down` ou `systemctl stop ...`)
3. Confirma que o app antigo não responde mais
4. (Quando seguro) Apaga a VM ou libera o servidor

### 🟢 Fase 8 — Monitoramento pós-deploy (eu + você)

Por 24-48h:
- Sentry recebendo erros
- Healthchecks.io alertando se sair
- Backup `pg_dump` rodando no cron (3h da manhã)
- GitHub Actions deploy testado com um commit trivial

---

## ⚠️ Pontos críticos

- **Não troca o DNS antes da Fase 3 completar**. Senão o site fica fora sem nada pronto pra responder.
- **NÃO me passa senha de novo em mensagem**. Tudo vai por SSH key.
- **Backup do app antigo** antes de desligar — `pg_dump` do Postgres legado, exportar uploads se houver. Mesmo que o usuário não use mais, dá pra restaurar se faltar algo.

## Rollback de emergência

Se algo der errado depois da Fase 4 e você quiser voltar imediatamente:
1. No painel Hostinger DNS: A record raiz/www → `2.24.107.203`
2. App antigo continua respondendo no servidor KFP (não foi desligado ainda)
3. Em ~4h o domínio volta pro estado anterior

Por isso a Fase 7 (desligar antigo) vem só depois da Fase 6 (smoke test público).
