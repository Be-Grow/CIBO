---
name: idea-completeness
description: Mapeia unidades de raciocínio em falas longas e audita dependência de contexto e publicidade; compatível com Codex/ChatGPT Work no Windows.
---

# Idea Completeness — CIBO / Codex / DarkChannel

Esta skill é um contrato editorial, NÃO uma implementação de modelo de IA nem garantia
de entendimento semântico. Funciona como diretriz para Codex/ChatGPT Work; no DarkChannel
há um adaptador usando o Qwen3 local e dois papéis sequenciais.

## Antes de editar

1. Obtenha transcrição com timestamps e áudio autorizado.
2. Identifique o assunto central, a tese, as evidências, exemplos e conclusão.
3. Procure início e fim em unidades de frase *existentes*, sem fabricar timestamps.
4. Compare pelo menos 60 segundos depois do fim pretendido (ou até acabar a fonte).
5. Se a fala posterior completar a explicação, o fim é incorreto mesmo havendo ponto final.
6. Não presuma que uma expressão como "portanto" prova conclusão.
7. Diferencie menção didática a produtos de argumento comercial.
8. Rejeite anúncio, mini-pitch e CTA comercial na seleção de conteúdo educativo.
9. Confirme o início/fim da palavra com áudio; o texto do Whisper pode deslocar tempos.
10. Uma ideia que não cabe na faixa de duração é rejeitada; não comprimir arbitrariamente.

## Agentes lógicos (uma IA por vez)

- Mapeador: devolve índices de frases start/end, tema e citação final literal.
- Auditor: recebe antes/candidato/depois e verifica início autossuficiente,
  desenvolvimento, conclusão real, continuação e intenção comercial.
- Validador: algoritmo puro verifica quotes, timestamps, duração, gatilhos
  antipitch, CIBO check-cut e desacordos.

Saídas: eligible_for_human_review, review_required, rejected ou model_unavailable.
Nenhum agente pode publicar ou marcar "human approved".

## Regra de segurança e dependência

Qwen3 é opcional e só roda quando a guarda de RAM autoriza. No Windows,
use python 3.11+, ffmpeg/ffprobe e evite scripts do CIBO que exigem macOS.
Se IA falhar, registre model_unavailable. Não diga que houve análise
semântica durante fallback lexical.

## QA da amostra

- check-cut com portable/cibo_windows.py (avisos, não aprovação).
- Ouça início e fim e verifique a transcrição contra áudio final.
- check-video e inspeção visual de cenas, legenda e movimentos.
- Grave feedback humano em JSONL LOCAL, fora do repositório público.
- Compare contra examples.json e só melhore a skill após regressões.
