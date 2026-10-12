---
name: lettering-motion
description: Anime legendas, letterings, cards, lower thirds e CTAs. Legenda palavra a palavra fica em Pillow com curvas de easing nomeadas; grafismo desenhado que entra na tela (cartão Seguir, lower third, título de gancho, número animado, CTA) é feito em Remotion com a skill anthropic-skills:motion-graphics, com template pronto em assets/remotion-template. Use ao criar ou revisar qualquer texto/card animado em qualquer skill de corte.
---

# Lettering Motion

Toda animação de texto/card do CIBO usa `scripts/easing.py` (curvas nomeadas + `entrance()` para slide-direcional com fade) em vez de reimplementar easing local em cada renderer. Isso existia de forma duplicada e incompleta antes: `render_caps.py` e `render_lettering.py` cada um tinha sua própria cópia de `ease_out_cubic`/`ease_out_back`, e nenhum tinha um componente de translação (slide) — só fade e scale-pop.

## Uso

```python
from easing import entrance, ease_out_back, ease_out_bounce

dx, dy, alpha = entrance(progress, direction='up', distance=40)  # slide de baixo pra cima + fade, desacelerando
paste(canvas, tile, final_x + dx, final_y + dy, alpha=alpha)
```

`direction` aceita `up`, `down`, `left` ou `right` — o elemento nasce deslocado `distance` px nessa direção a partir da posição final e converge enquanto ganha opacidade, com a curva de easing controlando a desaceleração (`ease_out_cubic` por padrão; troque por `ease_out_back` para um leve overshoot, ou `ease_out_bounce` para quicar). Ver `references/animation-catalog.md` para os presets nomeados e quando usar cada direção.

## Qual ferramenta usar

| O que é | Ferramenta | Por quê |
|---|---|---|
| Legenda corrida, palavra a palavra | Pillow + `easing.py` | Centenas de blocos por corte; render em lote rápido, no pipe de frames do motor |
| Ênfase pontual na legenda (pop, slide curto) | Pillow + `easing.py` | Mesmo pipe da legenda |
| Grafismo desenhado que entra na tela: cartão "Seguir"/@, lower third com nome, título de gancho, número que conta, CTA, end card | **Remotion** via `anthropic-skills:motion-graphics` | Mola de verdade (`spring`), vários elementos com tempos próprios, sombra, gradiente, borda e ícone; no Pillow isso saía duro e "de template" |
| Traço sendo desenhado, ícone contornando | SVG no Remotion (`stroke-dashoffset` em função do quadro) | O Remotion já rasteriza SVG; não precisa do cairosvg |

O usuário achou o motion feito só com slide/fade do Pillow "ruinzinho" (palestra João Campos, 12/10/2026). Por isso card, lower third e título não ficam mais no Pillow.

## Remotion neste Mac (validado em 12/10/2026)

- Node 26 em `/opt/homebrew/bin`. No macOS o Remotion baixa sozinho o `chrome-headless-shell`: **não** passe `--browser-executable` (a instrução da skill da Anthropic é para Linux).
- Template pronto em `assets/remotion-template/` com `SeguirCard` (cartão do Instagram: entra com mola, o botão "Seguir" é tocado e vira "Seguindo", sai descendo). Props: `name`, `handle`, `avatar` e `font` (arquivos em `public/`), `top` (y em 1080×1920) e `tap` (quadro do toque).
- Template também traz `GanchoTitle` (título de gancho: painel escuro abre na horizontal, palavras sobem uma a uma com mola, palavras de `accent` na cor de destaque, sai subindo). Props: `text`, `accent` (lista de palavras), `color`, `font`, `top` (padrão 150, acima da cabeça), `size`. Entra em 1,0 s, logo depois do burn de abertura, por 3,5 s; sem SFX (fica colado no burn).
- Copie o template para `04_work/mg/` do projeto, rode `npm i`, ponha a fonte **do cliente** e o avatar em `public/`. O template não traz fonte nem cor de cliente nenhum.
- Sempre um `npx remotion still ... --frame=N` composto sobre um quadro real do corte antes do render inteiro.
- Render com alpha: `npx remotion render src/index.ts SeguirCard out/card.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --props='{"name":"...","handle":"@..."}'`.
- Sobreposição: `scripts/overlay_card.sh ENTRADA.mp4 card.mov INICIO SAIDA.mov [SFX.wav TEMPO]`, numa passada separada sobre o MP4 pronto e **antes** do `burn_end.py`. O SFX vai no toque do botão (mudança visual real), nunca na entrada da fala.
- Posição: cartão de @ sempre no canto inferior, acima da faixa de UI do Instagram (y ≈ 1420 de 1920), nunca no topo. Ele não pode cobrir a legenda nem o rosto.
- Confira o @ no próprio Instagram (`og:title` da página) antes de renderizar. A transcrição erra o @: "jgcampus" em vez de @jgcampos.

## Pillow + `easing.py` (legenda)

Não use Remotion para a legenda corrida: são centenas de blocos e o motor já desenha a faixa em lote. Para ela, a árvore de `references/animation-catalog.md` continua valendo.

## Onde já está integrado

`scripts/easing.py` está copiado (mesma convenção de `tools.py`, duplicado por skill) em: `bombordo-boreste`, `autismo-cast`, `katia`, `podcast-reels` (`render_caps.py`, entrada da legenda) e `content-hub` (`render_lettering.py`, entrada do card). Ao portar para uma skill nova, copie o arquivo — não reimplemente easing local de novo.
