---
name: reel-motion
description: Motor PADRÃO de edição do CIBO (aprovado no job da Andreia Francomano, 20/10/2026) — reels 9:16 e versões 16:9 de talking head com motion nascido da fala (tela dividida, painel em cima ou ao lado, tela cheia no gancho e nas viradas), legenda palavra a palavra, burn nas trocas, SFX e trilha pelo tema, capa, e entrega como pacote por camadas montado no DaVinci Resolve pela API (projeto novo organizado, movimentos de câmera no Fusion, cores por tipo, QA na timeline e no render). Configurado por tema de cliente e montado com uma biblioteca de componentes Remotion. Use em todo job de edição de fala de cliente novo ou sem skill própria, e em qualquer reel "com motion" (Priscilla, João Campos, Andreia e novos), em vez de copiar o motor para o projeto.
---

# reel-motion — motor genérico de reel com motion

Nasceu do motor aprovado da Priscilla Daher (13/10/2026). O editor pediu: **um motor generalista que
aceita configurações, não um motor por cliente**, e **uma biblioteca de componentes reutilizáveis
(princípio do React), não animação feita do zero a cada reel**.

## Padrão de edição do CIBO: o fluxo da Andreia (editor, 20/10/2026)

"Eu gostei muito do que foi feito lá e gostaria que fosse o padrão de edição da CIBO." Todo job de fala sem skill própria
segue esta receita; clientes com skill própria mantêm identidade e regras deles, mas entregam pelo mesmo pacote DaVinci.
Referência viva: `andreia/demandaVideoEstiloPriscilla/` (brief, review_2026-10-20.md, 8 timelines).

| # | Etapa | Como |
|---|---|---|
| 1 | Briefing | `briefing-criativo`: tema (paleta, fontes, perfil de movimento `theme.motion`), formatos (9:16 e/ou 16:9 `orient: h`), trilha, desenho de som (bloco `sfx` do tema), **grafia de todo nome na tela** |
| 2 | Fonte | girar/full range no reel.json (`rotate`, `full_range`); rastreio de rosto `rastreio.py` → `track`; fps qualquer (o `davinci.py` faz a cópia 29,97 sozinho) |
| 3 | Trechos | roteiro fechado: `segs_auto.py` → fechar pela energia → `fala-limpa` (`hesita.py`, `checa_takes.py`); conversa: `takes.py` |
| 4 | Legenda | etapa `legenda` (MFA) → `conserta_mfa.py rNN/` onde o MFA colapsou → `legenda-cruzada` |
| 5 | Motion | `props.py` com painéis nascidos da fala (catálogo abaixo), `checa_props`, perfil do tema; `qa_paineis --video` |
| 6 | Som | trilha `talking-head-music` (prévia de 10 s no trecho real, 2–3 opções) e `sfx_tema.py rNN/ public/rNN/props.json temas/<tema>.json`, também com prévia antes do render |
| 7 | Prévia | `previa` + `revisa`; aprovação do piloto antes do lote |
| 8 | Pacote + Resolve | `fila_davinci.py PROJ "Projeto" "BeGrow/<Cliente>" r01 r01h …` = capa → pacote → projeto novo organizado → Fusion/cores → bins → `qa_resolve.py` |
| 9 | Depois do render do editor | `qa_render.py PROJ` (sincronia por trecho, offline, preto) nos dois formatos; `video-delivery-safety-check` |
| 10 | Correção | só o que mudou (`--so-el`, `trecho`, `resolve_refaz_de_backup.py`); nunca ciclos de .drt; QA de novo em todas as versões |

Teste de ponta a ponta (20/10/2026, `andreia/…/04_work/t01`, 15 s, painel `hub`, Resolve aberto): `fila_davinci.py` levou
3 min (pacote 0,6 GB, 26 clipes, 2 camadas de Fusion, `qa_resolve` OK). Achou e corrigiu: fundo do painel e etiquetas caíam
no bin `01 BRUTO`, e a reimportação do .drt deixava SFX órfãos duplicados ("X.wav import") — o `resolve_projeto.py organiza`
agora reclassifica e apaga só duplicado de mesmo arquivo que nenhuma timeline usa. Atalhos do teste: o `mix` remonta a voz do
`src_48k.wav` (copie/ligue o da fonte); `qa_paineis`, `capa_pausas` e `sfx_tema` rodam com `~/.venvs/audiotools/bin/python`.

