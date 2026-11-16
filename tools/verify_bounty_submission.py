"""Deterministic, offline validator for Pacta Chain-Feed Mismatch Challenge submissions (https://pacta.wtf/bounties/).

  python3 tools/verify_bounty_submission.py --body PR_BODY.md      # a filled .github/PULL_REQUEST_TEMPLATE/bounty_mismatch.md
  python3 tools/verify_bounty_submission.py --json fixture.json    # the same fields as a JSON object (see FIELDS_JSON)
  python3 tools/verify_bounty_submission.py --json bounties/wave-2/<chain>-<slug>.json   # Wave 2 (100 x $1 USDC, FIELDS_WAVE2)
  python3 tools/verify_bounty_submission.py --self-test            # built-in valid / invalid fixtures (run by verify_site_v2.py)

Wave 2 is auto-detected: a fixture with "wave": 2, or any file under bounties/wave-2/. Wave 1 (Slots #1-#4) is unchanged.

Checks every required field of the 6 proof items (chainId + checksummed address + slot rules, finalized block number + 32-byte
hash, >= 2 cast commands pinned with --block <blockNumber> on >= 2 distinct RPC endpoints with identical outputs, an https://
documentation URL + verbatim quote, a JSON MCP output, the checked Apache-2.0 grant and the four rule boxes) plus secret / exploit
guards. It never touches the network: maintainers still re-run the dual-RPC archive replay at the pinned blockHash and confirm the
documentation URL answers HTTP 200 before a merge. Exit 0 = valid, 1 = problems (printed one per line).
"""

import argparse
import json
import math
import os
import re
import shlex
import sys
import urllib.parse

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
    return self_test_wave2(idx, verbose) and ok


# ================= Wave 2: 100 x $1 USDC rolling pool (bounties/wave-2/<chain>-<slug>.json) =================
WAVE2_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bounty_wave2.json")
W2 = json.load(open(WAVE2_CONFIG))
WAVE2_DIR = W2["fixtureDir"]                                            # "bounties/wave-2"
WAVE2_NAME_RE = re.compile(r"^(ethereum|base|arbitrum)-([a-z0-9]+(?:-[a-z0-9]+)*)\.json$")
WAVE2_CHAINS = {int(k): v for k, v in W2["chains"].items()}
assert WAVE2_CHAINS == CHAINS
HUNTER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")   # a valid GitHub user name (1-39 chars)
FRAMEWORK_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,39}$")
FIELDS_WAVE2 = ["wave", "category", "slug", "protocol", "chainId", "contractAddress", "vaultPlatform", "pactaSlug", "priorPin", "hunter",
                "agentFramework", "basePayoutAddress", "mcpProof", "blockNumber", "blockHash", "castCommands", "rpcOutputs", "docsUrl", "docsQuote",
                "tvlUsd", "tvlReference", "apache2CommercialGrant", "rulesAccepted"]
WAVE2_OPTIONAL = {"vaultPlatform", "pactaSlug", "priorPin", "agentFramework", "tvlUsd", "tvlReference"}
TREASURY = W2["settlement"]["treasuryAddress"]
MAX_TVL_USD = 1_000_000_000_000                 # $1T: anything above is a typo or an attack on the TVL floor
# real tool output keys: pacta_check_preflight {"schema": "pacta.preflight_check.v1", "chain", "address", "verdict", ...};
# pacta_scan_control_plane {"chain", "address", "block", "codeBytes", ...} (no schema key); or the tools/call envelope (content / structuredContent)
PREFLIGHT_KEYSETS = ({"schema", "verdict"}, {"schema", "chain", "address"}, {"chain", "address", "block"})
CAST_VALUE_OPTS = {"--block": "block", "-b": "block", "--rpc-url": "rpc", "-r": "rpc"}


def _reject_constant(c):
    raise ValueError(f"non-standard JSON constant {c} (NaN / Infinity are not allowed)")


