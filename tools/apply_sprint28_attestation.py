#!/usr/bin/env python3
"""apply_sprint28_attestation.py - stamp the Sprint 28 Base EAS attestation and publish the staged Sprint 28 promotion.

    python3 tools/apply_sprint28_attestation.py --uid 0x<32-byte UID> --tx 0x<32-byte tx hash> [--core ../pacta-core] [--skip-tests]

Input: tools/staged/sprint-28-records.json (the Sprint 28 records, their summary audits/sprint-28/block-<n>-summary.md, the Ethereum
pin and the Base pin; Base records are read at the Base pin, every other record at the Ethereum pin). The UID must be the attestation of
that summary under schema 0x7ff4..df83 (chainId 1, the Ethereum pin, verifiedCount = aligned + protective records, driftCount =
parameter-delta records, summarySha256 = the staged SHA-256); this script does not read the chain, so check the UID on
base.easscan.org first. The summary file is never modified, so its SHA-256 is the same before and after the stamp.

Sprint 28 is the Pod 1 Wave 4 promotion (bulk harvester v2.0). New protocols of batches A-001..A-014 whose documentation was
compared on chain enter index.json as Base-EAS-attested records; the other new protocols of the cohort enter rpc-pinned.json as
RPC-pinned (rpc_observed) records at the same pins. Published RPC-pinned protocols whose v2.0 re-score produced documentation-compared
records that re-validate at the Sprint pins are converted (staged "converts_rpc_pinned": their RPC-pinned records are retired and
their Base-EAS records added; the slug stays). The merged community bounty gaps (Wave 1 Slot #4 and six Wave 2 PRs) become records
with hunter credit (staged "bounty_credits"; bounties/leaderboard.json gains wave2Credits and easAttestations sums both waves): three are new protocols (Upshift,
40 Acres (Base), DeFi Saver), Vesper V1 converts in place, and Inverse Finance (FiRM) / Yearn V3 gain maintenance records. Every other
published RPC-pinned record moves to the Sprint pins with each stated fact re-read; a controller Safe whose quorum changed is stated as
read (staged "repin_changes"). The radar gains a sixth decoded brief (NEW_BRIEFS: Lombard op 0xd07f). Graph node ids minted before
this Sprint are recorded in tools/graph_u4_baseline.json (minted_before).

It then, in one pass: index.json, rpc-pinned.json, graph_controller_facts.json, TOKENS, summary_short.SUMMARY, x-handles, claims.py,
the verify_site_v2.py EXPECT block and GRAPH_MANIFEST_SHA256, README / REMEDIATION_SERVICES coverage lines, @pacta/mcp-server counts,
the site rebuild, X feed, receipt cards, basket counts, graph mint, and in pacta-core the catalog / worker / analytics / x-feed sync;
then both repositories' test suites (unless --skip-tests). Nothing is committed, pushed or deployed.

The receipt cards need Pillow 11.0.0 (set PACTA_PILLOW_PATH to a directory holding it, or have it importable).
Re-running with the same --uid / --tx is a no-op; a different UID or tx for an already stamped Sprint 28 is refused.
UIDs / tx hashes made of one repeated byte (e.g. 0x2727..27) are placeholders: they need --allow-placeholder (preview only),
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
SPRINT = 28
# open community hunter PRs: these protocols gain no record and no conversion while the PR is open (none: #32 ... #71 merged)
NO_TOUCH = ()
LEADERBOARD = os.path.join(ROOT, "bounties", "leaderboard.json")
STAGED = os.path.join(HERE, "staged", f"sprint-{SPRINT}-records.json")
INDEX = os.path.join(ROOT, "docs", "api", "v1", "index.json")
PINNED = os.path.join(ROOT, "docs", "api", "v1", "rpc-pinned.json")
FACTS = os.path.join(HERE, "graph_controller_facts.json")
HEX32 = re.compile(r"0x[0-9a-f]{64}")
# radar briefs first published with this Sprint (tools/briefs_decoded.json + build_site.BRIEFS; the radar refresh lists them)
NEW_BRIEFS = ("lombard-op-0xd07f",)
# The published numbers after the stamp. predict_target() re-derives every number from the data and must agree before anything is
# written.
TARGET = {"sprints": 28, "records": 218, "eas_attestations": 28, "protocols": 309, "eas_protocols": 113, "rpc_protocols": 196, "briefs": 14,
          "badge_tiers": {"aligned": 69, "parameter_delta": 44, "rpc_observed": 196}, "base_records": 31,
          "rpc_by_chain": {"ethereum": 178, "base": 18}}
ROW_NOTE = ("Pod 1 Wave 4 promotion (bulk harvester v2.0): Steakhouse Prime USDC (Base), Wintermute Confidential WBTC, Asymmetry Finance, "
            "KyberSwap Classic, MCDEX, DIEM Relay, APY Finance and Whales Market attested; merged community gaps Upshift, 40 Acres (Base), "
            "DeFi Saver, Vesper V1, Inverse Finance (FiRM) and Yearn V3; Strata Markets and Zircuit Staking converted to Base EAS; "
            "69 further protocols published RPC-pinned (229 → 309)")
# the worker's / MCP's rpc_observed citation-footer probe stays on extra-finance-base (still RPC-pinned after Sprint 28)
FOOTER_PROBE = ("extra-finance-base", "extra-finance-base")


def fail(msg, code=2):
    print(f"apply_sprint{SPRINT}_attestation: {msg}", file=sys.stderr)
    sys.exit(code)


def read(p, mode="r"):
    with open(p, mode, **({} if "b" in mode else {"encoding": "utf-8"})) as fh:
        return fh.read()


def write(p, text):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def dump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


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


def run(cmd, cwd, name, env=None):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=1800)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print(f"  [{'ok' if r.returncode == 0 else 'FAIL'}] {name}: {' | '.join(tail)[:300]}")
    if r.returncode != 0:
        fail(f"{name} failed (exit {r.returncode})", 1)
    return r.stdout


def expect_now():
    s = read(os.path.join(ROOT, "verify_site_v2.py"))
    a, b = s.index("# ---- EXPECT-BEGIN"), s.index("# ---- EXPECT-END")
    ns = {}
    exec(s[s.index("EXPECT = {", a):b], ns)
    return ns["EXPECT"]


# ---------------------------------------------------------------- checks before writing
CORE_HINT = {"path": None}


def core_claims():
    """The slugs that already have a claims.py line in the pacta-core checkout (empty when no core is known yet)."""
    p = CORE_HINT["path"]
    if not p:
        return set()
    ns = {}
    exec(compile(read(os.path.join(p, "packages", "x-feed", "claims.py")), "claims.py", "exec"), ns)
    return set(ns["CLAIMS"])


def predict_target(staged, idx, pinned):
    """The post-stamp totals derived from the data alone; must equal TARGET."""
    es = idx["entries"] + staged["records"]
    rp = staged["rpc_pinned"]
    pin_after = rp["repinned"] + rp["entries"]
    names = {e["protocol"] for e in es}
    tiers = {"aligned": 0, "parameter_delta": 0, "rpc_observed": len({e["slug"] for e in pin_after})}
    for n in names:
        cl = {e["classification"] for e in es if e["protocol"] == n}
        tiers["aligned" if cl == {"aligned_baseline"} else "parameter_delta"] += 1
    eas = len(names)
    return {"sprints": max(e["sprint"] for e in es), "records": len(es),
            "eas_attestations": len(idx["onchain_anchoring"]["sprint_eas_attestations"]) + 1,
            "protocols": eas + tiers["rpc_observed"], "eas_protocols": eas, "rpc_protocols": tiers["rpc_observed"],
            "briefs": expect_now()["briefs"] + len(NEW_BRIEFS), "badge_tiers": tiers, "base_records": sum(e.get("chain") == "base" for e in es),
            "rpc_by_chain": {c: sum(e["chain"] == c for e in pin_after) for c in ("ethereum", "base")}}


def check_staged(staged, idx, pinned):
    sha = "0x" + hashlib.sha256(read(os.path.join(ROOT, staged["summary_doc"]), "rb")).hexdigest()
    rs = staged["records"]
    cls = [r["classification"] for r in rs]
    if staged["sprint"] != SPRINT or staged["summary_sha256"] != sha or any(r["summary_sha256"] != sha or r["sprint"] != SPRINT
                                                                            or r["summary_doc"] != staged["summary_doc"] for r in rs):
        fail(f"staged bundle does not match {staged['summary_doc']} (sha256 {sha})")
    e = staged["eas"]
    eth, base = staged["pins"]["ethereum"], staged["pins"]["base"]
    if (e["chainId"], e["blockNumber"], e["blockHash"]) != (1, eth["block_number"], eth["block_hash"]):
        fail("staged EAS block differs from the Ethereum pin")
    # Same convention as Sprints 1-25 (and PactaSentinelGuard: driftCount != 0 means drift): verifiedCount = aligned + protective
    # records, driftCount = parameter-delta records. RPC-pinned records are not attested and never counted.
    if (e["verifiedCount"], e["driftCount"]) != (cls.count("aligned_baseline") + cls.count("protective_delta"), cls.count("parameter_delta")):
        fail("staged EAS counts do not match the record classifications")
    decoded = {b["slug"] for b in json.loads(read(os.path.join(HERE, "briefs_decoded.json")))["briefs"]}
    radar = {it["brief"] for it in json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "radar.json")))["items"]}
    bs_src = read(os.path.join(HERE, "build_site.py"))
    for b in NEW_BRIEFS:
        if b not in decoded or f"briefs/{b}/" not in radar or f'\n    "{b}": "Pre-execution brief' not in bs_src:
            fail(f"new brief {b}: not decoded in briefs_decoded.json, not on the radar, or not in build_site.BRIEFS")
    if staged.get("slug_overrides") or staged.get("reverified"):
        fail(f"Sprint {SPRINT} overrides no slug and re-verifies no record in place")
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
    published = {protocol_slug(n) for n in idx_names} | {x["slug"] for x in pinned["entries"]}
    maint = staged.get("maintenance") or {}
    for slug, name in maint.items():
        if name not in idx_names or protocol_slug(name) != slug:
            fail(f"maintenance {slug}: not a published Base-EAS protocol named {name!r}")
    new = {p["slug"]: p for p in staged["new_protocols"]}
    converts = staged.get("converts_rpc_pinned") or {}
    pinned_by = {x["slug"]: x for x in pinned["entries"]}
    for slug, c in converts.items():
        if slug not in pinned_by or pinned_by[slug]["protocol"] != c["name"] or protocol_slug(c["name"]) != slug or slug in new:
            fail(f"conversion {slug}: not a published RPC-pinned protocol named {c['name']!r}")
        if sorted(r["id"] for r in rs if r["protocol"] == c["name"]) != sorted(c["records"]):
            fail(f"conversion {slug}: its staged records differ from the conversion's record ids")
    eas_new = {r["protocol"] for r in rs} - set(maint.values()) - {c["name"] for c in converts.values()}
    for name in eas_new:
        if name in idx_names or protocol_slug(name) in published:
            fail(f"{name}: already a published protocol")
        if new.get(protocol_slug(name), {}).get("basis") != "eas":
            fail(f"{name}: an EAS record of a protocol not staged as a new EAS protocol")
    rp = staged["rpc_pinned"]
    heads = rp["pinned_heads"]
    for ch in ("ethereum", "base"):
        if (heads[ch]["block_number"], heads[ch]["block_hash"]) != (staged["pins"][ch]["block_number"], staged["pins"][ch]["block_hash"]):
            fail(f"rpc_pinned.pinned_heads.{ch} differs from the Sprint pin")
    for x in rp["entries"] + rp["repinned"]:
        h = heads[x["chain"]]
        if (x["block_number"], x["block_hash"]) != (h["block_number"], h["block_hash"]) or x["base_eas_uid"] is not None:
            fail(f"rpc-pinned {x['id']}: not on the pinned head of its chain (or carries a UID)")
    old = {x["id"]: x for x in pinned["entries"] if x["slug"] not in converts}
    if sorted(old) != sorted(x["id"] for x in rp["repinned"]):
        fail("rpc_pinned.repinned must be exactly the published RPC-pinned records that are not converted")
    changes = staged.get("repin_changes") or {}
    for x in rp["repinned"]:
        o = old[x["id"]]
        diff = sorted(k for k in set(o) | set(x) if o.get(k) != x.get(k))
        text = o["onchain_observed"].replace(f"#{o['block_number']:,}", f"#{x['block_number']:,}")
        ch = changes.get(x["slug"])
        if ch:                                       # a controller Safe quorum re-read at the Sprint pin: the only fact that may change
            q0, q1 = ch["safe_quorum"]
            if (o.get("safe_quorum"), x.get("safe_quorum")) != (q0, q1) or text.count(f"Safe {q0}") != 1:
                fail(f"rpc_pinned.repinned {x['id']}: staged quorum change {ch} does not match the records")
            text = text.replace(f"Safe {q0}", f"Safe {q1}")
            allowed = {"block_number", "block_hash", "onchain_observed", "safe_quorum"}
        else:
            allowed = {"block_number", "block_hash", "onchain_observed"}
        if set(diff) - allowed or x["onchain_observed"] != text:
            fail(f"rpc_pinned.repinned {x['id']}: changes {diff}; only the pin (and a staged quorum change) may move")
    if set(changes) - {o_["slug"] for o_ in old.values()}:
        fail("repin_changes names a protocol that is not re-pinned")
    credits = staged.get("bounty_credits") or {}
    ids = {r["id"] for r in rs}
    for slug, cs_ in credits.items():
        for c in cs_:
            if (c["record"] not in ids and c["record"] not in {x["id"] for x in idx["entries"]}) or not os.path.exists(os.path.join(ROOT, c["fixture"])):
                fail(f"bounty credit {slug} PR #{c['pr']}: record {c['record']} not staged or fixture {c['fixture']} missing")
    rpc_new = {x["slug"] for x in rp["entries"]}
    if len(rpc_new) != len(rp["entries"]) or rpc_new & published or any(new.get(s, {}).get("basis") != "rpc_pinned" for s in rpc_new):
        fail("rpc_pinned.entries: one record per new RPC-pinned protocol, none already published")
    if {s for s, p in new.items() if p["basis"] == "eas"} != {protocol_slug(n) for n in eas_new} or \
            {s for s, p in new.items() if p["basis"] == "rpc_pinned"} != rpc_new:
        fail("new_protocols does not match the staged records")
    for key in ("tokens", "summary_lines"):
        if set(staged[key]) != set(new):
            fail(f"staged {key} must cover exactly the new protocols")
    conv_slugs = set(converts)
    deltas = {protocol_slug(r["protocol"]) for r in rs if r["classification"] in ("parameter_delta", "protective_delta")
              and r["protocol"] not in maint.values()} - {s_ for s_ in conv_slugs if s_ in core_claims()}
    claims_now = core_claims()
    deltas |= {s_ for s_, n_ in maint.items() if s_ not in claims_now
               and any(r["protocol"] == n_ and r["classification"] in ("parameter_delta", "protective_delta") for r in rs)}
    staged_x = set(staged.get("x_claims") or {})
    if deltas - staged_x or (staged_x - deltas) - set(claims_now):
        # a maintenance protocol that already has its claims.py line may carry a staged one (x_claims() keeps the published line)
        fail(f"staged x_claims must cover exactly the new delta / protective protocols {sorted(deltas)}")
    if set(staged.get("summary_line_updates") or {}) - set(maint) - conv_slugs - set(changes):
        fail("summary_line_updates may only change the line of a maintenance, converted or re-quorumed protocol")
    for r in rs:
        if protocol_slug(r["protocol"]) in NO_TOUCH:
            fail(f"{r['protocol']}: held by an open hunter PR; no record while it is open")
    if sorted(x["slug"] for x in staged["x_handles"]) != sorted(new):
        fail("staged x_handles must cover exactly the new protocols")
    for x in staged["x_handles"]:
        if (x["xHandle"] is None) != (x["xUrl"] is None) or (x["xHandle"] and not x.get("proofs")):
            fail(f"x_handles {x['slug']}: a handle needs its proofs (or null with no URL)")
    facts = json.loads(read(FACTS))
    for k, v in staged["controller_facts"]["contracts"].items():
        if k in facts["contracts"] and facts["contracts"][k] != v and facts["contracts"][k].get("pin") != v.get("pin"):
            pass                                                     # a contract re-read at the Sprint pin replaces its older facts
    for k, v in staged["controller_facts"]["pins"].items():
        if k in facts["pins"] and facts["pins"][k] != v:
            fail(f"graph_controller_facts pin {k} already exists with other values")
    got = predict_target(staged, idx, pinned)
    if got != TARGET:
        fail(f"derived totals {got} differ from TARGET {TARGET}")
    return sha


# ---------------------------------------------------------------- pacta-github-repo
def stamp_index(staged, uid, tx):
    idx = json.loads(read(INDEX))
    anc, cov = idx["onchain_anchoring"], idx["onchain_anchoring"]["attestation_coverage"]
    idx["entries"].extend({**r, "base_eas_uid": uid} for r in staged["records"])
    anc["sprint_eas_attestations"][str(SPRINT)] = uid
    anc[f"eas_multi_attest_sprint_{SPRINT}_tx"] = tx
    cov["base_eas_attested_sprints"] = f"1-{SPRINT}"
    cov["eas_multi_attest_txs"][str(SPRINT)] = tx
    cov["attested_not_yet_indexed_sprints"] = []
    idx["methodology"]["archive_rpc_endpoints_by_chain"] = {ch: staged["pins"][ch]["rpcs"] for ch in ("ethereum", "base")}
    es = idx["entries"]
    cls = [e["classification"] for e in es]
    idx["summary_metrics"] = {"sprints_completed": max(e["sprint"] for e in es), "records_indexed": len(es),
                              "parameter_deltas": cls.count("parameter_delta"), "protective_deltas": cls.count("protective_delta"),
                              "aligned_baselines": cls.count("aligned_baseline")}
    idx["generated_at"] = max(idx["generated_at"], iso(staged["pins"]["ethereum"]["timestamp"]))
    write(INDEX, dump(idx))
    return idx


def publish_pinned(staged):
    """rpc-pinned.json: every record on the Sprint pinned heads (the published ones re-pinned, the new promotions added)."""
    p = json.loads(read(PINNED))
    rp = staged["rpc_pinned"]
    before = {e["slug"] for e in p["entries"]}
    p["pinned_heads"] = rp["pinned_heads"]
    converted = set(staged.get("converts_rpc_pinned") or {})
    # the retired RPC-pinned records of converted protocols stay governed in the graph (tools/graph_retired.json; idempotent)
    gr_path = os.path.join(HERE, "graph_retired.json")
    gr = json.loads(read(gr_path)) if os.path.exists(gr_path) else {
        "schema": "pacta.graph_retired.v1",
        "description": "RPC-pinned records retired when their protocol was converted to Base-EAS records. tools/graph_manifest.py keeps "
                       "their contracts governed by that protocol (the graph only grows).", "records": []}
    have_ids = {r["record_id"] for r in gr["records"]}
    for e in p["entries"]:
        if e["slug"] in converted and e["id"] not in have_ids:
            gr["records"].append({"slug": e["slug"], "chain": e["chain"], "record_id": e["id"], "retired_at_sprint": SPRINT,
                                  "target_contract": e["target_contract"], "target_label": e.get("target_label"),
                                  "controller_address": e.get("controller_address"), "controller_kind": e.get("controller_kind")})
    gr["records"].sort(key=lambda r: (r["slug"], r["record_id"]))
    write(gr_path, json.dumps(gr, indent=1) + "\n")
    p["entries"] = rp["repinned"] + sorted(rp["entries"], key=lambda e: e["slug"])
    p["protocols"] = [x for x in p["protocols"] if x["slug"] not in converted]
    before -= converted
    have = {x["slug"] for x in p["protocols"]}
    for e in rp["entries"]:
        if e["slug"] not in have:
            p["protocols"].append({"slug": e["slug"], "name": e["protocol"], "family": e["family"], "category": e["category"],
                                   "chain": e["chain"], "chain_label": e["chain_label"], "record_ids": [e["id"]]})
    p["protocols"].sort(key=lambda x: x["slug"])
    if {x["slug"] for x in p["protocols"]} != {e["slug"] for e in p["entries"]} or not before <= {e["slug"] for e in p["entries"]}:
        fail("rpc-pinned.json: protocols list and records disagree", 1)
    by = {c: sum(e["chain"] == c for e in p["entries"]) for c in ("ethereum", "base")}
    p["summary"] = {"protocols": len(p["protocols"]), "records": len(p["entries"]), **by}
    p["description"] = sub_once(p["description"], r"observations of \d+ protocols \(\d+ Ethereum, \d+ Base\)",
                                f"observations of {len(p['protocols'])} protocols ({by['ethereum']} Ethereum, {by['base']} Base)", "rpc-pinned description")
    note = (f" Sprint {SPRINT} published {len(rp['entries'])} further protocols here (bulk harvester v2.0 promotion, documentation not "
            f"compared), converted {len(converted)} to Base-EAS records ({', '.join(sorted(converted))}) and moved every other record to "
            f"the Sprint {SPRINT} pinned heads, each stated fact re-read" + (" (a controller Safe quorum changed: " + ", ".join(
                f"{k} {v['safe_quorum'][0]} -> {v['safe_quorum'][1]}" for k, v in sorted((staged.get("repin_changes") or {}).items())) + ")."
                if staged.get("repin_changes") else "."))
    if note.strip() not in p["description"]:
        p["description"] += note
    p["generated_at"] = max(p["generated_at"], iso(staged["pins"]["ethereum"]["timestamp"]))
    write(PINNED, dump(p))
    return p


def merge_facts(staged):
    f = json.loads(read(FACTS))
    f["pins"].update(staged["controller_facts"]["pins"])
    held = set(f.get("held_protocols") or [])
    for k, v in staged["controller_facts"]["contracts"].items():
        if k not in f["contracts"]:
            f["contracts"][k] = v
    f["contracts"] = dict(sorted(f["contracts"].items()))
    f["pins"] = dict(sorted(f["pins"].items()))
    if held & {p["slug"] for p in staged["new_protocols"]}:
        fail("a new protocol is held (open bounty PR)", 1)
    write(FACTS, dump(f))


def summary_lines(staged):
    """Write the staged summary lines into tools/summary_short.py (SUMMARY stays one sorted line per slug; idempotent)."""
    p = os.path.join(HERE, "summary_short.py")
    s = read(p)
    m = re.search(r"^SUMMARY = \{\n(.*?)^\}\n", s, re.S | re.M)
    if not m:
        fail("summary_short.py: SUMMARY block not found", 1)
    ns = {}
    exec("SUMMARY = {\n" + m.group(1) + "}\n", ns)
    cur = ns["SUMMARY"]
    if "".join(f"    {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},\n" for k, v in sorted(cur.items())) != m.group(1):
        fail("summary_short.py: SUMMARY is not one sorted line per slug; refusing to rewrite it", 1)
    sys.path.insert(0, HERE)
    import summary_short
    lines = staged["summary_lines"]
    bad = {k: summary_short.problems(v) for k, v in lines.items() if summary_short.problems(v)}
    if bad:
        fail(f"staged summary lines fail M7: {bad}", 1)
    clash = {k for k in lines if k in cur and cur[k] != lines[k]}
    if clash:
        fail(f"summary_short.py already has other lines for {sorted(clash)}", 1)
    cur.update(lines)
    upd = staged.get("summary_line_updates") or {}
    bad = {k: summary_short.problems(v) for k, v in upd.items() if summary_short.problems(v)}
    if bad or any(k not in cur for k in upd):
        fail(f"summary_line_updates: {bad or 'a maintenance protocol without a published line'}", 1)
    cur.update(upd)
    body = "".join(f"    {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},\n" for k, v in sorted(cur.items()))
    write(p, s[:m.start(1)] + body + s[m.end(1):])


def add_tokens(staged):
    p = os.path.join(HERE, "build_lookup.py")
    s = read(p)
    if f"# Sprint {SPRINT} promotion" in s:
        return
    rows = [f'"{k}": {json.dumps(v, ensure_ascii=False)}' for k, v in sorted(staged["tokens"].items())]
    body, cur = [], ""
    for x in rows:
        cand = f"{cur}, {x}" if cur else x
        if cur and len("    " + cand + ",") > 140:
            body.append("    " + cur + ",")
            cur = x
        else:
            cur = cand
    body.append("    " + cur + ",")
    block = f"    # Sprint {SPRINT} promotion (bulk harvester v2.0)\n" + "\n".join(body) + "\n    # briefs\n"
    write(p, sub_once(s, r"    # briefs\n", lambda m: block, "build_lookup TOKENS"))


def record_minted_before():
    """U4: record the graph node ids minted before this Sprint (tools/graph_minted.json as published) in tools/graph_u4_baseline.json.
    Their texts are immutable and the TF-IDF cosine of a pair of them rises with corpus size, so verify_site_v2 holds such pairs to the
    baseline ceiling; every pair with a node first published in this Sprint stays below GRAPH_TAU. Idempotent."""
    p = os.path.join(HERE, "graph_u4_baseline.json")
    u4 = json.loads(read(p))
    if (u4.get("minted_before") or {}).get("sprint") == SPRINT:
        return
    minted = sorted(json.loads(read(os.path.join(HERE, "graph_minted.json")))["nodes"])
    if not set(u4["nodes"]) <= set(minted):
        fail("graph_u4_baseline.json: a pre-Sprint-24 baseline node is not in graph_minted.json", 1)
    u4["minted_before"] = {"sprint": SPRINT, "count": len(minted), "nodes": minted}
    write(p, json.dumps(u4, indent=1) + "\n")


# bounties/leaderboard.json easAttestations before Sprint 28: the Wave 1 slot 1-3 catches attested in earlier sprints
EAS_CREDITS_BEFORE = {"kinshu7777": 1, "scavenger-osan": 1, "veriton-dev": 1}


def wire_bounties(staged):
    """bounties/leaderboard.json easAttestations = the Base-EAS records credited to each hunter across every wave: the credits
    attested before Sprint 28 (EAS_CREDITS_BEFORE) plus this Sprint's staged credits (Wave 1 slot 4 and Wave 2). Fails closed on
    any other starting state; a re-run is a no-op."""
    credits = staged.get("bounty_credits") or {}
    counts = {}
    for cs_ in credits.values():
        for c in cs_:
            counts[c["hunter"]] = counts.get(c["hunter"], 0) + 1
    want = dict(EAS_CREDITS_BEFORE)
    for h, n in counts.items():
        want[h] = want.get(h, 0) + n
    want = {h: want[h] for h in sorted(want)}
    # the Wave 2 credits, so each published protocol page credits its hunters (Wave 1 credits come from the slot fixtures)
    w2 = sorted(({"fixture": os.path.basename(c["fixture"]), "pr": c["pr"], "pactaSlug": slug, "record": c["record"]}
                 for slug, cs_ in credits.items() for c in cs_ if c.get("wave") == 2), key=lambda c: c["pr"])
    lb = json.loads(read(LEADERBOARD))
    have = lb.get("easAttestations")
    if have not in (EAS_CREDITS_BEFORE, want) or lb.get("wave2Credits", []) not in ([], w2):
        fail(f"bounties/leaderboard.json easAttestations / wave2Credits are neither the pre-Sprint-{SPRINT} state nor the stamped one: {have}", 1)
    if have != want or lb.get("wave2Credits") != w2:
        lb["easAttestations"] = want
        lb["wave2Credits"] = w2
        write(LEADERBOARD, json.dumps(lb, indent=2, ensure_ascii=False) + "\n")
    return want


def pin_graph_manifest():
    """Re-pin verify_site_v2.GRAPH_MANIFEST_SHA256 to the rebuilt (and minted) graph manifest."""
    sha = hashlib.sha256(read(os.path.join(ROOT, "docs", "api", "v1", "graph-manifest.json"), "rb")).hexdigest()
    p = os.path.join(ROOT, "verify_site_v2.py")
    write(p, sub_once(read(p), r'^GRAPH_MANIFEST_SHA256 = "[0-9a-f]{64}"', f'GRAPH_MANIFEST_SHA256 = "{sha}"', "verify_site_v2 GRAPH_MANIFEST_SHA256",
                      flags=re.M))
    return sha


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
    exec(s[s.index("EXPECT = {", a):b], ns)
    x = {**ns["EXPECT"], **TARGET}
    x["multi_attest_txs"] = ns["EXPECT"]["multi_attest_txs"] + [str(SPRINT)]
    x["summaries"] = {**ns["EXPECT"]["summaries"], str(SPRINT): staged["summary_sha256"][2:]}
    write(p, s[:a] + head + render_expect(x) + s[b:])


def readme(staged, uid, tx):
    p = os.path.join(ROOT, "README.md")
    s = read(p)
    m = json.loads(read(INDEX))["summary_metrics"]
    t = TARGET
    cov = (f'**{t["protocols"]} protocols ({t["eas_protocols"]} Base-EAS attested + {t["rpc_protocols"]} RPC-observed) · {t["records"]} attested checks '
           f'across {t["eas_attestations"]} Base EAS batch attestations')
    s = sub_once(s, r"\*\*\d+ protocols \(\d+ Base-EAS attested \+ \d+ RPC-observed\) · \d+ attested checks across \d+ Base EAS batch attestations",
                 lambda m_: cov, "README coverage line", count=2)
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
    # REMEDIATION_SERVICES.md carries the same coverage numbers as the README (v4.5 G-P2-9)
    p = os.path.join(ROOT, "REMEDIATION_SERVICES.md")
    write(p, sub_once(read(p), r"\*\*\d+ protocols \(\d+ Base-EAS attested \+ \d+ RPC-observed\)\*\*, with \d+ attested checks across \d+ Base EAS batch attestations",
                      f'**{t["protocols"]} protocols ({t["eas_protocols"]} Base-EAS attested + {t["rpc_protocols"]} RPC-observed)**, with {t["records"]} '
                      f'attested checks across {t["eas_attestations"]} Base EAS batch attestations', "REMEDIATION_SERVICES coverage line"))


def basket_counts():
    """v4.7.1 V47-03: the harness pins the ?basket= row counts; they follow the published scorecards (new protocols join baskets)."""
    cards = json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "scorecards.json")))["protocols"]
    n = {b: sum(b in (c.get("baskets") or []) for c in cards) for b in ("stable_rwa", "eth_lst_lrt", "lending_vaults", "base")}
    if any(v >= len(cards) for v in n.values()):
        fail(f"a basket holds every protocol: {n}", 1)
    p = os.path.join(HERE, "app_harness.js")
    write(p, sub_once(read(p), r"out\.stable_rwa\.n === \d+ && out\.eth_lst_lrt\.n === \d+ && out\.lending_vaults\.n === \d+ && out\.base\.n === \d+",
                      f"out.stable_rwa.n === {n['stable_rwa']} && out.eth_lst_lrt.n === {n['eth_lst_lrt']} && out.lending_vaults.n === {n['lending_vaults']} "
                      f"&& out.base.n === {n['base']}", "app_harness basket counts"))
    p = os.path.join(ROOT, "verify_site_v2.py")
    write(p, sub_once(read(p), r"stable_rwa \d+, eth_lst_lrt \d+, lending_vaults \d+, base \d+;",
                      f"stable_rwa {n['stable_rwa']}, eth_lst_lrt {n['eth_lst_lrt']}, lending_vaults {n['lending_vaults']}, base {n['base']};",
                      "verify V47-03 basket counts"))
    return n


def mcp_counts(pkg):
    t = TARGET
    p = os.path.join(pkg, "test", "lookup.test.mjs")
    write(p, sub_once(read(p), r"const PUBLISHED = Object\.freeze\(\{[^}]*\}\);",
                      f'const PUBLISHED = Object.freeze({{ protocols: {t["protocols"]}, briefs: {t["briefs"]}, easAttestedProtocols: {t["eas_protocols"]}, '
                      f'rpcObservedProtocols: {t["rpc_protocols"]} }});', "mcp-server PUBLISHED"))
    p = os.path.join(pkg, "README.md")
    s = sub_once(read(p), r"  - Scope: \d+ Base-EAS-attested protocols", f'  - Scope: {t["eas_protocols"]} Base-EAS-attested protocols', "mcp README scope")
    write(p, sub_once(s, r"documentation compared\), \d+ RPC-observed protocols", f'documentation compared), {t["rpc_protocols"]} RPC-observed protocols',
                      "mcp README rpc scope"))


def snap_docs():
    out = {}
    for base, _, files in os.walk(os.path.join(ROOT, "docs")):
        for f in files:
            p = os.path.join(base, f)
            out[os.path.relpath(p, ROOT)] = hashlib.sha256(read(p, "rb")).hexdigest()
    return out


def build_once(i):
    run([sys.executable, "tools/build_b2a_feeds.py"], ROOT, f"build_b2a_feeds (pass {i})")
    run([sys.executable, "tools/build_site.py"], ROOT, f"build_site (pass {i})")
    shutil.copyfile(os.path.join(ROOT, "docs", "SKILL.md"), os.path.join(ROOT, "packages", "mcp-server", "SKILL.md"))


def build_twice():
    shots = []
    for i in (1, 2):
        build_once(i)
        shots.append(snap_docs())
    if shots[0] != shots[1]:
        fail(f"site build is not deterministic: {sorted(k for k in shots[0] if shots[0].get(k) != shots[1].get(k))[:5]}", 1)


# ---------------------------------------------------------------- X feed + receipt cards
def pillow_env():
    p = os.environ.get("PACTA_PILLOW_PATH")
    return {"PYTHONPATH": p} if p else {}


def stub_cards(staged):
    """build_site needs docs/cards/<slug>.png for every protocol page, and the cards come from the X feed, which reads the built
    scorecards: a new protocol's card is a copy of an existing card until build_x_feed / build_x_cards render its own."""
    cards = os.path.join(ROOT, "docs", "cards")
    src = os.path.join(cards, sorted(f for f in os.listdir(cards) if f.endswith(".png") and not f.startswith("radar-"))[0])
    stubs = []
    for p in staged_new_slugs(staged):
        dst = os.path.join(cards, f"{p}.png")
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
            stubs.append(dst)
    return src, stubs


