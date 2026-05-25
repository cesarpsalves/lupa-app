# ADR-0001: Django + HTMX em monolito server-rendered

- **Data:** 2026-05-24
- **Status:** accepted
- **Decisores:** Paulo Alves

## Contexto

A v2 do LUPA precisa de uma stack que atenda dois objetivos simultâneos:

1. **Portfólio:** código legível, decisões defensáveis em entrevista, ecossistema reconhecido por recrutadores brasileiros.
2. **Produto real:** entregável em ~3 meses por uma pessoa, baixo custo operacional, fácil manter no longo prazo.

O app antigo usou React + Vite + Supabase + Lovable e foi abandonado por scope creep e complexidade descontrolada.

## Decisão

Construir o app como **monolito Django 5 server-rendered**, com **HTMX 2** + **Alpine.js** pra interatividade no cliente, sem SPA, sem Node em produção.

## Consequências

### Positivas
- 1 linguagem (Python) ponta a ponta — onboarding curto pra qualquer dev
- Sem build pipeline JS complexa → deploy simples
- Django admin pronto pra debug e operação
- Migrations, ORM, forms, auth, i18n nativos
- HTMX permite UX moderna (parcial updates, modais, validação inline) sem virar SPA
- Recrutadores conhecem Django (vaga brasileira)

### Negativas
- Não impressiona quem busca "React/Next moderno" no portfólio
- Real-time pesado (chat, dashboards live) exigiria WebSockets/SSE depois
- Mobile-app nativo precisaria de API REST/GraphQL separada no futuro

### Neutras
- HTMX é stack relativamente nova no Brasil — diferencial pra quem entende o porquê, mistério pra quem não

## Alternativas consideradas

### FastAPI + SPA (React/Vue)
- Prós: skills mais demandadas, separação clara front/back, possibilita mobile nativo direto
- Contras: 2 codebases, 2 deploys, 2 sistemas de auth, mais cognitive load, prazo dobra
- Por que não: maximiza superfície técnica mas atrapalha entrega em 3 meses

### Flask + Templates (Jinja2)
- Prós: minimalista, mostra fundamentos
- Contras: Flask vira espaguete em SaaS multi-tenant sem disciplina extra; sem ORM/admin/migrations nativos
- Por que não: pra o tamanho do app (10+ apps Django), Flask exige reinventar muito

### Django REST + SPA separado
- Prós: combina robustez Django com frontend moderno
- Contras: ainda são 2 codebases pra 1 pessoa em 3 meses
- Por que não: mesmo problema do FastAPI + SPA, com mais boilerplate Django desperdiçado

## Referências

- [HTMX Essays — Carson Gross](https://htmx.org/essays/)
- [docs/01-prd.md](../01-prd.md)
- Memória: `decision_stack.md`
