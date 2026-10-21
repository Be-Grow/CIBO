# podcast-reels — histórico de falhas e detalhes

Texto completo das lições resumidas no índice no fim deste arquivo. Abra a seção do item quando o
sintoma aparecer ou antes de mexer no código do motor.

## Known failure modes — check these first

These all shipped once. Do not rediscover them.

1. **Captions look crooked.** Words were centred by their own bounding box, so `o`,
   `aí`, `É` float. Position by font ascent on a shared baseline. Already fixed —
   don't "simplify" `build_caption` back.
2. **Whole frame goes magenta.** `blend=all_mode=screen` ran on YUV and screened the
   chroma planes. Both inputs need `format=gbrp` first.
3. **Caption band renders as an opaque black bar.** `libvpx-vp9` in some builds
   accepts `-pix_fmt yuva420p` and silently writes `yuv420p`. Verify with `ffprobe`,
   or use the colour + `alphaextract` matte pair this skill ships.
4. **Cuts sound abrupt.** Boundaries land mid-word. Snapping to the quietest frame
   within ±160 ms plus 35/55 ms fades fixes it; the first start and last end are
   deliberately never snapped.
5. **File too big to deliver.** ~30 MB to the conversation, ~20 MB to a connected
   folder. Decide the target *before* rendering: `crf 24` + `maxrate 2900k` puts a
   47 s 1080×1920 clip at ~18 MB. Full quality means rendering on the user's machine.
6. **A clip comes out too short.** Trimming removes 15–25 %. Pick the source window
   ~20 % longer than the target, then check `total` in `plan.json` before rendering.
7. **Encoding the same frames twice.** Composing to an intermediate and then
   re-encoding it to glue the 1 s cover on the front doubled the cost of every
   change (130 s instead of 54 s per clip). `render.final()` takes `cover=` and
   emits the deliverable in a single pass — never chain a second full encode.
8. **A static talking head reads as dead.** `ZOOM_AMT` (default 0.055) gives each
   kept segment its own slow push-in / pull-out, alternating direction per cut,
   eased in and out. The source is oversampled by the same amount before
   `zoompan` so the move costs no sharpness. Set `ZOOM_AMT=0` to disable.
9. **Synthesised SFX sound cheap.** Point `CLICK` at a real sample (`assets/click.wav`);
   it is trimmed to its transient and normalised to `CLICK_GAIN` (default 0.22).
10. **Background jobs die.** On the desktop bridge each shell call is its own process
   group — `nohup`/`setsid` do not survive. Every ffmpeg call must finish inside one
   call (~45 s), so chunk long renders.
11. **Ken-burns zoom looks shaky/vibrating.** `passA`'s pre-`zoompan` oversample (`OS`/
    `OSW`) was computed from the *native crop* size (608×1080) instead of the *final
    output* size (1080×1920) — zoompan was fed a ~654×1161 source and had to do most of
    the 1080×1920 upscale itself with its own weaker scaler, which shimmers as the crop
    shifts fractionally frame to frame. Fixed: base the oversample on `W,H` so zoompan
    only ever crops and lightly downscales from an already-adequate source.
12. **A variable-weight font (e.g. Montserrat) renders too thin for captions/cover.**
    `ImageFont.truetype` on a variable font loads its default named instance, which
    for most families is Regular, not Bold. `render_caps.py` and `cover.py` call
    `set_variation_by_name(os.environ.get('FONT_WEIGHT','Bold'))` after loading —
    check the font's actual instance names first (fontTools `fvar` table) if
    `'Bold'` doesn't exist for a given font.
