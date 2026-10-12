#!/bin/zsh
# Sobrepõe um grafismo Remotion (ProRes 4444 com alpha) num MP4 pronto, com SFX opcional.
# uso: overlay_card.sh ENTRADA.mp4 CARD.mov INICIO_S SAIDA.mov [SFX.wav TEMPO_SFX_S]
# Passada separada sobre o MP4 final (no encode final do motor o agendador do ffmpeg trava
# com muitas entradas). Sai em H.264 crf 12 + PCM para a próxima etapa (ex.: burn_end.py).
set -e
in="$1"; card="$2"; t="$3"; out="$4"; sfx="$5"; ts="$6"
if [[ -n "$sfx" ]]; then
  ffmpeg -nostdin -v error -y -i "$in" -i "$card" -i "$sfx" -filter_complex \
  "[1:v]setpts=PTS+$t/TB[c];[0:v][c]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v];[2:a]atrim=0:0.25,volume=0.35,adelay=$(python3 -c "print(int($ts*1000))"):all=1[k];[0:a][k]amix=inputs=2:duration=first:normalize=0[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -c:a pcm_s16le "$out"
else
  ffmpeg -nostdin -v error -y -i "$in" -i "$card" -filter_complex \
  "[1:v]setpts=PTS+$t/TB[c];[0:v][c]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]" \
  -map "[v]" -map 0:a -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -c:a pcm_s16le "$out"
fi
