# katia — histórico de falhas

Texto completo das lições resumidas no índice do `SKILL.md`.

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

## Where to render

Caption bands, clicks, film burn and covers are cheap — do them anywhere. The h264
encodes are the slow part; on a 2-core sandbox a 45 s clip costs ~2 min end to end.
If the user's machine is reachable, run the encodes there instead. Keep an eye on
delivery limits: files over ~20 MB can't be written back to a connected folder, so
either render on the device or cap the bitrate (`crf 24`, `maxrate 2900k` lands a
47 s 1080×1920 clip at ~18 MB).
