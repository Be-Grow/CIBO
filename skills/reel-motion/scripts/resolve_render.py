#!/usr/bin/env python3
"""Importa pacotes do DaVinci (07_davinci/<nome>/timeline.fcpxml) num projeto NOVO do Resolve pela API e renderiza cada
timeline lá (prévia/entrega feita no próprio DaVinci; Andreia 19/10/2026: "tem como fazer a prévia no davinci?").
Render em MOV H.264 + LPCM (o AAC da API sai a 64 kb/s) e remonta o MP4 com AAC 256k; confere streams e duração.
Salva e fecha o projeto de trabalho e devolve o projeto que estava aberto (pela pasta dele).
SEM_RENDER=1: só importa e deixa o projeto novo aberto (editor finaliza; Andreia 19/10/2026).
uso: resolve_render.py "Nome do projeto" "Pasta/Sub" SAIDA_DIR pacote1 [pacote2 …]"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import os, re, subprocess, sys, time, json
from pathlib import Path
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
import DaVinciResolveScript as dvr

SEM = os.environ.get('SEM_RENDER') == '1'
NOME, PASTA, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3]).resolve(); PACS = [Path(p).resolve() for p in sys.argv[4:]]
r = dvr.scriptapp("Resolve"); pm = r.GetProjectManager()
cur = pm.GetCurrentProject(); ant = cur.GetName() if cur else None; pag = r.GetCurrentPage()

def caminho_do(nome):                       # pasta (lista) onde o projeto aberto mora, para devolver certo
    def busca(cam):
        if nome in (pm.GetProjectListInCurrentFolder() or []): return cam
        for f in pm.GetFolderListInCurrentFolder() or []:
            pm.OpenFolder(f); x = busca(cam + [f])
            if x is not None: return x
            pm.GotoParentFolder()
    pm.GotoRootFolder(); return busca([])

pm.SaveProject(); cam_ant = caminho_do(ant) if ant else None
try:
    pm.GotoRootFolder()
    for f in [x for x in PASTA.split('/') if x]:
        if f not in (pm.GetFolderListInCurrentFolder() or []): pm.CreateFolder(f)
        pm.OpenFolder(f)
    p = pm.LoadProject(NOME) if NOME in (pm.GetProjectListInCurrentFolder() or []) else pm.CreateProject(NOME)
    assert p, 'projeto não abriu'
    # fps e tamanho vêm do FCPXML do 1º pacote (aula "grosso" em 30 fps, João 21/10/2026); antes era fixo 29,97
    _fd = re.search(r'frameDuration="(\d+)/(\d+)s"', (PACS[0] / 'timeline.fcpxml').read_text(encoding='utf-8')) if PACS else None
    _fps = int(_fd[2]) / int(_fd[1]) if _fd else 30000 / 1001
    p.SetSetting("timelineFrameRate", "29.97" if abs(_fps - 29.97) < 0.01 else f'{_fps:g}')
    mp = p.GetMediaPool(); OUT.mkdir(parents=True, exist_ok=True)
    for pac in PACS:
        nome = pac.name; xml = pac / 'timeline.fcpxml'
        _f = re.search(r'<format [^>]*width="(\d+)" height="(\d+)"', xml.read_text(encoding='utf-8'))
        w, h = (int(_f[1]), int(_f[2])) if _f else ((1920, 1080) if '16x9' in nome else (1080, 1920))
        for i in range(p.GetTimelineCount(), 0, -1):          # reimportação: tira a timeline antiga de mesmo nome
            t = p.GetTimelineByIndex(i)
            if t and t.GetName() == nome: mp.DeleteTimelines([t])
        tl = mp.ImportTimelineFromFile(str(xml), {"timelineName": nome, "importSourceClips": True})
        if not tl:                                             # 2ª tentativa: mídia do pacote no pool antes do XML
            mp.ImportMedia([str(x) for x in sorted(pac.rglob('*')) if x.suffix.lower() in ('.mov', '.mp4', '.wav', '.png')])
            tl = mp.ImportTimelineFromFile(str(xml), {"timelineName": nome, "importSourceClips": False})
        if not tl: print(f'IMPORTAÇÃO FALHOU: {xml}', flush=True); continue
        tl.SetSetting("useCustomSettings", "1"); tl.SetSetting("timelineResolutionWidth", str(w)); tl.SetSetting("timelineResolutionHeight", str(h))
        v = tl.GetTrackCount("video"); a = tl.GetTrackCount("audio")
        itens = sum(len(tl.GetItemListInTrack("video", k) or []) for k in range(1, v + 1))
        print(f'{nome}: {v} faixas de vídeo, {a} de áudio, {itens} clipes; início {tl.GetStartFrame()}', flush=True)
        p.SetCurrentTimeline(tl)
        if (pac / 'legenda.srt').exists():                    # legenda do pacote na faixa de legenda da timeline
            if not tl.GetTrackCount('subtitle'): tl.AddTrack('subtitle')   # sem a faixa, o AppendToTimeline "aceita" e não põe nada
            it = mp.ImportMedia([str(pac / 'legenda.srt')]); it and mp.AppendToTimeline(it)
            n = len(tl.GetItemListInTrack('subtitle', 1) or [])
            print(f'  legenda.srt: {n} blocos na timeline' if n else '  legenda.srt: NÃO ENTROU (importe na mão)', flush=True)
        if SEM: continue
        p.LoadRenderPreset("H.264 Master")
        p.SetCurrentRenderFormatAndCodec("mov", "H264")
        ok = p.SetRenderSettings({"TargetDir": str(OUT / '_mov'), "CustomName": nome, "SelectAllFrames": True,
                                  "FormatWidth": w, "FormatHeight": h, "ExportVideo": True, "ExportAudio": True, "AudioCodec": "lpcm"})
        assert ok, 'SetRenderSettings falhou'
        j = p.AddRenderJob(); p.StartRendering([j], isInteractiveMode=False); t0 = time.time()
        while p.IsRenderingInProgress() and time.time() - t0 < 3600: time.sleep(2)
        st = p.GetRenderJobStatus(j); print('  render:', st.get('JobStatus'), f"{st.get('TimeTakenToRenderInMs', 0) / 1000:.0f}s", flush=True)
        mov = OUT / '_mov' / f'{nome}.mov'; mp4 = OUT / f'{nome}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mov), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(mp4)], check=True)
        pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height:format=duration', '-of', 'json', str(mp4)], capture_output=True, text=True).stdout
        d = json.loads(pr); print('  ', mp4.name, [(s['codec_type'], s.get('width'), s.get('height')) for s in d['streams']], f"{float(d['format']['duration']):.2f}s", flush=True)
    pm.SaveProject()
finally:
    if SEM: r.OpenPage('edit'); print('projeto aberto:', NOME); sys.exit(0)
    pm.CloseProject(pm.GetCurrentProject()); pm.GotoRootFolder()
    if ant and cam_ant is not None:
        for f in cam_ant: pm.OpenFolder(f)
        q = pm.LoadProject(ant); r.OpenPage(pag); print('projeto devolvido:', q.GetName() if q else 'FALHOU')
