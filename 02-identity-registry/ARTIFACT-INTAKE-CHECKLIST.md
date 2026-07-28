# Identity Registry V1.0.1 Artifact Intake

Compile `LaborCoinIdentityRegistryV1_Remix.sol` in Remix with the exact settings in `compiler-settings.json`.

Save these three files directly in this folder using the exact names:

- `LaborCoinIdentityRegistryV1.json`
- `LaborCoinIdentityRegistryV1_metadata.json`
- `LaborCoinIdentityRegistryV1.build-info.json`

Then run from the repository root:

```powershell
python .\record_compilation.py 02-identity-registry
python .\verify_master_compilation.py
```

Do not manually create or edit `COMPILATION-RECORD.json`, the sealed ZIP, or either master manifest. Do not reuse artifacts from another revision or compilation.