Nomes no pacote: todo arquivo leva o sufixo do reel (`voz__r01.wav`, `el/painel_0__r01h.mov`, `capa__r01.mov`), porque o
Resolve junta arquivos de mesmo nome entre pacotes (foi o "áudio de outro vídeo" do 03). Pacote antigo sem sufixo é
renomeado na próxima etapa `davinci`, sem renderizar de novo.

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
`davinci` (padrão do CIBO desde 18/10/2026: o editor faz o render final no Resolve; pacote validado num projeto NOVO,
ver client-router/regras-transversais "DaVinci Resolve pela API") — `final` (MP4 queimado, lento) só se pedirem; ajustes com `trecho A B` e `entrega`. Igual ao fluxo da `priscilla-daher` (ver lá os detalhes de
takes, MFA e capa).

## Biblioteca de componentes (regra)

- Painel novo = **composição das peças de `primitives.tsx`**. Antes de escrever JSX, veja se um painel
  de `PANELS` serve com outros textos/tempos; depois, se dá para montar com as peças existentes.
  Só crie peça nova quando nenhuma serve — e ela entra em `primitives.tsx`, genérica, usando só o
  tema (`C`, `fTitle`, `fAcc`, `fLab`), para o próximo cliente herdar.
- Sombra e escurecimento também são do tema (`C.shadow`, `C.scrim` em r,g,b; helpers `sh(a)`/`scr(a)`); destaque com fonte própria em `accent.family`; burn do pacote DaVinci em `theme.burnFF` (filtro ffmpeg). Antes ficavam no marrom da Priscilla em todo cliente (17/10/2026).
- Pacote DaVinci separa as partes de cada painel: envolva título, cada item, linha e risco em `<Pt k=…>` e liste as chaves em `PARTES` no `reel.py` (feito em checklist, timeline, waves, balance, root, curve, pillars, strike, cards, sides, route, stack, roles, ladder, hub; faça igual nos demais). Só importar no Resolve, sem render: `SEM_RENDER=1 resolve_render.py …` (deixa o projeto novo aberto). Pedido do editor, 17/10/2026.
- Nenhuma cor ou fonte fixa em componente: sempre `C.<papel>` e os helpers do tema. Papéis das cores:
  `paper/paper2` fundo do painel; `ink/ink2` texto no painel; `terra` destaque; `terraDark` faixa;
  `peach` destaque sobre vídeo; `white` superfície de card; `video` texto sobre vídeo;
  `onAccent` texto sobre o destaque; `pill` pílula; `bg` fundo.
- Mudança em peça ou painel compartilhado: rode o teste de regressão do tema da Priscilla (mesmo quadro
  do r02 no motor antigo e no novo, PSNR) antes de usar no lote.

## Catálogo (o que já existe — procure aqui antes de escrever JSX)

Peças (`primitives.tsx`): `Pill`, `Title`, `I` (destaque), `MediaFrame`, `Counter` (conta/salta nos valores ditos),
`DropCard` (card que cai e assenta), `StrikeChip` (chip que treme em `warnAt`, é riscado em `strikeAt`, pulsa em `pulseAt`).

Painéis (`PANELS`), pela função na fala:
| Fala | Painel |
|---|---|
| número dito, salto de valor | `counter` (grade que acende), `stat`, `tickets`, `bars` |
| peso acumulando, lista de cargas | `stack` |
| papéis/ideias abandonadas, um que domina | `roles` |
| uma ideia que abre em várias saídas | `hub` |
| "quanto mais X, mais Y", progressão | `ladder` |
| trajetória com marcos | `timeline`, `route` |
| tese corrigida | `strike` |
| dois lados / contraste | `sides` |
| ordem / passos | `cards`, `checklist`, `step` |
| ranking, preço, moedas | `rank`, `ruler`, `coins`, `oscillate` |

Vídeo de inserção (`inserts`, area `bottom`/`full`): só com aprovação do editor. O João reprovou B-roll de banco
(13/10/2026): reação de convidado em corte de foco no apresentador se resolve com o bruto multicâmera.

## Animação ligada ao conteúdo (regra do editor, 13/10/2026)

- **As animações não podem ser todas do mesmo jeito: cada painel nasce do que está sendo falado** naquele
  trecho (número dito vira contador; contraste vira lados; trajetória vira rota; tese corrigida vira
  riscado; lista dita vira checklist). Não use painel genérico só para "ter motion".
- Variar entre os reels do mesmo lote e do mesmo feed: cada reel tem pelo menos um painel próprio e não
  repete a família de painéis do reel anterior.
- Tempos de entrada casados com a palavra no `edit_mfa.json` (o `checa_props.py` cobra).

## Sem sobreposição (regra do editor, 13/10/2026)

