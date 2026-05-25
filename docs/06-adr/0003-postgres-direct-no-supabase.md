# ADR-0003: Postgres direto via docker-compose, sem Supabase

- **Data:** 2026-05-24
- **Status:** accepted
- **Decisores:** Paulo Alves

## Contexto

O app antigo usou Supabase self-hosted (Auth + RLS + Storage + RealTime + Postgres). A v2 escolheu Django, que tem auth, ORM e permissions próprios. Manter Supabase como camada gera **redundância** e acoplamento desnecessário.

O VPS atual já roda Postgres dentro do Supabase legado. Duas opções: usar esse Postgres compartilhado, ou subir um Postgres isolado dentro do compose da nova aplicação.

## Decisão

1. **Remover toda dependência de Supabase.** Django Auth + permissions próprias substituem.
2. **Postgres 16 dentro do `docker-compose.prod.yml`** da própria aplicação LUPA — isolado do Postgres do Supabase legado.
3. **Banco da aplicação:** `lupa_v2`, usuário `lupa_app` com privilégios mínimos.
4. **Backups:** `pg_dump` cron diário, retenção local 14d + offsite 30d.

## Consequências

### Positivas
- Portabilidade total: trocar de VPS = `pg_dump` + `pg_restore`, sem dependência de stack proprietária
- Versão do Postgres controlada pela aplicação (16 fixo)
- Zero risco de afetar dados do Supabase legado durante desenvolvimento
- Stack mais simples no portfólio (1 framework, não 2)
- Menos um ponto de falha (Supabase Auth indo embora não derruba app)
- Migrations Django são a única fonte da verdade do schema

### Negativas
- Perdemos features Supabase "grátis": RealTime, Storage com policies, Auth com OAuth providers já configurados
- Vou usar mais RAM no VPS (Postgres extra rodando)
- Refazer OAuth (Google/Apple sign-in) exige integração manual quando precisar

### Neutras
- Se um dia voltar pra managed Postgres (Neon, Supabase managed, RDS), é só apontar `DATABASE_URL` — código não muda

## Alternativas consideradas

### Usar o Postgres do Supabase legado como banco da v2 (banco separado `lupa_v2`)
- Prós: 1 instância Postgres só, economia de RAM
- Contras: acoplamento operacional (se o Supabase morre, a v2 morre); risco de tocar no legado por engano; versões de Postgres ficam amarradas à versão que o Supabase usa
- Por que não: portabilidade > economia marginal de RAM

### Manter Supabase como BaaS
- Prós: features prontas (Auth, Storage, RealTime)
- Contras: 2 stacks acopladas (Django + Supabase JS/SDK), redundância de auth, vendor lock-in lógico
- Por que não: contraria a escolha de Django; portfólio fica confuso ("é Django ou Supabase?")

### Managed Postgres externo (Neon, Supabase Cloud, ElephantSQL)
- Prós: backup, replicação, monitoramento gerenciados
- Contras: latência de rede VPS↔managed, custo mensal extra, complica setup local
- Por que não na v1: VPS já está pago, latência local zera, custo inicial 0. Migrar pra managed quando o custo de operação superar o de mensalidade

## Migração futura (não-bloqueante)

Se um dia quisermos voltar pra Supabase ou Neon:

```bash
# 1. Dump
docker compose exec db pg_dump -Fc lupa_v2 > /tmp/lupa.dump

# 2. Restore na managed
pg_restore -d $NEW_DATABASE_URL /tmp/lupa.dump

# 3. Trocar DATABASE_URL no .env de produção e reiniciar
```

Zero refactor de código.

## Referências

- [docs/03-architecture.md §3, §12](../03-architecture.md)
- [docs/04-security.md §8](../04-security.md)
