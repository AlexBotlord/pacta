#!/usr/bin/env python3
"""apply_sprint24_attestation.py - stamp the Sprint 24 Base EAS attestation and publish the staged Sprint 24 records.

    python3 tools/apply_sprint24_attestation.py --uid 0x<32-byte UID> --tx 0x<32-byte tx hash> [--core ../pacta-core] [--skip-tests]

Input: tools/staged/sprint-24-records.json (the 23 Sprint 24 records, their summary audits/sprint-24/block-<n>-summary.md, the Ethereum
pin and the Base pin: the Centrifuge V3 Root (Base) records and the Uniswap V4 Base record are read at the Base pin, every other record
at the Ethereum pin). The UID must be the attestation of that summary under schema 0x7ff4..df83 (chainId 1, the Ethereum pin,
verifiedCount = aligned + protective records, driftCount = parameter-delta records, summarySha256 = the staged SHA-256); this script does
not read the chain, so check the UID on base.easscan.org first. The summary file is never modified, so its SHA-256 is the same before
and after the stamp.

Two of the six protocols (staged "converts_rpc_pinned": synthetix-v3-core, centrifuge-liquidity-pools-base) are already published as
RPC-pinned (rpc_observed) pages. They move in place, keeping their published name, slug, primary contract and controller
(build_site.SLUG_OVERRIDES, build_lookup.CONVERTED_CONTINUITY): their records leave docs/api/v1/rpc-pinned.json and their Sprint 24
records enter index.json under the same slug, so the protocol count grows by 4 (the new protocols), not 6.

Part C (Section 3.4 dual chain + documentation re-scan, audits/sprint-24/drift-rescan-<n>.json): the three re-scanned records
(staged "reverified") keep their original pin, classification and Base EAS UID (the finding's provenance is never rewritten) and
gain a "reverified" entry {sprint 24, the Ethereum pin, the Sprint 24 UID, the summary, verdict, chain / docs status}. A "reconciled"
verdict would need the ALIGNED · Reconciled transition (reconciledFrom); this Sprint has none, and the stamp refuses one.

No Sprint 24 protocol comes from a Wave 1 bounty catch (staged "bounty_credits" is empty).

It then, in one pass:
  pacta-github-repo  index.json (records + base_eas_uid, Part C "reverified", sprint_eas_attestations["24"], eas_multi_attest_txs["24"],
                     summary_metrics), rpc-pinned.json (the converted protocols removed, summary recounted), TOKENS for the 4 new
                     protocols, the verify_site_v2.py EXPECT block and GRAPH_MANIFEST_SHA256 re-pin (after the rebuild), README coverage /
                     attestation / Sprint table, @pacta/mcp-server PUBLISHED counts + README scope + the rpc_observed footer probe;
                     rebuilds the site twice (byte-identical), records the new graph nodes / edges in tools/graph_minted.json, removes the
                     staged bundle, runs verify_site_v2.
  pacta-core         copies packages/mcp-server (src, test, README, SKILL.md), scripts/sync-lookup-catalog.py (worker LOOKUP block, both
                     protocol-slug allow-lists and analytics WAVE2_SLUGS: data lists only; mcp_client.py and protocol_graph_sync.py are
                     never touched), agent-directory-prs, PUBLISHED / BADGE_TIERS / SPRINT_PROTOCOL_SLUGS / RPC_PINNED_SLUGS in the tests;
                     the worker's rpc_observed citation-footer probe moves from synthetix-v3-core (converted here) to bedrock-unieth.
  tests              both repos' suites (unless --skip-tests). Nothing is committed, pushed or deployed.

Re-running with the same --uid / --tx is a no-op; a different UID or tx for an already stamped Sprint 24 is refused.
UIDs / tx hashes made of one repeated byte (e.g. 0x2121..21) are placeholders: they need --allow-placeholder (preview only),
and only a placeholder pair may use the same value for --uid and --tx.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPRINT = 24
STAGED = os.path.join(HERE, "staged", f"sprint-{SPRINT}-records.json")
INDEX = os.path.join(ROOT, "docs", "api", "v1", "index.json")
PINNED = os.path.join(ROOT, "docs", "api", "v1", "rpc-pinned.json")
HEX32 = re.compile(r"0x[0-9a-f]{64}")
# The published numbers after the stamp: 86 protocol pages = 80 EAS + 6 RPC, 86 badges (4 new protocols plus 2 RPC-pinned
# protocols converted in place). predict_target() re-derives every number from the data and must agree before anything is written.
TARGET = {"sprints": 24, "records": 159, "eas_attestations": 24, "protocols": 86, "eas_protocols": 80, "rpc_protocols": 6, "briefs": 8,
          "badge_tiers": {"aligned": 46, "parameter_delta": 34, "rpc_observed": 6}, "base_records": 22,
          "rpc_by_chain": {"ethereum": 2, "base": 4}}
NEW_TOKENS = {"steakhouse-financial-ethereum": ["steakUSDT", "steakPYUSD", "steakUSDC", "Steakhouse"],
              "uniswap-v4": ["UNI", "Uniswap v4", "PoolManager"], "chainlink-ccip": ["CCIP", "LINK", "Chainlink"],
              "obol-network": ["OBOL", "stOBOL", "Obol"]}
RPC_BY_CHAIN = {"ethereum": ["https://gateway.tenderly.co/public/mainnet", "https://rpc.mevblocker.io"],
                "base": ["https://mainnet.base.org", "https://base-rpc.publicnode.com"]}
# Part C: Section 3.4 dual chain + documentation re-scan of three earlier records (before = original Sprint 8 / 9 / 10 pin, after = the
# Sprint 24 Ethereum pin; plus the documented statement on a fresh HTTP-200 snapshot)
DRIFT_RESCANS = {"protocols": ["eigenlayer-core", "ondo-finance-ousg-flux-finance", "renzo-protocol-ezeth"], "checks": 18, "drifted": 0}
REVERIFIED = {"renzo-ezeth-deposit-queue-fee": "persists", "eigenlayer-core-proxy-admin-and-timelock": "still_aligned",
              "ondo-ousg-rate-limiter-and-flux-timelock": "persists"}
ROW_NOTE = ("Steakhouse Financial (Ethereum), Uniswap V4, Chainlink CCIP and Obol Network; Synthetix V3 Core and Centrifuge V3 Root (Base) "
            "moved from RPC-pinned to EAS-attested; Section 3.4 re-scan: Renzo, EigenLayer and Ondo unchanged")
# the worker's / MCP's rpc_observed citation-footer probe: synthetix-v3-core is converted by this Sprint, bedrock-unieth stays RPC-pinned
FOOTER_PROBE = ("synthetix-v3-core", "bedrock-unieth")
# no Sprint 24 protocol comes from a merged Wave 1 catch
BOUNTY_CREDITS = {}
SUBMISSIONS = os.path.join(ROOT, "bounties", "submissions")
LEADERBOARD = os.path.join(ROOT, "bounties", "leaderboard.json")


def fail(msg, code=2):
    print(f"apply_sprint24_attestation: {msg}", file=sys.stderr)
    sys.exit(code)


def read(p, mode="r"):
    with open(p, mode, **({} if "b" in mode else {"encoding": "utf-8"})) as fh:
        return fh.read()


def write(p, text):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def sub_once(text, pattern, repl, name, count=1, flags=0):
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n != count:
        fail(f"{name}: expected {count} match(es) of {pattern!r}, found {n}")
    return new


def placeholder(h):
    body = h[2:]
    return len(set(body[i:i + 2] for i in range(0, 64, 2))) == 1


def protocol_slug(name):
    sys.path.insert(0, HERE)
    import build_site                                            # the site's slug rule, including SLUG_OVERRIDES
    return build_site.protocol_slug(name)


def iso(ts):
    import datetime as dt
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd, cwd, name):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=900)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print(f"  [{'ok' if r.returncode == 0 else 'FAIL'}] {name}: {' | '.join(tail)[:300]}")
    if r.returncode != 0:
        fail(f"{name} failed (exit {r.returncode})", 1)
    return r.stdout


# ---------------------------------------------------------------- checks before writing
def predict_target(staged, idx, pinned):
    """The post-stamp totals derived from the data alone; must equal TARGET."""
    es = idx["entries"] + staged["records"]
    conv = staged["converts_rpc_pinned"]
    pin_left = [e for e in pinned["entries"] if e["slug"] not in conv]
    names = {e["protocol"] for e in es}
    tiers = {"aligned": 0, "parameter_delta": 0, "rpc_observed": len({e["slug"] for e in pin_left})}
    for n in names:
        cl = {e["classification"] for e in es if e["protocol"] == n}
        tiers["aligned" if cl == {"aligned_baseline"} else "parameter_delta"] += 1
    eas = len(names)
    return {"sprints": max(e["sprint"] for e in es), "records": len(es),
            "eas_attestations": len(idx["onchain_anchoring"]["sprint_eas_attestations"]) + 1,
            "protocols": eas + tiers["rpc_observed"], "eas_protocols": eas, "rpc_protocols": tiers["rpc_observed"],
            "briefs": TARGET["briefs"], "badge_tiers": tiers, "base_records": sum(e.get("chain") == "base" for e in es),
            "rpc_by_chain": {c: sum(e["chain"] == c for e in pin_left) for c in ("ethereum", "base")}}


def check_staged(staged, idx, pinned):
    sha = "0x" + hashlib.sha256(read(os.path.join(ROOT, staged["summary_doc"]), "rb")).hexdigest()
    rs = staged["records"]
    cls = [r["classification"] for r in rs]
    if staged["sprint"] != SPRINT or staged["summary_sha256"] != sha or any(r["summary_sha256"] != sha or r["sprint"] != SPRINT for r in rs):
        fail(f"staged bundle does not match {staged['summary_doc']} (sha256 {sha})")
    e = staged["eas"]
    if (e["chainId"], e["blockNumber"], e["blockHash"]) != (1, staged["pins"]["ethereum"]["block_number"], staged["pins"]["ethereum"]["block_hash"]):
        fail("staged EAS block differs from the Ethereum pin")
    # Same convention as Sprints 1-17 (and PactaSentinelGuard: driftCount != 0 means drift): verifiedCount = aligned + protective
    # records, driftCount = parameter-delta records. The Part C post-snapshot re-scan is reported separately in drift_rescans.
    if (e["verifiedCount"], e["driftCount"]) != (cls.count("aligned_baseline") + cls.count("protective_delta"), cls.count("parameter_delta")):
        fail("staged EAS counts do not match the record classifications")
    dr = staged.get("drift_rescans")
    if dr != {"block": e["blockNumber"], "protocols": DRIFT_RESCANS["protocols"], "checks": DRIFT_RESCANS["checks"], "drifted": DRIFT_RESCANS["drifted"]}:
        fail(f"staged drift_rescans {dr} differ from the Sprint {SPRINT} re-scan {DRIFT_RESCANS}")
    rv = staged.get("reverified") or {}
    have = {x["id"]: x for x in idx["entries"]}
    if {k: v.get("verdict") for k, v in rv.items()} != REVERIFIED:
        fail(f"staged reverified {rv} differs from the Sprint {SPRINT} Section 3.4 re-scan {REVERIFIED}")
    for rid, v in rv.items():
        if rid not in have or (v["block_number"], v["block_hash"]) != (e["blockNumber"], e["blockHash"]) or v["summary_doc"] != staged["summary_doc"]:
            fail(f"reverified {rid}: not an index.json record on the Sprint {SPRINT} Ethereum pin")
        if v["verdict"] in ("reconciled", "drifted"):
            fail(f"reverified {rid}: verdict {v['verdict']} needs a record transition, not a re-verification")
    for r in rs:
        if r["base_eas_uid"] is not None:
            fail(f"staged record {r['id']} already carries a UID")
        pin = staged["pins"][r["chain"]]
        if (r["block_number"], r["block_hash"]) != (pin["block_number"], pin["block_hash"]):
            fail(f"staged record {r['id']} is not on its chain's pin")
    ids = [x["id"] for x in idx["entries"]] + [r["id"] for r in rs]
    if len(set(ids)) != len(ids):
        fail("record id collision with index.json")
    idx_names = {x["protocol"] for x in idx["entries"]}
    pin_slugs = {x["slug"] for x in pinned["entries"]}
    conv = staged["converts_rpc_pinned"]
    for name in {r["protocol"] for r in rs}:
        slug = protocol_slug(name)
        if name in idx_names or slug in {protocol_slug(n) for n in idx_names}:
            fail(f"{name}: already an index.json protocol")
        if (slug in pin_slugs) != (slug in conv):
            fail(f"{name}: slug {slug} is " + ("RPC-pinned but not listed in converts_rpc_pinned" if slug in pin_slugs
                                                else "listed in converts_rpc_pinned but not RPC-pinned"))
    for slug, name in conv.items():
        if protocol_slug(name) != slug or slug not in pin_slugs or not any(r["protocol"] == name for r in rs):
            fail(f"converts_rpc_pinned {slug}: name / slug / record mismatch")
    for slug in NEW_TOKENS:
        if slug in pin_slugs or not any(protocol_slug(r["protocol"]) == slug for r in rs):
            fail(f"NEW_TOKENS {slug}: not a new Sprint {SPRINT} protocol")
    got = predict_target(staged, idx, pinned)
    if got != TARGET:
        fail(f"derived totals {got} differ from TARGET {TARGET}")
    check_credits(staged)
    return sha


def check_credits(staged):
    """Every staged bounty credit is a verified, paid, Apache-2.0-granted Wave 1 catch of a new Sprint protocol whose fixture has no
    pactaSlug yet (or already this one, on a re-run)."""
    lb = json.loads(read(LEADERBOARD))
    w1 = {s["slot"]: s for s in lb["wave1Settlements"]}
    new_slugs = {protocol_slug(r["protocol"]) for r in staged["records"]} - set(staged["converts_rpc_pinned"])
    if staged.get("bounty_credits") != BOUNTY_CREDITS:
        fail(f"staged bounty_credits {staged.get('bounty_credits')} differ from BOUNTY_CREDITS")
    for slug, c in staged["bounty_credits"].items():
        p = os.path.join(SUBMISSIONS, f"slot-{c['slot']}-{slug}.json")
        if slug not in new_slugs or not os.path.exists(p):
            fail(f"bounty credit {slug}: not a new Sprint {SPRINT} protocol with a merged fixture {os.path.relpath(p, ROOT)}")
        f = json.loads(read(p))
        s = w1.get(c["slot"])
        if (f.get("slot") != c["slot"] or f.get("apacheGrant") is not True or f.get("pactaSlug") not in (None, slug) or not s
                or (s["status"], s["hunter"], s["pr"]) != ("verified", c["hunter"], c["pr"]) or not s["payoutTxHash"]):
            fail(f"bounty credit {slug}: fixture / ledger mismatch for Slot #{c['slot']}")


# ---------------------------------------------------------------- pacta-github-repo
def stamp_index(staged, uid, tx):
    idx = json.loads(read(INDEX))
    anc, cov = idx["onchain_anchoring"], idx["onchain_anchoring"]["attestation_coverage"]
    idx["entries"].extend({**r, "base_eas_uid": uid} for r in staged["records"])
    for e_ in idx["entries"]:                                      # Part C: append the Section 3.4 re-verification (provenance kept)
        rv = (staged.get("reverified") or {}).get(e_["id"])
        if rv:
            e_["reverified"] = [x for x in e_.get("reverified", []) if x.get("sprint") != SPRINT] + [{**rv, "base_eas_uid": uid}]
    anc["sprint_eas_attestations"][str(SPRINT)] = uid
    anc[f"eas_multi_attest_sprint_{SPRINT}_tx"] = tx
    cov["base_eas_attested_sprints"] = f"1-{SPRINT}"
    cov["eas_multi_attest_txs"][str(SPRINT)] = tx
    cov["attested_not_yet_indexed_sprints"] = []
    idx["methodology"]["archive_rpc_endpoints_by_chain"] = RPC_BY_CHAIN
    es = idx["entries"]
    cls = [e["classification"] for e in es]
    idx["summary_metrics"] = {"sprints_completed": max(e["sprint"] for e in es), "records_indexed": len(es),
                              "parameter_deltas": cls.count("parameter_delta"), "protective_deltas": cls.count("protective_delta"),
                              "aligned_baselines": cls.count("aligned_baseline")}
    idx["generated_at"] = max(idx["generated_at"], iso(staged["pins"]["ethereum"]["timestamp"]))
    write(INDEX, json.dumps(idx, indent=2, ensure_ascii=False) + "\n")
    return idx


def convert_pinned(staged):
    """Remove the converted protocols from rpc-pinned.json (records + protocol list) and recount its summary."""
    p = json.loads(read(PINNED))
    conv = staged["converts_rpc_pinned"]
    before = len(p["entries"])
    p["entries"] = [e for e in p["entries"] if e["slug"] not in conv]
    p["protocols"] = [x for x in p["protocols"] if x["slug"] not in conv]
    if before - len(p["entries"]) != len(conv) or {x["slug"] for x in p["protocols"]} != {e["slug"] for e in p["entries"]}:
        fail("rpc-pinned.json: converted protocols are not exactly one record each", 1)
    by = {c: sum(e["chain"] == c for e in p["entries"]) for c in ("ethereum", "base")}
    n = len(p["entries"])
    p["summary"] = {"protocols": len(p["protocols"]), "records": n, **by}
    p["description"] = sub_once(p["description"], r"observations of \d+ protocols \(\d+ Ethereum, \d+ Base\)",
                                f"observations of {len(p['protocols'])} protocols ({by['ethereum']} Ethereum, {by['base']} Base)", "rpc-pinned description")
    moved = " and ".join(conv.values())
    note = (f" {moved} were re-scanned in Sprint {SPRINT}, compared against their documentation and moved to the Base-EAS-attested "
            f"index (same /protocols/ slugs); they are no longer RPC-pinned records here.")
    if note.strip() not in p["description"]:
        p["description"] += note
    write(PINNED, json.dumps(p, indent=2, ensure_ascii=False) + "\n")
    return p


def wire_bounties(staged):
    """pactaSlug into each credited Wave 1 fixture (only that key; the fixture's other bytes stay as merged) and easAttestations =
    the researcher's verified Wave 1 catches whose fixture now names a Base-EAS-attested protocol (derived, so a re-run is a no-op)."""
    for slug, c in staged["bounty_credits"].items():
        p = os.path.join(SUBMISSIONS, f"slot-{c['slot']}-{slug}.json")
        t = read(p)
        if json.loads(t).get("pactaSlug") != slug:
            t = sub_once(t, r'"pactaSlug": null', f'"pactaSlug": "{slug}"', f"{os.path.basename(p)} pactaSlug")
            if json.loads(t).get("pactaSlug") != slug:
                fail(f"{p}: pactaSlug not set", 1)
            write(p, t)
    idx = json.loads(read(INDEX))
    eas = {protocol_slug(e["protocol"]) for e in idx["entries"]}
    lb = json.loads(read(LEADERBOARD))
    counts = {}
    for s in lb["wave1Settlements"]:
        if s["status"] != "verified":
            continue
        for f_name in os.listdir(SUBMISSIONS):
            if f_name.startswith(f"slot-{s['slot']}-") and f_name.endswith(".json"):
                if json.loads(read(os.path.join(SUBMISSIONS, f_name))).get("pactaSlug") in eas:
                    counts[s["hunter"]] = counts.get(s["hunter"], 0) + 1
    want = {h: counts[h] for h in sorted(counts)}
    if lb["easAttestations"] != want:
        lb["easAttestations"] = want
        write(LEADERBOARD, json.dumps(lb, indent=2, ensure_ascii=False) + "\n")
    return want


def pin_graph_manifest():
    """Re-pin verify_site_v2.GRAPH_MANIFEST_SHA256 to the rebuilt (and minted) graph manifest."""
    sha = hashlib.sha256(read(os.path.join(ROOT, "docs", "api", "v1", "graph-manifest.json"), "rb")).hexdigest()
    p = os.path.join(ROOT, "verify_site_v2.py")
    write(p, sub_once(read(p), r'^GRAPH_MANIFEST_SHA256 = "[0-9a-f]{64}"', f'GRAPH_MANIFEST_SHA256 = "{sha}"', "verify_site_v2 GRAPH_MANIFEST_SHA256",
                      flags=re.M))
    return sha


def add_tokens():
    p = os.path.join(HERE, "build_lookup.py")
    s = read(p)
    line = "    " + ", ".join(f'"{k}": {json.dumps(v)}' for k, v in NEW_TOKENS.items()) + ",\n    # briefs\n"
    write(p, sub_once(s, r"    # briefs\n", lambda m: line, "build_lookup TOKENS"))


def render_expect(x):
    return (
        "EXPECT = {\n"
        f'    "sprints": {x["sprints"]}, "records": {x["records"]}, "eas_attestations": {x["eas_attestations"]},              # index.json sprints_completed / records_indexed; Base EAS sprint UIDs\n'
        f'    "protocols": {x["protocols"]}, "eas_protocols": {x["eas_protocols"]}, "rpc_protocols": {x["rpc_protocols"]},          # /protocols/ pages = EAS-attested + RPC-pinned; badges = protocols\n'
        f'    "briefs": {x["briefs"]}, "badge_tiers": {json.dumps(x["badge_tiers"])},\n'
        f'    "base_records": {x["base_records"]},                                                  # index.json records with chain "base"\n'
        f'    "rpc_by_chain": {json.dumps(x["rpc_by_chain"])},                         # rpc-pinned.json records per chain (sum = rpc_protocols)\n'
        f'    "multi_attest_txs": {json.dumps(x["multi_attest_txs"], ensure_ascii=False)},                              # attestation_coverage.eas_multi_attest_txs keys\n'
        '    "summaries": {' + ",\n                  ".join(f'"{k}": "{v}"' for k, v in x["summaries"].items())
        + "},   # audits/sprint-<n>/ summary SHA-256 (attested)\n"
        "}\n")


def set_expect(staged):
    p = os.path.join(ROOT, "verify_site_v2.py")
    s = read(p)
    a, b = s.index("# ---- EXPECT-BEGIN"), s.index("# ---- EXPECT-END")
    head = re.sub(r"tools/apply_sprint\d+_attestation\.py", f"tools/apply_sprint{SPRINT}_attestation.py", s[a:s.index("\n", a) + 1])
    ns = {}
    exec(s[s.index("EXPECT = {", a):b], ns)                     # the current block (a literal dict)
    x = {**ns["EXPECT"], **TARGET}
    x["multi_attest_txs"] = ns["EXPECT"]["multi_attest_txs"] + [str(SPRINT)]
    x["summaries"] = {**ns["EXPECT"]["summaries"], str(SPRINT): staged["summary_sha256"][2:]}
    s = s[:a] + head + render_expect(x) + s[b:]
    # the lookup search probe "uniswap" now also prefix-matches the new uniswap-v4 slug (the other probes rank as before)
    s = sub_once(s, re.escape('"uniswap": [["uniswap-governance-timelock", "prefix"]],'),
                 '"uniswap": [["uniswap-governance-timelock", "prefix"], ["uniswap-v4", "prefix"]],', "verify uniswap probe")
    # "kusd" substring-matches the new steakUSDC / steakUSDT tokens, as it already did the Base Steakhouse vault's steakUSDC
    s = sub_once(s, re.escape('"kusd": [["kerne-kusd-base", "exact"], ["steakhouse-usdc-metamorpho-base", "substring"]],'),
                 '"kusd": [["kerne-kusd-base", "exact"], ["steakhouse-financial-ethereum", "substring"]],', "verify kusd probe")
    # the RPC-observed clearance-CTA probe page moves with the footer probe (synthetix-v3-core is converted here)
    old, new = FOOTER_PROBE
    if old != new:
        s = sub_once(s, re.escape(f'pages.get(os.path.join("protocols", "{old}", "index.html"), ""), clearance_slug="{old}"'),
                     f'pages.get(os.path.join("protocols", "{new}", "index.html"), ""), clearance_slug="{new}"', "verify clearance-CTA probe")
    write(p, s)


def readme(staged, uid, tx):
    p = os.path.join(ROOT, "README.md")
    s = read(p)
    m = json.loads(read(INDEX))["summary_metrics"]
    t = TARGET
    cov = f'{t["protocols"]} Protocols ({t["records"]} Base EAS-Attested Records across {t["sprints"]} Sprints + {t["rpc_protocols"]} RPC-Observed Records)'
    s = sub_once(s, r"\d+ Protocols \(\d+ Base EAS-Attested Records across \d+ Sprints \+ \d+ RPC-Observed Records\)", cov, "README coverage line", count=2)
    s = sub_once(s, r"\*\*\d+ Indexed Protocols \(\d+ Base-EAS-Attested Protocols across \d+ Sprint Records in \d+ Sprints \+ \d+ RPC-Observed Protocols\)\*\*",
                 f'**{t["protocols"]} Indexed Protocols ({t["eas_protocols"]} Base-EAS-Attested Protocols across {t["records"]} Sprint Records in '
                 f'{t["sprints"]} Sprints + {t["rpc_protocols"]} RPC-Observed Protocols)**', "README indexed-protocols line")
    s = sub_once(s, r"The \d+ Sprint records: \d+ parameter deltas · \d+ protective deltas · \d+ aligned baselines\.",
                 f'The {m["records_indexed"]} Sprint records: {m["parameter_deltas"]} parameter deltas · {m["protective_deltas"]} protective deltas · '
                 f'{m["aligned_baselines"]} aligned baselines.', "README breakdown")
    s = sub_once(s, rf"Sprints 1–{SPRINT - 1} carry \*\*{SPRINT - 1} on-chain Base EAS sprint attestations\*\*: (.*?) and "
                    rf"(Sprint {SPRINT - 1} in tx `0x[0-9a-f]{{64}}`)\.",
                 lambda mm: (f"Sprints 1–{SPRINT} carry **{SPRINT} on-chain Base EAS sprint attestations**: {mm.group(1)}, {mm.group(2)} "
                             f"and Sprint {SPRINT} in tx `{tx}`."), "README attestations")
    e, b = staged["pins"]["ethereum"], staged["pins"]["base"]
    prev = re.search(rf"^\| \*\*Sprint {SPRINT - 1}\*\* \|.*\|\n", s, re.M)
    if not prev:
        fail(f"README: Sprint {SPRINT - 1} row not found")
    row = (f'| **Sprint {SPRINT}** | `{e["block_number"]}` (`{hex(e["block_number"])}`) · Base `{b["block_number"]}` | `{e["block_hash"]}` | '
           f'[`{uid[:6]}...{uid[-4:]}`](https://base.easscan.org/attestation/view/{uid}) | [`{staged["summary_doc"]}`]({staged["summary_doc"]}) — '
           f'{ROW_NOTE} |\n')
    write(p, s[:prev.end()] + row + s[prev.end():])


def mcp_counts(pkg):
    t = TARGET
    p = os.path.join(pkg, "test", "lookup.test.mjs")
    old, new = FOOTER_PROBE
    if old != new:
        write(p, sub_once(read(p), re.escape(f'  const slug = "{old}";\n  const item = LOOKUP_CATALOG.find'),
                          f'  const slug = "{new}";\n  const item = LOOKUP_CATALOG.find', "mcp-server footer probe"))
    write(p, sub_once(read(p), r"const PUBLISHED = Object\.freeze\(\{[^}]*\}\);",
                      f'const PUBLISHED = Object.freeze({{ protocols: {t["protocols"]}, briefs: {t["briefs"]}, easAttestedProtocols: {t["eas_protocols"]}, '
                      f'rpcObservedProtocols: {t["rpc_protocols"]} }});', "mcp-server PUBLISHED"))
    p = os.path.join(pkg, "README.md")
    s = sub_once(read(p), r"  - Scope: \d+ Base-EAS-attested protocols", f'  - Scope: {t["eas_protocols"]} Base-EAS-attested protocols', "mcp README scope")
    write(p, sub_once(s, r"documentation compared\), \d+ RPC-observed protocols", f'documentation compared), {t["rpc_protocols"]} RPC-observed protocols',
                      "mcp README rpc scope"))


def build_twice():
    def snap():
        out = {}
        for base, _, files in os.walk(os.path.join(ROOT, "docs")):
            for f in files:
                p = os.path.join(base, f)
                out[os.path.relpath(p, ROOT)] = hashlib.sha256(read(p, "rb")).hexdigest()
        return out
    shots = []
    for i in (1, 2):
        run([sys.executable, "tools/build_b2a_feeds.py"], ROOT, f"build_b2a_feeds (pass {i})")
        run([sys.executable, "tools/build_site.py"], ROOT, f"build_site (pass {i})")
        shutil.copyfile(os.path.join(ROOT, "docs", "SKILL.md"), os.path.join(ROOT, "packages", "mcp-server", "SKILL.md"))
        shots.append(snap())
    if shots[0] != shots[1]:
        fail(f"site build is not deterministic: {sorted(k for k in shots[0] if shots[0].get(k) != shots[1].get(k))[:5]}", 1)


# ---------------------------------------------------------------- pacta-core
def render_list(slugs, indent="  ", width=145):
    lines, cur = [], ""
    for q in (f'"{x}"' for x in slugs):
        cand = f"{cur}, {q}" if cur else q
        if cur and len(indent + cand + ",") > width:
            lines.append(indent + cur + ",")
            cur = q
        else:
            cur = cand
    return "\n".join(lines + [indent + cur])


def sync_core(core):
    t = TARGET
    src_pkg, dst_pkg = os.path.join(ROOT, "packages", "mcp-server"), os.path.join(core, "packages", "mcp-server")
    for sub in ("src", "test"):                                   # byte-identical trees (test/ has fixtures/)
        shutil.copytree(os.path.join(src_pkg, sub), os.path.join(dst_pkg, sub), dirs_exist_ok=True)
    for f in ("README.md", "SKILL.md"):
        shutil.copyfile(os.path.join(src_pkg, f), os.path.join(dst_pkg, f))
    run([sys.executable, "-B", "scripts/sync-lookup-catalog.py"], core, "pacta-core sync-lookup-catalog")
    run([sys.executable, "packages/agent-directory-prs/build_directory_prs.py", "--site-docs", os.path.join(ROOT, "docs")], core, "agent-directory-prs")
    lk = json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "lookup.json")))
    prot = [x for x in lk["items"] if x["kind"] == "protocol"]
    eas_slugs = sorted(x["slug"] for x in prot if x["easAttested"])
    rpc_slugs = sorted(x["slug"] for x in prot if not x["easAttested"])
    if (len(eas_slugs), len(rpc_slugs)) != (t["eas_protocols"], t["rpc_protocols"]):
        fail(f"lookup.json protocol split {len(eas_slugs)} + {len(rpc_slugs)} differs from TARGET", 1)
    p = os.path.join(core, "packages", "x402-edge-worker", "test", "worker.test.mjs")
    s = read(p)
    s = sub_once(s, r"const PUBLISHED = Object\.freeze\(\{[^}]*\}\);",
                 f'const PUBLISHED = Object.freeze({{ protocols: {t["protocols"]}, briefs: {t["briefs"]}, easAttestedProtocols: {t["eas_protocols"]}, '
                 f'rpcObservedProtocols: {t["rpc_protocols"]} }});', "worker PUBLISHED")
    s = sub_once(s, r"const BADGE_TIERS = Object\.freeze\(\{[^}]*\}\);",
                 "const BADGE_TIERS = Object.freeze({ " + ", ".join(f"{k}: {v}" for k, v in t["badge_tiers"].items()) + " });", "worker BADGE_TIERS")
    s = sub_once(s, r"const SPRINT_PROTOCOL_SLUGS = \[\n?(.*?)\];", lambda m: "const SPRINT_PROTOCOL_SLUGS = [\n" + render_list(eas_slugs) + "];",
                 "worker SPRINT_PROTOCOL_SLUGS", flags=re.S)
    s = sub_once(s, r"const RPC_PINNED_SLUGS = \[(.*?)\];", lambda m: "const RPC_PINNED_SLUGS = [\n" + render_list(rpc_slugs) + "];",
                 "worker RPC_PINNED_SLUGS", flags=re.S)
    # the "uniswap" lookup now also returns the new uniswap-v4 protocol (prefix match), after uniswap-governance-timelock
    s = sub_once(s, re.escape('assert.deepEqual(top(r), ["uniswap-governance-timelock"]);'),
                 'assert.deepEqual(top(r), ["uniswap-governance-timelock", "uniswap-v4"]);', "worker uniswap lookup")
    old, new = FOOTER_PROBE
    if new not in rpc_slugs:
        fail(f"citation-footer probe: {new} must stay rpc_observed", 1)
    if old != new:
        if old in rpc_slugs:
            fail(f"citation-footer probe: {old} must be converted", 1)
        s = sub_once(s, re.escape(f'["{old}", "{old}"]'), f'["{new}", "{new}"]', "worker footer probe case")
        s = sub_once(s, re.escape(f'slug !== "{old}"'), f'slug !== "{new}"', "worker footer probe easAttested")
    else:
        sub_once(s, re.escape(f'["{new}", "{new}"]'), f'["{new}", "{new}"]', "worker footer probe case (unchanged)")
    write(p, s)
    p = os.path.join(core, "packages", "analytics-sync", "test_analytics_sync.py")
    write(p, sub_once(read(p), r'PUBLISHED = \{"protocols": \d+, "easAttestedProtocols": \d+, "rpcObservedProtocols": \d+\}',
                      f'PUBLISHED = {{"protocols": {t["protocols"]}, "easAttestedProtocols": {t["eas_protocols"]}, "rpcObservedProtocols": {t["rpc_protocols"]}}}',
                      "analytics PUBLISHED"))
    check_core_catalog(core)


