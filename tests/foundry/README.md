# Foundry deployment and Polygon-fork suite

This is the next executable stage after the included Python assurance gates.

Required campaigns:

1. Exact artifact deployment and runtime-hash verification
2. LABR and Exchange cyclic finalization
3. Token limits, cooldown, strict-wallet behavior, and dividends
4. Exchange curve, fuzz, and reserve invariants
5. LABRV minter finalization and soulbound behavior
6. Registration EIP-712, replay protection, score bounds, and ERC-1271
7. Proposal Text Policy exhaustive corpus and mutation tests
8. Governance snapshot, quorum, approval, execution, denylist, and read-interface tests
9. Aragon permission grant and historical revocation tests on a Polygon fork
10. Full launch rehearsal with predicted and on-chain runtime-hash comparison

This stage remains pending until the current frontend, verifier, deployment
scripts, and repository files are supplied, because those are part of the
system under test.
