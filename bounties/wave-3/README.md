# Wave 3 — 3-Year Protocol Trajectory & Integrity Dossier (`2 × $20.00 USDC` on Base)

> **Status:** **OPEN (`2` Human-Researcher Dossier Slots · `$20.00 USDC` per Accepted Protocol · `$40.00 USDC` Backed On-Chain Now)**
> **Treasury (Base Mainnet EOA):** `0xcA4E2ff22B69A7284210c47BdeE21Aac1269da09` (`$40.05 USDC` unencumbered on-chain; Wave 1 `$100.00 USDC` & Wave 2 `$1.00` micro-bounties retired)
> **Live Bounties Board & Leaderboard:** <https://pacta.wtf/bounties/> · <https://pacta.wtf/leaderboard/>

Wave 2 single-gap `$1.00` micro-bounties are permanently **Completed & Retired**. Wave 3 shifts Pacta's open-research program to **institutional-grade, human-researcher multi-year due diligence (`2023–2026`)**: reconstructing how a DeFi protocol's live on-chain control plane evolved over 3 years, measuring its exact **Mean Time To Repair (`MTTR`)** across historical governance/documentation gaps, and auditing 12-month smart-contract engineering reality.

---

## Payout, Capacity & Settlement

- **Reward:** **`$20.00 USDC` (`20,000,000` atomic Base USDC, `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) per merged dossier**
- **Open Pool:** **`2` slots (`$40.00 USDC` confirmed unencumbered on-chain now)** in `0xcA4E2ff22B69A7284210c47BdeE21Aac1269da09` (externally owned account, not pre-escrowed in a smart contract)
- **Settlement SLA:** Paid directly on Base Mainnet (`chainId = 8453`) to `base_payout_address` within **7 days** of maintainer merge and dual-RPC historical replay verification.

---

## Eligible Targets (`7` EVM Chains + `170` `rpc_observed` Protocols Unlocked)

A protocol is eligible for Wave 3 if it holds **`>= $10,000,000` TVL** (`tvl_usd >= 10000000`) on any of **7 EVM chains**:

| `chain` | `chain_id` | Network |
| --- | --- | --- |
| `ethereum` | `1` | Ethereum Mainnet |
| `base` | `8453` | Base Mainnet |
| `arbitrum` | `42161` | Arbitrum One |
| `optimism` | `10` | OP Mainnet |
| `polygon` | `137` | Polygon PoS |
| `bnb` | `56` | BNB Smart Chain |
| `avalanche` | `43114` | Avalanche C-Chain |

- **All `rpc_observed` (`easAttested: false`) protocols in [`docs/api/v1/protocols.json`](../../docs/api/v1/protocols.json) (`170` protocols) are UNLOCKED and eligible!** Set `pacta_slug` to the protocol's slug in `protocols.json` when assessing an `rpc_observed` target, or `null` when assessing an unindexed `$10M+` protocol.
- Protocols already Base-EAS attested (`easAttested: true`) or already covered by a merged `bounties/wave-3/<chain>-<slug>.json` dossier are excluded as duplicates.

---

## Mandatory 3-Part Human-Researcher Dossier Schema (`2023–2026`)

Submit **one newly added JSON file per PR** at `bounties/wave-3/<chain>-<slug>.json` containing all required keys:

### Top-Level Target & Metadata Keys
- `wave`: integer `3`
- `chain`: `"ethereum" | "base" | "arbitrum" | "optimism" | "polygon" | "bnb" | "avalanche"`
- `chain_id`: matching chain ID (`1 | 8453 | 42161 | 10 | 137 | 56 | 43114`)
- `protocol_name`: human-readable protocol name (`2–120` chars)
- `slug`: lowercase kebab-case slug matching filename `bounties/wave-3/<chain>-<slug>.json`
- `pacta_slug`: `null` for unindexed targets, or an `rpc_observed` slug from `docs/api/v1/protocols.json`
- `contract_address`: mixed-case EIP-55 primary proxy / timelock / vault / controller address
- `tvl_usd`: finite number `>= 10000000` (`$10M+`)
- `tvl_source_url`: `https://` link to DefiLlama or official analytics proving `>= $10M` TVL
- `dossier_window`: `"2023-2026"` (or inception-to-`2026` window matching `^202[0-6]-2026$`)
- `trajectory_mode` *(optional)*: `"mutable_transitions"` or `"immutable_verified"`

### Part 1 — 3-Year On-Chain Control-Plane Timeline (`historical_transitions`)
- `historical_transitions`: array of **`>= 2` chronological objects** at strictly increasing `block_number`s (`>= 2` distinct blocks across `2023–2026`), proving either control-plane evolution (proxy upgrades, Safe signer/threshold rotations, timelock/role mutations) or multi-block 3-year immutability + controller verification:
  - `block_number` (`int > 0`, strictly increasing)
  - `block_date` (`"YYYY-MM-DD"`)
  - `tx_hash` (`0x` + 64 hex transaction hash)
  - `event_kind` (`"deployment_baseline" | "proxy_upgrade" | "signer_or_threshold_change" | "timelock_or_role_mutation" | "parameter_or_pause_mutation" | "immutability_checkpoint"`)
  - `rpc_or_cast_proof` (reproducible `cast call|storage|receipt|logs|code|tx|block` or `curl` JSON-RPC command with `--rpc-url https://...`, referencing `contract_address` or `tx_hash`)
  - `summary` (`24–1000` chars clinical summary)

### Part 2 — Historical Docs & DAO Governance Forensics (`docs_and_governance_forensics`)
- `docs_and_governance_forensics`: object proving historical gap windows and exact **`MTTR` repair duration** (or unrepaired open duration):
  - `mttr_status`: `"repaired" | "partially_repaired" | "unrepaired_open" | "zero_gap_verified"`
  - `mttr_days`: finite number `>= 0` when `repaired` or `partially_repaired` (`null` when `unrepaired_open` or `zero_gap_verified`)
  - `unrepaired_open_days` *(optional)*: finite number `>= 0` when `unrepaired_open`
  - `evidence_sources`: `>= 2` dated entries `{ "kind", "date", "url", "claim_summary" }`, including **at least one** dated GitHub commit/blob/PR URL (`github.com/.../commit/...`), Internet Archive snapshot (`web.archive.org/web/...`), or Snapshot / Tally / Discourse / DAO governance proposal URL
  - `gap_windows`: `>= 1` entries `{ "opened_block", "opened_date", "closed_block", "closed_date", "duration_days", "status", "summary" }`

### Part 3 — Repository & Engineering Reality Audit + Executive Risk Memo (`repo_audit` + `executive_risk_memo`)
- `repo_audit`: object with all **6** engineering-health keys:
  - `github_org_repo`: `"<org>/<repo>"`
  - `commits_12m_contracts`: trailing 12-month smart-contract commits (`int >= 0`)
  - `commits_12m_frontend_or_other`: trailing 12-month non-contract commits (`int >= 0`)
  - `human_contributors_12m`: distinct non-bot human contributors over trailing 12 months (`int >= 0`)
  - `bus_factor`: minimum distinct human engineers accounting for core contract maintenance (`1..human_contributors_12m`, or `0` if dormant)
  - `code_before_upgrade_verified`: `true | false` — whether deployed implementation upgrades trace to public commits predating on-chain execution
- `executive_risk_memo`: **`>= 400` characters** (`400–8,000` chars, `>= 45` distinct lexical words) of clinical due-diligence analysis synthesizing control-plane trajectory, repair speed (`MTTR`), and engineering bench strength. **Shallow 1-liner or repetitive bot spam is deterministically rejected by CI.**

### Part 4 — Researcher Attribution, Payout, MCP Receipt & Grant
- `contributor_github`: researcher's GitHub handle (earns a permanent Verified Base-EAS Researcher Credential at `https://pacta.wtf/leaderboard/#<handle>`)
- `agent_assist_framework` *(optional)*: `"human-researcher"`, `"claude-code"`, `"cursor"`, etc.
- `base_payout_address`: mixed-case EIP-55 Base Mainnet wallet address for the `$20.00 USDC` payout
- `mcp_tool_receipt`: `{ "tool", "arguments", "result" }` from querying Pacta's keyless MCP server (`https://mcp.pacta.wtf/mcp`) via `pacta_lookup_protocol`, `pacta_check_preflight`, or `pacta_scan_control_plane`
- `apache2_commercial_grant`: `true`
- `rules_accepted`: `[true, true, true, true]` (at most 2 concurrent open Wave 3 PRs, reproducible evidence, zero third-party repo spam, zero exploit PoCs)

---

## Local Validation Before Opening a PR

```bash
python3 tools/verify_bounty_submission.py --wave 3 --json bounties/wave-3/<chain>-<slug>.json
```

---

## Complete Valid Wave 3 Dossier Example (`bounties/wave-3/optimism-example-lending.json`)

```json
{
  "wave": 3,
  "chain": "optimism",
  "chain_id": 10,
  "protocol_name": "Example Lending",
  "slug": "example-lending",
  "pacta_slug": null,
  "contract_address": "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
  "tvl_usd": 28500000,
  "tvl_source_url": "https://defillama.com/protocol/example-lending",
  "dossier_window": "2023-2026",
  "trajectory_mode": "mutable_transitions",
  "historical_transitions": [
    {
      "block_number": 108400000,
      "block_date": "2023-08-19",
      "tx_hash": "0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a",
      "event_kind": "deployment_baseline",
      "rpc_or_cast_proof": "cast storage 0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103 --block 108400000 --rpc-url https://mainnet.optimism.io",
      "summary": "Initial EIP-1967 admin slot points to 2-of-3 founder Safe without timelock delay despite launch docs citing a 24h timelock."
    },
    {
      "block_number": 116250000,
      "block_date": "2024-02-16",
      "tx_hash": "0x2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b",
      "event_kind": "proxy_upgrade",
      "rpc_or_cast_proof": "cast receipt 0x2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b --rpc-url https://mainnet.optimism.io",
      "summary": "Upgraded(address) executed directly by 2-of-3 Safe in 0 seconds, rotating pool logic implementation while docs still claimed timelock gating."
    },
    {
      "block_number": 124900000,
      "block_date": "2024-07-08",
      "tx_hash": "0x3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c",
      "event_kind": "timelock_or_role_mutation",
      "rpc_or_cast_proof": "cast storage 0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103 --block 124900000 --rpc-url https://mainnet.optimism.io",
      "summary": "AdminChanged transferred EIP-1967 proxy admin to 48h TimelockController (minDelay = 172800s) governed by 4-of-7 guardian Safe."
    }
  ],
  "docs_and_governance_forensics": {
    "mttr_status": "repaired",
    "mttr_days": 142.0,
    "evidence_sources": [
      {
        "kind": "github_docs_commit",
        "date": "2024-07-08",
        "url": "https://github.com/example-lending/docs/commit/9f8e7d6c5b4a32109876543210fedcba98765432",
        "claim_summary": "Docs security page updated to list the deployed 48h TimelockController and 4-of-7 Safe addresses after OIP-14 execution."
      },
      {
        "kind": "governance_proposal",
        "date": "2024-07-01",
        "url": "https://snapshot.org/#/example-lending.eth/proposal/0xabc123",
        "claim_summary": "DAO proposal OIP-14 ratifying migration of proxy admin authority from launch multisig to 48-hour TimelockController."
      }
    ],
    "gap_windows": [
      {
        "opened_block": 116250000,
        "opened_date": "2024-02-16",
        "closed_block": 124900000,
        "closed_date": "2024-07-08",
        "duration_days": 142.0,
        "status": "repaired",
        "summary": "Zero-delay 2-of-3 EOA multisig retained unilateral upgrade control for 142 days while public security docs advertised timelock protection."
      }
    ]
  },
  "repo_audit": {
    "github_org_repo": "example-lending/core-contracts",
    "commits_12m_contracts": 64,
    "commits_12m_frontend_or_other": 118,
    "human_contributors_12m": 5,
    "bus_factor": 2,
    "code_before_upgrade_verified": true
  },
  "executive_risk_memo": "Across the 2023-2026 observation window, Example Lending transitioned its primary pool proxy admin from an initial 2-of-3 founder Gnosis Safe deployed at block 108,400,000 to a 48-hour TimelockController backed by a 4-of-7 guardian Safe at block 124,900,000, following an unannounced intermediate implementation upgrade at block 116,250,000 that left public security documentation stale for 142 days (MTTR = 142.0 days, closed by GitHub docs commit 9f8e7d6c). Repository forensics over the trailing 12 months show 64 smart-contract commits across 5 human engineers (bus factor = 2) with every mainnet implementation bytecode hash traceable to a tagged audit commit prior to on-chain execution, indicating disciplined post-2025 operational maturity despite the 2024 documentation lag.",
  "contributor_github": "example-researcher",
  "agent_assist_framework": "human-researcher",
  "base_payout_address": "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
  "mcp_tool_receipt": {
    "tool": "pacta_lookup_protocol",
    "arguments": {
      "query": "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359"
    },
    "result": {
      "schema": "pacta.protocol_lookup.v1",
      "query": "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
      "totalMatches": 0,
      "results": []
    }
  },
  "apache2_commercial_grant": true,
  "rules_accepted": [
    true,
    true,
    true,
    true
  ]
}
```

---

## Questions & Researcher Coordination

- **Community Q&A Hub:** <https://github.com/Fractal-Neurons/pacta/discussions>
- **Bounty Q&A Thread:** <https://github.com/Fractal-Neurons/pacta/discussions/44>
- **Historical Wave 2 Master Issue Archive:** <https://github.com/Fractal-Neurons/pacta/issues/41>