def check_core_catalog(core):
    """The worker's LOOKUP catalog (synced from lookup.mjs) must fit the lookup limit, and the analytics allow-lists must
    carry exactly the published protocol slugs (Sprint + RPC-pinned) with WAVE2 = the RPC-pinned ones."""
    t = TARGET
    lk = read(os.path.join(ROOT, "packages", "mcp-server", "src", "lookup.mjs"))
    n_items = len(json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "lookup.json")))["items"])
    m = re.search(r"maxLimit: ([^,]+),", lk)
    if not m or (m.group(1).strip() != "LOOKUP_CATALOG.length" and not (m.group(1).strip().isdigit() and n_items <= int(m.group(1)))):
        fail(f"LOOKUP_LIMITS.maxLimit {m and m.group(1)!r} does not cover the {n_items}-item catalog", 1)
    if n_items != t["protocols"] + t["briefs"]:
        fail(f"lookup catalog has {n_items} items, expected {t['protocols'] + t['briefs']}", 1)
    ns = {}
    src = read(os.path.join(core, "packages", "analytics-sync", "analytics_sync.py"))
    for name in ("WAVE2_SLUGS", "KNOWN_PROTOCOL_SLUGS"):
        mm = re.search(rf"^{name} = frozenset\(\{{(.*?)\}}\)", src, re.S | re.M)
        if not mm:
            fail(f"analytics_sync.py: {name} not found", 1)
        ns[name] = set(re.findall(r'"([a-z0-9-]+)"', mm.group(1)))
    lkj = json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "lookup.json")))
    prot = {x["slug"]: x["easAttested"] for x in lkj["items"] if x["kind"] == "protocol"}
    if ns["KNOWN_PROTOCOL_SLUGS"] != set(prot) or ns["WAVE2_SLUGS"] != {k for k, v in prot.items() if not v}:
        fail("analytics_sync allow-lists differ from the published protocol slugs", 1)
    w = read(os.path.join(core, "packages", "x402-edge-worker", "worker.mjs"))
    toml = read(os.path.join(core, "packages", "x402-edge-worker", "wrangler.toml"))
    if 'export const FREE_LAUNCH = "free_launch";' not in w or re.search(r"^\s*PRICING_MODE\s*=", toml, re.M):
        fail("worker pricing mode is not the default free_launch (wrangler.toml must leave PRICING_MODE unset)", 1)


