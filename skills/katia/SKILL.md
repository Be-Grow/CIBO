---
name: katia
description: Crie cortes verticais 9:16 para Reels, TikTok e Shorts da Katia, usando o estilo, a fonte e a trilha próprios desta cliente. Use somente em trabalhos da Katia.
---

# Katia → Reels

**Local setup:** dependencies (Pillow, numpy) live in a venv at
`~/.claude/skills/katia/.venv`. Run scripts with
`~/.claude/skills/katia/.venv/bin/python3 scripts/make_reels.py`, or
`source ~/.claude/skills/katia/.venv/bin/activate` first, instead of the
bare `python3` shown below. Requires `ffmpeg`/`ffprobe` on PATH (already present
via Homebrew).

Builds finished vertical cuts from a master video + SRT. Everything is driven by one
`job.json`; the scripts do transcription-free caption timing (reused from the SRT),
silence-snapped trimming, caption rendering, audio sweetening and the cover.

**Motor (12/10/2026):** a Katia não tem mais cópia do motor. `scripts/make_reels.py` e
`scripts/tools.py` chamam o motor único `podcast-reels` com o perfil `assets/profile.json`
(Montserrat Bold, manchete em 0,775 sem barra, correções e ênfases da cliente). Toda opção da
`podcast-reels` vale aqui (`VENC=auto`, `PARALLEL=auto`, `overlays`, `BURN_END_INLINE`,
`audio_qa.py`, `cover_rank.py`). A cópia antiga tinha bugs já corrigidos no motor: vídeo cortado
acima de 2 min, trilha em loop infinito travando o encode, frase sumindo da legenda.

## Katia — client defaults

- **Long interview podcast is a different job.** Besides the scripted monologues, Katia
  (Kátia Ribeiro) hosts a 50+ interview podcast (e.g. 2026-09-14 with Karla Sarney —
  spelled with K, Whisper writes "Carla"), recorded as an already-switched multicam
  16:9 master. When the user asks to "editar esse podcast" there, it means a clean
  long edit only — no Reels, no cover, no music, stays horizontal ("eu n quero corte,
  é um podcast limpo"). Use `limpeza-gravacao-bruta` (with `--punch` for same-shot
  joins) and `video-delivery-safety-check`; the raw audio peaks above 0 dBFS.

- **Caption + cover font:** Montserrat Bold (`assets/Montserrat-VariableFont_wght.ttf`,
  variable font — `render_caps.py`/`cover.py` call `set_variation_by_name('Bold')`,
  override with `FONT_WEIGHT` env if a different weight is ever needed). Set
  `"font"` in `job.json` to this path; do not fall back to the bundled CalSans.
- **Cover layout:** headline sits lower on the frame than the shared default
  (`COVER_Y=0.775` no perfil, vs `0.735` no motor) and has **no**
  blue accent bar above it (`COVER_BAR=0` no perfil) — Katia's cover is just scrim + headline + optional logo.
  Don't reintroduce the bar; it was removed on purpose for this client.
  **The 0.775 layout alone produced covers the user called "horríveis"**: in a tight
  9:16 crop the face sits low and the headline landed on her mouth. For every cover,
  frame a slightly wider still with the face in the upper third (face centre ≈ 30 %
  of the height), keep the headline only on clothing or the dark scrim, and check
  numerically that the headline top is below the chin with margin. Pick a frame with
  eyes on camera and mouth closed or a light smile. Review all covers side by side.
- **Captions never cover her face.** When the face sits low, move the band down with
  `CAP_BAND_Y` (default 810) and confirm on the contact sheet, over the whole clip.
- **Cuts without cover.** If the user asks for the cuts "sem capa", drop only the
  cover frame (start the MP4 after the thumbnail frame, `-c copy` if the cut lands on a
  keyframe, otherwise re-mux from the same render); don't re-render the whole clip
  ("não era só cortar fora o frame da capa?").
- **Cover photos for AI tools.** When asked for stills to feed an image AI, export ~20
  varied, sharp, well-lit frames of her face into one folder, and write the prompts
  naming Katia and referring to her photo.
- **Framing:** static single-camera talking-head recordings, but don't guess one
  `cropx` for the whole batch — a single eyeballed value (e.g. `0.58`) drifted
  0.05–0.13 off-center across the 8 reference clips because framing shifts
  slightly between recording moments even on the "same" camera. Run
  `scripts/face_crop.py --job job.json --clip <k> --out ... --preview ...` per
  clip and use `timeline[0][1]` as that clip's `cropx` (a single-shot talking
  head returns one timeline entry — no need for `cropx_timeline` plumbing here).
  Always eyeball the `--preview` image before trusting it.
- **Music:** pull from the shared library at
  `/Volumes/SSD/Movies/Edição/Mídia/gravaçõesSEBRAE/content_hub_assets/music/`
  (yes, that's the Content Hub/SEBRAE asset pool — it's a shared, license-cleared
  music pool, safe to reuse across clients) via the `talking-head-music` skill's
  workflow. Katia's content is reflective/empowering monologues, not corporate hype —
  favor warm, low-key, piano/string tracks (e.g. `piano_reflections_ahjay_stelino`,
  `your_breath_eugenio_mininni`, `better_times_are_coming_alejandro_magana`) over the
  driving/motivational-business tracks in that pool, and vary the offset per clip.
- **Cuts:** Katia's raw recordings are multi-take — she repeats the same scripted
  monologue several times until a take is approved (listen for restart cues like
  "volta", "de novo", "3, 2, 1" and an explicit "gostei"/approval after a clean take).
  Always cut from the last clean, approved take, never an earlier rehearsal.
- **Re-readings for the team are tests, not takes.** After the blocks, she re-reads
  some sentences to show the team which parts become Reels ("tem um corte que vai
  fazer bem aqui", "aí tem a outra", "só o começo dos dois") — looking down, reading,
  or turned to the side. Never use these in the long edit or in any Reel; they only
  tell you *which* sentences to cut. Use the matching real take inside the block
  (eyes on camera). One such test slipped into "Para compreender o transtorno
  bipolar" and the long version.
- **Long edit: remove every aside to the team** and check that the joins sound natural
  (skill `limpeza-gravacao-bruta`), then run `fala-limpa` on every Reel.

## Workflow

> **Entrega — padrão atual: MP4** (exceção temporária ao padrão DaVinci do CIBO, editor 20/10/2026). O render final sai
> pelo ffmpeg (`podcast-reels/references/render-ffmpeg-legado.md`) até existir o adaptador `job.json` → pacote DaVinci.
> Regra: `client-router/references/regras/davinci.md`.


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

## Music

`render.py`'s `final()` mixes background music automatically when a clip sets
`"music"` (path to the track) and optionally `"mix"` (`music_db` default -26,
`music_offset` seconds into the track to start from, `duck_threshold`/`duck_ratio`
for the sidechain duck against dialogue, both with sane defaults). Use the
`talking-head-music` skill to shortlist and pick the track and offset per clip
first — don't default to 0:00 or the first file in a folder. Aggregator downloads
(Pixabay, Mixkit, etc.) are blocked from the sandbox; pick from an approved local
library instead.

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
