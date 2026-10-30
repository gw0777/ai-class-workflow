# ai-class-workflow

| 디렉터리 | 내용 |
|---|---|
| [`paper_pipeline_v2/`](./paper_pipeline_v2) | 논문생산 파이프라인 v2 (Gemini+Claude, FastAPI/MCP, 구독 SaaS) |
| [`similarity_checker/`](./similarity_checker) | 개인용 논문 유사도·표절 검사 도구 (카피킬러 대체: 로컬/GitHub 코퍼스, 참고문헌 실존 검증, HTML 리포트) |

```bash
pip install -r similarity_checker/requirements.txt
python -m similarity_checker index add ./papers          # 비교 문헌 색인
python -m similarity_checker check 내논문.docx --out-dir reports --refs --online
```
