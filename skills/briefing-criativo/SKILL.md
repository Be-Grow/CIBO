---
name: briefing-criativo
description: Levanta com o editor só as decisões de estilo em aberto (tom, gancho, legenda, capa, motion, cor, trilha, SFX), grava o brief e os pontos de aprovação. Use no início de todo job, logo após o client-router.
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
- `client-router/references/regras/_checklist.md` (e a fase atual em `regras/`);
- a skill do cliente (`SKILL.md`, `references/client-content-bible.md`, `brand-profile.md`);
- as memórias do projeto e `07_manifests/brief.md` de jobs anteriores do mesmo cliente;
- o que o próprio pedido já diz.

Cada item do checklist fica **definido** (com a fonte) ou **em aberto**. Só os em aberto
viram pergunta. Nunca pergunte o que o perfil do cliente ou o pedido já respondem.

### 1b. Referência do editor ("quero nesse estilo")

Quando o editor mandar um vídeo de referência, meça antes de perguntar:
`~/.claude/skills/content-hub/.venv/bin/python3 scripts/analisa_referencia.py REF.mp4 --out PASTA`
(ritmo de corte, enquadramento, faixa e troca da legenda, cor, loudness, transientes; 5 s para um
reel de 1 min). As sugestões viram as opções recomendadas das perguntas (ritmo, `CAP_PRESET`,
enquadramento, cor) e entram no brief com a origem "referência do editor".

### 1c. Identidade sem manual de marca

Quando o cliente não tem manual, peça um print do canal/perfil (banner + thumbs) e **meça** as cores no
print (quantize por região: fundo, faixa, título, secundário) em vez de chutar; identifique as fontes
das thumbs pelo desenho das letras e diga que é identificação visual. Registre a paleta medida no
tema do cliente (`reel-motion/temas/`) e rode `reel-motion/scripts/contraste.py` (identidade sem perder
leitura). Ex.: João, 13/10/2026 — marinho/azul das thumbs, Montserrat Black do ep 24.

### 1d. Fonte em aberto ("tô sem ideia de fonte")

Monte uma folha com **3 opções lado a lado sobre um quadro real do cliente, já no layout e nas cores
do job** (título do painel + faixa + legenda com destaque): uma tirada da identidade dele (thumb mais
recente), uma variação da identidade, e a do estilo de referência pedido. Rotule cada uma, recomende
uma e pergunte. Confira antes de mostrar que o quadro é da pessoa certa (no João saiu a convidada na
1ª tentativa). Fontes baixadas entram no `acervo` com `add`.

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
- **Entrega**: diga o que foi decidido pela IA sem consulta, para o editor poder vetar, e **ofereça
  sempre o projeto editável** para Premiere Pro / DaVinci Resolve (`podcast-reels/scripts/projeto_nle.py`).
  Só gere se o editor pedir.

## O que não fazer

- Não pergunte detalhe técnico que o editor não escolhe (codec, CRF, loudness, offset de
  sincronia): isso é regra do CIBO e fica com a IA.
- Não pergunte o que já foi respondido neste job ou está no perfil do cliente.
- Não pare o trabalho esperando resposta quando dá para adiantar a parte que não depende
  dela (transcrição, rastreio de rosto, mezaninos).
- Não trate o silêncio como aprovação de algo visível: se a pergunta ficou sem resposta,
  siga com o recomendado e liste isso na entrega como decisão da IA.