def load_fixture(path):
    """json.load that refuses NaN / Infinity / -Infinity (they are not JSON and would slip past numeric floors)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh, parse_constant=_reject_constant)


def max_pinned_block(slug, docs=None):
    """Highest block Pacta has pinned for a published protocol, across protocols.json (surfaces), index.json (EAS records, by
    protocol name and surface id) and rpc-pinned.json (by slug). None when the slug is not published."""
    d = docs or os.path.join(ROOT, "docs", "api", "v1")
    prot = {x["slug"]: x for x in json.load(open(os.path.join(d, "protocols.json")))["protocols"]}
    if slug not in prot:
        return None
    p = prot[slug]
    ids = {s.get("id") for s in p.get("surfaces") or []}
    blocks = [s.get("blockNumber") for s in p.get("surfaces") or []]
    blocks += [e.get("block_number") for e in json.load(open(os.path.join(d, "index.json")))["entries"] if e.get("protocol") == p["name"] or e.get("id") in ids]
    blocks += [e.get("block_number") for e in json.load(open(os.path.join(d, "rpc-pinned.json")))["entries"] if e.get("slug") == slug or e.get("id") in ids]
    nums = [int(b) for b in blocks if isinstance(b, int) or (isinstance(b, str) and b.isdigit())]
    return max(nums) if nums else None


def parse_cast(cmd):
    """'cast call|storage <address> <positional...> --block N --rpc-url URL' -> (sub, address, positionals, block, rpc) or a problem string.
    Only --block / -b and --rpc-url / -r options are accepted (each exactly once), so every command is a pinned, comparable read."""
    try:
        toks = shlex.split(cmd)
    except ValueError as e:
        return f"unparseable ({e})"
    if len(toks) < 3 or toks[0] != "cast" or toks[1] not in ("call", "storage"):
        return "must start with 'cast call' or 'cast storage'"
    pos, opts, i = [], {}, 2
    while i < len(toks):
        t = toks[i]
        if t.startswith("-"):
            k, _, v = t.partition("=")
            if k not in CAST_VALUE_OPTS:
                return f"option {k} is not allowed (only --block and --rpc-url)"
            if not v:
                i += 1
                if i >= len(toks):
                    return f"option {k} needs a value"
                v = toks[i]
            if CAST_VALUE_OPTS[k] in opts:
                return f"option {k} given twice"
            opts[CAST_VALUE_OPTS[k]] = v
        else:
            pos.append(t)
        i += 1
    if not pos:
        return "missing the target address"
    return toks[1], pos[0], tuple(pos[1:]), opts.get("block"), opts.get("rpc")


def is_wave2(path, f):
    norm = os.path.normpath(path or "").replace(os.sep, "/")
    return (isinstance(f, dict) and f.get("wave") == 2) or os.path.dirname(norm).split("/")[-2:] == WAVE2_DIR.split("/")


def wave2_name_problems(path, f):
    """bounties/wave-2/<chain>-<slug>.json with <chain> = CHAINS[chainId] and <slug> = the fixture's slug."""
    norm = os.path.normpath(path).replace(os.sep, "/")
    m = WAVE2_NAME_RE.match(os.path.basename(norm))
    if not m or os.path.dirname(norm).split("/")[-2:] != WAVE2_DIR.split("/"):
        return [f"fixturePath: commit the fixture as {WAVE2_DIR}/<chain>-<slug>.json (<chain> = ethereum, base or arbitrum)"]
    probs = []
    try:
        chain = int(str(f.get("chainId")).strip())
    except (TypeError, ValueError):
        chain = None
    if CHAINS.get(chain) != m.group(1):
        probs.append(f"fixturePath: the file name says {m.group(1)} but chainId {f.get('chainId')} is {CHAINS.get(chain, 'unsupported')}")
    if f.get("slug") != m.group(2):
        probs.append(f"fixturePath: the file name slug {m.group(2)!r} must equal the fixture's slug {f.get('slug')!r}")
    return probs


def wave2_siblings(path):
    """Every other bounties/wave-2/*.json next to `path` (merged claims): [(chainId, lowercase address, slug)]."""
    d = os.path.dirname(os.path.abspath(path))
    me = os.path.realpath(path)
    out = []
    for p in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        q = os.path.join(d, p)
        if not p.endswith(".json") or os.path.realpath(q) == me:
            continue
        try:
            g = load_fixture(q)
            out.append((int(str(g.get("chainId")).strip()), str(g.get("contractAddress", "")).lower(), g.get("slug")))
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return out


