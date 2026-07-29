from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from keccak256 import keccak256_hex
from manifest_tools import (
    compiler_diagnostics,
    find_hex,
    load_json,
    render_manifest_markdown,
    required_zip_members,
    sha256_file,
    validate_build_profile,
    validate_compiler_input_source,
)

ROOT = Path(__file__).resolve().parent
manifest_path = ROOT / "MASTER_COMPILATION_MANIFEST.json"
manifest = load_json(manifest_path)
failures: list[str] = []
pending: list[str] = []


def fail(folder: str, message: str) -> None:
    failures.append(f"{folder}: {message}")


def keccak_hex(hexdata: str) -> str:
    value = hexdata[2:] if hexdata.startswith("0x") else hexdata
    return keccak256_hex(bytes.fromhex(value))


expected_markdown = render_manifest_markdown(manifest)
markdown_path = ROOT / "MASTER_COMPILATION_MANIFEST.md"
if not markdown_path.is_file():
    failures.append("root: missing MASTER_COMPILATION_MANIFEST.md")
elif markdown_path.read_text(encoding="utf-8") != expected_markdown:
    failures.append("root: Markdown manifest is not synchronized with authoritative JSON")

source_commit = manifest.get("source_repository", {}).get("source_freeze_commit", "")
source_commit_valid = isinstance(source_commit, str) and len(source_commit) == 40 and all(
    ch in "0123456789abcdef" for ch in source_commit.lower()
)

contracts = sorted(manifest.get("contracts", []), key=lambda item: item.get("order", 0))
if len(contracts) != 7 or [entry.get("order") for entry in contracts] != list(range(1, 8)):
    failures.append("root: manifest must contain exactly seven contracts in order 1 through 7")

