# ADR-0002: Multi-tenant — shared database / shared schema com `company_id`

- **Data:** 2026-05-24
- **Status:** accepted
- **Decisores:** Paulo Alves

## Contexto

LUPA é SaaS: cada empresa (fotógrafo freelancer, estúdio) é um *tenant*. Os dados de uma empresa **nunca** podem ser visíveis a outra. A estratégia de isolamento define complexidade operacional, custos, riscos de segurança e flexibilidade futura.

## Decisão

Adotar **shared database, shared schema** com uma coluna `company_id` em toda tabela de tenant, enforçada por:

1. **Manager customizado** (`TenantManager`) que aplica `.filter(company=current_company)` em todo `Model.objects` por padrão
2. **Middleware** (`TenantMiddleware`) que resolve o tenant ativo a partir do user logado e armazena em thread-local
3. **Views nunca aceitam `company_id` via URL/POST** — sempre vêm do `request.company`
4. **Falha fechado:** sem tenant ativo, `objects.all()` retorna `none()` (não a base inteira)
5. **Testes obrigatórios** de isolamento (cross-tenant 404)

## Consequências

### Positivas
- 1 banco, 1 backup, 1 conjunto de migrations
- Custos baixos em qualquer escala até dezenas de milhares de tenants
- Operação simples: dump/restore, monitoramento, métricas
- Permite queries cross-tenant *só pra admin* (relatórios globais)

### Negativas
- Risco de bug que vaze dados entre tenants (mitigado por manager + testes)
- Performance pode degradar com 1 tenant gigante (mitigado por índices `(company, *)` em tudo)
- "Customer-managed encryption keys" mais difícil

### Neutras
- Padrão amplamente usado (Notion, Linear, Pipedrive começaram assim)

## Alternativas consideradas

### Schema-per-tenant (Postgres schemas, ex.: django-tenants)
- Prós: isolamento físico mais forte, exclusão de tenant = drop schema
- Contras: migrations N× mais lentas, complexidade operacional, queries cross-tenant impossíveis
- Por que não: overkill pra MVP, dificulta debugging e relatórios admin

### Database-per-tenant
- Prós: isolamento total
- Contras: explode custo operacional desde tenant #1
- Por que não: inviável pra SaaS com free tier

### Row-Level Security (RLS) nativo do Postgres
- Prós: enforcement no banco, defesa adicional
- Contras: complexidade de gerenciamento de policies, conflito com Django auth, debugging difícil
- Por que não: posso adicionar como **2ª linha de defesa** depois do MVP, sem refatorar arquitetura

## Referências

- [docs/03-architecture.md §6](../03-architecture.md)
- [docs/04-security.md §6](../04-security.md)
