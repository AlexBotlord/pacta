"""graph_manifest.py - compile docs/api/v1/graph-manifest.json (schema pacta.graph_manifest.v1).

The durable Pacta protocol graph that pacta-core/packages/analytics-sync/protocol_graph_sync.py reconciles into sn-memory
(owning principal pacta@dri.network/gemini). Inputs (all committed, no network, no wall clock):

  docs/api/v1/protocols.json     the published protocols (EAS-attested + RPC-pinned) and their surfaces
  docs/api/v1/index.json         Sprint records, onchain_anchoring (Base EAS UIDs and transactions), generated_at
  docs/api/v1/rpc-pinned.json    RPC-pinned records (surfaces of the rpc_observed protocols)
  tools/graph_dependencies.json  verified on-chain dependencies between indexed protocols (dual-RPC pinned reads)
  bounties/submissions/*.json    merged bounty fixtures (a control-plane gap each)

Anchor nodes (immutable text; changing facts live in edge evidence):
  pacta-proto-<slug>             one per published protocol
  pacta-ctrl-<chain>-<addr8>     one per distinct primary / controller / surface-target contract (addr8 = address[2:10])
  pacta-gap-<surface id>         one per parameter_delta surface (and per merged bounty gap)
  pacta-eas-sprint-<N>           one per Base EAS sprint attestation

Durable directed relations (the only four labels):
  governed_by_controller          pacta-proto-* -> pacta-ctrl-*
  exhibits_control_plane_gap      pacta-proto-* -> pacta-gap-*
  attested_by_base_eas            pacta-proto-* -> pacta-eas-sprint-*
  collateral_contagion_upstream   pacta-proto-<downstream> -> pacta-proto-<upstream>

Every edge: edge_key, relation, direction, participants, observed_at (epoch of index.json generated_at), evidence (canonical
JSON <= 4096 bytes; addresses / hashes as lowercase hex WITHOUT 0x, no credential-shaped keys) and content_hash =
sha256(canonical({relation, direction, participants, evidence})). Node text abbreviates every 0x value (0xABCD..1234).
Every node text and every relation payload passes the FN-Memory 30515c0a pre-write scrubber (tools/fn_memory_scrub.py).
"""
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sys
import urllib.parse
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fn_memory_scrub as SCRUB  # noqa: E402

SCHEMA = "pacta.graph_manifest.v1"
OWNING_PRINCIPAL = "pacta@dri.network/gemini"
SOURCE_AGENT = "pacta@dri.network"
PLACE = "pacta:protocol-graph"
RELATIONS = ("governed_by_controller", "exhibits_control_plane_gap", "attested_by_base_eas", "collateral_contagion_upstream")
ROLES = {"governed_by_controller": ("protocol", "controller"), "exhibits_control_plane_gap": ("protocol", "control_plane_gap"),
         "attested_by_base_eas": ("protocol", "eas_attestation"), "collateral_contagion_upstream": ("downstream_protocol", "upstream_protocol")}
NODE_KINDS = ("protocol", "controller", "control_plane_gap", "eas_attestation")
MAX_EVIDENCE_BYTES = 4096
MAX_TEXT_CHARS = 1400
CHAIN_LABEL = {"ethereum": "Ethereum", "base": "Base"}
CHAIN_ID = {"ethereum": 1, "base": 8453}
# evidence keys must never look like credential assignments to the FN-Memory scrubber
_BAD_KEY = re.compile(r"(?i)token|secret|key|password|passwd|pwd")
_HEX0X = re.compile(r"0x[0-9a-fA-F]{12,}")
_FULL0X = re.compile(r"0x[0-9a-fA-F]{40}")
_SPACE = re.compile(r"\s+")


def canonical(value):
    return SCRUB.canonical(value)


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def short(h):
    """0xABCD..1234 (12 chars) for prose; never a full 0x value."""
    return h[:6] + ".." + h[-4:] if isinstance(h, str) and h.startswith("0x") and len(h) > 12 else h


