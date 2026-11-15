#!/usr/bin/env python3
"""apply_sprint17_attestation.py - stamp the Sprint 17 Base EAS attestation and publish the staged Sprint 17 records.

    python3 tools/apply_sprint17_attestation.py --uid 0x<32-byte UID> --tx 0x<32-byte tx hash> [--core ../pacta-core] [--skip-tests]

Input: tools/staged/sprint-17-records.json (6 records, audits/sprint-17/block-26418060-summary.md, Ethereum pin #26418060 plus
the Base pin #57635450 of the Steakhouse USDC record). The UID must be the attestation of that summary under schema
0x7ff4..df83 (chainId 1, block 26418060, verifiedCount 6, driftCount 0, summarySha256 = the staged SHA-256); this script does
not read the chain, so check the UID on base.easscan.org first.

It then, in one pass:
  pacta-github-repo  index.json (records + base_eas_uid, sprint_eas_attestations["17"], eas_multi_attest_txs["17"],
                     attested_not_yet_indexed_sprints [], summary_metrics, per-chain methodology), TOKENS for the 4 new
                     protocols, the verify_site_v2.py EXPECT block, README coverage / Sprint table, @pacta/mcp-server
                     PUBLISHED counts; rebuilds the site twice (byte-identical), removes the staged bundle, runs verify_site_v2.
  pacta-core         copies packages/mcp-server (src, test, README, SKILL.md), scripts/sync-lookup-catalog.py (worker
                     LOOKUP block + both protocol-slug allow-lists), agent-directory-prs, PUBLISHED / BADGE_TIERS /
                     SPRINT_PROTOCOL_SLUGS in the tests.
  tests              both repos' suites (unless --skip-tests). Nothing is committed, pushed or deployed.

Re-running with the same --uid / --tx is a no-op; a different UID or tx for an already stamped Sprint 17 is refused.
UIDs / tx hashes made of one repeated byte (e.g. 0x1717..17) are placeholders: they need --allow-placeholder (preview only).
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
SPRINT = 17
STAGED = os.path.join(HERE, "staged", f"sprint-{SPRINT}-records.json")
INDEX = os.path.join(ROOT, "docs", "api", "v1", "index.json")
HEX32 = re.compile(r"0x[0-9a-f]{64}")
# The published numbers after the stamp (Gemini's Sprint 17 spec: 58 protocol pages = 38 EAS + 20 RPC, 58 badges).
TARGET = {"sprints": 17, "records": 46, "eas_attestations": 17, "protocols": 58, "eas_protocols": 38, "rpc_protocols": 20, "briefs": 8,
          "badge_tiers": {"aligned": 21, "parameter_delta": 17, "rpc_observed": 20}, "base_records": 1}
NEW_TOKENS = {"falcon-finance-usdf-susdf": ["USDf", "sUSDf"], "m0-protocol-m": ["M", "M0", "MToken"],
              "solv-protocol-solvbtc": ["SolvBTC", "SOLV"], "steakhouse-usdc-metamorpho-base": ["steakUSDC", "Steakhouse", "MetaMorpho"]}
RPC_BY_CHAIN = {"ethereum": ["https://gateway.tenderly.co/public/mainnet", "https://rpc.mevblocker.io"],
                "base": ["https://mainnet.base.org", "https://base.drpc.org"]}


def fail(msg, code=2):
    print(f"apply_sprint17_attestation: {msg}", file=sys.stderr)
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


# ---------------------------------------------------------------- pacta-github-repo
def stamp_index(staged, uid, tx):
    idx = json.loads(read(INDEX))
    anc, cov = idx["onchain_anchoring"], idx["onchain_anchoring"]["attestation_coverage"]
    ids = {r["id"] for r in staged["records"]}
    for r in staged["records"]:
        if r["base_eas_uid"] is not None:
            fail(f"staged record {r['id']} already carries a UID")
    rs = [{**r, "base_eas_uid": uid} for r in staged["records"]]
    idx["entries"].extend(rs)
    if len({e["id"] for e in idx["entries"]}) != len(idx["entries"]) or not ids <= {e["id"] for e in idx["entries"]}:
        fail("record id collision")
    anc["sprint_eas_attestations"][str(SPRINT)] = uid
    anc["eas_multi_attest_sprint_17_tx"] = tx
    cov["base_eas_attested_sprints"] = f"1-{SPRINT}"
    cov["eas_multi_attest_txs"][str(SPRINT)] = tx
    cov["attested_not_yet_indexed_sprints"] = []
    meth = idx["methodology"]
    meth["archive_rpc_endpoints_by_chain"] = RPC_BY_CHAIN
    meth["record_chain"] = ("Records without a chain field are Ethereum Mainnet (chain id 1). Records with chain \"base\" (rpc_env_var $BASE_RPC_URL) "
                            "are pinned to a Base Mainnet block (chain id 8453) and replayed on mainnet.base.org + base.drpc.org; their Sprint's "
                            "EAS attestation commits to the Ethereum pin and to the summary SHA-256, which states the Base pin.")
    es = idx["entries"]
    cls = [e["classification"] for e in es]
    idx["summary_metrics"] = {"sprints_completed": max(e["sprint"] for e in es), "records_indexed": len(es),
                              "parameter_deltas": cls.count("parameter_delta"), "protective_deltas": cls.count("protective_delta"),
                              "aligned_baselines": cls.count("aligned_baseline")}
    idx["generated_at"] = max(idx["generated_at"], iso(staged["pins"]["ethereum"]["timestamp"]))
    write(INDEX, json.dumps(idx, indent=2, ensure_ascii=False) + "\n")
    return idx


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
        f'    "base_records": {x["base_records"]},                                                  # index.json records with chain "base" (Sprint 17 adds the first)\n'
        f'    "multi_attest_txs": {json.dumps(x["multi_attest_txs"], ensure_ascii=False)},                              # attestation_coverage.eas_multi_attest_txs keys\n'
        '    "summaries": {' + ",\n                  ".join(f'"{k}": "{v}"' for k, v in x["summaries"].items())
        + "},   # audits/sprint-<n>/ summary SHA-256 (attested)\n"
        "}\n")


def set_expect(staged):
    p = os.path.join(ROOT, "verify_site_v2.py")
    s = read(p)
    a, b = s.index("# ---- EXPECT-BEGIN"), s.index("# ---- EXPECT-END")
    head = s[a:s.index("\n", a) + 1]
    ns = {}
    exec(s[s.index("EXPECT = {", a):b], ns)                     # the current block (a literal dict)
    x = {**ns["EXPECT"], **TARGET}
    x["multi_attest_txs"] = ns["EXPECT"]["multi_attest_txs"] + [str(SPRINT)]
    x["summaries"] = {**ns["EXPECT"]["summaries"], str(SPRINT): staged["summary_sha256"][2:]}
    s = s[:a] + head + render_expect(x) + s[b:]
    # "kusd" now also substring-matches the new "steakUSDC" alias (ranked after the exact kUSD brief)
    s = sub_once(s, re.escape('"kusd": [["kerne-kusd-base", "exact"]],'),
                 '"kusd": [["kerne-kusd-base", "exact"], ["steakhouse-usdc-metamorpho-base", "substring"]],', "verifier kusd probe")
    write(p, s)


def readme(staged, uid, tx):
    p = os.path.join(ROOT, "README.md")
    s = read(p)
    idx = json.loads(read(INDEX))
    m = idx["summary_metrics"]
    t = TARGET
    cov = f'{t["protocols"]} Protocols ({t["records"]} Base EAS-Attested Records across {t["sprints"]} Sprints + {t["rpc_protocols"]} RPC-Observed Records)'
    s = sub_once(s, r"\d+ Protocols \(\d+ Base EAS-Attested Records across \d+ Sprints \+ \d+ RPC-Observed Records\)", cov, "README coverage line", count=2)
    s = sub_once(s, r"The \d+ Sprint records: \d+ parameter deltas · \d+ protective deltas · \d+ aligned baselines\.",
                 f'The {m["records_indexed"]} Sprint records: {m["parameter_deltas"]} parameter deltas · {m["protective_deltas"]} protective deltas · '
                 f'{m["aligned_baselines"]} aligned baselines.', "README breakdown")
    s = sub_once(s, r"Sprints 1–16 carry \*\*16 on-chain Base EAS sprint attestations\*\*: Sprints 1–12 in multi-attest tx (`0x[0-9a-f]{64}`) and "
                    r"Sprints 13–16 in multi-attest tx (`0x[0-9a-f]{64}`) \(Base block 57,032,413\)\.",
                 lambda mm: (f"Sprints 1–17 carry **17 on-chain Base EAS sprint attestations**: Sprints 1–12 in multi-attest tx {mm.group(1)}, "
                             f"Sprints 13–16 in multi-attest tx {mm.group(2)} (Base block 57,032,413) and Sprint 17 in tx `{tx}`."), "README attestations")
    e, b = staged["pins"]["ethereum"], staged["pins"]["base"]
    row16 = re.search(r"^\| \*\*Sprint 16\*\* \|.*\|\n", s, re.M)
    if not row16:
        fail("README: Sprint 16 row not found")
    row17 = (f'| **Sprint 17** | `{e["block_number"]}` (`{hex(e["block_number"])}`) · Base `{b["block_number"]}` | `{e["block_hash"]}` | '
             f'[`{uid[:6]}...{uid[-4:]}`](https://base.easscan.org/attestation/view/{uid}) | [`{staged["summary_doc"]}`]({staged["summary_doc"]}) — '
             f'M0 (`$M`), Falcon (`USDf`/`sUSDf`), Solv (`SolvBTC`), Steakhouse USDC MetaMorpho (Base) |\n')
    s = s[:row16.end()] + row17 + s[row16.end():]
    write(p, s)


def mcp_counts(pkg):
    t = TARGET
    p = os.path.join(pkg, "test", "lookup.test.mjs")
    write(p, sub_once(read(p), r"const PUBLISHED = Object\.freeze\(\{[^}]*\}\);",
                      f'const PUBLISHED = Object.freeze({{ protocols: {t["protocols"]}, briefs: {t["briefs"]}, easAttestedProtocols: {t["eas_protocols"]}, '
                      f'rpcObservedProtocols: {t["rpc_protocols"]} }});', "mcp-server PUBLISHED"))
    p = os.path.join(pkg, "README.md")
    write(p, sub_once(read(p), r"  - Scope: \d+ Base-EAS-attested protocols", f'  - Scope: {t["eas_protocols"]} Base-EAS-attested protocols', "mcp README scope"))


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
    eas_slugs = sorted(x["slug"] for x in lk["items"] if x["kind"] == "protocol" and x["easAttested"])
    p = os.path.join(core, "packages", "x402-edge-worker", "test", "worker.test.mjs")
    s = read(p)
    s = sub_once(s, r"const PUBLISHED = Object\.freeze\(\{[^}]*\}\);",
                 f'const PUBLISHED = Object.freeze({{ protocols: {t["protocols"]}, briefs: {t["briefs"]}, easAttestedProtocols: {t["eas_protocols"]}, '
                 f'rpcObservedProtocols: {t["rpc_protocols"]} }});', "worker PUBLISHED")
    s = sub_once(s, r"const BADGE_TIERS = Object\.freeze\(\{[^}]*\}\);",
                 "const BADGE_TIERS = Object.freeze({ " + ", ".join(f"{k}: {v}" for k, v in t["badge_tiers"].items()) + " });", "worker BADGE_TIERS")
    s = sub_once(s, r"const SPRINT_PROTOCOL_SLUGS = \[\n?(.*?)\];", lambda m: "const SPRINT_PROTOCOL_SLUGS = [\n" + render_list(eas_slugs) + "];",
                 "worker SPRINT_PROTOCOL_SLUGS", flags=re.S)
    write(p, s)
    p = os.path.join(core, "packages", "analytics-sync", "test_analytics_sync.py")
    write(p, sub_once(read(p), r'PUBLISHED = \{"protocols": \d+, "easAttestedProtocols": \d+, "rpcObservedProtocols": \d+\}',
                      f'PUBLISHED = {{"protocols": {t["protocols"]}, "easAttestedProtocols": {t["eas_protocols"]}, "rpcObservedProtocols": {t["rpc_protocols"]}}}',
                      "analytics PUBLISHED"))


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
    ap.add_argument("--uid", required=True, help="Base EAS attestation UID of the Sprint 17 summary (0x + 64 hex)")
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
    if uid == tx:
        fail("--uid and --tx must differ")
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
    sha = "0x" + hashlib.sha256(read(os.path.join(ROOT, staged["summary_doc"]), "rb")).hexdigest()
    cls = [r["classification"] for r in staged["records"]]
    if staged["sprint"] != SPRINT or staged["summary_sha256"] != sha or any(r["summary_sha256"] != sha for r in staged["records"]):
        fail(f"staged bundle does not match {staged['summary_doc']} (sha256 {sha})")
    if (staged["eas"]["verifiedCount"], staged["eas"]["driftCount"]) != (cls.count("aligned_baseline") + cls.count("protective_delta"), cls.count("parameter_delta")):
        fail("staged EAS counts do not match the record classifications")
    if sum(r["chain"] == "base" for r in staged["records"]) != TARGET["base_records"]:
        fail("staged Base record count differs from TARGET")

    print(f"Sprint {SPRINT}: {len(staged['records'])} records, summary {sha}, verifiedCount {staged['eas']['verifiedCount']}, "
          f"driftCount {staged['eas']['driftCount']}; UID {uid}; tx {tx}" + ("  [PLACEHOLDER: preview only]" if placeholder(uid) or placeholder(tx) else ""))
    idx = stamp_index(staged, uid, tx)
    m = idx["summary_metrics"]
    if (m["sprints_completed"], m["records_indexed"], len(idx["onchain_anchoring"]["sprint_eas_attestations"])) != (
            TARGET["sprints"], TARGET["records"], TARGET["eas_attestations"]):
        fail(f"unexpected index totals {m}", 1)
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
    lk = json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "lookup.json")))["totals"]
    pj = json.loads(read(os.path.join(ROOT, "docs", "api", "v1", "protocols.json")))["totals"]
    if (lk["protocols"], lk["easAttestedProtocols"], lk["rpcObservedProtocols"], pj["badgeTiers"]) != (
            TARGET["protocols"], TARGET["eas_protocols"], TARGET["rpc_protocols"], TARGET["badge_tiers"]):
        fail(f"catalog totals {lk} / badge tiers {pj['badgeTiers']} differ from TARGET {TARGET}", 1)
    if len([f for f in os.listdir(os.path.join(ROOT, "docs", "badges")) if f.endswith(".svg")]) != TARGET["protocols"]:
        fail("badge count differs from the protocol count", 1)
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
