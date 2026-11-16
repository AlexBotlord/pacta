# Wave 2 claims (100 × $1 USDC rolling pool, https://pacta.wtf/bounties/#wave-2)

Each Wave 2 PR adds exactly **one** new file in this directory, `bounties/wave-2/<chain>-<slug>.json`:

- `<chain>` is `ethereum`, `base` or `arbitrum` and must match `chainId` (1, 8453, 42161);
- `<slug>` is the lowercase kebab-case target slug and must equal the fixture's `slug`.

The validator treats a fixture as Wave 2 when it has `"wave": 2` or lives in this directory. Wave 1 fixtures
(`bounties/submissions/slot-<slot>-<protocol-slug>.json`) keep their own rules. Check yours offline before you open the PR:

```bash
python3 tools/verify_bounty_submission.py --json bounties/wave-2/<chain>-<slug>.json
```

## Fields (`FIELDS_WAVE2` in `tools/verify_bounty_submission.py`)

| key | rule |
| :--- | :--- |
| `wave` | `2` |
| `category` | `protocol_mismatch` (unindexed protocol, `tvlUsd` >= 10,000,000), `curated_vault_mismatch` (`tvlUsd` >= 5,000,000 and `vaultPlatform`) or `post_pin_drift` (an indexed protocol: `pactaSlug` + `priorPin`) |
| `slug` | lowercase kebab-case target slug (= the file name slug) |
| `protocol` | protocol or vault name |
| `chainId` | integer 1, 8453 or 42161 |
| `contractAddress` | mixed-case EIP-55 address that the cast commands read |
| `vaultPlatform` | `curated_vault_mismatch` only: `morpho`, `euler-v2`, `concrete`, `veda-boringvault`, `yearn-v3`, `pendle`, `maple` or `centrifuge` |
| `pactaSlug`, `priorPin` | `post_pin_drift` only: a slug from https://pacta.wtf/api/v1/protocols.json and the prior pinned Pacta block / tx |
| `hunter` | your GitHub user name (1–39 letters, digits or inner hyphens) |
| `agentFramework` | optional, e.g. `hermes`, `openclaw`, `claude-code`, `agno`, `human-researcher` (`^[a-z0-9][a-z0-9._-]{0,39}$`) |
| `basePayoutAddress` | your mixed-case EIP-55 Base address; not the zero address, a precompile (<= `0xffff`) or `contractAddress` |
| `mcpProof` | `{"tool": "pacta_lookup_protocol" \| "pacta_check_preflight" \| "pacta_scan_control_plane", "arguments": {...}, "result": {...}}` from the live Pacta `/mcp` server; the JSON must mention `contractAddress` or the slug / `pactaSlug` |
| `blockNumber`, `blockHash` | the finalized block (integer) and its 32-byte hash |
| `castCommands` | >= 2 `cast call` / `cast storage` commands, each with `--block <blockNumber>`, on >= 2 distinct `--rpc-url`s, reading `contractAddress` |
| `rpcOutputs` | `{"a": ..., "b": ...}`: identical, non-empty raw outputs |
| `docsUrl`, `docsQuote` | the official documentation page (https://, answering HTTP 200) and the verbatim sentence (>= 10 characters) |
| `tvlUsd`, `tvlReference` | not for `post_pin_drift`: TVL in USD (number) and an https:// source |
| `apache2CommercialGrant` | `true`: Pacta by Fractal Neurons may ingest, Base EAS-attest, publish on pacta.wtf and commercialize the merged record under Apache-2.0 |
| `rulesAccepted` | `[true, true, true, true]`: at most 3 concurrent open bounty PRs; every RPC output is real; no third-party spam; no exploit PoC |

Unknown keys, secrets (keys, tokens, mnemonics) and transaction-sending commands are refused.

**Duplicate guard:** a `protocol_mismatch` / `curated_vault_mismatch` target must not be in `docs/api/v1/protocols.json`
(by slug or by chain + address), and no two Wave 2 claims may share `(chainId, contractAddress)` or `slug`.

## CI gate (`.github/workflows/verify-bounty-pr.yml`)

The workflow runs on `pull_request` (never `pull_request_target`) with read-only permissions and no secrets. Before any Python
runs it requires the PR diff to be exactly one **added** regular file matching
`bounties/wave-2/(ethereum|base|arbitrum)-<slug>.json` (or a Wave 1 `bounties/submissions/slot-<1-4>-<slug>.json` fixture). It then
validates that JSON with `tools/verify_bounty_submission.py` taken from the PR's **base** commit, so no code from the PR is executed.

## Example

```json
{
  "wave": 2,
  "category": "protocol_mismatch",
  "slug": "example-lending",
  "protocol": "Example Lending",
  "chainId": 1,
  "contractAddress": "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
  "hunter": "example-hunter",
  "agentFramework": "claude-code",
  "basePayoutAddress": "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
  "mcpProof": {"tool": "pacta_lookup_protocol", "arguments": {"query": "example-lending"},
               "result": {"schema": "pacta.lookup.v1", "totalMatches": 0, "coverage_gap_hint": {"query": "example-lending"}}},
  "blockNumber": 23800000,
  "blockHash": "0x4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e4e",
  "castCommands": [
    "cast call 0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359 \"owner()(address)\" --block 23800000 --rpc-url https://eth.example-rpc-a.org",
    "cast call 0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359 \"owner()(address)\" --block 23800000 --rpc-url https://eth.example-rpc-b.org"
  ],
  "rpcOutputs": {"a": "0x1234567890AbcdEF1234567890aBcdef12345678", "b": "0x1234567890AbcdEF1234567890aBcdef12345678"},
  "docsUrl": "https://docs.example-lending.org/governance",
  "docsQuote": "All upgrades go through a 48-hour timelock.",
  "tvlUsd": 12500000,
  "tvlReference": "https://defillama.com/protocol/example-lending",
  "apache2CommercialGrant": true,
  "rulesAccepted": [true, true, true, true]
}
```

All values above are synthetic (EIP-55 test-vector addresses, a fake block). Payout: USDC on Base Mainnet in weekly batches,
within 7 days of maintainer merge, from the Pacta treasury externally owned account to `basePayoutAddress`. Funds are not
pre-escrowed in an automated contract.
