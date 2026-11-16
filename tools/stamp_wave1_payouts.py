"""Stamp the Wave 1 Base USDC payout transactions into bounties/leaderboard.json (one command), then optionally rebuild the site.

  python3 tools/stamp_wave1_payouts.py --slot1-tx 0x... --slot2-tx 0x... --slot3-tx 0x... --rebuild
  python3 tools/stamp_wave1_payouts.py --slot1-tx 0x... --dry-run          # print the change, write nothing

Deterministic and offline: it never talks to a chain. Before stamping, confirm each transaction on https://basescan.org/tx/<hash>
(a USDC transfer of 25.00 to the winner's payout address, from the Pacta treasury EOA). Rules:
- a hash must be 0x + 64 hex (stored lowercase) and not all zero;
- only a "verified" slot (with a hunter and a PR) can be stamped; Slot #4 stays in review until it has a winner;
- an already stamped slot keeps its hash unless --force is given (re-stamping the same hash is a no-op).
The site derives settled USDC from these hashes only: /bounties/ (Wave 1 Genesis Settlement Ledger) and /leaderboard/ show
"$0.00 (pending settlement)" until a slot is stamped, then "$25.00 USDC" with a BaseScan tx link.
"""

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LEADERBOARD = os.path.join(ROOT, "bounties", "leaderboard.json")
TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")


def dump(d):
    return json.dumps(d, indent=2, ensure_ascii=False) + "\n"


def stamp(d, txs, force=False):
    """txs: {slot: hash}. Returns (new dict, [change lines]); raises ValueError on any invalid input (nothing is written)."""
    d = json.loads(json.dumps(d))
    by_slot = {s["slot"]: s for s in d["wave1Settlements"]}
    changes = []
    for slot, h in sorted(txs.items()):
        if not (isinstance(h, str) and TX_RE.match(h)) or int(h, 16) == 0:
            raise ValueError(f"slot {slot}: {h!r} is not a 0x + 64-hex transaction hash")
        h = h.lower()
        s = by_slot.get(slot)
        if s is None or s["status"] != "verified" or not s.get("hunter") or not s.get("pr"):
            raise ValueError(f"slot {slot}: not a verified Wave 1 slot with a hunter and a PR; nothing to stamp")
        if s["payoutTxHash"] == h:
            continue
        if s["payoutTxHash"] and not force:
            raise ValueError(f"slot {slot}: already stamped with {s['payoutTxHash']} (pass --force to replace it)")
        changes.append(f"slot {slot} (@{s['hunter']}, PR #{s['pr']}): payoutTxHash {s['payoutTxHash']} -> {h}  https://basescan.org/tx/{h}")
        s["payoutTxHash"] = h
    return d, changes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for n in (1, 2, 3, 4):
        ap.add_argument(f"--slot{n}-tx", dest=f"slot{n}", help=f"Base USDC payout tx hash for Wave 1 Slot #{n}")
    ap.add_argument("--rebuild", action="store_true", help="run tools/build_site.py after stamping")
    ap.add_argument("--force", action="store_true", help="replace an existing, different hash")
    ap.add_argument("--dry-run", action="store_true", help="print the change and write nothing")
    ap.add_argument("--leaderboard", default=LEADERBOARD, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    txs = {n: getattr(a, f"slot{n}") for n in (1, 2, 3, 4) if getattr(a, f"slot{n}")}
    if not txs:
        ap.error("give at least one --slotN-tx")
    with open(a.leaderboard, encoding="utf-8") as fh:
        before = json.load(fh)
    try:
        after, changes = stamp(before, txs, a.force)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    for c in changes:
        print(c)
    if not changes:
        print("no change (already stamped)")
    if a.dry_run or not changes:
        return 0
    tmp = a.leaderboard + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(dump(after))
    os.replace(tmp, a.leaderboard)
    print(f"wrote {os.path.relpath(a.leaderboard, ROOT)}")
    if a.rebuild:
        return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_site.py")], cwd=ROOT).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