13. **A click SFX steps on the opening word.** `clicks.py` fires on every caption flagged
    `any` (emphasis), including caption 0 — if the clip's first word is in `job.emph`
    (common: it's usually the hook stat), the click lands right on top of it and sounds
    like the voice glitching. Fixed: skip `idx==0` in `clicks.build`. Emphasis styling
    (bigger text) on the opening word is still fine — only the audio click is suppressed.
14. **A long, unfragmented SRT cue ships as one on-screen wall of text.**
    `plan.py`'s caption builder only *merges* short adjacent SRT cues up to the
    18-char limit — it never *split* a cue that was already longer than that on
    its own. Whisper (or whatever produced the SRT) doesn't reliably break every
    sentence into short cues; a fluent passage with few pauses can land as one
    40-60 character segment, rendered motionless on screen for its whole
    duration instead of the intended short auto-wrapped captions. Fixed: atoms
    longer than 18 chars are now split into word-packed chunks before merging,
    with time apportioned by character count across the original cue's span.
    Caught by `caption-quality-gate`'s `block_long` warning — run it on every
    delivered clip, not just a visual spot-check.
15. **`music`/`mix`/`filename` silently vanish from the render.** `plan.py`'s
    `build()` used to return a hand-picked dict of fields (`name`, `src`, `keeps`,
    `total`, `headline`, `cropx`, `cover_t`, `caps`) as `plan.json`, which
    `make_reels.py` then reads as the clip config for every later stage —
    anything in `job.clips.<k>` that wasn't in that hand-picked list (`music`,
    `mix`, `filename`, a per-clip `logo`, ...) got dropped with no error, no
    warning, nothing in the render log. Result: 8 clips rendered "successfully"
    with zero background music despite a correct `job.json`. Fixed: `build()`
    now merges every other key from the original clip dict into its result
    before returning. If a job field doesn't show up in the render, check
    `work/plan.json` first — if it's missing there, no downstream code will
    ever see it, no matter how correct the JSON you wrote is.



16. **A imagem desliza de lado numa emenda.** O reenquadramento por deteccao de
    rosto (`face_crop.py`, na skill `bombordo-boreste`) fechava um recorte por
    **trecho mantido** em vez de por **plano de camera**: dois keeps do mesmo
    plano recebiam medianas de rosto diferentes — o falante se mexeu — e o
    `cropx` pulava de 0.485 para 0.520, ou seja ~46 px numa janela de 608 sobre
    1920, exatamente em cima de uma emenda onde a camera nunca cortou. Na tela
    isso le como erro de montagem. Corrigido: as deteccoes sao agrupadas por
    plano de camera (a comparacao de cena continua valendo tambem na junção
    entre dois keeps, entao um corte de camera dentro do trecho descartado ainda
    e detectado) e cada plano recebe um unico recorte. **Regra: `cropx` so pode
    mudar onde a camera corta de verdade.** A unica excecao aceitavel e trocar de
    falante dentro de um plano aberto, e mesmo assim so quando a troca cai
    exatamente sobre uma emenda que ja muda quem fala.
17. **Uma legenda mostra frase que foi cortada fora.** O mapeamento de cue para
    trecho mantido usava `if e2-s2>0.12`: bastavam 0,13 s de um cue caírem dentro
    do keep para o texto **inteiro** dele ir para a tela, mesmo com o audio
    daquela frase inteiramente descartado. Corrigido: acima de 85% de
    sobreposicao o cue vai inteiro; abaixo disso so vao as palavras
    proporcionais ao trecho ouvido; e se nao sobra nada legivel, o atomo e
    descartado. Note que o snap de silencio move a fronteira em ate ±160 ms
    depois desse calculo, entao encostar um keep no inicio de um cue vizinho
    ainda e arriscado — deixe folga.
18. **`cropx_timeline` tambem existe aqui.** Este motor aceita
    `cropx_timeline: [[tempo_no_fonte, cropx], ...]` por clipe, portado da
    `bombordo-boreste`. Use sempre que a gravacao alternar close e plano aberto:
    com recorte fixo, o plano aberto vira um enquadramento da mesa. Gere a lista
    com o `face_crop.py` e confira que cada mudanca coincide com um corte de
    camera.

19. **O snap move a emenda para dentro da palavra.** O ponto mais quieto em ±160 ms
    pode cair no meio da cauda sibilante ("posições" → "postos") ou logo depois de um
    ataque curto de outra voz ("contrária, tá?"). Quando o envelope medido a mão
    mostra isso, liste o tempo (no fonte) em `nosnap: [t, ...]` no clipe e ele fica
    exatamente onde foi pedido. Confirme sempre retranscrevendo só o áudio cortado
    (large-v3) antes do render.
