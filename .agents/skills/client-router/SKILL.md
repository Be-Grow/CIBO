---
name: client-router
description: "Ponto de entrada de todo trabalho de edição de vídeo do CIBO (cortes, reels, shorts, podcast, palestra, depoimento, produto, legenda, capa, trilha, motion, render), com ou sem cliente citado: identifica o cliente e a skill de corte, e traz o mapa de qual skill usar em cada etapa (briefing, estrutura, fala, trilha, motion, legenda, render, QA). Trata cada cliente como fluxo, estilo e assets isolados — nunca mistura fonte, logo, trilha, SFX ou capa entre clientes (Bombordo e Boreste, Content Hub, Katia, Autismo Cast, Dr. Energia, Fernanda, Malu, João Campos). Use antes de qualquer outra skill de edição."
---

# Adaptador Codex para CIBO

Antes de agir, leia integralmente a skill original em `skills/client-router/SKILL.md`. Leia também as referências que ela indicar. Os scripts, referências e assets originais continuam em `skills/client-router/`; resolva caminhos relativos a partir dessa pasta.

Siga o fluxo editorial e os pontos de aprovação definidos pela skill original e por `CLAUDE.md` e `skills/client-router/`. Adapte comandos ao Windows: verifique cada executável, use `py -3.12` para Python e `npm.cmd`/`npx.cmd` no PowerShell. Não presuma que caminhos ou dependências do macOS existam. Preserve os brutos e projetos; não sobrescreva nem reorganize sem auditar e confirmar o destino.

