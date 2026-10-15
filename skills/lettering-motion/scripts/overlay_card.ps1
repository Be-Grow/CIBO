param(
  [Parameter(Mandatory=$true, Position=0)][string]$InputVideo,
  [Parameter(Mandatory=$true, Position=1)][string]$Card,
  [Parameter(Mandatory=$true, Position=2)][double]$StartSeconds,
  [Parameter(Mandatory=$true, Position=3)][string]$OutputVideo,
  [Parameter(Position=4)][string]$Sfx,
  [Parameter(Position=5)][double]$SfxTime = 0
)
$ErrorActionPreference = 'Stop'
if ($Sfx) {
  $delay = [int]($SfxTime * 1000)
  $filter = "[1:v]setpts=PTS+$StartSeconds/TB[c];[0:v][c]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v];[2:a]atrim=0:0.25,volume=0.35,adelay=${delay}:all=1[k];[0:a][k]amix=inputs=2:duration=first:normalize=0[a]"
  & ffmpeg -nostdin -v error -y -i $InputVideo -i $Card -i $Sfx -filter_complex $filter -map '[v]' -map '[a]' -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -c:a pcm_s16le $OutputVideo
} else {
  $filter = "[1:v]setpts=PTS+$StartSeconds/TB[c];[0:v][c]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]"
  & ffmpeg -nostdin -v error -y -i $InputVideo -i $Card -filter_complex $filter -map '[v]' -map '0:a' -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -c:a pcm_s16le $OutputVideo
}
if ($LASTEXITCODE) { exit $LASTEXITCODE }
