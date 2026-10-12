# content-hub — histórico de falhas

- **Encode travado com 0% de CPU (12/10/2026)**: a trilha entrava em loop infinito (`-stream_loop -1` sem `-t`). Corrigido como na `podcast-reels` (item 23); o teste `~/CIBO/tests/regressao.py` pegou o travamento no Bombordo.
