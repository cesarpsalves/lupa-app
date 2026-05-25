# LUPA — User Journey do Fotógrafo L1 (Freelancer)

**Persona:** Bruno, 27 anos, fotógrafo freelancer de ensaios e eventos.
**Objetivo:** organizar agenda + cobrar sinal + entregar ensaio + receber saldo + ter histórico no caixa.

---

## Mapa geral

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   PÚBLICO    │───▶│  ONBOARDING  │───▶│   APP DIA    │
│  (landing)   │    │  (cadastro)  │    │   A DIA      │
└──────────────┘    └──────────────┘    └──────────────┘
                                                │
        ┌───────────────────────────────────────┼──────────────────────┐
        ▼                                       ▼                      ▼
   ┌─────────┐                            ┌──────────┐           ┌──────────┐
   │ AGENDA  │                            │ ATENDIM. │           │  CAIXA   │
   │ semanal │◀───────cria atendim.──────│ (núcleo) │──pagto──▶│ (registro)│
   └─────────┘                            └──────────┘           └──────────┘
        ▲                                       │
        └──────────agenda automática◀───────────┘
```

## 1. Aquisição (público)

### Tela: Landing pública (`/`)

```
┌───────────────────────────────────────────────────────────┐
│ LUPA               Como funciona  Para quem  Entrar  ▶ Começar grátis │
├───────────────────────────────────────────────────────────┤
│                                                           │
│   ORGANIZE SEU NEGÓCIO NUM SÓ APP                         │
│   Pra qualquer prestador de serviço.                      │
│   Começando por fotógrafos.                               │
│                                                           │
│   [▶ Começar grátis]  [Ver demo]                          │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ DISPONÍVEL HOJE PARA                                      │
│  📸 Fotógrafos                                            │
│                                                           │
│ SEU NICHO NÃO ESTÁ AQUI?                                  │
│  • 12 barbeiros esperando                                 │
│  • 8 personal trainers esperando                          │
│  • 5 esteticistas esperando                               │
│  [Entrar na lista do seu nicho ▼]                         │
└───────────────────────────────────────────────────────────┘
```

### CTAs primários
1. `▶ Começar grátis` → `/cadastro`
2. `Entrar na lista` → modal com `nicho + email`

### Princípios aplicados
- 1 ação primária acima da dobra
- Lista pública de espera = prova social + freio de scope creep

---

## 2. Onboarding (cadastro → primeira tela útil)

Total: **≤ 90 segundos**. Cada passo cabe numa tela mobile sem rolar.

### Passo 1 — Conta (`/cadastro`)

```
┌──────────────────────────────────┐
│   Crie sua conta                 │
│                                  │
│   Nome:    [________________]    │
│   Email:   [________________]    │
│   Senha:   [________________]    │
│   ☐ Aceito termos e privacidade  │
│                                  │
│   [    Criar conta    ]          │
│                                  │
│   Já tem conta? Entrar           │
└──────────────────────────────────┘
```

Validações inline. Erro: "Email já cadastrado — quer recuperar a senha?".

### Passo 2 — Sua empresa (`/onboarding/empresa`)

```
┌──────────────────────────────────┐
│   Conta criada! ✓                │
│   Agora me conta sobre você      │
│                                  │
│   Como você atende?              │
│                                  │
│   ◯ Só eu (autônomo)             │
│   ◯ Eu + ajudantes               │
│   ◯ Tenho equipe e estúdio       │
│                                  │
│   Nome do negócio:               │
│   [_____________________]        │
│   (pode ser seu nome)            │
│                                  │
│   [    Continuar    ]            │
└──────────────────────────────────┘
```

> A escolha aqui ativa **L1/L2/L3** — só L1 está habilitado na v1, demais vão pra waitlist interno.

### Passo 3 — O que você oferece (`/onboarding/servicos`)

```
┌──────────────────────────────────┐
│   Quase lá! 🎯                   │
│   Adicione 3-5 serviços comuns   │
│   (pode editar depois)           │
│                                  │
│   Sugestões pra fotógrafo:       │
│   ☑ Ensaio fotográfico individual│
│   ☑ Ensaio de gestante           │
│   ☑ Cobertura de evento          │
│   ☐ Ensaio newborn               │
│   ☐ Book profissional            │
│                                  │
│   + Adicionar serviço            │
│                                  │
│   [    Tudo pronto, vamos!    ]  │
└──────────────────────────────────┘
```

> Pré-popula da IA-personaliza-superfície baseada no nicho.

### Tela final do onboarding

Redireciona pra **Dashboard** com **tour de 3 dicas** (dismiss "Já entendi").

---

## 3. Dia a dia — Dashboard (`/app`)

```
┌─────────────────────────────────────┐
│ ☰  LUPA                    🔔 [BA]  │
├─────────────────────────────────────┤
│ Olá, Bruno 👋                       │
│                                     │
│ ┌─────────────┐ ┌─────────────┐    │
│ │ ESTE MÊS    │ │ A RECEBER   │    │
│ │ R$ 3.450    │ │ R$ 1.200    │    │
│ │ +12% vs ant.│ │ 4 saldos    │    │
│ └─────────────┘ └─────────────┘    │
│                                     │
│ HOJE                                │
│ • 10h  Ensaio Maria S. (gestante)   │
│ • 14h  Cobertura aniv. Pedro        │
│                                     │
│ ESTA SEMANA                  Ver ▶  │
│ Ter • Qua • [Qui] • Sex • Sáb       │
│  2     1     3      0     2         │
│                                     │
│ [+ Novo atendimento]                │
├─────────────────────────────────────┤
│  🏠   📅   📋   💰   ⚙️             │
│ Início Agenda Atend. Caixa Mais     │
└─────────────────────────────────────┘
```

### Bottom nav (mobile) — 5 itens, simples e idiomáticos
- 🏠 Início (dashboard)
- 📅 Agenda
- 📋 Atendimentos
- 💰 Caixa
- ⚙️ Mais (clientes, serviços, configurações, ajuda)

---

## 4. Fluxo principal — Novo atendimento

Acionado por: `+ Novo atendimento` (qualquer tela) **ou** "Agendar" na Agenda.

### Passo A — Quem vai atender? (`/atendimentos/novo/cliente`)

```
┌─────────────────────────────────┐
│ ◀ Novo atendimento     Passo 1/4│
├─────────────────────────────────┤
│ Quem é o cliente?               │
│                                 │
│ [🔍 buscar nome ou telefone]    │
│                                 │
│ Recentes:                       │
│  • Maria Silva  (11) 99...      │
│  • Pedro Costa  (11) 98...      │
│                                 │
│ ── ou ──                        │
│ [+ Novo cliente]                │
│                                 │
│                  [Continuar ▶]  │
└─────────────────────────────────┘
```

### Passo B — O que vai fazer? (`/atendimentos/novo/servicos`)

```
┌─────────────────────────────────┐
│ ◀ Novo atendimento     Passo 2/4│
├─────────────────────────────────┤
│ Quais serviços?                 │
│                                 │
│ ☑ Ensaio gestante  R$ 600       │
│ ☐ Ensaio individual R$ 400      │
│ ☐ Cobertura evento  R$ 800      │
│                                 │
│ [+ Serviço avulso]              │
│                                 │
│ Subtotal:           R$ 600,00   │
│ Desconto: [R$ 0]                │
│ Total:              R$ 600,00   │
│                                 │
│                  [Continuar ▶]  │
└─────────────────────────────────┘
```

### Passo C — Quando? (`/atendimentos/novo/data`)

```
┌─────────────────────────────────┐
│ ◀ Novo atendimento     Passo 3/4│
├─────────────────────────────────┤
│ Quando vai acontecer?           │
│                                 │
│ Data:   [▾ 28/05/2026]          │
│ Hora:   [▾ 14:00]               │
│ Dura:   [▾ 2h]                  │
│                                 │
│ Local: [_________________]      │
│ (opcional)                      │
│                                 │
│ Observações:                    │
│ [_____________________]         │
│                                 │
│                  [Continuar ▶]  │
└─────────────────────────────────┘
```

### Passo D — Pagamento (`/atendimentos/novo/pagamento`)

```
┌─────────────────────────────────┐
│ ◀ Novo atendimento     Passo 4/4│
├─────────────────────────────────┤
│ Como vai cobrar?                │
│                                 │
│ Total: R$ 600,00                │
│                                 │
│ ◉ Sinal + Saldo (recomendado)   │
│   Sinal:  [50%] = R$ 300        │
│   Saldo:  R$ 300 (na entrega)   │
│                                 │
│ ◯ Pagamento único no final      │
│ ◯ Já recebi tudo                │
│                                 │
│         [✓ Criar atendimento]   │
└─────────────────────────────────┘
```

**Ao confirmar:**
- Cria `Atendimento` em status `confirmado`
- Cria evento na agenda
- Cria 1-2 `Pagamento` pendente (sinal + saldo)
- **Volta pra tela do atendimento** com botão `Compartilhar link com cliente`

---

## 5. Detalhe do atendimento (`/atendimentos/:id`)

```
┌─────────────────────────────────┐
│ ◀ Atendimento #1247             │
│                       [⋮ Mais]  │
├─────────────────────────────────┤
│ 🟢 CONFIRMADO                   │
│                                 │
│ Maria Silva                     │
│ (11) 99999-1234                 │
│                                 │
│ 📅 28/05/2026 às 14h (2h)       │
│ 📍 Av. Paulista, 1000           │
│                                 │
│ SERVIÇOS                        │
│ • Ensaio gestante    R$ 600,00  │
│                                 │
│ PAGAMENTOS                      │
│ ✓ Sinal      R$ 300  (pago)     │
│ ⏳ Saldo     R$ 300  (pendente) │
│                                 │
│ [Marcar como concluído]         │
│ [Cancelar atendimento]          │
└─────────────────────────────────┘
```

### Estados (máquina de estado)

```
   orçamento ─aceito─▶ confirmado ─dia_chega─▶ em_execução
                                                    │
                                                concluído
                                                    │
                                              saldo_recebido
                                                    │
                                               finalizado ─cupom─▶ PDF
                                                    │
                                                 (cancelado em qualquer ponto)
