#!/usr/bin/env python3
"""Trava "o que o editor mexeu é dele" (23/11/2026). Correção de processo mais repetida do feedback: a CIBO apagou ou
reimportou timeline que o editor já tinha ajustado ("apagou as timelines que eu já tinha mexido").

Como funciona: toda timeline que a CIBO monta ou refaz ganha uma ASSINATURA (faixas, clipes, posição, corte e transform de
cada clipe), gravada em ~/.cibo/timelines_cibo.json. Antes de apagar ou substituir uma timeline, a CIBO compara:
  - assinatura igual        -> a timeline é como a CIBO deixou: pode apagar/refazer;
  - assinatura diferente    -> o editor mexeu: PARA e avisa;
  - timeline sem assinatura -> não foi a CIBO que montou (ou é de antes desta trava): é do editor, PARA e avisa.
Liberar uma vez, só depois de perguntar ao editor: CIBO_EDITOR_OK=1 na frente do comando.
Cor de grade (página Color) não entra na assinatura: a API não lê o grade. Corte, posição, zoom e Fusion entram.

Como biblioteca (não importa o Resolve; recebe os objetos):
    import guarda_editor as G
    G.marca(p, tl)                      # logo depois de a CIBO montar/refazer a timeline
    G.apaga(mp, p, tl, 'reimportação')  # no lugar de mp.DeleteTimelines([tl])
    G.editor_mexeu(p, tl) -> (bool, motivo)"""
import hashlib, json, os
from pathlib import Path

REG = Path(os.environ.get('CIBO_TIMELINES', Path.home() / '.cibo' / 'timelines_cibo.json'))
PROPS = ('Pan', 'Tilt', 'ZoomX', 'ZoomY', 'RotationAngle', 'AnchorPointX', 'AnchorPointY', 'CropLeft', 'CropRight',
         'CropTop', 'CropBottom', 'Opacity', 'FlipX', 'FlipY', 'CompositeMode')


class EditorMexeu(SystemExit):
    pass


def _f(fn, *a, padrao=None):
    try:
        return fn(*a)
    except Exception:
        return padrao


def assinatura(tl):
    linhas = []
    for ty in ('video', 'audio', 'subtitle'):
        n = _f(tl.GetTrackCount, ty, padrao=0) or 0
        linhas.append(f'{ty}:{n}')
        for k in range(1, n + 1):
            for it in _f(tl.GetItemListInTrack, ty, k, padrao=[]) or []:
                pr = {}
                if ty == 'video':
                    for nome in PROPS:
                        v = _f(it.GetProperty, nome)
                        if v is not None: pr[nome] = round(v, 4) if isinstance(v, float) else v
                linhas.append(json.dumps([ty, k, _f(it.GetName), _f(it.GetStart), _f(it.GetEnd), _f(it.GetLeftOffset),
                                          _f(it.GetFusionCompCount, padrao=0), pr], sort_keys=True, ensure_ascii=False))
    return hashlib.sha1('\n'.join(linhas).encode()).hexdigest()


def _chave(p, tl):
    return f'{_f(p.GetName, padrao="?")}::{_f(tl.GetUniqueId, padrao=None) or _f(tl.GetName)}'


def _le():
    try:
        return json.loads(REG.read_text())
    except (FileNotFoundError, ValueError):
        return {}


def _grava(d):
    REG.parent.mkdir(parents=True, exist_ok=True)
    tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1)); os.replace(tmp, REG)


def marca(p, tl):
    """a CIBO acabou de montar/refazer esta timeline: guarda a assinatura"""
    d = _le(); d[_chave(p, tl)] = {'nome': _f(tl.GetName), 'assinatura': assinatura(tl)}; _grava(d)


def editor_mexeu(p, tl):
    rec = _le().get(_chave(p, tl))
    if not rec:
        return True, 'timeline sem assinatura da CIBO (montada pelo editor ou antes desta trava)'
    if rec['assinatura'] != assinatura(tl):
        return True, 'o editor mexeu depois que a CIBO montou (clipes, cortes, posição ou Fusion mudaram)'
    return False, ''


def pode_mexer(p, tl, acao):
    """True se pode; senão imprime o motivo e devolve False (para quem prefere pular a timeline em vez de parar)"""
    mexeu, motivo = editor_mexeu(p, tl)
    if not mexeu or os.environ.get('CIBO_EDITOR_OK') == '1':
        return True
    print(f'!! NÃO {acao} "{_f(tl.GetName)}": {motivo}. Pergunte ao editor; liberar: CIBO_EDITOR_OK=1 na frente do comando.', flush=True)
    return False


def apaga(mp, p, tl, acao='apago'):
    """apaga só timeline que está como a CIBO deixou; senão para o script (EditorMexeu)"""
    nome = _f(tl.GetName)
    if not pode_mexer(p, tl, acao):
        raise EditorMexeu(f'parado para não apagar trabalho do editor em "{nome}"')
    ok = mp.DeleteTimelines([tl])
    d = _le(); d.pop(_chave(p, tl), None); _grava(d)
    return ok
