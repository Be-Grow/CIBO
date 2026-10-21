"""Saída curta para os scripts do CIBO (eficiência, fase 3.1, 21/10/2026).

Uso, logo depois dos imports do script:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'client-router/scripts'))
    import saida_curta; saida_curta.curta()

O script se reexecuta como filho; tudo o que ele e os subprocessos (ffmpeg, Remotion, Resolve) escrevem vai para
<projeto>/05_qa/logs/<script>_<hora>.log. No terminal: no máximo 15 linhas (as marcadas como resultado + o fim) e o
caminho do log; em erro, o caminho e as últimas 20 linhas, com o mesmo código de saída. CIBO_VERBOSO=1 desliga.
"""
import os, re, signal, subprocess, sys, time
from pathlib import Path

MAX, ERRO = 15, 20
IMPORTA = re.compile(r'^\s*(==|OK|ok |FALHA|ERRO|AVISO|aviso|nota|resumo|checagem)|Traceback|Error|OK\b|FALHA')


def _pasta_log():
    for a in sys.argv[1:]:
        p = Path(a).expanduser()
        if not p.exists():
            continue
        for d in [p if p.is_dir() else p.parent, *p.resolve().parents]:
            if (d / '05_qa').is_dir() or (d / '04_work').is_dir():
                return d / '05_qa' / 'logs'
    return Path(os.environ.get('TMPDIR', '/Volumes/SSD/CIBO/tmp')) / 'cibo_logs'


def _limpa(linhas):
    return [l.rsplit('\r', 1)[-1].rstrip() for l in linhas if l.rsplit('\r', 1)[-1].strip()]


def resumo(linhas, codigo, log):
    linhas = _limpa(linhas)
    if codigo:
        return [f'FALHA (código {codigo}) — log completo: {log}'] + linhas[-ERRO:]
    if len(linhas) <= MAX:
        return linhas
    imp = [l for l in linhas[:-5] if IMPORTA.search(l)][-(MAX - 6):]
    return imp + linhas[-5:] + [f'({len(linhas)} linhas; log completo: {log})']


def curta():
    if os.environ.get('CIBO_VERBOSO') == '1' or os.environ.get('_CIBO_CURTO') == '1':
        return
    pasta = _pasta_log()
    pasta.mkdir(parents=True, exist_ok=True)
    log = pasta / f"{Path(sys.argv[0]).stem}_{time.strftime('%Y%m%d-%H%M%S')}_{os.getpid()}.log"
    env = dict(os.environ, _CIBO_CURTO='1', PYTHONUNBUFFERED='1')
    with open(log, 'w') as f:
        f.write('$ ' + ' '.join(sys.argv) + '\n'); f.flush()
        p = subprocess.Popen([sys.executable, *sys.argv], stdout=f, stderr=subprocess.STDOUT, env=env)
        for s in (signal.SIGTERM, signal.SIGINT):   # quem mata o pai (lote.py, Ctrl-C) leva o filho junto
            signal.signal(s, lambda sig, frm: (p.send_signal(sig), None))
        codigo = p.wait()
    linhas = open(log, errors='replace').read().splitlines()[1:]
    print('\n'.join(resumo(linhas, codigo, log)), file=sys.stderr if codigo else sys.stdout, flush=True)
    os._exit(codigo if codigo >= 0 else 128 - codigo)
