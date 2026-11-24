#!/usr/bin/env python3
"""Lê o padrão de edição de um cliente a partir de um projeto do DaVinci (editor, 24/11/2026: "se o editor tiver projetos do
davinci, ele pode alimentar a cibo com eles"). QUEM RODA É A CIBO (aprende.py chama sozinho para .drp na entrada ou "davinci:…").

uso: le_davinci.py --drp ARQ.drp --out PASTA          projeto exportado (.drp): importa num projeto temporário e apaga no fim
     le_davinci.py --projeto "Pasta/Sub/Nome" --out PASTA   projeto que já está no banco do Resolve: só lê, nunca salva
     opções: --timeline NOME (só essa; padrão: todas)  --sem-xml (não exporta FCPXML de cada timeline)

Saída em PASTA: leitura.json (tudo, clipe a clipe), padrao.json (resumo agregado) e padrao.md (ficha em português);
timelines/*.fcpxml de registro. O projeto que o editor tinha aberto volta a ficar aberto no fim, mesmo com erro.
O que lê (doc local `doc_resolve.py api`; Text+ pelo fórum da Blackmagic, ver regras/davinci.md 24/11/2026):
  timeline: resolução, fps, duração, faixas com nome; clipe: tempo, Pan/Tilt/Zoom/Crop/Opacity, cor, arquivo de mídia;
  títulos Text+ (comp do Fusion): texto, fonte, estilo, tamanho, cor, posição; ferramentas do Fusion usadas.
"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.dirname(_o.path.realpath(__file__))); import saida_curta; saida_curta.curta()
import argparse, json, os, re, statistics as st, sys, time, unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'reel-motion' / 'scripts'))
import fusion_kit as K   # noqa: E402

PASTA_TMP = 'CIBO leitura'          # pasta do Project Manager onde o .drp entra (apagada no fim se ficar vazia)
PROPS = ('Pan', 'Tilt', 'ZoomX', 'ZoomY', 'RotationAngle', 'CropLeft', 'CropRight', 'CropTop', 'CropBottom', 'Opacity',
         'CompositeMode', 'FlipX', 'FlipY')
TXT_IN = ('StyledText', 'Font', 'Style', 'Size', 'Red1', 'Green1', 'Blue1', 'Center', 'CharacterSpacing', 'LineSpacing')
nfc = lambda s: unicodedata.normalize('NFC', s or '')


# ---------------------------------------------------------------- Project Manager
def caminho_do(pm, nome):
    """pasta (lista) onde o projeto `nome` mora, para devolver o editor ao lugar certo"""
    def busca(cam):
        if nome in (pm.GetProjectListInCurrentFolder() or []): return cam
        for f in pm.GetFolderListInCurrentFolder() or []:
            pm.OpenFolder(f); x = busca(cam + [f])
            if x is not None: return x
            pm.GotoParentFolder()
    pm.GotoRootFolder(); return busca([])


def vai_para(pm, cam, cria=False):
    pm.GotoRootFolder()
    for f in cam:
        if f not in (pm.GetFolderListInCurrentFolder() or []):
            assert cria, f'pasta não existe no Project Manager: {"/".join(cam)}'
            pm.CreateFolder(f)
        assert pm.OpenFolder(f), f'não abriu a pasta {f}'


# ---------------------------------------------------------------- leitura
def num(v):
    try: return round(float(v), 4)
    except (TypeError, ValueError): return v


def le_texto(tool):
    d = {}
    for k in TXT_IN:
        try: v = tool.GetInput(k)
        except Exception: v = None
        if v is None: continue
        if isinstance(v, dict): v = [num(v[i]) for i in sorted(v) if isinstance(i, (int, float))]
        d[k] = num(v) if not isinstance(v, (str, list)) else v
    if all(k in d for k in ('Red1', 'Green1', 'Blue1')):
        d['cor'] = '#' + ''.join(f'{max(0, min(255, round(float(d[k]) * 255))):02X}' for k in ('Red1', 'Green1', 'Blue1'))
    return d


def le_comps(it):
    out = []
    for i in range(1, (it.GetFusionCompCount() or 0) + 1):
        comp = it.GetFusionCompByIndex(i)
        if not comp: continue
        ferr, textos = [], []
        for t in (comp.GetToolList(False) or {}).values():
            tipo = (t.GetAttrs() or {}).get('TOOLS_RegID', '?')
            ferr.append(tipo)
            if tipo in ('TextPlus', 'Text3D'): textos.append(le_texto(t))
        out.append({'ferramentas': sorted(ferr), 'textos': textos})
    return out


def le_item(it, f, tipo):
    s, e = it.GetStart(), it.GetEnd()
    d = {'nome': it.GetName(), 'ini': round(s / f, 3), 'dur': round((e - s) / f, 3), 'cor': it.GetClipColor() or ''}
    mi = it.GetMediaPoolItem()
    if mi:
        d['arquivo'] = mi.GetClipProperty('File Path') or mi.GetClipProperty('File Name') or ''
    if tipo == 'video':
        for k in PROPS:
            try: v = it.GetProperty(k)
            except Exception: v = None
            if v is not None: d[k] = num(v)
        c = le_comps(it)
        if c: d['fusion'] = c
    return d


def le_timeline(tl):
    f = K.fps(tl); ini = tl.GetStartFrame()
    T = {'nome': tl.GetName(), 'fps': f, 'largura': int(tl.GetSetting('timelineResolutionWidth') or 0),
         'altura': int(tl.GetSetting('timelineResolutionHeight') or 0),
         'dur': round((tl.GetEndFrame() - ini) / f, 2), 'faixas': []}
    for tipo in ('video', 'audio', 'subtitle'):
        for i in range(1, (tl.GetTrackCount(tipo) or 0) + 1):
            its = []
            for it in tl.GetItemListInTrack(tipo, i) or []:
                d = le_item(it, f, tipo); d['ini'] = round(d['ini'] - ini / f, 3); its.append(d)
            T['faixas'].append({'tipo': tipo, 'n': i, 'nome': tl.GetTrackName(tipo, i), 'itens': its})
    return T


# ---------------------------------------------------------------- resumo
VID_EXT = {'.mp4', '.mov', '.mxf', '.braw', '.r3d', '.m4v', '.avi', '.mts'}
sem_acento = lambda s: ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower()) if unicodedata.category(c) != 'Mn')


def tipo_audio(faixa, it):
    """voz, trilha ou sfx: primeiro pelo nome da faixa (o editor nomeia), depois pelo arquivo e pela duração"""
    n = sem_acento(faixa)
    if re.search(r'trilha|music|bgm|\bbg\b|fundo', n): return 'trilha'
    if re.search(r'sfx|\bfx\b|efeito|whoosh|foley', n): return 'sfx'
    if re.search(r'voz|voice|dialog|fala|camera|cam\b|ref|locu|mic', n): return 'voz'
    if Path(it.get('arquivo', '')).suffix.lower() in VID_EXT: return 'voz'
    return 'trilha' if it['dur'] >= 20 else 'sfx'


def eh_legenda(faixa):
    return bool(re.search(r'legenda|caption|subtit|sub\b|\bcc\b', sem_acento(faixa)))


def resumo(tls):
    fontes, tamanhos, cores, ys, exemplos, ferr = Counter(), [], Counter(), [], [], Counter()
    zooms, cortes, audios, res, camadas, leg_dur = [], [], {'voz': Counter(), 'trilha': Counter(), 'sfx': Counter()}, Counter(), Counter(), []
    for T in tls:
        res[f'{T["largura"]}x{T["altura"]} @ {T["fps"]:g} fps'] += 1
        vids = [x for x in T['faixas'] if x['tipo'] == 'video' and x['itens']]
        # câmera = faixa de vídeo mais baixa com mídia de vídeo de verdade (bruto), não gráfico/legenda
        cam = next((x for x in vids if not eh_legenda(x['nome'])
                    and any(Path(i.get('arquivo', '')).suffix.lower() in VID_EXT and i['dur'] > 1 for i in x['itens'])), None)
        if cam and T['dur'] > 0:
            cortes.append(len(cam['itens']) / (T['dur'] / 60))
            zooms += [i['ZoomX'] for i in cam['itens'] if isinstance(i.get('ZoomX'), (int, float))]
        for fx in T['faixas']:
            if fx['itens']: camadas[(fx['tipo'], fx['nome'] or f'{fx["tipo"]} {fx["n"]}')] += len(fx['itens'])
            if fx['tipo'] == 'subtitle' or (fx['tipo'] == 'video' and eh_legenda(fx['nome'])):
                leg_dur += [i['dur'] for i in fx['itens']]
            for it in fx['itens']:
                if fx['tipo'] == 'video':
                    for c in it.get('fusion', []):
                        ferr.update(c['ferramentas'])
                        for t in c['textos']:
                            if t.get('Font'): fontes[(t['Font'] + ' ' + str(t.get('Style', ''))).strip()] += 1
                            if isinstance(t.get('Size'), (int, float)): tamanhos.append(t['Size'])
                            if t.get('cor'): cores[t['cor']] += 1
                            if isinstance(t.get('Center'), list) and len(t['Center']) > 1: ys.append(t['Center'][1])
                            if t.get('StyledText') and len(exemplos) < 12: exemplos.append(t['StyledText'][:80])
                elif fx['tipo'] == 'audio' and it.get('arquivo'):
                    audios[tipo_audio(fx['nome'], it)][Path(it['arquivo']).name] += 1
    md = lambda xs: round(st.median(xs), 3) if xs else None
    return {'timelines': len(tls), 'formatos': dict(res),
            'camadas': [{'tipo': k[0], 'faixa': k[1], 'clipes': v} for k, v in camadas.items()],
            'legenda_blocos': len(leg_dur), 'legenda_dur_mediana': md(leg_dur),
            'fontes_titulos': dict(fontes.most_common(8)), 'tamanho_titulo_mediana': md(tamanhos),
            'cores_texto': dict(cores.most_common(8)), 'altura_texto_mediana': md(ys), 'exemplos_texto': exemplos,
            'ferramentas_fusion': dict(ferr.most_common(12)), 'zoom_camera_mediana': md(zooms),
            'cortes_por_min_mediana': round(st.median(cortes), 1) if cortes else None,
            'trilhas': sorted(audios['trilha']), 'sfx_mais_usados': dict(audios['sfx'].most_common(10)),
            'voz': sorted(audios['voz'])}


def ficha(nome, R):
    L = [f'# Padrão lido do projeto do DaVinci "{nome}"', '',
         f'{R["timelines"]} timeline(s): ' + ', '.join(f'{k} ({v})' for k, v in R['formatos'].items()) + '.', '',
         '## Camadas usadas', '']
    L += [f'- {c["faixa"]} ({"vídeo" if c["tipo"] == "video" else "áudio" if c["tipo"] == "audio" else "legenda"}): {c["clipes"]} clipe(s)'
          for c in R['camadas']]
    L.append('')
    if R['legenda_blocos']:
        L += [f'Legenda: {R["legenda_blocos"]} blocos, {R["legenda_dur_mediana"]:.1f} s cada (mediana).', '']
    if R['fontes_titulos']:
        L += ['## Títulos (Text+)', '', '- Fontes: ' + ', '.join(f'{k} ({v}×)' for k, v in R['fontes_titulos'].items())]
        if R['tamanho_titulo_mediana'] is not None: L.append(f'- Tamanho mais comum: {R["tamanho_titulo_mediana"]}')
        if R['cores_texto']: L.append('- Cores do texto: ' + ', '.join(f'{k} ({v}×)' for k, v in R['cores_texto'].items()))
        if R['altura_texto_mediana'] is not None:
            y = R['altura_texto_mediana']; L.append(f'- Altura do texto na tela: {y:.2f} (0 = pé, 1 = topo; '
                                                    + ('parte de baixo' if y < 0.4 else 'meio' if y < 0.6 else 'parte de cima') + ')')
        if R['exemplos_texto']: L.append('- Exemplos: ' + ' | '.join(R['exemplos_texto'][:6]))
        L.append('')
    else:
        L += ['Nenhum título Text+ (texto feito no DaVinci). Se há legenda, ela veio pronta em arquivo (veja as camadas).', '']
    L += ['## Montagem', '']
    if R['cortes_por_min_mediana'] is not None: L.append(f'- Cortes por minuto na câmera: {R["cortes_por_min_mediana"]}')
    if R['zoom_camera_mediana'] is not None: L.append(f'- Zoom típico da câmera: {R["zoom_camera_mediana"]}')
    if R['ferramentas_fusion']: L.append('- Efeitos do Fusion usados: ' + ', '.join(f'{k} ({v}×)' for k, v in R['ferramentas_fusion'].items()))
    L += ['', '## Som', '']
    L.append('- Trilhas: ' + (', '.join(R['trilhas']) if R['trilhas'] else 'nenhuma'))
    L.append('- SFX: ' + (', '.join(f'{k} ({v}×)' for k, v in R['sfx_mais_usados'].items()) if R['sfx_mais_usados'] else 'nenhum'))
    return '\n'.join(L) + '\n'


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--drp', type=Path); g.add_argument('--projeto')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--timeline'); ap.add_argument('--sem-xml', action='store_true')
    a = ap.parse_args()
    out = a.out; (out / 'timelines').mkdir(parents=True, exist_ok=True)

    r, pm, cur = K.resolve()
    ant = cur.GetName() if cur else None
    if ant and ant.startswith('Untitled Project'): ant = None     # Untitled: não salva nem devolve (prende a API)
    if ant: K.salva(pm)
    cam_ant = caminho_do(pm, ant) if ant else None
    tmp_nome, tmp_cam = None, [PASTA_TMP]
    try:
        if a.drp:
            assert a.drp.exists(), f'não achei {a.drp}'
            vai_para(pm, tmp_cam, cria=True)
            tmp_nome = f'leitura {time.strftime("%Y%m%d-%H%M%S")}'
            assert pm.ImportProject(str(a.drp.resolve()), tmp_nome), f'ImportProject recusou {a.drp} (versão do Resolve mais antiga que a do projeto?)'
            p = pm.LoadProject(tmp_nome); nome = a.drp.stem
        else:
            partes = [x for x in a.projeto.split('/') if x]
            vai_para(pm, partes[:-1]); nome = partes[-1]
            assert nome in (pm.GetProjectListInCurrentFolder() or []), f'projeto não achado: {a.projeto}'
            p = pm.LoadProject(nome)
        assert p, f'não abriu o projeto {nome} (janelas: {K.dialogos()})'
        tls = []
        for tl in K.timelines(p):
            if a.timeline and nfc(tl.GetName()) != nfc(a.timeline): continue
            p.SetCurrentTimeline(tl)
            T = le_timeline(tl); tls.append(T)
            if not a.sem_xml:
                arq = out / 'timelines' / (re.sub(r'[\\/:*?"<>|]', '_', tl.GetName()) + '.fcpxml')
                T['fcpxml'] = str(arq) if tl.Export(str(arq), r.EXPORT_FCPXML_1_10, r.EXPORT_NONE) else None
            print(f'  {tl.GetName()}: {sum(len(x["itens"]) for x in T["faixas"])} clipes em {len(T["faixas"])} faixas')
        assert tls, 'nenhuma timeline lida' + (f' com o nome {a.timeline}' if a.timeline else '')
        R = resumo(tls)
        (out / 'leitura.json').write_text(json.dumps({'projeto': nome, 'timelines': tls}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        (out / 'padrao.json').write_text(json.dumps(R, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        (out / 'padrao.md').write_text(ficha(nome, R), encoding='utf-8')
        print(f'padrão: {out / "padrao.md"}')
    finally:   # devolve o editor ao projeto dele e apaga o temporário, aconteça o que acontecer
        if ant:
            vai_para(pm, cam_ant or []); pm.LoadProject(ant)
        elif pm.GetCurrentProject():
            pm.CloseProject(pm.GetCurrentProject())        # sem projeto do editor para voltar: só fecha o lido
        if tmp_nome:                                       # o temporário só sai depois de fechado (DeleteProject recusa o aberto)
            vai_para(pm, tmp_cam)
            if not pm.DeleteProject(tmp_nome):
                print(f'AVISO: não apaguei o projeto temporário "{PASTA_TMP}/{tmp_nome}"; apague no Project Manager')
            vazia = not pm.GetProjectListInCurrentFolder() and not pm.GetFolderListInCurrentFolder()
            pm.GotoRootFolder()
            if vazia: pm.DeleteFolder(PASTA_TMP)
        vai_para(pm, cam_ant or [])


if __name__ == '__main__':
    main()
