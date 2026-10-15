param([Parameter(Mandatory=$true,Position=0)][string]$Html,[Parameter(Mandatory=$true,Position=1)][string]$Pdf)
$ErrorActionPreference='Stop'
$candidates=@((Get-Command chrome.exe -ErrorAction SilentlyContinue).Source,
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  (Get-Command msedge.exe -ErrorAction SilentlyContinue).Source)
$browser=$candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $browser) { throw 'Chrome ou Edge não encontrado. Instale um navegador Chromium ou informe o caminho pelo PATH.' }
$htmlPath=(Resolve-Path -LiteralPath $Html).Path
$pdfPath=[IO.Path]::GetFullPath($Pdf)
& $browser --headless=new --disable-gpu --no-pdf-header-footer "--print-to-pdf=$pdfPath" ([uri]$htmlPath).AbsoluteUri 2>$null
if ($LASTEXITCODE) { exit $LASTEXITCODE }
Write-Output "PDF: $pdfPath"
