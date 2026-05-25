# ADR-0004: Monolito Docker em VPS único, sem Kubernetes

- **Data:** 2026-05-24
- **Status:** accepted
- **Decisores:** Paulo Alves

## Contexto

Definir topologia de deploy: 1 binário, microserviços, K8s, serverless? O produto é um SaaS pequeno que precisa rodar em ~3 meses, ser barato, e ser fácil de operar por 1 pessoa.

## Decisão

**docker-compose em 1 VPS** (atualmente 31.97.26.125, Hostinger). Composição:

- `nginx` — reverse proxy + TLS + rate limit
- `web` — Gunicorn rodando Django
- `db` — Postgres 16
- `redis` — cache, locks, futuro fila
- `backup` — cron container ou cron do host com `pg_dump`

Deploy: GitHub Actions builda imagem, faz push pro `ghcr.io`, e executa `ssh paulo@vps "cd ~/lupa && docker compose pull && docker compose up -d"`.

## Consequências

### Positivas
- Operação trivial: 1 servidor, 1 docker-compose, logs em journald
- Custo: ~R$50/mês (VPS já existente)
- Rollback simples: `docker compose up -d` com tag anterior
- Logs e debug centralizados
- Sem orquestrador a aprender/configurar/quebrar

### Negativas
- SPOF: VPS cai = app cai (mitigado por backups + IaC mínimo pra recriar em <1h)
- Sem auto-scaling horizontal automático (não é problema com até centenas de tenants)
- Deploy com downtime de ~10-30s (mitigado: zero-downtime via blue-green é otimização futura)

### Neutras
- Migrar pra K8s/Fly/Render depois é trivial — a aplicação é portátil

## Alternativas consideradas

### Render / Railway / Fly.io
- Prós: PaaS, sem operar servidor
- Contras: custo escala rápido, vendor lock-in operacional, demonstra menos no portfólio
- Por que não na v1: VPS já pago, oportunidade de mostrar ops no portfólio (Nginx, systemd, certbot, backup)

### Kubernetes (k3s/k8s)
- Prós: portfólio brilhante pra vagas de SRE/DevOps
- Contras: complexidade massiva pra 1 servidor; aprende-se K8s ao custo de não entregar o produto
- Por que não: viola "produto pequeno feito direito"

### Serverless (Lambda + RDS)
- Prós: escala automática, paga só uso
- Contras: cold start em Django é doloroso, ORM + serverless conflita com pool de conexões, mais caro abaixo de tráfego razoável
- Por que não: stack errada pra Django monolito

## Roadmap de escalabilidade

Quando atingirmos limites do VPS único (provavelmente >500 tenants ativos):

1. Movar Postgres pra managed (Neon, Supabase Cloud, RDS)
2. Subir 2º VPS atrás de load balancer (Nginx do VPS 1 vira LB se preciso)
3. Migrar pra Fly.io/Render se operar 2+ VPS ficar pesado
4. Considerar Celery + worker dedicado se tasks ficarem pesadas

Cada passo só quando dor real aparecer.

## Referências

- [docs/03-architecture.md §12](../03-architecture.md)
- "Boring Technology" — Dan McKinley