20. **Multicâmera:** o motor recebe um `src` só. Monte antes um master horizontal
    sincronizado (offset por correlação do envelope de áudio entre as câmeras), com
    a troca de câmera em silêncio entre keeps e cada plano já recortado em 608×1080
    no centro de um quadro 1920×1080 (`cropx: 0.5`). Ganho de voz por falante com
    `volume` + expressão: a expressão é **linear**, não dB (`if(lt(t,X),2.818,19.95)`
    = +9/+26 dB), e zere o tempo com `asetpts=PTS-STARTPTS` quando houver `-ss`.
21. **Voz de microfone distante elevada +20 dB traz chiado e sala.** Limpe antes do
    ganho com DeepFilterNet (`~/.venvs/dfn`, `deepFilter --atten-lim 24`): no pod da
    Lilian o SNR foi de 24 para 39 dB sem perder palavra (conferido retranscrevendo).
    Depois, EQ por falante medida em bandas relativas a 1–2 kHz (lapela abafada:
    -4 dB em 350 Hz, +5 dB em 3,5 kHz, shelf +4 dB em 7,5 kHz), compressão leve 2,5:1,
    de-esser e ganho fixo. Cor por câmera: meça neutro (camisa branca) e ângulo de pele
    (~123°) antes e depois; corrigir o neutro só nos realces já empurra a pele para o
    amarelo, então aplique metade e meça de novo. No zsh, escreva `${VAR}[x]` em
    filtergraph: `$VAR[x]` vira índice de array.

## Caption rhythm: never drop a block

`plan.py` runs a `ritmo()` pass over the finished captions. A one-word block with
0.15 s reaches 60 characters per second and reads as a flash, not a caption. The
pass tries, in order: stretch into the silence that follows (free), borrow time
from the next block and then the previous one (only costs if they are tight too),
and merge as a last resort (it fattens the line).

**Dropping a block is never an option.** The old code ended with
`out=[o for o in out if o['e']-o['s']>0.18]`, which silently deleted captions the
de-overlap step had squeezed to nothing — in real material that removed a whole
spoken sentence from the screen and left an orphan word behind, with nothing in
any report to show it had happened. Squeezed blocks now merge into the neighbour
instead.

Tunable with `MIN_BLOCK` (0.45 s), `MAX_CPS` (20) and `MAX_MERGE_CHARS` (30).

The pass cannot fix everything, and it should not pretend to. When the speaker
talks faster than the reading limit and no neighbour has slack, a block stays
above 32 CPS. That is a case for `caption-quality-gate` to flag and for a human
to decide — better a flagged fast caption than a mutilated sentence.

## Film burn on the way out

`render.py` screen-blends the film burn at the head of every clip. Setting
`BURN_OUT` to a number of seconds also blends a second copy so its flare lands at
the very end, which closes the clip instead of letting it just stop. The asset
peaks 0.53 s in, so `BURN_OUT=0.63` puts the peak on the last frame.

**It ships off (`BURN_OUT=0`) on purpose.** This skill is the engine behind
several clients; turning an outro burn on by default would change the delivered
look for clients who never asked for it. Each client skill opts in.

## Where to render

Caption bands, clicks, film burn and covers are cheap — do them anywhere. The h264
encodes are the slow part; on a 2-core sandbox a 45 s clip costs ~2 min end to end.
If the user's machine is reachable, run the encodes there instead. Keep an eye on
delivery limits: files over ~20 MB can't be written back to a connected folder, so
either render on the device or cap the bitrate (`crf 24`, `maxrate 2900k` lands a
47 s 1080×1920 clip at ~18 MB).

## Music

`render.py`'s `final()` mixes background music automatically when a clip sets
`"music"` (path to the track) and optionally `"mix"` (`music_db` default -26,
`music_offset` seconds into the track to start from, `duck_threshold`/`duck_ratio`
for the sidechain duck against dialogue, both with sane defaults). Use the
`talking-head-music` skill to shortlist and pick the track and offset per clip
first — don't default to 0:00 or the first file in a folder. Aggregator downloads
(Pixabay, Mixkit, etc.) are blocked from the sandbox; pick from an approved local
library instead.

