# ai-class-workflow

| 디렉터리 | 내용 |
|---|---|
| [`paper_pipeline_v2/`](./paper_pipeline_v2) | 논문생산 파이프라인 v2 (Gemini+Claude, FastAPI/MCP, 구독 SaaS) |
| [`similarity_checker/`](./similarity_checker) | 개인용 논문 유사도·표절 검사 도구 (카피킬러 대체: 로컬/GitHub 코퍼스, 참고문헌 실존 검증, HTML 리포트) |
| [`agent_office/`](./agent_office) | 디스코드 채널별 역할 봇 7개(매니저·실장·조교·총무·팀장·작가·비서) 하네스: 승인 가드레일, 넘김 기록, 맥미니 launchd 24시간 가동, 사무실 대시보드 |

```bash
pip install -r similarity_checker/requirements.txt
python -m similarity_checker index add ./papers          # 비교 문헌 색인
python -m similarity_checker check 내논문.docx --out-dir reports --refs --online
```

```bash
# 디스코드 사무실(봇 7개) — 맥미니 24시간 서버
bash agent_office/deploy/install_macmini.sh            # venv + .env + launchd + pmset
cd agent_office && python -m agent_office --check      # 설정 점검
```