```

### Ao concluir
1. Botão `Marcar como concluído` → atendimento vira `concluído`
2. Modal: "Recebeu o saldo agora?" → Sim/Não
3. Se Sim: marca pagamento como pago, vira `finalizado`, gera **Cupom PDF** automaticamente
4. Mostra `[Baixar cupom]` `[Enviar por WhatsApp]` `[Compartilhar link]`

---

## 6. Agenda (`/agenda`)

```
┌──────────────────────────────────┐
│ ◀  Maio 2026  ▶          [+]    │
├──────────────────────────────────┤
│  D   S   T   Q   Q   S   S       │
│ 25  26  27 [28] 29  30  31       │
├──────────────────────────────────┤
│ Quinta, 28 de maio               │
│                                  │
│ 10:00 ─────────────────          │
│ ┃ Ensaio Maria S. (gestante)     │
│ ┃ 10:00 - 12:00                  │
│ 11:00                            │
│ 12:00 ─────────────────          │
│                                  │
│ 13:00                            │
│ 14:00 ─────────────────          │
│ ┃ Aniv. Pedro (cobertura)        │
│ ┃ 14:00 - 17:00                  │
│ 15:00                            │
│ 16:00                            │
└──────────────────────────────────┘
```

**Visões:** dia (default mobile) / semana (default desktop) / mês (lista compacta).
**Toque no bloco** → detalhe do atendimento.

---

## 7. Caixa (`/caixa`)

```
┌──────────────────────────────────┐
│ Caixa                            │
├──────────────────────────────────┤
│ Maio 2026         [▾ filtrar]    │
│                                  │
│ Entradas:   R$ 4.650             │
│ Saídas:     R$    200            │
│ ───────────────────────          │
│ Saldo:      R$ 4.450             │
│                                  │
│ MOVIMENTOS                       │
│ • 28/05  +R$ 300  Sinal Maria S. │
│ • 27/05  +R$ 800  Saldo Pedro    │
│ • 27/05  -R$ 200  Combustível    │
│ • 25/05  +R$ 600  Ensaio Carla   │
│                                  │
│ [+ Registrar entrada/saída]      │
└──────────────────────────────────┘
```

- Entradas/saídas vinculadas a atendimentos aparecem **read-only** (vêm do fluxo)
- Saídas manuais (combustível, equipamento) podem ser criadas livremente
- Filtro por período, categoria

---

## 8. Mais (`/mais`)

```
┌──────────────────────────────────┐
│ Mais                             │
├──────────────────────────────────┤
│ 👥 Clientes                    ▶ │
│ 📋 Serviços                    ▶ │
│ 🏢 Minha empresa               ▶ │
│ ⏰ Horário de funcionamento    ▶ │
│ 🔐 Segurança (senha, 2FA)      ▶ │
│ 💳 Plano e faturamento         ▶ │
│ 📤 Exportar meus dados (LGPD)  ▶ │
│ ❓ Ajuda                       ▶ │
│ 🚪 Sair                          │
└──────────────────────────────────┘
```

---

## 9. Casos de borda mapeados

| Caso | Comportamento |
|---|---|
| Cliente cancela depois do sinal | Atendimento → `cancelado`, sinal vira "não-reembolsado" (config padrão) ou registro de devolução manual |
| Cliente reagenda | Edita data do atendimento, mantém pagamentos |
| Sinal não pago e data passou | Banner amarelo no detalhe + lembrete no dashboard |
| Atendimento sem agenda (orçamento abandonado) | Fica em `orçamento` por 30 dias, depois auto-arquivado |
| Conflito de horário ao criar | Aviso: "Você já tem atendimento das 14h às 16h. Continuar mesmo assim?" |
| Bruno apaga cliente com atendimentos | Soft delete + impede se houver financeiro pendente |
| Bruno esquece de marcar pagamento | Saldo pendente fica visível em dashboard até resolvido |

## 10. Acessibilidade

- Tab order lógico em todos os fluxos
- `aria-label` em ícones-botão
- Contraste mínimo AAA pro texto principal, AA pra UI secundária
- Foco visível (não `outline:none` cego)
- Estados (`confirmado`, `pendente`) sempre com cor + ícone + texto (não só cor)
- Erros associados ao campo via `aria-describedby`

## 11. Telas adiadas (v1.5+)

- Galeria de fotos do cliente
- Contrato eletrônico
- Calendário multiusuário (L2)
- Loja/PDV (L3)
- Relatórios avançados (lucro por serviço, por cliente)
