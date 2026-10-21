# Regras transversais — Entrega

- **Nomes**: `NN - HEADLINE.mp4`, com acentos, numerados pela ordem da fala no episódio, e
  `CAPA - NN - HEADLINE.png` (prefixo, para as capas ficarem agrupadas no Finder). Nunca
  `corte01.mp4`. Troque `"` por `'`.
- **Pastas que ele lê de relance**: poucos níveis, nomes em português (`CORTES/Cortes ep1`),
  sem taxonomia numerada nem manifesto que ele não pediu. Nenhum arquivo temporário na
  árvore final. Rode `video-project-structure` no início e no fim, mas o nome das pastas de
  entrega segue esta regra.
- **Uma versão por vídeo** na pasta de entrega: sobrescreva ao refazer. Nada de v1/v2/final
  acumulando, salvo quando o usuário pedir uma pasta nova (ex.: "v2, sem sobrescrever").
- **Transcrição sempre com tempo** (`[hh:mm:ss - hh:mm:ss] texto` + SRT). Sem tempo, ele
  considera inútil. Skill `transcricao-aulas` para aulas e gravações longas.
- **Não diga que está bom antes de olhar.** O portão automático é piso: rode
  `caption-quality-gate`, `legenda-cruzada` e `video-delivery-safety-check`, olhe as contact
  sheets e **meça de novo depois de cada correção**, porque a correção costuma criar um
  defeito novo. O que não dá para verificar (ouvido, ritmo), diga que não verificou.
- **Abra a pasta no Finder ao terminar** (`open "<pasta>"`). Ele pediu isso em quase toda
  sessão.

- **Capa pensada para o grid do feed (3:4):** título fora do rosto, pessoa mais baixa no quadro, olhos abertos e
  boca fechada, escolhida olhando a imagem (`reel-motion/scripts/capa_cand.py` faz a folha com o recorte pronto).
  A capa nova vai também no quadro 0 do vídeo.

Volta ao checklist: [`_checklist.md`](_checklist.md).