def staged_new_slugs(staged):
    return sorted(p["slug"] for p in staged["new_protocols"])


def x_handles(core, staged):
    """packages/x-feed/x-handles.json + the staged entries (first-party proofs or null), sorted by slug as published."""
    p = os.path.join(core, "packages", "x-feed", "x-handles.json")
    reg = json.loads(read(p))
    have = {x["slug"] for x in reg["protocols"]}
    add = [x for x in staged["x_handles"] if x["slug"] not in have]
    reg["protocols"] = sorted(reg["protocols"] + add, key=lambda x: x["slug"])
    write(p, dump(reg))


def x_claims(core, staged):
    """packages/x-feed/claims.py: the staged "docs say / chain says" line of each new delta or protective protocol, inserted in
    slug order within its group (parameter deltas, protective deltas); build_x_feed binds every token to the scorecard evidence."""
    p = os.path.join(core, "packages", "x-feed", "claims.py")
    s = read(p)
    heads = {"parameter_delta": "    # ---- parameter deltas", "protective_delta": "    # ---- protective deltas"}
    for slug, c in sorted((staged.get("x_claims") or {}).items()):
        if f'    "{slug}": (' in s:
            continue
        line = (f'    "{slug}": ({json.dumps(c["docs"])}, {json.dumps(c["chain"])}, '
                f'({", ".join(json.dumps(t) for t in c["doc_tokens"])},), ({", ".join(json.dumps(t) for t in c["chain_tokens"])},)),\n')
        a = s.index(heads[c["group"]])
        nxt = [s.index(h) for h in heads.values() if s.index(h) > a] + [s.index("\n}\n", a)]
        b = min(nxt)
        keys = [(m.start() + a, m.group(1)) for m in re.finditer(r'^    "([a-z0-9.-]+)": \(', s[a:b], re.M)]
        at = next((i for i, k in keys if k > slug), b + 1 if b == s.index("\n}\n", a) else b)
        s = s[:at] + line + s[at:]
    write(p, s)
    ns = {}
    exec(compile(s, p, "exec"), ns)
    if any(k not in ns["CLAIMS"] for k in (staged.get("x_claims") or {})):
        fail("claims.py: a staged line did not land", 1)


