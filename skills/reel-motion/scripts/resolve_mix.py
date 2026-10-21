#!/usr/bin/env python3
"""Copia o ajuste de volume de clipe do editor para outras timelines (Andreia 19/10/2026: SFX −3 dB, trilha +10 dB com
ducker na faixa). A API do Resolve não lê nem grava volume de clipe nem efeito de faixa: o volume vai pelo .drt
(EffectFiltersBA do Sm2TiAudioClip, parâmetro 124 = volume em dB, double little-endian) e a timeline volta com o mesmo
nome. O ducker (efeito de faixa) NÃO vai no .drt: salve um preset do Fairlight na timeline do editor e aplique com --preset.
uso: resolve_mix.py --sfx -3 --trilha 10 [--preset NOME] "TIMELINE" […]   (projeto aberto no Resolve)"""
import re, shutil, struct, sys, tempfile, zipfile
from pathlib import Path
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
import DaVinciResolveScript as dvr

PRE, POS = '800a1d087c38004a0f085f1a0b0a0911', '4a004a004a004a00'      # forma gravada pelo Resolve (volume do clipe)


def ganho(clipe, novo):
    """novo(dB atual) → dB; grava no EffectFiltersBA do clipe"""
    e = re.search(r'<EffectFiltersBA>([0-9a-f]*)</EffectFiltersBA>|<EffectFiltersBA/>', clipe)
    m = re.search(r'0a0911([0-9a-f]{16})4a', e.group(1) or '') if e else None
    db = struct.unpack('<d', bytes.fromhex(m.group(1)))[0] if m else 0.0
    corpo = PRE + struct.pack('<d', novo(db)).hex() + POS
    return clipe.replace(e.group(0), f'<EffectFiltersBA>00000002{len(corpo) // 2:08x}{corpo}</EffectFiltersBA>', 1)


def ajusta(xml, sfx, trilha):
    i, j = xml.index('<AudioTrackVec>'), xml.index('</AudioTrackVec>')
    cont = {'sfx': 0, 'trilha': 0}
    def troca(m):
        c = m.group(0); fp = re.search(r'<MediaFilePath>([^<]*)', c).group(1)
        if '/sfx/' in fp and sfx is not None:
            cont['sfx'] += 1; return ganho(c, lambda d: d + sfx)
        if re.search(r'/trilha(__[^/]*)?\.wav$', fp) and trilha is not None:
            cont['trilha'] += 1; return ganho(c, lambda d: trilha)
        return c
    a = re.sub(r'<Sm2TiAudioClip .*?</Sm2TiAudioClip>', troca, xml[i:j], flags=re.S)
    return xml[:i] + a + xml[j:], cont


if __name__ == '__main__':
    arg = sys.argv[1:]; op = lambda k: float(arg[arg.index(k) + 1]) if k in arg else None
    sfx, trilha = op('--sfx'), op('--trilha'); preset = arg[arg.index('--preset') + 1] if '--preset' in arg else None
    nomes = [a for k, a in enumerate(arg) if not a.startswith('--') and (k == 0 or not arg[k - 1].startswith('--'))]
    r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    sys.path.insert(0, str(Path(__file__).parent)); from resolve_cores import aplica
    for nome in nomes:
        tl = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome)
        if sfx is not None or trilha is not None:
            tmp = Path(tempfile.mkdtemp()); drt = tmp / 'a.drt'
            assert tl.Export(str(drt), r.EXPORT_DRT, r.EXPORT_NONE), 'exportação .drt falhou'
            d = tmp / 'x'; zipfile.ZipFile(drt).extractall(d); seq = next((d / 'SeqContainer').glob('*.xml'))
            s, cont = ajusta(seq.read_text(encoding='utf-8'), sfx, trilha); seq.write_text(s, encoding='utf-8')
            with zipfile.ZipFile(tmp / 'b.drt', 'w', zipfile.ZIP_DEFLATED) as z:
                for f in d.rglob('*'):
                    if f.is_file(): z.write(f, f.relative_to(d))
            tl.SetName(nome + ' (antiga)')
            novo = mp.ImportTimelineFromFile(str(tmp / 'b.drt'), {'timelineName': nome}); assert novo, 'importação .drt falhou'
            novo.SetName(nome); mp.DeleteTimelines([tl]); aplica(novo); tl = novo
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            cont = {}
        ok = ''
        if preset:
            p.SetCurrentTimeline(tl); ok = f', preset {preset}: {p.ApplyFairlightPresetToCurrentTimeline(preset)}'
        print(f'{nome[:45]}: {cont}{ok}', flush=True)
    r.GetProjectManager().SaveProject()
