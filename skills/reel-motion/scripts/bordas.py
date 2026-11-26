#!/usr/bin/env python3
"""Borda de corte pela PALAVRA EXATA (MFA), com o som como desempate. A correção mais repetida do CIBO (12 vezes até 25/11/2026:
"corte comendo metade da palavra", "comendo muitas palavras nos intervalos dos cortes").

Por que não basta o som (versão até 25/11, hoje em bordas_som.py): o Whisper marca o fim da palavra cedo, e um silêncio de
40 ms acontece DENTRO da palavra ("Tik|Tok", "vin|te"). No João (25/11) a borda caiu em "ide|ia" e o trecho seguinte comeu o "se".

Como confere: alinha com o MFA o texto do Whisper em volta dos cortes (uma janela por grupo de trechos próximos, ~30 s de
alinhamento por reel; cache em W/bordas_mfa.json) e exige, em toda borda que corta algo (inclusive emendas internas):
  fim    depois do fim da última palavra mantida + rabo (o som da palavra até cair abaixo do piso, máx 0,15 s) e antes da próxima
  começo antes do começo da 1ª palavra mantida (folga até 0,04 s) e depois do fim da palavra anterior
Borda dentro de palavra: --aplica inclui a palavra inteira (fim anda até o fim dela + rabo; começo volta ao começo dela).
Precisa andar mais que 0,6 s (fim) / 0,4 s (começo) = OUVIR. Sem MFA ou sem palavras: confere só pelo som (bordas_som.py) e avisa.

uso: bordas.py W [--aplica]           W = PROJ/04_work/rNN (segs.json, src_16k.wav; palavras: src_w.json, ou
                                      PROJ/02_transcripts/*words*.json da fonte do reel.json, ou --palavras)
     bordas.py --segs S.json --wav F --palavras WH.json [--cache C.json] [--aplica]   qualquer skill (tempos da fonte)
Saída: 0 = tudo certo (ou corrigido com --aplica); 1 = borda para corrigir/ouvir; 2 = não conseguiu conferir."""
import glob, json, os, subprocess, sys
from pathlib import Path

try:
    import numpy as np
except ImportError:                                               # python3 do sistema: a trava NÃO pode só quebrar
    alt = Path.home() / '.venvs/audiotools/bin/python'
    if alt.exists() and Path(sys.executable).resolve() != alt.resolve():
        os.execv(str(alt), [str(alt), __file__] + sys.argv[1:])
    print('!! bordas.py sem numpy: as bordas NÃO foram conferidas', file=sys.stderr); sys.exit(2)

AQUI = Path(__file__).resolve().parent
MFA_PY = Path(os.environ.get('CIBO_ALINHA_MFA', Path.home() / '.claude/skills/fala-limpa/scripts/alinha_mfa.py'))
a = sys.argv[1:]
if not a or a[0] in ('-h', '--help'): sys.exit(__doc__)
def opt(n, d=None):
    return a[a.index(n) + 1] if n in a else d
APLICA = '--aplica' in a
MAXF, MAXI, RABO, FOLGA = 0.6, 0.4, 0.15, 0.04


def acha_palavras(W):
    if (W / 'src_w.json').exists(): return W / 'src_w.json'
    try:
        src = Path(json.load(open(W / 'reel.json')).get('src', '')).stem.lower()
    except Exception:
        src = ''
    cand = sorted(glob.glob(str(W.parent.parent / '02_transcripts' / '*words*.json')))
    pref = [c for c in cand if src and Path(c).stem.split('_')[0].lower() in src]
    return Path((pref or cand)[0]) if (pref or cand) else None


if '--segs' in a:
    SEGS, WAV = Path(opt('--segs')), Path(opt('--wav')); PAL = Path(opt('--palavras')) if opt('--palavras') else None
    CACHE = Path(opt('--cache') or SEGS.with_name('bordas_mfa.json'))
else:
    W = Path(a[0]); SEGS, WAV = W / 'segs.json', W / 'src_16k.wav'
    PAL = Path(opt('--palavras')) if opt('--palavras') else acha_palavras(W); CACHE = W / 'bordas_mfa.json'
