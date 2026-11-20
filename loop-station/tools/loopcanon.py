#!/usr/bin/env python3
"""루프 정석(Loop Canon) 실행기.

트리거 → 커넥터 → 메모리 → 서브에이전트(병렬) → 워크트리(격리·병합) → 스킬(자가진단) → 사람 검토.

판단(수집·분석·작성·채점)은 에이전트가 하고, 규칙(발동·중복 방지·상한·격리·병합·중단·검토)은
이 도구가 결정론적으로 강제한다. 자가진단 루브릭 단계는 기존 loopstation.py 98점 게이트를 그대로 쓴다.
Python 표준 라이브러리만 사용한다. 명세: loop-station/LOOP_CANON.md

사용법:
    python3 loop-station/tools/loopcanon.py validate [loops/*.json ...]
    python3 loop-station/tools/loopcanon.py due [--at 2026-11-20T09:00:00+09:00]
    python3 loop-station/tools/loopcanon.py match --event events.json
    python3 loop-station/tools/loopcanon.py start <loop_id> [--at ...] [--event event.json]
    python3 loop-station/tools/loopcanon.py merge <run_dir|run_id>
    python3 loop-station/tools/loopcanon.py check <run_dir|run_id> [--record records/<run_id>.json]
    python3 loop-station/tools/loopcanon.py review <run_dir|run_id> --decision approve|revise \\
        --reviewer 이름 --note "검토 의견" [--lesson "스킬 메모리에 남길 교훈"]
    python3 loop-station/tools/loopcanon.py status <loop_id>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import loopstation
except ModuleNotFoundError:  # 다른 위치에서 모듈로 불러올 때
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import loopstation

SCHEMA_VERSION = 1
MAX_ROUNDS_CAP = loopstation.MAX_ITERATIONS  # 품질 게이트와 같은 회전 상한(5)
DEFAULT_WINDOW_MINUTES = 60
MAX_SUMMARY_CHARS_CAP = 2000

LOOP_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
OFFSET_RE = re.compile(r"^[+-](\d{2}):(\d{2})$")

TRIGGER_TYPES = ("schedule", "event")
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
CONNECTOR_CATEGORIES = ("communication", "project", "data", "design", "web_search")
CONNECTOR_LABELS = {
    "communication": "커뮤니케이션",
    "project": "프로젝트 관리",
    "data": "데이터",
    "design": "디자인",
    "web_search": "웹 검색",
}
ACCESS_LEVELS = ("read", "write", "read_write")
WRITE_ACCESS = ("write", "read_write")
ISOLATION_MODES = ("directory", "git_worktree")
INSTRUCTION_MODES = ("goal", "path")
PRIORITIES = ("high", "normal", "low")  # 앞쪽일수록 먼저 처리
PRIORITY_LABELS = {"high": "긴급", "normal": "보통", "low": "낮음"}
STATUSES = ("idle", "running", "awaiting_review", "done", "halted")
STATUS_LABELS = {
    "idle": "대기",
    "running": "진행 중",
    "awaiting_review": "사람 검토 대기",
    "done": "완료",
    "halted": "중단",
}
ACTIVE_STATUSES = ("running", "awaiting_review")
DECISIONS = ("approve", "revise")


class LoopError(Exception):
    """규칙 위반으로 동작을 거부할 때 쓰는 예외 (메시지는 사용자에게 그대로 보인다)."""


@dataclass(frozen=True)
class Paths:
    """loop-station/ 아래 루프 정석 경로 묶음. 테스트에서는 임시 폴더를 root로 쓴다."""

    root: Path

    @property
    def repo_root(self) -> Path:
        return self.root.parent

    @property
    def loops(self) -> Path:
        return self.root / "loops"

    @property
    def memory(self) -> Path:
        return self.root / "memory"

    @property
    def runs(self) -> Path:
        return self.root / "runs"

    @property
    def records(self) -> Path:
        return self.root / "records"


DEFAULT_PATHS = Paths(loopstation.BASE_DIR)


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_str_list(value: object, *, allow_empty: bool = False) -> bool:
    if not isinstance(value, list):
        return False
    if not value and not allow_empty:
        return False
    return all(_is_str(v) for v in value)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _read_json(path: Path, what: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LoopError(f"{what} 파일이 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LoopError(f"{what} JSON 형식 오류: {path} ({exc})") from exc


def parse_offset(text: str) -> timezone:
    m = OFFSET_RE.match(text)
    if not m:
        raise LoopError(f"utc_offset 형식 오류: {text!r} (예: +09:00)")
    sign = 1 if text[0] == "+" else -1
    return timezone(sign * timedelta(hours=int(m.group(1)), minutes=int(m.group(2))))


def parse_time(text: str) -> datetime:
    """ISO 8601 시각을 읽는다. 시간대 오프셋이 없으면 거부한다(시간대 추측 금지)."""
    try:
        dt = datetime.fromisoformat(text)
    except (TypeError, ValueError) as exc:
        raise LoopError(
            f"시각 형식 오류: {text!r} (예: 2026-11-20T09:00:00+09:00)"
        ) from exc
    if dt.tzinfo is None:
        raise LoopError(
            f"시각에 시간대 오프셋이 없습니다: {text!r} (예: 2026-11-20T09:00:00+09:00)"
        )
    return dt


# ---------------------------------------------------------------------------
# ⓪ 루프 명세 검증 (validate)
# ---------------------------------------------------------------------------


def _validate_trigger(trig: object, err) -> None:
    if not isinstance(trig, dict):
        err("trigger: 객체여야 합니다")
        return
    kind = trig.get("type")
    if kind not in TRIGGER_TYPES:
        err(f"trigger.type은 {TRIGGER_TYPES} 중 하나여야 합니다")
        return
    offset = trig.get("utc_offset")
    m = OFFSET_RE.match(offset) if isinstance(offset, str) else None
    if not m or int(m.group(1)) > 14 or int(m.group(2)) > 59:
        err("trigger.utc_offset은 +HH:MM 형식이어야 합니다 (예: +09:00)")

    if kind == "schedule":
        days = trig.get("weekdays")
        if (
            not isinstance(days, list)
            or not days
            or any(d not in WEEKDAYS for d in days)
        ):
            err(f"trigger.weekdays는 {WEEKDAYS} 중 1개 이상이어야 합니다")
        elif len(set(days)) != len(days):
            err("trigger.weekdays에 중복이 있습니다")
        time_text = trig.get("time")
        tm = TIME_RE.match(time_text) if isinstance(time_text, str) else None
        if not tm:
            err("trigger.time은 HH:MM(24시간) 형식이어야 합니다")
        window = trig.get("window_minutes", DEFAULT_WINDOW_MINUTES)
        if not _is_int(window) or not (1 <= window <= 1440):
            err("trigger.window_minutes는 1~1440 정수여야 합니다")
        elif tm and int(tm.group(1)) * 60 + int(tm.group(2)) + window > 1440:
            err(
                "trigger.time + window_minutes가 자정을 넘으면 안 됩니다 (요일 판정이 흔들림)"
            )
        return

    # event
    if not _is_str(trig.get("source")):
        err("trigger.source: 이벤트 출처 문자열 필수 (예: email)")
    if not _is_str_list(trig.get("any_keywords")):
        err("trigger.any_keywords: 1개 이상의 키워드 목록 필수")
    if "exclude_keywords" in trig and not _is_str_list(
        trig["exclude_keywords"], allow_empty=True
    ):
        err("trigger.exclude_keywords: 키워드 목록이어야 합니다")
    rules = trig.get("priority_rules", [])
    if not isinstance(rules, list):
        err("trigger.priority_rules: 목록이어야 합니다")
        rules = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict) or rule.get("level") not in PRIORITIES:
            err(f"trigger.priority_rules[{i}].level은 {PRIORITIES} 중 하나여야 합니다")
        elif not _is_str_list(rule.get("keywords")):
            err(f"trigger.priority_rules[{i}].keywords: 1개 이상의 키워드 목록 필수")
    if trig.get("default_priority", "normal") not in PRIORITIES:
        err(f"trigger.default_priority는 {PRIORITIES} 중 하나여야 합니다")


def _validate_connectors(conns: object, err) -> None:
    if not isinstance(conns, list) or not conns:
        err("connectors: 1개 이상의 목록이어야 합니다")
        return
    names: set[str] = set()
    for i, c in enumerate(conns):
        p = f"connectors[{i}]"
        if not isinstance(c, dict):
            err(f"{p}: 객체여야 합니다")
            continue
        if c.get("category") not in CONNECTOR_CATEGORIES:
            err(f"{p}.category는 {CONNECTOR_CATEGORIES} 중 하나여야 합니다")
        if c.get("access") not in ACCESS_LEVELS:
            err(f"{p}.access는 {ACCESS_LEVELS} 중 하나여야 합니다")
        for k in ("name", "purpose"):
            if not _is_str(c.get(k)):
                err(f"{p}.{k} 문자열 필수")
        name = c.get("name")
        if isinstance(name, str):
            if name in names:
                err(f"{p}.name 중복: {name}")
            names.add(name)


def _validate_subagents(subs: object, err) -> None:
    if not isinstance(subs, list) or not subs:
        err("subagents: 1개 이상의 목록이어야 합니다")
        return
    roles: set[str] = set()
    for i, s in enumerate(subs):
        p = f"subagents[{i}]"
        if not isinstance(s, dict):
            err(f"{p}: 객체여야 합니다")
            continue
        role = s.get("role")
        if not isinstance(role, str) or not LOOP_ID_RE.match(role):
            err(
                f"{p}.role은 영소문자/숫자/하이픈 슬러그여야 합니다 (작업 폴더 이름이 됨)"
            )
        elif role in roles:
            err(f"{p}.role 중복: {role}")
        else:
            roles.add(role)
        if not _is_str(s.get("task")):
            err(f"{p}.task 문자열 필수")
        group = s.get("group")
        if not _is_int(group) or group < 1:
            err(f"{p}.group은 1 이상의 정수여야 합니다 (같은 group = 병렬 실행)")


def _validate_skill(skill: object, err, repo_root: Path | None) -> None:
    if not isinstance(skill, dict):
        err("skill: 객체여야 합니다")
        return
    for k in ("purpose", "deliverable", "user"):
        if not _is_str(skill.get(k)):
            err(f"skill.{k} 문자열 필수 (루프의 목적·결과물·사용자)")
    mode = skill.get("instruction_mode")
    if mode not in INSTRUCTION_MODES:
        err(
            f"skill.instruction_mode는 {INSTRUCTION_MODES} 중 하나여야 합니다 (목적 지시 | 경로 지시)"
        )
    steps = skill.get("steps", [])
    if mode == "path" and not _is_str_list(steps):
        err("skill.steps: 경로 지시(path)는 1개 이상의 단계 목록이 필요합니다")
    elif not _is_str_list(steps, allow_empty=True):
        err("skill.steps: 문자열 목록이어야 합니다")
    if not _is_str_list(skill.get("conditions")):
        err("skill.conditions: 1개 이상의 조건 목록 필수")
    criteria = skill.get("success_criteria")
    if not _is_str_list(criteria):
        err("skill.success_criteria: 1개 이상의 성공 기준 목록 필수")
    else:
        for i, c in enumerate(criteria):
            if not re.search(r"\d", c):
                err(f"skill.success_criteria[{i}]: 구체적 수치가 있어야 합니다 ({c!r})")
    prohibitions = skill.get("prohibitions")
    if not isinstance(prohibitions, list) or not prohibitions:
        err("skill.prohibitions: 1개 이상의 금지 사항 목록 필수")
    else:
        for i, pr in enumerate(prohibitions):
            if (
                not isinstance(pr, dict)
                or not _is_str(pr.get("rule"))
                or not _is_str(pr.get("reason"))
            ):
                err(f"skill.prohibitions[{i}]: rule과 reason(이유) 문자열 필수")
    reporting = skill.get("reporting")
    if not isinstance(reporting, dict) or not all(
        _is_str(reporting.get(k)) for k in ("to", "format", "when")
    ):
        err("skill.reporting: to/format/when 문자열 필수 (보고 기준)")
    exceptions = skill.get("exceptions")
    if not isinstance(exceptions, list) or not exceptions:
        err("skill.exceptions: 1개 이상의 예외 처리 목록 필수")
    else:
        for i, ex in enumerate(exceptions):
            if (
                not isinstance(ex, dict)
                or not _is_str(ex.get("situation"))
                or not _is_str(ex.get("handling"))
            ):
                err(f"skill.exceptions[{i}]: situation과 handling 문자열 필수")
    self_check = skill.get("self_check")
    if not isinstance(self_check, dict):
        err("skill.self_check: 객체여야 합니다 (자가진단 루브릭)")
        return
    rubric = self_check.get("rubric")
    if not _is_str(rubric) or not rubric.endswith(".md"):
        err("skill.self_check.rubric: 루브릭 .md 경로 필수")
    elif repo_root is not None and not (repo_root / rubric).is_file():
        err(f"skill.self_check.rubric 파일이 없습니다: {rubric}")
    if not isinstance(self_check.get("gate_record"), bool):
        err("skill.self_check.gate_record: 불리언 필수 (98점 게이트 기록 요구 여부)")


def _validate_stop(stop: object, err) -> None:
    if not isinstance(stop, dict):
        err("stop_conditions: 객체여야 합니다")
        return
    rules = (
        ("summary_max_chars", 1, MAX_SUMMARY_CHARS_CAP),
        ("min_improvements", 1, 100),
        ("min_attachments", 0, 100),
        ("max_rounds", 1, MAX_ROUNDS_CAP),
        ("daily_run_cap", 1, 1000),
    )
    for key, lo, hi in rules:
        v = stop.get(key)
        if not _is_int(v) or not (lo <= v <= hi):
            err(f"stop_conditions.{key}는 {lo}~{hi} 정수여야 합니다")


def validate_spec(spec: object, repo_root: Path | None = None) -> list[str]:
    """루프 명세 dict를 검증해 오류 메시지 목록을 돌려준다. 빈 목록이면 유효."""
    errors: list[str] = []
    err = errors.append
    if not isinstance(spec, dict):
        return ["루프 명세는 JSON 객체여야 합니다"]
    if spec.get("schema_version") != SCHEMA_VERSION:
        err(f"schema_version은 {SCHEMA_VERSION}이어야 합니다")
    loop_id = spec.get("loop_id")
    if not isinstance(loop_id, str) or not LOOP_ID_RE.match(loop_id):
        err("loop_id는 영소문자/숫자/하이픈 슬러그여야 합니다")
    if not _is_str(spec.get("title")):
        err("title 문자열 필수")

    _validate_trigger(spec.get("trigger"), err)
    _validate_connectors(spec.get("connectors"), err)
    memory = spec.get("memory")
    if not isinstance(memory, dict) or not _is_str_list(
        memory.get("context"), allow_empty=True
    ):
        err("memory.context: 컨텍스트 메모리 초기 문장 목록이어야 합니다")
    _validate_subagents(spec.get("subagents"), err)
    worktree = spec.get("worktree")
    if (
        not isinstance(worktree, dict)
        or worktree.get("isolation") not in ISOLATION_MODES
    ):
        err(f"worktree.isolation은 {ISOLATION_MODES} 중 하나여야 합니다")
    _validate_skill(spec.get("skill"), err, repo_root)
    _validate_stop(spec.get("stop_conditions"), err)

    review = spec.get("human_review")
    if not isinstance(review, dict):
        err("human_review: 객체여야 합니다")
        review = {}
    else:
        if not isinstance(review.get("required"), bool):
            err("human_review.required: 불리언 필수")
        if not _is_str(review.get("reviewer")):
            err("human_review.reviewer 문자열 필수")
        if not _is_str_list(review.get("checklist")):
            err("human_review.checklist: 1개 이상의 확인 항목 필수")

    # 교차 규칙: 외부에 쓰는 커넥터가 있으면 사람 검토 없이 끝낼 수 없다.
    conns = spec.get("connectors")
    if isinstance(conns, list):
        writers = [
            c.get("name")
            for c in conns
            if isinstance(c, dict) and c.get("access") in WRITE_ACCESS
        ]
        if writers and review.get("required") is not True:
            err(
                f"쓰기 커넥터({', '.join(map(str, writers))})가 있으면 human_review.required는 true여야 합니다"
            )
    return errors


def load_spec_file(path: Path, repo_root: Path | None) -> tuple[dict | None, list[str]]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"JSON 읽기 실패: {exc}"]
    errors = validate_spec(spec, repo_root)
    if isinstance(spec, dict) and isinstance(spec.get("loop_id"), str):
        expected = spec["loop_id"] + ".json"
        if path.name != expected:
            errors.append(f"파일명은 {expected} 이어야 합니다 (현재 {path.name})")
    return (spec if isinstance(spec, dict) else None), errors


def load_spec(paths: Paths, loop_id: str) -> dict:
    if not LOOP_ID_RE.match(loop_id):
        raise LoopError(f"loop_id 형식 오류: {loop_id!r}")
    path = paths.loops / f"{loop_id}.json"
    if not path.is_file():
        raise LoopError(f"루프 명세가 없습니다: {path}")
    spec, errors = load_spec_file(path, paths.repo_root)
    if errors or spec is None:
        raise LoopError(
            f"루프 명세 검증 실패 ({path.name}):\n  - " + "\n  - ".join(errors)
        )
    return spec


def load_all_specs(paths: Paths) -> list[dict]:
    specs: list[dict] = []
    failures: list[str] = []
    for path in sorted(paths.loops.glob("*.json")):
        spec, errors = load_spec_file(path, paths.repo_root)
        if errors or spec is None:
            failures.append(f"{path.name}:\n  - " + "\n  - ".join(errors))
        else:
            specs.append(spec)
    if failures:
        raise LoopError("루프 명세 검증 실패:\n" + "\n".join(failures))
    return specs


# ---------------------------------------------------------------------------
# ① 트리거 — 시간 기반(알람 시계) / 이벤트 기반(초인종)
# ---------------------------------------------------------------------------


def schedule_slot(spec: dict, at: datetime) -> str | None:
    """시간 기반 루프가 `at` 시각에 발동하면 그 예약 슬롯(ISO 문자열)을, 아니면 None을 돌려준다."""
    trig = spec["trigger"]
    if trig["type"] != "schedule":
        return None
    local = at.astimezone(parse_offset(trig["utc_offset"]))
    if WEEKDAYS[local.weekday()] not in trig["weekdays"]:
        return None
    hh, mm = (int(x) for x in trig["time"].split(":"))
    slot = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    window = timedelta(minutes=trig.get("window_minutes", DEFAULT_WINDOW_MINUTES))
    if slot <= local < slot + window:
        return slot.isoformat()
    return None


def validate_event(event: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(event, dict):
        return ["이벤트는 JSON 객체여야 합니다"]
    for k in ("id", "source", "received_at"):
        if not _is_str(event.get(k)):
            errors.append(f"이벤트 {k} 문자열 필수")
    if not _is_str(event.get("subject")) and not _is_str(event.get("body")):
        errors.append("이벤트 subject 또는 body 중 하나는 있어야 합니다")
    if _is_str(event.get("received_at")):
        try:
            parse_time(event["received_at"])
        except LoopError as exc:
            errors.append(f"이벤트 received_at: {exc}")
    return errors


def match_event(spec: dict, event: dict) -> str | None:
    """이벤트가 루프 트리거와 맞으면 긴급도(high|normal|low)를, 아니면 None을 돌려준다."""
    trig = spec["trigger"]
    if trig["type"] != "event" or event.get("source") != trig["source"]:
        return None
    text = f"{event.get('subject', '')}\n{event.get('body', '')}".casefold()
    if not any(k.casefold() in text for k in trig["any_keywords"]):
        return None
    if any(k.casefold() in text for k in trig.get("exclude_keywords", [])):
        return None
    levels = [
        rule["level"]
        for rule in trig.get("priority_rules", [])
        if any(k.casefold() in text for k in rule["keywords"])
    ]
    if levels:
        return min(levels, key=PRIORITIES.index)  # 여러 규칙이 맞으면 가장 긴급한 쪽
    return trig.get("default_priority", "normal")


def triage(specs: list[dict], events: list[dict]) -> tuple[list[dict], list[str]]:
    """이벤트를 루프에 배정하고 긴급도 → 도착 시각 순으로 정렬한 처리 대기열을 만든다."""
    queue: list[dict] = []
    unmatched: list[str] = []
    for ev in events:
        hits = [
            (spec["loop_id"], p)
            for spec in specs
            if (p := match_event(spec, ev)) is not None
        ]
        if not hits:
            unmatched.append(ev["id"])
            continue
        for loop_id, priority in hits:
            queue.append(
                {
                    "event_id": ev["id"],
                    "loop_id": loop_id,
                    "priority": priority,
                    "received_at": ev["received_at"],
                }
            )
    queue.sort(
        key=lambda q: (PRIORITIES.index(q["priority"]), parse_time(q["received_at"]))
    )
    return queue, unmatched


# ---------------------------------------------------------------------------
# ③ 메모리 — 상태 · 처리 이력 · 평가 기록 · 컨텍스트 (+ 스킬 메모리)
# ---------------------------------------------------------------------------


class Memory:
    """memory/<loop_id>/ 아래 4종 메모리 + 스킬 메모리."""

    def __init__(self, paths: Paths, loop_id: str) -> None:
        self.loop_id = loop_id
        self.dir = paths.memory / loop_id
        self.state_path = self.dir / "state.json"  # 상태
        self.history_path = self.dir / "history.jsonl"  # 처리 이력
        self.evaluations_path = self.dir / "evaluations.jsonl"  # 평가 기록
        self.context_path = self.dir / "context.md"  # 컨텍스트
        self.skill_path = (
            self.dir / "skill-notes.md"
        )  # 스킬 메모리 (루프가 성장하는 층)

    def ensure(self, spec: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        if not self.context_path.exists():
            lines = [f"# 컨텍스트 메모리 — {spec['title']}", ""]
            lines += [f"- {c}" for c in spec["memory"]["context"]] or ["- (아직 없음)"]
            self.context_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if not self.skill_path.exists():
            self.skill_path.write_text(
                f"# 스킬 메모리 — {spec['title']}\n\n"
                "사람 검토에서 나온 교훈을 쌓는다. 다음 실행은 시작 전에 이 파일을 먼저 읽는다.\n\n",
                encoding="utf-8",
            )
        if not self.state_path.exists():
            _write_json(self.state_path, self.default_state())

    def default_state(self) -> dict:
        return {
            "loop_id": self.loop_id,
            "status": "idle",
            "run_id": None,
            "round": 0,
            "updated_at": None,
        }

    def state(self) -> dict:
        if not self.state_path.exists():
            return self.default_state()
        data = _read_json(self.state_path, "상태 메모리")
        if not isinstance(data, dict) or data.get("status") not in STATUSES:
            raise LoopError(f"상태 메모리가 손상되었습니다: {self.state_path}")
        return data

    def save_state(self, **updates: object) -> None:
        state = self.state()
        state.update(updates)
        _write_json(self.state_path, state)

    def _jsonl(self, kind: str) -> Path:
        return {"history": self.history_path, "evaluations": self.evaluations_path}[
            kind
        ]

    def append(self, kind: str, entry: dict) -> None:
        path = self._jsonl(kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read(self, kind: str) -> list[dict]:
        """jsonl을 읽는다. 손상된 줄이 있으면 거부한다 (상한·중복 판정이 틀어지지 않도록 fail-closed)."""
        path = self._jsonl(kind)
        if not path.exists():
            return []
        entries: list[dict] = []
        for n, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LoopError(
                    f"메모리 손상: {path} {n}번째 줄 ({exc}) — 해당 줄을 고친 뒤 다시 실행하세요"
                ) from exc
            if not isinstance(entry, dict):
                raise LoopError(f"메모리 손상: {path} {n}번째 줄이 객체가 아닙니다")
            entries.append(entry)
        return entries

    def add_lesson(self, run_id: str, at: datetime, lesson: str) -> None:
        with self.skill_path.open("a", encoding="utf-8") as fh:
            fh.write(f"- {at.date().isoformat()} [{run_id}] {lesson.strip()}\n")


def already_triggered(mem: Memory, trigger_key: str) -> bool:
    return any(
        h.get("event") == "started" and h.get("trigger_key") == trigger_key
        for h in mem.read("history")
    )


# ---------------------------------------------------------------------------
# ②④⑤ 실행 시작 — 가드(중복·상한·동시 실행) + 서브에이전트 격리 작업 폴더
# ---------------------------------------------------------------------------


def _load_run(run_dir: Path) -> dict:
    meta = _read_json(run_dir / "run.json", "실행 메타")
    if not isinstance(meta, dict) or meta.get("status") not in STATUSES:
        raise LoopError(f"실행 메타가 손상되었습니다: {run_dir / 'run.json'}")
    return meta


def resolve_run_dir(paths: Paths, arg: str) -> Path:
    p = Path(arg)
    if (p / "run.json").is_file():
        return p
    if loopstation.RUN_ID_RE.match(arg):
        matches = sorted(paths.runs.glob(f"*/{arg}/run.json"))
        if len(matches) == 1:
            return matches[0].parent
    raise LoopError(f"실행 폴더를 찾을 수 없습니다: {arg}")


def _transition(
    mem: Memory,
    run_dir: Path,
    meta: dict,
    *,
    status: str,
    at: datetime,
    event: str,
    **detail,
) -> None:
    meta["status"] = status
    meta["updated_at"] = at.isoformat()
    _write_json(run_dir / "run.json", meta)
    mem.save_state(
        status=status,
        run_id=meta["run_id"],
        round=meta["round"],
        updated_at=at.isoformat(),
    )
    mem.append(
        "history",
        {"at": at.isoformat(), "run_id": meta["run_id"], "event": event, **detail},
    )


def start_run(
    paths: Paths, spec: dict, at: datetime, event: dict | None = None
) -> Path:
    """트리거를 확인하고 가드를 통과하면 실행 폴더를 만든다. 실행 폴더 경로를 돌려준다."""
    trig = spec["trigger"]
    loop_id = spec["loop_id"]
    tz = parse_offset(trig["utc_offset"])
    mem = Memory(paths, loop_id)
    mem.ensure(spec)

    state = mem.state()
    if state["status"] in ACTIVE_STATUSES:
        raise LoopError(
            f"진행 중인 실행이 있습니다: {state['run_id']} ({STATUS_LABELS[state['status']]}) — "
            "그 실행을 끝내거나 검토를 마친 뒤 시작하세요"
        )

    if trig["type"] == "schedule":
        if event is not None:
            raise LoopError("시간 기반 루프에는 이벤트를 넘기지 않습니다")
        trigger_key = schedule_slot(spec, at)
        if trigger_key is None:
            raise LoopError(
                f"예약 시각이 아닙니다: {', '.join(trig['weekdays'])} {trig['time']} "
                f"({trig['utc_offset']}) 부터 {trig.get('window_minutes', DEFAULT_WINDOW_MINUTES)}분 안에만 발동"
            )
        priority = "normal"
    else:
        if event is None:
            raise LoopError("이벤트 기반 루프는 --event 로 이벤트를 넘겨야 합니다")
        ev_errors = validate_event(event)
        if ev_errors:
            raise LoopError("이벤트 형식 오류:\n  - " + "\n  - ".join(ev_errors))
        priority = match_event(spec, event)
        if priority is None:
            raise LoopError(
                f"이벤트 {event['id']}가 트리거 조건(출처·키워드)과 맞지 않습니다"
            )
        trigger_key = f"event:{event['id']}"

    if already_triggered(mem, trigger_key):
        raise LoopError(f"이미 처리한 트리거입니다: {trigger_key} (중복 실행 방지)")

    local = at.astimezone(tz)
    local_date = local.date().isoformat()
    started_today = sum(
        1
        for h in mem.read("history")
        if h.get("event") == "started" and h.get("local_date") == local_date
    )
    cap = spec["stop_conditions"]["daily_run_cap"]
    if started_today >= cap:
        mem.append(
            "history",
            {
                "at": at.isoformat(),
                "run_id": None,
                "event": "blocked",
                "reason": "daily_run_cap",
                "trigger_key": trigger_key,
            },
        )
        raise LoopError(
            f"일일 실행 상한 도달: {local_date} {started_today}/{cap}회 — 다음 날로 넘깁니다"
        )

    run_id = f"{local:%Y%m%d-%H%M%S}-{loop_id}"
    run_dir = paths.runs / loop_id / run_id
    if run_dir.exists():
        raise LoopError(f"같은 run_id의 실행 폴더가 이미 있습니다: {run_dir}")

    workers = []
    for s in sorted(spec["subagents"], key=lambda s: s["group"]):
        (run_dir / "workers" / s["role"]).mkdir(parents=True)
        workers.append(
            {
                "role": s["role"],
                "task": s["task"],
                "group": s["group"],
                "output": f"workers/{s['role']}/output.json",
            }
        )
    (run_dir / "attachments").mkdir(parents=True)
    meta = {
        "schema_version": SCHEMA_VERSION,
        "loop_id": loop_id,
        "run_id": run_id,
        "started_at": at.isoformat(),
        "updated_at": at.isoformat(),
        "trigger_type": trig["type"],
        "trigger_key": trigger_key,
        "priority": priority,
        "event": event,
        "isolation": spec["worktree"]["isolation"],
        "round": 1,
        "status": "running",
        "workers": workers,
    }
    _write_json(run_dir / "run.json", meta)
    _write_json(
        run_dir / "report.json",
        {"summary": "", "improvements": [], "attachments": [], "resolutions": {}},
    )
    mem.save_state(status="running", run_id=run_id, round=1, updated_at=at.isoformat())
    mem.append(
        "history",
        {
            "at": at.isoformat(),
            "run_id": run_id,
            "event": "started",
            "trigger_key": trigger_key,
            "local_date": local_date,
            "priority": priority,
        },
    )
    return run_dir


# ---------------------------------------------------------------------------
# ⑤ 워크트리 병합 — 각자 결과는 그대로 두고, 서로 다른 부분은 충돌로 표시
# ---------------------------------------------------------------------------


def merge_run(paths: Paths, run_dir: Path, at: datetime | None = None) -> dict:
    at = at or _now()
    meta = _load_run(run_dir)
    if meta["status"] != "running":
        raise LoopError(
            f"진행 중인 실행만 병합할 수 있습니다 (현재 {STATUS_LABELS[meta['status']]})"
        )
    mem = Memory(paths, meta["loop_id"])

    merged: dict = {}
    agreed_by: dict[str, list[str]] = {}
    conflicts: dict[str, dict] = {}
    failed: list[dict] = []
    ok: list[str] = []
    for w in meta["workers"]:
        role, out = w["role"], run_dir / w["output"]
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
        except FileNotFoundError:
            failed.append({"role": role, "reason": "산출물 없음"})
            continue
        except (OSError, json.JSONDecodeError) as exc:
            failed.append({"role": role, "reason": f"읽기 실패: {exc}"})
            continue
        findings = data.get("findings") if isinstance(data, dict) else None
        if not isinstance(findings, dict):
            failed.append({"role": role, "reason": "findings 객체 없음"})
            continue
        ok.append(role)
        for key, value in findings.items():
            if key in conflicts:
                conflicts[key][role] = value
            elif key not in merged:
                merged[key] = value
                agreed_by[key] = [role]
            elif merged[key] == value:
                agreed_by[key].append(role)
            else:
                conflicts[key] = {r: merged[key] for r in agreed_by.pop(key)}
                conflicts[key][role] = value
                del merged[key]

    if not ok:
        mem.append(
            "history",
            {"at": at.isoformat(), "run_id": meta["run_id"], "event": "merge_failed"},
        )
        raise LoopError(
            "모든 서브에이전트 결과가 없거나 손상되었습니다 — 병합할 결과가 없습니다"
        )

    result = {
        "run_id": meta["run_id"],
        "merged_at": at.isoformat(),
        "ok_workers": ok,
        "failed_workers": failed,
        "merged": merged,
        "agreed_by": agreed_by,
        "conflicts": [{"key": k, "values": v} for k, v in conflicts.items()],
    }
    _write_json(run_dir / "merged.json", result)
    _transition(
        mem,
        run_dir,
        meta,
        status="running",
        at=at,
        event="merged",
        conflicts=len(conflicts),
        failed_workers=len(failed),
    )
    return result


# ---------------------------------------------------------------------------
# ⑥ 스킬 자가진단 + 중단 조건 (완료 3조건 · 충돌 해소 · 98점 게이트 · 회전 상한)
# ---------------------------------------------------------------------------


def evaluate_report(
    spec: dict, run_dir: Path, meta: dict, record_path: Path
) -> tuple[list[str], dict]:
    stop = spec["stop_conditions"]
    problems: list[str] = []
    metrics: dict = {}

    try:
        report = _read_json(run_dir / "report.json", "보고서")
    except LoopError as exc:
        return [str(exc)], metrics
    if not isinstance(report, dict):
        return ["보고서(report.json)는 JSON 객체여야 합니다"], metrics

    summary = report.get("summary")
    n_chars = len(summary.strip()) if isinstance(summary, str) else 0
    metrics["summary_chars"] = n_chars
    if n_chars == 0:
        problems.append("요약이 비어 있습니다")
    elif n_chars > stop["summary_max_chars"]:
        problems.append(
            f"요약 {n_chars}자 > 상한 {stop['summary_max_chars']}자 (공백 포함)"
        )

    improvements = report.get("improvements")
    n_imp = (
        sum(1 for s in improvements if _is_str(s))
        if isinstance(improvements, list)
        else 0
    )
    metrics["improvements"] = n_imp
    if n_imp < stop["min_improvements"]:
        problems.append(f"개선 제안 {n_imp}건 < 최소 {stop['min_improvements']}건")

    attachments = report.get("attachments")
    attachments = attachments if isinstance(attachments, list) else []
    base = run_dir.resolve()
    found = 0
    for a in attachments:
        if not _is_str(a):
            problems.append(f"첨부 경로가 문자열이 아닙니다: {a!r}")
            continue
        target = (run_dir / a).resolve()
        if not target.is_relative_to(base):
            problems.append(f"첨부가 실행 폴더 밖을 가리킵니다: {a}")
        elif not target.is_file():
            problems.append(f"첨부 파일이 없습니다: {a}")
        else:
            found += 1
    metrics["attachments"] = found
    if found < stop["min_attachments"]:
        problems.append(f"첨부 파일 {found}개 < 최소 {stop['min_attachments']}개")

    if meta["workers"]:
        merged_path = run_dir / "merged.json"
        if not merged_path.is_file():
            problems.append("서브에이전트 결과를 아직 병합(merge)하지 않았습니다")
        else:
            merged = _read_json(merged_path, "병합 결과")
            if not isinstance(merged, dict) or not isinstance(
                merged.get("conflicts"), list
            ):
                return problems + [
                    "병합 결과(merged.json)가 손상되었습니다 — merge를 다시 실행하세요"
                ], metrics
            resolutions = report.get("resolutions")
            resolutions = resolutions if isinstance(resolutions, dict) else {}
            open_keys = [
                c["key"]
                for c in merged.get("conflicts", [])
                if not _is_str(resolutions.get(c["key"]))
            ]
            metrics["unresolved_conflicts"] = len(open_keys)
            if open_keys:
                problems.append(
                    f"충돌 미해결 {len(open_keys)}건: {', '.join(open_keys)} (report.resolutions에 결정 근거 기재)"
                )

    if spec["skill"]["self_check"]["gate_record"]:
        if not record_path.is_file():
            problems.append(
                f"자가진단 기록이 없습니다: {record_path} (loopstation 98점 게이트)"
            )
        else:
            rec, errors = loopstation.load_and_validate(record_path)
            if errors or rec is None:
                problems.append("자가진단 기록 검증 실패: " + "; ".join(errors))
            elif not rec["passed"]:
                problems.append(f"자가진단 게이트 미통과: {rec['final_total']}/100")
            else:
                metrics["gate_score"] = rec["final_total"]
    return problems, metrics


def check_run(
    paths: Paths,
    run_dir: Path,
    record_path: Path | None = None,
    at: datetime | None = None,
) -> dict:
    """완료 조건을 판정한다. 통과 → 사람 검토 대기, 실패 → 다음 회전, 상한 도달 → 중단."""
    at = at or _now()
    meta = _load_run(run_dir)
    if meta["status"] != "running":
        raise LoopError(
            f"진행 중인 실행만 판정할 수 있습니다 (현재 {STATUS_LABELS[meta['status']]})"
        )
    spec = load_spec(paths, meta["loop_id"])
    mem = Memory(paths, meta["loop_id"])
    record_path = record_path or (paths.records / f"{meta['run_id']}.json")

    problems, metrics = evaluate_report(spec, run_dir, meta, record_path)
    passed = not problems
    checked_round = meta["round"]
    max_rounds = spec["stop_conditions"]["max_rounds"]
    if passed:
        status = "awaiting_review" if spec["human_review"]["required"] else "done"
        event = "checked_pass"
    elif checked_round >= max_rounds:
        status, event = "halted", "halted"
    else:
        status, event = "running", "checked_revise"
        meta["round"] = checked_round + 1

    evaluation = {
        "at": at.isoformat(),
        "run_id": meta["run_id"],
        "kind": "self_check",
        "round": checked_round,
        "passed": passed,
        "problems": problems,
        "metrics": metrics,
        "next_status": status,
    }
    mem.append("evaluations", evaluation)
    _transition(
        mem, run_dir, meta, status=status, at=at, event=event, round=checked_round
    )
    return evaluation


# ---------------------------------------------------------------------------
# ⑦ 사람 검토 — 승인해야 완료, 교훈은 스킬 메모리로
# ---------------------------------------------------------------------------


def review_run(
    paths: Paths,
    run_dir: Path,
    *,
    decision: str,
    reviewer: str,
    note: str,
    lesson: str | None = None,
    at: datetime | None = None,
) -> dict:
    at = at or _now()
    if decision not in DECISIONS:
        raise LoopError(f"decision은 {DECISIONS} 중 하나여야 합니다")
    if not _is_str(reviewer) or not _is_str(note):
        raise LoopError("검토자(reviewer)와 검토 의견(note)은 비워 둘 수 없습니다")
    meta = _load_run(run_dir)
    if meta["status"] != "awaiting_review":
        raise LoopError(
            f"사람 검토 대기 상태에서만 검토할 수 있습니다 (현재 {STATUS_LABELS[meta['status']]})"
        )
    spec = load_spec(paths, meta["loop_id"])
    mem = Memory(paths, meta["loop_id"])

    reviewed_round = meta["round"]
    if decision == "approve":
        status, event = "done", "approved"
    elif reviewed_round >= spec["stop_conditions"]["max_rounds"]:
        status, event = "halted", "halted"
    else:
        status, event = "running", "revise_requested"
        meta["round"] = reviewed_round + 1

    entry = {
        "at": at.isoformat(),
        "run_id": meta["run_id"],
        "kind": "human_review",
        "round": reviewed_round,
        "decision": decision,
        "reviewer": reviewer.strip(),
        "note": note.strip(),
        "next_status": status,
    }
    mem.append("evaluations", entry)
    if lesson and lesson.strip():
        mem.add_lesson(meta["run_id"], at, lesson)
    _transition(
        mem, run_dir, meta, status=status, at=at, event=event, round=reviewed_round
    )
    return entry


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _load_events(path: Path) -> list[dict]:
    data = _read_json(path, "이벤트")
    events = data if isinstance(data, list) else [data]
    problems = []
    for i, ev in enumerate(events):
        problems += [f"[{i}] {e}" for e in validate_event(ev)]
    if problems:
        raise LoopError("이벤트 형식 오류:\n  - " + "\n  - ".join(problems))
    return events


def _cmd_validate(paths: Paths, files: list[str]) -> int:
    targets = [Path(f) for f in files] or sorted(paths.loops.glob("*.json"))
    if not targets:
        print("검증할 루프 명세가 없습니다", file=sys.stderr)
        return 1
    failed = False
    for path in targets:
        _, errors = load_spec_file(path, paths.repo_root)
        if errors:
            failed = True
            print(f"[실패] {path}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"[OK] {path}")
    return 1 if failed else 0


def _cmd_due(paths: Paths, at: datetime) -> int:
    hits = 0
    for spec in load_all_specs(paths):
        slot = schedule_slot(spec, at)
        if slot is None:
            continue
        hits += 1
        done = already_triggered(Memory(paths, spec["loop_id"]), slot)
        print(
            f"[발동] {spec['loop_id']} — 슬롯 {slot}{' (이미 실행됨)' if done else ''}"
        )
    if not hits:
        print(f"발동할 시간 기반 루프 없음 ({at.isoformat()})")
    return 0


def _cmd_match(paths: Paths, event_file: Path) -> int:
    queue, unmatched = triage(load_all_specs(paths), _load_events(event_file))
    if queue:
        print("처리 대기열 (긴급도 → 도착 순):")
        for n, q in enumerate(queue, start=1):
            print(
                f"  {n}. [{PRIORITY_LABELS[q['priority']]}] {q['event_id']} → {q['loop_id']} ({q['received_at']})"
            )
    for ev_id in unmatched:
        print(f"  - {ev_id}: 일치하는 루프 없음 (처리하지 않음)")
    return 0


def _cmd_status(paths: Paths, loop_id: str) -> int:
    spec = load_spec(paths, loop_id)
    mem = Memory(paths, loop_id)
    state = mem.state()
    print(f"{spec['title']} ({loop_id})")
    print(
        f"  상태: {STATUS_LABELS[state['status']]} · 실행 {state['run_id'] or '—'} · 회전 {state['round']}"
    )
    history = mem.read("history")
    for h in history[-5:]:
        print(f"  {h.get('at')} {h.get('event')} {h.get('run_id') or ''}".rstrip())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="루프 정석(Loop Canon) 실행기")
    parser.add_argument(
        "--root", type=Path, default=DEFAULT_PATHS.root, help=argparse.SUPPRESS
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate", help="루프 명세 검증")
    p.add_argument("files", nargs="*")
    p = sub.add_parser("due", help="지금(또는 --at) 발동할 시간 기반 루프")
    p.add_argument("--at")
    p = sub.add_parser("match", help="이벤트를 루프에 배정하고 긴급도 순 대기열 출력")
    p.add_argument("--event", required=True, type=Path)
    p = sub.add_parser("start", help="트리거 확인 + 가드 통과 시 실행 폴더 생성")
    p.add_argument("loop_id")
    p.add_argument("--at")
    p.add_argument("--event", type=Path)
    p = sub.add_parser("merge", help="서브에이전트 결과 병합 (충돌 표시)")
    p.add_argument("run")
    p = sub.add_parser("check", help="완료 조건·중단 조건 판정")
    p.add_argument("run")
    p.add_argument("--record", type=Path)
    p = sub.add_parser("review", help="사람 검토 기록 (승인해야 완료)")
    p.add_argument("run")
    p.add_argument("--decision", required=True, choices=DECISIONS)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--note", required=True)
    p.add_argument("--lesson")
    p = sub.add_parser("status", help="루프 상태와 최근 이력")
    p.add_argument("loop_id")

    args = parser.parse_args(argv)
    paths = Paths(args.root.resolve())

    try:
        if args.cmd == "validate":
            return _cmd_validate(paths, args.files)
        if args.cmd == "due":
            return _cmd_due(paths, parse_time(args.at) if args.at else _now())
        if args.cmd == "match":
            return _cmd_match(paths, args.event)
        if args.cmd == "start":
            spec = load_spec(paths, args.loop_id)
            event = None
            if args.event:
                events = _load_events(args.event)
                if len(events) != 1:
                    raise LoopError(
                        "start --event 에는 이벤트 1건만 넘깁니다 (여러 건은 match로 대기열부터)"
                    )
                event = events[0]
            run_dir = start_run(
                paths, spec, parse_time(args.at) if args.at else _now(), event
            )
            print(f"[시작] {run_dir}")
            for s in sorted(spec["subagents"], key=lambda s: s["group"]):
                print(
                    f"  group {s['group']} · {s['role']}: {s['task']} → workers/{s['role']}/output.json"
                )
            print(
                f"  스킬 메모리 먼저 읽기: {Memory(paths, spec['loop_id']).skill_path}"
            )
            return 0
        if args.cmd == "merge":
            result = merge_run(paths, resolve_run_dir(paths, args.run))
            print(
                f"[병합] 성공 {len(result['ok_workers'])} · 실패 {len(result['failed_workers'])} · "
                f"합의 {len(result['merged'])} · 충돌 {len(result['conflicts'])}"
            )
            for f in result["failed_workers"]:
                print(f"  실패: {f['role']} — {f['reason']}")
            for c in result["conflicts"]:
                print(f"  충돌: {c['key']} — {', '.join(c['values'])}")
            return 0
        if args.cmd == "check":
            ev = check_run(paths, resolve_run_dir(paths, args.run), args.record)
            label = "통과" if ev["passed"] else "미충족"
            print(
                f"[판정] 회전 {ev['round']} {label} → {STATUS_LABELS[ev['next_status']]}"
            )
            for prob in ev["problems"]:
                print(f"  - {prob}")
            return 0 if ev["passed"] else 1
        if args.cmd == "review":
            entry = review_run(
                paths,
                resolve_run_dir(paths, args.run),
                decision=args.decision,
                reviewer=args.reviewer,
                note=args.note,
                lesson=args.lesson,
            )
            print(f"[검토] {entry['decision']} → {STATUS_LABELS[entry['next_status']]}")
            return 0
        if args.cmd == "status":
            return _cmd_status(paths, args.loop_id)
    except LoopError as exc:
        print(f"[거부] {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
