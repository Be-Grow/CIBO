#!/usr/bin/env python3
"""Fecha o corte como numa timeline: o VIDEO acaba seco (sem fade, sem congelar) e o film
burn fica numa trilha por cima, comecando antes e ACABANDO DEPOIS do video, sobre o preto.

uso: burn_end.py ENTRADA.mp4 SAIDA.mp4 [FILMBURN.mp4]
A entrada deve ter sido renderizada com BURN_OUT=0. O script:
  - poe o pico do burn (0,53 s do asset de 1,4 s) exatamente no ultimo quadro do video,
    entao o corte seco fica escondido no clarao;
  - depois do fim do video so existe preto, e o resto do burn (0,87 s) toca sobre ele;
  - audio: segue ate o fim do video e a cauda sai em fade sobre o preto.
Regra do usuario: "nao e fade, e o burning e segue pra um video preto, como se eu tivesse a
track do video e a track do efeito por cima, acabando mais na frente dela".
"""
import os, subprocess, sys
src, out = sys.argv[1], sys.argv[2]
fb = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), '..', 'assets', 'filmburn_blue.mp4')
D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                         capture_output=True, text=True).stdout)
w, h = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x', src],
                      capture_output=True, text=True).stdout.strip().split('x')
tail = out + '.burntail.mp4'
# burn + 2,5 s de preto (tpad de cauda no burn nao funciona encadeado: o video acabava junto com o asset)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', fb, '-f', 'lavfi', '-i', f'color=black:s={w}x{h}:r=30:d=2.5', '-filter_complex',
                f'[0:v]fps=30,scale={w}:{h},format=yuv420p,setsar=1[a];[1:v]format=yuv420p,setsar=1[b];[a][b]concat=n=2:v=1:a=0[v]',
                '-map', '[v]', '-c:v', 'libx264', '-crf', '10', '-preset', 'fast', tail], check=True)
PEAK = 0.53
st, tot = D - PEAK, D - PEAK + 1.4
fc = (f'[0:v]tpad=stop_mode=add:stop_duration={tot - D + 0.1:.3f}:color=black,format=gbrp[v];'
      f'[1:v]format=gbrp,tpad=start_mode=add:start_duration={st:.3f}:color=black[b];'
      f'[v][b]blend=all_mode=screen:shortest=1,format=yuv420p[vo];'
      f'[0:a]apad=pad_dur={tot - D + 0.1:.3f},afade=t=out:st={D - 0.05:.3f}:d={tot - D + 0.05:.3f}'
      # BURN_END_LIMIT (ex.: 0.84): limitador de pico no fim da cadeia, para o true peak
      # ficar abaixo de -1 dBTP. Desligado por padrao: os outros clientes saem identicos.
      + (f',alimiter=limit={os.environ["BURN_END_LIMIT"]}:level=false' if os.environ.get('BURN_END_LIMIT') else '')
      + '[ao]')
# BURN_END_BT709=1: este e o ultimo encode da cadeia; sem as tags a entrega sai sem Rec.709.
# As flags de linha de comando sozinhas nao bastam: o blend em gbrp entrega quadros com
# primarias/transferencia "unknown" e o x264 grava isso. O h264_metadata escreve no bitstream.
COLOR = (['-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
          '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0']
         if os.environ.get('BURN_END_BT709') else [])
tmp = out + '.tmp.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', tail, '-filter_complex', fc, '-map', '[vo]', '-map', '[ao]',
                '-t', f'{tot:.3f}', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', *COLOR, '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', tmp], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-i', tmp, '-f', 'null', '-'], check=True)
os.replace(tmp, out); os.remove(tail); print('ok', out, f'{tot:.2f}s')
