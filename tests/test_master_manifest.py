from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from manifest_tools import render_manifest_markdown

ROOT = Path(__file__).resolve().parents[1]


class MasterManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "MASTER_COMPILATION_MANIFEST.json").read_text(encoding="utf-8"))

    def test_order_and_folders(self):
        self.assertEqual(
            [entry["folder"] for entry in self.manifest["contracts"]],
            [
                "01-policy",
                "02-identity-registry",
                "03-exchange",
                "04-token",
                "05-labrv",
                "06-registration",
                "07-governance",
            ],
        )

    def test_source_records_are_source_only(self):
        forbidden = {
            "status",
            "artifact_sha256",
            "metadata_sha256",
            "build_info_sha256",
            "creation_bytecode_keccak256",
            "runtime_template_keccak256",
            "compiler_diagnostics",
        }
        for entry in self.manifest["contracts"]:
            record = json.loads((ROOT / entry["folder"] / "SOURCE-RECORD.json").read_text(encoding="utf-8"))
            self.assertEqual(record["record_type"], "SOURCE_FREEZE")
            self.assertFalse(forbidden.intersection(record))

    def test_markdown_is_generated_from_json(self):
        actual = (ROOT / "MASTER_COMPILATION_MANIFEST.md").read_text(encoding="utf-8")
        self.assertEqual(actual, render_manifest_markdown(self.manifest))

    def test_master_verifier_exit_matches_manifest_state(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "verify_master_compilation.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        all_recorded = all(
            entry.get("status") == "RECORDED_PREDEPLOYMENT"
            for entry in self.manifest["contracts"]
        )
        expected_returncode = 0 if all_recorded else 2
        expected_text = (
            "MASTER COMPILATION VERIFICATION: PASS"
            if all_recorded
            else "MASTER COMPILATION VERIFICATION: PRECOMPILATION PENDING"
        )
        self.assertEqual(
            result.returncode, expected_returncode, result.stdout + result.stderr
        )
        self.assertIn(expected_text, result.stdout)


if __name__ == "__main__":
    unittest.main()