- O João reprovou os cortes 02 e 03 por "elementos sobrepondo outros". Quadros-teste soltos não pegam isso.
- **Antes de mostrar qualquer prévia ou final: `qa_paineis.py PROJ rNN 0.5 --video <prévia>`** (painel a cada 0,5 s, folhas em 05_qa; com `--video` os quadros saem da prévia em segundos, sem renderStill quadro a quadro, que levava ~9 s/quadro com a máquina ocupada) e olhe
  todas as folhas: pílula sobre título, texto quebrando, elemento cortado na borda do painel, linhas de pílulas coladas.
- Pílulas soltas (`tags`): com `layout.autoTags` (tema do João) as da mesma linha (mesmo y) são distribuídas pela largura
  medida, sem colidir; linhas de pílulas abaixo de y 870 do desenho saem da borda — use 790/855.
- Prefira dar a informação dentro do próprio painel (destaque no título, pulso do item, subtítulo do card) a uma pílula solta.

## Jeito de mexer por cliente (perfis de movimento, 20/10/2026)

O editor pediu mais qualidade no motion; aprovado no antes/depois do 02 da Andrea ("ficou mais suave", 05_qa/motion_antes_depois).
Tudo no Remotion, só princípios de animação (o editor não usa After Effects). `theme.motion` no tema do cliente:

| Perfil | Curva de entrada | Duração | Quique | Título | Fundo vivo | Para |
|---|---|---|---|---|---|---|
| `atual` (padrão sem bloco) | bezier(.22,.61,.36,1) | 1× | sim | inteiro | não | sai idêntico ao motor antigo |
| `editorial` | bezier(.3,0,.15,1) | 1,15× | não | palavra por palavra, 70 ms | sim | bem-estar, espiritualidade, editorial (Andrea) |
| `premium` | bezier(.4,0,.2,1) | 1,2× | não | palavra, 80 ms | leve | luxo, marca premium |
| `energetico` | bezier(.16,1,.3,1) | 0,8× | 1,3× | palavra, 45 ms | não | hype, negócios rápidos |

- Campos soltos sobrescrevem o perfil: `{"perfil": "editorial", "dur": 1.05, "ambient": 0.5}`.
- Peças: `Title` (máscara por palavra), `Ambient` (manchas de luz que derivam ~16 s), `pop(y1)` no lugar de curva com
  quique fixa (o perfil escala ou zera o quique), `M.settle` = detalhe que assenta depois do elemento (subtítulo do card em `sides`).
- Princípios que valem para painel novo: entrada desacelera até parar, saída acelera; um destaque por quadro;
  grupo entra escalonado (40–80 ms por item, grupo inteiro ≤ 0,8 s); elemento maior ou que anda mais leva mais tempo;
  conteúdo sério/bem-estar sem quique; pelo menos 0,3 s parado depois de cada movimento.
- Escolha o perfil no briefing pelo tom do cliente; mostre antes/depois de 10 s quando mudar.
- Tipografia (20/10/2026, ajuste fino aprovado sem diferença perceptível; o ganho visível está no movimento): título com
  `title.lh` 1,1 e `title.ls` '-0.015em' (serifa grande); legenda ≥ 60 px na tela dividida; `motion.peso` [ini, fim] faz a
  palavra de destaque engrossar ao aparecer (só fonte variável; Andrea [400, 750]).

## Cor: identidade sem perder leitura (regra do editor, 13/10/2026)

- As cores dos painéis vêm da identidade do cliente (medidas de material real dele: thumbs, banner,
  capa aprovada), **mas nunca à custa da leitura**. Todo par texto/fundo do tema passa no contraste
  WCAG ≥ 4,5:1 (≥ 3:1 para título ≥ 60 px). Meça com `scripts/contraste.py temas/<tema>.json` ao criar ou
  mudar um tema; destaque que não passa vira fundo (faixa) com texto claro, não texto colorido.

## Bruto multicâmera (episódio já editado + câmeras originais)

Quando a fonte é o episódio editado e o editor manda o bruto, a **imagem vem do bruto e o áudio continua o do episódio**
(já nivelado). Assim um corte com foco no apresentador nunca cai num plano de reação da convidada.
1. Identifique cada arquivo (quadro + duração) e os duplicados (mesmo tamanho e mesmo hash de começo/fim).
2. `acha_trechos.py EP_16k.wav sync/epXX.json rNN/segs.json … -- BRUTO1 BRUTO2` casa cada trecho no bruto (envelope 10 ms + forma de onda).
   O close da convidada casa com score ~0,98; o aberto ~0,85; trecho < 1,5 s pode dar falso positivo.
