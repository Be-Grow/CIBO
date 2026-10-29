---
name: reel-motion
description: Motor PADRÃO de edição do CIBO — reels 9:16 e 16:9 de fala com motion nascido da fala, por tema de cliente, entregues como pacote no DaVinci. Use em todo job de fala sem skill própria e em reel "com motion".
---

# reel-motion — motor padrão de edição do CIBO

Motor generalista configurado por tema de cliente (`temas/<cliente>.json`) + biblioteca de componentes Remotion.
Nunca copie o motor para o projeto; nunca anime do zero o que a biblioteca já tem. Por que cada regra existe: `references/historico.md`.

## Padrão de edição do CIBO (10 etapas)

Todo job de fala sem skill própria segue esta receita. Cliente com skill própria mantém identidade e regras dele e entrega
pelo mesmo pacote DaVinci. Referência viva: `andreia/demandaVideoEstiloPriscilla/`.

| # | Etapa | Como |
|---|---|---|
| 1 | Briefing | `briefing-criativo`: tema (paleta, fontes, perfil de movimento `theme.motion`), formatos (9:16 e/ou 16:9 `orient: h`), trilha, desenho de som (bloco `sfx` do tema), **grafia de todo nome na tela** |
| 2 | Fonte | girar/full range no reel.json (`rotate`, `full_range`); rastreio de rosto `rastreio.py` → `track`; fps qualquer (o `davinci.py` faz a cópia 29,97 sozinho) |
| 3 | Trechos | roteiro fechado: `segs_auto.py` → fechar pela energia → `fala-limpa` (`hesita.py`, `checa_takes.py`); conversa: `takes.py` |
| 4 | Legenda | etapa `legenda` (MFA) → `conserta_mfa.py rNN/` onde o MFA colapsou → `legenda-cruzada` |
| 5 | Motion | `props.py` com painéis nascidos da fala (`references/catalogo.md`), `checa_props`, perfil do tema; `qa_paineis --video` |
| 6 | Som | trilha `talking-head-music` (prévia de 10 s no trecho real, 2–3 opções) e `sfx_tema.py rNN/ public/rNN/props.json temas/<tema>.json`, também com prévia antes do render |
| 7 | Revisão | `revisa` (sem render). **Prévia é no Resolve, não no Remotion** (Andreia 19/10: "tem como fazer a prévia no davinci?"; João 21/10: noite perdida em prévia Remotion de aula): o piloto vai pelo passo 8 e o editor aprova lá. `previa` só se ele pedir MP4 |
| 8 | Pacote + Resolve | **Sempre pela API, sem perguntar se ele prefere importar** (João 21/10): `fila_davinci.py PROJ "Projeto" "BeGrow/<Cliente>" r01 r01h …` = capa → pacote → projeto novo organizado → Fusion/cores → bins → `qa_resolve.py`. Antes, leia `client-router/references/regras/davinci.md` inteiro (lições da Andreia). Aula/vídeo longo: `"grosso": true` (bruto cortado + voz + trilha + legenda SRT, sem painel/rastreio/render) |
| 9 | Depois do render do editor | `qa_render.py PROJ` (sincronia por trecho, offline, preto) nos dois formatos; `video-delivery-safety-check` |
| 10 | Correção | **direto na timeline do Resolve pela API, render só da camada que muda** (kit `scripts/timeline/`, README; editor 29/10/2026: "ajuste mais rápido na timeline, pacote só dos componentes que mudam"). Nunca pacote inteiro novo nem `rNN` novo por ajuste. Também: `--so-el`, `trecho`, `resolve_refaz_de_backup.py`; nunca ciclos de .drt; QA de novo em todas as versões |

Todo arquivo do pacote leva o sufixo do reel (`voz__r01.wav`): o Resolve junta mídia de mesmo nome entre pacotes. Toda regra geral do DaVinci (nomes, FPS, .drt/GlobalIn,
LoadRenderPreset, bins, cores) mora em `client-router/references/regras/davinci.md`.

## Estrutura

