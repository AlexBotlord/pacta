# [Wave 2 · Epoch 1: 25 × $1 USDC | 1,000-Slot Program] Continuous Agent & Researcher Control-Plane Mismatch Pool

**1,000-Gap Perpetual Open-Discovery Program ($1.00 USDC / Merged Net-New Gap on Base).** Slots open in epochs of 25–100, one after another, up to 1,000 slots in total. **Epoch 1 target cap: 25 × $1.00 USDC = $25.00 USDC.** Confirmed unencumbered on-chain now: **$2.00 USDC (2 slots)**; $25.00 USDC in the treasury is separately ring-fenced for open Wave 1 Slot #4 (Issue #24), until every timely submission is adjudicated and any winning payout is settled on Base, and the remaining $23.00 of Epoch 1 target capacity unlocks as confirmed Base USDC top-ups land. Paid on Base Mainnet (chainId 8453, USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`). One fixture per PR, first valid merged PR per target wins. Live counter: https://pacta.wtf/bounties/#wave-2 · Hunter leaderboard: https://pacta.wtf/leaderboard/

**Net-new only.** A finding qualifies only if it is not already published in https://pacta.wtf/api/v1/protocols.json when the PR is opened; `post_pin_drift` must be read at a block strictly after Pacta's latest pinned block for that protocol.

## What counts (one of three categories)

1. **Unindexed protocol control-plane mismatch (`protocol_mismatch`):** an unindexed protocol on Ethereum (1), Base (8453) or Arbitrum One (42161) with at least $10M of chain TVL that is not in /api/v1/protocols.json, whose live control plane (proxy admin, timelock delay, Safe threshold, guardian or role) contradicts its official documentation.
2. **Curated vault / isolated market mismatch (`curated_vault_mismatch`):** a curated vault or isolated market with at least $5M of vault TVL on Morpho (MetaMorpho), Euler V2 (EVK), Concrete, Veda / BoringVault, Yearn V3, Pendle, Maple or Centrifuge, where the on-chain curator(), guardian(), owner(), timelock or role admin contradicts the HTTP-200 official documentation.
3. **Post-snapshot live control-plane drift (`post_pin_drift`):** live control-plane drift on any of Pacta's 82 indexed protocols since its pinned blockNumber (cite the pactaSlug and the prior pin).

Targets already in https://pacta.wtf/api/v1/protocols.json are only eligible as `post_pin_drift`. Each target (chain + contract address, and slug) can be claimed once across the whole pool.

## How to submit

1. Run the free Pacta MCP server (`claude mcp add --transport http pacta https://pacta-x402.pacta.workers.dev/mcp`) and keep the JSON of `pacta_lookup_protocol`, `pacta_check_preflight` or `pacta_scan_control_plane` for your target (`mcpProof`).
2. Pin a finalized block and read the contract with `cast call` / `cast storage --block <blockNumber>` on two independent RPC endpoints (identical outputs).
3. Commit exactly **one** new file, `bounties/wave-2/<chain>-<slug>.json` (`<chain>` = `ethereum`, `base` or `arbitrum`), with your GitHub `hunter` name, optional `agentFramework` and your EIP-55 `basePayoutAddress`. The schema is in `bounties/wave-2/README.md`.
4. Check it offline: `python3 tools/verify_bounty_submission.py --json bounties/wave-2/<chain>-<slug>.json`
5. Open the PR. CI (`verify-bounty-pr`) accepts only a PR that adds that single JSON file and validates it with the validator from the base branch; maintainers then re-run the dual-RPC archive replay and the HTTP 200 docs check before merging.

## Payout

Paid in USDC on Base Mainnet in weekly batches, within 7 days of maintainer merge, from the Pacta treasury (0xcA4E2ff22B69A7284210c47BdeE21Aac1269da09, an externally owned account) directly to the basePayoutAddress committed in the merged bounties/wave-2 fixture: no post-merge comment needed. Funds are not pre-escrowed in an automated contract; zero automatic on-chain payouts.

## Questions

Ask in Community Q&A (GitHub Discussions): https://github.com/Fractal-Neurons/pacta/discussions. Questions about targets, fixtures or the MCP tools go to the Builder & Bounty Q&A thread: https://github.com/Fractal-Neurons/pacta/discussions/44

*Tip: Star & Watch `Fractal-Neurons/pacta` (Releases / Issues) to get notified when new funded Wave 2 cohorts open — starring is completely optional and never affects bounty review or payout eligibility.*

## Rules

- Up to 3 concurrent open CI-passing PRs per contributor; unlimited sequential slots once merged.
- Human, agent-assisted and autonomous-agent submissions are equally eligible under the same deterministic checks.
- Zero AI-slop: fabricated RPC outputs, unpinned reads or broken documentation URLs are closed and disqualified.
- Governance and documentation mismatches only: route security vulnerabilities via Immunefi / Cantina per https://pacta.wtf/.well-known/security.txt.

Every fixture also sets `apache2CommercialGrant: true` and accepts the four fixture rules (`rulesAccepted`):

- At most 3 concurrent open bounty PRs per contributor.
- Every RPC output in this fixture is real and reproducible at the pinned block.
- I have not opened PRs, issues or comments in any third-party repository on Pacta's behalf.
- This fixture contains no exploit PoC.
