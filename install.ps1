# KOTEacher 한 번에 설치 (Windows 10/11, PowerShell)
#
#   irm https://raw.githubusercontent.com/Hong-Iron/KOTEacher/main/install.ps1 | iex
#
# 하는 일: 파이썬·git·Ollama 확인(없으면 winget으로 설치) → 앱 내려받기 → 패키지 → 문제 팩 → 모델 → 시작 메뉴 바로가기
# 아직 Windows 실기기에서 시험하지 않았습니다. 막히면 README의 '직접 설치'를 따라 주세요.
$ErrorActionPreference = "Stop"
$Repo = "https://github.com/Hong-Iron/KOTEacher.git"
$Dir = if ($env:KOTEACHER_DIR) { $env:KOTEACHER_DIR } else { Join-Path $HOME "KOTEacher" }

function Say($m) { Write-Host "`n> $m" -ForegroundColor Cyan }
function Ok($m) { Write-Host "  v $m" -ForegroundColor Green }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User") }

Say "파이썬, git, Ollama 확인"
if (-not (Have "winget")) { throw "winget이 없습니다. Microsoft Store에서 '앱 설치 관리자'를 설치한 뒤 다시 실행해 주세요." }
if (-not (Have "python")) { winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements; Refresh-Path }
if (-not (Have "git")) { winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements; Refresh-Path }
if (-not (Have "ollama")) { winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements; Refresh-Path }
Ok (python --version)

Say "KOTEacher 내려받기 -> $Dir"
if (Test-Path (Join-Path $Dir ".git")) { git -C $Dir pull --ff-only } else { git clone --depth 1 $Repo $Dir }
Set-Location $Dir

Say "패키지 설치 (가상환경 .venv)"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -q --upgrade pip
.\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
Ok "pywebview, markdown 설치했습니다"

Say "문제 팩 만들기 (약 20초)"
.\.venv\Scripts\python.exe tools\build_packs.py | Select-Object -First 2

Say "코치 모델 받기"
for ($i = 0; $i -lt 30; $i++) { try { Invoke-RestMethod http://127.0.0.1:11434/api/version | Out-Null; break } catch { Start-Sleep 1 } }
$Model = if ($env:KOTEACHER_MODEL) { $env:KOTEACHER_MODEL } else { .\.venv\Scripts\python.exe -c "from koteacher import ollama; print(ollama.recommend()['model'])" }
# GitHub 패키지(ghcr.io)는 끊기면 config.PULL_TRIES번까지 다시 받고(받던 데서 잇는다), 그래도 안 되면 Ollama 저장소의 원래 판
$Fallback, $Tries = (.\.venv\Scripts\python.exe -c "from koteacher import config as c; f = c.FALLBACK.get('$Model', ''); print(f or '-', c.PULL_TRIES if f else 1)").Split(" ")
for ($i = 1; $i -le [int]$Tries; $i++) {
  ollama pull $Model
  if ($LASTEXITCODE -eq 0) { break }
  if ($i -lt [int]$Tries) { Write-Host "  GitHub에서 받다가 멈췄습니다. 다시 받습니다 ($($i + 1)/$Tries)"; Start-Sleep ($i * 2) }
}
if ($LASTEXITCODE -ne 0 -and $Fallback -ne "-") { Write-Host "  GitHub에서 받지 못해 Ollama 서버에서 $Fallback 을 받습니다"; $Model = $Fallback; ollama pull $Model }
if ($LASTEXITCODE -eq 0) { Ok "모델 $Model 을 받았습니다" } else { Write-Host "  모델을 받지 못했습니다. 앱을 연 뒤 안내에 따라 받으면 됩니다." }

Say "시작 메뉴 바로가기 만들기"
$Lnk = Join-Path ([Environment]::GetFolderPath("Programs")) "KOTEacher.lnk"
$Sh = New-Object -ComObject WScript.Shell
$S = $Sh.CreateShortcut($Lnk)
$S.TargetPath = Join-Path $Dir ".venv\Scripts\pythonw.exe"
$S.Arguments = "-m koteacher"
$S.WorkingDirectory = $Dir
$S.IconLocation = Join-Path $Dir "assets\KOTEacher.ico"
$S.Save()
Ok "시작 메뉴에서 KOTEacher를 찾을 수 있습니다"

Say "설치가 끝났습니다. 업데이트할 때는 이 명령을 한 번 더 실행하면 됩니다."