def hex0(h):
    """Full lowercase hex WITHOUT 0x (evidence only)."""
    assert isinstance(h, str) and re.fullmatch(r"0x[0-9a-fA-F]+", h), h
    return h[2:].lower()


def prose(s, limit=None):
    s = _HEX0X.sub(lambda m: short(m.group(0)), _SPACE.sub(" ", str(s or "")).strip())
    return s if limit is None or len(s) <= limit else s[:limit - 1].rstrip() + "…"


def epoch(iso):
    return float(dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())


def proto_id(slug):
    return f"pacta-proto-{slug}"


def ctrl_id(chain, addr):
    return f"pacta-ctrl-{chain}-{addr.lower()[2:10]}"


def gap_id(surface_id):
    return f"pacta-gap-{surface_id}"


def eas_id(n):
    return f"pacta-eas-sprint-{int(n)}"


def content_hash(edge):
    return sha256_hex(canonical({k: edge[k] for k in ("relation", "direction", "participants", "evidence")}))


def manifest_sha256(manifest):
    return sha256_hex(canonical({k: v for k, v in manifest.items() if k != "manifest_sha256"}))


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _sprint_tx(cov, n):
    """The Base transaction that carries sprint n's attestation (keys are '1–12', '13–16', '17', ...)."""
    for k, tx in cov.items():
        parts = [int(x) for x in re.split(r"[–-]", k)]
        if parts[0] <= n <= parts[-1]:
            return tx
    raise KeyError(f"no EAS transaction for sprint {n}")


def _check_evidence(ev, where):
    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)
    bad = [k for k in keys(ev) if _BAD_KEY.search(k)]
    assert not bad, f"{where}: credential-shaped evidence keys {bad}"
    blob = canonical(ev).decode()
    assert not _FULL0X.search(blob), f"{where}: 0x-prefixed 40/64-hex value in evidence"
    assert len(canonical(ev)) <= MAX_EVIDENCE_BYTES, f"{where}: evidence {len(canonical(ev))} bytes"