3. `aplica_mapa.py rNN/ sync/epXX.json` grava `video_map` no reel.json (trecho curto que destoa herda o offset dos vizinhos).
   Corte do convidado: monte o `video_map` à mão (pergunta do apresentador no aberto, resposta no close).
4. `reel.py PROJ rNN camera` usa o `video_map` (recorte 9:16 em `raw_cx` ou `cx` por trecho).
Também ficam aqui: `props_base.py` (props de um reel a partir das partes do corte) e `sfx_auto.py` (SFX e cliques a partir do props).

## Texto da legenda

- `edit_fix` só para palavra que o Whisper **inventou** na emenda ("porque", "E aí") ou ouviu claramente errado
  ("te porrando" → "te empurrando"). Variação de fala ("de"/"com", "tava"/"estava") fica como o modelo grande ouviu:
  no 01 do João a legenda cruzada (large-v3) derrubou duas trocas minhas.
- Correção pontual depois do render: `trecho A B` refaz só aqueles segundos.

## Recorte e qualidade

- `camera: crop` trava a altura inteira da fonte (608×1080 em 1080p). Nunca close mais apertado
  (regra transversal "sem zoom além da escala nativa"; o João reclamou em 09/10/2026).

## RAM (Mac de 16 GB)

- Um trabalho pesado por vez quando há Whisper rodando. Quadros de vídeo longo: um `ffmpeg -ss T -frames:v 1`
  por quadro, nunca `fps=1/60` decodificando o episódio inteiro.

## Variações pedidas pela Priscilla (13/10/2026)
- **Tela dividida invertida:** `split: [{s, e, inv: true}]` põe ela em cima (topo da cabeça um pouco cortado, `layout.camUp`, padrão 300) e o painel embaixo, subido `layout.invPad` (150) acima da borda por causa da interface do Instagram; a legenda vai para cima do painel, sobre o vídeo. Entre um trecho normal e um invertido, ponha uma tela cheia curta (não emende os dois).
- **Olhar para o lado:** `scripts/olhar.py public/rNN/camera.mov --folha 05_qa/rNN_olhar.jpg` antes da prévia; o detector marca também piscada e cabeça inclinada, então confira a folha. Olhada clara numa emenda/pausa: segure o quadro anterior olhando para a câmera (`freezeframes`) e re-renderize só o trecho; olhada com ela falando em tela cheia fica.
- **Capa para o feed:** `capa.frame_file` = quadro recortado da fonte aberta 4K (ela mais baixa, título acima da cabeça, dentro da faixa 240–1680 do grid 3:4); com `shift` o topo vazio vira a imagem desfocada.
- **Trilha:** `music_gap` 18,5 dB (o `mix` calibra sozinho).

## Eficiência (auditoria de 14/10/2026, medida na sessão da Priscilla)

A sessão dos reels 01–05 teve 1.575 turnos do agente para ~62 mensagens do editor; 529 M tokens de leitura de cache
(cada turno relê todo o contexto), 98 imagens lidas e 55 comandos só de status. O custo cresce com **turnos × contexto**,
então o que mais economiza é fazer menos turnos e não encher o contexto.
- **Status:** `scripts/status.py PROJ` responde "como tá?" num comando (etapas por reel, o que roda, pausados, órfãos, SSD).
  Não encadeie ps/tail/ls; espere a notificação do trabalho em segundo plano em vez de consultar.
- **Um comando por decisão:** encadeie as etapas que não pedem julgamento (props → mix → prévia → folhas) num comando só.
- **Imagens:** cada imagem lida fica no contexto e é relida em todo turno. Leia folha só onde há decisão visual
  (capa, painéis antes da prévia); o resto é checador: `checa_props`, `checa_takes`, `hesita.py` (ééé e repetição),
  `olhar.py`, legenda cruzada, `qa_paineis --video`.
- **Takes:** `scripts/takes.py src_large.json src_16k.wav` (só a voz dela; tentativas superadas resumidas com ~ — não esconda:
  no 05 o take bom era o "superado" 2 vezes).
- **Um trabalho pesado por vez com Whisper rodando**; renders com 2 abas (`--concurrency=2`). Máximo: 1 render + 1 câmera.
- **Câmera:** sai direto em 1080 (`out_size`; warp continua em 4K). Medido em 20 s: 407 s → 356 s, 2,55 GB → 0,36 GB,
  PSNR 47 dB / SSIM 0,992 contra o proxy antigo. Planos iguais ao job anterior: enquadramentos reaproveitados, sem face_track.
