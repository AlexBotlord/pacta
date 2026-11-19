#!/usr/bin/env python3
"""apply_sprint31_attestation.py - stamp the Sprint 31 Base EAS attestation and publish the staged Sprint 31 records.

    python3 tools/apply_sprint31_attestation.py --uid 0x<32-byte UID> --tx 0x<32-byte tx hash>
        [--core ../pacta-core] [--skip-tests]

Input: tools/staged/sprint-31-records.json (written by pacta-core packages/bulk-harvester/promote/s31_stage.py + s26_emit.py --sprint 31).
The UID must be the attestation of the staged summary under schema 0x7ff4..df83 (chainId 1, the Ethereum pin, verifiedCount = aligned +
protective records, driftCount = parameter-delta records, summarySha256 = the staged SHA-256); this script does not read the chain.

Sprint 31 converts published RPC-pinned protocols to Base-EAS records under the stop rule (no new RPC-observed row): conversions from the
v2.1 re-score bundles and from promote/s31_curated.py (staged "converts_rpc_pinned"; their RPC-pinned records are retired). No Wave 2
PR is folded (Epoch 1 closed at 25 / 25, Epoch 2 unfunded): BOUNTY_PRS is empty and the epoch capacity is unchanged.

Everything else is the Sprint 28 / 29 apply (imported). Nothing is committed, pushed or deployed. Placeholder UIDs / tx hashes (one
repeated byte) need --allow-placeholder and are preview-only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apply_sprint29_attestation as S29  # noqa: E402  (configures and extends the Sprint 28 apply; re-pointed to Sprint 31 below)

A = S29.A
SPRINT = 31
A.SPRINT = S29.SPRINT = SPRINT
A.STAGED = os.path.join(HERE, "staged", f"sprint-{SPRINT}-records.json")
S29.NOTES = os.path.join(HERE, "staged", f"sprint-{SPRINT}-surface-notes.json")   # optional
A.NEW_BRIEFS = ()
# open community hunter PRs (#47, #81, #106-#117): these protocols gain no record while the PR is open
A.NO_TOUCH = ("optimism-bridge", "usd-ai", "tori-finance", "circle-gateway", "ethena-usde-susde", "aave-v3-gho", "cap", "chainlink-ccip",
              "ondo-finance-ousg-flux-finance", "kelp-dao-rseth", "fraxtal-bridge", "theo-network-thusd", "theo-network", "gami-labs", "gmx")
# ---- TARGET-BEGIN (written by the staging run; predict_target() re-derives every number and must agree)
A.TARGET = {"sprints": 31, "records": 258, "eas_attestations": 31, "protocols": 312, "eas_protocols": 142, "rpc_protocols": 170, "briefs": 17,
            "badge_tiers": {"aligned": 90, "parameter_delta": 52, "rpc_observed": 170}, "base_records": 34,
            "rpc_by_chain": {"ethereum": 157, "base": 13}}
# ---- TARGET-END
A.ROW_NOTE = ("Backlog conversion under the stop rule (Base-EAS records only, no new RPC-observed row): ten protocols moved from "
              "RPC-pinned to Base EAS (6 curated documentation-vs-chain records checked against verified source, 4 v2.1 re-scores, R-009 "
              "and R-010); new gaps: the Sonic Gateway fail-safe (200 days on chain, 14 documented) and CIAN Yield Layer allocation "
              "settings (Safe-direct, documented as time-locked); no Wave 2 fold")
# Wave 2: no PR folded in Sprint 31; the capacity stays where Sprint 30 left it
S29.BOUNTY_PRS = ()
S29.WAVE2_BEFORE = {"settledEpochSlots": 25, "fundedUnencumberedSlots": 0, "fundedUnencumberedUsdc": "0.00", "ringFencedUsdc": "45.05"}
S29.WAVE2_CAPACITY = dict(S29.WAVE2_BEFORE)
# no new protocol this Sprint: build_lookup TOKENS gains no "Sprint 31 promotion" block (an empty block would not parse)
_add_tokens = A.add_tokens
A.add_tokens = lambda staged: _add_tokens(staged) if staged.get("tokens") else None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if A.TARGET is None:
        A.fail("TARGET is not set: run the staging (s31_stage.py + s26_emit.py --sprint 31) and write the TARGET block first")
    if S29.BOUNTY_PRS:
        return S29.main(argv)                      # --wave2-payouts required and checked there
    if "--wave2-payouts" in argv:
        A.fail("--wave2-payouts given, but Sprint 31 folds no Wave 2 PR (BOUNTY_PRS is empty)")
    return A.main(argv)


if __name__ == "__main__":
    sys.exit(main())