for f in (SEGS, WAV):
    if not f.exists(): print(f'!! {f} não existe: bordas NÃO conferidas', file=sys.stderr); sys.exit(2)


def so_pelo_som(motivo):
    print(f'aviso: {motivo}: conferindo SÓ PELO SOM (fraco para palavra comida)', flush=True)
    som = AQUI / 'bordas_som.py'
    args = [str(WAV.parent)] if '--segs' not in a else None
    if args is None:                                              # bordas_som.py só aceita W: monta um W temporário
        print('!! modo --segs sem palavras/MFA: bordas NÃO conferidas', file=sys.stderr); sys.exit(2)
    os.execv(sys.executable, [sys.executable, str(som)] + args + (['--aplica'] if APLICA else []))


if not PAL or not PAL.exists(): so_pelo_som('sem palavras do Whisper da fonte')
if not MFA_PY.exists(): so_pelo_som('alinhador MFA não encontrado')

S = json.load(open(SEGS))
# só bordas que cortam algo
bordas = []
for k, seg in enumerate(S):
    s, e = float(seg[0]), float(seg[1])
    if not (k and abs(s - float(S[k - 1][1])) < 0.02): bordas.append((k, 'começo', s))
    if not (k + 1 < len(S) and abs(float(S[k + 1][0]) - e) < 0.02): bordas.append((k, 'fim', e))

# janelas de alinhamento: bordas próximas (< 40 s) dividem uma janela
ts = sorted(t for _, _, t in bordas); janelas = []
for t in ts:
    if janelas and t - janelas[-1][1] < 40: janelas[-1][1] = t
    else: janelas.append([t, t])
janelas = [(round(max(0, x - 3), 2), round(y + 3, 2)) for x, y in janelas]

cache = json.load(open(CACHE)) if CACHE.exists() else {}
if cache.get('palavras_de') != str(PAL): cache = {'palavras_de': str(PAL), 'janelas': {}}
palavras = []
for j0, j1 in janelas:
    chave = next((c for c in cache['janelas'] if float(c.split('-')[0]) <= j0 and float(c.split('-')[1]) >= j1), None)
    if not chave:
        tmp = CACHE.with_name(f'.mfa_{j0}-{j1}.json')
        r = subprocess.run([sys.executable, str(MFA_PY), '--audio', str(WAV), '--words', str(PAL), '--range', str(j0), str(j1),
                            '--out', str(tmp), '--margem', '1.0'], capture_output=True, text=True)
        if r.returncode or not tmp.exists():
            so_pelo_som(f'MFA falhou na janela {j0}-{j1}: ' + ((r.stdout + r.stderr).strip().splitlines() or ['?'])[-1][:120])
        m = json.load(open(tmp)); tmp.unlink()
        chave = f'{j0}-{j1}'
        cache['janelas'][chave] = [(w['word'].strip(), w['start'], w['end'], bool(w.get('mfa'))) for s_ in m['segments'] for w in s_['words']]
        json.dump(cache, open(CACHE, 'w'))
    palavras += [tuple(w) for w in cache['janelas'][chave]]
palavras = sorted({(p[1], p[2], p[0], p[3]) for p in palavras})   # (ini, fim, texto, mfa)

# som: rabo da palavra (até cair abaixo do piso)
SR, P = 16000, 160
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(WAV), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                                 capture_output=True).stdout, np.int16).astype(np.float32) / 32768
n = len(x) // P
L = 20 * np.log10(np.sqrt((x[:n * P].reshape(n, P) ** 2).mean(1)) + 1e-9)
cs = L[L > -70]; ruido, voz = np.percentile(cs, 10), np.percentile(cs, 90)
PISO = min(max(ruido + 8, voz - 30), voz - 12)
q = lambda t: min(max(int(round(t * 100)), 0), n - 1)


