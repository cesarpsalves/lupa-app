# LUPA — Product Requirements Document (PRD)

**Autor:** Paulo Alves
**Status:** Draft v1 — aguardando validação
**Última atualização:** 2026-05-24

---

## 1. Visão

**LUPA é o sistema de gestão pra qualquer prestador de serviço — começando por fotógrafos.**

Um único lugar pra organizar agenda, atendimentos, recibos e caixa. Sem precisar assinar Trello + Google Agenda + planilha + WhatsApp Business + emissor de PDF separadamente.

## 2. O problema

Prestadores de serviço autônomos no Brasil orquestram seu negócio com **5+ ferramentas desconectadas**: caderno, WhatsApp, Google Agenda, planilha de Excel, calculadora, gerador de PDF online. O resultado: retrabalho, esquecimento de cobranças, dificuldade de saber o lucro real, e zero histórico do cliente.

Ferramentas SaaS específicas existem (Trinks, Studio Ninja, iClinic) mas:
- São caras pra autônomo iniciante
- Têm curva de aprendizado alta
- São pensadas pra desktop, mal adaptadas pro celular
- Cada uma serve **um nicho** — quem muda de área perde tudo

## 3. A solução

Um app **mobile-first responsive** que cobre o ciclo completo do prestador:

```
agendamento → execução → cobrança → registro no caixa
```

Construído sobre um **schema genérico** que se adapta ao nicho via configuração (terminologia, campos, presets), não código novo.

## 4. Beachhead: fotógrafo profissional

Por que fotógrafo primeiro:
- Ticket médio alto (justifica preço de SaaS)
- Concorrência média (não saturada como beleza)
- Fluxo cobre os 3 módulos centrais (agenda, atendimento longo, cupom, caixa, sinal)
- Os 3 sub-perfis (freelancer, estúdio, loja) viram **níveis progressivos** do produto

### 4.1. Personas

**L1 — Bruno, fotógrafo freelancer (foco do MVP)**
- 27 anos, faz ensaios de gestante, casamento, formatura
- Trabalha sozinho, usa caderno e Instagram DM
- Cobra sinal de 30-50%, recebe saldo na entrega
- Não tem CNPJ ou é MEI recém-aberto
- Dor principal: perde data, esquece cobrança, não sabe quanto ganhou no mês

**L2 — Carla, estúdio fotográfico (v1.5/v2)**
- Tem espaço fixo, 1-2 assistentes/auxiliares
- Aluga o espaço pra outros fotógrafos
- Precisa de agenda compartilhada por profissional + recurso (sala A, sala B)
- Já usa alguma ferramenta paga, mas reclama de complexidade

**L3 — Marcos, estúdio + loja (v2+)**
- Estúdio + vende equipamentos, álbuns, molduras
- Precisa de estoque, controle balcão, PDV
- Equivalente a "pequeno comércio + serviço"

## 5. Princípios de produto

### 5.1. Não-negociáveis

1. **Acessível a um idoso** — fluxos lineares, fontes ≥16px, botões ≥44px, copy em PT-BR claro. Ver [Princípio de Design Acessível](../../.claude/projects/-Users-pauloalves-Documents-lupasolucoes/memory/principle_design_acessivel.md).
2. **Schema genérico desde o dia 1** — qualquer nicho futuro deve entrar por configuração, não código.
3. **Mobile-first responsive** — ambos casos (mobile gerenciamento, desktop edição) bem servidos.
4. **Segurança não é feature, é regra** — [docs/04-security.md](./04-security.md).
5. **Threshold público pra expansão** — 15 interessados na waitlist OU 50 pagantes no nicho atual ativa próximo nicho.

### 5.2. O que NÃO faremos (anti-escopo)

Lista explícita do que está **fora** da v1, com motivo. Adição requer revisão escrita.

| Item | Por quê fica fora |
|---|---|
| WhatsApp bot/atendente IA | Foi o módulo que mais quebrou no app antigo. Pra v3 como módulo plugável. |
| Galeria de fotos pro cliente | Complexo de fazer bem (storage, link público, watermark). v1.5. |
| Contrato eletrônico com assinatura | Compliance + integração externa. v1.5. |
| NFS-e (nota fiscal de serviço) | Integração com prefeitura varia por cidade. v2. |
| App nativo iOS/Android | PWA cobre 95% das necessidades. Nativo só se houver demanda. |
| Marketplace de prestadores | Não é o produto. Distrai do core. |
| Múltiplas moedas / i18n | Brasil first. |
| Integração com Google Agenda | Vira "outra ferramenta" — produto core deve substituir, não complementar. v2 se houver demanda. |

## 6. Escopo v1 (MVP — meses 1-3)

### 6.1. Features

