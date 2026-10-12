# autismo-cast — histórico de falhas

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
8. **Motion feels twitchy.** Do not reset a zoom at every edit. Place
   `impact_pulses` on meaningful words and give them about 0.9–1.2 s with a modest
   4–5.5% amplitude; use `long_moves` around 2.3–3.0 s for slower visual variation.
   The sine envelope starts and ends at rest. Moves below roughly 0.7 s usually read
   as a camera glitch instead of emphasis.
9. **Clicks are absent or become repetitive.** Point `CLICK` at a real sample
   (`assets/click.wav`), trim it to the transient, and define a short reviewed
   `click_times` list per clip. Two to four semantic hits usually work better than
   firing on every emphasised caption. Normalize with `CLICK_GAIN` only after trimming.
10. **Background jobs die.** On the desktop bridge each shell call is its own process
   group — `nohup`/`setsid` do not survive. Every ffmpeg call must finish inside one
   call (~45 s), so chunk long renders.
11. **Ken-burns zoom looks shaky/vibrating.** `passA`'s pre-`zoompan` oversample (`OS`/
    `OSW`) was computed from the *native crop* size (608×1080) instead of the *final
    output* size (1080×1920) — zoompan was fed a ~654×1161 source and had to do most of
    the 1080×1920 upscale itself with its own weaker scaler, which shimmers as the crop
    shifts fractionally frame to frame. Fixed: base the oversample on `W,H` so zoompan
    only ever crops and lightly downscales from an already-adequate source.
12. **A click SFX steps on the opening word.** `clicks.py` fires on every caption flagged
    `any` (emphasis), including caption 0 — if the clip's first word is in `job.emph`
    (common: it's usually the hook stat), the click lands right on top of it and sounds
    like the voice glitching. Fixed: skip `idx==0` in `clicks.build`. Emphasis styling
    (bigger text) on the opening word is still fine — only the audio click is suppressed.
13. **Face tracking causes shake or a glitch at camera changes.** Never drive the crop
    from every detected frame. `face_crop.py` locates hard cuts at frame precision and
    uses the median face centre for the whole shot. Apply changes only at those cut
    frames or existing edit boundaries. A crop that switches even 2–3 frames before
    the camera does creates a visible sideways glitch. Separate `keeps` are not
    automatically separate camera shots: if jump cuts reuse the same camera and
    composition, keep one crop across them. Re-centering every keep by a few pixels
    produces repeated lateral pulls that become more visible during zooms.
14. **Film burn fails to concatenate or stretches the frame.** Normalize the main,
    burn and generated gap to `setsar=1` before concatenating/blending. For the outro,
    reuse the burn's original audio with short fades and mix it into the last transition.
15. **Limiter unexpectedly makes everything louder.** ffmpeg's `alimiter` can
    auto-level by default. Use `level=false`; a ceiling near `0.85` leaves enough room
    for AAC conversion without true-peak clipping.
16. **"Stream specifier ':a' ... matches no streams" on the final render.** The
    bundled `filmburn_blue.mp4` is video-only — `render.final()` used to
    unconditionally reuse `[2:a]` (the burn's own audio) for the outro mix, which
    fails outright against a silent burn asset. Fixed: `render.py` now probes
    `FILMBURN` for an audio stream with `ffprobe` and only builds the burn-audio
    mix layer when one exists, otherwise skips straight to the limiter. If you
    swap in a burn asset that *does* carry its own whoosh/SFX audio, this path
    picks it up automatically — no code change needed.
17. **A long, unfragmented SRT cue ships as one on-screen wall of text.**
    `plan.py`'s caption builder only *merged* short adjacent SRT cues up to the
    18-char limit — it never *split* a cue that was already longer than that on
    its own. A fluent passage with few pauses can land as one 30-40 character
    segment, sitting motionless on screen for its whole duration instead of
    short auto-wrapped captions. Fixed: atoms longer than 18 chars are now split
    into word-packed chunks before merging, with time apportioned by character
    count across the original cue's span. Caught by `caption-quality-gate`'s
    `block_long` warning — run it on every delivered clip, not just a visual
    spot-check.
18. **Full-episode clean edit ships with audio that stops early.** Cutting several
    segments of a ~1 h episode with multiple `trim`/`atrim` of the same input in one
    filter graph produced 59:56 of video but only 4:17 of audio, and ffmpeg still
    exited with code 0. Decode the audio to a full WAV and cut it there (`-ss S -t D -i full.wav`);
    cut the video separately and mux them with `-c:v copy`. Pick every IN/OUT from **word-level**
    Whisper, not segment timestamps: a "um, dois, três, vai" count-in hid inside a
    segment. After the render, confirm the audio and video stream durations match
    with `ffprobe`, and transcribe the audio around each join in the rendered file.

## Where to render

Before the first render on a new machine or delivery profile, use the `video-render-optimizer` skill. Detect the GPU and FFmpeg hardware encoders, benchmark CPU versus hardware on 8–15 seconds of representative project footage, and decide using encode time, SSIM, compatibility, real bitrate and projected size. For 1080×1920/30 start around 6–8 Mb/s with a 10 Mb/s ceiling. Do not select hardware merely because it exists; reject it when it inflates bitrate or loses visible quality, and verify the final MP4 bitrate with `ffprobe`.

Caption bands, clicks, film burn and covers are cheap — do them anywhere. The h264
encodes are the slow part; on a 2-core sandbox a 45 s clip costs ~2 min end to end.
If the user's machine is reachable, run the encodes there instead. Keep an eye on
delivery limits: files over ~20 MB can't be written back to a connected folder, so
either render on the device or cap the bitrate (`crf 24`, `maxrate 2900k` lands a
47 s 1080×1920 clip at ~18 MB).

On Apple Silicon, `VIDEO_ENCODER=h264_videotoolbox` uses the Mac's Media Engine.
It is especially useful for review iterations; start around `VT_BITRATE=16M` for
1080×1920. On an M4 Air benchmark, a 12 s encode fell from 10.09 s with
`libx264 slow` to 2.37 s with VideoToolbox. Hardware encoding needs more bitrate
for comparable quality, so keep `libx264` as the default for compact final masters.