def build(root, controller_facts=None):
    """controller_facts: optional replacement for tools/graph_controller_facts.json (verify_site_v2 perturbs the mutable facts to
    prove pacta-ctrl-* node text never depends on them)."""
    docs = os.path.join(root, "docs", "api", "v1")
    prot = _load(os.path.join(docs, "protocols.json"))
    idx = _load(os.path.join(docs, "index.json"))
    pinned = _load(os.path.join(docs, "rpc-pinned.json"))
    deps = _load(os.path.join(root, "tools", "graph_dependencies.json"))
    cfacts_doc = controller_facts or _load(os.path.join(root, "tools", "graph_controller_facts.json"))
    cfacts, cfacts_pins = cfacts_doc["contracts"], cfacts_doc["pins"]
    subs = sorted(glob.glob(os.path.join(root, "bounties", "submissions", "*.json")))
    observed_at = epoch(idx["generated_at"])
    records = {e["id"]: e for e in idx["entries"]}
    pin_records = {e["id"]: e for e in pinned["entries"]}
    protocols = sorted(prot["protocols"], key=lambda p: p["slug"])
    slugs = [p["slug"] for p in protocols]
    assert len(slugs) == len(set(slugs)), "duplicate protocol slugs"
    by_slug = {p["slug"]: p for p in protocols}
    anc = idx["onchain_anchoring"]
    uids = {int(k): v for k, v in anc["sprint_eas_attestations"].items()}
    txs = anc["attestation_coverage"]["eas_multi_attest_txs"]
    nodes, edges = {}, {}
    name_to_slug = {p["name"]: p["slug"] for p in protocols}

    def protocol_slug_of(e):
        return e.get("slug") or name_to_slug.get(e.get("protocol"))

    def add_node(nid, kind, text):
        assert nid not in nodes, f"duplicate node {nid}"
        assert len(text) <= MAX_TEXT_CHARS, f"{nid}: text {len(text)} chars"
        nodes[nid] = {"id": nid, "kind": kind, "text": text}

    def add_edge(relation, src, tgt, evidence):
        sr, tr = ROLES[relation]
        key = f"{relation}:{src}->{tgt}"
        assert key not in edges, f"duplicate edge {key}"
        ev = {"edge_id": key, **evidence}
        _check_evidence(ev, key)
        e = {"edge_key": key, "relation": relation, "direction": "directed",
             "participants": [{"id": src, "role": sr, "side": "source"}, {"id": tgt, "role": tr, "side": "target"}],
             "observed_at": observed_at, "evidence": ev}
        e["content_hash"] = content_hash(e)
        edges[key] = e

    # ---- controllers: every distinct primary / controller / surface-target contract
    ctrl = {}                                    # (chain, addr) -> {"roles": set, "labels": set, "protocols": set, "surfaces": [...]}
    for p in protocols:
        ch = p["chain"]
        def touch(addr, role, label=None, surface=None, kind=None):
            c = ctrl.setdefault((ch, addr.lower()), {"addr": addr, "roles": set(), "labels": set(), "protocols": set(), "surfaces": [], "kinds": set()})
            c["roles"].add(role)
            c["protocols"].add(p["slug"])
            if label:
                c["labels"].add(label)
            if surface and surface not in c["surfaces"]:
                c["surfaces"].append(surface)
            if kind:
                c["kinds"].add(kind)
        touch(p["primaryContract"], "primary_contract", p.get("targetLabel"))
        if p.get("controllerAddress"):
            touch(p["controllerAddress"], "controller", None, None, p.get("controllerKind"))
        for s in p.get("surfaces") or []:
            if s.get("targetContract"):         # delta surfaces live in gap nodes; RPC-pinned surface strings are templated
                touch(s["targetContract"], "surface_target", s.get("targetLabel"),
                      None if s.get("classification") in ("parameter_delta", "rpc_observed") else s.get("surface"))
    addr8 = {}
    for (ch, a) in ctrl:
        nid = ctrl_id(ch, a)
        assert nid not in addr8, f"addr8 collision {nid}: {addr8.get(nid)} vs {a}"
        addr8[nid] = a
    role_text = {"primary_contract": "primary", "controller": "controller", "surface_target": "checked"}
    by_target, by_controller = {}, {}
    for e in list(idx["entries"]) + list(pinned["entries"]):
        by_target.setdefault((e.get("chain") or "ethereum", e["target_contract"].lower()), []).append(e)
        if e.get("controller_address"):
            by_controller.setdefault((e.get("chain") or "ethereum", e["controller_address"].lower()), []).append(e)

    def url_words(u):
        """host + path of a documentation URL (identity: where this contract is documented / governed)."""
        sp = urllib.parse.urlsplit(u or "")
        return (sp.netloc + sp.path.rstrip("/") + (" " + sp.fragment.strip("/") if sp.fragment else "")) if sp.netloc else None

    used_quotes = set()

    value_res = [r"\b\d+\s*(?:-|\s)\s*of\s*(?:-|\s)\s*\d+\b", r"\b\d+/\d+(?=\s+signers)",
                 r"\b\d+(?:\.\d+)?\s*-?\s*(?:s|secs?|seconds?|mins?|minutes?|h|hrs?|hours?|d|days?|wks?|weeks?)\b",
                 r"\b\d+(?:\.\d+)?\s*%", r"\s*=\s*\d+(?:\.\d+)?\b(?!\.)", r"\b\d+\s+(?=(?:advisory board )?(?:votes?|signers?|oracles?)\b)"]
    quote_res = [r"(?<![A-Za-z0-9])'(?:[^']|'(?=[A-Za-z]))*'(?![A-Za-z0-9])", r'"[^"]*"', "\u2018[^\u2019]*\u2019",
                 r"(?<![A-Za-z0-9])'[^']*$", r'"[^"]*$']

    def drop_values(t):
        """Identity only: strip mutable governance quantities (k-of-n, signer counts, delays, fee / threshold values) and
        quoted documentation passages (which restate them); the observed values live in governed_by_controller evidence."""
        for rx in quote_res:
            t = re.sub(rx, " ", t)
        for rx in value_res:
            t = re.sub(rx, " ", t, flags=re.I)
        t = re.sub(r"\s*=\s+of\b", " is a share of", t)
        t = re.sub(r"\s*=\s*(?=[.;,(]|$)", " ", t)
        t = re.sub(r"(?<![A-Za-z0-9_])\(\s*[,;]?\s*\)|\(\s+\)|\[\s*\]", " ", t)     # emptied parentheses, not getter "()"
        t = re.sub(r"(?:\s*(?:\band\b|[:;,]))+\s*(?=$|[;.)])", "", t)
        t = re.sub(r"\s+([,;:.)])", r"\1", re.sub(r"\(\s+", "(", t))
        return re.sub(r"\s{2,}", " ", t).strip(" ;:,-.")

    def named_in_records(ch, a, slugs):
        """How the attested records name a contract they do not target: the label written before its address and the getter
        that returned it (no observed values)."""
        out = []
        for e in idx["entries"]:
            if (e.get("chain") or "ethereum") != ch or protocol_slug_of(e) not in slugs or e["target_contract"].lower() == a:
                continue
            obs = str(e.get("onchain_observed") or "")
            for mm in re.finditer(r"(?:([A-Za-z]\w*(?:\.\w+)?\(\))\s*=\s*)?([A-Z][A-Za-z0-9_.-]*(?: [A-Z][A-Za-z0-9_.-]*){0,3})?\s*\(?0x" + a[2:10], obs, re.I):
                label = (mm.group(2) or "").strip()
                if label.lower().startswith("0x") or not (label or mm.group(1)):
                    continue
                out.append(f"{label or 'returned'}" + (f" via {mm.group(1)}" if mm.group(1) else "") + f" on {e.get('target_label') or 'target'}")
        return list(dict.fromkeys(out))[:3]

    sig_contracts = Counter(sig for sig, _ in {(e["call_signature"], ((e.get("chain") or "ethereum"), e["target_contract"].lower()))
                                               for es in by_target.values() for e in es if e.get("call_signature")})

    def identity_facts(ch, a, slugs):
        """Immutable identity only (M3): what was checked on this contract (record getters and the attested
        documentation quote of each non-delta record that targets it), how records name it, what it controls, and where it is
        documented / governed. Mutable observations (threshold, owners, delay, code) live in governed_by_controller evidence."""
        facts = []
        for e in sorted(by_target.get((ch, a), []), key=lambda e: e["id"]):
            if e.get("call_signature"):
                sel = str(e.get("selector_or_slot") or "")
                unique = sig_contracts.get(e["call_signature"]) == 1      # a shared getter's selector adds no identity
                facts.append(e["call_signature"] + (f" selector {sel[2:]}" if unique and re.fullmatch(r"0x[0-9a-fA-F]{8}", sel) else ""))
            ds = e.get("observed_delay_source") or {}
            if str(ds.get("contract") or "").lower() == a and ds.get("getter") and ds["getter"] != e.get("call_signature"):
                facts.append(f"also reads {ds['getter']}")
            if e.get("provenance") == "rpc_pinned":
                if url_words(e.get("docs_url")):
                    facts.append("documented at " + url_words(e["docs_url"]))
            elif e.get("classification") != "parameter_delta" and e.get("documented_reference"):    # delta quotes live in gap nodes
                q = prose(drop_values(e["documented_reference"]), 200)
                key = re.sub(r"[^a-z0-9]+", " ", e["documented_reference"].lower())[:80]
                if key not in used_quotes:            # one contract per attested quote
                    used_quotes.add(key)
                    if q:
                        facts.append("documented in " + q)
        for e in sorted(by_controller.get((ch, a), []), key=lambda e: e["id"]):
            if e["target_contract"].lower() == a:
                continue
            facts.append(drop_values(f"controls {e.get('target_label') or 'target'}"))
            if url_words(e.get("governance_url")):
                facts.append("governed via " + url_words(e["governance_url"]))
        if not by_target.get((ch, a)):
            facts += named_in_records(ch, a, slugs)
        return list(dict.fromkeys(facts))[:6]

    def observed_controller(ch, a):
        """Mutable pinned controller facts for governed_by_controller evidence (hex lowercase, no 0x; Safe nonce omitted:
        it is a transaction counter, not a control-plane fact)."""
        f = cfacts.get(f"{ch}:{a[2:]}")
        if not f:
            return None
        pin = cfacts_pins.get(ch) or {}
        out = {"facts_block_number": pin.get("block_number"), "code_bytes": f.get("code_bytes"), "code_keccak_hex": f.get("code_keccak_hex")}
        if f.get("safe_threshold"):
            owners = sorted(f.get("safe_owner_hex") or [])
            out.update(safe_threshold=f["safe_threshold"], safe_owners_count=f["safe_owners"], safe_version=f.get("safe_version"),
                       safe_owners_digest_hex=sha256_hex("".join(owners).encode()) if owners else None)
        if f.get("timelock_min_delay") is not None:
            out["timelock_delay_seconds"] = f["timelock_min_delay"]
        if f.get("owner_hex"):
            out["owner_hex"] = f["owner_hex"]
        return out

    for (ch, a), c in sorted(ctrl.items()):
        labels = sorted(c["labels"]) or sorted(f"{k.replace('_', ' ')}" for k in c["kinds"]) or ["contract"]
        facts = identity_facts(ch, a, c["protocols"])
        names = sorted(by_slug[x]["name"] for x in c["protocols"])
        label_words = set(re.findall(r"[a-z0-9]+", " ".join(labels).lower()))
        fact_words = set(re.findall(r"[a-z0-9]+", " ".join(facts).lower()))
        if not c["labels"] and not facts:         # controller-only without other identity: name it by its protocol slug
            where = f" in {', '.join(sorted(c['protocols']))}"
        elif not c["labels"]:                     # name the protocol unless the identity facts already do
            where = "" if any(w in fact_words for n in names for w in re.findall(r"[a-z]{4,}", n.lower())) else f" of {', '.join(names)}"
        elif (not any(w in label_words for n in names for w in re.findall(r"[a-z0-9]+", n.lower()))
              and any(e.get("classification") != "parameter_delta" for e in by_target.get((ch, a), []))):
            where = f" of {', '.join(names)}"     # the label does not say whose contract it is
        else:
            where = ""
        getter_words = set(re.findall(r"[a-z0-9]+", " ".join(re.findall(r"\w+\([^)]*\)", " ".join(facts))).lower()))
        surfaces = [prose(drop_values(x)) for x in c["surfaces"][:4]]
        surfaces = [x for x in surfaces       # a surface that, value-stripped, only restates its getter adds no identity
                    if len(set(re.findall(r"[a-z0-9]+", x.lower())) - getter_words) > 1]
        roles = "/".join(role_text[r] for r in sorted(c["roles"]))
        roles = "" if roles == "controller" and not c["labels"] else roles + " "    # a kind label already says "controller"
        text = (f"{'; '.join(labels)} {short(c['addr'])} [{CHAIN_ID[ch] if CHAIN_LABEL[ch].lower() in ' '.join(labels + names).lower() else CHAIN_LABEL[ch] + ' ' + str(CHAIN_ID[ch])}"
                f"{', ' + roles.strip() if roles.strip() else ''}{where}] "
                + ("; ".join(dict.fromkeys(x for x in surfaces + facts if x)) or "no direct read") + ".")
        add_node(ctrl_id(ch, a), "controller", prose(text, MAX_TEXT_CHARS))

    # ---- EAS sprint attestations
    sprint_protocols = {}
    for p in protocols:
        for n in p.get("sprints") or []:
            sprint_protocols.setdefault(int(n), []).append(p)
    for n in sorted(uids):
        recs = [e for e in idx["entries"] if e["sprint"] == n]
        assert recs, f"sprint {n} has no records"
        eth = next(e for e in recs if e.get("chain", "ethereum") == "ethereum") if any(e.get("chain", "ethereum") == "ethereum" for e in recs) else recs[0]
        cls = {}
        for e in recs:
            cls[e["classification"]] = cls.get(e["classification"], 0) + 1
        names = sorted({e["protocol"] for e in recs})
        assets = sorted({t for p in sprint_protocols.get(n, []) for t in p.get("tokens") or []})
        text = (f"Sprint {n} Base EAS attestation {short(uids[n])} in tx {short(_sprint_tx(txs, n))}: Ethereum block {eth['block_number']} "
                f"{short(eth['block_hash'])}, summary {short(recs[0]['summary_sha256'])}, {len(recs)} records "
                f"({', '.join(f'{v} {k.replace('_', ' ')}' for k, v in sorted(cls.items()))}) for {'; '.join(names)}"
                + (f" ({', '.join(assets)})" if assets else "") + ".")
        add_node(eas_id(n), "eas_attestation", prose(text, MAX_TEXT_CHARS))

    # ---- protocols
    for p in protocols:
        ch = p["chain"]
        surf = [s for s in p.get("surfaces") or []]
        basis = (f"EAS Sprint {', '.join(str(n) for n in p['sprints'])}" if p.get("easAttested") else "RPC-pinned")
        kind = (p.get("controllerKind") or "").replace("_", " ")
        ctrl_part = f"; controller {kind + ' ' if kind else ''}{short(p['controllerAddress'])}" if p.get("controllerAddress") else ""
        cat = re.sub(r"\s*\((?:Base|Ethereum)\)\s*$", "", p["category"])
        chain_part = f"chainId {p['chainId']}" if CHAIN_LABEL[ch].lower() in p["name"].lower() else f"{CHAIN_LABEL[ch]} chainId {p['chainId']}"
        cls = {}
        for s_ in surf:
            cls[s_["classification"]] = cls.get(s_["classification"], 0) + 1
        mix = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(cls.items()) if k != "rpc_observed")
        text = (f"{p['name']} [{p['slug']}]: {cat}; {chain_part}"
                + (f"; assets {', '.join(p.get('tokens') or [])}" if p.get("tokens") else "")
                + f"; primary {short(p['primaryContract'])}{ctrl_part}; {basis}; tier {p['badge']['tier']}"
                + (f" ({mix})" if mix else "") + ".")
        add_node(proto_id(p["slug"]), "protocol", prose(text, MAX_TEXT_CHARS))

    # ---- gaps: one per parameter_delta surface
    for p in protocols:
        for s in p.get("surfaces") or []:
            if s.get("classification") != "parameter_delta":
                continue
            r = records.get(s["id"]) or pin_records.get(s["id"]) or {}
            text = (f"Control-plane gap {s['id']}: {p['name']} — {prose(s.get('surface'))}. Observed: {prose(r.get('onchain_observed'), 520)} "
                    f"Documented: {prose(r.get('documented_reference'), 300)} Sprint {s.get('sprint')}, {CHAIN_LABEL[s.get('chain') or p['chain']]} "
                    f"block {s.get('blockNumber')}.")
            add_node(gap_id(s["id"]), "control_plane_gap", prose(text, MAX_TEXT_CHARS))
    for path in subs:                             # merged bounty fixtures: one gap each
        f = _load(path)
        sid = "bounty-slot-{}-{}".format(f.get("slot"), re.sub(r"[^a-z0-9-]+", "-", str(f.get("pactaSlug") or f.get("protocol") or "x").lower()).strip("-"))
        text = (f"Control-plane gap {sid}: bounty submission for {prose(f.get('protocol'))} at {short(str(f.get('contractAddress')))} "
                f"(chainId {f.get('chainId')}, block {f.get('blockNumber')}). Documented: {prose(f.get('docsQuote'), 300)}")
        add_node(gap_id(sid), "control_plane_gap", prose(text, MAX_TEXT_CHARS))

    # ---- edges
    for p in protocols:
        src, ch = proto_id(p["slug"]), p["chain"]
        addrs = {}
        def note(addr, role, s=None):
            a = addrs.setdefault(addr.lower(), {"roles": set(), "surface_ids": [], "labels": set()})
            a["roles"].add(role)
            if s is not None:
                a["surface_ids"].append(s["id"])
                if s.get("targetLabel"):
                    a["labels"].add(s["targetLabel"])
        note(p["primaryContract"], "primary_contract")
        if p.get("controllerAddress"):
            note(p["controllerAddress"], "controller")
        for s in p.get("surfaces") or []:
            if s.get("targetContract"):
                note(s["targetContract"], "surface_target", s)
        for a, info in sorted(addrs.items()):
            add_edge("governed_by_controller", src, ctrl_id(ch, a), {
                "protocol_slug": p["slug"], "chain": ch, "chain_id": p["chainId"], "contract_hex": a[2:],
                "address_roles": sorted(info["roles"]), "surface_ids": sorted(set(info["surface_ids"])),
                "target_labels": sorted(info["labels"]), "controller_kind": p.get("controllerKind") if "controller" in info["roles"] else None,
                "evidence_basis": p.get("evidenceBasis"), "badge_tier": p["badge"]["tier"],
                "observed_controller": observed_controller(ch, a)})
        for s in p.get("surfaces") or []:
            if s.get("classification") == "parameter_delta":
                r = records.get(s["id"]) or {}
                add_edge("exhibits_control_plane_gap", src, gap_id(s["id"]), {
                    "protocol_slug": p["slug"], "surface_id": s["id"], "classification": s["classification"], "sprint": s.get("sprint"),
                    "chain": s.get("chain") or ch, "target_contract_hex": hex0(s["targetContract"]), "block_number": s.get("blockNumber"),
                    "block_hash_hex": hex0(s["blockHash"]) if s.get("blockHash") else None, "surface": prose(s.get("surface"), 300),
                    "observed_delay_seconds": r.get("observed_delay_seconds"), "documented_delay_seconds": r.get("documented_delay_seconds"),
                    "summary_sha256_hex": hex0(r["summary_sha256"]) if r.get("summary_sha256") else None})
        for n in p.get("sprints") or []:
            recs = [e for e in idx["entries"] if e["sprint"] == n and e["protocol"] == p["name"]]
            add_edge("attested_by_base_eas", src, eas_id(n), {
                "protocol_slug": p["slug"], "sprint": int(n), "eas_uid_hex": hex0(uids[int(n)]), "eas_tx_hex": hex0(_sprint_tx(txs, int(n))),
                "summary_sha256_hex": hex0(recs[0]["summary_sha256"]) if recs else None,
                "record_ids": sorted(e["id"] for e in recs), "classifications": sorted({e["classification"] for e in recs}),
                "block_numbers": sorted({e["block_number"] for e in recs})})
    for path in subs:
        f = _load(path)
        slug = f.get("pactaSlug")
        sid = "bounty-slot-{}-{}".format(f.get("slot"), re.sub(r"[^a-z0-9-]+", "-", str(slug or f.get("protocol") or "x").lower()).strip("-"))
        if slug in by_slug:
            add_edge("exhibits_control_plane_gap", proto_id(slug), gap_id(sid), {
                "protocol_slug": slug, "surface_id": sid, "classification": "bounty_submission", "chain_id": f.get("chainId"),
                "target_contract_hex": hex0(f["contractAddress"]), "block_number": f.get("blockNumber"),
                "block_hash_hex": hex0(f["blockHash"]) if f.get("blockHash") else None, "bounty_slot": f.get("slot")})
    for d in deps["dependencies"]:
        assert d["downstream_slug"] in by_slug and d["upstream_slug"] in by_slug, d
        add_edge("collateral_contagion_upstream", proto_id(d["downstream_slug"]), proto_id(d["upstream_slug"]), {
            "downstream_slug": d["downstream_slug"], "upstream_slug": d["upstream_slug"], "dependency": d["dependency"],
            "summary": d["summary"], "reads": d["reads"]})

    for e in edges.values():                      # every endpoint exists
        for part in e["participants"]:
            assert part["id"] in nodes, f"{e['edge_key']}: missing node {part['id']}"
    node_list = [nodes[k] for k in sorted(nodes)]
    edge_list = [edges[k] for k in sorted(edges)]
    for n in node_list:                           # FN-Memory pre-write scrubber (memory_store text)
        assert not SCRUB.looks_like_secret(n["text"]), (n["id"], SCRUB.secret_span(n["text"]))
        assert not re.search(r"0x[0-9a-fA-F]{9,}", n["text"]), f"{n['id']}: unabbreviated 0x value in text"
    for e in edge_list:                           # ... and the relation payload
        raw = SCRUB.relation_payload_text(e["relation"], e["direction"], e["participants"], e["observed_at"], e["evidence"])
        assert not SCRUB.looks_like_secret(raw), (e["edge_key"], SCRUB.secret_span(raw))
    by_kind = {k: sum(1 for n in node_list if n["kind"] == k) for k in NODE_KINDS}
    by_rel = {r: sum(1 for e in edge_list if e["relation"] == r) for r in RELATIONS}
    src_sha = {name: sha256_hex(open(os.path.join(docs, name), "rb").read()) for name in ("protocols.json", "index.json", "rpc-pinned.json")}
    for name in ("graph_dependencies.json", "graph_controller_facts.json"):
        src_sha[name] = sha256_hex(open(os.path.join(root, "tools", name), "rb").read())
    manifest = {
        "schema": SCHEMA, "generated_at": idx["generated_at"], "observed_at": observed_at,
        "owning_principal": OWNING_PRINCIPAL, "source_agent": SOURCE_AGENT, "place": PLACE,
        "description": ("Durable Pacta protocol graph for sn-memory: immutable anchor nodes and four structural directed relation types, "
                        "reconciled by pacta-core analytics-sync protocol_graph_sync.py (writes held unless PACTA_GRAPH_WRITE_ENABLED=1). "
                        "Hex in evidence is lowercase without 0x; node text abbreviates 0x values."),
        "relation_types": list(RELATIONS),
        "sources": {"sha256": src_sha, "bounty_submissions": [os.path.relpath(p, root) for p in subs]},
        "protocols": [p["slug"] for p in protocols],
        "counts": {"protocols": len(protocols), "nodes": len(node_list), "nodes_by_kind": by_kind, "edges": len(edge_list),
                   "edges_by_relation": by_rel, "max_evidence_bytes": max(len(canonical(e["evidence"])) for e in edge_list),
                   "protocols_with_controller_edge": len({e["evidence"]["protocol_slug"] for e in edge_list if e["relation"] == "governed_by_controller"})},
        "nodes": node_list, "edges": edge_list,
    }
    assert manifest["counts"]["protocols_with_controller_edge"] == len(protocols)
    manifest["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


def render(manifest):
    return json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=False) + "\n"


def write(root, docs_dir=None):
    m = build(root)
    out = os.path.join(docs_dir or os.path.join(root, "docs"), "api", "v1", "graph-manifest.json")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render(m))
    return m


if __name__ == "__main__":
    m = write(os.path.dirname(HERE))
    print(json.dumps(m["counts"]), m["manifest_sha256"])
