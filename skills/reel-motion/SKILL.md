---
name: reel-motion
description: Motor PADRÃO de edição do CIBO — reels 9:16 e 16:9 de fala com motion nascido da fala, por tema de cliente, entregues como pacote no DaVinci. Use em todo job de fala sem skill própria e em reel "com motion".
---

# reel-motion — motor padrão de edição do CIBO

Motor generalista configurado por tema de cliente (`temas/<cliente>.json`) + biblioteca de componentes Remotion.
Nunca copie o motor para o projeto; fora do piloto, não anime do zero o que a biblioteca já tem. Por que cada regra existe: `references/historico.md`.

## Pedido do editor → como se faz aqui (leia antes de qualquer job; cada linha já foi cobrada 2 a 10 vezes)

Antes de escrever script em pasta de job, ache a linha. Se não tem linha, o script novo nasce em `scripts/` do motor, não no job.

| O editor pede / o job precisa | Faça assim | Nunca |
|---|---|---|
| Zoom in/out, punch, movimento de câmera | **No Fusion, com motion blur (shutter 360°)**: `"camera_fusion": true` no reel.json (a fila roda o `resolve_fx.py`); ajuste pontual na timeline: `fusion_kit.py zoom "TL" "CÂMERA bruto" T0 T1 1.10`. O `davinci` recusa `camera_moves` sem essa chave | renderizar `camera.mov` para ter zoom; keyframe seco sem o editor pedir |
| Selo, logo, cartão entrando e saindo | `fusion_kit.py entra-sai "TL" "FAIXA"` (escala→1, blur→0, opacidade) | animar em Remotion o que é um PNG parado |
| Qualquer conversa com o Resolve | `import fusion_kit as K` (`K.resolve`, `K.abre_projeto`, `K.timeline`, `K.faixa`, `K.clipe_em`, `K.salva`); ver o que tem: `fusion_kit.py lista "TL"` | `dvr.scriptapp` à mão; `pm.SaveProject()` direto (trava no "Untitled Project") |
| Corte de fala | `reel.py PROJ rNN cortes` e, se avisar borda em cima da voz, `bordas.py W --aplica` antes da legenda | fechar o corte no tempo do Whisper: a voz acaba depois |
| Bruto 16:9 em reel 9:16, ou qualquer fonte de tamanho diferente da timeline | `"posicao_resolve": "auto"` no reel.json: o motor corrige a posição no Resolve e dá o zoom que enche o quadro (1,7778 no 16:9). `track` e `crops` em px reais da fonte. O `davinci` recusa sem a chave | a conta 1,7778 à mão em job novo (`"manual"` é só para job antigo que já gravou assim); escala 1 com barra sem o editor pedir |
| Entrega e conferência | `fila_davinci.py` → projeto novo organizado → o editor confere no preview | ffmpeg na entrega; MP4 queimado; render ou still pelo Resolve para conferir |
| Ajuste depois do primeiro pacote | na timeline pela API (`scripts/timeline/README.md`), render só da camada que muda | pacote novo, `rNN` novo, apagar timeline que o editor já mexeu |
| Trilha e SFX | 2–3 opções com prévia de 10 s no trecho real, antes do pacote; kit e tom na rubrica do cliente | escolher e nivelar sem ouvir; o mesmo som em tudo |
| Capa | quadro expressivo (olho aberto, nítido), um quadro diferente por corte, título fora do rosto, 1 quadro na timeline | primeiro quadro que aparecer; capas iguais no lote |
| Arquivo refeito no pacote | nome novo + `ReplaceClip` | mesmo nome (o Media Pool devolve o antigo do cache) |

**Motion sob medida no piloto (decisão do editor, 14/11/2026).** No primeiro reel de cada job o motion é feito para aquele vídeo: pode
escrever painel/animação nova e olhar o quadro quantas vezes precisar, sem o limite de "uma folha por decisão". Aprovado o piloto, o que
nasceu ali entra em `primitives.tsx`/`panels.tsx` como peça genérica do tema e o resto do lote sai da biblioteca. Fora do piloto vale a regra
da biblioteca (não animar do zero o que já existe).

**Fim de job:** script que você escreveu em `04_work/` é correção que o motor ainda não tem. Antes de fechar: suba ao motor o que serve
para o próximo cliente, anote o resto em `/Volumes/SSD/CIBO/repo/todo.md`, e rode `/Volumes/SSD/CIBO/repo/tests/fusion_kit_teste.py` se mexeu em script do Resolve.
(Em 14/11/2026 havia 170 scripts em pastas de job, 57 refazendo a conexão com o Resolve, e a biblioteca de Fusion da Andrea só existia lá.)

## Contrato do agente (10/11/2026) — o que o motor cobra sozinho

O caminho de um job de fala é este, e cada passo grava um **selo** (impressão digital dos arquivos conferidos) em `rNN/work/selos.json`.
A etapa seguinte recusa selo que falta ou ficou velho. **"Pronto" é o que `reel.py PROJ rNN selos` mostra, nunca a palavra do agente.**

| Passo | Comando | Selo | Se reclamar |
|---|---|---|---|
| estado | `status.py PROJ` | mostra `cortes✓ layout✗ audio· pacote·` | ✗ = arquivo mudou depois do selo: refaça a etapa |
| cortes | `reel.py PROJ rNN cortes` | `cortes` | corrija o `segs.json` ou registre a decisão em reel.json `"cortes_ouvidos": {"a-b": "motivo"}`. Borda em cima da voz (`bordas.py`) também trava desde 23/11/2026: `bordas.py W --aplica` acerta pelo silêncio |
| motion | escreva `rNN/motion.json` (declarativo: ver cabeçalho de `scripts/monta_props.py`; `scripts/esquema.py` lista painéis e campos) → `props` → `verifica` | `layout` | a saída diz o alvo e o defeito; `VERIFICA_TUDO=1` dá a folha única com tudo |
| som | `sfx.json` → `mix` | `audio` | — |
| pacote | `davinci` (exige os três) → `fila_davinci.py` | `pacote` | liberar sem selo é decisão do editor (`SELOS_OK=1`) |

