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
    G.editor_mexeu(p, tl) -> (bool, motivo)
    G.o_que_mudou(p, tl) -> ['V1 "r02" em 0:12.0: mudou o corte (8.0s → 6.5s)', …] ou None
Linha de comando (a CIBO roda antes de refazer; o editor nunca): guarda_editor.py [TIMELINE…] lista o que o editor mudou.
O que o editor mudou é dele: preserve, conte a ele e, se for ajuste que se repete, registre (feedback.py add / licao.py add)."""
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


def itens(tl):
    """a "foto" da timeline: faixas e, por clipe, nome, posição, corte, Fusion e transform"""
    fx = {'trilhas': {}, 'clipes': []}
    for ty in ('video', 'audio', 'subtitle'):
        n = _f(tl.GetTrackCount, ty, padrao=0) or 0
        fx['trilhas'][ty] = n
        for k in range(1, n + 1):
            for it in _f(tl.GetItemListInTrack, ty, k, padrao=[]) or []:
                pr = {}
                if ty == 'video':
                    for nome in PROPS:
                        v = _f(it.GetProperty, nome)
                        if v is not None: pr[nome] = round(v, 4) if isinstance(v, float) else v
                fx['clipes'].append([ty, k, _f(it.GetName), _f(it.GetStart), _f(it.GetEnd), _f(it.GetLeftOffset),
                                     _f(it.GetFusionCompCount, padrao=0), pr])
    return fx


def assinatura(tl, fx=None):
    fx = fx or itens(tl)
    linhas = [f'{ty}:{n}' for ty, n in fx['trilhas'].items()] + \
             [json.dumps(c, sort_keys=True, ensure_ascii=False) for c in fx['clipes']]
    return hashlib.sha1('\n'.join(linhas).encode()).hexdigest()


NOMES = {'video': 'vídeo', 'audio': 'áudio', 'subtitle': 'legenda'}
PROP_PT = {'Pan': 'posição horizontal', 'Tilt': 'posição vertical', 'ZoomX': 'zoom', 'ZoomY': 'zoom',
           'RotationAngle': 'rotação', 'AnchorPointX': 'ponto de âncora', 'AnchorPointY': 'ponto de âncora',
           'CropLeft': 'recorte', 'CropRight': 'recorte', 'CropTop': 'recorte', 'CropBottom': 'recorte',
           'Opacity': 'opacidade', 'FlipX': 'espelhamento', 'FlipY': 'espelhamento', 'CompositeMode': 'modo de mistura'}


def _tc(fr, fps):
    s = (fr or 0) / (fps or 30)
    return f'{int(s // 60)}:{s % 60:04.1f}'


def mudancas(antes, depois, fps=30):
    """o que o editor mudou, em português de edição (lista curta, para mostrar e para registrar)"""
    import difflib
    out = []
    for ty in ('video', 'audio', 'subtitle'):
        a, b = antes['trilhas'].get(ty, 0), depois['trilhas'].get(ty, 0)
        if a != b: out.append(f'faixas de {NOMES[ty]}: {a} → {b}')
    faixas = sorted({(c[0], c[1]) for c in antes['clipes'] + depois['clipes']})
    for ty, k in faixas:
        A = [c for c in antes['clipes'] if (c[0], c[1]) == (ty, k)]
        B = [c for c in depois['clipes'] if (c[0], c[1]) == (ty, k)]
        lugar = f"{ {'video': 'V', 'audio': 'A', 'subtitle': 'L'}[ty]}{k}"
        sm = difflib.SequenceMatcher(a=[c[2] for c in A], b=[c[2] for c in B], autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op in ('delete', 'replace'):
                for c in A[i1:i2]: out.append(f'{lugar}: tirou "{c[2]}" (estava em {_tc(c[3], fps)})')
            if op in ('insert', 'replace'):
                for c in B[j1:j2]: out.append(f'{lugar}: pôs "{c[2]}" em {_tc(c[3], fps)}')
            if op == 'equal':
                for ca, cb in zip(A[i1:i2], B[j1:j2]):
                    nome, d = cb[2], []
                    if ca[3] != cb[3]: d.append(f'moveu de {_tc(ca[3], fps)} para {_tc(cb[3], fps)}')
                    if (ca[4] - ca[3]) != (cb[4] - cb[3]) or ca[5] != cb[5]:
                        d.append(f'mudou o corte ({(ca[4] - ca[3]) / fps:.1f}s → {(cb[4] - cb[3]) / fps:.1f}s)')
                    if (ca[6] or 0) != (cb[6] or 0): d.append('mexeu no Fusion')
                    mud = sorted({PROP_PT.get(x, x) for x in set(ca[7]) | set(cb[7]) if ca[7].get(x) != cb[7].get(x)})
                    if mud: d.append('mudou ' + ', '.join(mud))
                    if d: out.append(f'{lugar} "{nome}" em {_tc(cb[3], fps)}: ' + '; '.join(d))
    return out


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
    """a CIBO acabou de montar/refazer esta timeline: guarda a assinatura e a foto (para saber depois O QUE o editor mudou)"""
    fx = itens(tl)
    d = _le(); d[_chave(p, tl)] = {'nome': _f(tl.GetName), 'assinatura': assinatura(tl, fx), 'foto': fx}; _grava(d)


def _fps(tl):
    try:
        return float(tl.GetSetting('timelineFrameRate'))
    except Exception:
        return 30.0


def o_que_mudou(p, tl):
    """lista do que o editor mudou desde que a CIBO montou; None = timeline sem foto (não foi a CIBO, ou é de antes)"""
    rec = _le().get(_chave(p, tl))
    if not rec or 'foto' not in rec:
        return None
    return mudancas(rec['foto'], itens(tl), _fps(tl))


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
    print(f'!! NÃO {acao} "{_f(tl.GetName)}": {motivo}.', flush=True)
    mud = o_que_mudou(p, tl)
    for m in (mud or [])[:8]: print('   - ' + m, flush=True)
    if mud and len(mud) > 8: print(f'   … e mais {len(mud) - 8}', flush=True)
    print('   Conte ao editor o que ele mudou, preserve, e refaça só o que ele pedir; liberar: CIBO_EDITOR_OK=1.', flush=True)
    return False


def apaga(mp, p, tl, acao='apago'):
    """apaga só timeline que está como a CIBO deixou; senão para o script (EditorMexeu)"""
    nome = _f(tl.GetName)
    if not pode_mexer(p, tl, acao):
        raise EditorMexeu(f'parado para não apagar trabalho do editor em "{nome}"')
    ok = mp.DeleteTimelines([tl])
    d = _le(); d.pop(_chave(p, tl), None); _grava(d)
    return ok


if __name__ == '__main__':
    # uso (a CIBO roda, nunca o editor): guarda_editor.py [NOME_DA_TIMELINE …]  → o que o editor mudou em cada timeline
    # da CIBO no projeto aberto (sem nome: todas). Rode ANTES de refazer qualquer coisa e conte ao editor em português.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent)); import fusion_kit as K
    r, _pm, p = K.resolve()                                   # fusion_kit.resolve() devolve (resolve, gerente, projeto aberto)
    nomes = sys.argv[1:]
    for i in range(1, p.GetTimelineCount() + 1):
        tl = p.GetTimelineByIndex(i)
        if nomes and tl.GetName() not in nomes: continue
        mud = o_que_mudou(p, tl)
        if mud is None:
            if nomes: print(f'{tl.GetName()}: sem foto da CIBO (montada pelo editor ou antes da trava): trate como do editor')
            continue
        print(f'{tl.GetName()}: ' + ('igual ao que a CIBO montou' if not mud else f'{len(mud)} mudança(s) do editor'))
        for m in mud[:15]: print('   - ' + m)
