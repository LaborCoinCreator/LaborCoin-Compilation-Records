# LaborCoin Compilation Records

This repository is the authoritative compilation-provenance record for the seven LaborCoin Revision 7.2 contracts.

**Current status: precompilation source freeze. No contract is represented as compiled or deployment-ready.**

## Repository rule

Each numbered folder is the only approved destination for that contract's compiler exports and generated sealed record.

| Order | Folder | Contract | Version |
|---:|---|---|---|
| 1 | `01-policy` | `LaborCoinProposalTextPolicyV1` | V1.0.1 |
| 2 | `02-identity-registry` | `LaborCoinIdentityRegistryV1` | V1.0.1 |
| 3 | `03-exchange` | `LaborCoinExchangeV7` | V7.0.0 |
| 4 | `04-token` | `LaborCoinV4` | V4.0.0 |
| 5 | `05-labrv` | `LaborVoteV9` | V9.1.1 |
| 6 | `06-registration` | `LaborCoinRegistrationV6` | V6.1.1 |
| 7 | `07-governance` | `LaborCoinGovernanceV15` | V15.1.1 |

This public repository intentionally excludes superseded prelaunch compiler records and incomplete revision history. Those records are not authoritative for Revision 7.2.

## Exact compilation workflow

For each component in order:

1. Confirm the normal and Remix source hashes match `SOURCE-RECORD.json` and `MASTER_COMPILATION_MANIFEST.json`.
2. Compile the `_Remix.sol` source in Remix using the exact `compiler-settings.json` profile.
3. Export the artifact, metadata, and build-info files under the exact names listed in the component checklist.
4. Place those three exports directly in the matching numbered folder.
5. Run:

```powershell
python .\record_compilation.py 01-policy
python .\verify_master_compilation.py
```

Change the folder argument for each component. `record_compilation.py` validates the compiler profile and diagnostics, computes SHA-256 and Keccak-256 commitments, writes `COMPILATION-RECORD.json`, creates a deterministic sealed ZIP, and updates both master manifests.

A previously recorded component cannot be silently overwritten. `--replace` is available only for an explicit prepublication correction and must never be used after final publication or deployment reliance.

## Verification commands

```powershell
python .\VERIFY_RELEASE.py
python .\verify_master_compilation.py
```

Before artifacts exist, the master verifier must return `PRECOMPILATION PENDING` with exit code 2. After all seven records are complete, it must return `PASS` with exit code 0.

## Authority hierarchy

1. `MASTER_COMPILATION_MANIFEST.json` is authoritative for the release-wide record.
2. Each `SOURCE-RECORD.json` is immutable source-freeze evidence only.
3. Each generated `COMPILATION-RECORD.json` is authoritative for its artifact set and bytecode commitments.
4. Each deterministic sealed ZIP must match the loose files byte-for-byte.
5. `MASTER_COMPILATION_MANIFEST.md` is generated from the JSON manifest and must not be edited independently.
