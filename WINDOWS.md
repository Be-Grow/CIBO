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

Biblioteca de assets que o editor já tem em outro disco (ex.: `D:\EDIÇÃO`, 26/11/2026: "não quero que tu modifique a estrutura do que já tem em edição"): nunca copie nem reorganize; crie uma junção dentro do acervo (`New-Item -ItemType Junction -Path "<acervo>\EDIÇÃO" -Target "D:\EDIÇÃO"`) e catalogue como referência (`acervo.py index "D:/EDIÇÃO" --tags edicao-d`). Antes de `move-library`, remova a junção (o `copytree` copiaria a biblioteca inteira) e recrie depois.

Configure uma vez a biblioteca com `py -3.12 skills\acervo\scripts\acervo.py init "D:\CIBO Acervo"`. A localização é gravada em `%USERPROFILE%\.cibo\acervo.json`. `move-library` usa `shutil.copytree`, mantém a cópia antiga e só atualiza a configuração depois que a cópia termina. Para assets Mac que não existem neste checkout, informe os arquivos reais no job ou cadastre-os no acervo; não reutilize caminhos `/Volumes/...` como se fossem caminhos Windows.

Para localizar o Google Drive para desktop em uma unidade não padrão, defina `CIBO_DRIVE_ROOT` para a raiz montada. `entrega_drive.py` continua em simulação sem `--confirmo`. No Windows o DriveFS não fornece ao script os IDs por atributo estendido; use `--destino` e confira a sincronização no Drive para desktop. Links de pasta não podem ser resolvidos automaticamente pelo script no Windows.

## Diferenças de scripts

- **Regra das camadas de plataforma (editor, 26/11/2026: "polimorfismo… a mesma api funciona em múltiplos dispositivos, mas a implementação por baixo muda de sistema pra sistema"):** adaptação para Windows nunca muda o comportamento do Mac. O código chama uma interface única e cada sistema tem a sua classe; a do Mac devolve exatamente o que o código fazia antes. Hoje: `tests/plataforma.py` (teste), `skills/_shared/asr_compat.py` (Whisper), `skills/_shared/paths.py` (`portable_path`), `skills/_shared/resolve_env.py` (DaVinci). Sistema novo = classe nova, sem tocar em quem chama.
- `tests/regressao.py` pergunta à `tests/plataforma.py` onde ficam a referência, o Python de cada skill, o motor do reel-motion e os temporários. As referências de render comparam bits, e ffmpeg ou sistema diferentes mudam os bits: o Windows tem a sua em `tests/golden/windows/`, gravada de um checkout LIMPO da `main` (worktree + `CIBO_SKILLS`), nunca da pasta com mudanças em teste. Não aplica `taskpolicy`; em timeout, termina a árvore do processo com `taskkill`.
- Fontes dos temas do reel-motion apontam para o acervo do Mac (`/Volumes/SSD/CIBO Acervo/fonte/...`): o `reel.py` traduz com `portable_path` para o acervo daqui, e a fonte precisa estar no acervo (`acervo.py add ARQ --type fonte --client <cliente>`). Sem ela, o job para nas fontes.
- Whisper (`skills/_shared/asr_compat.py`): classe `MLX` no Mac, `FasterWhisper` no resto. No Windows o áudio é lido pelo ffmpeg (o PyAV 19 tirou o `metadata_errors` que o faster-whisper 1.2.1 usa; não há roda de PyAV antiga para o Python 3.12 do Windows). `CIBO_ASR_DEVICE` é `auto` por padrão: tenta a placa de vídeo e cai para o processador. Placa NVIDIA precisa das bibliotecas CUDA no ambiente da CIBO: `uv pip install --python <python da CIBO> nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"` (a classe carrega as DLLs sozinha). RTX 3050 4 GB, large-v3-turbo em `int8_float16`: 4 s para 18 s de fala (processador ~39 s).
- DaVinci portátil (fora de `C:\Program Files`): grave `CIBO_RESOLVE_DIR`, `RESOLVE_SCRIPT_API` e `RESOLVE_SCRIPT_LIB` nas variáveis do usuário; a montagem no Resolve é pela API, não por FCPXML (ver `client-router/references/regras/davinci.md` → "Montagem nativa pela API").
- O verificador de variações de gancho valida decodificação integral com FFmpeg. AVFoundation/QuickTime é exclusivo do macOS e é omitido no Windows.
- Use `skills\lettering-motion\scripts\overlay_card.ps1` e `skills\relatorio-estrategia-social\scripts\html_to_pdf.ps1` no PowerShell. Os `.sh` originais continuam disponíveis para usuários macOS.
- O alinhador MFA pode ser configurado com `CIBO_MFA_HOME`; no Windows instale o Montreal Forced Aligner e os modelos compatíveis no ambiente escolhido. Se não estiver disponível, o fluxo deve marcar o alinhamento como pendente e conservar os tempos do Whisper.
- Fontes, modelos, logos, sons, fontes de vídeo e credenciais privados descritos nas skills não são incluídos por esta adaptação. Configure `YUNET`, caminhos no job ou cadastre assets autorizados no acervo.

## Verificação local

Rode `py -3.12 -m compileall -q skills tests` para validar sintaxe Python e `py -3.12 tests\regressao.py check` para renderizar os motores sintéticos. A regressão precisa das dependências de cada motor e pode divergir das referências douradas se a versão do FFmpeg ou o encoder mudar. Não use `record` para aceitar diferenças sem confirmar que a mudança é intencional.
