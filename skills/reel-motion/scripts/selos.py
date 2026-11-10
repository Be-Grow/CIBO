"""Selos do motor (10/11/2026): cada portão que passa grava a impressão digital do que conferiu. A etapa seguinte só anda
com o selo valendo para os arquivos de AGORA — "pronto" deixa de ser palavra do agente e vira fato no disco.
Portões: cortes (segs.json), layout (props.json), audio (segs + sfx + trilha), pacote (tudo acima).
uso no reel.py: selos.grava(W, 'layout', [props]) · selos.vale(W, 'layout', [props]) · selos.resumo(W, {...})"""
import hashlib, json, time
from pathlib import Path

ORDEM = ('cortes', 'layout', 'audio', 'pacote')
COMO = {'cortes': 'cortes', 'layout': 'verifica', 'audio': 'mix', 'pacote': 'davinci'}   # etapa do reel.py que dá cada selo


def digital(arqs):
    h = hashlib.sha1()
    for a in arqs:
        a = Path(a); h.update(a.name.encode()); h.update(a.read_bytes() if a.exists() else b'<falta>')
    return h.hexdigest()


def _le(W):
    f = Path(W) / 'work' / 'selos.json'
    return json.load(open(f)) if f.exists() else {}


def grava(W, nome, arqs, nota=''):
    s = _le(W); s[nome] = {'id': digital(arqs), 'quando': time.strftime('%d/%m %H:%M'), 'nota': nota}
    (Path(W) / 'work').mkdir(exist_ok=True); json.dump(s, open(Path(W) / 'work' / 'selos.json', 'w'), ensure_ascii=False, indent=1)


def tira(W, nome):
    s = _le(W)
    if s.pop(nome, None) is not None:
        json.dump(s, open(Path(W) / 'work' / 'selos.json', 'w'), ensure_ascii=False, indent=1)


def vale(W, nome, arqs):
    s = _le(W).get(nome)
    return bool(s) and s['id'] == digital(arqs)


def estado(W, entradas):
    """{'cortes': 'ok 10/11 15:02' | 'velho' (arquivo mudou depois do selo) | 'falta'} para cada portão em entradas"""
    s = _le(W); out = {}
    for n in ORDEM:
        if n not in entradas:
            continue
        out[n] = 'falta' if n not in s else (f"ok {s[n]['quando']}" if s[n]['id'] == digital(entradas[n]) else 'velho')
    return out