- **Robustez:** render com limite de tempo (12 s por segundo de vídeo, mín. 6 min) e 1 nova tentativa; trava por etapa
  (`work/.trava_<etapa>`) impede duas câmeras no mesmo arquivo; órfãos do motor (esbuild/Chrome com pai 1) são encerrados
  antes de cada render — dois ficaram 4 h a ~280% de CPU. Encerrar render: mate o grupo (`os.killpg`), nunca só o npm.
- **Mudou trecho (gaguejada, take trocado) depois das props:** `scripts/retempo.py segs_antigo segs_novo props.py sfx.json reel.json`
  recalcula os tempos; confira à mão o que caiu em take vindo de outro ponto da fonte (o remapeador joga para a emenda).
- **Ajuste pontual:** `trecho A B`, `capa`, `audio`, `entrega` — nunca render inteiro para mudança localizada.
- **Reel já entregue:** não regere a câmera dele (mesmo com imagem equivalente). No 05 a câmera nova tinha o zoom alguns px diferente
  nos punches (15% dos quadros < 35 dB contra a antiga, nitidez igual); um `trecho` depois emendaria duas câmeras e pularia.

- **Melhorias dos extras 06–10 (14/10/2026):**
  - `capa_cand.py FONTE folha.jpg T1 T2…` monta os candidatos de capa já no recorte de feed (rosto detectado, cabeça em
    y≈600); `--grava T rNN/capa_feed.png` grava o escolhido. Capa saiu de 3–5 turnos para 1 folha + 1 comando.
  - `checa_props.py` sugere as palavras ditas em cada vazio do painel e pega: etiqueta passando da borda direita
    (largura estimada, um pouco conservadora), abaixo de y 690 em painel invertido, abaixo de y 770 em painel normal
    (encosta na legenda) e duas etiquetas sobrepostas na mesma faixa. Pegou 4 defeitos em reels já entregues (06, 08, 09, 10).
  - Conversa livre (entrevista): voz dela a −17/−30 dB, equipe −38/−42 → `"takes_min": -34` no reel.json. Ela olha para
    quem pergunta, quase nunca para a câmera: capa com olho aberto e boca fechada aceita olhar de lado (máx. 2 folhas).
  - `hesita.py` dá falso positivo onde o texto do Whisper difere do alinhado; confirme com transcrição literal do trecho.
  - Quando o editor delega a revisão, pule a prévia: `final` direto + `qa_paineis --video <entrega>`; o que estiver
    errado sai por `trecho`. Encadeie mix → camera → final → folhas num comando por reel.
  - `checa_takes.py` também acusa corte no meio da fala (voz volta forte em até 0,35 s depois do corte): pegou o
    "marketplace" cortado e o "Depois" solto do 05; em conversa livre dá aviso nos cortes de propósito, confira cada um.
  - `checa_props.py` acusa etiqueta com palavras que ela não diz em ±8 s (o "mandioca, milho, tofu" do 05 veio de outro take).
  - **Fila de espera:** nunca `while pgrep -f "trecho"` — o próprio comando contém o texto e espera a si mesmo para sempre
    (três filas ficaram 4 h paradas, 14/10/2026). Encadeie em sequência num comando só, ou espere a trava `work/.trava_<etapa>` sumir.
  - `custo.py SESSAO.jsonl rNN` mede turnos/imagens/tokens por reel (revisão de eficiência a cada reel).
  - Encerrar o `reel.py` agora leva o render junto (o render roda em grupo próprio).

## Temas existentes

| Tema | Cliente | Notas |
|---|---|---|
| `priscilla` | Priscilla Daher | padrão do motor; Instrument Serif + destaque itálico terracota; capa "serif" |
| `andreia` | Andrea Francomano | creme, violeta-escuro e dourado; Cormorant Garamond (títulos, itálico dourado) + Montserrat (legenda); capa "serif" com bgFill cor |
| `joao-campos` | João Campos / Vai Lá e Faz Caxt | marinho/azul das thumbs, Montserrat Black em caixa alta, destaque por peso + azul claro, faixa azul royal; capa "faixa" |

## Revisão automática e fila (2ª auditoria, 14/10/2026)
- `reel.py PROJ rNN revisa` junta checa_takes (voz da equipe, corte no meio da palavra por energia + fim de palavra do Whisper),
  hesita, checa_props (inclui etiqueta que ela não diz) e olhar nas pontas dos cortes. O `final` roda a revisa antes. ~15 s.
  Por último, a nota criativa do `gancho-e-ritmo` (gancho 3 s, tempo morto, densidade, variação, ênfase, final; limiar no
  bloco `"qualidade"` do tema). No `final`, nota abaixo do limiar para o render; o editor libera com `GANCHO_OK=1`.