def x_feed_and_cards(core):
    xf = os.path.join(core, "packages", "x-feed")
    run([sys.executable, "-B", os.path.join(xf, "build_x_feed.py"), "--site", ROOT, "--worker",
         os.path.join(core, "packages", "x402-edge-worker", "worker.mjs")], core, "build_x_feed (+ worker X_FEED)")
    for f in ("x-feed.json", "x-handles.json"):
        shutil.copyfile(os.path.join(xf, f), os.path.join(ROOT, "docs", "api", "v1", f))
    run([sys.executable, "-B", os.path.join(xf, "build_x_cards.py"), "--out", os.path.join(ROOT, "docs", "cards")], core,
        "build_x_cards", env=pillow_env())
    feed = json.loads(read(os.path.join(xf, "x-feed.json")))
    want = {i["cardFilename"] for i in feed["items"]}
    cards = os.path.join(ROOT, "docs", "cards")
    for f in sorted(os.listdir(cards)):                 # a radar card whose operation has executed leaves the feed, and its card goes
        if f.endswith(".png") and f.startswith("radar-") and f not in want:
            os.remove(os.path.join(cards, f))
            print(f"  removed docs/cards/{f} (its radar operation is no longer active)")
    have = {f for f in os.listdir(cards) if f.endswith(".png")}
    if want != have:
        fail(f"docs/cards differs from the feed's cards: missing {sorted(want - have)[:4]} extra {sorted(have - want)[:4]}", 1)


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
    if FOOTER_PROBE[1] not in rpc_slugs:
        fail(f"citation-footer probe: {FOOTER_PROBE[1]} must stay rpc_observed", 1)
    write(p, s)
    # the beacon's brief allow-list (worker + analytics) follows the published briefs: the v4.6 radar briefs had not reached it
    briefs = sorted(x["slug"] for x in lk["items"] if x["kind"] == "brief")
    if len(briefs) != t["briefs"]:
        fail(f"lookup.json has {len(briefs)} briefs, expected {t['briefs']}", 1)
    p = os.path.join(core, "packages", "x402-edge-worker", "worker.mjs")
    write(p, sub_once(read(p), r"export const BRIEF_SLUGS = new Set\(\[[^\]]*\]\);",
                      lambda m: "export const BRIEF_SLUGS = new Set([\n" + render_list(briefs) + "]);", "worker BRIEF_SLUGS", flags=re.S))
    p = os.path.join(core, "packages", "x402-edge-worker", "test", "worker.test.mjs")
    s = sub_once(read(p), r"assert\.equal\(BRIEF_SLUGS\.size, \d+\);", f"assert.equal(BRIEF_SLUGS.size, {t['briefs']});", "worker BRIEF_SLUGS size")
    pairs = [[x["slug"], x["relatedProtocolSlug"]] for x in lk["items"] if x.get("relatedProtocolSlug")]
    s = sub_once(s, r"(assert\.deepEqual\(LOOKUP_CATALOG\.filter\(\(x\) => x\.relatedProtocolSlug\)\.map\(\(x\) => \[x\.slug, x\.relatedProtocolSlug\]\),\n\s*)\[\[.*?\]\]\);",
                 lambda m: m.group(1) + json.dumps(pairs, separators=(", ", ": ")) + ");", "worker radar brief pairs", flags=re.S)
    write(p, s)
    p = os.path.join(core, "packages", "analytics-sync", "analytics_sync.py")
    write(p, sub_once(read(p), r"^BRIEF_SLUGS = frozenset\(\{[^}]*\}\)", lambda m: "BRIEF_SLUGS = frozenset({\n" + render_list(briefs, indent="    ") + "})",
                      "analytics BRIEF_SLUGS", flags=re.S | re.M))
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
        ns[name] = set(re.findall(r'"([a-z0-9.-]+)"', mm.group(1)))
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
    # tools/app_harness.js reads its synthetic DOM on stdin: verify_site_v2 builds that input and runs it (every harness scenario)
    run([sys.executable, "verify_site_v2.py"], ROOT, "verify_site_v2 (node tools/app_harness.js scenarios)")
    run(["git", "diff", "--check"], ROOT, "pacta-github-repo git diff --check")
    if not core:
        return
    w = os.path.join(core, "packages", "x402-edge-worker")
    run([node, "--test"] + sorted(f"test/{f}" for f in os.listdir(os.path.join(w, "test")) if f.endswith(".test.mjs")), w, "worker tests")
    run([sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"], os.path.join(w, "test"), "worker deploy tests")
    m = os.path.join(core, "packages", "mcp-server")
    run([node, "--test"] + sorted(f"test/{f}" for f in os.listdir(os.path.join(m, "test")) if f.endswith(".test.mjs")), m, "pacta-core mcp-server tests")
    run([sys.executable, "-m", "unittest", "test_analytics_sync"], os.path.join(core, "packages", "analytics-sync"), "analytics-sync tests")
    run([sys.executable, "-m", "unittest", "discover", "-s", "packages/x-feed", "-p", "test_*.py"], core, "x-feed tests", env=pillow_env())
    run([sys.executable, "-B", "packages/x-feed/build_x_feed.py", "--site", ROOT, "--worker", "packages/x402-edge-worker/worker.mjs", "--check"],
        core, "build_x_feed --check")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], os.path.join(core, "packages", "world-pulse"), "world-pulse tests")
    run([sys.executable, "-B", "scripts/sync-lookup-catalog.py", "--check"], core, "sync-lookup-catalog --check")
    run([sys.executable, "packages/agent-directory-prs/verify_directory_prs.py"], core, "verify_directory_prs")
    run([sys.executable, "scripts/check-no-secrets-or-quarantine.py", "--all"], core, "secret / quarantine gate")
    run(["git", "diff", "--check"], core, "pacta-core git diff --check")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--uid", required=True, help=f"Base EAS attestation UID of the Sprint {SPRINT} summary (0x + 64 hex)")
    ap.add_argument("--tx", required=True, help="Base transaction that created it (0x + 64 hex)")
    ap.add_argument("--core", default=os.path.join(ROOT, "..", "pacta-core"), help="pacta-core checkout to sync (default ../pacta-core)")
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
    core = os.path.abspath(a.core)
    CORE_HINT["path"] = core
    if not os.path.isfile(os.path.join(core, "scripts", "sync-lookup-catalog.py")):
        fail(f"--core {core}: not a pacta-core checkout (Sprint {SPRINT} rebuilds the X feed and handles there)")
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
        return finish(core, node, a.skip_tests, None)
    if not os.path.exists(STAGED):
        fail(f"{os.path.relpath(STAGED, ROOT)} not found")
    staged = json.loads(read(STAGED))
    pinned = json.loads(read(PINNED))
    sha = check_staged(staged, idx, pinned)

    print(f"Sprint {SPRINT}: {len(staged['records'])} records, summary {sha}, verifiedCount {staged['eas']['verifiedCount']}, "
          f"driftCount {staged['eas']['driftCount']}; {len(staged['new_protocols'])} new protocols "
          f"({len(staged['rpc_pinned']['entries'])} RPC-pinned); UID {uid}; tx {tx}"
          + ("  [PLACEHOLDER: preview only]" if placeholder(uid) or placeholder(tx) else ""))
    idx = stamp_index(staged, uid, tx)
    m = idx["summary_metrics"]
    if (m["sprints_completed"], m["records_indexed"], len(idx["onchain_anchoring"]["sprint_eas_attestations"]),
            sum(e.get("chain") == "base" for e in idx["entries"])) != (TARGET["sprints"], TARGET["records"], TARGET["eas_attestations"], TARGET["base_records"]):
        fail(f"unexpected index totals {m}", 1)
    publish_pinned(staged)
    merge_facts(staged)
    summary_lines(staged)
    add_tokens(staged)
    x_handles(core, staged)
    x_claims(core, staged)
    set_expect(staged)
    readme(staged, uid, tx)
    wire_bounties(staged)
    record_minted_before()
    mcp_counts(os.path.join(ROOT, "packages", "mcp-server"))
    stub_src, stubs = stub_cards(staged)
    os.remove(STAGED)
    if not os.listdir(os.path.dirname(STAGED)):
        os.rmdir(os.path.dirname(STAGED))
    return finish(core, node, a.skip_tests, (stub_src, stubs))


