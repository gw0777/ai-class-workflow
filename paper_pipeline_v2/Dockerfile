# 논문생산 무인 파이프라인 v2 — 서버 컨테이너
FROM python:3.11-slim

WORKDIR /app

# 의존성 먼저 설치(레이어 캐시)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# API 키는 이미지에 굽지 않는다 — 실행 시 -e 또는 --env-file로 주입
ENV HOST=0.0.0.0 \
    PORT=8000 \
    OUTPUT_DIR=/app/output

EXPOSE 8000

# 간단 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health',timeout=3).status==200 else 1)" || exit 1

CMD ["python", "mcp_server.py"]