- **Variação e movimento (biblioteca compartilhada `scripts/movimento.py`, 20/10/2026).** `planeja` transforma ênfases
  candidatas em movimentos alternando punch/pulse/long com intervalo mínimo por tipo (presets `editorial`, `podcast`,
  `energetico`, ajustáveis no bloco `"movimento"` do tema); sai como `camera_moves` (reel) ou `impact_pulses`/`long_moves`
  (motores de podcast, mesmo formato que o render deles já lê). `confere` é o orçamento: no máximo N iguais seguidos por
  categoria (`"variacao": {"sfx": 3, "burn": 2, "movimento": 2, "painel": 1}`, 0 = sem limite), e roda no `revisa` como aviso.
  Andreia: sfx 0 (a tigela única foi aprovada), movimento 3, painel 3.
  Validado no estado antigo do 05: pegou marketplace, "Depois" solto, "seis por cen|to" e "mandioca, milho, tofu".
  O Whisper adianta o início das palavras: serve para conferir o FIM do corte, não o início.
  O aviso de olhar tem falso positivo (1:18 do 05 estava olhando a câmera): é lista para conferir numa tira, não verdade.
- `lote.py PROJ "r06 trecho 43 47.2" "r08 final" …` roda etapas uma por vez, segue se uma falhar, resume no fim.
  Nunca mais fila com `while pgrep -f`.
- Custo: o contexto por turno é o que mais pesa (844 mil/turno no fim da sessão). Um lote por sessão; o estado mora no disco
  (`status.py`, reel.json, segs.json), não na conversa.

## Pacote para o DaVinci (14/10/2026)
- `reel.py PROJ rNN davinci` → `07_davinci/<nome>/timeline.fcpxml` + mídia. Para reel com correção pedida: o editor
  importa (File > Import > Timeline), corrige o erro bobo e exporta por lá; nada de render final aqui.
- Tudo fragmentado: bruto em takes com alça, voz por take, cada painel/etiqueta/etapa/título/bloco de legenda/burn/SFX
  em arquivo e clipe próprios. `davinci painel_2` re-renderiza só esse elemento (Reel.tsx: props `layer` + `el`).
- Custo no 10 (41 s): câmera 121 s, fundo 38 s, legenda 45 s, 17 elementos ~3 min; 110 clipes, 2,6 GB.
- O DaVinci ignora o modo de mesclagem do FCPXML: burn vai com alfa. Não abrir o DaVinci para testar (pedido do editor).
- `"formato": "so_legenda"` no reel.json: ela em tela cheia com gancho, títulos e legenda; sem painéis, tela dividida
  e burns; SFX só nos textos (o original fica em sfx_com_paineis.json). Pedido da Priscilla para variar formato (06, 14/10/2026).
- `"extras": [{"arq": "extras/x.mov", "s": 0, "nome": "…"}]`: elemento feito fora do Remotion (ex.: cartão com logo de
  marca no gancho), entra numa faixa própria do pacote DaVinci junto com o PNG.

## Versão horizontal 16:9 e fonte de celular (Andreia, 19/10/2026)
- `"orient": "h"` no reel.json → composição `ReelH` (1920×1080): painel à esquerda (`layoutH.panelW`, desenho 1080×940 escalado),
  pessoa desliza para a direita; legenda sob ela na tela dividida; gancho/títulos com `layoutH.hookScale`. Mesma pasta de dados
  copiada para `rNNh/` (segs, edit_mfa, blocos, props.py iguais; câmera e mix próprios). Capa 16:9 = `CapaH` (título à esquerda, `shift` em x).
- Celular gravado deitado (arquivo 1080×1920 com imagem 16:9): `"rotate": "cclock"`; HEVC do iPhone é full range → `"full_range": true`.
- Câmera de mão / pessoa que se mexe: `scripts/rastreio.py FONTE rosto/vNN_track.json --rotate cclock` + `"track"` no reel.json →
  o recorte 9:16 segue o rosto quadro a quadro (sendcmd no crop); no 16:9 o props recebe `camX` como trilha [[t, x]].
- `"layout": {"camShift": …}` no reel.json ajusta o layout só daquele reel (rosto mais alto/baixo na fonte: camShift = 1300 − cy·1,78).
- **Fim de palavra comido**: segs gerados pelo fim do Whisper cortaram "espiritu|al", "proble|ma", "men|te" (+0,1–0,23 s).
  Feche cada trecho pela energia (voz abaixo de −45 dB + 0,03 s), não pelo `end` do Whisper; confira todas as emendas antes das props.
