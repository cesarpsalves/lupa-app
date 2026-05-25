# LUPA — Segurança

> Documento autoritativo de segurança. Toda credencial, token ou segredo segue as regras aqui.

## 1. Princípios

1. **Zero segredos no repo.** Nenhuma chave, senha, token ou string de conexão entra em arquivo versionado. `.env` está no `.gitignore` desde o commit 0.
2. **Princípio do menor privilégio.** Usuários do banco, do servidor e da aplicação têm exatamente as permissões que precisam — nada além.
3. **Defesa em profundidade.** Várias camadas (firewall + auth + RBAC + RLS lógico no Django + audit log) devem falhar para haver brecha.
4. **Tudo audita-se.** Operações sensíveis (login, alteração financeira, cancelamento) gravam audit log com `user_id`, `ip`, `timestamp`, `before/after`.
5. **Falhar fechado.** Em dúvida sobre permissão, negar acesso. Erros não vazam stack trace em produção.

## 2. Plano de rotação imediata (ação do usuário)

Pré-requisito para qualquer deploy ou conexão ao VPS. **Senha root foi exposta em conversa** — está queimada.

### 2.1. Trocar senha root do VPS

```bash
ssh root@<ip>
passwd root          # nova senha forte (>20 chars, gerada com pwgen ou similar)
```

### 2.2. Criar usuário não-root e configurar chave SSH

Na sua máquina local:

```bash
ssh-keygen -t ed25519 -C "paulo-vps-$(date +%Y%m%d)" -f ~/.ssh/lupa_vps
```

No VPS (como root, por enquanto):

```bash
adduser paulo
usermod -aG sudo paulo
mkdir -p /home/paulo/.ssh
# Copiar conteúdo de ~/.ssh/lupa_vps.pub para:
nano /home/paulo/.ssh/authorized_keys
chown -R paulo:paulo /home/paulo/.ssh
chmod 700 /home/paulo/.ssh
chmod 600 /home/paulo/.ssh/authorized_keys
```

Testar de outra janela **antes** de fechar a sessão root:

```bash
ssh -i ~/.ssh/lupa_vps paulo@<ip>
sudo whoami    # deve retornar "root"
```

### 2.3. Hardening SSH

Editar `/etc/ssh/sshd_config` no VPS:

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers paulo
```

Recarregar e validar (sem fechar a sessão atual):

```bash
sudo sshd -t                      # valida config
sudo systemctl reload ssh
```

### 2.4. Firewall mínimo (UFW)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

### 2.5. Fail2ban contra brute-force

```bash
sudo apt install fail2ban -y
sudo systemctl enable --now fail2ban
```

### 2.6. Trocar senha do Postgres/Supabase

Se a senha SSH exposta foi reusada em qualquer lugar (Postgres, Supabase admin, painéis), **rotacionar todas**.

### 2.7. Auditar logs recentes

```bash
sudo last -F | head -50           # logins recentes
sudo lastb -F | head -50          # tentativas falhadas
sudo journalctl -u ssh --since "7 days ago" | grep -Ei 'accepted|failed'
```

Procurar IPs/usuários que você não reconhece.

## 3. Secrets management no projeto Django

### 3.1. Estrutura

```
.env                    # NUNCA versionado; gerado localmente
.env.example            # versionado; só placeholders
config/settings/
  base.py               # comum
  dev.py                # SECURE_SSL_REDIRECT=False, DEBUG=True
  prod.py               # DEBUG=False, SECURE_*=True
```

### 3.2. Variáveis sensíveis (vão pro `.env`)

```env
SECRET_KEY=<gerada com django.core.management.utils.get_random_secret_key()>
DATABASE_URL=postgres://user:pass@host:5432/lupa_v2
EMAIL_HOST_PASSWORD=
SENTRY_DSN=
ALLOWED_HOSTS=lupa.pauloalves.dev,localhost
CSRF_TRUSTED_ORIGINS=https://lupa.pauloalves.dev
```

### 3.3. Carregamento

`django-environ` ou `pydantic-settings` no `base.py`. Falha fechado: se variável obrigatória ausente, app não sobe.

### 3.4. Em produção

Variáveis no `systemd` unit file (`EnvironmentFile=/etc/lupa/lupa.env`) com permissão `600` e dono `lupa:lupa`. Nunca em arquivo legível por outros usuários.

## 4. Configurações Django de produção

```python
# config/settings/prod.py
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000          # 1 ano (só após validar HTTPS)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
```

CSP via `django-csp` para evitar XSS:

```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")   # revisar quando frontend maduro
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

