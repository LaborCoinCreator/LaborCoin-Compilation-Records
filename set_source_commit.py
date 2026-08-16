from __future__ import annotations

import argparse
import re
from pathlib import Path

from manifest_tools import (
    atomic_write_json,
    atomic_write_text,
    load_json,
    render_manifest_markdown,
)

ROOT = Path(__file__).resolve().parent

parser = argparse.ArgumentParser(
    description="Bind the compilation record to the committed LaborCoin source freeze."
)
parser.add_argument(
    "commit",
    help="Full 40-character Git commit hash from the LaborCoin source repository",
)
args = parser.parse_args()

commit = args.commit.lower()

if not re.fullmatch(r"[0-9a-f]{40}", commit):
    raise SystemExit(
        "Commit must be the full 40-character hexadecimal Git commit hash."
    )

manifest_path = ROOT / "MASTER_COMPILATION_MANIFEST.json"
manifest = load_json(manifest_path)

statuses = [entry.get("status") for entry in manifest["contracts"]]
allowed = {"PENDING_COMPILATION", "RECORDED_PREDEPLOYMENT"}

if any(status not in allowed for status in statuses):
    raise SystemExit("Unsupported contract status in master manifest.")

if not any(status == "PENDING_COMPILATION" for status in statuses):
    raise SystemExit(
        "Source commit rebinding is allowed only while at least one "
        "replacement compilation is pending."
    )

manifest["source_repository"]["source_freeze_commit"] = commit

atomic_write_json(manifest_path, manifest)
atomic_write_text(
    ROOT / "MASTER_COMPILATION_MANIFEST.md",
    render_manifest_markdown(manifest),
)

print(f"Source freeze commit recorded: {commit}")