# CIBO portátil — Windows + Codex/ChatGPT Work

Este adaptador funciona com Python 3.11+ e FFmpeg/FFprobe existente no PATH. Não requer Claude Code, Homebrew, MLX, MPS ou DaVinci. O restante do CIBO não foi portado integralmente: scripts que usam caminhos /Volumes ou frameworks de Mac continuam separados.

## Windows (PowerShell)

Na pasta do repositório:

    py -3 portable\cibo_windows.py check-cut --transcription "C:\caminho\transcription.json" --start 100 --end 155
    py -3 portable\cibo_windows.py check-video --video "C:\caminho\sample.mp4"
    py -3 portable\cibo_windows.py feedback --log "C:\Dev\DarkChannel-Studio\data\editorial-feedback.jsonl" --job-id JOB --sha256 HASH_64_HEX --decision rejected --reason "Ideia não concluída" --start 100 --end 155
    py -3 portable\cibo_windows.py feedback --log "C:\Dev\DarkChannel-Studio\data\editorial-feedback.jsonl" --summary

O CLI funciona também com python3 no Linux/macOS. check-cut apenas sinaliza problemas lexicais e de timestamps; não prova conclusão semântica. check-video decodifica e mede A/V, mas não identifica pitch. Feedback fica em arquivo local e não no histórico público do CIBO.

## Implementação inicial portada

- Checagem de bordas inspirada em podcast-reels/scripts/checa_cortes.py.
- QA básico de MP4 inspirado em video-delivery-safety-check.
- Feedback editorial JSONL inspirado em client-router/scripts/feedback.py.

## Não portado integralmente

- fala-limpa: Silero VAD, SpeechBrain, MFA e modelos locais pesados exigem adaptação e testes.
- legenda-cruzada: implementação original usa MLX/large-v3 em macOS.
- DaVinci, Premiere, Remotion, biblioteca de música, SSD, assets e identidades de clientes.
- semantic-broll-validator: processo de revisão semântica, não modelo de IA executável.

## Codex e ChatGPT Work

Leia AGENTS.md e execute testes locais. No DarkChannel, use o módulo versionado e um avaliador semântico Qwen3. O QA de borda não substitui o raciocínio editorial nem o aceite humano. Não misturar recursos de clientes.
