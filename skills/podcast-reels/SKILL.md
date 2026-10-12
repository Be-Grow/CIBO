---
name: podcast-reels
description: Turn a long podcast episode plus its SRT into vertical 9:16 Reels/TikTok/Shorts cuts with baseline-aligned Cal Sans captions, emphasis lettering, camera-click SFX, a blue film-burn intro, an eased zoom-out-with-blur opener, and a headline cover. Use when the user asks for "cortes", clips, Reels, Shorts or TikToks from a podcast, or wants captions burned into a vertical clip.
---

# Podcast → Reels

**Local setup:** dependencies (Pillow, numpy) live in a venv at
`~/.claude/skills/podcast-reels/.venv`. Run scripts with
`~/.claude/skills/podcast-reels/.venv/bin/python3 scripts/make_reels.py`, or
`source ~/.claude/skills/podcast-reels/.venv/bin/activate` first, instead of the
bare `python3` shown below. Requires `ffmpeg`/`ffprobe` on PATH (already present
via Homebrew).


Builds finished vertical cuts from a master video + SRT. Everything is driven by one
`job.json`; the scripts do transcription-free caption timing (reused from the SRT),
silence-snapped trimming, caption rendering, audio sweetening and the cover.

## Workflow

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
   `headline`, `filename` (the delivered basename — never leave this as the clip
   key; deliverables must be named after the headline, e.g.
   `01 - ELEGANCIA NAO E - FICAR INVISIVEL - DEPOIS DOS 50`, matching the cover's
   `CAPA - <filename>.png`), `cropx`, `cover_t`, and `keeps` (list of `[start,end]`
   in *clip-local* seconds).
5. **Run it:**
   ```bash
   JOB=job.json python3 scripts/make_reels.py            # all clips
   JOB=job.json python3 scripts/make_reels.py corte01    # one clip
   ```

## Choosing `keeps`

`keeps` is the edit. Drop filler, false starts, repeated phrases and dead air; keep
whole clauses. Boundaries are then **snapped automatically** to the quietest 10 ms
frame within ±160 ms and given 35 ms/55 ms fades, so cuts land in breaths instead of
on top of a word. Do not hand-tune to the millisecond — snap it.

The first `keeps` start and the last end are never snapped, so the clip opens and
closes exactly where you asked.

## What the pipeline produces

| Stage | What it does |
|---|---|
| `plan.py` | snaps keeps to silence, maps SRT cues through the trim, merges them into ≤18-char captions, flags emphasis words |
| `render_caps.py` | draws captions to a 1080×420 band as two H.264 streams (colour + alpha matte) — fast and small |
| `clicks.py` | synthesises a soft shutter click, one per emphasis caption |
| `render.py` | cut+crop+scale with a per-segment eased ken-burns zoom, eased zoom-out with blur opener (Python, frame-exact), screen-blends the blue film burn, overlays captions, mixes clicks, prepends the cover — **all in one x264 pass** |
| `cover.py` | grabs `cover_t`, adds scrim + headline + logo → `capa_*.png` |

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
| framing | `cropx` | everything | ~2 min |
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

## Render padrão (rápido) e opções

Comece todo job assim (detalhes no item 46 do histórico):

```bash
taskpolicy -B -t 0 -l 0 -p $$          # em background o macOS usa os núcleos lentos
export JOB=job.json ZOOM_AMT=0 BURN_OUT=0 VENC=auto PASSA_DIRECT=1 \
       BURN_END_INLINE=1 BURN_END_LIMIT=0.84 BURN_END_BT709=1
~/.claude/skills/podcast-reels/.venv/bin/python3 scripts/make_reels.py corte01 | grep -E "built|DONE|Error"
```

| Chave | Onde | O que faz |
|---|---|---|
| `VENC=auto` | env | encoder escolhido pelo perfil de hardware (`video-render-optimizer`); falhou → x264 |
| `PASSA_DIRECT=1` | env | recorte direto no ffmpeg (só com `ZOOM_AMT=0`) |
| `BURN_END_INLINE=1` | env | burn de saída sobre preto dentro do `final()` (+`BURN_END_LIMIT`, `BURN_END_BT709`) |
| `overlays` | clipe | `.mov` com alpha (Remotion) + SFX opcional, na mesma codificação |
| `crop_h` | clipe | recorte mais baixo para tirar logo de terceiros do rodapé |
| `cropx_timeline`, `cropx_interp` | clipe | enquadramento por plano / seguindo a pessoa no palco |
| `cover_src`, `cover_src_t`, `cover_src_x` | clipe | capa de qualquer momento da gravação |
| `voice_af`, `music`, `mix` | clipe | cadeia da voz; trilha com ducking (`duck_ratio` 3, `duck_threshold` 0.1, `music_db` −18 em fala contínua) |
| `burn_at`, `nosnap`, `cover_style` | clipe | burn no meio; emenda sem snap; estilo de capa (`lpa`) |
| `REPLAN=1` | env | refaz o plano de legendas (senão `captions_<clip>.json` manda) |

Trilha: escolha com `talking-head-music` (por corte, com offset). Fim do corte: vídeo acaba seco
e o burn passa do fim sobre preto, nunca fade.

## Economia de tokens

- Filtre a saída: `| grep -E "built|DONE|Error"`. O plano de legendas só é impresso com
  `PLAN_VERBOSE=1`; para revisar, abra `work/review.csv` no trecho que interessa.
- QA de lote numa chamada: `scripts/qa_lote.py PASTA` (verify, LUFS, pico, cor, duração e uma
  folha de contato por corte numa imagem só).
- Uma folha de contato por decisão, nunca quadro a quadro.

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
- **Fixed crop per clip.** `cropx` is the horizontal centre (0–1) of the 608×1080
  window; set it per clip so an off-centre speaker isn't clipped.

## Deliverables

`outdir/<clip>.mp4` (1 s cover + film burn + clip) and `outdir/capa_<clip>.png`.
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