**Ducking em fala contínua:** o default `duck_ratio` 6 / `duck_threshold` 0.08 mantém a
trilha abaixada o corte inteiro quando a fala não para, e o usuário ouve "a música demora
demais pra aparecer". Para talking head contínuo use `duck_ratio` 3, `duck_threshold` 0.1 e
`music_db` ~-18, e meça por subtração (final − `A_<clip>.mp4`): a música deve estar presente
desde o primeiro segundo e ~16–20 dB abaixo da voz. **Final do corte (regra fixa): como numa timeline.** O vídeo acaba seco — sem fade e sem
congelar — e o film burn fica numa trilha por cima, começando antes e ACABANDO DEPOIS do fim
do vídeo, sobre preto. Renderize com `BURN_OUT=0` e rode `scripts/burn_end.py ENTRADA SAIDA`:
o pico do burn (0,53 s do asset de 1,4 s) cai no último quadro do vídeo, o resto do efeito toca
sobre o preto, e a cauda do áudio sai em fade. Não use `BURN_OUT=0.63` (corta o burn no meio)
nem fade/escurecimento da imagem. (podLilian, 09/10/2026: "não é fade, é o burning e segue pra
um vídeo preto, como se eu tivesse a track do vídeo e a track do efeito por cima, acabando
mais na frente dela")

## Zoom suave e cortes de gaguejada (aprendido em fernanda-produto)

Padrão de movimento aprovado pelo usuário ("esse zoom ficou muito bom"). Vale propagar para as skills que usam este motor, respeitando a identidade de cada cliente:

- **Zoom de ênfase:** entra em 0,6 s (ease in-out senoidal, +12%) e volta em 4 s, a cada 10–18 s, no começo de frase, só com o falante em tela cheia. Entrada de 0,25 s foi reprovada como "rápida demais".
- **Centralização:** use crop dinâmico (`crop=w='W/z':h='H/z':x='(W-W/z)/2':y='(H-H/z)*0.38'`) e depois `scale` fixo. `scale(eval=frame)` + `crop=...:'(iw-W)/2'` usa o `iw` da configuração inicial e ancora o zoom no canto: o falante "escorrega" e o zoom parece ir para a esquerda.
- **Vários zooms:** combine os termos com `max()`. Somar termos que se sobrepõem dobra o zoom.
- **Corte de gaguejada:** corte de silêncio a silêncio medido no envelope do áudio em passos de 10 ms, não pelos tempos de palavra do Whisper, que deixaram meia sílaba ("q-que"). Esconda o jump cut com um zoom seco de +10% que volta em 3 s. Transcreva o trecho cortado de novo antes do render.
- **Transições:** coloque entrada e saída de B-roll, burn e SFX no centro de uma pausa real da fala. Um flash com whoosh sobre a palavra retomada soou como "corte cortando palavras". Ferramenta de referência: `fernanda-produto/scripts/find_pauses.py`.

## Corrigido em 10/2026 (corte da Paula, cliente Michele)

22. **Vídeo para em 2:01 e só o áudio segue.** O burn de abertura era estendido com
    `tpad=stop_duration=120` e o `blend ... shortest=1` cortava o vídeo em ~121 s. Todo clipe
    acima de 2 min saía truncado e o encode parecia travar no fim. Agora a extensão é
    `total+5`. Confira sempre `ffprobe -show_entries stream=codec_type,duration`: vídeo e
    áudio têm que bater.
23. **Encode que chega ao fim mas não fecha (0% de CPU).** A música entrava com
    `-stream_loop -1` sem `-t`, uma entrada infinita. Agora tem `-t total+offset+2`. O áudio
    do passA também entra por uma segunda leitura do arquivo, separada do `[0:v]`.
24. **Legenda invisível ao baixar a faixa.** `CY` era `1020-BAND_Y`, então com `BAND_Y=1150`
    a legenda ficava fora da faixa. Agora o padrão é `BAND_Y+210`, e `BAND_Y`/`CAP_CY` entram
    no fingerprint das legendas. Meça a matte (`signalstats` YMAX > 16) antes de entregar.
25. **MP4 truncado aceito pelo cache.** O final é gravado em `.part.mp4` e só renomeado ao
    terminar.
26. **Opções novas por clipe:** `cropx_interp: true` (o recorte acompanha a pessoa andando no
    palco, com interpolação entre os pontos de `cropx_timeline`) e `burn_at: [s, ...]` (burn
    de transição no meio do clipe, com o pico na emenda). Motion graphics (cards e lower
    third) entram numa passada separada sobre o MP4 pronto: dentro do encode final, com
    10 entradas, o agendador do ffmpeg travava.
27. **O recorte pula para o lugar errado em alguns trechos.** Com `cropx_interp`, os pontos
    de cada keep eram filtrados por `a<=t<=b`. O snap de silêncio move a borda alguns
    centésimos para dentro, os pontos ficavam de fora e o trecho caía no `cropx` do primeiro
    keep: 13 de 35 trechos com a pessoa saindo do quadro. Agora a tolerância é de 0,45 s,
    com o ponto mais próximo como reserva.
28. **O mix final saía sem cliques e sem tratamento de voz.** `[voice]` era consumido duas
    vezes (sidechain e amix). O ffmpeg ligava o segundo uso ao primeiro áudio livre (o áudio
    cru do passA), sem erro nenhum. Agora tem `asplit`. Novo `voice_af` por clipe: ganho fixo,
    EQ e limitador de pico na voz. Meça com `ebur128` depois do render: mudar o `voice_af`
    tem que mudar o LUFS.
29. **passA quadrático.** Cada keep decodificava o arquivo desde o início (`trim=start`).
    Agora usa `-ss` na entrada + `trim=duration`: 18 min viraram 6 min no mesmo clipe.

## Corrigido em 12/10/2026 (palestra do João Campos)

30. **Palavras curtas sumiam da legenda.** O mapeamento de cue para trecho mantido tinha
    `if e2-s2<=0.12: continue`: com SRT palavra por palavra, "eu", "a", "é" (e um "não", que
    inverte a frase) eram descartados inteiros. O piso agora é 0,02 s. A Content Hub já tinha
    essa correção; ela não tinha chegado aqui.
31. **Ênfase vazando de outro cliente.** `plan.py` somava ao `job.emph` uma lista fixa de um
    episódio de portos (mundo, risco, oportunidade, segurança...) e um `FIX` fixo do mesmo
    episódio. Toda palavra comum dessas ganhava destaque em jobs sem relação. Agora ênfase e
    correção vêm só do job.
32. **Capa de qualquer momento da gravação.** Chaves por clipe `cover_src` (arquivo
    horizontal), `cover_src_t` (tempo nele) e `cover_src_x` (centro do rosto em px). O recorte
    9:16 sai na escala nativa e sobe uma vez só. Sem essas chaves, a capa continua saindo de
    `cover_t` dentro do corte. Use quando o corte é todo em plano aberto e há um plano fechado
    melhor, de frente e de boca fechada, em outro ponto. Ache os planos fechados com YuNet
    (rosto com largura ≥ 140 px no 1920) e escolha numa folha de contato com o tempo real.
33. **Palestra de palco, câmera única ou corte ao vivo.** Rastreie o rosto (YuNet a cada 3
    quadros, continuidade de trilha, reinício em corte de câmera medido contra o quadro de 4
    atrás, para pegar dissolve curto) (`scripts/track_stage.py SRC.mov OUT.json`, com o OpenCV do venv da content-hub) e gere `cropx_timeline` com zona morta de 60 px e resposta 0,14 por quadro (110 px deixava o rosto encostado na borda quando ele anda e fora do centro no plano fechado) +
    `cropx_interp: true`. No plano aberto de 1080p, o recorte nativo de 608×1080 já deixa o
    palestrante de corpo inteiro ocupando a vertical: `ZOOM_AMT=0`, sem close.
34. **Clique de ênfase reprovado: "som de click bizarro… no meio das falas do jg"** (João
    Campos, 12/10/2026). O clique sintético/`click.wav` em toda palavra de ênfase, somado ao
    `voice_af` (que aplica +10 dB depois da mistura com os cliques), soou estranho e alto. O
    usuário aprovou o `camera_click.mp3` dele (4 batidas; mora em
    `~/CIBO/skills/fernanda-produto/assets/`, uso no João autorizado) **baixo** nas falas. Opções
    novas no `clicks.py`, desligadas por padrão: `CLICK_VARIANTS=1` separa as batidas do
    arquivo e alterna; `CLICK_MIN_GAP=2.5` evita rajada. Como o `voice_af` vem depois, ajuste
    `CLICK_GAIN` para o pico do clique ficar ~-20 dBFS no arquivo final, e meça. Nunca clique
    na primeira palavra nem colado em outro SFX (ex.: toque do cartão "Seguir").
35. **Tags Rec.709 sumiam no `burn_end.py`.** O blend em gbrp entrega quadros com
    primárias/transferência "unknown" e as flags de linha de comando não sobrescrevem. Com
    `BURN_END_BT709=1` ele grava via `h264_metadata` no bitstream; `BURN_END_LIMIT=0.84` põe
    um limitador no fim (true peak abaixo de -1 dBTP). Os dois desligados por padrão. Para
    corrigir um arquivo já entregue sem re-encode: `ffmpeg -i in.mp4 -c copy -bsf:v
    h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1 out.mp4`.

## Corrigido em 12/10/2026 (LPA e Você, cortes da Carolina Fernandes)

34. **Capa nova, MP4 com a capa velha.** O estágio `final` não tinha `cover_src`,
    `cover_src_t` e `cover_src_x` no fingerprint: trocar o frame da capa refazia o PNG, mas o
    primeiro quadro do MP4 continuava com a capa antiga, vinda do cache. Agora as três chaves
    entram no fingerprint do `final`.
35. **Tempo de palavra do Whisper atrasado ~0,3 s em fonte do YouTube.** A legenda do corte
    começou com "ter?" (resto da frase cortada) e perdeu "o". Depois de fechar os `keeps`,
    transcreva **o áudio já cortado** (large-v3, `--word-timestamps`, `--initial-prompt` com
    nomes e termos do episódio para sair pontuado), descarte palavra com `probability < 0.2`
    nos primeiros 0,6 s (alucinação "aquilo, né?") e devolva os tempos ao master pelos keeps
    para gerar o SRT do job. Emendas pelo envelope (`find_pauses.py env`), nunca pelo tempo
    de palavra.
36. **Download do YouTube sem perda.** `yt-dlp --download-sections` com
    `--force-keyframes-at-cuts` **recodifica** o trecho (q=29): não use. Sem a flag, o trecho
    sai em cópia de stream. Se o áudio `251` der 403, use o HLS `234` (`-f "270+234/270+140"`).
    Baixe só a minutagem pedida com folga de ~10 s de cada lado e transcreva só ela.
37. **Grafismo da fonte cortado pelo 9:16** (card de definição queimado no plano aberto).
    Não deixe o texto cortado pela metade: no `A_<clip>.mp4` (escala nativa, antes do `final`),
    componha um painel desfocado com bordas em degradê sobre a área do card cortado e
    reposicione o card inteiro, recortado da fonte com máscara (círculo + barra + caixa,
    medidos por diferença entre um quadro com e outro sem o card). O card entra com fade só
    depois que a animação original formou a caixa. Depois apague `I_<clip>.mp4` e rode o
    `make_reels` de novo: o `cut` fica em cache e só a intro e o final são refeitos.
38. **Troca de câmera 1 quadro atrasada (plano de 1 quadro).** O passA decodifica com `-ss a` +
    `setpts=PTS-STARTPTS`: t=0 é o primeiro quadro real depois de `a`, não `a`. Com `a` fora da
    grade de quadros (16,41 s), a troca do `cropx_timeline` caía um quadro depois do corte de
    câmera: um quadro da câmera nova com o recorte antigo (abajur, almofada). O `crop_expr` agora
    desconta esse deslocamento. Ponha cada ponto da timeline ~15 ms antes do primeiro quadro da
    câmera nova (meça com diferença de quadros a partir de um tempo na grade, ex.: 16,0) e, depois
    do render, procure planos de 1–9 quadros no MP4 fora do burn de entrada/saída.
39. **Clique:** o padrão do `clicks.py` agora são os dois sons do usuário (`click lens.wav` e
    `camera_click.mp3`, este dividido nas 4 batidas), alternados. O sintetizado só entra se os
    arquivos sumirem. Ao trocar o som, apague `clicks_<clip>.wav` e o MP4: o cache do clique
    depende só do tempo das legendas.
40. **Capa `cover_style: "lpa"`** (LPA e Você): frame limpo, sem degradê, barra ou logo;
    manchete em Montserrat Bold centralizada na vertical, alinhada à esquerda (margem 90 px),
    sombra deslocada 12 px para baixo com blur 9.
41. **`burn_end.py` recodifica o vídeo inteiro** só para pôr 1,4 s no fim: é a etapa mais lenta
    depois do passA. O preset agora é `BURN_END_PRESET` (padrão `fast`). Resolvido no item 46:
    `BURN_END_INLINE=1` faz o mesmo fim dentro do `final()`.
42. **Ganho de voz é por episódio, não por cliente.** O `voice_af` com +6 dB que deixou o
    episódio da Carolina em −14 LUFS deixou o da Maria Rita (mesmo podcast) em −19,5. Meça o
    LUFS do trecho mantido de cada fonte antes (`ebur128`) e calcule o ganho. Se já renderizou,
    corrija só o áudio com `-c:v copy` (sem recodificar o vídeo).
43. **Logo de transmissão queimado no bruto (Marandu TV, João Campos 12/10/2026).** Não apague
    com `delogo`/`removelogo`: o usuário reprovou o borrão ("ao invés de aplicar um blur
    estranho"). Reenquadre: `crop_h` por clipe (opt-in) faz um recorte mais baixo ancorado no
    topo (`crop_h*9/16` de largura) que deixa o rodapé de fora, no vídeo e na capa. 992 tira
    um logo que começa em y=998 (+8,9% de escala, dentro do aceitável). Só travar o `cropx`
    longe do logo não serve quando a pessoa anda até o canto do logo: o rosto encosta na
    borda. Ao trocar a largura, converta a timeline mantendo o centro:
    `novo = (antigo*(1920-608)+304-cw/2)/(1920-cw)`. Ache a caixa do logo pelo desvio
    temporal baixo em ~60 quadros espalhados (é a única coisa que não muda).
44. **Capa: varra a gravação, não pegue o primeiro quadro bom** ("as capas dos cortes não
    ficaram boas", João Campos). Rosto neutro, mão em posição estranha ou plano aberto
    reprovam. YuNet a 2 qps na gravação inteira (descarte telas estáticas: mesma caixa
    repetida), filtre por rosto grande, nítido e de frente, monte folhas de contato e depois
    amostre 5 qps ±1,6 s em volta das melhores. **O que aprova é close de rosto, de frente,
    olhando para a câmera** ("de rosto tá ótimo"). Gesto grande (braço erguido, apontar,
    sorriso de pé em plano aberto) foi chamado de "horrível": rosto pequeno, mão cortada na
    borda ou braço disputando com o rosto. Confira a borda: dedo entrando no quadro reprova.
    Scripts em `scripts/cover_scan.py`.
45. **Acabamento em cima do MP4 entregue não é idempotente.** Cartão/título (`overlay_card.sh`
    ou `post.sh` do projeto), `burn_end.py` e troca de áudio sobrescrevem o arquivo final. Numa
    fila "render → acabamento em todos", se um render falhar ou ficar em cache, o acabamento
    roda de novo num arquivo que já tinha cartão e burn: dois cartões, dois burns. Rode o
    acabamento só nos clipes cujo `final` foi refeito (linha `final:<clip> built` no log).
    Um `final` do ffmpeg ficou parado com 0% de CPU e o `.part.mp4` quase pronto (palestra
    do João); matar e rodar o clipe sozinho resolveu em 33 s. Se a fila parar sem progresso,
    olhe `ps` (estado S e tempo de CPU parado) antes de esperar mais.
46. **Render rápido: uma codificação só, na GPU** ("demora muito", 12/10/2026). O fluxo antigo
    codificava o vídeo três vezes (final → cartão/título → `burn_end.py`) e redimensionava cada
    quadro no PIL mesmo sem zoom: ~3–4 min por corte. Tudo opt-in (sem as chaves, a saída é
    idêntica quadro a quadro):
    - `VENC=auto` (recomendado): escolhe pelo perfil de hardware da `video-render-optimizer`
      (`hw_profile.py`), que revalida sozinho; se o hardware falhar no `final()`, refaz em x264.
      `VENC=videotoolbox|nvenc|qsv|amf` força um encoder (alvo `VT_MBPS`=8, teto
      `VT_MAX_MBPS`=10; intermediários a 40 Mb/s). No M4: 4,2× mais rápido, SSIM 0,9941 × 0,9952, aprovado pela
      `video-render-optimizer` e na comparação visual de pele, barba e letra.
    - `PASSA_DIRECT=1` (só com `ZOOM_AMT=0`): o ffmpeg já entrega o quadro em 1080×1920 e o
      Python só repassa os bytes.
    - `overlays` por clipe: `[{"file": card.mov, "t": 8.0, "sfx": {"file","at","trim","gain"}}]`,
      com tempo no arquivo entregue (capa incluída). Substitui `overlay_card.sh`/`post.sh`.
    - `BURN_END_INLINE=1` (+ `BURN_END_LIMIT`, `BURN_END_BT709`): o fim do `burn_end.py` dentro
      do `final()`.
    Corte 02 da palestra do João: 53 s do zero (antes ~3,5 min), mesma duração, SSIM 0,99 contra
    a entrega antiga, AUTOMATED_PASS. Lote completo (7 cortes, 13 entradas no `final()` com título, cartão,
    SFX e burn): 6 min 40 s do zero, os 7 com AUTOMATED_PASS e duração idêntica à entrega; o
    travamento do agendador com muitas entradas (item 26) não voltou. Script de projeto pronto: `joãoCortes/04_work/render_all.sh`.
    Rode com `taskpolicy -B -t 0 -l 0 -p $$` no topo do script: em background o macOS joga o
    ffmpeg nos núcleos de eficiência.

## Falhas conhecidas (índice)

Texto completo em `references/historico-falhas.md`: abra o item quando o sintoma aparecer.

- 1. Captions look crooked
- 2. Whole frame goes magenta
- 3. Caption band renders as an opaque black bar
- 4. Cuts sound abrupt
- 5. File too big to deliver
- 6. A clip comes out too short
- 7. Encoding the same frames twice
- 8. A static talking head reads as dead
- 9. Synthesised SFX sound cheap
- 10. Background jobs die
- 11. Ken-burns zoom looks shaky/vibrating
- 12. A variable-weight font (e.g. Montserrat) renders too thin for captions/cover
- 13. A click SFX steps on the opening word
- 14. A long, unfragmented SRT cue ships as one on-screen wall of text
- 15. `music`/`mix`/`filename` silently vanish from the render
- 16. A imagem desliza de lado numa emenda
- 17. Uma legenda mostra frase que foi cortada fora
- 18. `cropx_timeline` tambem existe aqui
- 19. O snap move a emenda para dentro da palavra
- 20. Multicâmera:
- 21. Voz de microfone distante elevada +20 dB traz chiado e sala
- 22. Vídeo para em 2:01 e só o áudio segue
- 23. Encode que chega ao fim mas não fecha (0% de CPU)
- 24. Legenda invisível ao baixar a faixa
- 25. MP4 truncado aceito pelo cache
- 26. Opções novas por clipe:
- 27. O recorte pula para o lugar errado em alguns trechos
- 28. O mix final saía sem cliques e sem tratamento de voz
- 29. passA quadrático
- 30. Palavras curtas sumiam da legenda
- 31. Ênfase vazando de outro cliente
- 32. Capa de qualquer momento da gravação
- 33. Palestra de palco, câmera única ou corte ao vivo
- 34. Clique de ênfase reprovado: "som de click bizarro… no meio das falas do jg"
- 35. Tags Rec.709 sumiam no `burn_end.py`
- 34. Capa nova, MP4 com a capa velha
- 35. Tempo de palavra do Whisper atrasado ~0,3 s em fonte do YouTube
- 36. Download do YouTube sem perda
- 37. Grafismo da fonte cortado pelo 9:16
- 38. Troca de câmera 1 quadro atrasada (plano de 1 quadro)
- 39. Clique:
- 40. Capa `cover_style: "lpa"`
- 41. `burn_end.py` recodifica o vídeo inteiro
- 42. Ganho de voz é por episódio, não por cliente
- 43. Logo de transmissão queimado no bruto (Marandu TV, João Campos 12/10/2026)
- 44. Capa: varra a gravação, não pegue o primeiro quadro bom
- 45. Acabamento em cima do MP4 entregue não é idempotente
- 46. Render rápido: uma codificação só, na GPU
