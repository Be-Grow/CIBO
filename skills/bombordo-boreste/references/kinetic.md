# Bombordo — legenda animada (kinetic typography)

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

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
