---
name: bombordo-boreste
description: Crie cortes verticais 9:16 para Reels, TikTok e Shorts do podcast Bombordo e Boreste, usando o estilo, os assets e o fluxo de edição próprios deste cliente — legenda estática ou animada (kinetic typography palavra por palavra), capa com o convidado sorrindo e legenda abaixo do queixo. Use somente em trabalhos do Bombordo e Boreste.
---

# Bombordo e Boreste → Reels

**Local setup:** dependencies (Pillow, numpy, OpenCV headless) live in the bundled venv at
`~/.claude/skills/bombordo-boreste/.venv`. Run scripts with
`~/.claude/skills/bombordo-boreste/.venv/bin/python3
~/.claude/skills/bombordo-boreste/scripts/make_reels.py`, or activate that venv first,
instead of the bare `python3` shown below. Requires `ffmpeg` and `ffprobe` on PATH.


Builds finished vertical cuts from a master video + SRT. Everything is driven by one
`job.json`; the scripts do transcription-free caption timing (reused from the SRT),
silence-snapped trimming, caption rendering, audio sweetening and the cover.


## Regras do cliente (correções do usuário e do Daniel)

- **Tudo no DaVinci, nunca ffmpeg na entrega (20/10/2026, EP 07: "que diacho de ffmpeg, na demanda da Andreia eu fiz
  tudo lá no DaVinci").** Episódio completo, cortes e versões longas são montados e renderizados no Resolve com o fluxo
  do `reel-motion` (pacote `davinci`, `resolve_render.py`, `resolve_fx.py` para punch-in/zoom no Fusion, `resolve_cores.py`,
  `resolve_mix.py`, `qa_resolve.py`/`qa_render.py`), em projeto novo e organizado (regras-transversais → "Projeto
  organizado"). O `make_reels.py`/`render.py` daqui queimam tudo no ffmpeg: use-os só para gerar camadas (legenda com
  alfa, capa) e prévias de conferência, nunca para o MP4 final. ffmpeg fica para análise, extração de áudio e prévia.

- **Punchline no início.** O Daniel (host) pediu: "seria legal já colocar a punch line no
  início do corte". O corte abre com a frase mais forte (gancho nos 3 primeiros segundos),
  mesmo que ela venha do meio do trecho. Pode ser um *cold open* de 1 frase antes do
  contexto, desde que a frase volte inteira e sem corte seco no meio de palavra.
- **5 cortes por episódio, sem repetir fala.** Todo episódio fecha com 5 cortes no total:
  conte o que já existe e complete. Nenhuma fala pode aparecer em dois cortes. Antes de
  escolher, levante as janelas já usadas (`master_in` + cada `keeps` de cada `job.json`,
  mais os cortes que vieram prontos do Drive) e descarte candidatos que se sobreponham.
- **Pastas dos episódios (desde 09/10/2026).** Uma pasta por episódio com o nome do Drive e a numeração
  do YouTube: `content/bombordo/EP NN - Convidado/`, na estrutura da skill `video-project-structure`:
  bruto em `01_sources/masters/`, projeto de edição (job.json, pipeline) em `04_work/`, entregas em
  `06_deliverables/` (episódio, cortes, capas; `_versoes_antigas/`). Pastas antigas `epN`, `CORTES/` e
  `brutos/` não existem mais; o mapa está em `_migracao_2026-10-09.json`. Identifique o episódio pelos
  convidados ou pela duração, nunca só pelo número (arquivos antigos usam epN = EP N-1).
- **Grafia:** "Bombordo e Boreste", com "Bombordo" sempre junto. O Whisper escreve
  "Bom Bordo" ou parte a palavra entre duas cues: as regras de `fix` do `job.json` cobrem
  os dois casos. Copie-as para cada episódio novo e confira nas transcrições entregues.
- **Sempre partir do bruto/master do episódio** em `EP NN - Convidado/01_sources/masters/` (ou o master
  em `04_work/sources/master/`), nunca de um MP4 solto em `~/Movies` (pode ser versão substituída, com a grafia errada).
- **Capa:** a pessoa de frente, olhos abertos e sorriso real (`cover_pick.py --master`).
  A convidada precisa ficar bonita: pode vir de qualquer momento do episódio (`cover_from`).
- **Música a −27 dB** (`mix.music_db`), não −21: "a música tá um pouco muito alta".
- **Entrega:** os cortes vão para `EP NN - Convidado/06_deliverables/cortes/`, sem níveis numerados. Arquivos
  `NN - HEADLINE.mp4`, com acentos, numerados pela ordem em que a fala aparece no
  episódio (ordenar por `master_in`), e a capa `CAPA - NN - HEADLINE.png` (prefixo, para as
  capas ficarem agrupadas no Finder). Grave o nome em `filename` no `job.json`, senão o
  próximo render volta ao nome antigo. Troque `"` por `'` no nome do arquivo.
- **Transcrição sempre com tempo** (`[hh:mm:ss - hh:mm:ss] texto`, blocos de ~20 s, mais
  o SRT). Texto corrido sem tempo o usuário considera inútil. Entregue a de todos os
  episódios do lote.

## Reenquadramento: um recorte por plano de camera

`face_crop.py` decide **um recorte por plano de camera**, nunca por trecho
mantido. Fechar o recorte a cada `keep` foi um bug real com defeito visivel: dois
keeps do mesmo plano recebem medianas de rosto diferentes porque o falante se
mexeu, o `cropx` pula dezenas de pixels numa emenda onde a camera nunca cortou, e
o video entregue desliza de lado. A deteccao de cena tambem roda na junção entre
dois keeps, entao um corte de camera que caiu dentro do trecho descartado
continua sendo detectado.

**Regra: `cropx` so muda onde a camera corta.** A unica excecao e trocar de
falante dentro de um plano aberto, e so quando a troca cai exatamente sobre uma
emenda que ja muda quem fala. Antes de renderizar, confira que toda mudanca de
`cropx_timeline` coincide com um corte de camera.

## O passe de ritmo das legendas

Este motor e o mesmo da `podcast-reels`, e correcoes precisam ser propagadas nos
dois sentidos. O passe `ritmo()` (blocos que piscam sao esticados, pedem tempo
emprestado ao vizinho ou fundem, e **nunca** sao descartados) veio de la; o
`cropx_timeline` foi daqui para la. O codigo antigo terminava com um
`[o for o in out if o['e']-o['s']>0.18]` que apagava em silencio legendas
espremidas pelo de-overlap, sumindo com falas inteiras sem deixar rastro em
relatorio nenhum.

## Legenda so mostra o que e ouvido

O mapeamento de cue para trecho mantido exige sobreposicao **relativa**, nao um
limiar absoluto: acima de 85% do cue o texto vai inteiro; abaixo disso vao so as
palavras proporcionais ao trecho ouvido; se nao sobra nada, o atomo e descartado.
Com o limiar absoluto antigo, 0,13 s de um cue bastavam para jogar a frase
inteira na tela com o audio dela cortado fora.


## Workflow

Before editing, read and update `references/client-content-bible.md` and `references/asset-source-catalog.md`. Use `video-project-structure` to audit the fixed project layout and prevent raw/stock media from entering Drive asset packages.

1. **Read the SRT, not the video.** Collapse it into a readable transcript first:
   group cues into ~15 s blocks and print `[start - end] text`. Pick the clips from
   that. Never scrub the video looking for moments.
2. **Identify host vs guest** from conversational flow (who introduces, who asks,
   who answers) and say so before proposing cuts.
3. **Pick moments** with a hook in the first 3 s, one clear idea, and a closing
   punchline or a cliffhanger question. Target 42–55 s of *kept* audio — the trim
   removes 15–25 % of the raw window, so choose a window ~20 % longer.
4. **Write `job.json`** (see `assets/job.example.json`) with, per clip: `src`,
   `master_in` (its IN point in the master, seconds — used to map SRT cues),
   `headline`, fallback `cropx`, `cover_t`, and `keeps` (list of `[start,end]` in
   *clip-local* seconds). Before rendering, generate and visually review a
   shot-aware `cropx_timeline` with `face_crop.py`; never assume one crop fits every
   camera in a clip.
5. **Polish captions against the real audio (mandatory after any keeps change):**
   ```bash
   JOB=job.json python3 scripts/asr_polish.py --beats
   ```
   Re-transcribes every kept segment with large-v3 AND turbo (no domain prompt —
   a "ports" prompt turned "no ponto" into "no porto"), fixes punctuation/casing,
   drops edge phantoms / adds audible edge words only when both models agree,
   never touches acronyms or `emph` terms (both models hear "CCO" as "social"),
   and re-places clicks/zooms on emphasised captions (they are output-time and go
   stale when keeps move). Everything else lands in `asr_polish_report.json` —
   read it; one-model disagreements are decided by an isolated no-prompt check.
   `make_reels.py` also warns when a `cropx_timeline` change sits just after a
   keep start (the first frames would keep the previous shot's crop — ep4 showed
   an empty shelf for 0.5 s).
   **Caption height:** captions must never cover a face. After the cut exists, run
   `python3 scripts/safe_zone.py <work>/A_<clip>.mp4` and put the returned centre in
   `job.clips.<clip>.cap_cy` (band = cap_cy±210; ep4 landed at 1218–1380, the old
   fixed 1020 sat on chins and beards). Two-line captions use tight leading
   (`LINE_PITCH` in render_caps.py) — the old ascent+descent stacking read as two captions.
   **Cover frame:** run `python3 scripts/cover_pick.py [clip]` and choose `cover_t`
   from `<work>/cover_cands_<clip>.jpg` (frontal, eyes open, composed mouth). A round
   second picked blind landed on profiles, blinks and mid-word mouths.
   The cover must make the guest look good. If every frame inside the cut is a
   profile (ep4: Juliana), take the still from anywhere in the episode — usually the
   guest's introduction, filmed frontal and smiling — with
   `job.clips.<clip>.cover_from = {"src": master, "t": s, "x0": crop x}`; it gets a
   subtle edge-preserving skin/light retouch (`cover_retouch_amount`, default 0.35).
   Find those moments with `python3 scripts/cover_pick.py --master <master.mp4>`
   (genuine smiles: strict smile + teeth + eyes open, whole episode). Approved by the
   client: a real smile with eyes open, or a soft smile in a slight 3/4 turn. Rejected:
   mid-word mouths, raised eyebrows, a serious/sad face, a flat straight-on close-up.
6. **Run it:**
   ```bash
   JOB=job.json python3 scripts/make_reels.py            # all clips
   JOB=job.json python3 scripts/make_reels.py corte01    # one clip
   ```

## Animated captions (kinetic typography) — `scripts/kinetic/`

Approved by the client on ep4 (EP 3 on YouTube). Replaces the static caption band with a
frame-by-frame animated layer; the rest of the pipeline (cut, intro, burn, cover, music) is
unchanged. Python (Pillow + NumPy + OpenCV, 2x supersampling), not Remotion/ASS/drawtext:
real directional blur, easing and springs per frame, no new toolchain. See
`scripts/kinetic/README.md` for every parameter.

```bash
K=scripts/kinetic/cli.py
JOB=job.json python3 $K align                     # word timing: large-v3 word timestamps on the cut's
                                                  #   voice, aligned to the reviewed captions, onset-snapped
JOB=job.json python3 $K segment                   # 1-4 word blocks + destaques (editable JSON)
JOB=job.json python3 $K preview corte02 --dur 8   # preview + contact sheet: SHOW IT AND WAIT FOR OK
JOB=job.json python3 $K render-all                # H.264 CRF 18 into job.kinetic_outdir, original
                                                  #   deliverable's audio copied untouched (-c:a copy)
```

What the client approved, and what failed before it did:
- Word-by-word entry ~1.5 frame before the sound (slide + directional blur + fade + 0.9→1 scale);
  the word being spoken turns brand blue `#4F95FF`, spoken words return to white.
- Destaques chosen **by meaning** (`kinetic.yaml` → `videos.<clip>.highlights`, in speech order):
  the central point, numbers, emotion, strong verbs. The automatic scorer picked "falou",
  "ainda", "mas enfim" — keep it only as a draft. ~1 destaque every 3–4 blocks.
- A destaque pops in as **one unit** and scales as a **group** (word-by-word left "7" hanging
  at the line's edge; per-word scaling collided into "7 desetembro"). A leading article or
  preposition rides small above it, **tight** (`highlight_lead_gap` 0.22 × small size — the
  big line's full leading read as two captions).
- The previous block must be gone before the next appears in the same spot: exit ends at the
  next entry and shortens (≥70 ms) when speech is continuous. Overlapping exit/entry read as
  garbled text ("a m*falou*supervisora").
- A block shorter than ~0.35 s on screen is a flash: fold it into the next block.
- On screen only "?" and "!" (punctuation still splits blocks); whisper's mid-sentence capitals
  are lowered, but names keep theirs: `PROPER` in segment.py + `proper:` in kinetic.yaml, any word
  capitalised mid-sentence 2+ times and never lower-case in the clip, and adjacent capitals
  ("Wilson Sons" had gone out as "wilson sons" — add the guest's company/port names to `proper`).
- Band centred on the clip's `cap_cy` (below the chin), width 760 px (clear of the Reels buttons).
  **Every** block must fit 760 px, destaques included: a long destaque stays on one line down to
  1.5x, then stacks in two big lines ("presidente / mais novo"), never a lopsided "24 / funcionários";
  the entry zoom is capped at the frame width. A font-size floor once let "presidente mais novo"
  and "supervisora de operações" run edge to edge, cut off under the buttons — after render-all,
  check the widest destaques of every clip, not only the 8 s preview.
- Punch-in on each destaque (`punch_in`, engine `scripts/punch.py`), approved after the client
  said the old one "looked like a spring" (zoompan + a sin pulse: straight up and back down,
  crop rounded to whole pixels). Now Premiere keyframes: Easy Ease `cubic-bezier(0.33,0,0.67,1)`
  (y outside [0,1] is refused — no overshoot), scale interpolated in log space, 0.40 s ramps,
  100% → 105%, same curve back. Holds while the destaque is on screen, at least 0.4 s; a
  return must rest 0.3 s at 100% before the next rise, else it holds through (dip-and-back
  also reads as a bounce). Motion blur only on the zoom: 360° shutter, each moving frame =
  mean of 16 subframes over the whole frame interval, centred; frames at rest are untouched.
  Works on yuv420p planes (no colour drift). The job's `long_moves` run on the same curve.
  The cover is grabbed from the frame saved BEFORE the zoom (`A_<clip>_clean_cover.mkv`).
  Preview one zoom with `preview <clip> --start <t> --dur 4`, then `render-all --out <new dir>`.

## Chamada do episódio (`scripts/chamada.py`)

O pilar "Episódio da semana" da estratégia pede um corte de chamada: frase mais forte do convidado
nos 3 primeiros segundos, **nome do convidado na tela**, corte no auge e "o resto está no episódio".
Depois do `render` da legenda animada do corte escolhido:

```bash
python3 scripts/chamada.py "<corte>.mp4" --nome "ARTHUR NETO" --sub "Sócio da Alphamar Agência Marítima" \
    --logo <logo_podcast.png> --lt 6.6 10.6 --y 300
```

`--lt` = entrada/saída do nome (logo depois da frase de impacto); `--y` = topo do nome, fora da faixa
da legenda (`cap_cy` ± 210) e do rosto. Guarde antes uma cópia limpa do corte: o script reescreve o
arquivo (uma passada de vídeo, card final de 2,5 s com "Episódio completo: Bombordo e Boreste no YouTube").
Aprovado no EP 04 (Ayrton) e usado no EP 05 (Arthur).

## Histórias do Porto → XML para o DaVinci (EP 06, 18/10/2026)

O editor prefere fazer o render final no DaVinci: entregue um XML (FCP7) com **cada camada numa
trilha** em vez do MP4 queimado. Scripts prontos em
`scripts/historias_xml/` (cópia do EP 06; README explica a ordem): `componentes.py <historia>` (painéis ProRes
1080x660, legenda ProRes 4444 com alfa, sombra, fade, trilha mixada, capa, `xml_cfg.json`) e
`xml_resolve.py <historia>` (V1 Daniel, V2 painéis, V3 sombra, V4 legenda, V5 burn Screen, V6 fade, V7 capa;
A1 voz, A2/A3 trilha L/R, A4 cliques, A5 whooshes, A6 SFX/bipe). Copie para a história nova e troque `STORIES`.

O que o Resolve 20 faz com XML do FCP7 (medido importando e renderizando pela API, não suposto):
- **Encaixa o clipe na timeline antes do Movimento** ("Scale entire image to fit", o padrão): o bruto
  1920x1080 numa timeline 1080x1920 já entra a 0,5625, então escala do XML = escala desejada / encaixe.
- O centro (`horiz`/`vert`) é fração do **clipe já encaixado** (1080x607 no bruto, 1080x660 num painel).
- O `<when>` de cada keyframe conta do **início da mídia** (soma o `<in>`). Sem isso, os keyframes do
  Daniel (bruto começando em 4:28) caíam fora do clipe e o punch-in e a descida sumiam.
- Recusa a importação inteira se uma trilha de áudio aponta para o áudio do MP4 ("Operation canceled"):
  extraia `voz_bruto.wav`.
- Toda trilha de áudio vira **mono centralizada (−3 dB)**: voz dual-mono numa trilha só (+3 dB no ganho),
  trilha estéreo em duas com `audiopan` −1/+1.
- Teste sempre: projeto "TESTE XML CIBO", `ImportTimelineFromFile` + render 540x960 e folha de quadros.
  Arquivo trocado no mesmo caminho fica em cache no Media Pool (use nome novo para medir de novo).
- A API não cria Adjustment Clip: entregue o LUT (.cube) e o editor aplica.
- **Capa pela API (`AppendToTimeline`) não pode ser PNG nem `.mov` de 1 quadro (EP 07, 20/10/2026).** O Resolve trata os dois como still de 5 s e ignora o `endFrame`: a capa entrou com 150 quadros e cobriu o início dos 5 cortes. Use um ProRes de 5 quadros (`ffmpeg -loop 1 -i capa.png -frames:v 5 -r 30 -c:v prores_ks -profile:v 3 "capa ... 5q.mov"`) com `startFrame 0`, `endFrame 1` (`endFrame 0` é recusado), na faixa de cima "CAPA". Depois confira se `GetDuration() == 1`. No XML a capa PNG de 1 quadro funciona, porque lá o in e out é respeitado.

Som do Histórias do Porto: trilha a **−23 dB** (o editor achou −27 baixa), ducking ratio 3; whoosh nas
emendas (nunca no burn de abertura/fechamento) e na entrada/saída dos painéis; os dois cliques alternados; SFX cômico na piada (disco arranhado antes da resposta seca,
grilos no silêncio constrangedor); **palavrão leva bipe** 1 kHz (acervo `bipe-censura`, nível −5 dB,
voz cortada na palavra) e a legenda mostra "c*". Uma gravação de Histórias pode ter duas histórias e
muitas tomadas: use só a última tomada completa de cada uma, mais a vinheta de outra tomada.

**Início de tomada ("pode ir, vai"):** o Daniel dá a deixa antes de começar, e o Whisper engole o "vai" no
"A história" (põe as duas palavras coladas e erra o tempo). Não identifique a sílaba pelo Whisper: no perfil
de energia em 10 ms do `voz_bruto.wav` a sequência é deixa → "vai" → **respiração** (~-40 dB, 0,3 s) →
"A história"; o início vai no vale entre a respiração e o "A" (EP 06: "vai" 205,58–205,72, respiração
205,95–206,25, "A" 206,30 → início 206,267). Mover o início é deslocar **todas** as camadas (edit.json,
words/blocks, `edit_a_fc.txt`, refs/música/SFX em `STORIES`, SRT) e refazer XML e MP4; confira com
correlação do MP4 contra o bruto, não com transcrição (o Whisper "ouve" o "vai" mesmo depois de ele sair).

## Choosing `keeps`

`keeps` is the edit. Drop filler, false starts, repeated phrases and dead air; keep
whole clauses. Boundaries are then **snapped automatically** to the quietest 10 ms
frame within ±160 ms and given 35 ms/55 ms fades, so cuts land in breaths instead of
on top of a word. Do not hand-tune to the millisecond — snap it.

The first `keeps` start and the last end are never snapped, so the clip opens and
closes exactly where you asked.

Before accepting the last end, read at least the following 10–20 seconds of transcript
and verify that the speaker's **semantic thought** is complete. A grammatical pause or
period is not enough when the next clause qualifies, explains, or finishes the idea.
End after the complete thought, leave a short natural breath, and then start the outro;
never use the film burn to hide a sentence or context cut in half.

## What the pipeline produces

| Stage | What it does |
|---|---|
| `plan.py` | snaps keeps to silence, maps SRT cues through the trim, merges them into ≤18-char captions, flags emphasis words |
| `face_crop.py` | detects camera cuts at frame precision, samples faces with OpenCV, and emits one median crop per shot plus a visual preview |
| `render_caps.py` | draws captions to a 1080×420 band as two H.264 streams (colour + alpha matte) — fast and small |
| `clicks.py` | places a real, softly mixed shutter sample at reviewed `click_times` |
| `render.py` | cut+crop+scale with time-coded eased motion, eased zoom-out with blur opener (Python, frame-exact), screen-blends the blue film burn at both ends, overlays captions, mixes clicks/music/outro SFX, prepends the cover — **all in one x264 pass** |
| `cover.py` | grabs `cover_t`, adds scrim + headline + logo → `capa_*.png` |

Every delivered cut must have a cover. Produce both a standalone 1080×1920 PNG named
`CAPA - <headline>.png` and the same cover as the MP4's opening thumbnail frame. Before
delivery, verify that the PNG exists, inspect it visually, extract frame zero from the
MP4, and confirm that it contains the same headline treatment and logo. A rendered MP4
without this two-part cover delivery is incomplete.

The Bombordo e Boreste cover signature must be unique. Use authorized thumbnails as composition references, then compare layout, crop, typography, colours, logo and effects against the cross-client cover registry; never recycle another client's structure.

## Changing a finished cut

This is the common case, and it must not cost a full rebuild. Stages are
fingerprinted in `work/.stamps.json`; only what actually changed re-renders.
A no-op run is ~0.5 s.

| Request | Edit | Rebuilds | Cost |
|---|---|---|---|
| wrong word, bad line break, emphasis | `work/captions_<clip>.json` | caps → compose → deliver | ~35 s |
| caption position / size / colour | `job.style`, then `REPLAN=0` | caps → compose → deliver | ~35 s |
| headline or cover frame | `job.clips.<k>.headline` / `cover_t` | cover → deliver | ~8 s |
| trim, extend, drop a beat | `job.clips.<k>.keeps` + `REPLAN=1` | everything | ~2 min |
| framing | `cropx_timeline` (or fallback `cropx`) | everything | ~2 min |
| bitrate / size | `crf`, `preset`, `extra_v` | deliver | ~15 s |

`work/captions_<clip>.json` is the source of truth once it exists — `plan.py` will
not overwrite it unless `REPLAN=1`. Hand-edit `t`, `w` and `em` there; that is where
a Portuguese fix belongs after the first pass. `work/review.csv` maps every caption to
its timecode **in the delivered file** (cover included), so a note like "aos 12 s está
errado" resolves to a row without opening the video.

## Never render a full clip to look at something

```bash
JOB=job.json python3 scripts/tools.py probe corte01 12 18   # 6 s @540p, ~2 s
JOB=job.json python3 scripts/tools.py sheet corte01         # 8-frame sheet, ~2 s
```

`sheet` crops to the caption band. Run it after **any** visual change and actually
look at it before rendering or delivering. Every visual bug in this skill's history
was visible in a contact sheet and got caught only after a full render instead.

For framing, run the dedicated analyser and inspect its full-height preview:

```bash
python3 scripts/face_crop.py --job job.json --clip corte01 \
  --out work/face_corte01.json --preview work/face_corte01.jpg
```

Copy the reviewed `timeline` into `job.clips.<clip>.cropx_timeline`. Detection is a
proposal, not permission to skip visual review.

## Rules that matter

- **Captions align on a shared baseline.** Words are positioned by font ascent, never
  by their own bounding box — otherwise `o`, `aí`, `É` float up and the line looks
  crooked. Emphasis words are larger but sit on the same baseline.
- **≤18 characters** per caption, auto-wrapped to two lines and auto-shrunk to fit.
- **Fix the Portuguese.** Auto-transcribed SRTs mangle jargon. Put regex→replacement
  pairs in `job.fix`; they run *after* cues are merged, so multi-word fixes work.
- **Emphasis** words come from `job.emph` (space-separated, matched case- and
  punctuation-insensitively).
- **Alpha in ffmpeg:** this build's `libvpx-vp9` silently drops alpha and `qtrle`/PNG
  MOVs are huge. Ship colour + `alphaextract` matte as two H.264 files and
  `alphamerge` them at compose time.
- **`blend=all_mode=screen` must run in RGB.** Screening YUV planes tints the whole
  frame magenta — `format=gbrp` both inputs first.
- **Shot-aware crop.** `cropx` is only a fallback. Prefer `cropx_timeline`, whose
  entries are `[source-local-second, cropx]`. Detect faces by shot, use a median centre
  and quantize it; do not follow normal head movement frame by frame. Confirm the
  transition frame and inspect the generated contact sheet before the full render.
- **Final burn must complete the transition.** Screen-blend it over the last 1.3–1.4 s,
  fade the composite fully to black, and hold a short black tail so the underlying
  interview frame never reappears after the burn. Keep its own sound below the
  dialogue/music mix (around −6 dB is a useful starting point).

## Music

Use a licensed/approved track and mix it *under* the voice. Start at **−27 dB** (the user
rejected −21 as "muito alta") and
use `sidechaincompress` keyed off the dialogue; validate by listening because masters
and musical arrangements vary. Preserve the chosen mix in `job.mix` so cache
fingerprints invalidate correctly when gain or ducking changes. A clip-level `mix`
overrides global mix fields when different masters need different gain.

## Deliverables

After every final render, run `caption-quality-gate` and `video-delivery-safety-check`; automated success never replaces visual/audio review against the job. At demand closeout, rerun `video-project-structure`, update the client bible/source catalog/manifests, and upload the required skills and reusable licensed assets to the client's Drive. Never upload raw/master/proxy or stock video to the skills/assets Drive.

`outdir/<headline>.mp4` (thumbnail frame + intro/outro film burn + clip) and
`outdir/CAPA - <headline>.png`.
Also hand back the DaVinci `HH:MM:SS:FF` in/out of each source window so the editor
can find the moment in the master.

## Falhas conhecidas (índice)

Texto completo em `references/historico-falhas.md`: abra o item quando o sintoma aparecer.

- 1. Captions look crooked
- 2. Whole frame goes magenta
- 3. Caption band renders as an opaque black bar
- 4. Cuts sound abrupt
- 5. File too big to deliver
- 6. A clip comes out too short
- 7. Encoding the same frames twice
- 8. Motion feels twitchy
- 9. Clicks are absent or become repetitive
- 10. Background jobs die
- 11. Ken-burns zoom looks shaky/vibrating
- 12. A click SFX steps on the opening word
- 13. Face tracking causes shake or a glitch at camera changes
- 14. Film burn fails to concatenate or stretches the frame
- 15. Limiter unexpectedly makes everything louder
- 16. "Stream specifier ':a' ... matches no streams" on the final render
- 17. A long, unfragmented SRT cue ships as one on-screen wall of text
