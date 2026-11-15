# Bounty submissions (Pacta Chain-Feed Mismatch Challenge, https://pacta.wtf/bounties/)

Each bounty PR commits exactly one JSON fixture at `bounties/submissions/slot-<slot>-<protocol-slug>.json` (for example `slot-1-example-vault.json`) and fills `.github/PULL_REQUEST_TEMPLATE/bounty_mismatch.md`.

Fixture keys (`FIELDS_JSON` in `tools/verify_bounty_submission.py`): `slot`, `issue`, `chainId`, `contractAddress`, `protocol`, `tvlReference`, `pactaSlug`, `blockNumber`, `blockHash`, `priorPin`, `castCommands` (list), `rpcOutputs` (`{"a", "b"}`), `docsUrl`, `docsQuote`, `mcpOutput` (object), `apacheGrant` (true), `rules` (4 × true).

Check both offline before you open the PR:

```bash
python3 tools/verify_bounty_submission.py --json bounties/submissions/slot-<slot>-<protocol-slug>.json
python3 tools/verify_bounty_submission.py --body PR_BODY.md
```

**Agent-assisted & autonomous-agent submissions welcome:** Human, agent-assisted, and autonomous-agent submissions are equally eligible under the exact same deterministic dual-RPC archive replay, HTTP 200 official-docs verification, and 1-open-PR-per-contributor rules (0 fabricated outputs).