```
reel-motion/
  scripts/reel.py        pipeline por etapas: reel.py PROJ rNN ETAPA
  scripts/{blocos,mix,checa_props,checa_takes,wt}.py
  temas/<cliente>.json   cores, fontes, título/legenda/rótulo, destaque, filtros, capa
  mg/src/reel/theme.ts       tema (C, T, applyTheme) + helpers fTitle/fAcc/fLab/fCap, easing, ramp
  mg/src/reel/primitives.tsx peças: Pill, Title, I (destaque), MediaFrame, Fonts, Grain, VBlur…
  mg/src/reel/panels.tsx     painéis = composição das peças + registro PANELS
  mg/src/reel/Reel.tsx       só a composição: layout dividido/cheio, legenda, gancho, lower, burns
  mg/src/reel/Capa.tsx       capa por layout do tema ("serif" Priscilla, "faixa" João)
  mg/node_modules -> /Volumes/SSD/CIBO/reel-motion/node_modules (no SSD, nunca no disco interno)
```

O projeto do cliente guarda só dados: `PROJ/04_work/rNN/{reel.json,segs.json,props.py,blocos_manual.txt,sfx.json}`
e `PROJ/04_work/public/` (pasta pública do Remotion: camera.mov, mídia, fontes copiadas do tema).
`reel.json` escolhe o tema (`"tema": "joao-campos"`) e a câmera (`"camera": "face"` para bruto com
rastreio de rosto, `"crop"` para fonte já editada/multicâmera com `crops: [{at, cx}]`).

Etapas: `fonte` → `takes` → `voz` → `legenda` → `props` → `camera` → `mix` → `previa` → (aprovação) →
`davinci` (padrão do CIBO: o editor faz o render final no Resolve; pacote validado num projeto NOVO,
ver `client-router/references/regras/davinci.md`) — `final` (MP4 queimado, lento) só se pedirem; ajustes com `trecho A B` e `entrega`. Igual ao fluxo da `priscilla-daher` (ver lá os detalhes de
takes, MFA e capa).

## Biblioteca de componentes (regra)

- Painel novo = **composição das peças de `primitives.tsx`**. Antes de escrever JSX, veja se um painel
  de `PANELS` serve com outros textos/tempos; depois, se dá para montar com as peças existentes.
  Só crie peça nova quando nenhuma serve — e ela entra em `primitives.tsx`, genérica, usando só o
  tema (`C`, `fTitle`, `fAcc`, `fLab`), para o próximo cliente herdar.
- Sombra e escurecimento também são do tema (`C.shadow`, `C.scrim` em r,g,b; helpers `sh(a)`/`scr(a)`); destaque com fonte própria em `accent.family`; burn do pacote DaVinci em `theme.burnFF` (filtro ffmpeg).
- Pacote DaVinci separa as partes de cada painel: envolva título, cada item, linha e risco em `<Pt k=…>` e liste as chaves em `PARTES` no `reel.py` (feito em checklist, timeline, waves, balance, root, curve, pillars, strike, cards, sides, route, stack, roles, ladder, hub; faça igual nos demais). Só importar no Resolve, sem render: `SEM_RENDER=1 resolve_render.py …` (deixa o projeto novo aberto).
- Nenhuma cor ou fonte fixa em componente: sempre `C.<papel>` e os helpers do tema. Papéis das cores:
  `paper/paper2` fundo do painel; `ink/ink2` texto no painel; `terra` destaque; `terraDark` faixa;
  `peach` destaque sobre vídeo; `white` superfície de card; `video` texto sobre vídeo;
  `onAccent` texto sobre o destaque; `pill` pílula; `bg` fundo.
- Mudança em peça ou painel compartilhado: rode o teste de regressão do tema da Priscilla (mesmo quadro
  do r02 no motor antigo e no novo, PSNR) antes de usar no lote.

## Regras de motion (detalhe e exemplos em `references/motion-regras.md`)

- Cada painel nasce do que está sendo falado; cada reel do lote tem painel próprio e não repete a família do anterior;
  entrada casada com a palavra (`checa_props.py` cobra).
