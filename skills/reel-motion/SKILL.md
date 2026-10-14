---
name: reel-motion
description: Motor genérico de reels verticais 9:16 com tela dividida (painel de motion em cima, pessoa embaixo, tela cheia no gancho e nas viradas), legenda palavra a palavra, burn nas trocas de painel e capa — configurado por tema de cliente (cores, fontes, caixa alta, estilo do destaque, burn, layout da capa) e montado com uma biblioteca de componentes Remotion reutilizáveis. Use para qualquer reel "com motion" no estilo Priscilla Daher, de qualquer cliente (Priscilla, João Campos/Vai Lá e Faz Caxt e novos), em vez de copiar o motor para o projeto.
---

# reel-motion — motor genérico de reel com motion

Nasceu do motor aprovado da Priscilla Daher (13/10/2026). O editor pediu: **um motor generalista que
aceita configurações, não um motor por cliente**, e **uma biblioteca de componentes reutilizáveis
(princípio do React), não animação feita do zero a cada reel**.

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
`final`; ajustes com `trecho A B` e `entrega`. Igual ao fluxo da `priscilla-daher` (ver lá os detalhes de
takes, MFA e capa).

## Biblioteca de componentes (regra)

- Painel novo = **composição das peças de `primitives.tsx`**. Antes de escrever JSX, veja se um painel
  de `PANELS` serve com outros textos/tempos; depois, se dá para montar com as peças existentes.
  Só crie peça nova quando nenhuma serve — e ela entra em `primitives.tsx`, genérica, usando só o
  tema (`C`, `fTitle`, `fAcc`, `fLab`), para o próximo cliente herdar.
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
| `joao-campos` | João Campos / Vai Lá e Faz Caxt | marinho/azul das thumbs, Montserrat Black em caixa alta, destaque por peso + azul claro, faixa azul royal; capa "faixa" |

## Revisão automática e fila (2ª auditoria, 14/10/2026)
- `reel.py PROJ rNN revisa` junta checa_takes (voz da equipe, corte no meio da palavra por energia + fim de palavra do Whisper),
  hesita, checa_props (inclui etiqueta que ela não diz) e olhar nas pontas dos cortes. O `final` roda a revisa antes. ~15 s.
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
