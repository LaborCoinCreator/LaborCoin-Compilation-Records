from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid JSON {path}: {exc}") from exc


def normalize_hex(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("bytecode is not a string")
    value = value[2:] if value.startswith("0x") else value
    if not value or len(value) % 2 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
        raise ValueError("bytecode is not complete hexadecimal data")
    return "0x" + value.lower()


def find_hex(obj: Any, keys: set[str]) -> str | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys:
                if isinstance(value, str) and value:
                    try:
                        return normalize_hex(value)
                    except ValueError:
                        pass
                if isinstance(value, dict) and isinstance(value.get("object"), str):
                    try:
                        return normalize_hex(value["object"])
                    except ValueError:
                        pass
            found = find_hex(value, keys)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_hex(value, keys)
            if found:
                return found
    return None


def compiler_diagnostics(build_info: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    output = build_info.get("output", {}) if isinstance(build_info, dict) else {}
    raw = output.get("errors", []) if isinstance(output, dict) else []
    diagnostics = []
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict):
            diagnostics.append({
                "severity": item.get("severity"),
                "type": item.get("type"),
                "message": item.get("formattedMessage") or item.get("message"),
            })
    if any(item.get("severity") == "error" for item in diagnostics):
        raise ValueError("compiler build-info contains error diagnostics")
    status = "ZERO_DIAGNOSTICS" if not diagnostics else f"WARNINGS_RECORDED:{len(diagnostics)}"
    return status, diagnostics


def validate_build_profile(build_info: dict[str, Any]) -> None:
    blob = json.dumps(build_info, separators=(",", ":"), sort_keys=True).lower()
    markers = [
        "0.8.36",
        '"optimizer":{"enabled":true,"runs":200',
        '"evmversion":"prague"',
        '"viair":false',
        '"bytecodehash":"ipfs"',
    ]
    missing = [marker for marker in markers if marker not in blob]
    if missing:
        raise ValueError("build-info is missing required compiler marker(s): " + ", ".join(missing))


def render_manifest_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Revision 7.2 Master Compilation Manifest",
        "",
        f"**Release status:** {manifest.get('status', 'UNKNOWN')}",
        f"**Artifact status:** {manifest.get('artifact_status', 'UNKNOWN')}",
        f"**Source freeze commit:** `{manifest.get('source_repository', {}).get('source_freeze_commit', 'UNRECORDED')}`",
        "**Deployment authorization:** NONE",
        "",
        "| Order | Component | Folder | Compilation status |",
        "|---:|---|---|---|",
    ]
    for entry in sorted(manifest.get("contracts", []), key=lambda item: item["order"]):
        lines.append(
            f"| {entry['order']} | {entry['version']} | `{entry['folder']}` | {entry['status']} |"
        )
    lines += [
        "",
        "The JSON manifest is authoritative for exact hashes, artifact names, bytecode commitments, and compiler diagnostics.",
        "This Markdown file is generated from the JSON manifest and must not be edited independently.",
        "",
    ]
    return "\n".join(lines)


def atomic_write_text(path: Path, text: str) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(path)


def atomic_write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def required_zip_members(entry: dict[str, Any]) -> list[str]:
    contract = entry["contract"]
    artifacts = entry["artifacts"]
    return [
        f"{contract}.sol",
        f"{contract}_Remix.sol",
        "compiler-settings.json",
        "SOURCE-RECORD.json",
        artifacts["artifact"],
        artifacts["metadata"],
        artifacts["build_info"],
        "COMPILATION-RECORD.json",
    ]
