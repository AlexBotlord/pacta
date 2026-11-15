<!--
Pacta Chain-Feed Mismatch Challenge: 4 x $25 USDC = $100 USDC hard cap, 7-day sprint Nov 15 - Nov 22, 2026.
Rules and the four slot issues: https://pacta.wtf/bounties/
Fill in EVERY field below (replace each <...>), then check it offline before you open the PR:
  python3 tools/verify_bounty_submission.py --body PR_BODY.md
Governance / documentation parameter mismatches only. Never post an exploit PoC here: security vulnerabilities go to
Immunefi / Cantina per https://pacta.wtf/.well-known/security.txt.
-->

## Fixture file

- Fixture: <bounties/submissions/slot-<slot>-<protocol-slug>.json (exactly one JSON fixture per PR; keys in bounties/submissions/README.md)>
  Check it with: python3 tools/verify_bounty_submission.py --json bounties/submissions/slot-<slot>-<protocol-slug>.json

## Bounty slot

- Slot: <1 | 2 | 3 | 4>
- Issue: <https://github.com/Fractal-Neurons/pacta/issues/21 | 22 | 23 | 24>

## 1. chainId & contract address

- chainId: <1 | 8453 | 42161>
- Contract address: <checksummed 0x... address>
- Protocol: <protocol or curated vault name>
- TVL reference: <https:// link showing >= $25M (slots 1-2), >= $10M (slot 3) or >= $15M (slot 4, unindexed)>
- Pacta slug: <slot 4 drift on an indexed protocol only: the slug from https://pacta.wtf/api/v1/protocols.json, else n/a>

## 2. Pinned finalized block

- blockNumber: <finalized block number>
- blockHash: <0x + 64 hex>
- Prior Pacta pin: <slot 4 drift only: the pinned Pacta block / tx, else n/a>

## 3. Deterministic dual-RPC cast proof

```bash
<cast call <address> "<signature>" [args] --block <blockNumber> --rpc-url <RPC endpoint A>>
<cast call <address> "<signature>" [args] --block <blockNumber> --rpc-url <RPC endpoint B>>
```

- RPC A output: <raw output from endpoint A>
- RPC B output: <raw output from endpoint B (must be identical)>

## 4. Live official documentation claim (HTTP 200)

- Docs URL: <https:// URL of the official docs page, HTTP 200>
- Verbatim quote: <the exact sentence that conflicts with the on-chain state>

## 5. Pacta MCP output

```json
<JSON from pacta_lookup_protocol / pacta_check_preflight / pacta_scan_control_plane>
```

## 6. Apache-2.0 contribution & commercialization grant

- [ ] I grant Pacta by Fractal Neurons perpetual, irrevocable rights under Apache-2.0 to ingest, Base EAS-attest, publish on pacta.wtf, and commercialize this merged mismatch record.

## Rules

- [ ] This is my only open bounty PR (max 1 open PR per contributor across all slots).
- [ ] Every RPC output above is real, pinned to the block above, and reproducible on 2 independent endpoints (no AI-generated or fabricated values).
- [ ] I have not opened PRs, issues or comments in any third-party repository on Pacta's behalf.
- [ ] This PR contains no exploit PoC: it reports a governance / documentation parameter mismatch only.

<!-- Settlement: paid in USDC on Base Mainnet within 48h of maintainer merge from the Pacta treasury (0x4348DF1BEFAffcbA248B5118B1b782B1B2bdEd14, an EOA) once you comment your public Base 0x... address on the merged PR. Funds are not pre-escrowed in an automated contract; zero automatic on-chain payouts. -->