def validate_wave2(f, idx=None, siblings=(), docs=None):
    """Wave 2 fixture -> list of problems (empty = valid). siblings: [(chainId, lowercase address, slug)] of the other merged claims."""
    probs = []
    bad = probs.append
    if not isinstance(f, dict):
        return ["fixture: a JSON object is required"]
    raw = json.dumps(f, sort_keys=True)
    addrs, slugs = idx or indexed()
    unknown = sorted(set(f) - set(FIELDS_WAVE2))
    if unknown:
        bad(f"fields: unknown keys {unknown} (allowed: {', '.join(FIELDS_WAVE2)})")
    if f.get("wave") != 2:
        bad("wave: must be 2")
    cat = f.get("category")
    if cat not in W2["categories"]:
        bad(f"category: one of {', '.join(W2['categories'])}")
    slug = f.get("slug")
    if not (isinstance(slug, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) and len(slug) <= 64):
        bad("slug: lowercase kebab-case target slug (a-z, 0-9, '-'; <= 64 chars)")
    if not _filled(f.get("protocol")):
        bad("protocol: name the protocol or curated vault")
    chain = f.get("chainId")
    chain = chain if isinstance(chain, int) and not isinstance(chain, bool) else None
    if chain not in CHAINS:
        bad("chainId: must be the integer 1 (Ethereum), 8453 (Base) or 42161 (Arbitrum One)")
    addr = f.get("contractAddress")
    if not checksummed(addr):
        bad("contractAddress: a mixed-case EIP-55 checksummed 0x address is required")
    elif int(addr, 16) <= 0xFFFF:
        bad("contractAddress: the zero address and precompiles (<= 0xffff) are not protocol contracts")
    elif addr.lower() == TREASURY.lower():
        bad("contractAddress: the Pacta treasury is not a bounty target")
    pay = f.get("basePayoutAddress")
    if not checksummed(pay):
        bad("basePayoutAddress: your mixed-case EIP-55 checksummed Base 0x address (USDC is paid there)")
    elif int(pay, 16) <= 0xFFFF:
        bad("basePayoutAddress: the zero address and precompiles (<= 0xffff) cannot receive the payout")
    elif isinstance(addr, str) and pay.lower() == addr.lower():
        bad("basePayoutAddress: must differ from contractAddress")
    elif pay.lower() == TREASURY.lower():
        bad("basePayoutAddress: must not be the Pacta treasury")
    hunter = f.get("hunter")
    if not (isinstance(hunter, str) and HUNTER_RE.fullmatch(hunter)):
        bad("hunter: your GitHub user name (1-39 letters, digits or inner hyphens)")
    fw = f.get("agentFramework")
    if fw is not None and not (isinstance(fw, str) and FRAMEWORK_RE.fullmatch(fw)):
        bad("agentFramework: optional lowercase id such as hermes, openclaw, claude-code, agno or human-researcher (a-z 0-9 . _ -, <= 40 chars)")
    psl = f.get("pactaSlug")
    if cat == "post_pin_drift":
        if psl not in slugs:
            bad("pactaSlug: post_pin_drift needs a published slug from https://pacta.wtf/api/v1/protocols.json")
        if not _filled(f.get("priorPin")):
            bad("priorPin: post_pin_drift needs the prior pinned Pacta block / tx")
        pinned = max_pinned_block(psl, docs) if psl in slugs else None
        bn_ = f.get("blockNumber")
        if pinned is not None and isinstance(bn_, int) and not isinstance(bn_, bool) and bn_ <= pinned:
            bad(f"blockNumber: post_pin_drift must be read after Pacta's latest pin for {psl} (block {pinned}); got {bn_}")
    elif cat in W2["categories"]:
        need = W2["categories"][cat]["minTvlUsd"]
        tvl = f.get("tvlUsd")
        if not (isinstance(tvl, (int, float)) and not isinstance(tvl, bool) and math.isfinite(tvl) and need <= tvl <= MAX_TVL_USD):
            bad(f"tvlUsd: {cat} needs a finite TVL between ${need:,} and ${MAX_TVL_USD:,} (a number in USD)")
        ref = f.get("tvlReference")
        if not (isinstance(ref, str) and re.match(r"^https://[^\s/@]+\.[^\s/@]+/\S*$", ref)):
            bad("tvlReference: an https:// link to a verifiable TVL source")
        if isinstance(slug, str) and slug in slugs:
            bad("duplicate: slug is already indexed by Pacta (use category post_pin_drift for live drift on an indexed protocol)")
        if checksummed(addr) and chain in CHAINS and f"{CHAINS[chain]}:{addr.lower()}" in addrs:
            bad("duplicate: contractAddress is already indexed by Pacta (use category post_pin_drift for live drift on an indexed protocol)")
    if cat == "curated_vault_mismatch" and f.get("vaultPlatform") not in W2["vaultPlatforms"]:
        bad(f"vaultPlatform: one of {', '.join(W2['vaultPlatforms'])}")
    if checksummed(addr) and chain in CHAINS and any(c == chain and a == addr.lower() for c, a, _ in siblings):
        bad("duplicate: another bounties/wave-2 claim already covers this (chainId, contractAddress)")
    if isinstance(slug, str) and any(s == slug for _, _, s in siblings):
        bad("duplicate: another bounties/wave-2 claim already uses this slug")
    mp = f.get("mcpProof")
    if not (isinstance(mp, dict) and mp.get("tool") in W2["mcpTools"] and isinstance(mp.get("arguments"), dict) and mp["arguments"]
            and isinstance(mp.get("result"), dict) and mp["result"]):
        bad("mcpProof: {\"tool\": pacta_lookup_protocol | pacta_check_preflight | pacta_scan_control_plane, \"arguments\": {non-empty}, \"result\": {non-empty}}")
    else:
        res = mp["result"]
        keys = set(res)
        envelope = isinstance(res.get("content"), list) or isinstance(res.get("structuredContent"), dict)
        if mp["tool"] == "pacta_lookup_protocol":
            shaped = envelope or bool(keys & {"schema", "results"})
        else:
            shaped = envelope or any(ks <= keys for ks in PREFLIGHT_KEYSETS)
        if not shaped:
            bad(f"mcpProof: result is not a {mp['tool']} output (raw tool JSON with its schema keys, or the tools/call content / structuredContent)")
        ser = json.dumps(res, sort_keys=True).lower()             # provenance from the RESULT only, never from arguments
        refs = [addr.lower()] if isinstance(addr, str) and addr else []
        if cat == "post_pin_drift" and isinstance(psl, str) and psl:
            refs.append(psl.lower())
        if not any(r in ser for r in refs):
            bad("mcpProof: the result must contain the contractAddress" + (" or the pactaSlug" if cat == "post_pin_drift" else "")
                + " (run pacta_check_preflight / pacta_scan_control_plane on the target; a lookup miss does not name the contract)")
    bn = f.get("blockNumber")
    bn = bn if isinstance(bn, int) and not isinstance(bn, bool) and 0 < bn < 10 ** 16 else None
    if bn is None:
        bad("blockNumber: a positive integer finalized block number")
    bh = f.get("blockHash")
    if not (isinstance(bh, str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", bh)) or (isinstance(bh, str) and int(bh, 16) == 0):
        bad("blockHash: the exact 32-byte 0x block hash")
    raw_cmds = f.get("castCommands")
    cmds = raw_cmds if isinstance(raw_cmds, list) and all(isinstance(c, str) for c in raw_cmds) else []
    parsed = [parse_cast(c) for c in cmds]
    errs = [f"#{i + 1}: {p}" for i, p in enumerate(parsed) if isinstance(p, str)]
    if len(cmds) < 2 or errs:
        bad("castCommands: at least 2 'cast call' / 'cast storage' commands (one per RPC endpoint)" + (f"; {'; '.join(errs)}" if errs else ""))
    else:
        if bn is not None and any(p[3] != str(bn) for p in parsed):
            bad("castCommands: every command must pin --block <blockNumber>")
        if checksummed(addr) and any(p[1].lower() != addr.lower() for p in parsed):
            bad("castCommands: every command must read contractAddress (the first positional argument)")
        if len({(p[0], p[2]) for p in parsed}) != 1:
            bad("castCommands: every command must be the same read (same call / storage and the same signature, arguments or slot)")
        hosts = []
        for p in parsed:
            u = urllib.parse.urlsplit(p[4] or "")
            hosts.append(u.hostname if u.scheme == "https" and u.hostname and "." in u.hostname else None)
        if None in hosts:
            bad("castCommands: every command needs --rpc-url https://<public host>")
        elif len(set(hosts)) < 2:
            bad("castCommands: 2 independent RPC endpoints (distinct --rpc-url hosts)")
    outs = f.get("rpcOutputs") if isinstance(f.get("rpcOutputs"), dict) else {}
    a, b = _filled(outs.get("a")), _filled(outs.get("b"))
    if not a or not b:
        bad("rpcOutputs: the raw output from both endpoints")
    elif str(a).strip() != str(b).strip():
        bad("rpcOutputs: the two endpoints must return identical outputs")
    url = f.get("docsUrl")
    if not (isinstance(url, str) and re.fullmatch(r"https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/\S*)?", url)) or re.search(r"https://(?:\d{1,3}\.){3}\d{1,3}", url or ""):
        bad("docsUrl: a direct https:// URL to the official documentation (public host name, answering HTTP 200)")
    q = f.get("docsQuote")
    if not (isinstance(q, str) and len(q.strip()) >= 10):
        bad("docsQuote: the verbatim documentation sentence (>= 10 characters)")
    if f.get("apache2CommercialGrant") is not True:
        bad("apache2CommercialGrant: must be true (Apache-2.0 contribution & commercialization grant)")
    ra = f.get("rulesAccepted")
    if not (isinstance(ra, list) and len(ra) == len(W2["rules"]) and all(r is True for r in ra)):
        bad("rulesAccepted: [true, true, true, true] (3 open PRs max, real RPC outputs, no third-party spam, no exploit PoC)")
    if any(r.search(raw) for r in SECRET_RES):
        bad("secrets: remove private keys, mnemonics, API tokens, JWTs and Bearer credentials")
    if any(r.search(raw) for r in EXPLOIT_RES):
        bad("exploit: no transaction-sending commands or exploit PoCs (route vulnerabilities via Immunefi / Cantina)")
    return probs


def valid_fixture_wave2(category="protocol_mismatch", first=None):
    """A complete, valid Wave 2 fixture (synthetic: an unindexed EIP-55 test-vector address, fake but well-formed block data)."""
    addr = "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359"             # EIP-55 test vector (mixed case), not indexed by Pacta
    pay = "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB"              # EIP-55 test vector
    f = {"wave": 2, "category": category, "slug": "example-lending", "protocol": "Example Lending", "chainId": 1, "contractAddress": addr,
         "hunter": "example-hunter", "agentFramework": "claude-code", "basePayoutAddress": pay,
         "mcpProof": {"tool": "pacta_lookup_protocol", "arguments": {"query": addr},
                      "result": {"schema": "pacta.protocol_lookup.v1", "query": addr, "totalMatches": 0, "count": 0, "results": [],
                                 "coverage_gap_hint": {"reason": "unindexed"}}},
         "blockNumber": 23800000, "blockHash": "0x" + "4e" * 32,
         "castCommands": [f'cast call {addr} "owner()(address)" --block 23800000 --rpc-url https://eth.example-rpc-a.org',
                          f'cast call {addr} "owner()(address)" --block 23800000 --rpc-url https://eth.example-rpc-b.org'],
         "rpcOutputs": {"a": "0x1234567890AbcdEF1234567890aBcdef12345678", "b": "0x1234567890AbcdEF1234567890aBcdef12345678"},
         "docsUrl": "https://docs.example-lending.org/governance", "docsQuote": "All upgrades go through a 48-hour timelock.",
         "tvlUsd": 12500000, "tvlReference": "https://defillama.com/protocol/example-lending", "apache2CommercialGrant": True, "rulesAccepted": [True] * 4}
    if category == "curated_vault_mismatch":
        f.update(slug="example-curated-vault", protocol="Example Curated Vault", vaultPlatform="morpho", tvlUsd=6000000, chainId=8453,
                 castCommands=[c.replace("eth.example", "base.example") for c in f["castCommands"]],
                 mcpProof={"tool": "pacta_check_preflight", "arguments": {"chain": "base", "address": addr},
                           "result": {"schema": "pacta.preflight_check.v1", "chain": "base", "chainId": 8453, "address": addr,
                                      "verdict": "INSTANT_EOA_ADMIN_RISK"}})
    if category == "post_pin_drift":
        first = first or {"slug": "example", "chain": "ethereum"}
        pin = max_pinned_block(first["slug"]) or 23700000
        bn = pin + 1000                                               # read strictly after Pacta's latest pin
        f.update(slug=first["slug"], protocol="Drifted protocol", pactaSlug=first["slug"], priorPin=f"Pacta pinned block {pin}", blockNumber=bn,
                 castCommands=[c.replace("--block 23800000", f"--block {bn}") for c in f["castCommands"]],
                 mcpProof={"tool": "pacta_scan_control_plane", "arguments": {"chain": "ethereum", "address": addr},
                           "result": {"chain": "ethereum", "address": addr, "block": {"number": bn}, "codeBytes": 4096}})
        f.pop("tvlUsd")
        f.pop("tvlReference")
    return f


def self_test_wave2(idx, verbose=False):
    """Wave 2: the 3 categories pass; each mutation fails with its expected problem; file name and duplicate guards."""
    ok = True
    first = next(x for x in json.load(open(PROTOCOLS))["protocols"] if x["chain"] == "ethereum")
    goods = {c: valid_fixture_wave2(c, first) for c in W2["categories"]}
    for c, g in goods.items():
        if validate_wave2(g, idx):
            ok = False
            print(f"self-test FAIL: wave 2 valid {c} fixture -> {validate_wave2(g, idx)}")
    good, vault, drift = goods["protocol_mismatch"], goods["curated_vault_mismatch"], goods["post_pin_drift"]
    tok = "gh" + "p_" + "B" * 20
    sib = [(1, good["contractAddress"].lower(), "other-target")]
    cases = [
        ("wave", good, {"wave": 1}), ("category", good, {"category": "rug"}), ("slug", good, {"slug": "Bad_Slug"}),
        ("chainId", good, {"chainId": "1"}), ("chainId", good, {"chainId": 137}),
        ("contractAddress", good, {"contractAddress": good["contractAddress"].lower()}),
        ("basePayoutAddress", good, {"basePayoutAddress": good["basePayoutAddress"].lower()}),
        ("basePayoutAddress", good, {"basePayoutAddress": "0x0000000000000000000000000000000000000000"}),
        ("basePayoutAddress", good, {"basePayoutAddress": good["contractAddress"]}), ("basePayoutAddress", good, {"basePayoutAddress": None}),
        ("hunter", good, {"hunter": "-bad-"}), ("hunter", good, {"hunter": "a" * 40}), ("hunter", good, {"hunter": "x/../y"}),
        ("agentFramework", good, {"agentFramework": "Claude Code"}), ("agentFramework", good, {"agentFramework": "<svg>"}),
        ("mcpProof", good, {"mcpProof": None}), ("mcpProof", good, {"mcpProof": {}}), ("mcpProof", good, {"mcpProof": {"tool": "other_tool", "result": {"a": 1}}}),
        ("mcpProof", good, {"mcpProof": {"tool": "pacta_lookup_protocol", "result": {"schema": "pacta.lookup.v1", "totalMatches": 0}}}),
        ("tvlUsd", good, {"tvlUsd": 9999999}), ("tvlUsd", good, {"tvlUsd": "12500000"}), ("tvlUsd", vault, {"tvlUsd": 4999999}),
        ("tvlReference", good, {"tvlReference": "http://defillama.com/x"}), ("vaultPlatform", vault, {"vaultPlatform": "beefy"}),
        ("pactaSlug", drift, {"pactaSlug": "not-a-slug"}), ("priorPin", drift, {"priorPin": None}),
        ("duplicate", good, {"slug": first["slug"]}),
        ("duplicate", good, {"contractAddress": first["primaryContract"],
                             "castCommands": [c.replace(good["contractAddress"], first["primaryContract"]) for c in good["castCommands"]]}),
        ("blockNumber", good, {"blockNumber": "23800000"}), ("blockHash", good, {"blockHash": "0x" + "00" * 32}),
        ("castCommands", good, {"castCommands": good["castCommands"][:1]}),
        ("castCommands", good, {"castCommands": [c.replace("--block 23800000", "--block latest") for c in good["castCommands"]]}),
        ("castCommands", good, {"castCommands": [c.replace("example-rpc-b", "example-rpc-a") for c in good["castCommands"]]}),
        ("rpcOutputs", good, {"rpcOutputs": {"a": "0x01", "b": "0x02"}}), ("docsUrl", good, {"docsUrl": "https://10.0.0.1/docs"}),
        ("docsQuote", good, {"docsQuote": "short"}), ("apache2CommercialGrant", good, {"apache2CommercialGrant": "yes"}),
        ("rulesAccepted", good, {"rulesAccepted": [True, True, True]}), ("fields", good, {"payoutNote": "x"}),
        ("secrets", good, {"docsQuote": "token " + tok + " in the docs"}),
        ("secrets", good, {"castCommands": [c + " --private-key 0xabc" for c in good["castCommands"]]}),
        ("exploit", good, {"docsQuote": "then cast send the drain tx to the vault"}),
        # adversarial review findings, one case each: contract guards, mcpProof arguments + result provenance, every cast reads the target, finite TVL
        ("contractAddress", good, {"contractAddress": "0x000000000000000000000000000000000000aB01",
                                   "castCommands": [c.replace(good["contractAddress"], "0x000000000000000000000000000000000000aB01") for c in good["castCommands"]]}),
        ("contractAddress", good, {"contractAddress": TREASURY, "castCommands": [c.replace(good["contractAddress"], TREASURY) for c in good["castCommands"]]}),
        ("basePayoutAddress", good, {"basePayoutAddress": TREASURY}),
        ("mcpProof", good, {"mcpProof": {**good["mcpProof"], "arguments": {}}}),
        ("mcpProof", good, {"mcpProof": {k: v for k, v in good["mcpProof"].items() if k != "arguments"}}),
        ("mcpProof", good, {"mcpProof": {**good["mcpProof"], "arguments": "query"}}),
        ("mcpProof", good, {"mcpProof": {"tool": "pacta_check_preflight", "arguments": {"address": good["contractAddress"]},
                                         "result": {"schema": "pacta.preflight_check.v1", "verdict": "IMMUTABLE_NO_ADMIN", "address": "0x" + "12" * 20}}}),
        ("mcpProof", good, {"mcpProof": {"tool": "pacta_lookup_protocol", "arguments": {"query": good["contractAddress"]},
                                         "result": {"schema": "pacta.protocol_lookup.v1", "query": "example lending", "totalMatches": 0}}}),
        ("mcpProof", good, {"mcpProof": {"tool": "pacta_check_preflight", "arguments": {"address": good["contractAddress"]},
                                         "result": {"note": good["contractAddress"]}}}),
        ("castCommands", good, {"castCommands": [good["castCommands"][0], good["castCommands"][1].replace(good["contractAddress"], good["basePayoutAddress"])]}),
        ("castCommands", good, {"castCommands": [good["castCommands"][0], good["castCommands"][1].replace('"owner()(address)"', '"admin()(address)"')]}),
        ("castCommands", good, {"castCommands": [good["castCommands"][0],
                                                 f'cast storage {good["contractAddress"]} 0x0 --block 23800000 --rpc-url https://eth.example-rpc-b.org']}),
        ("castCommands", good, {"castCommands": [c + " --private" for c in good["castCommands"]]}),
        ("castCommands", good, {"castCommands": [c.replace("https://", "http://") for c in good["castCommands"]]}),
        ("castCommands", good, {"castCommands": [good["castCommands"][0], good["castCommands"][1].replace("eth.example-rpc-b.org", "eth.example-rpc-a.org/v2")]}),
        ("castCommands", good, {"castCommands": [good["castCommands"][0] + ' "unterminated']}),
        ("tvlUsd", good, {"tvlUsd": float("inf")}), ("tvlUsd", good, {"tvlUsd": float("nan")}), ("tvlUsd", good, {"tvlUsd": -float("inf")}),
        ("tvlUsd", good, {"tvlUsd": 2_000_000_000_000}), ("tvlUsd", good, {"tvlUsd": True}),
        # net-new only: drift must be read strictly after Pacta's latest pin for the protocol
        ("blockNumber", drift, {"blockNumber": max_pinned_block(first["slug"]),
                                "castCommands": [c.replace(f"--block {drift['blockNumber']}", f"--block {max_pinned_block(first['slug'])}") for c in drift["castCommands"]]}),
        ("blockNumber", drift, {"blockNumber": max_pinned_block(first["slug"]) - 5,
                                "castCommands": [c.replace(f"--block {drift['blockNumber']}", f"--block {max_pinned_block(first['slug']) - 5}") for c in drift["castCommands"]]}),
    ]
    for want, base, patch in cases:
        probs = validate_wave2({**base, **patch}, idx)
        if not any(p.startswith(want + ":") for p in probs):
            ok = False
            print(f"self-test FAIL: wave 2 {patch} -> expected '{want}', got {probs}")
        elif verbose:
            print(f"self-test ok: wave 2 {want}")
    env_ok = {**good, "mcpProof": {"tool": "pacta_check_preflight", "arguments": {"chain": "ethereum", "address": good["contractAddress"]},
                                     "result": {"content": [{"type": "text", "text": json.dumps({"schema": "pacta.preflight_check.v1", "chain": "ethereum",
                                                                                                  "address": good["contractAddress"], "verdict": "TIMELOCK_PROTECTED"})}],
                                                "isError": False}}}
    if validate_wave2(env_ok, idx):
        ok = False
        print(f"self-test FAIL: wave 2 tools/call envelope proof refused -> {validate_wave2(env_ok, idx)}")
    for bad_json in ('{"tvlUsd": NaN}', '{"tvlUsd": Infinity}', '{"tvlUsd": -Infinity}'):
        try:
            json.loads(bad_json, parse_constant=_reject_constant)
            ok = False
            print(f"self-test FAIL: {bad_json} parsed")
        except ValueError:
            pass
    for want, sibs in (("duplicate", sib), ("duplicate", [(8453, "0x" + "1" * 40, good["slug"])])):
        if not any(p.startswith(want + ":") for p in validate_wave2(good, idx, sibs)):
            ok = False
            print(f"self-test FAIL: wave 2 sibling collision {sibs} not refused")
    if validate_wave2(good, idx, [(8453, good["contractAddress"].lower(), "other-target")]):   # same address on another chain is a distinct claim
        ok = False
        print("self-test FAIL: wave 2 same address on another chain refused")
    for path, f, want in (("bounties/wave-2/ethereum-example-lending.json", good, True), ("bounties/wave-2/base-example-lending.json", good, False),
                          ("bounties/wave-2/ethereum-other.json", good, False), ("bounties/wave-2/polygon-example-lending.json", good, False),
                          ("bounties/wave-2/Ethereum-Example.json", good, False), ("bounties/wave-3/ethereum-example-lending.json", good, False),
                          ("bounties/wave-2/../wave-2/x/ethereum-example-lending.json", good, False),
                          ("bounties/wave-2/base-example-curated-vault.json", vault, True), ("bounties/wave-2/ethereum-" + first["slug"] + ".json", drift, True)):
        if (not wave2_name_problems(path, f)) != want:
            ok = False
            print(f"self-test FAIL: wave 2 fixture path {path} expected {'ok' if want else 'refused'}")
    for path, f, want in (("bounties/wave-2/ethereum-x.json", {}, True), ("x.json", {"wave": 2}, True), ("bounties/submissions/slot-1-x.json", {"slot": 1}, False)):
        if is_wave2(path, f) != want:
            ok = False
            print(f"self-test FAIL: wave detection {path}")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--body", help="filled bounty_mismatch.md PR body")
    g.add_argument("--json", help="JSON fixture: Wave 1 fields " + ", ".join(FIELDS_JSON) + "; Wave 2 (bounties/wave-2/<chain>-<slug>.json) fields "
                   + ", ".join(FIELDS_WAVE2))
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        ok = self_test(verbose=False)
        print("self-test ok" if ok else "self-test FAILED")
        return 0 if ok else 1
    if a.body:
        f = parse_body(open(a.body).read())
    else:
        try:
            f = load_fixture(a.json)
        except ValueError as e:
            print(f"FAIL json: {e}")
            print("1 problem(s)")
            return 1
    if a.json and is_wave2(a.json, f):
        probs = validate_wave2(f, siblings=wave2_siblings(a.json)) + wave2_name_problems(a.json, f)
    else:
        probs = validate(f) + (fixture_name_problems(a.json, f) if a.json else [])
    for p in probs:
        print("FAIL " + p)
    print("valid submission (offline checks; maintainers re-run the dual-RPC replay and the HTTP 200 docs check)" if not probs else f"{len(probs)} problem(s)")
    return 0 if not probs else 1


if __name__ == "__main__":
    sys.exit(main())
