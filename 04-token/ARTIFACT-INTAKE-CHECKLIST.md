# LABR V4.0.0 Artifact Intake

Compile `LaborCoinV4_Remix.sol` in Remix with the exact settings in `compiler-settings.json`.

Save these three files directly in this folder using the exact names:

- `LaborCoinV4.json`
- `LaborCoinV4_metadata.json`
- `LaborCoinV4.build-info.json`

Then run from the repository root:

```powershell
python .\record_compilation.py 04-token
python .\verify_master_compilation.py
```

Do not manually create or edit `COMPILATION-RECORD.json`, the sealed ZIP, or either master manifest. Do not reuse artifacts from another revision or compilation.
