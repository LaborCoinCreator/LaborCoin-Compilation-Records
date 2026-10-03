from __future__ import annotations

import argparse
from pathlib import Path

from manifest_tools import atomic_write_json, atomic_write_text, load_json, render_manifest_markdown

ROOT = Path(__file__).resolve().parent
EXPECTED_COMMIT = "f5a1b200a6f703538b88319d5135b20f36dbae1c"
EXPECTED_RECORD_COMMIT = "660931b0272c30705274b71ea36d6f6b74a4a430"
EXPECTED_MANIFEST_SHA256 = "6afdeb3a44b227dcbe751a683fc6eb4b1e9190352e6e87a26717245ec8b3a05d"

parser = argparse.ArgumentParser(
    description="Verify/reassert the fixed LaborCoin Revision 7.3 source-freeze binding."
)
parser.add_argument("commit", help="Exact Revision 7.3 source-freeze commit")
args = parser.parse_args()
commit = args.commit.lower()

if commit != EXPECTED_COMMIT:
    raise SystemExit(
        "Revision 7.3 is permanently bound to source commit " + EXPECTED_COMMIT
    )

manifest_path = ROOT / "MASTER_COMPILATION_MANIFEST.json"
manifest = load_json(manifest_path)
if manifest.get("release") != "LaborCoin Revision 7.3":
    raise SystemExit("Master manifest is not Revision 7.3")

source = manifest.get("source_repository", {})
source["source_freeze_commit"] = EXPECTED_COMMIT
source["source_freeze_record_commit"] = EXPECTED_RECORD_COMMIT
source["source_manifest_sha256"] = EXPECTED_MANIFEST_SHA256
manifest["source_repository"] = source

atomic_write_json(manifest_path, manifest)
atomic_write_text(ROOT / "MASTER_COMPILATION_MANIFEST.md", render_manifest_markdown(manifest))
print(f"Revision 7.3 source binding verified: {EXPECTED_COMMIT}")
