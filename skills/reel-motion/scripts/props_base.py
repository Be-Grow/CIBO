"""Monta o props.json de um reel a partir das partes próprias do corte (usado pelos rNN/props.py)."""
import json, os
BURNS = os.path.join(os.path.dirname(__file__), 'public/burns/burns.json')


def build(W, OUT, dur, split, panels, hook=None, titles=None, burns=(), lower=None, tail=0.8, end_fade=0.9):
    r = os.path.basename(W)
    blocks = json.load(open(f'{W}/blocos.json'))
    for b in blocks:
        b.pop('audio', None)
    B = json.load(open(BURNS))
    p = {"camera": f"{r}/camera.mov", "duration": round(dur + tail, 3), "endFade": end_fade, "split": split, "panels": panels, "captions": blocks}
    if hook: p["hook"] = hook
    if titles: p["titles"] = titles
    if lower: p["lower"] = lower
    p["burns"] = [dict(t=t, src=f'burns/burn_{k}.mp4', peak=B[k]['peak'], dur=B[k]['dur']) for t, k in burns]
    json.dump(p, open(OUT, 'w'), ensure_ascii=False, indent=1)
    print('ok', OUT)