- Nada sobreposto: `qa_paineis.py PROJ rNN 0.5 --video <prévia>` antes de mostrar qualquer prévia ou final.
- Perfil de movimento no tema (`theme.motion`: `atual`, `editorial`, `premium`, `energetico`), escolhido no briefing pelo tom.
- Cor da identidade sem perder leitura: contraste ≥ 4,5:1 (≥ 3:1 título ≥ 60 px) com `contraste.py temas/<tema>.json`.
- `camera: crop` nunca mais apertado que a altura nativa; um trabalho pesado por vez quando há Whisper rodando.

## Temas existentes

| Tema | Cliente | Notas |
|---|---|---|
| `priscilla` | Priscilla Daher | padrão do motor; Instrument Serif + destaque itálico terracota; capa "serif" |
| `andreia` | Andrea Francomano | creme, violeta-escuro e dourado; Cormorant Garamond (títulos, itálico dourado) + Montserrat (legenda); capa "serif" com bgFill cor |
| `joao-campos` | João Campos / Vai Lá e Faz Caxt | marinho/azul das thumbs, Montserrat Black em caixa alta, destaque por peso + azul claro, faixa azul royal; capa "faixa" |
| `growth-leaders` | João Campos / Growth Leaders | marca própria do evento: nunca misture com `joao-campos`; saída seca |

## Revisão automática e fila
- `reel.py PROJ rNN revisa` junta checa_takes (voz da equipe, corte no meio da palavra por energia + fim de palavra do Whisper),
  hesita, checa_props (inclui etiqueta que ela não diz) e olhar nas pontas dos cortes. O `final` roda a revisa antes. ~15 s.
  Por último, a nota criativa do `gancho-e-ritmo` (gancho 3 s, tempo morto, densidade, variação, ênfase, final; limiar no
  bloco `"qualidade"` do tema). No `final`, nota abaixo do limiar para o render; o editor libera com `GANCHO_OK=1`.
- **Variação e movimento (biblioteca compartilhada `scripts/movimento.py`).** `planeja` transforma ênfases
  candidatas em movimentos alternando punch/pulse/long com intervalo mínimo por tipo (presets `editorial`, `podcast`,
  `energetico`, ajustáveis no bloco `"movimento"` do tema); sai como `camera_moves` (reel) ou `impact_pulses`/`long_moves`
  (motores de podcast, mesmo formato que o render deles já lê). `confere` é o orçamento: no máximo N iguais seguidos por
  categoria (`"variacao": {"sfx": 3, "burn": 2, "movimento": 2, "painel": 1}`, 0 = sem limite), e roda no `revisa` como aviso.
  Andreia: sfx 0 (a tigela única foi aprovada), movimento 3, painel 3.
- `lote.py PROJ "r06 trecho 43 47.2" "r08 final" …` roda etapas uma por vez, segue se uma falhar, resume no fim.
  Nunca mais fila com `while pgrep -f`.

## Referências (abra só quando o gatilho bater)

| Arquivo | Abra se |
|---|---|
| `references/catalogo.md` | for montar painel: veja o que já existe (peças e painéis pela função na fala) antes de escrever JSX |
| `references/motion-regras.md` | painel novo, perfil de movimento, cor do tema, pílulas sobrepostas, tela invertida, olhar para o lado, capa do feed |
| `references/fonte-e-legenda.md` | bruto multicâmera (`acha_trechos`/`aplica_mapa`), `edit_fix` na legenda, recorte, RAM |
| `references/davinci-licoes.md` | etapa `davinci` do motor: fragmentação, custo, `so_legenda`, `extras` |
| `client-router/references/regras/davinci.md` | qualquer regra do Resolve: nomes, FPS, .drt/GlobalIn, cache, render, bins, cores |
| `references/fusion-camera.md` | movimento de câmera no Fusion, curva dura, mix do editor, corrigir texto sem remontar |
| `references/horizontal-16x9.md` | versão 16:9 (`orient: h`) ou fonte de celular (rotação, 30 fps, full range) |
| `references/eficiencia-auditorias.md` | custo do job, `status.py`, auditorias e validação dos checadores |
| `references/historico.md` | quiser saber de onde veio uma regra (datas, falas do editor, testes medidos) |
| `references/clientes/<cliente>/` | rubrica e lições do cliente (`client-router/scripts/licao.py ler <cliente>`) |