for entry in contracts:
    folder_name = entry["folder"]
    folder = ROOT / folder_name
    contract = entry["contract"]
    source = folder / f"{contract}.sol"
    remix_source = folder / f"{contract}_Remix.sol"
    settings = folder / "compiler-settings.json"
    source_record_path = folder / "SOURCE-RECORD.json"

    for path, key in [
        (source, "source_sha256"),
        (remix_source, "remix_source_sha256"),
        (settings, "compiler_settings_sha256"),
        (source_record_path, "source_record_sha256"),
    ]:
        if not path.is_file():
            fail(folder_name, f"missing {path.name}")
        elif sha256_file(path) != entry.get(key):
            fail(folder_name, f"{path.name} hash mismatch")

    if source_record_path.is_file():
        try:
            source_record = load_json(source_record_path)
            if source_record.get("record_type") != "SOURCE_FREEZE":
                fail(folder_name, "SOURCE-RECORD.json is not source-only")
            if source_record.get("contract") != contract:
                fail(folder_name, "SOURCE-RECORD.json contract mismatch")
            if source_record.get("expected_artifacts") != entry.get("artifacts"):
                fail(folder_name, "SOURCE-RECORD.json artifact names mismatch")
            forbidden_dynamic = {
                "status", "artifact_sha256", "metadata_sha256", "build_info_sha256",
                "creation_bytecode_keccak256", "runtime_template_keccak256", "compiler_diagnostics",
            }
            if forbidden_dynamic.intersection(source_record):
                fail(folder_name, "SOURCE-RECORD.json contains dynamic compilation fields")
        except ValueError as exc:
            fail(folder_name, str(exc))

    artifacts = entry["artifacts"]
    artifact_paths = {key: folder / value for key, value in artifacts.items() if key != "sealed_record"}
    record_path = folder / "COMPILATION-RECORD.json"
    zip_path = folder / artifacts["sealed_record"]

    if entry.get("status") == "PENDING_COMPILATION":
        unexpected = [path.name for path in [*artifact_paths.values(), record_path, zip_path] if path.exists()]
        if unexpected:
            fail(folder_name, "unrecorded artifact files are present: " + ", ".join(unexpected))
        pending.append(contract)
        continue

    if entry.get("status") != "RECORDED_PREDEPLOYMENT":
        fail(folder_name, f"unsupported status {entry.get('status')}")
        continue

    required_paths = [*artifact_paths.values(), record_path, zip_path]
    missing = [path.name for path in required_paths if not path.is_file()]
    if missing:
        fail(folder_name, "missing recorded files: " + ", ".join(missing))
        continue

    try:
        artifact = load_json(artifact_paths["artifact"])
        metadata = load_json(artifact_paths["metadata"])
        build_info = load_json(artifact_paths["build_info"])
        record = load_json(record_path)
        validate_build_profile(build_info)
        validate_compiler_input_source(
            build_info, metadata, remix_source, contract
        )
        diagnostic_status, diagnostics = compiler_diagnostics(build_info)
    except ValueError as exc:
        fail(folder_name, str(exc))
        continue

    hash_pairs = [
        ("artifact_sha256", artifact_paths["artifact"]),
        ("metadata_sha256", artifact_paths["metadata"]),
        ("build_info_sha256", artifact_paths["build_info"]),
        ("compilation_record_sha256", record_path),
        ("sealed_record_sha256", zip_path),
    ]
    for key, path in hash_pairs:
        actual = sha256_file(path)
        if entry.get(key) != actual:
            fail(folder_name, f"master manifest {key} mismatch")
        if key != "sealed_record_sha256" and key != "compilation_record_sha256" and record.get(key) != actual:
            fail(folder_name, f"COMPILATION-RECORD.json {key} mismatch")

    for key in ["source_sha256", "remix_source_sha256", "compiler_settings_sha256", "source_record_sha256"]:
        if record.get(key) != entry.get(key):
            fail(folder_name, f"COMPILATION-RECORD.json {key} mismatch")

    creation = find_hex(artifact, {"bytecode"})
    runtime = find_hex(artifact, {"deployedBytecode", "runtimeBytecode"})
    if not creation or not runtime:
        fail(folder_name, "artifact bytecode could not be extracted")
    else:
        expected_values = {
            "creation_bytecode_bytes": (len(creation) - 2) // 2,
            "runtime_template_bytes": (len(runtime) - 2) // 2,
            "creation_bytecode_keccak256": keccak_hex(creation),
            "runtime_template_keccak256": keccak_hex(runtime),
        }
        for key, actual in expected_values.items():
            if entry.get(key) != actual:
                fail(folder_name, f"master manifest {key} mismatch")
            if record.get(key) != actual:
                fail(folder_name, f"COMPILATION-RECORD.json {key} mismatch")

    if entry.get("compiler_diagnostics") != diagnostic_status or record.get("compiler_diagnostics") != diagnostic_status:
        fail(folder_name, "compiler diagnostic status mismatch")
    if record.get("diagnostics") != diagnostics:
        fail(folder_name, "compiler diagnostic contents mismatch")
    if record.get("status") != "RECORDED_PREDEPLOYMENT" or record.get("contract") != contract:
        fail(folder_name, "compilation record identity/status mismatch")

    try:
        with zipfile.ZipFile(zip_path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                fail(folder_name, f"corrupt ZIP member {bad_member}")
            expected_members = required_zip_members(entry)
            actual_members = archive.namelist()
            if actual_members != expected_members:
                fail(folder_name, "sealed ZIP member list or order mismatch")
            for member in expected_members:
                loose = folder / member
                if loose.is_file() and archive.read(member) != loose.read_bytes():
                    fail(folder_name, f"sealed ZIP member differs from loose file: {member}")
    except Exception as exc:
        fail(folder_name, f"invalid sealed ZIP: {exc}")

if failures:
    print("MASTER COMPILATION VERIFICATION: FAIL")
    for failure in failures:
        print("-", failure)
    sys.exit(1)

if pending:
    print("MASTER COMPILATION VERIFICATION: PRECOMPILATION PENDING")
    print("Missing Revision 7.2 records:")
    for contract in pending:
        print("-", contract)
    sys.exit(2)

if not source_commit_valid:
    print("MASTER COMPILATION VERIFICATION: FAIL")
    print("- root: source_freeze_commit must be a full 40-character Git commit before final PASS")
    sys.exit(1)

if manifest.get("artifact_status") != "RECORDED_PREDEPLOYMENT":
    print("MASTER COMPILATION VERIFICATION: FAIL")
    print("- root: all contracts are recorded but artifact_status is not RECORDED_PREDEPLOYMENT")
    sys.exit(1)

print("MASTER COMPILATION VERIFICATION: PASS")
print("Seven source records, loose artifact sets, bytecode commitments, compilation records, and sealed ZIP contents verified.")
print("Deployment tests and on-chain runtime verification remain separate gates.")
