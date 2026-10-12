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

## Regras de motion (calibradas)

Números para o motion não sair "de template" (o usuário chamou o antigo de "ruinzinho"). Fontes:
`iart-ai/motion-design-skills` (MIT) e `kmilo93sd/agent-video-editor` (MIT), lidas em 12/10/2026.

| Movimento | Curva | Duração |
|---|---|---|
| Entrada | `cubic-bezier(0.16, 1, 0.3, 1)` (desacelera forte) | 300–500 ms |
| Saída | `cubic-bezier(0.7, 0, 0.84, 0)` | 200–300 ms (sai mais rápido do que entra) |
| Deslocamento | `cubic-bezier(0.65, 0, 0.35, 1)` | 300–400 ms |
| "Pop" de marca | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 400–600 ms |
| Escalonamento de itens | 40–80 ms por item, no máximo ~700 ms no total | — |

No Remotion, a mola calibrada em 33 mil quadros de recaps da Apple é `spring({config: {damping:
15.35, stiffness: 115, mass: 1}})`: chega desacelerando, sem quique (já no template). Use
`Easing.bezier(...)` com os valores acima em `interpolate` quando precisar da curva exata.

**Medido em vídeos de referência** (`IskakovDamir/apple-motion`, `Tejashmakwana/motionmaxxing`,
MIT/Apache, 12/10/2026):
- Entrada animada termina em ~8 quadros, com a maior parte do percurso nos 4 primeiros e cauda
  longa. Movimento típico de ~10 quadros (0,33 s).
- **No máximo uma mola com quique por peça** (no cartão Seguir, só o toque no botão).
- Saída: na maioria das vezes é corte (59% nos recaps da Apple), não animação.
- Quase nada aparece por fade: chega se movendo, revelando ou focando. Chega maior e encolhe
  até o lugar; nada cresce do zero.
- Palavras no ritmo da fala: 2–4 quadros entre palavras num gancho rápido, 4–6 num título,
  8–12 acompanhando a voz.
- Nunca: rótulo de "interface" no canto, contador tipo "01 / TEMA", texto-slogan ("Não é só X.
  É Y."), cartão genérico com bolinha de status. Cartão final ≤ 1,4 s; nunca mais de 3 quadros
  parados seguidos.

**Guias oficiais do Remotion** (cópia local, sem gastar tokens à toa: abra só o que precisar),
em `~/.cibo/vendor/remotion-skills/skills/remotion-markup/`:
`measuring-text.md` (`fitText`/`measureText`: a frase sempre cabe no cartão),
`motion-blur.md` (`HtmlInCanvasMotionBlur`), `light-leaks.md` (vazamento de luz procedural,
alternativa de licença limpa ao film burn), `transitions.md` (`@remotion/transitions`),
`text-highlights.md`, `lottie.md` (animações do LottieFiles), `sfx.md`, `video-editing.md`.
Para atualizar: `git clone --depth 1 https://github.com/remotion-dev/skills`. O Remotion é
gratuito para pessoa física e empresa de até 3 pessoas; acima disso exige licença.

- **Tempo com a fala:** o grafismo entra no máximo 0,5 s antes da palavra que o nomeia, tem
  conteúdo em até 1 s e cada elemento entra até 0,6 s depois de ser falado.
- **Tempo de leitura:** texto fica no mínimo `max(1,5 s; palavras × 0,33 s + 0,5 s)`; legenda
  com ≥ 20 quadros por bloco.
- **Contenção:** um único "momento uau" por peça; nada de animar o quadro inteiro de uma vez;
  não anime texto que ainda está sendo lido; sem overshoot em assunto sério ou financeiro; não
  empilhe transição sobre transição (wipe + giro + fade).
- **Som do grafismo:** um SFX por evento visual, 12–24 dB abaixo da voz, com o ataque 2–4
  quadros **antes** do evento; nunca em cima de palavra-chave.
- **Um cartão por vez** na faixa de grafismo; legenda e cartão nunca cobrem o rosto.
- Biblioteca CC0 de SFX (whoosh, clique, pop, notificação, impacto, stinger): `acervo.py find
  cc0 --type sfx`. Licença livre de verdade, ao contrário de efeitos ripados do YouTube.

## Remotion neste Mac (validado em 12/10/2026)

- Node 26 em `/opt/homebrew/bin`. No macOS o Remotion baixa sozinho o `chrome-headless-shell`: **não** passe `--browser-executable` (a instrução da skill da Anthropic é para Linux).
- Template pronto em `assets/remotion-template/` com `SeguirCard` (cartão do Instagram: entra com mola, o botão "Seguir" é tocado e vira "Seguindo", sai descendo). Props: `name`, `handle`, `avatar` e `font` (arquivos em `public/`), `top` (y em 1080×1920) e `tap` (quadro do toque).
- Template também traz `GanchoTitle` (título de gancho: painel escuro abre na horizontal, palavras sobem uma a uma com mola, palavras de `accent` na cor de destaque, sai subindo). Props: `text`, `accent` (lista de palavras), `color`, `font`, `top` (padrão 150, acima da cabeça), `size`. Entra em 1,0 s, logo depois do burn de abertura, por 3,5 s; sem SFX (fica colado no burn).
- Copie o template para `04_work/mg/` do projeto, rode `npm i`, ponha a fonte **do cliente** e o avatar em `public/`. O template não traz fonte nem cor de cliente nenhum. O avatar é a foto **atual do perfil do Instagram** do cliente (peça ao usuário; o círculo mostra a imagem quadrada inteira, como no app), nunca um quadro recortado do vídeo: o cliente reclamou de "foto aleatória" (João Campos, 12/10/2026).
- Sempre um `npx remotion still ... --frame=N` composto sobre um quadro real do corte antes do render inteiro.
- Render com alpha: `npx remotion render src/index.ts SeguirCard out/card.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --props='{"name":"...","handle":"@..."}'`.
- Sobreposição: no `podcast-reels`, ponha o `.mov` em `overlays` do clipe (item 46 da skill): entra na mesma codificação do corte, sem recodificar a entrega. `scripts/overlay_card.sh ENTRADA.mp4 card.mov INICIO SAIDA.mov [SFX.wav TEMPO]` fica só para motor que não tem `overlays`, numa passada separada **antes** do `burn_end.py`. O SFX vai no toque do botão (mudança visual real), nunca na entrada da fala.
- Posição: cartão de @ sempre no canto inferior, acima da faixa de UI do Instagram (y ≈ 1420 de 1920), nunca no topo. Ele não pode cobrir a legenda nem o rosto.
- Confira o @ no próprio Instagram (`og:title` da página) antes de renderizar. A transcrição erra o @: "jgcampus" em vez de @jgcampos.

## Pillow + `easing.py` (legenda)

Não use Remotion para a legenda corrida: são centenas de blocos e o motor já desenha a faixa em lote. Para ela, a árvore de `references/animation-catalog.md` continua valendo.

## Onde já está integrado

`scripts/easing.py` está copiado (mesma convenção de `tools.py`, duplicado por skill) em: `bombordo-boreste`, `autismo-cast`, `katia`, `podcast-reels` (`render_caps.py`, entrada da legenda) e `content-hub` (`render_lettering.py`, entrada do card). Ao portar para uma skill nova, copie o arquivo — não reimplemente easing local de novo.
