# podcast-reels — economia de tokens

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Economia de tokens

- Filtre a saída: `| grep -E "built|DONE|Error"`. O plano de legendas só é impresso com
  `PLAN_VERBOSE=1`; para revisar, abra `work/review.csv` no trecho que interessa.
- QA de lote numa chamada: `scripts/qa_lote.py PASTA` (verify, LUFS, pico, cor, duração e uma
  folha de contato por corte numa imagem só).
- Uma folha de contato por decisão, nunca quadro a quadro.
- Capa: `cover_scan.py` (varredura) + `cover_rank.py SCAN VIDEO --crop-h ...` (nota do Vision da
  Apple: qualidade do rosto, pose, olhos, mão acima do queixo, tamanho) → uma folha com os 8
  melhores. Calibrado com as capas do João: as 6 aprovadas acima das 3 reprovadas.
- Som: `audio_qa.py` (clique sobre fala ou alto, trilha sumindo ou alta, emenda cortando
  palavra, última palavra engolida), uma linha por corte.
- Antes de subir mudança de motor para o CIBO: `python3 ~/CIBO/tests/regressao.py check`.
