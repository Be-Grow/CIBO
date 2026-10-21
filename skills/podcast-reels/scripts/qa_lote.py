#!/usr/bin/env python3
"""QA de um lote de cortes numa chamada só, com saída curta (economia de tokens).

uso: qa_lote.py PASTA_DE_ENTREGA [--frames 0,2.2,9.6,0.6,-1.0] [--sheet SAIDA.jpg] [--only 01,03]

Para cada `NN - *.mp4` da pasta: verify_video (video-delivery-safety-check) com a capa
`CAPA - <nome>.png`, LUFS integrado, true peak, primárias de cor, duração e codec. Imprime
uma linha por corte e monta UMA folha de contato (um corte por linha, quadros nos tempos
pedidos; negativos contam do fim, fração < 1 é proporção da duração). Leia só a folha.
"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import argparse, glob, json, os, re, subprocess, sys, tempfile

VERIFY = os.path.expanduser('~/.claude/skills/video-delivery-safety-check/scripts/verify_video.py')


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(f):
    d = json.loads(run(['ffprobe', '-v', 'error', '-show_entries',
                        'format=duration:stream=codec_type,codec_name,color_primaries',
                        '-of', 'json', f]).stdout)
    v = next((s for s in d['streams'] if s['codec_type'] == 'video'), {})
    return float(d['format']['duration']), v.get('codec_name'), v.get('color_primaries')


def loud(f):
    e = run(['ffmpeg', '-nostdin', '-i', f, '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', e)
    p = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', e)
    return (float(i[-1]) if i else None), (float(p[-1]) if p else None)


def verify(f, cover, tmp):
    out = os.path.join(tmp, 'v.json')
    run([sys.executable, VERIFY, '--video', f, '--output-json', out] + (['--cover', cover] if os.path.exists(cover) else []))
    try:
        d = json.load(open(out))
        return d.get('automated_status'), d.get('errors') or [], d.get('warnings') or []
    except (OSError, ValueError):
        return 'VERIFY_FALHOU', [], []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pasta')
    ap.add_argument('--frames', default='0,2.2,9.6,0.6,-1.0')
    ap.add_argument('--sheet')
    ap.add_argument('--only')
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.pasta, '[0-9][0-9] - *.mp4')))
    if a.only:
        keep = set(a.only.split(','))
        files = [f for f in files if os.path.basename(f)[:2] in keep]
    sheet = a.sheet or os.path.join(a.pasta, '..', 'qa_lote.jpg')
    ts = [float(x) for x in a.frames.split(',')]
    rows, ok_all = [], True
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            name = os.path.basename(f)[:-4]
            dur, codec, prim = probe(f)
            lufs, peak = loud(f)
            st, errs, warns = verify(f, os.path.join(a.pasta, f'CAPA - {name}.png'), tmp)
            bad = (st != 'AUTOMATED_PASS' or prim != 'bt709' or lufs is None or abs(lufs + 14) > 1
                   or peak is None or peak > -1.0)
            ok_all &= not bad
            print(f"{'OK ' if not bad else 'ERRO'} {name[:2]} {dur:6.2f}s {codec} {prim} {lufs} LUFS pico {peak} {st}"
                  + (f" erros={errs[:2]}" if errs else '') + (f" avisos={warns[:2]}" if warns else ''))
            # quadros da folha
            outs = []
            for j, t in enumerate(ts):
                tt = dur + t if t < 0 else (dur * t if 0 < t < 1 else t)
                o = os.path.join(tmp, f'{name[:2]}_{j}.png')
                run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{max(0, tt):.3f}', '-i', f,
                     '-frames:v', '1', '-vf', 'scale=180:320', o])
                outs.append(o)
            row = os.path.join(tmp, f'row_{name[:2]}.png')
            ins = sum((['-i', o] for o in outs), [])
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *ins, '-filter_complex', f'hstack={len(outs)}', row])
            rows.append(row)
        if rows:
            ins = sum((['-i', r] for r in rows), [])
            fc = f'vstack={len(rows)}' if len(rows) > 1 else 'null'
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *ins, '-filter_complex', fc, '-q:v', '4', sheet])
    print(f"folha: {os.path.abspath(sheet)}  ({len(rows)} cortes x {len(ts)} quadros: {a.frames})")
    sys.exit(0 if ok_all else 1)


if __name__ == '__main__':
    main()
