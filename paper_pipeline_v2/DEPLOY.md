# 배포 가이드

파이프라인 서버를 **공개적으로 접근 가능한 주소**로 띄우는 방법과, n8n에서 연결하는 방법을 설명합니다.
n8n 클라우드는 `localhost` 에 접근할 수 없으므로, 아래 중 하나로 공개 URL을 확보해야 합니다.

## 1. 로컬 실행 (개발·테스트용)

```bash
cd paper_pipeline_v2
pip install -r requirements.txt
cp .env.example .env   # GEMINI_API_KEY, CLAUDE_API_KEY 입력
python mcp_server.py    # http://localhost:8000
```

## 2. Docker 실행

```bash
cd paper_pipeline_v2
docker build -t paper-pipeline-v2 .

# .env 파일로 키 주입 (이미지에 키를 굽지 않음)
docker run --rm -p 8000:8000 --env-file .env \
  -v "$PWD/output:/app/output" \
  paper-pipeline-v2
```

- `--env-file .env` : `GEMINI_API_KEY`, `CLAUDE_API_KEY` 등 주입
- `-v .../output` : GATE 통과 결과물(.md/.json)을 호스트에 보관
- 헬스체크: `curl http://localhost:8000/health`

## 3. 공개 URL 확보

### (A) 빠른 터널 — ngrok (임시/데모)

```bash
ngrok http 8000
# 출력된 https://xxxx.ngrok-free.app 를 복사
```

n8n 워크플로의 **"논문 파이프라인 호출"** 노드 URL에:
```
https://xxxx.ngrok-free.app/api/pipeline/run
```

### (B) 상시 서버 — 클라우드 VM / 컨테이너 호스팅

Railway, Render, Fly.io, AWS/GCP 등에 위 Docker 이미지를 배포하고,
환경변수(`GEMINI_API_KEY`, `CLAUDE_API_KEY`)를 플랫폼 시크릿으로 설정하세요.
공개 도메인이 생기면 `https://<도메인>/api/pipeline/run` 을 n8n에 입력합니다.

## 4. n8n 연결

1. n8n 워크플로 **"논문생산 파이프라인 v2 실행"** 열기
2. **"논문 파이프라인 호출"** 노드의 URL에 위에서 확보한 공개 주소 입력
3. Timeout은 논문 생성 시간을 고려해 넓게(기본 800000ms) 유지
4. **"주제 입력"** 노드에서 topic/keywords 수정 후 실행

## 보안

- API 키는 절대 이미지/소스에 포함하지 말고 `--env-file` 또는 플랫폼 시크릿으로만 주입하세요.
- ngrok 무료 URL은 누구나 접근 가능하므로, 공개 서버에는 간단한 인증(예: 헤더 키)을 추가하는 것을 권장합니다.