def rabo(fim, limite):
    """fim da palavra pelo som: anda de `fim` até cair abaixo do piso (máx RABO) sem passar de `limite`"""
    i = q(fim)
    while i < q(min(fim + RABO, limite)) and L[i] >= PISO: i += 1
    return round(i / 100, 2)


def vizinhas(t):
    """(palavra que contém t ou None, última que termina antes de t, primeira que começa depois de t)"""
    dentro = next((w for w in palavras if w[0] + 0.02 < t < w[1] - 0.02), None)
    antes = max((w for w in palavras if w[1] <= t + 0.02), default=None, key=lambda w: w[1])
    depois = min((w for w in palavras if w[0] >= t - 0.02), default=None, key=lambda w: w[0])
    return dentro, antes, depois


novo = [list(s) for s in S]; mexe, ouvir, linhas = set(), 0, {}
for k, lado, t in bordas:
    dentro, antes, depois = vizinhas(t); nota = None
    ant_lim = float(S[k - 1][1]) if k else 0.0; prox_lim = float(S[k + 1][0]) if k + 1 < len(S) else n / 100
    if lado == 'fim':
        if dentro:
            alvo = rabo(dentro[1], min(depois[0] if depois and depois[0] > dentro[1] else 1e9, prox_lim))
            alvo = max(alvo, round(dentro[1] + 0.02, 2))
            if alvo - t > MAXF: nota = f"fim {t:.2f} corta '{dentro[2]}' ({dentro[0]:.2f}-{dentro[1]:.2f}); incluir é +{alvo - t:.2f} s: OUVIR"; ouvir += 1
            else: nota = f"fim {t:.2f}→{alvo:.2f} (+{alvo - t:.2f} s; cortava '{dentro[2]}')"; novo[k][1] = alvo; mexe.add(k)
        elif antes:
            ok_ate = rabo(antes[1], min(depois[0] if depois else 1e9, prox_lim))
            if t < min(ok_ate, depois[0] if depois else 1e9) - 0.01:
                alvo = min(ok_ate, prox_lim)
                nota = f"fim {t:.2f}→{alvo:.2f} (+{alvo - t:.2f} s; rabo de '{antes[2]}' soando)"; novo[k][1] = alvo; mexe.add(k)
    else:
        if dentro:
            alvo = round(max(dentro[0] - 0.02, antes[1] if antes else 0, ant_lim), 2)
            if t - alvo > MAXI: nota = f"começo {t:.2f} corta '{dentro[2]}' ({dentro[0]:.2f}-{dentro[1]:.2f}); incluir é -{t - alvo:.2f} s: OUVIR"; ouvir += 1
            else: nota = f"começo {t:.2f}→{alvo:.2f} (-{t - alvo:.2f} s; cortava '{dentro[2]}')"; novo[k][0] = alvo; mexe.add(k)
        elif depois and t > depois[0] - 0.005:
            alvo = round(max(depois[0] - FOLGA, antes[1] if antes else 0, ant_lim), 2)
            if alvo < t - 0.005:
                nota = f"começo {t:.2f}→{alvo:.2f} (-{t - alvo:.2f} s; colado no ataque de '{depois[2]}')"; novo[k][0] = alvo; mexe.add(k)
    if nota: linhas.setdefault(k, []).append(nota)

for k in sorted(linhas):
    print(f'{float(S[k][0]):.2f}-{float(S[k][1]):.2f} corte no som: ' + '; '.join(linhas[k]))   # formato que o portão lê
print(f'{len(S)} trechos, {len(bordas)} bordas conferidas pela palavra (MFA, {len(palavras)} palavras) | '
      f'{len(mexe)} trecho(s) com borda corrigível, {ouvir} para ouvir')
if APLICA and mexe:
    bak = SEGS.with_name(SEGS.name + '.bak-bordas')
    if not bak.exists(): bak.write_text(SEGS.read_text())
    json.dump(novo, open(SEGS, 'w')); print(f'{SEGS.name} corrigido ({len(mexe)} trechos); original em {bak.name}. Refaça voz/legenda.')
sys.exit(0 if (APLICA and not ouvir) or not (mexe or ouvir) else 1)