## 5. Autenticação

- **Senhas:** Argon2id como hasher principal (`PASSWORD_HASHERS`), bcrypt como fallback.
- **Política:** mínimo 12 chars, validadores Django nativos + bloquear top-1000 senhas comuns.
- **Bloqueio:** `django-axes` — 5 falhas em 5 min = bloqueio de 30 min + alerta no log.
- **2FA:** `django-otp` + TOTP para contas com role admin/owner. Opcional para `employee` (recomendado).
- **Sessão:** `SESSION_COOKIE_AGE = 60 * 60 * 8` (8h). `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`.
- **Reset de senha:** token de uso único, expira em 30min, invalidado após primeiro uso.

## 6. Autorização (multi-tenant)

Modelo: **shared-database, shared-schema** com `company_id` em toda tabela de tenant.

- Middleware `TenantMiddleware` resolve `request.company` a partir do user logado.
- Manager customizado `TenantQuerySet` aplica `.filter(company=request.company)` automaticamente em todo `Model.objects`.
- Views nunca recebem `company_id` por parâmetro — sempre do `request.company`.
- Testes obrigatórios: cross-tenant access deve retornar 404 (não 403 — não vazar existência).

Roles via `django-guardian` ou enum simples:

| Role | Pode |
|---|---|
| `owner` | Tudo dentro da empresa, incluindo billing e exclusão |
| `manager` | Tudo operacional, sem billing/exclusão |
| `employee` | Apenas seus próprios atendimentos |
| `viewer` | Read-only (contador, sócio passivo) |

## 7. LGPD

- **Base legal:** execução de contrato (cliente final cadastrado) + legítimo interesse (auditoria/segurança).
- **Dados pessoais coletados:** nome, CPF/CNPJ, telefone, email, endereço, histórico de atendimentos.
- **Direitos do titular:**
  - Exportação (`GET /privacy/export` — JSON de todos os dados do user)
  - Exclusão (`POST /privacy/delete` — soft delete + purge em 30 dias)
  - Retificação (formulário de perfil)
- **Retenção:** dados financeiros 5 anos (legal); demais 2 anos após inatividade, depois purge.
- **Encarregado (DPO):** contato em `/privacidade`.
- **Cookies:** banner de consent para analytics; essenciais (auth, csrf) dispensam consent.
- **Audit log:** toda leitura de dado sensível de cliente por outro usuário é logada.

## 8. Banco de dados

- **Não usar `postgres` superuser na aplicação.** Criar usuário `lupa_app` com permissões só na database `lupa_v2`.
- **TLS na conexão.** `?sslmode=require` no `DATABASE_URL`.
- **Backup diário.** `pg_dump` cron + retenção 14 dias local + 30 dias num bucket S3-compatible.
- **Encryption at rest:** depende do provedor; documentar limitação se não disponível no Supabase self-hosted.

## 9. Dependências

- **`pip-audit` no CI** — falha o build se houver CVE de severidade alta.
- **Renovate ou Dependabot** — PRs automáticos de update.
- **Pin de versões** em `requirements.txt` (gerado via `pip-tools`).

## 10. Headers / proxy / CDN

- **Nginx** na frente do Gunicorn:
  - HTTP/2, rate limit por IP (`limit_req_zone`).
  - `client_max_body_size` apropriado (uploads de imagens).
  - Bloqueio de paths sensíveis (`/.git`, `/.env`, `wp-admin`, etc).
- **Certbot** com renovação automática (`certbot renew --post-hook 'systemctl reload nginx'` no cron).

## 11. Monitoramento

- **Sentry** para exceções (free tier).
- **Healthcheck endpoint** `/healthz` (banco, cache, disk).
- **Uptime Robot** ou similar pingando `/healthz` a cada 5min.

## 12. Incident response

- **Runbook mínimo** em `docs/runbooks/incident.md` (a criar): quem, o quê, comunicação.
- **Logs centralizados** — `journalctl` + envio para arquivo rotacionado; futuro: Loki/Grafana.

## 13. Checklist pré-deploy

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` único de produção (não o de dev)
- [ ] `ALLOWED_HOSTS` setado
- [ ] HTTPS funcionando + redirect
- [ ] `pip-audit` limpo
- [ ] Backup automático funcionando (testado restore)
- [ ] Sentry recebendo eventos
- [ ] Rate limit no Nginx ativo
- [ ] Senha do banco rotacionada vs valor de dev
- [ ] 2FA ativo na conta `owner`
