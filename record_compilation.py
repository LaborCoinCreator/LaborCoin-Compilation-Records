from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

from keccak256 import keccak256_hex
from manifest_tools import (
    atomic_write_json,
    atomic_write_text,
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
MANIFEST_PATH = ROOT / "MASTER_COMPILATION_MANIFEST.json"


def keccak_hex(hexdata: str) -> str:
    value = hexdata[2:] if hexdata.startswith("0x") else hexdata
    return keccak256_hex(bytes.fromhex(value))


def deterministic_zip(zip_path: Path, files: list[Path]) -> None:
    temp = zip_path.with_name(zip_path.name + ".tmp")
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    temp.replace(zip_path)


parser = argparse.ArgumentParser(description="Validate and seal one LaborCoin compilation artifact set.")
parser.add_argument("folder", help="Numbered component folder, for example 01-policy")
parser.add_argument(
    "--replace",
    action="store_true",
    help="Explicitly replace a previously recorded predeployment artifact set. Never use after final publication.",
)
args = parser.parse_args()

manifest = load_json(MANIFEST_PATH)
source_commit = manifest.get("source_repository", {}).get("source_freeze_commit", "")
if not isinstance(source_commit, str) or len(source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in source_commit.lower()):
    raise SystemExit(
        "Record the full LaborCoin source-freeze commit first: python set_source_commit.py <40-character-commit>"
    )
entry = next((item for item in manifest["contracts"] if item["folder"] == args.folder), None)
if entry is None:
    raise SystemExit(f"Unknown component folder: {args.folder}")
if entry["status"] != "PENDING_COMPILATION" and not args.replace:
    raise SystemExit(
        f"{entry['contract']} is already recorded. Stop, review the existing record, or rerun with --replace only before final publication."
    )

folder = ROOT / args.folder
contract = entry["contract"]
source = folder / f"{contract}.sol"
remix_source = folder / f"{contract}_Remix.sol"
settings = folder / "compiler-settings.json"
source_record_path = folder / "SOURCE-RECORD.json"
artifact_paths = {key: folder / value for key, value in entry["artifacts"].items() if key != "sealed_record"}
required = [source, remix_source, settings, source_record_path, *artifact_paths.values()]
missing = [path.name for path in required if not path.is_file()]
if missing:
    raise SystemExit("Missing required files: " + ", ".join(missing))

source_record = load_json(source_record_path)
source_checks = {
    "source_sha256": sha256_file(source),
    "remix_source_sha256": sha256_file(remix_source),
    "compiler_settings_sha256": sha256_file(settings),
    "source_record_sha256": sha256_file(source_record_path),
}
for key, actual in source_checks.items():
    if entry.get(key) != actual:
        raise SystemExit(f"Frozen {key} mismatch for {contract}")
if source_record.get("contract") != contract or source_record.get("expected_artifacts") != entry["artifacts"]:
    raise SystemExit("SOURCE-RECORD.json does not match the master manifest")

artifact = load_json(artifact_paths["artifact"])
metadata = load_json(artifact_paths["metadata"])
build_info = load_json(artifact_paths["build_info"])
validate_build_profile(build_info)
diagnostic_status, diagnostics = compiler_diagnostics(build_info)

if not isinstance(artifact, dict):
    raise SystemExit("Artifact export must be a JSON object")
if not isinstance(metadata, dict):
    raise SystemExit("Metadata export must be a JSON object")

metadata_settings = metadata.get("settings")
if not isinstance(metadata_settings, dict):
    raise SystemExit("Metadata settings must be a JSON object")

compilation_target = metadata_settings.get("compilationTarget")
if not isinstance(compilation_target, dict) or len(compilation_target) != 1:
    raise SystemExit("Metadata must identify exactly one compilation target")

target_source, target_contract = next(iter(compilation_target.items()))
if target_contract != contract:
    raise SystemExit(
        f"Metadata identifies {target_contract}, expected {contract}"
    )

try:
    validate_compiler_input_source(
        build_info, metadata, remix_source, contract
    )
except ValueError as exc:
    raise SystemExit(str(exc)) from exc

build_output = build_info.get("output")
if not isinstance(build_output, dict):
    raise SystemExit("Build-info output must be a JSON object")

build_contracts = build_output.get("contracts")
if not isinstance(build_contracts, dict):
    raise SystemExit("Build-info output.contracts must be a JSON object")

target_source_output = build_contracts.get(target_source)
if not isinstance(target_source_output, dict):
    raise SystemExit(
        f"Build-info does not contain compilation source {target_source}"
    )

target_output = target_source_output.get(target_contract)
if not isinstance(target_output, dict):
    raise SystemExit(
        f"Build-info does not contain {target_contract} at {target_source}"
    )

metadata_output = metadata.get("output")
if not isinstance(metadata_output, dict):
    raise SystemExit("Metadata output must be a JSON object")

artifact_abi = artifact.get("abi")
metadata_abi = metadata_output.get("abi")
build_info_abi = target_output.get("abi")

if artifact_abi != metadata_abi or artifact_abi != build_info_abi:
    raise SystemExit(
        "Artifact ABI does not match metadata and build-info target"
    )

creation = find_hex(artifact, {"bytecode"})
runtime = find_hex(artifact, {"deployedBytecode", "runtimeBytecode"})
if not creation or not runtime:
    raise SystemExit(
        "Could not locate complete creation and deployed runtime bytecode in artifact"
    )

target_evm = target_output.get("evm")
if not isinstance(target_evm, dict):
    raise SystemExit("Build-info target is missing EVM output")

expected_creation = (
    target_evm.get("bytecode", {}).get("object")
    if isinstance(target_evm.get("bytecode"), dict)
    else None
)
expected_runtime = (
    target_evm.get("deployedBytecode", {}).get("object")
    if isinstance(target_evm.get("deployedBytecode"), dict)
    else None
)

if not isinstance(expected_creation, str) or not isinstance(expected_runtime, str):
    raise SystemExit(
        "Build-info target is missing creation or deployed runtime bytecode"
    )

if (
    creation.removeprefix("0x").lower()
    != expected_creation.removeprefix("0x").lower()
):
    raise SystemExit(
        "Artifact creation bytecode does not match build-info target"
    )

if (
    runtime.removeprefix("0x").lower()
    != expected_runtime.removeprefix("0x").lower()
):
    raise SystemExit(
        "Artifact deployed runtime bytecode does not match build-info target"
    )

record = {
    "record_format_version": 2,
    "status": "RECORDED_PREDEPLOYMENT",
    "release": manifest["release"],
    "contract": contract,
    "version": entry["version"],
    "folder": args.folder,
    "source_sha256": source_checks["source_sha256"],
    "remix_source_sha256": source_checks["remix_source_sha256"],
    "compiler_settings_sha256": source_checks["compiler_settings_sha256"],
    "source_record_sha256": source_checks["source_record_sha256"],
    "artifact_sha256": sha256_file(artifact_paths["artifact"]),
    "metadata_sha256": sha256_file(artifact_paths["metadata"]),
    "build_info_sha256": sha256_file(artifact_paths["build_info"]),
    "creation_bytecode_bytes": (len(creation) - 2) // 2,
    "runtime_template_bytes": (len(runtime) - 2) // 2,
    "creation_bytecode_keccak256": keccak_hex(creation),
    "runtime_template_keccak256": keccak_hex(runtime),
    "compiler_diagnostics": diagnostic_status,
    "diagnostics": diagnostics,
}
record_path = folder / "COMPILATION-RECORD.json"
atomic_write_json(record_path, record)
record_hash = sha256_file(record_path)

zip_path = folder / entry["artifacts"]["sealed_record"]
member_paths = [folder / name for name in required_zip_members(entry)]
deterministic_zip(zip_path, member_paths)

entry.update({
    "status": "RECORDED_PREDEPLOYMENT",
    "artifact_sha256": record["artifact_sha256"],
    "metadata_sha256": record["metadata_sha256"],
    "build_info_sha256": record["build_info_sha256"],
    "compilation_record_sha256": record_hash,
    "sealed_record_sha256": sha256_file(zip_path),
    "creation_bytecode_bytes": record["creation_bytecode_bytes"],
    "runtime_template_bytes": record["runtime_template_bytes"],
    "creation_bytecode_keccak256": record["creation_bytecode_keccak256"],
    "runtime_template_keccak256": record["runtime_template_keccak256"],
    "compiler_diagnostics": diagnostic_status,
})

pending = any(item["status"] == "PENDING_COMPILATION" for item in manifest["contracts"])
manifest["artifact_status"] = "PARTIAL" if pending else "RECORDED_PREDEPLOYMENT"
atomic_write_json(MANIFEST_PATH, manifest)
atomic_write_text(ROOT / "MASTER_COMPILATION_MANIFEST.md", render_manifest_markdown(manifest))

print(f"RECORDED: {contract}")
print(f"Compilation record SHA-256: {record_hash}")
print(f"Sealed ZIP SHA-256: {entry['sealed_record_sha256']}")
