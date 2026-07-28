# LaborVote V9.1.1 Artifact Intake

Compile `LaborVoteV9_Remix.sol` in Remix with the exact settings in `compiler-settings.json`.

Save these three files directly in this folder using the exact names:

- `LaborVoteV9.json`
- `LaborVoteV9_metadata.json`
- `LaborVoteV9.build-info.json`

Then run from the repository root:

```powershell
python .\record_compilation.py 05-labrv
python .\verify_master_compilation.py
```

Do not manually create or edit `COMPILATION-RECORD.json`, the sealed ZIP, or either master manifest. Do not reuse artifacts from another revision or compilation.
