# 논문생산 파이프라인 v2 — 원클릭 설정 (Windows)
# 관리자 PowerShell에서 실행:  powershell -ExecutionPolicy Bypass -File .\setup.ps1
# 수행 내용: 의존성 설치 → .env 생성(키 입력) → 테스트 → 방화벽 규칙(TCP 8000) → 실행 안내
# 남는 수동 단계는 Tailscale 로그인뿐입니다.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=== 논문생산 파이프라인 v2 설정 시작 ===" -ForegroundColor Cyan

# 0) 관리자 권한 확인 (방화벽 규칙에 필요)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "관리자 권한이 아닙니다. 방화벽 규칙 단계는 건너뜁니다. (전체 설정은 관리자 PowerShell에서 다시 실행)"
}

# 1) Python 확인
try { $pyVersion = python --version 2>&1 }
catch { Write-Error "python을 찾을 수 없습니다. https://www.python.org/downloads/ 에서 설치 후 다시 실행하세요."; exit 1 }
Write-Host "[1/5] Python 확인: $pyVersion" -ForegroundColor Green

# 2) 의존성 설치
Write-Host "[2/5] 의존성 설치 중..." -ForegroundColor Green
python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) { Write-Error "pip 설치 실패"; exit 1 }

# 3) .env 생성 + API 키 입력 (키는 저장소에 커밋되지 않음)
Write-Host "[3/5] .env 설정" -ForegroundColor Green
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
$envText = Get-Content ".env" -Raw
if ($envText -match "your-gemini-api-key-here") {
    $gemini = Read-Host "GEMINI_API_KEY 입력"
    if ($gemini) { $envText = $envText -replace "your-gemini-api-key-here", $gemini }
}
if ($envText -match "your-anthropic-api-key-here") {
    $claude = Read-Host "CLAUDE_API_KEY 입력"
    if ($claude) { $envText = $envText -replace "your-anthropic-api-key-here", $claude }
}
Set-Content ".env" $envText -NoNewline
Write-Host "  .env 저장 완료" -ForegroundColor Gray

# 4) 테스트
Write-Host "[4/5] 테스트 실행" -ForegroundColor Green
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { Write-Warning "테스트 실패 — 위 출력을 확인하세요. 설정은 계속 진행합니다." }

# 5) 방화벽 규칙 (TCP 8000 인바운드 허용, 중복 생성 방지)
if ($isAdmin) {
    Write-Host "[5/5] 방화벽 규칙 확인" -ForegroundColor Green
    $ruleName = "paper-pipeline-v2 (TCP 8000)"
    if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 | Out-Null
        Write-Host "  방화벽 규칙 추가됨: $ruleName" -ForegroundColor Gray
    } else {
        Write-Host "  방화벽 규칙 이미 존재: $ruleName" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== 설정 완료 ===" -ForegroundColor Cyan
Write-Host "남은 수동 단계:"
Write-Host "  1. Tailscale 로그인 (원격 접속용): tailscale 앱에서 로그인"
Write-Host "  2. 서버 시작:  python mcp_server.py   (http://localhost:8000)"
Write-Host "  3. 동작 확인:  curl http://localhost:8000/health"
