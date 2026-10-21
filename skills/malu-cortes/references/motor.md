# Malu — motor (scripts desta skill)

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Motor da Malu (scripts desta skill)

Ligado só no job da Malu; o `render.py` da `fernanda-produto` chama tudo no `prep`. Sem as chaves abaixo o grafo da Fernanda é idêntico ao de antes (conferido quadro a quadro e no PCM da voz e da música). Nada do Bombordo foi alterado: o código veio por cópia adaptada.

- **`camera_engine: "malu"` → `scripts/camera.py`**: cortes, enquadramento por plano (face track), zooms, push-in e respiro saem da fonte 4K num warp só, com Easy Ease `cubic-bezier(0.33,0,0.67,1)`, escala em log e shutter 360° (até 16 subquadros). O resultado é `<work>/camera.mov` (ProRes 422 HQ), reaproveitado enquanto nada muda (impressão digital em `camera.json`). Movimentos em `camera_moves`: `{"t", "kind": "punch"|"push"|"breathe", "amount", "in", "until"}`, em tempo editado; sem essa chave, os `smooth_zooms` viram `punch`. Leva ~9 min por reel de 50 s num M4 e usa ~0,6 GB. O grafo antigo do zoom (escala 4K repetida por janela) travou o v10 com 11 GB.
- **`caption_engine: "kinetic"` → `scripts/kinetic/cli.py job.json words|blocks|chin|layer|all|sheet`**:
  - `words`: tempo por palavra, com o texto do `captions.json` e o tempo do Whisper do áudio editado (`word_timing`), ajustado no ataque só depois de pausa real e com o master em 16 kHz (`audio16k`).
  - `blocks`: gera `<work>/kinetic/blocks.json`, editável. Divide os blocos pelo conjunto da frase: nunca separa "40 dias", nunca termina bloco em artigo, "não" ou demonstrativo, e as quebras feitas à mão são fronteiras. O destaque vem com a palavra pequena por cima.
  - `chin`: mede o queixo no `camera.mov` e gera `<work>/chin_track.json` e `kinetic/chin_sheet.jpg`.
  - `layer`: gera `<work>/kinetic_caps.mov` em QuickTime Animation, RGBA sem perdas.
  - `sheet`: gera a folha de contatos com o meio de cada entrada, destaque, saída e zoom.
  - Destaques pelo sentido: `kinetic.highlights`, em ordem de fala; `"Toxina#2"` indica a segunda ocorrência.
  - Configuração: `kinetic/config.json` + `job["kinetic"]` + `<work>/kinetic.json`.
- **Altura da legenda**: cada bloco fica abaixo do queixo mais baixo do tempo em que está na tela, incluindo o auge do zoom, com folga para a entrada e a saída. Dentro de um plano a altura é a do bloco mais exigente, então a legenda só muda de altura no corte. Na tela dividida vale `position.split_cy`, e outros layouts vão em `caption_layouts` (`start`, `end`, `cy`, `kind`). Nenhum bloco fica na tela durante uma troca de layout. Se a zona segura de baixo vencer, a camada lista o bloco. Relatório em `kinetic/positions.json`.
- **Queixo**: `chin_track.py` ignora os quadros de referência (não é o rosto dela) e descarta falso rosto isolado (mão/copo que foge 0,6 altura de rosto da mediana dos vizinhos).
- **Mapa**: `scripts/mapa.py job.json 05_qa/<reel>_mapa_edicao.md` monta a tabela de eventos e mede o maior trecho sem mudança visual.
- **Gráficos** (`job["graphics"]`): `title`, `callout` (pílulas empilham quando não cabem), `number` (unidade longa vai embaixo; `big_px`/`unit_px`/`cy` configuráveis — sobre o rosto dela, nunca: no plano dela o número vai pequeno e em linha única no alto, acima da cabeça, como "150 milhões de anos" no reel 04), `endcard` (recorte do master sem o ombro: `[1760, 1860, 400, 533]` em 47,5 s).
- **Ainda não construído** (fazer antes de usar): lower third (falta o texto: nome e função), audição da biblioteca de SFX com o usuário e a regra "SFX nunca sobre consoante" dentro do `review_job.py` (hoje o `audio.py` já desvia os picos das consoantes).
