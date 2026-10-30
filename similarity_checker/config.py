"""검사 옵션(카피킬러의 검사 설정에 대응)."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field


def default_db_path() -> str:
    """코퍼스 DB 기본 경로. 환경변수 SIMCHECK_DB 가 있으면 우선."""
    return os.environ.get("SIMCHECK_DB") or os.path.join(".simcheck", "corpus.db")


@dataclass
class CheckConfig:
    # --- 일치 판정 ---
    min_run: int = 6            # 연속 일치 어절 수(카피킬러 기본 6어절) 이상이면 '일치'
    sim_threshold: float = 0.70 # 어절 시퀀스 유사도(0~1) 이상이면 '유사'(바꿔쓰기 의심)
    loose: bool = True          # 조사/어미 일부 제거 후 비교(표현 변형에 강함)
    candidates: int = 30        # 문장당 정밀 비교할 후보 문장 수
    index_ngram: int = 3        # 역색인 어절 n-gram 크기

    # --- 제외 규칙(카피킬러 '검사 설정'에 대응) ---
    exclude_quotes: bool = True        # 인용부호로 감싼 문장 제외
    exclude_citations: bool = True     # 출처표시(저자, 연도)/[n] 포함 문장 제외
    exclude_references: bool = True    # 참고문헌 목록 제외
    exclude_toc: bool = True           # 목차 제외
    min_tokens: int = 5                # 이 어절 수 미만 문장은 검사 제외

    # --- 비교 대상 ---
    exclude_sources: list[str] = field(default_factory=list)  # 출처 라벨에 이 문자열이 포함되면 제외(자기 자신 등)

    def to_dict(self) -> dict:
        return asdict(self)
