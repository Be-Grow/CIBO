"""Gera reel.json "video_map" (um por trecho de segs.json): imagem do bruto no mesmo instante do episódio.
Trecho cujo offset destoa da mediana dos vizinhos (falso positivo em trecho curto) herda o offset da mediana.
uso: aplica_mapa.py rNN/ sync/epXX.json"""
import json, sys, statistics
W, M = sys.argv[1], json.load(open(sys.argv[2]))
S = json.load(open(f'{W}/segs.json'))
rows = [M[f'{a:.2f}-{b:.2f}'] for a, b in S]
out = []
for i, r in enumerate(rows):
    viz = [x for j, x in enumerate(rows) if j != i and abs(j - i) <= 3]
    med = statistics.median([x['offset'] for x in viz]) if viz else r['offset']
    src = statistics.mode([x['bruto'] for x in viz]) if viz else r['bruto']
    if abs(r['offset'] - med) > 0.3 and (S[i][1] - S[i][0] < 1.5 or r.get('score', 1) < 0.6):   # só trecho curto ou fraco
        print(f'trecho {i} {S[i][0]:.2f}: offset {r["offset"]:.2f} destoa, usa {med:.2f} ({src.split("/")[-1]})'); r = {'bruto': src, 'offset': med}
    out.append({'src': r['bruto'], 'off': r['offset']})
c = json.load(open(f'{W}/reel.json')); c['video_map'] = out; json.dump(c, open(f'{W}/reel.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'trechos mapeados')
