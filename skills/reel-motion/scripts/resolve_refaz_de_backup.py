#!/usr/bin/env python3
"""Refaz timelines do Resolve a partir de um .drt de backup, numa importação só (Andreia 20/10/2026).
Cada ciclo exportar→importar .drt soma 1 ao GlobalIn do MediaIn1 das camadas de ajuste (Fusion); com 1 ou 2 o render
falha ("The Fusion composition at 00:00:00:02 could not be processed successfully") e a API não grava esse valor.
Então: nunca encadeie ciclos de .drt na mesma timeline; parta do backup, aplique as edições no XML e importe uma vez.
Aplica o edita() do resolve_refaz_audio (SFX só nas trocas, volumes, MediaRef do trecho offline), troca o bruto .mp4 pela
cópia em 29,97 (_2997/*.mov) e recoloca o que ficar offline com a mídia certa (copiando Pan/Zoom/Rotation do vizinho).
uso: resolve_refaz_de_backup.py BACKUP.drt "NOME DA TIMELINE" […pares]   (projeto aberto no Resolve)"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import re, shutil, sys, tempfile, unicodedata, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from resolve_refaz_audio import edita, dvr
from resolve_cores import aplica

nfc = lambda x: unicodedata.normalize('NFC', x)
PROPS = ('Scaling', 'Pan', 'Tilt', 'ZoomX', 'ZoomY', 'RotationAngle', 'FlipX', 'FlipY', 'CropLeft', 'CropRight', 'CropTop', 'CropBottom')


def itens(t, ty='video'):
    return [(k, it) for k in range(1, t.GetTrackCount(ty) + 1) for it in t.GetItemListInTrack(ty, k) or []]


def globalin(t):
    return [int(it.GetFusionCompByIndex(1).FindTool('MediaIn1').GetInput('GlobalIn')) for _, it in itens(t) if it.GetFusionCompCount()]


def religa(mp, t, bruto):
    """bruto .mp4 → .mov 29,97; clipe sem mídia na faixa do bruto volta com o item certo"""
    for _, it in itens(t):
        m = it.GetMediaPoolItem(); fp = m.GetClipProperty('File Path') if m else ''
        mm = re.match(r'(.*/01_sources/)([^/]+)\.(?:mp4|MP4|mov|MOV)$', fp or '')
        if mm and Path(mm.group(1) + '_2997/' + mm.group(2) + '.mov').exists(): m.ReplaceClip(mm.group(1) + '_2997/' + mm.group(2) + '.mov')
    off = 0
    for ty, mt in (('video', 1), ('audio', 2)):                 # o áudio da câmera (A1) também fica offline no último trecho
        for k, it in itens(t, ty):
            if it.GetMediaPoolItem() or it.GetFusionCompCount() or not it.GetName().startswith('v0'): continue
            # vizinho pela faixa e pelo bruto (o nome muda de .mp4 para .mov); sem isso o clipe perde o RotationAngle 90 do iPhone
            # e sai deitado (02/03 da Andreia, 20/10/2026). O Pan de cada trecho vem do timeline.fcpxml do pacote (position × 34,14 com Scaling 1; o clipe recolocado entra com Scaling 0 e fica pequeno se não copiar).
            viz = [x for kk, x in itens(t, ty) if kk == k and x.GetMediaPoolItem() and x.GetName()[:8] == it.GetName()[:8]]
            m = viz[-1].GetMediaPoolItem() if viz else bruto
            st, du, lo = it.GetStart(), it.GetDuration(), it.GetLeftOffset()
            pr = {p: viz[-1].GetProperty(p) for p in PROPS} if viz and ty == 'video' else {}
            t.DeleteClips([it])
            novo = mp.AppendToTimeline([{'mediaPoolItem': m, 'startFrame': lo, 'endFrame': lo + du, 'recordFrame': st, 'trackIndex': k, 'mediaType': mt}])
            for p, v in pr.items(): novo[0].SetProperty(p, v)
            off += 1
    return off


def mpis(mp):
    """todos os itens do media pool por caminho (NFC)"""
    out, pilha = {}, [mp.GetRootFolder()]
    while pilha:
        fo = pilha.pop(); pilha += fo.GetSubFolderList() or []
        for c in fo.GetClipList() or []:
            fp = c.GetClipProperty('File Path')
            if fp: out[nfc(fp)] = c
    return out


def pacote_certo(mp, t, nome):
    """o Resolve junta arquivos de mesmo nome entre pacotes (voz.wav do 03 tocando o do 01, Andreia 20/10/2026):
    cada clipe de 07_davinci/<outro pacote>/ volta para o arquivo do próprio pacote, mesmo lugar e trecho"""
    todos, n = mpis(mp), 0
    for ty, mt in (('video', 1), ('audio', 2)):
        for k, it in itens(t, ty):
            m = it.GetMediaPoolItem(); fp = nfc(m.GetClipProperty('File Path')) if m else ''
            if '/07_davinci/' not in fp: continue
            base, resto = fp.split('/07_davinci/'); pac, rel = resto.split('/', 1)
            if pac == nfc(nome): continue
            certo = f'{base}/07_davinci/{nfc(nome)}/{rel}'
            if not Path(certo).exists(): print('  sem', certo); continue
            novo_m = todos.get(certo) or (mp.ImportMedia([certo]) or [None])[0]
            if not novo_m: print('  não importou', certo); continue
            todos[certo] = novo_m
            st, du, lo = it.GetStart(), it.GetDuration(), it.GetLeftOffset()
            t.DeleteClips([it])
            ok = mp.AppendToTimeline([{'mediaPoolItem': novo_m, 'startFrame': lo, 'endFrame': lo + du, 'recordFrame': st, 'trackIndex': k, 'mediaType': mt}])
            n += bool(ok)
    return n


def recarrega(mp, t, fins=('titulo_lower', 'capa')):
    """arquivo regravado no lugar (ex.: nome corrigido no lower e na capa): o item do media pool relê o disco"""
    feitos = set()
    for _, it in itens(t):
        m = it.GetMediaPoolItem(); fp = m.GetClipProperty('File Path') if m else ''
        if re.sub(r'__[^/]*$', '', Path(fp).stem) in fins and fp not in feitos: m.ReplaceClip(fp); feitos.add(fp)
    return len(feitos)


if __name__ == '__main__':
    a = sys.argv[1:]; pares = list(zip(a[::2], a[1::2]))
    r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    tl_de = lambda nome: next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if nfc(p.GetTimelineByIndex(i).GetName()) == nfc(nome)), None)
    for drt, nome in pares:
        tmp = Path(tempfile.mkdtemp()); d = tmp / 'x'; zipfile.ZipFile(drt).extractall(d); seq = next((d / 'SeqContainer').glob('*.xml'))
        s, info, _ = edita(seq.read_text(encoding='utf-8')); seq.write_text(s, encoding='utf-8')
        with zipfile.ZipFile(tmp / 'b.drt', 'w', zipfile.ZIP_DEFLATED) as z:
            for f in d.rglob('*'):
                if f.is_file(): z.write(f, f.relative_to(d))
        velha = tl_de(nome); velha.SetName(nfc(nome) + ' (antiga)')
        bruto = next((it.GetMediaPoolItem() for _, it in itens(velha) if it.GetMediaPoolItem() and '/_2997/' in (it.GetMediaPoolItem().GetClipProperty('File Path') or '')), None)
        novo = mp.ImportTimelineFromFile(str(tmp / 'b.drt'), {'timelineName': nome}); assert novo, 'importação .drt falhou'
        novo.SetName(nome); p.SetCurrentTimeline(novo)
        info['religados'] = religa(mp, novo, bruto)
        info['pacote'] = pacote_certo(mp, novo, nome); info['recarregados'] = recarrega(mp, novo)
        resto = [it.GetName() for ty in ('video', 'audio') for _, it in itens(novo, ty) if not it.GetMediaPoolItem() and not it.GetFusionCompCount()]
        info['GlobalIn'] = sorted(set(globalin(novo))); info['offline'] = resto[:3]
        if not resto and info['GlobalIn'] == [0]: mp.DeleteTimelines([velha])
        aplica(novo); shutil.rmtree(tmp, ignore_errors=True)
        print(f'{nome[:45]}: {info}', flush=True)
    r.GetProjectManager().SaveProject()