def finish(core, node, skip_tests, stubs):
    """Everything after the stamp; idempotent, so a re-run with the same --uid / --tx completes an interrupted apply."""
    build_once(0)                                     # scorecards.json for the X feed (new cards are still stubs here)
    x_feed_and_cards(core)
    if stubs:
        src = read(stubs[0], "rb")
        if any(read(p, "rb") == src for p in stubs[1]):
            fail("a new protocol's card is still a stub after build_x_cards", 1)
    build_twice()
    print(f"  basket counts: {basket_counts()}")
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
    run([sys.executable, "verify_site_v2.py"], ROOT, "verify_site_v2")
    sync_core(core)
    # the Worker's OpenAPI document embeds catalog-derived numbers (e.g. the lookup limit maximum): re-snapshot it from the synced
    # worker, rebuild (root /openapi.json copy) and re-verify
    run([sys.executable, "tools/sync_openapi.py", "--core", core], ROOT, "sync_openapi")
    build_twice()
    run([sys.executable, "tools/sync_openapi.py", "--check", "--core", core], ROOT, "sync_openapi --check")
    run([sys.executable, "verify_site_v2.py", "--manifest", "docs/api/v1/graph-manifest.json"], ROOT, "verify_site_v2 --manifest (after the OpenAPI re-snapshot)")
    if not skip_tests:
        tests(core, node)
    print(f"done: Sprint {SPRINT} stamped ({TARGET['records']} records, {TARGET['sprints']} sprints, {TARGET['protocols']} protocol pages = "
          f"{TARGET['eas_protocols']} EAS + {TARGET['rpc_protocols']} RPC, {TARGET['protocols']} badges). Review the diffs, then commit; nothing was pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