- `motion.json` substitui o `props.py` à mão: sem coordenada de etiqueta (`"onde": "topo"|"base"`, a linha quebra sozinha), sem lista de burns, sem
  tela dividida escrita (sai dos painéis), vídeo sem legenda com `"legenda": false`. `props.py` antigo continua funcionando.
- O motor escolhe o próprio Python (venv com numpy/PIL) e cada processo tem o seu bundle: pode rodar `verifica` de outro reel durante um render.
- **Capa é do editor (trava, 23/11/2026):** `final`, `capa` e `entrega` recusam reel.json `"capa"` sem `"editor": "<o que ele escolheu>"`.
  Mostre a folha do `capa_cand.py`, pergunte e registre a escolha nas palavras dele. Prévia sem escolha: `CAPA_PROVISORIA=1` (não entrega).
- **Timeline que o editor mexeu é dele (trava, 23/11/2026):** `scripts/guarda_editor.py`. Toda timeline que a CIBO monta ganha assinatura;
  apagar/reimportar só passa se ela está como a CIBO deixou. Script novo que apaga timeline usa `G.apaga(mp, p, tl)`, nunca
  `mp.DeleteTimelines` direto, e chama `G.marca(p, tl)` depois de montar. Liberar: `CIBO_EDITOR_OK=1`, só depois de perguntar.
- **Dúvida de DaVinci: consulte a documentação antes de tentar** (editor, 23/11/2026): `scripts/doc_resolve.py api TERMO` (API de
  scripting) ou `doc_resolve.py manual TERMO` (manual do Resolve). Achou algo que não estava em `regras/davinci.md`? Anote lá.
- Mudou o motor? `/Volumes/SSD/CIBO/repo/tests/regressao.py check --engine reel-motion` (22 s, sem câmera) antes do push.

## Padrão de edição do CIBO (10 etapas)

Todo job de fala sem skill própria segue esta receita. Cliente com skill própria mantém identidade e regras dele e entrega
pelo mesmo pacote DaVinci. Referência viva: `andreia/demandaVideoEstiloPriscilla/`.

| # | Etapa | Como |
|---|---|---|
| 1 | Briefing | `briefing-criativo`: tema (paleta, fontes, perfil de movimento `theme.motion`), formatos (9:16 e/ou 16:9 `orient: h`), trilha, desenho de som (bloco `sfx` do tema), **grafia de todo nome na tela** |
| 2 | Fonte | girar/full range no reel.json (`rotate`, `full_range`); rastreio de rosto `rastreio.py` → `track`; fps qualquer (o `davinci.py` faz a cópia 29,97 sozinho) |
| 3 | Trechos | roteiro fechado: `segs_auto.py` → fechar pela energia → `fala-limpa` (`hesita.py`, `checa_takes.py`); conversa: `takes.py` |
| 4 | Legenda | etapa `legenda` (MFA) → `conserta_mfa.py rNN/` onde o MFA colapsou → `legenda-cruzada` |
| 5 | Motion | `props.py` com painéis nascidos da fala (`references/catalogo.md`), `checa_props`, perfil do tema; **`reel.py PROJ rNN verifica` até dar OK** (portão de layout, ~15 s, sem câmera; a etapa `davinci` recusa sem ele) |
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
- **Câmera de YouTube nos cortes: `camera_cortes.py PROJ rNN`** (Bruno, 11/11/2026). Planeja um estado por take e grava `camera_moves` no reel.json (keyframes no bruto pelo `davinci`, sem render): `empurra` = zoom in lento que no corte volta seco, nunca zoom out; `fechado` = salto de +16% no corte, volta em outro; `aberto` = parado. Remendo < 2,5 s herda o estado anterior; troca no quadro exato do corte. `--ver` só mostra o plano; `--push`/`--salto` ajustam a dose.
- **Vídeo sem legenda é detectado sozinho** (`captions` vazio no props, ex.: YouTube 16:9): o pacote não renderiza a camada de legenda nem grava SRT, o `checa_props` libera a faixa de baixo do painel e o `gancho-e-ritmo` mede o ritmo pela fala (`--mfa`). Nada de arquivo-coringa de legenda no pacote.
- **`reel.py PROJ rNN verifica` = portão de layout (10/11/2026).** Renderiza 1 quadro por painel, título, palavra-chave, gancho e tarja
  (layer `verifica`, sem câmera) e o `Medidor.tsx` mede o DOM: painel que não renderiza (campo faltando, ex.: `strike` sem `line2At`),
  texto que vaza do painel/quadro, estoura a caixa, fica sobre outra peça, pílula sobre pílula, letra menor que 19 px, painel vazio.
  Saída curta com o id de cada alvo + folha marcada `05_qa/rNN_verifica.jpg`; `VERIFICA_TUDO=1` monta a folha com todos os alvos
  (a conferência visual do motion, uma folha só). Passou = selo do props atual; a etapa `davinci` não roda sem o selo
  (`VERIFICA_OK=1` só por decisão do editor). Sobreposição intencional: `"verifica_ignora": ["painel_03:texto sobre elemento"]`.
  **Nunca diga "motion pronto" só com o `checa_props`: ele confere tempo, não layout** (YT 01 da Priscilla: 5 painéis quebrados e
  8 com texto cortado com "OK: nenhuma pendência"). Etiquetas: prefira `"layout": {"autoTags": true}` (largura medida) a x na mão.
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
