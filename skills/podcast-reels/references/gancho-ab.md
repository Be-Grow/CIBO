# podcast-reels — variações de gancho (A/B)

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Variações de gancho (teste A/B)

`scripts/variacoes_gancho.py CORPO.mp4 GANCHO1.mp4 [GANCHO2 ...] --sem-capa --out PASTA`: um vídeo por
gancho, volume do gancho igualado ao do corpo (LUFS), tamanho/qps ajustados, GPU com `VENC=auto`.
Cada saída é conferida pelo ffmpeg e pelo AVFoundation (`av_check`, compilado de `av_check.swift`):
arquivo que roda no ffmpeg pode travar no QuickTime/iPhone. Ganchos de 3 s em 1 corte de 58 s: 24 s.
