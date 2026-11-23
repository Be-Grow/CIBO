# CIBO no Windows

Este guia registra a adaptação dos scripts originalmente escritos para macOS. Os arquivos e projetos de edição do usuário não são migrados automaticamente.

## Requisitos

- Windows 10/11, PowerShell 7 recomendado.
- Python 3.12 (`py -3.12`), FFmpeg/FFprobe no `PATH`, Node.js LTS e `uv`.
- Instale as dependências Python com `py -3.12 -m pip install -r skills\<skill>\requirements-windows.txt` quando esse arquivo existir; para as demais skills, use o `requirements.txt` correspondente. Isso evita instalar `mlx-whisper`, que é exclusivo de Apple Silicon. Na primeira execução do `faster-whisper`, o modelo é baixado para o cache do usuário.
- Remotion executa com `npm.cmd`/`npx.cmd` no PowerShell quando a política bloqueia os wrappers `.ps1`.

## Instalação do checkout

Mantenha o clone em local estável. O CIBO encontra as skills relativas à raiz do repositório; `CIBO_ROOT` e `CIBO_SKILLS` permitem apontar para outro local.

```powershell
$env:CIBO_ROOT = 'S:\Edição BEGrow\CIBO'
$env:CIBO_SKILLS = Join-Path $env:CIBO_ROOT 'skills'
$env:CIBO_TEMP = Join-Path $env:TEMP 'CIBO'
$env:PYTHONUTF8 = '1' # preserva caminhos com acentos no Python do Windows
py -3.12 .\skills\video-render-optimizer\scripts\hw_profile.py detect
py -3.12 .\skills\video-render-optimizer\scripts\hw_profile.py env --json
```

`hw_profile.py install-schedule` cria uma tarefa semanal no Task Scheduler; `uninstall-schedule` remove essa tarefa. `env` imprime atribuições PowerShell no Windows e `export` em shells Unix.

## Acervo e arquivos locais

Configure uma vez a biblioteca com `py -3.12 skills\acervo\scripts\acervo.py init "D:\CIBO Acervo"`. A localização é gravada em `%USERPROFILE%\.cibo\acervo.json`. `move-library` usa `shutil.copytree`, mantém a cópia antiga e só atualiza a configuração depois que a cópia termina. Para assets Mac que não existem neste checkout, informe os arquivos reais no job ou cadastre-os no acervo; não reutilize caminhos `/Volumes/...` como se fossem caminhos Windows.

Para localizar o Google Drive para desktop em uma unidade não padrão, defina `CIBO_DRIVE_ROOT` para a raiz montada. `entrega_drive.py` continua em simulação sem `--confirmo`. No Windows o DriveFS não fornece ao script os IDs por atributo estendido; use `--destino` e confira a sincronização no Drive para desktop. Links de pasta não podem ser resolvidos automaticamente pelo script no Windows.

## Diferenças de scripts

- `tests/regressao.py` usa as skills do checkout, encontra `.venv\Scripts\python.exe` e tem fallback para o Python atual. Não aplica `taskpolicy`; em timeout, termina a árvore do processo com `taskkill`.
- Whisper usa `faster-whisper` fora de Apple Silicon, com `CIBO_ASR_DEVICE` (`cpu` padrão ou `cuda`) e `CIBO_ASR_COMPUTE_TYPE` opcionais. MLX continua sendo usado somente no macOS quando instalado.
- O verificador de variações de gancho valida decodificação integral com FFmpeg. AVFoundation/QuickTime é exclusivo do macOS e é omitido no Windows.
- Use `skills\lettering-motion\scripts\overlay_card.ps1` e `skills\relatorio-estrategia-social\scripts\html_to_pdf.ps1` no PowerShell. Os `.sh` originais continuam disponíveis para usuários macOS.
- O alinhador MFA pode ser configurado com `CIBO_MFA_HOME`; no Windows instale o Montreal Forced Aligner e os modelos compatíveis no ambiente escolhido. Se não estiver disponível, o fluxo deve marcar o alinhamento como pendente e conservar os tempos do Whisper.
- Fontes, modelos, logos, sons, fontes de vídeo e credenciais privados descritos nas skills não são incluídos por esta adaptação. Configure `YUNET`, caminhos no job ou cadastre assets autorizados no acervo.

## Verificação local

Rode `py -3.12 -m compileall -q skills tests` para validar sintaxe Python e `py -3.12 tests\regressao.py check` para renderizar os motores sintéticos. A regressão precisa das dependências de cada motor e pode divergir das referências douradas se a versão do FFmpeg ou o encoder mudar. Não use `record` para aceitar diferenças sem confirmar que a mudança é intencional.
