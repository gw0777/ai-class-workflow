#!/usr/bin/env bash
# 맥미니 24시간 서버 설치 스크립트 (스레드 ①: launchd 자동 재시작 + 전원 복구 자동 시작)
#   bash agent_office/deploy/install_macmini.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$HERE/.." && pwd)"          # .../agent_office
REPO_DIR="$(cd "$APP_DIR/.." && pwd)"      # .../ai-class-workflow
PLIST_SRC="$HERE/launchd/com.agentoffice.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.agentoffice.plist"
VENV="$APP_DIR/.venv"

echo "[1/5] 가상환경 + 의존성"
if [ ! -d "$VENV" ]; then python3 -m venv "$VENV"; fi
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$APP_DIR/requirements.txt"
mkdir -p "$APP_DIR/logs" "$APP_DIR/output"

echo "[2/5] .env"
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "  -> $APP_DIR/.env 를 열어 ANTHROPIC_API_KEY, DISCORD_TOKEN(또는 역할별 토큰), OWNER_DISCORD_ID 를 채우세요."
fi

echo "[3/5] 설정 점검"
(cd "$APP_DIR" && "$VENV/bin/python" -m agent_office --check) || echo "  ! 점검에서 경고가 있습니다. .env 를 채운 뒤 다시 실행하세요."

echo "[4/5] launchd 등록 (로그인 시 자동 시작 + 비정상 종료 시 재시작)"
mkdir -p "$HOME/Library/LaunchAgents"
sed -e "s#__REPO__#$REPO_DIR#g" -e "s#__PYTHON__#$VENV/bin/python#g" "$PLIST_SRC" > "$PLIST_DST"
launchctl bootout "gui/$(id -u)" "$PLIST_DST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl kickstart -k "gui/$(id -u)/com.agentoffice"

echo "[5/5] 전원·절전 설정 (관리자 암호 필요; 건너뛰려면 Ctrl+C)"
echo "  - 정전 후 자동 시작(autorestart), 잠들지 않기(sleep 0), 디스크 절전 끄기"
sudo pmset -a autorestart 1 sleep 0 disksleep 0 displaysleep 10 || echo "  (pmset 건너뜀)"

cat <<MSG

완료. 확인:
  launchctl print gui/$(id -u)/com.agentoffice | head -20
  tail -f $APP_DIR/logs/agent_office.err.log
  대시보드: http://127.0.0.1:8787   (외부에서 보려면 Tailscale 등으로 접속)
중지/재시작:
  launchctl kickstart -k gui/$(id -u)/com.agentoffice
  launchctl bootout gui/$(id -u) $PLIST_DST
MSG
