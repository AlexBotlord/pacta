#!/usr/bin/env python3
"""apply_sprint30_attestation.py - stamp the Sprint 30 Base EAS attestation and publish the staged Sprint 30 records.

    python3 tools/apply_sprint30_attestation.py --uid 0x<32-byte UID> --tx 0x<32-byte tx hash> [--wave2-payouts <pr>=0x<tx>,...]
        [--core ../pacta-core] [--skip-tests]

Input: tools/staged/sprint-30-records.json (written by pacta-core packages/bulk-harvester/promote/s30_stage.py + s26_emit.py --sprint 30).
The UID must be the attestation of the staged summary under schema 0x7ff4..df83 (chainId 1, the Ethereum pin, verifiedCount = aligned +
protective records, driftCount = parameter-delta records, summarySha256 = the staged SHA-256); this script does not read the chain.

Sprint 30 converts published RPC-pinned protocols to Base-EAS records under the stop rule (no new RPC-observed row): conversions from the
v2.1 re-score bundles and from promote/s30_curated.py (staged "converts_rpc_pinned"; their RPC-pinned records are retired). Merged and
paid Wave 2 community catches are folded the Sprint 29 way: list their PRs in BOUNTY_PRS with the epoch capacity after the payouts
(WAVE2_CAPACITY), add the catches to promote/bounty_s30.py, re-stage, then pass each payout with --wave2-payouts.

Everything else is the Sprint 28 / 29 apply (imported). Nothing is committed, pushed or deployed. Placeholder UIDs / tx hashes (one
repeated byte) need --allow-placeholder and are preview-only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apply_sprint29_attestation as S29  # noqa: E402  (configures and extends the Sprint 28 apply; re-pointed to Sprint 30 below)

A = S29.A
SPRINT = 30
A.SPRINT = S29.SPRINT = SPRINT
A.STAGED = os.path.join(HERE, "staged", f"sprint-{SPRINT}-records.json")
S29.NOTES = os.path.join(HERE, "staged", f"sprint-{SPRINT}-surface-notes.json")   # optional
A.NEW_BRIEFS = ()
# open community hunter PRs (#47, #81, #106-#112): these protocols gain no record while the PR is open (#106 Tori: verified, queued
# for Epoch 2)
A.NO_TOUCH = ("optimism-bridge", "usd-ai", "tori-finance", "circle-gateway", "ethena-usde-susde", "aave-v3-gho", "cap", "chainlink-ccip",
              "ondo-finance-ousg-flux-finance")
# ---- TARGET-BEGIN (written by the staging run; predict_target() re-derives every number and must agree)
A.TARGET = {"sprints": 30, "records": 248, "eas_attestations": 30, "protocols": 312, "eas_protocols": 132, "rpc_protocols": 180, "briefs": 17,
            "badge_tiers": {"aligned": 82, "parameter_delta": 50, "rpc_observed": 180}, "base_records": 32,
            "rpc_by_chain": {"ethereum": 165, "base": 15}}
# ---- TARGET-END
A.ROW_NOTE = ("Backlog conversion under the stop rule (Base-EAS records only, no new RPC-observed row): fifteen protocols "
              "moved from RPC-pinned to Base EAS (7 curated documentation-vs-chain records, 8 v2.1 re-scores, R-006 to R-008); Wave 2 Epoch 1 closed "
              "(25 / 25): Bedrock (uniBTC) (#100) attested as a new protocol, Polygon Bridge (#104) and Inverse Finance (FiRM) (#99) gain "
              "records, post-pin drift re-read for Kelp (#96), Resolv (#97), infiniFi (#101) and Threshold (#102) (311 → 312)")
# Wave 2 folding: the 7 merged and paid Sprint 30 PRs (Epoch 1 complete, 25 / 25), 1.00 USDC each: post-pin drift #96 (Kelp), #97 (Resolv),
# #99 (Inverse FiRM), #101 (infiniFi), #102 (Threshold); contract-target mismatches #100 (Bedrock uniBTC, new) and #104 (Polygon Bridge)
S29.BOUNTY_PRS = (96, 97, 99, 100, 101, 102, 104)
S29.WAVE2_BEFORE = {"settledEpochSlots": 18, "fundedUnencumberedSlots": 7, "fundedUnencumberedUsdc": "7.00", "ringFencedUsdc": "45.05"}
S29.WAVE2_CAPACITY = {"settledEpochSlots": 25, "fundedUnencumberedSlots": 0, "fundedUnencumberedUsdc": "0.00", "ringFencedUsdc": "45.05"}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if A.TARGET is None:
        A.fail("TARGET is not set: run the staging (s30_stage.py + s26_emit.py --sprint 30) and write the TARGET block first")
    if S29.BOUNTY_PRS:
        return S29.main(argv)                      # --wave2-payouts required and checked there
    if "--wave2-payouts" in argv:
        A.fail("--wave2-payouts given, but Sprint 30 folds no Wave 2 PR (BOUNTY_PRS is empty)")
    return A.main(argv)


if __name__ == "__main__":
    sys.exit(main())
