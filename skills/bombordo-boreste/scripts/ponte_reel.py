#!/usr/bin/env python3
"""Ponte reel-motion -> camadas do Bombordo (editor, 01/11/2026: "mude o motor de bombordo e boreste para o mesmo da
andreia e fernanda ... esse motor aqui erra muito nos cortes das falas").

Os trechos e a fala de cada corte saem do reel-motion (rNN/segs.json em segundos do bruto, checa_takes, hesita, MFA,
revisa); a identidade continua a do Bombordo (legenda kinetic Cal Sans, burn azul, clique, punch-in, capa, fade).
Esta ponte converte o resultado de um rNN para o formato que o kit de camadas do Bombordo lê:

  PROJ/04_work/cortes/<corte>/edit.json            keeps (= segs), seams, total
  PROJ/04_work/cortes/<corte>/edit16k.wav          voz montada (ducking da trilha)
  PROJ/04_work/cortes/<corte>/kinetic/words_<corte>.json   palavras do MFA (w, s, e) -> kinetic segment

uso: ponte_reel.py PROJ rNN [corteNN] [--segment]
  --segment  já roda o kinetic segment (blocos + destaques; kinetic.yaml em 04_work/cortes/)
Depois: componentes.py <corte> (caps caption fade music cover cfg) e o XML/Resolve do kit do episódio.
"""
import json, os, shutil, sys

P = os.path.abspath(sys.argv[1]); R = sys.argv[2]
K = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else 'corte' + R[1:]
W = os.path.join(P, '04_work', R); D = os.path.join(P, '04_work', 'cortes', K)
os.makedirs(os.path.join(D, 'kinetic'), exist_ok=True)

S = json.load(open(os.path.join(W, 'segs.json')))
seams, acc = [], 0.0
for a, b in S[:-1]:
    acc += b - a; seams.append(round(acc, 3))
total = round(sum(b - a for a, b in S), 3)
json.dump(dict(keeps=S, seams=seams, total=total, origem=f'reel-motion {R}'), open(os.path.join(D, 'edit.json'), 'w'), indent=1)
shutil.copy2(os.path.join(W, 'voz16k.wav'), os.path.join(D, 'edit16k.wav'))

ws = json.load(open(os.path.join(W, 'edit_mfa.json')))['segments'][0]['words']
out = []
for w in ws:
    t = w['word'].strip()
    if not t:
        continue
    s, e = round(w['start'], 3), round(w['end'], 3)
    if out and s < out[-1]['e']:          # MFA nunca sobrepõe, mas o edit_fix pode juntar palavras
        s = out[-1]['e']
    out.append(dict(w=t, s=s, e=max(e, s + 0.04), src='mfa'))
json.dump(dict(clip=K, total=total, words=out), open(os.path.join(D, 'kinetic', f'words_{K}.json'), 'w'), ensure_ascii=False, indent=1)
print(f'{R} -> {K}: {len(S)} trechos, {total:.2f}s, {len(out)} palavras')

if '--segment' in sys.argv:
    KIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kinetic')
    sys.path.insert(0, KIN)
    import segment
    from common import load_config
    ycfg = os.path.join(P, '04_work', 'cortes', 'kinetic.yaml')
    cfg = load_config(K, ycfg if os.path.exists(ycfg) else None)
    segment.build({}, D, K, cfg)
