from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from manifest_tools import render_manifest_markdown

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SOURCE_COMMIT = "f5a1b200a6f703538b88319d5135b20f36dbae1c"
EXPECTED_SOURCE_RECORD_COMMIT = "660931b0272c30705274b71ea36d6f6b74a4a430"
EXPECTED_SOURCE_MANIFEST_SHA256 = "6afdeb3a44b227dcbe751a683fc6eb4b1e9190352e6e87a26717245ec8b3a05d"


class MasterManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(
            (ROOT / "MASTER_COMPILATION_MANIFEST.json").read_text(encoding="utf-8")
        )

    def test_revision_and_source_binding(self):
        self.assertEqual(self.manifest["manifest_format_version"], 3)
        self.assertEqual(self.manifest["release"], "LaborCoin Revision 7.3")
        source = self.manifest["source_repository"]
        self.assertEqual(source["release_path"], "release/revision-7.3-source-freeze")
        self.assertEqual(source["source_freeze_commit"], EXPECTED_SOURCE_COMMIT)
        self.assertEqual(source["source_freeze_record_commit"], EXPECTED_SOURCE_RECORD_COMMIT)
        self.assertEqual(source["source_manifest_sha256"], EXPECTED_SOURCE_MANIFEST_SHA256)

    def test_compiler_profile_matches_component_settings(self):
        profile = json.loads((ROOT / "COMPILER_PROFILE.json").read_text(encoding="utf-8"))
        self.assertEqual(self.manifest["compiler"], profile)
        for entry in self.manifest["contracts"]:
            settings = json.loads(
                (ROOT / entry["folder"] / "compiler-settings.json").read_text(encoding="utf-8")
            )
            self.assertEqual(settings, profile)

    def test_order_contracts_and_folders(self):
        self.assertEqual(
            [(entry["folder"], entry["contract"]) for entry in self.manifest["contracts"]],
            [('01-policy', 'LaborCoinProposalTextPolicyV1'), ('02-identity-registry', 'LaborCoinIdentityRegistryV1'), ('03-exchange', 'LaborCoinExchangeV7'), ('04-token', 'LaborCoinV4'), ('05-labrv', 'LaborVoteV9'), ('06-registration', 'LaborCoinRegistrationV6'), ('07-governance', 'LaborCoinGovernanceV16')],
        )

    def test_source_records_are_source_only_and_match_manifest(self):
        forbidden = {
            "status", "artifact_sha256", "metadata_sha256", "build_info_sha256",
            "creation_bytecode_keccak256", "runtime_template_keccak256",
            "compiler_diagnostics",
        }
        for entry in self.manifest["contracts"]:
            record = json.loads(
                (ROOT / entry["folder"] / "SOURCE-RECORD.json").read_text(encoding="utf-8")
            )
            self.assertEqual(record["record_type"], "SOURCE_FREEZE")
            self.assertEqual(record["release"], self.manifest["release"])
            self.assertEqual(record["order"], entry["order"])
            self.assertEqual(record["folder"], entry["folder"])
            self.assertEqual(record["contract"], entry["contract"])
            self.assertEqual(record["version"], entry["version"])
            self.assertEqual(record["source_sha256"], entry["source_sha256"])
            self.assertEqual(record["remix_source_sha256"], entry["remix_source_sha256"])
            self.assertEqual(record["compiler_settings_sha256"], entry["compiler_settings_sha256"])
            self.assertEqual(record["expected_artifacts"], entry["artifacts"])
            self.assertFalse(forbidden.intersection(record))

    def test_markdown_is_generated_from_json(self):
        actual = (ROOT / "MASTER_COMPILATION_MANIFEST.md").read_text(encoding="utf-8")
        self.assertEqual(actual, render_manifest_markdown(self.manifest))

    def test_master_verifier_exit_matches_manifest_state(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "verify_master_compilation.py")],
            cwd=ROOT, capture_output=True, text=True, check=False,
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
        self.assertEqual(result.returncode, expected_returncode, result.stdout + result.stderr)
        self.assertIn(expected_text, result.stdout)


if __name__ == "__main__":
    unittest.main()
