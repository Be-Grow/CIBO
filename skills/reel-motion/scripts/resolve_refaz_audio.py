#!/usr/bin/env python3
"""Refaz fonte, trilha e SFX de timelines já montadas no Resolve, sem perder Fusion/camadas (Andreia 19/10/2026, crítica da
cliente: trilha "muito animada" e alta, SFX demais e variados; e "Media Offline" + áudio atrasado no fim).
- Fonte: o pacote declarava 29,97 e o bruto do iPhone é 30 fps; o Resolve força 1:1 (o vídeo escorrega 1 quadro a cada 1000
  e o último trecho passa do fim do arquivo e fica offline, sem media pool item). ReplaceClip do bruto para a cópia em 29,97
  por tempo (01_sources/_2997/*.mov, com 1 s de folga) e, no .drt, o trecho offline ganha o MediaRef dos irmãos.
- Trilha: uma música para todos, início por vídeo, GAP dB abaixo da voz (loudness integrada), fade no fim; clipe a 0 dB.
- SFX: só um por troca de painel (o mais perto do início de cada burn, ±15 quadros), todos com o mesmo som; os outros saem.
O .drt NÃO troca mídia (o Resolve religa pelo MediaRef e ignora MediaFilePath): o som novo é gravado no lugar do arquivo do
pacote (antigo vai para lixo/audio_antigo/) e o item do media pool é recarregado; pelo .drt só volume e remoção de clipes.
uso: resolve_refaz_audio.py --musica ARQ --sfx ARQ [--gap 22] [--inicio 01=0,02=30] PACOTE […]"""
import re, shutil, struct, subprocess, sys, tempfile, unicodedata, zipfile
from pathlib import Path
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
import DaVinciResolveScript as dvr

FPS = 30000 / 1001
nfc = lambda x: unicodedata.normalize('NFC', x)
VOL = lambda db: '0000000200000020800a1d087c38004a0f085f1a0b0a0911' + struct.pack('<d', db).hex() + '4a004a004a004a00'   # volume do clipe (dB)
EFX = r'<EffectFiltersBA>[0-9a-f]*</EffectFiltersBA>|<EffectFiltersBA/>'


def dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)], capture_output=True, text=True).stdout)


def lufs(f):
    e = subprocess.run(['ffmpeg', '-nostats', '-i', str(f), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])


def nivel(src, out, alvo, ss, d, fade_fim):
    """trecho de src com loudness integrada = alvo, duração exata d (o media pool item mantém a duração)"""
    tmp = out.with_name(out.stem + '.tmp.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', str(src), '-af',
                    f'apad=whole_dur={d},atrim=0:{d},afade=t=in:d=0.02,afade=t=out:st={max(0, d - fade_fim):.3f}:d={fade_fim}',
                    '-ar', '48000', '-ac', '2', str(tmp)], check=True)
    g = alvo - lufs(tmp)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(tmp), '-af', f'volume={g:.2f}dB,alimiter=limit=0.89:level=false',
                    '-ar', '48000', '-c:a', 'pcm_s24le', str(out)], check=True)
    tmp.unlink()


def arquivos(pac, lixo, musica, sfx_src, gap, ini, fim):
    """grava trilha.wav e sfx/*.wav novos no lugar (mesma duração); os antigos vão para o lixo"""
    um = lambda base: next(pac.glob(f'{base}__*.wav'), pac / f'{base}.wav')      # voz__r01.wav (pacote novo) ou voz.wav
    tr = um('trilha'); voz = lufs(um('voz')); bk = lixo / pac.name; feito = []
    if not (bk / tr.name).exists():
        bk.mkdir(parents=True, exist_ok=True); shutil.copy2(tr, bk / tr.name); shutil.copytree(pac / 'sfx', bk / 'sfx')
    nivel(musica, tr, voz - gap, ini, max(dur(bk / tr.name), fim + 1), 2.5); feito.append('trilha')
    for f in sorted((bk / 'sfx').glob('*.wav')):
        d = dur(f); nivel(sfx_src, pac / 'sfx' / f.name, voz - 10, 0, d, min(1.5, d / 2))
    return round(voz, 1)


def edita(s):
    """bruto offline → MediaRef dos irmãos; SFX só nas trocas (volume 0 dB); trilha a 0 dB"""
    refs = {}                                                   # o trecho offline vem com <MediaRef/> vazio
    CL = r'<Sm2Ti(?:Video|Audio)Clip .*?</Sm2Ti(?:Video|Audio)Clip>'
    for c in re.findall(CL, s, re.S):
        fp, ref = re.search(r'<MediaFilePath>([^<]+)<', c), re.search(r'<MediaRef>([^<]+)<', c)
        if fp and ref and '/01_sources/' in fp.group(1): refs.setdefault(nfc(fp.group(1)), ref.group(1))
    def bruto(m):
        c = m.group(0); fp = re.search(r'<MediaFilePath>([^<]+)<', c)
        if fp and nfc(fp.group(1)) in refs:
            c = re.sub(r'<MediaRef>[^<]*</MediaRef>|<MediaRef/>', f'<MediaRef>{refs[nfc(fp.group(1))]}</MediaRef>', c, count=1)
        return c
    s = re.sub(CL, bruto, s, flags=re.S)
    i, j = s.index('<AudioTrackVec>'), s.index('</AudioTrackVec>'); a = s[i:j]
    v = s[s.index('<VideoTrackVec>'):s.index('</VideoTrackVec>')]
    burns = [int(re.search(r'<Start>(\d+)', c).group(1)) for c in re.findall(r'<Sm2TiVideoClip .*?</Sm2TiVideoClip>', v, re.S) if '/burns/' in c]
    el = re.findall(r'[ \t]*<Element>\s*<Sm2TiAudioClip .*?</Sm2TiAudioClip>\s*</Element>\n', a, re.S)
    sx = [(e, int(re.search(r'<Start>(\d+)', e).group(1))) for e in el if '/sfx/' in e]
    fica = set()
    for b in burns:
        perto = min(sx, key=lambda x: abs(x[1] - b), default=None)
        if perto and abs(perto[1] - b) <= 15: fica.add(perto[0])
    for e, _ in sx:
        a = a.replace(e, re.sub(EFX, f'<EffectFiltersBA>{VOL(0.0)}</EffectFiltersBA>', e, count=1) if e in fica else '', 1)
    for e in el:
        if re.search(r'/trilha(__[^/<]*)?\.wav<', e):
            a = a.replace(e, re.sub(EFX, f'<EffectFiltersBA>{VOL(0.0)}</EffectFiltersBA>', e, count=1), 1)
    fim = max((int(re.search(r'<Start>(\d+)', e).group(1)) + int(re.search(r'<Duration>(\d+)', e).group(1)) for e in el if re.search(r'/voz(__[^/<]*)?\.wav<', e)), default=0) / FPS
    return s[:i] + a + s[j:], {'burns': len(burns), 'sfx': f'{len(fica)}/{len(sx)}', 'bruto refs': len(refs)}, fim


