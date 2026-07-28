# Policy V1.0.1 Artifact Intake

Compile `LaborCoinProposalTextPolicyV1_Remix.sol` in Remix with the exact settings in `compiler-settings.json`.

Save these three files directly in this folder using the exact names:

- `LaborCoinProposalTextPolicyV1.json`
- `LaborCoinProposalTextPolicyV1_metadata.json`
- `LaborCoinProposalTextPolicyV1.build-info.json`

Then run from the repository root:

```powershell
python .\record_compilation.py 01-policy
python .\verify_master_compilation.py
```

Do not manually create or edit `COMPILATION-RECORD.json`, the sealed ZIP, or either master manifest. Do not reuse artifacts from another revision or compilation.
