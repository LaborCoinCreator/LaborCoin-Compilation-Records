# Exchange V7.0.0 Artifact Intake

Compile `LaborCoinExchangeV7_Remix.sol` in Remix with the exact settings in `compiler-settings.json`.

Save these three files directly in this folder using the exact names:

- `LaborCoinExchangeV7.json`
- `LaborCoinExchangeV7_metadata.json`
- `LaborCoinExchangeV7.build-info.json`

Then run from the repository root:

```powershell
python .\record_compilation.py 03-exchange
python .\verify_master_compilation.py
```

Do not manually create or edit `COMPILATION-RECORD.json`, the sealed ZIP, or either master manifest. Do not reuse artifacts from another revision or compilation.