def tests(core, node):
    run([node, "--test"] + sorted(f"test/{f}" for f in os.listdir(os.path.join(ROOT, "packages", "mcp-server", "test")) if f.endswith(".test.mjs")),
        os.path.join(ROOT, "packages", "mcp-server"), "pacta-github-repo mcp-server tests")
    run(["git", "diff", "--check"], ROOT, "pacta-github-repo git diff --check")
    if not core:
        return
    w = os.path.join(core, "packages", "x402-edge-worker")
    run([node, "--test"] + sorted(f"test/{f}" for f in os.listdir(os.path.join(w, "test")) if f.endswith(".test.mjs")), w, "worker tests")
    run([sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"], os.path.join(w, "test"), "worker deploy tests")
    m = os.path.join(core, "packages", "mcp-server")
    run([node, "--test"] + sorted(f"test/{f}" for f in os.listdir(os.path.join(m, "test")) if f.endswith(".test.mjs")), m, "pacta-core mcp-server tests")
    run([sys.executable, "-m", "unittest", "test_analytics_sync"], os.path.join(core, "packages", "analytics-sync"), "analytics-sync tests")
    run([sys.executable, "-B", "scripts/sync-lookup-catalog.py", "--check"], core, "sync-lookup-catalog --check")
    run([sys.executable, "packages/agent-directory-prs/verify_directory_prs.py"], core, "verify_directory_prs")
    run([sys.executable, "scripts/check-no-secrets-or-quarantine.py", "--all"], core, "secret / quarantine gate")
    run(["git", "diff", "--check"], core, "pacta-core git diff --check")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--uid", required=True, help=f"Base EAS attestation UID of the Sprint {SPRINT} summary (0x + 64 hex)")
    ap.add_argument("--tx", required=True, help="Base transaction that created it (0x + 64 hex)")
    ap.add_argument("--core", default=os.path.join(ROOT, "..", "pacta-core"), help="pacta-core checkout to sync (default ../pacta-core)")
    ap.add_argument("--no-core", action="store_true", help="stamp pacta-github-repo only")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--allow-placeholder", action="store_true", help="accept a repeated-byte UID / tx (preview runs only; never ship)")
    a = ap.parse_args(argv)
    uid, tx = a.uid.lower(), a.tx.lower()
    for name, h in (("--uid", uid), ("--tx", tx)):
        if not HEX32.fullmatch(h) or int(h, 16) == 0:
            fail(f"{name} must be 0x + 64 hex digits (non-zero)")
        if placeholder(h) and not a.allow_placeholder:
            fail(f"{name} {h[:10]}… is a repeated-byte placeholder; pass --allow-placeholder for a preview run")
    if uid == tx and not placeholder(uid):
        fail("--uid and --tx must differ (a real attestation UID is never its transaction hash)")
    core = None if a.no_core else os.path.abspath(a.core)
    if core and not os.path.isfile(os.path.join(core, "scripts", "sync-lookup-catalog.py")):
        fail(f"--core {core}: not a pacta-core checkout (use --no-core to skip)")
    node = os.environ.get("NODE") or shutil.which("node")
    if not node and not a.skip_tests:
        fail("node not found (set NODE or pass --skip-tests)")

    idx = json.loads(read(INDEX))
    have = idx["onchain_anchoring"]["sprint_eas_attestations"].get(str(SPRINT))
    if have is not None:
        txs = idx["onchain_anchoring"]["attestation_coverage"]["eas_multi_attest_txs"]
        if not (have == uid and txs.get(str(SPRINT)) == tx and any(e["sprint"] == SPRINT for e in idx["entries"])):
            fail(f"Sprint {SPRINT} is already stamped with UID {have} / tx {txs.get(str(SPRINT))}; refusing to overwrite")
        print(f"Sprint {SPRINT} is already stamped with {uid}: re-running the idempotent steps (rebuild, verify, pacta-core sync, tests)")
        return finish(core, node, a.skip_tests)
    if not os.path.exists(STAGED):
        fail(f"{os.path.relpath(STAGED, ROOT)} not found")
    staged = json.loads(read(STAGED))
    pinned = json.loads(read(PINNED))
    sha = check_staged(staged, idx, pinned)

    print(f"Sprint {SPRINT}: {len(staged['records'])} records, summary {sha}, verifiedCount {staged['eas']['verifiedCount']}, "
          f"driftCount {staged['eas']['driftCount']}; converts {', '.join(staged['converts_rpc_pinned'])}; UID {uid}; tx {tx}"
          + ("  [PLACEHOLDER: preview only]" if placeholder(uid) or placeholder(tx) else ""))
    idx = stamp_index(staged, uid, tx)
    m = idx["summary_metrics"]
    if (m["sprints_completed"], m["records_indexed"], len(idx["onchain_anchoring"]["sprint_eas_attestations"]),
            sum(e.get("chain") == "base" for e in idx["entries"])) != (TARGET["sprints"], TARGET["records"], TARGET["eas_attestations"], TARGET["base_records"]):
        fail(f"unexpected index totals {m}", 1)
    convert_pinned(staged)
    wire_bounties(staged)
    add_tokens()
    set_expect(staged)
    readme(staged, uid, tx)
    mcp_counts(os.path.join(ROOT, "packages", "mcp-server"))
    os.remove(STAGED)
    if not os.listdir(os.path.dirname(STAGED)):
        os.rmdir(os.path.dirname(STAGED))
    return finish(core, node, a.skip_tests)


def finish(core, node, skip_tests):
    """Everything after the stamp; idempotent, so a re-run with the same --uid / --tx completes an interrupted apply."""
    build_twice()
    # the published graph only grows: record the new Sprint nodes / edges as minted (existing entries are never edited)
    run([sys.executable, "-B", "tools/graph_manifest.py", "--mint"], ROOT, "graph_manifest --mint")
    build_twice()                                     # the manifest after minting is the published one
    print(f"  graph manifest re-pinned: {pin_graph_manifest()}")
    lk = json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "lookup.json")))["totals"]
    pj = json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "protocols.json")))
    if (lk["protocols"], lk["easAttestedProtocols"], lk["rpcObservedProtocols"], pj["totals"]["badgeTiers"]) != (
            TARGET["protocols"], TARGET["eas_protocols"], TARGET["rpc_protocols"], TARGET["badge_tiers"]):
        fail(f"catalog totals {lk} / badge tiers {pj['totals']['badgeTiers']} differ from TARGET {TARGET}", 1)
    slugs = [p["slug"] for p in pj["protocols"]]
    if len(slugs) != len(set(slugs)) or len(slugs) != TARGET["protocols"]:
        fail(f"protocols.json lists {len(slugs)} protocols ({len(set(slugs))} distinct slugs); expected {TARGET['protocols']}", 1)
    pin = json.loads(read(PINNED))
    idx = json.loads(read(INDEX))
    uid = idx["onchain_anchoring"]["sprint_eas_attestations"][str(SPRINT)]
    for p in pj["protocols"]:
        if any(e["slug"] == p["slug"] for e in pin["entries"]) == p["easAttested"]:
            fail(f"protocols.json {p['slug']}: easAttested {p['easAttested']} contradicts rpc-pinned.json", 1)
        if SPRINT in p.get("sprints", []) and (not p["easAttested"] or uid not in p["baseEasUids"] or p["badge"]["tier"] == "rpc_observed"):
            fail(f"protocols.json {p['slug']}: Sprint {SPRINT} protocol not stamped", 1)
    if len([f for f in os.listdir(os.path.join(ROOT, "docs", "badges")) if f.endswith(".svg")]) != TARGET["protocols"]:
        fail("badge count differs from the protocol count", 1)
    lb = json.loads(read(LEADERBOARD))
    for slug, c in BOUNTY_CREDITS.items():
        page = read(os.path.join(ROOT, "docs", "protocols", slug, "index.html"))
        if f'data-research-credit="{c["hunter"]}"' not in page or f'/pull/{c["pr"]}"' not in page or lb["easAttestations"].get(c["hunter"], 0) < 1:
            fail(f"{slug}: research credit for @{c['hunter']} (PR #{c['pr']}) missing on the page or the leaderboard", 1)
    run([sys.executable, "verify_site_v2.py"], ROOT, "verify_site_v2")
    if core:
        sync_core(core)
    if not skip_tests:
        tests(core, node)
    print(f"done: Sprint {SPRINT} stamped ({TARGET['records']} records, {TARGET['sprints']} sprints, {TARGET['protocols']} protocol pages = "
          f"{TARGET['eas_protocols']} EAS + {TARGET['rpc_protocols']} RPC, {TARGET['protocols']} badges). Review the diffs, then commit; nothing was pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
