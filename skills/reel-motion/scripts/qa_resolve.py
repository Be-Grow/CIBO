#!/usr/bin/env python3
"""Auditoria das timelines no Resolve antes de dizer "pronto" (Andrea, 20/10/2026: o editor achou na tela, um por um,
offline, trecho deitado, trecho pequeno com faixa preta, áudio de outro vídeo e render falhando no Fusion).
Por timeline: clipe sem mídia, arquivo de 07_davinci/ vindo de OUTRO pacote (o Resolve junta arquivos de mesmo nome),
clipe do bruto com Scaling/RotationAngle diferente dos irmãos, GlobalIn do MediaIn1 ≠ 0 nas camadas de ajuste (o render
falha no Fusion). Rode com o render parado (durante o render a API devolve propriedades vazias).
uso: qa_resolve.py [trecho do nome da timeline …]   (sem argumento: todas, menos a do editor)   sai 1 se achar problema"""
import sys, unicodedata
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
import DaVinciResolveScript as dvr

nfc = lambda x: unicodedata.normalize('NFC', x)


def itens(t, ty='video'):
    return [(k, it) for k in range(1, t.GetTrackCount(ty) + 1) for it in t.GetItemListInTrack(ty, k) or []]


def audita(t):
    n, prob = nfc(t.GetName()), []
    for ty in ('video', 'audio'):
        for k, it in itens(t, ty):
            m = it.GetMediaPoolItem(); fp = nfc(m.GetClipProperty('File Path')) if m else ''
            if not m and not it.GetFusionCompCount():
                prob.append(f'{ty}{k} {it.GetName()[:30]}: sem mídia (offline)')
            if '/07_davinci/' in fp and fp.split('/07_davinci/')[1].split('/')[0] != n:
                prob.append(f'{ty}{k} {fp.split("/")[-1]}: arquivo de outro pacote ({fp.split("/07_davinci/")[1].split("/")[0][:30]})')
    bruto = [it for _, it in itens(t) if it.GetMediaPoolItem() and '/01_sources/' in (it.GetMediaPoolItem().GetClipProperty('File Path') or '')]
    for p in ('Scaling', 'RotationAngle'):
        v = [it.GetProperty(p) for it in bruto]
        if len(set(map(str, v))) > 1:
            prob.append(f'bruto com {p} diferente entre os trechos: {v}')
    g = [int(it.GetFusionCompByIndex(1).FindTool('MediaIn1').GetInput('GlobalIn')) for _, it in itens(t) if it.GetFusionCompCount()]
    if any(g):
        prob.append(f'GlobalIn do Fusion {sorted(set(g))} (render vai falhar; refaça com resolve_refaz_de_backup.py)')
    return prob


if __name__ == '__main__':
    p = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
    if p.IsRenderingInProgress():
        sys.exit('render em andamento: a API não lê as propriedades agora')
    filtro = [nfc(a) for a in sys.argv[1:]]; ruim = 0
    for i in range(1, p.GetTimelineCount() + 1):
        t = p.GetTimelineByIndex(i); n = nfc(t.GetName())
        if 'teste do editor' in n or (filtro and not any(f in n for f in filtro)): continue
        prob = audita(t); ruim += bool(prob)
        print(f'{"OK " if not prob else "ERRO"} {n}')
        for x in prob: print('     ', x)
    sys.exit(1 if ruim else 0)
