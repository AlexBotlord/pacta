"""Deterministic, offline validator for Pacta Chain-Feed Mismatch Challenge submissions (https://pacta.wtf/bounties/).

  python3 tools/verify_bounty_submission.py --body PR_BODY.md      # a filled .github/PULL_REQUEST_TEMPLATE/bounty_mismatch.md
  python3 tools/verify_bounty_submission.py --json fixture.json    # the same fields as a JSON object (see FIELDS_JSON)
  python3 tools/verify_bounty_submission.py --self-test            # built-in valid / invalid fixtures (run by verify_site_v2.py)

Checks every required field of the 6 proof items (chainId + checksummed address + slot rules, finalized block number + 32-byte
hash, >= 2 cast commands pinned with --block <blockNumber> on >= 2 distinct RPC endpoints with identical outputs, an https://
documentation URL + verbatim quote, a JSON MCP output, the checked Apache-2.0 grant and the four rule boxes) plus secret / exploit
guards. It never touches the network: maintainers still re-run the dual-RPC archive replay at the pinned blockHash and confirm the
documentation URL answers HTTP 200 before a merge. Exit 0 = valid, 1 = problems (printed one per line).
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import BOUNTY_ISSUE_URLS  # noqa: E402  (single source of the #21-#24 issue numbers)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TEMPLATE = os.path.join(ROOT, ".github", "PULL_REQUEST_TEMPLATE", "bounty_mismatch.md")
PROTOCOLS = os.path.join(ROOT, "docs", "api", "v1", "protocols.json")
CHAINS = {1: "ethereum", 8453: "base", 42161: "arbitrum"}
SLOT_CHAINS = {1: {1}, 2: {1}, 3: {8453, 42161}, 4: {1, 8453, 42161}}
LABELS = {"Slot": "slot", "Issue": "issue", "chainId": "chainId", "Contract address": "contractAddress", "Protocol": "protocol",
          "TVL reference": "tvlReference", "Pacta slug": "pactaSlug", "blockNumber": "blockNumber", "blockHash": "blockHash",
          "Prior Pacta pin": "priorPin", "RPC A output": "rpcA", "RPC B output": "rpcB", "Docs URL": "docsUrl", "Verbatim quote": "docsQuote"}
GRANT = "I grant Pacta by Fractal Neurons perpetual, irrevocable rights under Apache-2.0 to ingest, Base EAS-attest, publish on pacta.wtf, and commercialize this merged mismatch record."
RULES = ["This is my only open bounty PR", "Every RPC output above is real", "I have not opened PRs, issues or comments in any third-party repository",
         "This PR contains no exploit PoC"]
FIXTURE_DIR = "bounties/submissions"
FIXTURE_NAME_RE = re.compile(r"^slot-([1-4])-([a-z0-9]+(?:-[a-z0-9]+)*)\.json$")


def fixture_name_problems(path, f):
    """The committed fixture must be bounties/submissions/slot-<slot>-<protocol-slug>.json, with <slot> = the fixture's slot."""
    norm = os.path.normpath(path).replace(os.sep, "/")
    m = FIXTURE_NAME_RE.match(os.path.basename(norm))
    if not m or os.path.dirname(norm).split("/")[-2:] != FIXTURE_DIR.split("/"):
        return [f"fixturePath: commit the fixture as {FIXTURE_DIR}/slot-<slot>-<protocol-slug>.json"]
    if str(f.get("slot")).strip().lstrip("#") != m.group(1):
        return [f"fixturePath: the file name says slot {m.group(1)} but the fixture says slot {f.get('slot')}"]
    return []


FIELDS_JSON = ["slot", "issue", "chainId", "contractAddress", "protocol", "tvlReference", "pactaSlug", "blockNumber", "blockHash", "priorPin",
               "castCommands", "rpcOutputs", "docsUrl", "docsQuote", "mcpOutput", "apacheGrant", "rules"]
SECRET_RES = [re.compile(x) for x in (r"sk-[A-Za-z0-9_-]{12,}", r"gh[pousr]_[A-Za-z0-9]{16,}", r"github_pat_[A-Za-z0-9_]{16,}", r"(?i)\bBearer\s+\S",
                                      r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"(?i)--private-key\b",
                                      r"(?i)--mnemonic\b", r"(?i)\bseed phrase\b")]
EXPLOIT_RES = [re.compile(x, re.I) for x in (r"\bcast send\b", r"\bforge script\b.*--broadcast", r"\bexploit (?:poc|contract|script)\b", r"\bdrain(?:ed|ing)? funds\b")]