if __name__ == '__main__':
    arg = sys.argv[1:]; op = lambda k, d=None: arg[arg.index(k) + 1] if k in arg else d
    musica, sfx_src, gap = Path(op('--musica')), Path(op('--sfx')), float(op('--gap', 22))
    inicios = dict(x.split('=') for x in op('--inicio', '').split(',') if x)
    pacs = [Path(a) for k, a in enumerate(arg) if not a.startswith('--') and (k == 0 or not arg[k - 1].startswith('--'))]
    lixo = pacs[0].parent.parent / 'lixo' / 'audio_antigo'
    r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    sys.path.insert(0, str(Path(__file__).parent)); from resolve_cores import aplica
    tl_de = lambda nome: next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if nfc(p.GetTimelineByIndex(i).GetName()) == nome), None)
    # 1. timelines → .drt editado (antes de mexer em mídia) e arquivos novos no disco
    drts = {}
    for pac in pacs:
        nome = nfc(pac.name); tl = tl_de(nome); tmp = Path(tempfile.mkdtemp()); drt = tmp / 'a.drt'
        assert tl.Export(str(drt), r.EXPORT_DRT, r.EXPORT_NONE), 'exportação .drt falhou'
        d = tmp / 'x'; zipfile.ZipFile(drt).extractall(d); seq = next((d / 'SeqContainer').glob('*.xml'))
        s, info, fim = edita(seq.read_text(encoding='utf-8')); seq.write_text(s, encoding='utf-8')
        with zipfile.ZipFile(tmp / 'b.drt', 'w', zipfile.ZIP_DEFLATED) as z:
            for f in d.rglob('*'):
                if f.is_file(): z.write(f, f.relative_to(d))
        info['voz LUFS'] = arquivos(pac, lixo, musica, sfx_src, gap, float(inicios.get(nome[:2], 0)), fim)
        drts[nome] = (tmp, info); print(f'{nome[:45]}: {info}', flush=True)
    # 2. media pool: bruto → cópia 29,97; trilha/SFX recarregados do disco (todas as timelines do projeto)
    mpis = {}
    for i in range(1, p.GetTimelineCount() + 1):
        t = p.GetTimelineByIndex(i)
        for ty in ('video', 'audio'):
            for k in range(1, t.GetTrackCount(ty) + 1):
                for it in t.GetItemListInTrack(ty, k) or []:
                    m = it.GetMediaPoolItem()
                    if m: mpis[m.GetMediaId()] = m
    troca = {'bruto': 0, 'audio': 0}
    for m in mpis.values():
        fp = m.GetClipProperty('File Path') or ''
        mm = re.match(r'(.*/01_sources/)([^/]+)\.(?:mp4|MP4|mov|MOV)$', fp)
        if mm and Path(mm.group(1) + '_2997/' + mm.group(2) + '.mov').exists():
            troca['bruto'] += bool(m.ReplaceClip(mm.group(1) + '_2997/' + mm.group(2) + '.mov'))
        elif '/07_davinci/' in fp and (re.search(r'/trilha(__[^/]*)?\.wav$', fp) or '/sfx/' in fp):
            troca['audio'] += bool(m.ReplaceClip(fp))
    print('media pool:', troca, flush=True)
    # 3. timelines voltam com o mesmo nome
    for nome, (tmp, info) in drts.items():
        tl = tl_de(nome); tl.SetName(nome + ' (antiga)')
        novo = mp.ImportTimelineFromFile(str(tmp / 'b.drt'), {'timelineName': nome}); assert novo, 'importação .drt falhou'
        novo.SetName(nome)
        off = [it.GetName() for ty in ('video', 'audio') for k in range(1, novo.GetTrackCount(ty) + 1)
               for it in novo.GetItemListInTrack(ty, k) or [] if not it.GetMediaPoolItem() and not it.GetFusionCompCount()]
        if off: print(f'{nome[:45]}: {len(off)} clipes sem mídia {off[:3]}; a antiga fica como "(antiga)"', flush=True)
        else: mp.DeleteTimelines([tl])
        aplica(novo); shutil.rmtree(tmp, ignore_errors=True)
    r.GetProjectManager().SaveProject(); print('ok', flush=True)
