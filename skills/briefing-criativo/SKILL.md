---
name: briefing-criativo
description: Antes de editar, levante com o editor as decisões artísticas e de estilo que ainda não estão definidas (objetivo, tom, gancho, legenda, capa, motion, cor, trilha, SFX, entrega), perguntando só o que está em aberto, com opções tiradas do histórico do cliente, e registre tudo num brief do projeto que guia o job. Inclui pontos de aprovação no mapa de cortes e num corte piloto antes do lote. Use no início de todo job de edição de qualquer cliente, logo depois do client-router, e sempre que o pedido não disser o estilo de algo que vai aparecer na tela ou no som.
---

# Briefing criativo

O fluxo do CIBO ficou automático demais: a IA escolhia sozinha gancho, capa, cartão, cor,
trilha e cliques, e o editor só via as decisões depois do render, em forma de retrabalho
(capa "horrível", "foto aleatória" no cartão, "click bizarro", blur no logo). O usuário
pediu (12/10/2026): **a IA deve questionar o editor para que o máximo de detalhes seja
fornecido e nada fique ao acaso; com essa descrição ela trabalha num modelo mais preciso.**

Perguntar não é interrogar. O objetivo é que cada decisão visível ou audível tenha dono:
o editor, o perfil do cliente ou uma escolha registrada da IA que o editor aprovou.

## Quando rodar

1. No início de todo job, **depois** do `client-router` (cliente identificado) e **antes** de
   escolher momentos, montar job ou renderizar.
2. Quando um pedido novo no meio do job envolve algo de estilo que o brief não cobre
   ("faz um cartão de seguir", "põe uma trilha").
3. Quando o editor reprova algo: a reprovação vira pergunta respondida e entra no brief.

## Procedimento

### 1. Levante o que já está decidido (sem perguntar)

Leia, nesta ordem, e preencha o checklist de `references/checklist.md`:

- a linha do cliente em `client-router/references/client-registry.md`;
- `client-router/references/regras-transversais.md`;
- a skill do cliente (`SKILL.md`, `references/client-content-bible.md`, `brand-profile.md`);
- as memórias do projeto e `07_manifests/brief.md` de jobs anteriores do mesmo cliente;
- o que o próprio pedido já diz.

Cada item do checklist fica **definido** (com a fonte) ou **em aberto**. Só os em aberto
viram pergunta. Nunca pergunte o que o perfil do cliente ou o pedido já respondem.

### 2. Pergunte o que está em aberto

- Use a ferramenta de pergunta com opções (`AskUserQuestion`): até 4 perguntas por
  rodada, 2–4 opções cada; a opção recomendada vem primeiro e é a última escolha do cliente
  ou o padrão do motor, marcada como "(Recomendado)". O editor sempre pode escrever "Outro".
- **Primeira rodada = o que muda o trabalho inteiro**: objetivo/plataforma, quantidade e
  duração, tom e tipo de gancho, quem é o perfil que posta. **Segunda rodada = visual e som**:
  legenda, capa, motion, trilha e SFX. Uma terceira rodada só se ainda houver item de
  impacto em aberto. Mais de ~12 perguntas no total é interrogatório: o resto vira escolha
  registrada da IA, mostrada no mapa de cortes.
- Para escolha visual, mostre em vez de descrever: `preview` com mockup ASCII nas opções,
  ou 2–3 quadros/stills reais lado a lado (capa A/B/C, legenda A/B) antes de perguntar.
  Uma prévia de capa custa segundos; refazer 7 capas custou um render.
- Se o editor responder "decide você" / "tanto faz", registre como **delegado à IA** e use
  o padrão documentado, sem perguntar de novo no mesmo job.
- Se o pedido é urgente ("rápido", "pra já"), faça uma rodada só com as 3–4 decisões de
  maior risco e siga.

### 3. Registre o brief

Grave `07_manifests/brief.md` com `assets/brief_template.md`: cada decisão com o valor, a
origem (`editor`, `perfil do cliente`, `delegado à IA`) e a data. O brief é a fonte de
verdade do job: o `job.json` e as escolhas de render seguem o brief, e qualquer divergência
é bug.

Preferência que vale para os próximos jobs do cliente (não só para este) entra também no
perfil: linha do registro, bíblia do cliente ou memória do projeto. Ajuste pontual fica só
no brief.

### 4. Pontos de aprovação durante o job

- **Mapa de cortes antes de renderizar**: tabela com nº, manchete, in/out no master,
  duração, gancho (primeira frase) e o porquê de cada corte, mais as escolhas que ficaram
  delegadas à IA (trilha por corte, frame da capa). Peça aprovação ou ajuste com uma
  pergunta. Mudar a lista nesse ponto é grátis; depois do render não é.
- **Piloto antes do lote**: renderize o primeiro corte completo (capa, legenda, motion, som),
  mostre e pergunte se o padrão está aprovado antes de rodar os demais.
- **Entrega**: diga o que foi decidido pela IA sem consulta, para o editor poder vetar.

## O que não fazer

- Não pergunte detalhe técnico que o editor não escolhe (codec, CRF, loudness, offset de
  sincronia): isso é regra do CIBO e fica com a IA.
- Não pergunte o que já foi respondido neste job ou está no perfil do cliente.
- Não pare o trabalho esperando resposta quando dá para adiantar a parte que não depende
  dela (transcrição, rastreio de rosto, mezaninos).
- Não trate o silêncio como aprovação de algo visível: se a pergunta ficou sem resposta,
  siga com o recomendado e liste isso na entrega como decisão da IA.
