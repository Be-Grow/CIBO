---
name: autismo-cast
description: Crie cortes verticais 9:16 para Reels, TikTok e Shorts do Autismo Cast, usando o estilo, os assets e o fluxo de edição próprios deste cliente. Use somente em trabalhos do Autismo Cast.
---

# Autismo Cast → Reels

**Local setup:** dependencies (Pillow, numpy, OpenCV headless) live in the bundled venv at
`~/.claude/skills/autismo-cast/.venv`. Run scripts with
`~/.claude/skills/autismo-cast/.venv/bin/python3
~/.claude/skills/autismo-cast/scripts/make_reels.py`, or activate that venv first,
instead of the bare `python3` shown below. Requires `ffmpeg` and `ffprobe` on PATH.


Builds finished vertical cuts from a master video + SRT. Everything is driven by one
`job.json`; the scripts do transcription-free caption timing (reused from the SRT),
silence-snapped trimming, caption rendering, audio sweetening and the cover.

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

The Autismo Cast cover signature must be unique. Use authorized thumbnails as composition references, then compare layout, crop, typography, colours, logo and effects against the cross-client cover registry; never recycle another client's structure.

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

Use a licensed/approved track and mix it *under* the voice. Start around −21 dB and
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
- 18. Full-episode clean edit ships with audio that stops early