- **SSD lotou**: o bundle do Remotion copiava a pasta pública inteira (12 GB) a cada render/quadro-teste/capa. Agora `pub_enxuta()`
  monta `04_work/_pub/rNN` com hard links só do reel (etapa `pub`); use `PUBLIC_DIR=04_work/_pub/rNN` no `stills.mjs`.
  Nunca rode quadros-teste junto de um render: o `limpa_bundles` do render apaga o bundle deles.
- Painéis novos: `waves` (lê × emite frequência), `balance` (balança que pende), `root` (rótulo na superfície × raiz),
  `curve` (linha no tempo da fala: pico e volta), `pillars` (pilares + teto). Extras: ladder `labelSize`/`sw`, roles `centerY`/`titleOut`,
  timeline `x0`/`x1`, balance `arm`/`panSize`. Capa: `bgFill: "cor"` (topo liso em vez do quadro desfocado que mostrava rosto fantasma).
- `capa_pausas.py rNN camera.mov folha.jpg` = candidatos de capa nas pausas da fala; `so_capa` gera só a capa.
- Prévia/entrega no próprio DaVinci: `scripts/resolve_render.py "Projeto" "Pasta/Sub" SAIDA pacote…` importa cada timeline.fcpxml num
  projeto novo, renderiza MOV H.264+LPCM e remonta MP4 AAC 256k; devolve o projeto que estava aberto pela pasta dele.
- Render por etapa reusa UM bundle (`bundle_unico()`, em `04_work/_bundle/rNN`, apagado ao sair): no pacote DaVinci eram ~35 renders e cada um reempacotava (13 s). Medido: 61 quadros com alfa em 10 s a partir do bundle pronto.
- Camada `camera` do pacote DaVinci sai pelo ffmpeg (`camera_ffmpeg`: deslocamento da tela dividida por sendcmd + fade final), 92 s contra 5,5 min no Remotion; sem motion blur/grão na troca. `"camera_ffmpeg": false` no reel.json volta ao Remotion.
- **Correções do editor (Andreia, 19/10/2026):** (1) identidade roxo + dourado tem que aparecer: painel roxo profundo, texto creme,
  destaque dourado (tema `andreia`); (2) 16:9 em **terços**: painel nos 2/3 da esquerda (`layoutH.panelW` 1280), pessoa centralizada
  no terço da direita, legenda da tela dividida no rodapé do painel; (3) SFX: whoosh variado (nunca o mesmo em tudo) e temático
  (hoje `scripts/sfx_tema.py`, modo `variado`; kit em `CIBO Acervo/sfx/andreia/wav`), nível medido
  contra a voz — os do kit global ficaram 8–10 dB abaixo e sumiram; (4) câmera e zoom no DaVinci (`camera_davinci` + `camera_moves`).

## Movimentos de câmera no Fusion (Andreia, 19/10/2026)
- `"camera_fusion": true` no reel.json: o bruto vai só com o enquadramento base; cada punch/zoom e cada troca de tela dividida
  vira um clipe de ajuste com Transform do Fusion (Motion Blur, Quality 10, Shutter 360°), keyframes de Size/Center.
  O davinci.py grava `movimentos.json`; `scripts/resolve_fx.py PACOTE` exporta a timeline em .drt, injeta as faixas de ajuste
  (modelo `assets/davinci_faixa_ajuste.xml`) logo acima do bruto, reimporta e anima. Zooms embaixo, telas divididas em cima.
- Entregue também `timeline.drt` no pacote (o FCPXML não leva clipe de ajuste nem Fusion).
- API do Resolve: sempre com limite de tempo (`perl -e 'alarm N; exec …'`) e sem navegar pastas de projeto com o projeto
  aberto — o resolve_render.py travou o DaVinci do editor assim. Leia/escreva o .drt em UTF-8 e compare caminhos em NFC.
- Vertical sem zoom além do nativo: bruto 1080p na escala 1,0, topo encostado no painel, faixa "fundo desfocado" embaixo.
- Curvas (19/10/2026, "tá muito duro, faz ease in/out"): keyframe só nas poses (começa, para, pico) com alça plana; no meio de
  movimento, tangente monotônica; keyframe extra só se o S do ease erra > ~12 px (subdivisão recursiva, trecho < 1 s fica no ease).
  Alças do `SetKeyFrames` são RELATIVAS ao keyframe (absolutas estouram a curva). Conferir lendo de volta (`GetInput` por quadro).
  `resolve_fx.py --curvas PACOTE` refaz só as curvas na timeline aberta.
