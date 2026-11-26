<<<<<<< HEAD
﻿# Instruções do CIBO para Codex

Em pedidos de edição de vídeo, comece pela skill `client-router` em `.agents/skills/client-router/` e siga as skills que ela encaminhar. Leia sempre a especificação original em `skills/<nome>/SKILL.md` e as referências indicadas; scripts, referências e assets originais permanecem em `skills/`.

Este repositório foi escrito para Claude Code em macOS. No Windows, siga `WINDOWS.md`, confira a disponibilidade das dependências e use `py -3.12`, `npm.cmd`/`npx.cmd` no PowerShell. Não presuma caminhos, assets, modelos ou credenciais do Mac. Preserve materiais brutos e projetos existentes; audite antes de mover ou sobrescrever arquivos. Siga os pontos de aprovação definidos pela skill original.
=======
# CIBO — Instruções Codex/ChatGPT Work (Windows/macOS/Linux)

1. Leia README.md e a skill relevante em skills/<skill>/SKILL.md.
2. Detecte sys.platform, ffmpeg, ffprobe e memória antes de executar.
3. Se a skill exigir macOS/DaVinci/MLX/MFA de SSD, registre unsupported_on_windows; não a adapte silenciosamente.
4. Use o Python do ambiente virtual explicitamente. Windows: .venv\Scripts\python.exe; Unix: .venv/bin/python.
5. Não altere credenciais, não publique nem processe material sem autorização.
6. Não misture assets e identidades de clientes; preserve os jobs anteriores.
7. Use o CLI independente em portable/README_WINDOWS.md.
8. A verificação lexical de bordas não comprova ideia completa. Revisão humana continua obrigatória.
9. DarkChannel: adapte os algoritmos e contratos, não os caminhos absolutos/macOS da skill.
10. Valide antes do commit; não mova produção sem autorização ou smoke real.
>>>>>>> origin/growos/windows-codex-adapter
