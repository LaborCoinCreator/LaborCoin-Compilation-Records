# LaborCoin Compilation Records

This `revision-7.3` branch is the authoritative compilation-provenance workspace for the seven LaborCoin Revision 7.3 contracts. Revision 7.2 remains preserved on `main` and in Git history.

**Current status: precompilation source freeze. No Revision 7.3 contract is represented as officially compiled or deployment-ready.**

## Source binding

- Authoritative contract-source commit: `f5a1b200a6f703538b88319d5135b20f36dbae1c`
- Source-freeze evidence-record commit: `660931b0272c30705274b71ea36d6f6b74a4a430`
- `SOURCE_MANIFEST.json` SHA-256: `6afdeb3a44b227dcbe751a683fc6eb4b1e9190352e6e87a26717245ec8b3a05d`
- Source-freeze evidence path: `release/revision-7.3-source-freeze`

The source commit fixes the seven contract sources. The later evidence-record commit contains the validated source-freeze package and manifest that point back to that source commit.

## Repository rule

Each numbered folder is the only approved destination for that contract's official Revision 7.3 compiler exports and generated sealed record.

| Order | Folder | Contract | Version |
|---:|---|---|---|
| 1 | `01-policy` | `LaborCoinProposalTextPolicyV1` | V1.1.1 |
| 2 | `02-identity-registry` | `LaborCoinIdentityRegistryV1` | V1.0.1 |
| 3 | `03-exchange` | `LaborCoinExchangeV7` | V7.1.0 |
| 4 | `04-token` | `LaborCoinV4` | V4.1.0 |
| 5 | `05-labrv` | `LaborVoteV9` | V9.1.1 |
| 6 | `06-registration` | `LaborCoinRegistrationV6` | V6.1.1 |
| 7 | `07-governance` | `LaborCoinGovernanceV16` | V16.0.0 |

## Exact compilation workflow

For each component in order:

1. Confirm the normal and Remix source hashes match `SOURCE-RECORD.json` and `MASTER_COMPILATION_MANIFEST.json`.
2. Compile the `_Remix.sol` source in Remix using the exact `compiler-settings.json` profile.
3. Export the artifact, metadata, and build-info files under the exact names listed in the component checklist.
4. Place only those three exports directly in the matching numbered folder.
5. Run `python .\record_compilation.py <folder>`, then `python .\verify_master_compilation.py`.

`record_compilation.py` validates the frozen source binding, compiler profile, diagnostics, compiler-input source, ABI consistency, and bytecode consistency; computes SHA-256 and Keccak-256 commitments; writes `COMPILATION-RECORD.json`; creates a deterministic sealed ZIP; and updates both master manifests.

A previously recorded component cannot be silently overwritten. `--replace` remains a prepublication correction mechanism only and must never be used after final publication or deployment reliance.

## Verification commands

```powershell
python .\run_python_tests.py
python .\verify_master_compilation.py
python .\VERIFY_RELEASE.py
```

Before official artifacts exist, the master verifier must return `PRECOMPILATION PENDING` with exit code 2. After all seven official Revision 7.3 records are complete, it must return `PASS` with exit code 0.

## Authority hierarchy

1. `MASTER_COMPILATION_MANIFEST.json` is authoritative for the release-wide compilation record.
2. Each `SOURCE-RECORD.json` binds one numbered component to its frozen canonical source, Remix source, compiler settings, and expected artifact names.
3. Each generated `COMPILATION-RECORD.json` is authoritative for its official artifact set and bytecode commitments.
4. Each deterministic sealed ZIP must match the loose files byte-for-byte.
5. `MASTER_COMPILATION_MANIFEST.md` is generated from the JSON manifest and must not be edited independently.