| # | Feature | Descrição mínima |
|---|---|---|
| F1 | **Autenticação** | Cadastro com email/senha, login, recuperação. 2FA opcional pra owner. |
| F2 | **Onboarding** | Wizard de 3 passos: dados da empresa → nicho (escolha de preset) → 5 serviços iniciais. |
| F3 | **Multi-tenant** | Cada empresa isolada por `company_id`. Convite por email pra adicionar funcionários. |
| F4 | **Clientes** | CRUD com nome, contato, observações, histórico de atendimentos. Busca por nome/telefone. |
| F5 | **Serviços (catálogo)** | CRUD com nome, descrição, preço base, duração estimada. |
| F6 | **Agenda** | Visualização dia/semana, criar/editar/cancelar agendamento, recorrente opcional. |
| F7 | **Atendimento (núcleo)** | Máquina de estado: `orçamento → confirmado → em execução → concluído → finalizado`. Anexa cliente, serviços (1+), pagamento. |
| F8 | **Pagamento parcelado** | Sinal (% configurável) + saldo. Cada pagamento gera movimento no caixa. |
| F9 | **Cupom em PDF** | Gera PDF do atendimento concluído (dados empresa, cliente, serviços, valores, data). Download + envio por link. |
| F10 | **Caixa** | Lista de movimentos (entradas/saídas), filtros por data, total do dia/semana/mês. Saída manual permitida. |
| F11 | **Dashboard** | 4 cards: faturamento do mês, atendimentos da semana, sinais pendentes, próximos da agenda. |
| F12 | **Configurações** | Dados da empresa, logo, horário de funcionamento, % padrão de sinal. |
| F13 | **Landing pública** | Página de marketing + cadastro + waitlist por nicho (contador público). |
| F14 | **Política de privacidade + LGPD** | Páginas estáticas + endpoints de exportar/excluir dados. |

### 6.2. Métricas de sucesso (v1)

- **15 fotógrafos cadastrados** em 30 dias após launch
- **5 fotógrafos ativos** (criaram ≥3 atendimentos) em 60 dias
- **Tempo médio do onboarding ao primeiro cupom < 10min**
- **Zero incidente de segurança** (cross-tenant access, vazamento de dados)
- **Lighthouse mobile ≥ 90** em Performance e Accessibility na landing

## 7. v1.5 (meses 4-5)

- Galeria de entrega de fotos (link público com expiração)
- Contrato em PDF com assinatura digital simples (link + IP + timestamp)
- Convite/agenda compartilhada com múltiplos profissionais (preparação L2)
- Modo "estúdio" — recursos (sala A, sala B) reserváveis junto com agenda
- Notificações por email (lembrete de agendamento, cobrança vencida)
- Relatórios financeiros (lucro por serviço, ticket médio)

## 8. v2 (meses 6-9)

- Módulo Loja: produtos, estoque, PDV (perfil L3)
- WhatsApp bot **escopo fechado** (agendar, confirmar, cobrar — sem conversa livre)
- NFS-e por cidade (começar São Paulo)
- Expansão pra 2º nicho (após threshold)
- App PWA instalável

## 9. Restrições não-funcionais

| Categoria | Requisito |
|---|---|
| **Performance** | TTFB < 300ms, LCP < 2.5s no 4G mediano |
| **Acessibilidade** | WCAG 2.1 AA mínimo |
| **Browsers** | Chrome/Edge/Safari/Firefox últimas 2 versões + iOS Safari 14+ |
| **Idiomas** | PT-BR only na v1 |
| **Disponibilidade** | 99% uptime (~7h downtime/mês — adequado pra SaaS pequeno) |
| **Backup** | Diário, retenção 14d local + 30d offsite |
| **LGPD** | Conforme [04-security.md §7](./04-security.md) |

## 10. Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Scope creep (erro do app antigo) | Alta | Crítico | Anti-escopo explícito (§5.2). PR review obrigatório pra features novas. |
| Baixa aquisição de fotógrafos | Média | Alto | Posicionamento específico ("pro fotógrafo brasileiro que cansou de planilha"), conteúdo no LinkedIn/Instagram |
| Concorrência forte (Studio Ninja, Sprout) | Alta | Médio | Brecha: preço + simplicidade + UX em PT-BR. Não tentar feature parity. |
| Dependência de VPS único | Alta | Alto | Backups testados, IaC mínimo (docker-compose + makefile) pra recriar em 1h |
| LGPD/processo de pessoa física | Baixa | Crítico | Implementar §7 do security desde o dia 1, DPO contact visível |
| Eu (Paulo) sumir do projeto | Média | Crítico | Documentação completa, README portfolio-grade, ADRs |

## 11. Decisões em aberto

- [ ] Domínio definitivo (lupa.app? usar lupasolucoes.com?)
- [ ] Pricing exato (free + pago, quanto?)
- [ ] Provider de email transacional (Resend? Postmark? SES?)
- [ ] Provider de storage de arquivos (S3? R2? local first?)

## 12. Glossário

- **Atendimento** = unidade de trabalho (ensaio, sessão, projeto). Renomeável por nicho.
- **Cupom** = comprovante de serviço prestado em PDF (precursor da NFS-e).
- **Tenant / Empresa** = unidade de isolamento multi-cliente.
- **Beachhead** = nicho de entrada que ancora o produto enquanto se expande.
- **L1/L2/L3** = níveis progressivos do perfil de fotógrafo (freelancer/estúdio/loja).
