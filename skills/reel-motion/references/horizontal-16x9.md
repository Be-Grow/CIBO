# reel-motion — versão 16:9 e fonte de celular

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Versão horizontal 16:9 e fonte de celular (Andreia, 19/10/2026)
- `"orient": "h"` no reel.json → composição `ReelH` (1920×1080): painel à esquerda (`layoutH.panelW`, desenho 1080×940 escalado),
  pessoa desliza para a direita; legenda sob ela na tela dividida; gancho/títulos com `layoutH.hookScale`. Mesma pasta de dados
  copiada para `rNNh/` (segs, edit_mfa, blocos, props.py iguais; câmera e mix próprios). Capa 16:9 = `CapaH` (título à esquerda, `shift` em x).
- Celular gravado deitado (arquivo 1080×1920 com imagem 16:9): `"rotate": "cclock"`; HEVC do iPhone é full range → `"full_range": true`.
- Câmera de mão / pessoa que se mexe: `scripts/rastreio.py FONTE rosto/vNN_track.json --rotate cclock` + `"track"` no reel.json →
  o recorte 9:16 segue o rosto quadro a quadro (sendcmd no crop); no 16:9 o props recebe `camX` como trilha [[t, x]].
- `"layout": {"camShift": …}` no reel.json ajusta o layout só daquele reel (rosto mais alto/baixo na fonte: camShift = 1300 − cy·1,78).
- **Fim de palavra comido**: segs gerados pelo fim do Whisper cortaram "espiritu|al", "proble|ma", "men|te" (+0,1–0,23 s).
  Feche cada trecho pela energia (voz abaixo de −45 dB + 0,03 s), não pelo `end` do Whisper; confira todas as emendas antes das props.
- **SSD lotou**: o bundle do Remotion copiava a pasta pública inteira (12 GB) a cada render/quadro-teste/capa. Agora `pub_enxuta()`
  monta `04_work/_pub/rNN` com hard links só do reel (etapa `pub`); use `PUBLIC_DIR=04_work/_pub/rNN` no `stills.mjs`.
  Nunca rode quadros-teste junto de um render: o `limpa_bundles` do render apaga o bundle deles.
- Painéis novos: `waves` (lê × emite frequência), `balance` (balança que pende), `root` (rótulo na superfície × raiz),
  `curve` (linha no tempo da fala: pico e volta), `pillars` (pilares + teto). Extras: ladder `labelSize`/`sw`, roles `centerY`/`titleOut`,
  timeline `x0`/`x1`, balance `arm`/`panSize`. Capa: `bgFill: "cor"` (topo liso em vez do quadro desfocado que mostrava rosto fantasma).
- `capa_pausas.py rNN camera.mov folha.jpg` = candidatos de capa nas pausas da fala; `so_capa` gera só a capa.
- Prévia/entrega no próprio DaVinci: `scripts/resolve_render.py "Projeto" "Pasta/Sub" SAIDA pacote…` importa cada timeline.fcpxml num
  projeto novo, renderiza MOV H.264+LPCM e remonta MP4 AAC 256k; devolve o projeto que estava aberto pela pasta dele.
- Render por etapa reusa UM bundle (`bundle_unico()`, em `04_work/_bundle/rNN`, apagado ao sair): no pacote DaVinci eram ~35 renders e cada um reempacotava (13 s). Medido: 61 quadros com alfa em 10 s a partir do bundle pronto.
- Camada `camera` do pacote DaVinci sai pelo ffmpeg (`camera_ffmpeg`: deslocamento da tela dividida por sendcmd + fade final), 92 s contra 5,5 min no Remotion; sem motion blur/grão na troca. `"camera_ffmpeg": false` no reel.json volta ao Remotion.
- **Correções do editor (Andreia, 19/10/2026):** (1) identidade roxo + dourado tem que aparecer: painel roxo profundo, texto creme,
  destaque dourado (tema `andreia`); (2) 16:9 em **terços**: painel nos 2/3 da esquerda (`layoutH.panelW` 1280), pessoa centralizada
  no terço da direita, legenda da tela dividida no rodapé do painel; (3) SFX: whoosh variado (nunca o mesmo em tudo) e temático
  (hoje `scripts/sfx_tema.py`, modo `variado`; kit em `CIBO Acervo/sfx/andreia/wav`), nível medido
  contra a voz — os do kit global ficaram 8–10 dB abaixo e sumiram; (4) câmera e zoom no DaVinci (`camera_davinci` + `camera_moves`).
