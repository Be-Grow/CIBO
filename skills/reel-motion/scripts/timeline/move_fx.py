# desloca movimentos.json depois de tirar [A,B) quadros (tempo relativo ao início da timeline) e grava num pacote-fantasma
# com o nome da timeline (o resolve_fx procura a timeline pelo nome da pasta). uso: move_fx.py PACOTE_ORIG "NOME TL" A B
import json, os, sys
pac, nome, A, B = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); D = B - A
m = json.load(open(f'{pac}/movimentos.json')); novas = []
for c in m['camadas']:
    i, f = c['inicio'], c['inicio'] + c['dur']
    if f <= A: novas.append(c); continue
    if i >= B: c['inicio'] -= D; novas.append(c); continue
    if A <= i and f <= B: continue                       # camada inteira dentro do trecho: sai
    kf = [k for k in c['kf'] if not (A <= i + k[0] < B)]  # tira os quadros do trecho cortado
    kf = [[k[0] - (D if i + k[0] >= B else 0)] + k[1:] for k in kf]
    if i >= A: c['inicio'] = A; kf = [[k[0] - (A - i) if k[0] >= (A - i) else k[0]] + k[1:] for k in kf]
    c['kf'] = kf; c['dur'] = c['dur'] - (min(f, B) - max(i, A)); novas.append(c)
m['camadas'] = novas; os.makedirs(f'tmp/fx/{nome}', exist_ok=True)
json.dump(m, open(f'tmp/fx/{nome}/movimentos.json', 'w'), ensure_ascii=False); print(len(novas), 'camadas →', f'tmp/fx/{nome}')
