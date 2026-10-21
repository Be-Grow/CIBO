# Content Hub — áudio: as três camadas

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Áudio: escolha uma das três camadas

Masters OBS podem conter `both`, `main` e `holly`. Não misture as três. Analise as faixas, selecione **uma só** por gravação e registre a escolha. Favoreça voz do convidado inteligível, baixa reverberação/ruído, ausência de clipping e nível estável; `both` não é automaticamente a melhor.

Trate a faixa escolhida com `scripts/audio_select_enhance.py`, usando Pedalboard para filtro passa-altas, compressão, ganho e limiter. A redução de ruído deve ser moderada para não metalizar a voz. Compare o antes/depois por escuta e valide picos antes do render.

SNR, ruído e clipping apenas classificam qualidade; não provam que a faixa pertence ao convidado em imagem. Antes de aprovar, transcreva uma amostra de cada candidata no mesmo timecode e compare com o SRT/contexto e com o movimento labial. Rejeite qualquer faixa semanticamente divergente, mesmo que tenha a melhor pontuação técnica. Registre `semantic_match`, trecho comparado e decisão no relatório. Se a automação não puder confirmar correspondência, a escolha fica `REVIEW_REQUIRED`, nunca aprovada automaticamente.

Faça QA rigoroso em quatro etapas: (1) compare métricas das três faixas; (2) escute amostras A/B em fala baixa, fala forte e pausas; (3) verifique voz natural, ruído, reverberação, clipping, sibilância e sincronismo; (4) repita a escuta no MP4 final depois de música, SFX e codificação. Se a redução de ruído criar voz metálica, bombeamento ou cortes de final de palavra, alivie o gate/processamento. Qualidade e naturalidade da voz têm prioridade sobre silêncio absoluto.
