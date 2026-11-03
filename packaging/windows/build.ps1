# Construit l'exécutable et l'installateur Windows (PowerShell)
# Prérequis : Python 3.10+ et Inno Setup 6 (winget install JRSoftware.InnoSetup)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\..")
$version = (Select-String -Path version.py -Pattern '"(.+)"').Matches[0].Groups[1].Value
python -m venv .venv-build
.\.venv-build\Scripts\pip install -r requirements.txt pyinstaller
.\.venv-build\Scripts\pyinstaller packaging\gscolorname.spec --noconfirm --distpath dist --workpath build
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 introuvable (winget install JRSoftware.InnoSetup)" }
& $iscc "/DAppVersion=$version" packaging\windows\gscolorname.iss
Write-Host "OK : dist\gsColorName-$version-win64-setup.exe"
