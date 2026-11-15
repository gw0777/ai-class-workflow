"""GitHub 저장소에서 문서를 수집해 코퍼스에 추가한다.

spec 형식: owner/repo[@ref][:subpath]
    예) gw0777/ai-class-workflow
        gw0777/papers@main:published/
"""
from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass

from .extract import SUPPORTED_EXTS, extract
from .online import GITHUB_API, HttpClient

_SPEC_RE = re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)(?:@(?P<ref>[^:]+))?(?::(?P<path>.+))?$")


@dataclass
class RepoSpec:
    owner: str
    repo: str
    ref: str | None = None
    path: str = ""

    @classmethod
    def parse(cls, spec: str) -> "RepoSpec":
        m = _SPEC_RE.match(spec.strip().removeprefix("https://github.com/"))
        if not m:
            raise ValueError(f"잘못된 저장소 지정: {spec} (형식: owner/repo[@ref][:path])")
        return cls(m["owner"], m["repo"], m["ref"], (m["path"] or "").strip("/"))


def _headers(token: str | None) -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = token or os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def list_repo_files(spec: RepoSpec, client: HttpClient, token: str | None = None) -> tuple[str, list[dict]]:
    """(ref, [{path, size, sha}]) — 지원 형식 파일만."""
    h = _headers(token)
    ref = spec.ref
    if not ref:
        info = client.get_json(f"{GITHUB_API}/repos/{spec.owner}/{spec.repo}", headers=h)
        ref = info.get("default_branch", "main")
    tree = client.get_json(f"{GITHUB_API}/repos/{spec.owner}/{spec.repo}/git/trees/{ref}", {"recursive": "1"}, h)
    files = []
    for node in tree.get("tree", []):
        if node.get("type") != "blob":
            continue
        p = node["path"]
        if spec.path and not p.startswith(spec.path + "/") and p != spec.path:
            continue
        if os.path.splitext(p)[1].lower() in SUPPORTED_EXTS:
            files.append({"path": p, "size": node.get("size", 0), "sha": node.get("sha", "")})
    return ref, files


def download_raw(spec: RepoSpec, ref: str, path: str, token: str | None = None, timeout: float = 60.0) -> bytes:
    import requests

    h = _headers(token)
    h["Accept"] = "application/vnd.github.raw+json"
    r = requests.get(f"{GITHUB_API}/repos/{spec.owner}/{spec.repo}/contents/{path}", params={"ref": ref},
                     headers=h, timeout=timeout)
    r.raise_for_status()
    return r.content


def fetch_repo_documents(spec_str: str, client: HttpClient | None = None, token: str | None = None,
                         max_size: int = 30 * 1024 * 1024, downloader=None):
    """generator: (source_label, title, text, kind, warnings)"""
    client = client or HttpClient(timeout=30)
    spec = RepoSpec.parse(spec_str)
    ref, files = list_repo_files(spec, client, token)
    downloader = downloader or (lambda p: download_raw(spec, ref, p, token))
    for f in files:
        if f["size"] > max_size:
            continue
        data = downloader(f["path"])
        ext = os.path.splitext(f["path"])[1].lower()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            doc = extract(tmp_path)
        finally:
            os.unlink(tmp_path)
        label = f"github:{spec.owner}/{spec.repo}@{ref}/{f['path']}"
        title = doc.title if doc.title != os.path.basename(tmp_path) else os.path.basename(f["path"])
        yield label, title, doc.text, doc.kind, doc.warnings
