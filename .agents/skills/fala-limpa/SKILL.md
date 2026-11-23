---
name: fala-limpa
description: "Audite e limpe a fala de cortes de talking head e entrevista antes do render e no QA — detecta e manda cortar outra voz (entrevistador, alguém ao fundo), hesitações (\"ééé\", \"ahn\", pausas de pensamento) e palavra final engolida pelo fade. Use em todo corte de fala de qualquer cliente (Fernanda/Malu, podcasts, depoimentos), junto com a skill de corte do cliente."
---

# Adaptador Codex para CIBO

Antes de agir, leia integralmente a skill original em `skills/fala-limpa/SKILL.md`. Leia também as referências que ela indicar. Os scripts, referências e assets originais continuam em `skills/fala-limpa/`; resolva caminhos relativos a partir dessa pasta.

Siga o fluxo editorial e os pontos de aprovação definidos pela skill original e por `CLAUDE.md` e `skills/client-router/`. Adapte comandos ao Windows: verifique cada executável, use `py -3.12` para Python e `npm.cmd`/`npx.cmd` no PowerShell. Não presuma que caminhos ou dependências do macOS existam. Preserve os brutos e projetos; não sobrescreva nem reorganize sem auditar e confirmar o destino.