- Cores e nomes das camadas no DaVinci: `scripts/resolve_cores.py` (tabela em client-router/regras-transversais, regra do CIBO 19/10/2026); o resolve_fx.py aplica no fim.
- **Mix do editor para as outras timelines** (19/10/2026): `scripts/resolve_mix.py --sfx -3 --trilha 10 [--preset NOME] "TIMELINE"…`.
  A API não lê nem grava volume de clipe nem efeito de faixa: o volume vai pelo .drt (`EffectFiltersBA`, parâmetro 124, dB em
  double) e a timeline volta com o mesmo nome (Fusion e camadas preservados). O ducker da faixa TRILHA (Inspector > Audio, fonte VOZ)
  não vai no .drt: o editor salva um preset do Fairlight na timeline dele e o `--preset` aplica nas outras.
- **FPS da fonte (Andreia 19/10/2026, "Media Offline" no fim + áudio atrasado):** a timeline é 29,97; bruto de iPhone
  em 30 fps é forçado 1:1 pelo Resolve (escorrega 1 quadro/1000 e o último trecho passa do fim do arquivo → offline).
  Resolvido em 20/10/2026: o `davinci.py` lê o fps e, fora de 29,97, usa uma cópia por tempo em `01_sources/_2997/`
  (feita uma vez por fonte, 1 s de folga, sem timecode). Testado no r01: timeline idêntica à entregue, só com o bruto trocado.
  Timeline já montada: `scripts/resolve_refaz_audio.py` (ReplaceClip do bruto; trilha/SFX novos no lugar dos arquivos).
- **.drt não troca mídia:** o Resolve religa pelo `MediaRef` e ignora `MediaFilePath`; ele também junta arquivos de mesmo nome
  entre pacotes (o 03 abriu com a trilha.wav do 01). Troca de mídia: `MediaPoolItem.ReplaceClip` ou arquivo novo no mesmo caminho.
  Trecho sem media pool item: `DeleteClips` + `AppendToTimeline` (endFrame exclusivo) copiando Pan/Zoom/Rotation do vizinho.
- **Crítica da cliente (Andreia):** trilha dramática/espiritual (Heavy Heart, STEYL) a 22 dB abaixo da voz, sem ducker; SFX só nas
  trocas de painel e com um som só (tigela tibetana), nada nas frases/legendas.
- **Cache de render do Resolve** fica no disco interno (`~/Movies/CacheClip`) e lotou o Mac: aponte para o SSD.
- **Nunca encadeie ciclos de .drt (exportar→importar) na mesma timeline** (Andreia, 20/10/2026): cada ciclo soma 1 ao `GlobalIn`
  do `MediaIn1` das camadas de ajuste (Fusion) e o render falha com "The Fusion composition at 00:00:00:02 could not be processed".
  A API não grava esse valor. Confira com `FindTool('MediaIn1').GetInput('GlobalIn')` (tem que ser 0) e refaça a partir do
  backup numa importação só: `scripts/resolve_refaz_de_backup.py BACKUP.drt "NOME"`. Guarde o .drt antes de qualquer edição por XML.
- **Mesmo nome entre pacotes = mídia trocada** (Andreia, 20/10/2026): o Resolve junta `voz.wav`/`trilha.wav` de pacotes diferentes
  num item só; o 03 tocou trechos da voz do 01 ("o áudio parece de outro vídeo"). Resolvido no motor (sufixo `__rNN` em todo
  arquivo do pacote, ver "Padrão de edição do CIBO"); para pacotes antigos, depois de importar, audite se cada clipe vem
  de `07_davinci/<próprio pacote>/` — `resolve_refaz_de_backup.py` faz isso (`pacote_certo`) e também recoloca o clipe offline
  da câmera com `RotationAngle 90` (o bruto do iPhone sai deitado sem ele). QA de sincronia por trecho: correlação do áudio do
  render com o áudio da câmera no mesmo quadro (atraso ≈ 0 ms, corr > 0,9).
- **Corrigir texto de um elemento sem remontar o pacote:** `reel.py PROJ rNN davinci titulo_lower --so-el` (não chama o davinci.py,
  que regravaria voz/trilha/SFX) + `so_capa`; depois `ReplaceClip` no item para o Resolve reler o arquivo.
- **Tigela da Andrea** (bloco `sfx` do tema `andreia`, modo `so_trocas`): `tibetan-singing-bowl` grave em todos os vídeos (editor, 20/10/2026: a aguda `sfx-singing-bowl-hit-agudo-36st` soou "feliz demais"), 16 LUFS abaixo da voz, só nas trocas de painel; escolha o som pelo tom do vídeo, com prévia no trecho real (voz+trilha). A grave "não combina
  com a ideia de frequência" (editor, 20/10/2026); agudo alto incomoda. Prévias de tom: asetrate+atempo encadeado (atempo ≥ 0,5 por filtro).