# ---- keccak-256 (EIP-55), stdlib only ----
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
       0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
       0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
       0x000000000000800A, 0x800000008000000A, 0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_R = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M = (1 << 64) - 1


def keccak(data):
    msg = bytearray(data) + b"\x01"
    while len(msg) % 136:
        msg.append(0)
    msg[-1] |= 0x80
    a = [[0] * 5 for _ in range(5)]
    for off in range(0, len(msg), 136):
        for i in range(17):
            a[i % 5][i // 5] ^= int.from_bytes(msg[off + 8 * i:off + 8 * i + 8], "little")
        for rc in _RC:
            c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]
            d = [c[(x - 1) % 5] ^ (((c[(x + 1) % 5] << 1) | (c[(x + 1) % 5] >> 63)) & _M) for x in range(5)]
            a = [[a[x][y] ^ d[x] for y in range(5)] for x in range(5)]
            b = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    r = _R[x][y]
                    b[y][(2 * x + 3 * y) % 5] = ((a[x][y] << r) | (a[x][y] >> (64 - r))) & _M if r else a[x][y]
            a = [[b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
            a[0][0] ^= rc
    return b"".join(a[i % 5][i // 5].to_bytes(8, "little") for i in range(4))


def checksummed(addr):
    """True only for a mixed-case EIP-55 address (an all-lower / all-upper address is not 'checksummed')."""
    if not isinstance(addr, str) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", addr):
        return False
    body = addr[2:]
    if body in (body.lower(), body.upper()):
        return False
    h = keccak(body.lower().encode()).hex()
    return body == "".join(ch.upper() if ch.isalpha() and int(h[i], 16) >= 8 else ch.lower() for i, ch in enumerate(body.lower()))


def indexed(path=PROTOCOLS):
    """{"<chain>:<lowercase address>"} of every published contract, and the set of published slugs."""
    p = json.load(open(path))
    addrs, slugs = set(), set()
    for x in p["protocols"]:
        slugs.add(x["slug"])
        for a in [x.get("primaryContract"), x.get("controllerAddress")] + [s.get("targetContract") for s in x.get("surfaces") or []]:
            if isinstance(a, str):
                addrs.add(f'{x["chain"]}:{a.lower()}')
    return addrs, slugs


def _filled(v):
    v = (v or "").strip() if isinstance(v, str) else v
    return None if v in (None, "", "n/a", "N/A") or (isinstance(v, str) and v.startswith("<") and v.endswith(">")) else v


def parse_body(text):
    """A filled PR body (bounty_mismatch.md) -> the JSON field dict."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    f = {}
    for m in re.finditer(r"^- (" + "|".join(re.escape(k) for k in LABELS) + r"):[ \t]*(.*)$", text, re.M):
        f[LABELS[m.group(1)]] = _filled(m.group(2))
    blocks = re.findall(r"```(\w*)\n(.*?)```", text, re.S)
    cmds = [ln.strip() for lang, b in blocks if lang in ("bash", "sh", "shell", "") for ln in b.splitlines() if ln.strip().startswith("cast ")]
    f["castCommands"] = cmds
    js = [b for lang, b in blocks if lang == "json"]
    try:
        f["mcpOutput"] = json.loads(js[0]) if js else None
    except ValueError:
        f["mcpOutput"] = "invalid"
    f["rpcOutputs"] = {"a": f.pop("rpcA", None), "b": f.pop("rpcB", None)}
    box = lambda s: re.search(r"^- \[[xX]\] " + re.escape(s), text, re.M) is not None
    f["apacheGrant"] = box(GRANT)
    f["rules"] = [box(r) for r in RULES]
    f["_raw"] = text
    return f


def validate(f, idx=None):
    """-> list of problems (empty = valid)."""
    probs = []
    bad = probs.append
    raw = f.get("_raw") or json.dumps({k: v for k, v in f.items() if k != "_raw"})
    addrs, slugs = idx or indexed()
    try:
        slot = int(str(f.get("slot")).strip().lstrip("#"))
    except (TypeError, ValueError):
        slot = None
    if slot not in BOUNTY_ISSUE_URLS:
        bad("slot: must be 1, 2, 3 or 4")
    elif _filled(f.get("issue")) != BOUNTY_ISSUE_URLS[slot]:
        bad(f"issue: must be {BOUNTY_ISSUE_URLS[slot]} for slot {slot}")
    try:
        chain = int(str(f.get("chainId")).strip())
    except (TypeError, ValueError):
        chain = None
    if chain not in CHAINS:
        bad("chainId: must be 1 (Ethereum), 8453 (Base) or 42161 (Arbitrum One)")
    elif slot in SLOT_CHAINS and chain not in SLOT_CHAINS[slot]:
        bad(f"chainId: slot {slot} accepts {sorted(SLOT_CHAINS[slot])}")
    addr = _filled(f.get("contractAddress"))
    if not checksummed(addr):
        bad("contractAddress: a mixed-case EIP-55 checksummed 0x address is required")
    if not _filled(f.get("protocol")):
        bad("protocol: name the protocol or curated vault")
    slug = _filled(f.get("pactaSlug"))
    drift = slot == 4 and slug is not None
    if drift:
        if slug not in slugs:
            bad("pactaSlug: must be a published slug from https://pacta.wtf/api/v1/protocols.json")
        if not _filled(f.get("priorPin")):
            bad("priorPin: slot 4 drift needs the prior pinned Pacta block / tx")
    else:
        tvl = _filled(f.get("tvlReference"))
        if not (isinstance(tvl, str) and re.match(r"^https://[^\s/@]+\.[^\s/@]+/\S*$", tvl)):
            bad("tvlReference: an https:// link to a verifiable TVL source")
        if checksummed(addr) and chain in CHAINS and f"{CHAINS[chain]}:{addr.lower()}" in addrs:
            bad("contractAddress: already indexed by Pacta (unindexed slots need a protocol outside protocols.json; slot 4 drift needs pactaSlug)")
    bn = _filled(f.get("blockNumber"))
    bn = int(bn) if isinstance(bn, (str, int)) and re.fullmatch(r"[1-9][0-9]{0,15}", str(bn)) else None
    if bn is None:
        bad("blockNumber: a positive decimal block number")
    bh = _filled(f.get("blockHash"))
    if not (isinstance(bh, str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", bh)) or (isinstance(bh, str) and int(bh, 16) == 0):
        bad("blockHash: the exact 32-byte 0x block hash")
    cmds = [c for c in (f.get("castCommands") or []) if isinstance(c, str)]
    if len(cmds) < 2 or not all(re.match(r"^cast (?:call|storage) ", c) for c in cmds):
        bad("castCommands: at least 2 'cast call' / 'cast storage' commands (one per RPC endpoint)")
    if bn is not None and any(not re.search(rf"--block[ =]{bn}(?:\s|$)", c) for c in cmds):
        bad("castCommands: every command must pin --block <blockNumber>")
    rpcs = {m.group(1) for c in cmds for m in [re.search(r"--rpc-url[ =](\S+)", c)] if m}
    if len(rpcs) < 2:
        bad("castCommands: 2 independent RPC endpoints (distinct --rpc-url values)")
    if checksummed(addr) and not any(addr.lower() in c.lower() for c in cmds):
        bad("castCommands: at least one command must read the contract address")
    outs = f.get("rpcOutputs") or {}
    a, b = _filled(outs.get("a")), _filled(outs.get("b"))
    if not a or not b:
        bad("rpcOutputs: the raw output from both endpoints")
    elif str(a).strip() != str(b).strip():
        bad("rpcOutputs: the two endpoints must return identical outputs")
    url = _filled(f.get("docsUrl"))
    if not (isinstance(url, str) and re.fullmatch(r"https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/\S*)?", url)) or re.search(r"https://(?:\d{1,3}\.){3}\d{1,3}", url or ""):
        bad("docsUrl: a direct https:// URL to the official documentation (public host name)")
    q = _filled(f.get("docsQuote"))
    if not (isinstance(q, str) and len(q.strip()) >= 10):
        bad("docsQuote: the verbatim documentation sentence (>= 10 characters)")
    mo = f.get("mcpOutput")
    if not isinstance(mo, dict) or not (set(mo) & {"schema", "verdict", "results", "structuredContent", "result", "totalMatches"}):
        bad("mcpOutput: the JSON object returned by pacta_lookup_protocol / pacta_check_preflight / pacta_scan_control_plane")
    if f.get("apacheGrant") is not True:
        bad("apacheGrant: check the Apache-2.0 contribution & commercialization grant")
    rules = f.get("rules") or []
    if len(rules) != 4 or not all(r is True for r in rules):
        bad("rules: check all four rule boxes (1 open PR, real dual-RPC outputs, no third-party spam, no exploit PoC)")
    if any(r.search(raw) for r in SECRET_RES):
        bad("secrets: remove private keys, mnemonics, API tokens, JWTs and Bearer credentials")
    scan = re.sub(r"^- \[[ xX]\] .*$", "", raw, flags=re.M)        # the rule / grant checkbox text itself names "exploit PoC"
    if any(r.search(scan) for r in EXPLOIT_RES):
        bad("exploit: no transaction-sending commands or exploit PoCs (route vulnerabilities via Immunefi / Cantina)")
    return probs


def valid_fixture():
    """A complete, valid slot-1 submission (synthetic values: an unindexed address, fake but well-formed block data)."""
    addr = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"            # EIP-55 test vector (mixed case), not indexed by Pacta
    h = "0x" + "3f" * 32
    return {"slot": "1", "issue": BOUNTY_ISSUE_URLS[1], "chainId": "1", "contractAddress": addr, "protocol": "Example Vault",
            "tvlReference": "https://defillama.com/protocol/example-vault", "pactaSlug": None, "blockNumber": "23800000", "blockHash": h, "priorPin": None,
            "castCommands": [f'cast call {addr} "owner()(address)" --block 23800000 --rpc-url https://eth.example-rpc-a.org',
                             f'cast call {addr} "owner()(address)" --block 23800000 --rpc-url https://eth.example-rpc-b.org'],
            "rpcOutputs": {"a": "0x1234567890AbcdEF1234567890aBcdef12345678", "b": "0x1234567890AbcdEF1234567890aBcdef12345678"},
            "docsUrl": "https://docs.example-vault.org/governance", "docsQuote": "All upgrades go through a 48-hour timelock.",
            "mcpOutput": {"schema": "pacta.preflight_check.v1", "verdict": "INSTANT_EOA_ADMIN_RISK"}, "apacheGrant": True, "rules": [True] * 4}


def body_of(f):
    """Render a field dict as a filled bounty_mismatch.md body (used by the self-test)."""
    o = f["rpcOutputs"]
    return "\n".join([
        "## Bounty slot", f"- Slot: {f['slot']}", f"- Issue: {f['issue']}", "", "## 1. chainId & contract address",
        f"- chainId: {f['chainId']}", f"- Contract address: {f['contractAddress']}", f"- Protocol: {f['protocol']}",
        f"- TVL reference: {f['tvlReference'] or 'n/a'}", f"- Pacta slug: {f['pactaSlug'] or 'n/a'}", "", "## 2. Pinned finalized block",
        f"- blockNumber: {f['blockNumber']}", f"- blockHash: {f['blockHash']}", f"- Prior Pacta pin: {f['priorPin'] or 'n/a'}", "",
        "## 3. Deterministic dual-RPC cast proof", "```bash"] + f["castCommands"] + ["```", f"- RPC A output: {o['a']}", f"- RPC B output: {o['b']}", "",
        "## 4. Live official documentation claim (HTTP 200)", f"- Docs URL: {f['docsUrl']}", f"- Verbatim quote: {f['docsQuote']}", "",
        "## 5. Pacta MCP output", "```json", json.dumps(f["mcpOutput"]), "```", "", "## 6. Apache-2.0 contribution & commercialization grant",
        f"- [{'x' if f['apacheGrant'] else ' '}] {GRANT}", "", "## Rules"]
        + [f"- [{'x' if ok else ' '}] {r} (...)" for ok, r in zip(f["rules"], RULES)]) + "\n"


def self_test(verbose=False):
    """Valid fixture passes (JSON and PR body); each mutation fails with its expected problem; the empty template fails."""
    ok = True
    idx = indexed()
    good = valid_fixture()
    for name, probs in (("json", validate(dict(good), idx)), ("body", validate(parse_body(body_of(good)), idx))):
        if probs:
            ok = False
            print(f"self-test FAIL: valid fixture ({name}) -> {probs}")
    tok = "gh" + "p_" + "A" * 20
    first = next(x for x in json.load(open(PROTOCOLS))["protocols"] if x["chain"] == "ethereum")   # the fixtures use chainId 1
    cases = [
        ("slot", {"slot": "5"}), ("issue", {"issue": "https://github.com/Fractal-Neurons/pacta/issues/99"}), ("chainId", {"chainId": "137"}),
        ("chainId", {"chainId": "8453"}), ("contractAddress", {"contractAddress": good["contractAddress"].lower()}),
        ("contractAddress", {"contractAddress": "0x5AAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"}),
        ("contractAddress", {"contractAddress": first["primaryContract"], "castCommands": [c.replace(good["contractAddress"], first["primaryContract"]) for c in good["castCommands"]]}),
        ("tvlReference", {"tvlReference": "http://defillama.com/x"}), ("blockNumber", {"blockNumber": "latest"}),
        ("blockHash", {"blockHash": "0x1234"}), ("blockHash", {"blockHash": "0x" + "00" * 32}),
        ("castCommands", {"castCommands": good["castCommands"][:1]}),
        ("castCommands", {"castCommands": [c.replace("--block 23800000", "--block latest") for c in good["castCommands"]]}),
        ("castCommands", {"castCommands": [c.replace("example-rpc-b", "example-rpc-a") for c in good["castCommands"]]}),
        ("rpcOutputs", {"rpcOutputs": {"a": "0x01", "b": "0x02"}}), ("rpcOutputs", {"rpcOutputs": {"a": "0x01", "b": None}}),
        ("docsUrl", {"docsUrl": "http://docs.example.org/x"}), ("docsUrl", {"docsUrl": "https://10.0.0.1/docs"}), ("docsQuote", {"docsQuote": "short"}),
        ("mcpOutput", {"mcpOutput": "invalid"}), ("mcpOutput", {"mcpOutput": {"foo": 1}}), ("apacheGrant", {"apacheGrant": False}),
        ("rules", {"rules": [True, True, True, False]}), ("secrets", {"docsQuote": "token " + tok + " in the docs"}),
        ("secrets", {"castCommands": [c + " --private-key 0xabc" for c in good["castCommands"]]}),
        ("exploit", {"docsQuote": "then cast send the drain tx to the vault"}),
        ("pactaSlug", {"slot": "4", "issue": BOUNTY_ISSUE_URLS[4], "pactaSlug": "not-a-slug", "priorPin": "block 1"}),
        ("priorPin", {"slot": "4", "issue": BOUNTY_ISSUE_URLS[4], "pactaSlug": first["slug"], "priorPin": None}),
    ]
    for want, patch in cases:
        f = {**good, **patch}
        for name, probs in (("json", validate(f, idx)), ("body", validate(parse_body(body_of(f)), idx))):
            if not any(p.startswith(want + ":") for p in probs):
                ok = False
                print(f"self-test FAIL: {name} {patch} -> expected '{want}', got {probs}")
            elif verbose:
                print(f"self-test ok: {name} {want}")
    drift = {**good, "slot": "4", "issue": BOUNTY_ISSUE_URLS[4], "pactaSlug": first["slug"], "priorPin": "Pacta pinned block 23800000",
             "contractAddress": good["contractAddress"]}
    if validate(drift, idx):
        ok = False
        print(f"self-test FAIL: slot-4 drift fixture -> {validate(drift, idx)}")
    for path, slot, want in (("bounties/submissions/slot-1-example-vault.json", "1", True), ("slot-1-example-vault.json", "1", False),
                             ("bounties/submissions/slot-2-example-vault.json", "1", False), ("bounties/submissions/Slot-1-X.json", "1", False),
                             ("bounties/submissions/slot-5-x.json", "5", False), ("other/submissions/slot-1-x.json", "1", False)):
        if (not fixture_name_problems(path, {"slot": slot})) != want:
            ok = False
            print(f"self-test FAIL: fixture path {path} (slot {slot}) expected {'ok' if want else 'refused'}")
    tpl = validate(parse_body(open(TEMPLATE).read()), idx)
    if len(tpl) < 10:
        ok = False
        print(f"self-test FAIL: the empty PR template must fail on most fields, got {tpl}")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--body", help="filled bounty_mismatch.md PR body")
    g.add_argument("--json", help="JSON fixture with the fields " + ", ".join(FIELDS_JSON))
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        ok = self_test(verbose=False)
        print("self-test ok" if ok else "self-test FAILED")
        return 0 if ok else 1
    f = parse_body(open(a.body).read()) if a.body else json.load(open(a.json))
    probs = validate(f) + (fixture_name_problems(a.json, f) if a.json else [])
    for p in probs:
        print("FAIL " + p)
    print("valid submission (offline checks; maintainers re-run the dual-RPC replay and the HTTP 200 docs check)" if not probs else f"{len(probs)} problem(s)")
    return 0 if not probs else 1


if __name__ == "__main__":
    sys.exit(main())
