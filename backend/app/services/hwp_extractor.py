"""
Plain-text extraction from HWP / HWPX files.

HWPX (modern, ZIP+XML): parsed in-stdlib via zipfile + ElementTree.
HWP  (legacy OLE compound document): reads the `PrvText` preview stream
via `olefile`. Full body parsing requires walking the BodyText record
stream per the HWP5 binary spec and is out of scope here — callers
should treat extraction as best-effort preview text for .hwp.
"""
from __future__ import annotations

import io
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import olefile
from olefile.olefile import NotOleFileError


HWPX_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HWPX_PARA_TAG = f"{{{HWPX_NS}}}p"
HWPX_TEXT_TAG = f"{{{HWPX_NS}}}t"


class HwpExtractionError(Exception):
    pass


def detect_format(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in {"hwp", "hwpx"}:
        raise HwpExtractionError(f"Unsupported extension: .{ext}")
    return ext


def extract_text(path: str, fmt: str) -> str:
    if fmt == "hwpx":
        return _extract_hwpx(path)
    if fmt == "hwp":
        return _extract_hwp_preview(path)
    raise HwpExtractionError(f"Unsupported format: {fmt}")


def _extract_hwpx(path: str) -> str:
    parts: list[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            section_names = sorted(
                n for n in zf.namelist()
                if n.startswith("Contents/section") and n.endswith(".xml")
            )
            if not section_names:
                raise HwpExtractionError("HWPX archive has no Contents/section*.xml")

            for name in section_names:
                with zf.open(name) as f:
                    tree = ET.parse(f)
                for para in tree.iter(HWPX_PARA_TAG):
                    chunks = [t.text for t in para.iter(HWPX_TEXT_TAG) if t.text]
                    if chunks:
                        parts.append("".join(chunks))
                    parts.append("\n")
    except zipfile.BadZipFile as e:
        raise HwpExtractionError(f"Not a valid HWPX (zip) file: {e}") from e

    return "".join(parts).strip()


def _extract_hwp_preview(path: str) -> str:
    try:
        ole = olefile.OleFileIO(path)
    except (OSError, NotOleFileError) as e:
        raise HwpExtractionError(f"Not a valid HWP (OLE) file: {e}") from e

    try:
        if not ole.exists("PrvText"):
            raise HwpExtractionError(
                "HWP has no PrvText preview stream; full-body extraction is not supported"
            )
        with ole.openstream("PrvText") as stream:
            raw = stream.read()
    finally:
        ole.close()

    return raw.decode("utf-16-le", errors="replace").rstrip("\x00").strip()
