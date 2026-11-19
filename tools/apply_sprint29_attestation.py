#!/usr/bin/env python3
"""apply_sprint29_attestation.py - stamp the Sprint 29 Base EAS attestation and publish the staged Sprint 29 records.

    python3 tools/apply_sprint29_attestation.py --uid 0x<32-byte UID> --tx 0x<32-byte tx hash>
        --wave2-payouts 82=0x<tx>,83=0x<tx>,90=0x<tx>,92=0x<tx>,93=0x<tx>,94=0x<tx> [--core ../pacta-core] [--skip-tests]

Input: tools/staged/sprint-29-records.json (the Sprint 29 records, their summary audits/sprint-29/block-<n>-summary.md and both pins;
written by pacta-core packages/bulk-harvester/promote/s29_stage.py + s26_emit.py --sprint 29). The UID must be the attestation of that
summary under schema 0x7ff4..df83 (chainId 1, the Ethereum pin, verifiedCount = aligned + protective records, driftCount =
parameter-delta records, summarySha256 = the staged SHA-256); this script does not read the chain, so check the UID on
base.easscan.org first. The summary file is never modified.

Sprint 29 is the Wave 5 gap audit under the stop rule (no new un-scored row): it adds Base-EAS records only.
- The merged and paid Wave 2 community catches folded in with hunter credit (staged "bounty_credits"):
  #82 Lagoon and #90 Base Bridge (new Base-EAS protocols), #83 f(x) Protocol v2 (a maintenance record of a published protocol), and
  the post-pin drift catches #92 Renzo Protocol (ezETH) and #93 / #94 Lido (stETH / Dual Governance) (maintenance records, re-read at
  the Sprint pin and at the published prior pin).
  --wave2-payouts gives each PR's Base payout transaction (32-byte hashes; truncated hashes are refused): they join
  bounties/leaderboard.json wave2Settlements, and tools/bounty_wave2.json / bounties/WAVE2-MASTER-ISSUE.md move to the epoch
  capacity below (WAVE2_CAPACITY). A further Codex-approved Wave 2 PR is folded the same way: add its catch to
  promote/bounty_s29.py, re-stage, add its payout here, re-run (before the EAS hash is computed).
- Published RPC-pinned protocols whose v2.1 re-score re-validates at the Sprint pins are converted (staged "converts_rpc_pinned").
- Every other published RPC-pinned record moves to the Sprint pins with each stated fact re-read (as in Sprint 28).

Everything else is Sprint 28's apply (tools/apply_sprint28_attestation.py, imported): index.json, rpc-pinned.json, graph facts, TOKENS,
summary lines, X handles / claims, the verify_site_v2.py EXPECT block, README / REMEDIATION_SERVICES coverage, MCP counts, the site
rebuild, X feed + receipt cards, graph mint, pacta-core sync and both test suites. Nothing is committed, pushed or deployed.
UIDs / tx hashes made of one repeated byte (e.g. 0x2929..29) are placeholders: preview only, with --allow-placeholder.
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apply_sprint28_attestation as A  # noqa: E402

SPRINT = 29
A.SPRINT = SPRINT
A.STAGED = os.path.join(HERE, "staged", f"sprint-{SPRINT}-records.json")
A.NEW_BRIEFS = ()               # the Lista Lending brief was published with the radar refresh before this Sprint
# open community hunter PRs (#47, #81, #84-#89, #91): these protocols gain no record while the PR is open
A.NO_TOUCH = ("optimism-bridge", "usd-ai", "aevo", "yearn-og-usdc", "spark-usdc-vault", "swissborg-morpho-usdc", "fraxlend",
              "gauntlet-usdc-prime")
# ---- TARGET-BEGIN (written by the staging run; predict_target() re-derives every number and must agree)
A.TARGET = {"sprints": 29, "records": 225, "eas_attestations": 29, "protocols": 311, "eas_protocols": 116, "rpc_protocols": 195, "briefs": 17,
            "badge_tiers": {"aligned": 70, "parameter_delta": 46, "rpc_observed": 195}, "base_records": 31,
            "rpc_by_chain": {"ethereum": 178, "base": 17}}
# ---- TARGET-END
A.ROW_NOTE = ("Wave 5 gap audit under the stop rule (Base-EAS records only, no new RPC-observed row): merged Wave 2 community gaps "
              "Lagoon (#82) and Base Bridge (#90) attested as new protocols, f(x) Protocol v2 (#83) gains a record, post-pin drift re-read "
              "for Renzo Protocol (ezETH) (#92) and the two Lido Dual Governance committee Safes (#93, #94); flaunch converted to Base EAS "
              "(v2.1 re-score); Peapods (PEAS) Base surface noted (309 → 311)")
BOUNTY_PRS = (82, 83, 90, 92, 93, 94)
# Wave 2 epoch 1 capacity after the three payouts (confirmed unencumbered + ring-fenced = the treasury's unencumbered USDC)
WAVE2_CAPACITY = {"settledEpochSlots": 18, "fundedUnencumberedSlots": 7, "fundedUnencumberedUsdc": "7.00", "ringFencedUsdc": "45.05"}
WAVE2_BEFORE = {"settledEpochSlots": 12, "fundedUnencumberedSlots": 13, "fundedUnencumberedUsdc": "13.00", "ringFencedUsdc": "66.07"}
HEX32 = re.compile(r"0x[0-9a-f]{64}")


def x_feed_and_cards(core):
    """Sprint 28's step, except that the four 1200 x 628 social cards (x-card-*, make_og --social-only) are not feed cards (verify_site_v2
    excludes them the same way)."""
    xf = os.path.join(core, "packages", "x-feed")
    A.run([sys.executable, "-B", os.path.join(xf, "build_x_feed.py"), "--site", A.ROOT, "--worker",
           os.path.join(core, "packages", "x402-edge-worker", "worker.mjs")], core, "build_x_feed (+ worker X_FEED)")
    for f in ("x-feed.json", "x-handles.json"):
        shutil.copyfile(os.path.join(xf, f), os.path.join(A.ROOT, "docs", "api", "v1", f))
    A.run([sys.executable, "-B", os.path.join(xf, "build_x_cards.py"), "--out", os.path.join(A.ROOT, "docs", "cards")], core, "build_x_cards",
          env=A.pillow_env())
    want = {i["cardFilename"] for i in json.loads(A.read(os.path.join(xf, "x-feed.json")))["items"]}
    cards = os.path.join(A.ROOT, "docs", "cards")
    for f in sorted(os.listdir(cards)):
        if f.endswith(".png") and f.startswith("radar-") and f not in want:
            os.remove(os.path.join(cards, f))
            print(f"  removed docs/cards/{f} (its radar operation is no longer active)")
    have = {f for f in os.listdir(cards) if f.endswith(".png") and not f.startswith("x-card-")}
    if want != have:
        A.fail(f"docs/cards differs from the feed's cards: missing {sorted(want - have)[:4]} extra {sorted(have - want)[:4]}", 1)


A.x_feed_and_cards = x_feed_and_cards
PAYOUTS = {}
NOTES = os.path.join(HERE, "staged", f"sprint-{SPRINT}-surface-notes.json")
_publish_pinned = A.publish_pinned


def publish_pinned(staged):
    """Sprint 28's step, then the staged surface notes (promote/peapods_s29.py): a published RPC-pinned record keeps its row and its
    re-pinned facts and gains one factual sentence + an l2_surfaces entry read at the Sprint pin of the other chain. Only a record that is
    re-pinned this Sprint may carry a note; a re-run is a no-op."""
    p = _publish_pinned(staged)
    if not os.path.exists(NOTES):
        return p
    notes = json.loads(A.read(NOTES))
    if notes.get("schema") != "pacta.surface_notes.v1" or notes.get("sprint") != SPRINT:
        A.fail(f"{os.path.relpath(NOTES, A.ROOT)}: not Sprint {SPRINT} surface notes", 1)
    repinned = {e["slug"] for e in staged["rpc_pinned"]["repinned"]}
    by = {e["slug"]: e for e in p["entries"]}
    for n in notes["notes"]:
        e = by.get(n["slug"])
        pin = staged["pins"][n["chain_pin"]["chain"]]
        if n["slug"] not in repinned or e is None:
            A.fail(f"surface note {n['slug']}: not a re-pinned RPC-pinned record", 1)
        if (n["chain_pin"]["block_number"], n["chain_pin"]["block_hash"]) != (pin["block_number"], pin["block_hash"]):
            A.fail(f"surface note {n['slug']}: not read at the Sprint {n['chain_pin']['chain']} pin", 1)
        if n["append_onchain_observed"] not in e["onchain_observed"]:
            e["onchain_observed"] += n["append_onchain_observed"]
        surf = [x for x in e.get("l2_surfaces", []) if x["chain"] != n["l2_surface"]["chain"]] + [n["l2_surface"]]
        e["l2_surfaces"] = sorted(surf, key=lambda x: x["chain_id"])
    A.write(A.PINNED, A.dump(p))
    return p


A.publish_pinned = publish_pinned


def wire_bounties(staged):
    """bounties/leaderboard.json: easAttestations += this Sprint's credits; wave2Credits gains them; wave2Settlements gains the three
    payouts (--wave2-payouts); tools/bounty_wave2.json and the master issue move to WAVE2_CAPACITY. Fails closed on any other starting
    state; a re-run is a no-op."""
    credits = staged.get("bounty_credits") or {}
    new = sorted(({"fixture": os.path.basename(c["fixture"]), "pr": c["pr"], "pactaSlug": slug, "record": c["record"]}
                  for slug, cs_ in credits.items() for c in cs_ if c.get("wave") == 2), key=lambda c: c["pr"])
    if sorted(c["pr"] for c in new) != sorted(BOUNTY_PRS):
        A.fail(f"staged bounty credits {sorted(c['pr'] for c in new)} differ from the Sprint {SPRINT} PRs {BOUNTY_PRS}", 1)
    lb = json.loads(A.read(A.LEADERBOARD))
    have_w2 = lb.get("wave2Credits") or []
    stamped = all(c in have_w2 for c in new)
    before = [c for c in have_w2 if c["pr"] not in BOUNTY_PRS]
    if not stamped and len(before) != len(have_w2):
        A.fail("bounties/leaderboard.json wave2Credits already carries part of the Sprint 29 credits", 1)
    if not stamped:
        eas = dict(lb.get("easAttestations") or {})
        for c in (c for cs_ in credits.values() for c in cs_):
            eas[c["hunter"]] = eas.get(c["hunter"], 0) + 1
        lb["easAttestations"] = {h: eas[h] for h in sorted(eas)}
        lb["wave2Credits"] = sorted(before + new, key=lambda c: c["pr"])
    fix = {pr: f for pr, f in ((c["pr"], c["fixture"]) for c in new)}
    have_s = {s["fixture"]: s for s in lb["wave2Settlements"]}
    for pr in BOUNTY_PRS:
        f, tx = fix[pr], PAYOUTS[pr]
        if f in have_s:
            if have_s[f]["payoutTxHash"] != tx:
                A.fail(f"wave2Settlements {f}: published payout {have_s[f]['payoutTxHash']} differs from --wave2-payouts {tx}", 1)
            continue
        lb["wave2Settlements"].append({"fixture": f, "payoutTxHash": tx})
    lb["wave2Settlements"].sort(key=lambda s: s["fixture"])
    A.write(A.LEADERBOARD, json.dumps(lb, indent=2, ensure_ascii=False) + "\n")
    # epoch capacity: tools/bounty_wave2.json + bounties/WAVE2-MASTER-ISSUE.md
    p = os.path.join(HERE, "bounty_wave2.json")
    cfg = json.loads(A.read(p))
    cur = {k: cfg[k] for k in WAVE2_CAPACITY}
    if cur not in (WAVE2_BEFORE, WAVE2_CAPACITY):
        A.fail(f"tools/bounty_wave2.json capacity {cur} is neither the pre-Sprint-{SPRINT} state nor the stamped one", 1)
    tot_b = f'{float(WAVE2_BEFORE["fundedUnencumberedUsdc"]) + float(WAVE2_BEFORE["ringFencedUsdc"]):.2f}'
    tot_a = f'{float(WAVE2_CAPACITY["fundedUnencumberedUsdc"]) + float(WAVE2_CAPACITY["ringFencedUsdc"]):.2f}'
    if cur == WAVE2_BEFORE:
        cfg.update(WAVE2_CAPACITY)
        cfg["ringFencedFor"] = A.sub_once(cfg["ringFencedFor"], re.escape(f"${tot_b} USDC total unencumbered"), f"${tot_a} USDC total unencumbered",
                                          "bounty_wave2 ringFencedFor")
        A.write(p, json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    if len(lb["wave2Settlements"]) != cfg["settledEpochSlots"]:
        A.fail(f"{len(lb['wave2Settlements'])} wave2Settlements vs settledEpochSlots {cfg['settledEpochSlots']}", 1)
    p = os.path.join(A.ROOT, "bounties", "WAVE2-MASTER-ISSUE.md")
    s = A.read(p)
    old = (f"Confirmed unencumbered on-chain now: **${WAVE2_BEFORE['fundedUnencumberedUsdc']} USDC ({WAVE2_BEFORE['fundedUnencumberedSlots']} slots)**; "
           f"${WAVE2_BEFORE['ringFencedUsdc']} USDC in the treasury is separately ring-fenced for subsequent Wave 2 epochs (${tot_b} USDC total")
    new_t = (f"Confirmed unencumbered on-chain now: **${WAVE2_CAPACITY['fundedUnencumberedUsdc']} USDC ({WAVE2_CAPACITY['fundedUnencumberedSlots']} slots)**; "
             f"${WAVE2_CAPACITY['ringFencedUsdc']} USDC in the treasury is separately ring-fenced for subsequent Wave 2 epochs (${tot_a} USDC total")
    if old in s:
        A.write(p, s.replace(old, new_t, 1))
    elif new_t not in s:
        A.fail("bounties/WAVE2-MASTER-ISSUE.md: capacity line not found", 1)
    bounty_expect(tot_b, tot_a)
    return lb["easAttestations"]


def bounty_expect(tot_b, tot_a):
    """verify_site_v2.py: the Wave 2 capacity check follows WAVE2_CAPACITY (exact strings, each found the expected number of times;
    idempotent)."""
    b, a = WAVE2_BEFORE, WAVE2_CAPACITY
    rem = "0.00"
    pairs = [
        (f"funded capacity = confirmed unencumbered USDC only ({b['settledEpochSlots']} Epoch 1 slots settled on Base; {b['fundedUnencumberedSlots']} slots / "
         f"${b['fundedUnencumberedUsdc']} unencumbered completing Epoch 1; ${b['ringFencedUsdc']} Epoch 2+ reserve from ${tot_b} treasury;",
         f"funded capacity = confirmed unencumbered USDC only ({a['settledEpochSlots']} Epoch 1 slots settled on Base; {a['fundedUnencumberedSlots']} slots / "
         f"${a['fundedUnencumberedUsdc']} unencumbered completing Epoch 1; ${a['ringFencedUsdc']} Epoch 2+ reserve from ${tot_a} treasury;", 1),
        (f'== ({b["settledEpochSlots"]}, {b["fundedUnencumberedSlots"]}, "{b["fundedUnencumberedUsdc"]}", "{b["ringFencedUsdc"]}")',
         f'== ({a["settledEpochSlots"]}, {a["fundedUnencumberedSlots"]}, "{a["fundedUnencumberedUsdc"]}", "{a["ringFencedUsdc"]}")', 1),
        (f'== ({b["settledEpochSlots"]}, {b["fundedUnencumberedSlots"]}, "{b["fundedUnencumberedUsdc"]}", "{rem}")',
         f'== ({a["settledEpochSlots"]}, {a["fundedUnencumberedSlots"]}, "{a["fundedUnencumberedUsdc"]}", "{rem}")', 1),
        (f'len(lb_["wave2Settlements"]) == {b["settledEpochSlots"]}', f'len(lb_["wave2Settlements"]) == {a["settledEpochSlots"]}', 2),
        (f'"${b["ringFencedUsdc"]} USDC in the treasury is separately ring-fenced for subsequent Wave 2 epochs (${tot_b} USDC total unencumbered',
         f'"${a["ringFencedUsdc"]} USDC in the treasury is separately ring-fenced for subsequent Wave 2 epochs (${tot_a} USDC total unencumbered', 1),
        (f'"Confirmed unencumbered on-chain now: **${b["fundedUnencumberedUsdc"]} USDC ({b["fundedUnencumberedSlots"]} slots)**"',
         f'"Confirmed unencumbered on-chain now: **${a["fundedUnencumberedUsdc"]} USDC ({a["fundedUnencumberedSlots"]} slots)**"', 1),
        # the stamp-tool simulation's settled total of kinshu7777 (Wave 1 unstamped): Wave 2 PRs #77 + #76, + #90 from this Sprint
        ('st_rows["kinshu7777"]["settled"] == 2 * BS.REWARD_ATOMIC   # + Wave 2 PR #54 (paid); kinshu7777: Wave 2 PRs #77 + #76 (paid) once Wave 1 is unstamped',
         'st_rows["kinshu7777"]["settled"] == 3 * BS.REWARD_ATOMIC   # + Wave 2 PR #54 (paid); kinshu7777: Wave 2 PRs #77 + #76 + #90 (paid) once Wave 1 is unstamped', 1),
    ]
    p = os.path.join(A.ROOT, "verify_site_v2.py")
    s = A.read(p)
    for old, new, n in pairs:
        if s.count(new) == n and s.count(old) == 0:
            continue
        if s.count(old) != n:
            A.fail(f"verify_site_v2.py: {old[:80]!r} found {s.count(old)} times (expected {n})", 1)
        s = s.replace(old, new)
    A.write(p, s)


A.wire_bounties = wire_bounties


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if A.TARGET is None:
        A.fail("TARGET is not set: run the staging (s29_stage.py + s26_emit.py --sprint 29) and write the TARGET block first")
    if "--wave2-payouts" not in argv:
        A.fail("--wave2-payouts 82=0x..,83=0x..,90=0x..,92=0x..,93=0x..,94=0x.. is required (the Base payout transactions of the folded PRs)")
    i = argv.index("--wave2-payouts")
    spec = argv[i + 1]
    del argv[i:i + 2]
    allow = "--allow-placeholder" in argv
    for part in spec.split(","):
        k, _, v = part.partition("=")
        v = v.lower()
        if not k.isdigit() or int(k) not in BOUNTY_PRS or not HEX32.fullmatch(v) or int(v, 16) == 0:
            A.fail(f"--wave2-payouts {part!r}: expected <pr>=0x + 64 hex for PRs {BOUNTY_PRS}")
        if A.placeholder(v) and not allow:
            A.fail(f"--wave2-payouts {part!r} is a repeated-byte placeholder; pass --allow-placeholder for a preview run")
        PAYOUTS[int(k)] = v
    if sorted(PAYOUTS) != sorted(BOUNTY_PRS):
        A.fail(f"--wave2-payouts must name each of {BOUNTY_PRS} once")
    return A.main(argv)


if __name__ == "__main__":
    sys.exit(main())
