# reel-motion — movimentos de câmera no Fusion

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Movimentos de câmera no Fusion (Andreia, 19/10/2026)
- `"camera_fusion": true` no reel.json: o bruto vai só com o enquadramento base; cada punch/zoom e cada troca de tela dividida
  vira um clipe de ajuste com Transform do Fusion (Motion Blur, Quality 10, Shutter 360°), keyframes de Size/Center.
  O davinci.py grava `movimentos.json`; `scripts/resolve_fx.py PACOTE` exporta a timeline em .drt, injeta as faixas de ajuste
  (modelo `assets/davinci_faixa_ajuste.xml`) logo acima do bruto, reimporta e anima. Zooms embaixo, telas divididas em cima.
- Entregue também `timeline.drt` no pacote (o FCPXML não leva clipe de ajuste nem Fusion).
- API do Resolve: sempre com limite de tempo (`perl -e 'alarm N; exec …'`) e sem navegar pastas de projeto com o projeto
  aberto — o resolve_render.py travou o DaVinci do editor assim. Leia/escreva o .drt em UTF-8 e compare caminhos em NFC.
- Vertical sem zoom além do nativo: bruto 1080p na escala 1,0, topo encostado no painel, faixa "fundo desfocado" embaixo.
- Curvas (19/10/2026, "tá muito duro, faz ease in/out"): keyframe só nas poses (começa, para, pico) com alça plana; no meio de
  movimento, tangente monotônica; keyframe extra só se o S do ease erra > ~12 px (subdivisão recursiva, trecho < 1 s fica no ease).
  Alças do `SetKeyFrames` são RELATIVAS ao keyframe (absolutas estouram a curva). Conferir lendo de volta (`GetInput` por quadro).
  `resolve_fx.py --curvas PACOTE` refaz só as curvas na timeline aberta.
- Cores e nomes das camadas no DaVinci: `scripts/resolve_cores.py` (tabela em client-router/references/regras/davinci.md, regra do CIBO 19/10/2026); o resolve_fx.py aplica no fim.
- **Mix do editor para as outras timelines** (19/10/2026): `scripts/resolve_mix.py --sfx -3 --trilha 10 [--preset NOME] "TIMELINE"…`.
  A API não lê nem grava volume de clipe nem efeito de faixa: o volume vai pelo .drt (`EffectFiltersBA`, parâmetro 124, dB em
  double) e a timeline volta com o mesmo nome (Fusion e camadas preservados). O ducker da faixa TRILHA (Inspector > Audio, fonte VOZ)
  não vai no .drt: o editor salva um preset do Fairlight na timeline dele e o `--preset` aplica nas outras.
- **FPS da fonte (Andreia 19/10/2026, "Media Offline" no fim + áudio atrasado):** a timeline é 29,97; bruto de iPhone
  em 30 fps é forçado 1:1 pelo Resolve (escorrega 1 quadro/1000 e o último trecho passa do fim do arquivo → offline).
  Resolvido em 20/10/2026: o `davinci.py` lê o fps e, fora de 29,97, usa uma cópia por tempo em `01_sources/_2997/`
  (feita uma vez por fonte, 1 s de folga, sem timecode). Testado no r01: timeline idêntica à entregue, só com o bruto trocado.
  Timeline já montada: `scripts/resolve_refaz_audio.py` (ReplaceClip do bruto; trilha/SFX novos no lugar dos arquivos).
- **.drt não troca mídia:** o Resolve religa pelo `MediaRef` e ignora `MediaFilePath`; ele também junta arquivos de mesmo nome
  entre pacotes (o 03 abriu com a trilha.wav do 01). Troca de mídia: `MediaPoolItem.ReplaceClip` ou arquivo novo no mesmo caminho.
  Trecho sem media pool item: `DeleteClips` + `AppendToTimeline` (endFrame exclusivo) copiando Pan/Zoom/Rotation do vizinho.
- **Crítica da cliente (Andreia):** trilha dramática/espiritual (Heavy Heart, STEYL) a 22 dB abaixo da voz, sem ducker; SFX só nas
  trocas de painel e com um som só (tigela tibetana), nada nas frases/legendas.
- **Cache de render do Resolve** fica no disco interno (`~/Movies/CacheClip`) e lotou o Mac: aponte para o SSD.
- **Nunca encadeie ciclos de .drt (exportar→importar) na mesma timeline** (Andreia, 20/10/2026): cada ciclo soma 1 ao `GlobalIn`
  do `MediaIn1` das camadas de ajuste (Fusion) e o render falha com "The Fusion composition at 00:00:00:02 could not be processed".
  A API não grava esse valor. Confira com `FindTool('MediaIn1').GetInput('GlobalIn')` (tem que ser 0) e refaça a partir do
  backup numa importação só: `scripts/resolve_refaz_de_backup.py BACKUP.drt "NOME"`. Guarde o .drt antes de qualquer edição por XML.
- **Mesmo nome entre pacotes = mídia trocada** (Andreia, 20/10/2026): o Resolve junta `voz.wav`/`trilha.wav` de pacotes diferentes
  num item só; o 03 tocou trechos da voz do 01 ("o áudio parece de outro vídeo"). Resolvido no motor (sufixo `__rNN` em todo
  arquivo do pacote, ver "Padrão de edição do CIBO"); para pacotes antigos, depois de importar, audite se cada clipe vem
  de `07_davinci/<próprio pacote>/` — `resolve_refaz_de_backup.py` faz isso (`pacote_certo`) e também recoloca o clipe offline
  da câmera com `RotationAngle 90` (o bruto do iPhone sai deitado sem ele). QA de sincronia por trecho: correlação do áudio do
  render com o áudio da câmera no mesmo quadro (atraso ≈ 0 ms, corr > 0,9).
- **Corrigir texto de um elemento sem remontar o pacote:** `reel.py PROJ rNN davinci titulo_lower --so-el` (não chama o davinci.py,
  que regravaria voz/trilha/SFX) + `so_capa`; depois `ReplaceClip` no item para o Resolve reler o arquivo.
- **Tigela da Andrea** (bloco `sfx` do tema `andreia`, modo `so_trocas`): `tibetan-singing-bowl` grave em todos os vídeos (editor, 20/10/2026: a aguda `sfx-singing-bowl-hit-agudo-36st` soou "feliz demais"), 16 LUFS abaixo da voz, só nas trocas de painel; escolha o som pelo tom do vídeo, com prévia no trecho real (voz+trilha). A grave "não combina
  com a ideia de frequência" (editor, 20/10/2026); agudo alto incomoda. Prévias de tom: asetrate+atempo encadeado (atempo ≥ 0,5 por filtro).
