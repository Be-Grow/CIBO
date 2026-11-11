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
