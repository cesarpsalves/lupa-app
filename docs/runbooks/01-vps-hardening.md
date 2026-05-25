# Runbook: Hardening do VPS

> **Quem executa:** você (Paulo).
> **Quando:** antes do primeiro deploy.
> **Por quê:** a senha SSH foi exposta em conversa, e mesmo se não tivesse sido, root direto + senha é fraco demais pra produção.
> **Tempo estimado:** 10–15 minutos.

---

## Pré-requisitos

- Acesso SSH atual ao VPS (`root@31.97.26.125`).
- Terminal local (Mac, Linux ou WSL).
- Editor de texto (`nano` ou `vim` no servidor).

---

## Etapa 1 — Gerar chave SSH na sua máquina local

**Pula esta etapa se você já tem `~/.ssh/id_ed25519` ou outra chave ed25519/rsa.**

Na sua máquina (Mac):

```bash
ssh-keygen -t ed25519 -C "paulo-vps-$(date +%Y%m%d)" -f ~/.ssh/lupa_vps
```

Quando perguntar senha (passphrase), use **uma passphrase forte** (recomendado) ou Enter pra sem passphrase. Vai gerar 2 arquivos:

- `~/.ssh/lupa_vps` (privada, **nunca compartilhe**)
- `~/.ssh/lupa_vps.pub` (pública, pode colar em qualquer lugar)

Veja a pública:

```bash
cat ~/.ssh/lupa_vps.pub
```

Copie a saída inteira (vai começar com `ssh-ed25519 AAAA...`). Você vai usar no Etapa 3.

---

## Etapa 2 — Conectar ao VPS e trocar a senha root

```bash
ssh root@31.97.26.125
```

Quando estiver dentro:

```bash
passwd root
```

Digita **duas vezes** uma senha forte nova (≥20 caracteres, gere com `openssl rand -base64 24` se quiser). **Anota num gerenciador de senhas** — você ainda vai precisar dela no Etapa 5 antes de desligarmos login por senha.

---

## Etapa 3 — Criar usuário `paulo` com SSH key

Ainda como root no VPS:

```bash
adduser paulo
# Quando perguntar senha: define uma. Vamos desabilitar depois.
# Outros campos (nome, telefone) podem ficar em branco.

usermod -aG sudo paulo

# Configura SSH key
mkdir -p /home/paulo/.ssh
nano /home/paulo/.ssh/authorized_keys
```

No editor `nano`: **cole o conteúdo da chave pública** que você copiou na Etapa 1 (a linha inteira que começa com `ssh-ed25519 AAAA...`). Salva com `Ctrl+O`, Enter, sai com `Ctrl+X`.

Ajusta as permissões:

```bash
chown -R paulo:paulo /home/paulo/.ssh
chmod 700 /home/paulo/.ssh
chmod 600 /home/paulo/.ssh/authorized_keys
```

---

## Etapa 4 — Testar login como `paulo` (deixa o root logado!)

**NÃO feche a sessão root ainda.** Abre **outra janela do terminal local** e testa:

```bash
ssh -i ~/.ssh/lupa_vps paulo@31.97.26.125
```

Deve entrar sem pedir senha (só a passphrase da chave, se você definiu uma). Confirma que vira root:

```bash
sudo whoami
```

Se retornar `root` → tudo OK. **Não feche essa segunda janela ainda.**

Se deu erro: volta na janela do root e corrige (provavelmente foi um typo na chave ou nas permissões).

---

## Etapa 5 — Hardening do SSHd

Na janela do **paulo** (sudo):

```bash
sudo nano /etc/ssh/sshd_config
```

Procura e ajusta (ou adiciona) estas linhas (Ctrl+W no nano pra buscar):

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers paulo
```

Se a linha existir mas estiver comentada (`#`), tira o `#`. Salva e sai.

Valida a sintaxe (importante, senão pode te deixar fora):

```bash
sudo sshd -t
```

Se não imprimiu nada → tá OK. Recarrega:

```bash
sudo systemctl reload ssh
```

**Abre uma TERCEIRA janela** e testa que `paulo` ainda entra:

```bash
ssh -i ~/.ssh/lupa_vps paulo@31.97.26.125
```

Se entrou → 🎉. Agora pode fechar a janela do `root` antiga.

Tenta também (deve **falhar**):

```bash
ssh root@31.97.26.125
# Permission denied
```

---

## Etapa 6 — Firewall (UFW)

Como `paulo`:

```bash
sudo apt update
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
# digita "y"
sudo ufw status verbose
```

Deve listar as 3 portas (22, 80, 443) como permitidas.

---

## Etapa 7 — Fail2ban (anti-brute-force)

```bash
sudo apt install fail2ban -y
sudo systemctl enable --now fail2ban
sudo systemctl status fail2ban
# verifica que está "active (running)"
```

---

## Etapa 8 — Auditar logs (sanity check)

```bash
# Logins bem-sucedidos nos últimos dias
sudo last -F | head -30

# Tentativas falhadas recentes
sudo lastb -F | head -30

# SSH específico
sudo journalctl -u ssh --since "7 days ago" | grep -Ei 'accepted|failed' | head -50
```

Se aparecer **IP estranho** com `Accepted` ou um volume alto de `Failed` de um IP só, você tem um problema (mas o hardening que você acabou de fazer já mitiga).

---

## Etapa 9 — (Opcional) Trocar senha do Postgres / Supabase legado

Se a senha exposta foi reusada em qualquer outro lugar (Postgres legado, painéis do Supabase, etc.), **rotacione tudo**. O LUPA novo vai ter senha própria gerada no deploy.

---

## ✅ Checklist final

- [ ] Senha root rotacionada
- [ ] Usuário `paulo` criado com SSH key
- [ ] `PermitRootLogin no` no `sshd_config`
- [ ] `PasswordAuthentication no` no `sshd_config`
- [ ] SSH `paulo` funciona via chave
- [ ] SSH `root` falha
- [ ] UFW ativo com portas 22/80/443
- [ ] Fail2ban rodando
- [ ] Senha do Postgres rotacionada (se aplicável)

Quando terminar, me avise com **"hardening pronto"** e eu sigo com o [02-deploy.md](./02-deploy.md).

---

## 🆘 Se algo der errado

**Travei fora do servidor (perdi acesso SSH)**:
- O VPS Hostinger tem console web no painel. Acessa por lá, ajusta o que faltou, recarrega o sshd.

**O sshd não inicia depois do reload**:
- Sempre dá `sudo sshd -t` ANTES do `reload`. Se aceitou e ainda assim quebrou, edita pelo console web e reverte a linha.

**Esqueci a passphrase da SSH key**:
- Gera uma nova: `ssh-keygen -t ed25519 -f ~/.ssh/lupa_vps_v2`. Depois pelo console web, substitui o `authorized_keys`.
