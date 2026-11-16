"""build_lookup.py - the deterministic protocol / token lookup catalog (task-14e685be73f9).

One item per published record page: every /protocols/<slug>/ page (index.json Sprint protocols, Base-EAS-attested, plus
rpc-pinned.json Wave-2 protocols, RPC-observed only) and every /briefs/<slug>/ page (onboarding.json + radar.json).
Every value is read from docs/api/v1/{index,rpc-pinned,onboarding,radar}.json; only the token / product aliases (TOKENS)
are curated here, and a protocol without aliases fails the build.

Writes:
  docs/api/v1/lookup.json                       the catalog (schema pacta.protocol_lookup_catalog.v1)
  packages/mcp-server/src/lookup.mjs            the same items, between the CATALOG-BEGIN / CATALOG-END markers
pacta-core keeps packages/mcp-server/src/lookup.mjs byte-identical and embeds its LOOKUP block verbatim in
packages/x402-edge-worker/worker.mjs (scripts/sync-lookup-catalog.py), so the hosted gateway answers lookups in memory.

Scoped truthfulness: index.json protocols are evidenceBasis "eas_attested" (on-chain compared with the documentation,
Base EAS UIDs); rpc-pinned protocols are evidenceBasis "rpc_observed" with documentationComparison "not_assessed" and
are never labelled aligned or parameter_delta; briefs are block-pinned verification briefs.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from onboarding_scan import eip55  # noqa: E402  (pure keccak / EIP-55 helper; importing never touches the network)

BASE = "https://pacta.wtf"
CATALOG_SCHEMA = "pacta.protocol_lookup_catalog.v1"
CHAIN_IDS = {"ethereum": 1, "base": 8453}
ONB_CHAIN = {"eth": "ethereum", "base": "base"}
SOURCES = ["/api/v1/index.json", "/api/v1/rpc-pinned.json", "/api/v1/onboarding.json", "/api/v1/radar.json"]
# Searchable token / product symbols and aliases per record page (curated; everything else comes from the feeds).
TOKENS = {
    "aave-v3-gho": ["GHO", "AAVE"], "across-protocol-hubpool": ["ACX"], "aerodrome-finance-base": ["AERO", "veAERO"],
    "balancer-v2-vault-timelock": ["BAL", "veBAL"], "bedrock-unieth": ["uniETH"], "beefy-finance-base": ["BIFI"],
    "centrifuge-liquidity-pools-base": ["CFG"], "compound-v3-comet": ["COMP", "cUSDCv3", "Comet"], "convex-finance": ["CVX", "cvxCRV"],
    "curve-finance-crvusd": ["crvUSD", "CRV"], "eigenlayer-core": ["EIGEN"], "ethena-usde-susde": ["USDe", "sUSDe", "ENA"],
    "ether-fi-core-eeth-weeth": ["eETH", "weETH", "ETHFI"], "ether-fi-liquid-veda-boringvault": ["Liquid", "Veda", "BoringVault"],
    "euler-v2-evk": ["EUL", "EVK", "EVC"], "extra-finance-base": ["EXTRA"], "f-x-protocol-v2": ["fxUSD", "FXN"],
    "fluid-instadapp": ["FLUID", "INST"], "frax-ether-sfrxeth": ["frxETH", "sfrxETH", "FXS"], "gearbox-v3-v3-1": ["GEAR"],
    "inverse-finance-firm": ["DOLA", "INV", "FiRM"], "kelp-dao-rseth": ["rsETH"], "lido-steth-dual-governance": ["stETH", "wstETH", "LDO"],
    "liquity-v2-bold": ["BOLD", "LQTY"], "lombard-lbtc": ["LBTC"], "mantle-liquid-staking-meth-cmeth": ["mETH", "cmETH"],
    "maple-finance-v2-syrup": ["SYRUP", "syrupUSDC", "syrupUSDT"], "mellow-protocol-lido-earn": ["Mellow", "Lido Earn"],
    "metamorpho-re7-weth-vs-re7-usdt": ["Re7WETH", "Re7USDT", "MetaMorpho"], "moonwell-lending-base": ["WELL"], "morpho-blue-core": ["MORPHO"],
    "ondo-finance-ousg-flux-finance": ["OUSG", "ONDO", "Flux"], "origin-superoeth-base": ["superOETHb", "OETH", "OGN"],
    "pendle-finance-v2": ["PENDLE", "vePENDLE"], "puffer-finance-pufeth": ["pufETH", "PUFFER"], "renzo-protocol-ezeth": ["ezETH", "REZ"],
    "reserve-protocol-rtoken": ["eUSD", "RSR"], "resolv-usr-rlp": ["USR", "RLP", "wstUSR", "RESOLV"], "rocket-pool-reth": ["rETH", "RPL"],
    "safe-singleton-core": ["SAFE"], "seamless-protocol-base": ["SEAM"], "spark-sky": ["USDS", "sUSDS", "DAI", "SKY", "MKR", "SPK"],
    "stader-labs-ethx": ["ETHx", "SD"], "stakewise-v3-oseth": ["osETH", "SWISE"], "superform-v2-base": ["Superform", "SuperVaults"],
    "superstate-ustb-uscc": ["USTB", "USCC"], "swell-sweth-rsweth": ["swETH", "rswETH", "SWELL"], "symbiotic-core": ["Symbiotic"],
    "synthetix-v3-core": ["SNX", "sUSD"], "threshold-network-tbtc": ["tBTC", "T"], "treehouse-tree-teth": ["tETH", "TREE"],
    "uniswap-governance-timelock": ["UNI"],
    "usual-money-usd0-usd0": ["USD0", "USD0++", "USUAL"], "yearn-v3": ["YFI"],
    "falcon-finance-usdf-susdf": ["USDf", "sUSDf"], "m0-protocol-m": ["M", "M0", "MToken"], "solv-protocol-solvbtc": ["SolvBTC", "SOLV"], "steakhouse-usdc-metamorpho-base": ["steakUSDC", "Steakhouse", "MetaMorpho"],
    "nexus-mutual": ["NXM", "wNXM", "Nexus Mutual"], "enzyme-finance": ["MLN", "Enzyme"], "stargate-v2": ["STG", "Stargate"], "aerodrome-slipstream-base": ["AERO", "Slipstream"],
    "aave-v3-base": ["AAVE", "Aave Base"], "compound-v3-base": ["COMP", "cUSDCv3"], "liquid-collective-lseth": ["LsETH", "Liquid Collective"], "ethena-usdtb": ["USDtb", "USDTB"],
    "concrete": ["ctDeltaWeETH", "Concrete"], "cap": ["cUSD", "stcUSD", "CAP"], "infinifi": ["iUSD", "siUSD", "liUSD"], "stake-link": ["stLINK", "SDL"],
    # briefs
    "kerne-kusd-base": ["kUSD", "Kerne"], "efix-efixdi-base": ["efixDI+", "EFIXDI", "EFIX"], "circle-cirbtc-eth": ["cirBTC", "Circle"],
    "paxos-paxgy-eth": ["PAXGy", "Paxos"], "tether-usat-eth": ["USAT", "Tether"], "ethena-ops-0x0ca0-0x1fe5": ["USDe", "RLUSD", "USAT"],
    "etherfi-op-0x244e": ["eETH", "weETH"], "treehouse-op-0x2f11": ["TREE", "tETH"],
}


def _addr(a):
    """Checksummed address; the feeds already publish EIP-55 forms, so any mismatch is a data error."""
    if a is None:
        return None
    c = eip55(a)
    assert a.lower() == c.lower() and a in (c, a.lower()), f"malformed or mis-checksummed address in feed: {a}"
    return c


# RPC-pinned protocols converted in place to EAS-attested keep the primary contract, its label and the controller their
# RPC-pinned page published (values copied from that record), so the protocol page, the lookup preflight and the durable graph
# (pacta-proto-* anchor, its pacta-ctrl-* nodes and governed_by_controller edges) never lose an anchor on conversion.
CONVERTED_CONTINUITY = {
    "frax-ether-sfrxeth": {"primaryContract": "0xbAFA44EFE7901E04E39Dad13167D089C559c1138", "targetLabel": "frxETHMinter",
                           "controllerAddress": "0x8306300ffd616049FD7e4b0354a64Da835c1A81C", "controllerKind": "multisig_safe"},
    "puffer-finance-pufeth": {"primaryContract": "0xD9A442856C234a39a81a089C06451EBAa4306a72", "targetLabel": "PufferVault (pufETH)",
                              "controllerAddress": "0x8c1686069474410E6243425f4a10177a94EBEE11", "controllerKind": "contract_controller"},
}


def _protocol_item(name, v):
    es, first = v["entries"], v["entries"][0]
    pinned = v["pinned"]
    chain = first.get("chain", "ethereum")
    classes = sorted({e["classification"] for e in es})
    if pinned:
        assert classes == ["rpc_observed"], (name, classes)
        ctrl, ctrl_kind = _addr(first.get("controller_address")), first.get("controller_kind")
        basis = {"classification": "rpc_observed", "evidenceBasis": "rpc_observed", "easAttested": False, "baseEasUids": [],
                 "documentationComparison": "not_assessed"}
    else:
        src = first.get("observed_delay_source") or {}
        ctrl = _addr(src.get("contract")) if src.get("contract") else None
        ctrl_kind = "timelock" if ctrl else None
        uids = sorted({e["base_eas_uid"] for e in es})
        assert all(u and u.startswith("0x") and len(u) == 66 for u in uids), name
        assert "rpc_observed" not in classes, name
        basis = {"classification": classes[0] if len(classes) == 1 else "mixed", "evidenceBasis": "eas_attested", "easAttested": True,
                 "baseEasUids": uids, "documentationComparison": "compared", "sprints": sorted({int(e["sprint"]) for e in es})}
    primary, label = _addr(first["target_contract"]), first["target_label"]
    keep = CONVERTED_CONTINUITY.get(v["slug"]) if not pinned else None
    if keep:
        primary, label, ctrl, ctrl_kind = (_addr(keep["primaryContract"]), keep["targetLabel"], _addr(keep["controllerAddress"]),
                                           keep["controllerKind"])
    return {"kind": "protocol", "slug": v["slug"], "name": name, "tokens": TOKENS[v["slug"]], "category": first["category"],
            "chain": chain, "chainId": CHAIN_IDS[chain], "primaryContract": primary, "targetLabel": label,
            "controllerAddress": ctrl, "controllerKind": ctrl_kind,
            "observedDelaySeconds": first.get("observed_delay_seconds"), "documentedDelaySeconds": first.get("documented_delay_seconds"),
            **basis,
            "surfaces": [{"id": e["id"], "surface": e["surface"], "classification": e["classification"],
                          "targetContract": _addr(e["target_contract"]), "targetLabel": e["target_label"]} for e in es],
            "url": f"{BASE}/protocols/{v['slug']}/", "preflightArgs": {"chain": chain, "address": primary}}


def _onboarding_item(b):
    chain = ONB_CHAIN[b["chain"]]
    supply = [c for c in b["checks"] if c.get("sig") == "totalSupply()"]
    assert supply, b["slug"]
    token = _addr(supply[0]["to"])
    return {"kind": "brief", "slug": b["slug"], "name": f'{b["asset"]} onboarding verification brief', "tokens": TOKENS[b["slug"]],
            "category": "Collateral onboarding verification brief", "chain": chain, "chainId": CHAIN_IDS[chain],
            "primaryContract": token, "targetLabel": b["asset"], "controllerAddress": None, "controllerKind": None,
            "observedDelaySeconds": None, "documentedDelaySeconds": None,
            "classification": "onboarding_delta_brief", "evidenceBasis": "pinned_rpc_brief", "easAttested": False, "baseEasUids": [],
            "venue": b["venue"], "forumUrl": b["forum"]["url"], "pinnedBlock": int(b["pin"]["number"]), "relatedProtocolSlug": None,
            "url": f"{BASE}/briefs/{b['slug']}/", "preflightArgs": {"chain": chain, "address": token}}


def _radar_item(it, related):
    slug = it["brief"].rstrip("/").split("/")[-1]
    tl = _addr(it["timelock"])
    return {"kind": "brief", "slug": slug, "name": it["title"], "tokens": TOKENS[slug], "category": "Timelock radar brief (queued operations)",
            "chain": "ethereum", "chainId": 1, "primaryContract": tl, "targetLabel": f'{it["protocol"]} timelock',
            "controllerAddress": tl, "controllerKind": "timelock", "observedDelaySeconds": int(it["min_delay_seconds"]), "documentedDelaySeconds": None,
            "classification": "timelock_radar_brief", "evidenceBasis": "pinned_rpc_brief", "easAttested": False, "baseEasUids": [],
            "eta": int(it["eta"]), "relatedProtocolSlug": related[slug],
            "url": f"{BASE}/briefs/{slug}/", "preflightArgs": {"chain": "ethereum", "address": tl}}


def build_items(sp, onb, radar, brief_protocol):
    """sp = build_site.site_protocols(idx, pinned); brief_protocol = build_site.BRIEF_PROTOCOL."""
    protocols = sorted((_protocol_item(n, v) for n, v in sp.items()), key=lambda x: x["slug"])
    briefs = sorted([_onboarding_item(b) for b in onb["briefs"]] + [_radar_item(it, brief_protocol) for it in radar["items"]],
                    key=lambda x: x["slug"])
    items = protocols + briefs
    slugs = [x["slug"] for x in items]
    assert len(slugs) == len(set(slugs)), "duplicate slug"
    assert set(TOKENS) == set(slugs), f"TOKENS out of sync: missing {sorted(set(slugs) - set(TOKENS))} extra {sorted(set(TOKENS) - set(slugs))}"
    assert all(x["tokens"] for x in items)
    assert all(x["relatedProtocolSlug"] in {p["slug"] for p in protocols} for x in briefs if x["relatedProtocolSlug"])
    for x in items:
        for s in json.dumps(x, ensure_ascii=False):
            assert s not in "  ", x["slug"]
    return items


def totals(items):
    p = [x for x in items if x["kind"] == "protocol"]
    return {"protocols": len(p), "briefs": len(items) - len(p), "easAttestedProtocols": sum(x["easAttested"] for x in p),
            "rpcObservedProtocols": sum(x["evidenceBasis"] == "rpc_observed" for x in p), "items": len(items)}


def catalog_json(items):
    doc = {"schema": CATALOG_SCHEMA, "sources": [BASE + s for s in SOURCES], "totals": totals(items), "items": items,
           "search": {"http": "https://pacta-x402.pacta.workers.dev/v1/protocols/lookup?q=<name, token or 0x address>",
                      "mcp": "pacta_lookup_protocol", "note": "Free discovery in every pricing mode; preflightArgs feed pacta_check_preflight directly."}}
    return json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


BEGIN, END = "// ---- CATALOG-BEGIN (generated by tools/build_lookup.py; do not edit by hand)\n", "// ---- CATALOG-END\n"


def catalog_js(items):
    rows = "".join("  " + json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + ",\n" for x in items)
    return BEGIN + "export const LOOKUP_CATALOG = lookupFreeze([\n" + rows + "]);\n" + END


def sync_module(path, items):
    """Rewrite the generated catalog between the markers of packages/mcp-server/src/lookup.mjs; True when it changed."""
    src = open(path, encoding="utf-8").read()
    a, b = src.index(BEGIN), src.index(END) + len(END)
    new = src[:a] + catalog_js(items) + src[b:]
    if new != src:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
    return new != src


def write_all(root, docs, sp, onb, radar, brief_protocol):
    items = build_items(sp, onb, radar, brief_protocol)
    t = totals(items)
    n_pin = sum(v["pinned"] for v in sp.values())          # counts follow the feeds; verify_site_v2.EXPECT pins the published numbers
    assert (t["protocols"], t["briefs"], t["easAttestedProtocols"], t["rpcObservedProtocols"]) == (
        len(sp), len(onb["briefs"]) + len(radar["items"]), len(sp) - n_pin, n_pin), t
    with open(os.path.join(docs, "api", "v1", "lookup.json"), "w", encoding="utf-8") as fh:
        fh.write(catalog_json(items))
    sync_module(os.path.join(root, "packages", "mcp-server", "src", "lookup.mjs"), items)
    write_badges(docs, items)
    with open(os.path.join(docs, "api", "v1", "protocols.json"), "w", encoding="utf-8") as fh:
        fh.write(protocols_json(sp, items))
    return items


# ---- control-plane status badges: byte-identical to badgeSvg() in packages/mcp-server/src/lookup.mjs (the worker's
# GET /v1/badges/<slug>.svg serves the same block); verify_site_v2.py compares all 53 through node.
BADGE_TITLE = "Pacta Control Plane"
BADGE_TIERS = {"aligned": ("Aligned · Base EAS", "#047857"), "parameter_delta": ("Parameter Delta", "#b45309"),
               "rpc_observed": ("RPC-Observed", "#475569")}


def badge_tier(item):
    if not item or item.get("kind") != "protocol":
        return None
    if item.get("evidenceBasis") == "rpc_observed":
        return "rpc_observed"
    return "aligned" if item.get("classification") == "aligned_baseline" else "parameter_delta"


def _num(x):
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def badge_svg(item):
    tier = badge_tier(item)
    right, color = BADGE_TIERS[tier]
    left, slug = BADGE_TITLE, item["slug"]
    lw, rw = len(left) * 7 + 12, len(right) * 7 + 12
    w = lw + rw
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{left}: {right}">'
            f'<title>{left}: {right} ({slug})</title>'
            f'<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#1f2937"/><rect x="{lw}" width="{rw}" height="20" fill="{color}"/></g>'
            f'<g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,Geneva,sans-serif" font-size="11">'
            f'<text x="{_num(lw / 2)}" y="14">{left}</text><text x="{_num(lw + rw / 2)}" y="14">{right}</text></g></svg>\n')


def write_badges(docs, items):
    d = os.path.join(docs, "badges")
    os.makedirs(d, exist_ok=True)
    want = {}
    for x in items:
        if x["kind"] == "protocol":
            want[x["slug"] + ".svg"] = badge_svg(x)
    for name in os.listdir(d):                      # stale badges of removed protocols never linger
        if name.endswith(".svg") and name not in want:
            os.remove(os.path.join(d, name))
    for name, svg in sorted(want.items()):
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            fh.write(svg)
    return want


# ---- docs/api/v1/protocols.json: one record per /protocols/<slug>/ page with its badge tier, evidence basis and pinned
# surfaces (block number + hash). The same truthful split as the catalog: 33 eas_attested vs 20 rpc_observed.
PROTOCOLS_SCHEMA = "pacta.protocols.v1"
API = "https://pacta-x402.pacta.workers.dev"
REGISTRY = "0x35D21Bb4Df6586FE7759b5e57263ffeB3e1fd872"
EAS_BASE = "0x4200000000000000000000000000000000000021"
EAS_SCHEMA_UID = "0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83"


def protocols_json(sp, items):
    by = {x["slug"]: x for x in items if x["kind"] == "protocol"}
    out = []
    for name, v in sp.items():
        x = by[v["slug"]]
        tier = badge_tier(x)
        surf = []
        for e in v["entries"]:
            surf.append({"id": e["id"], "surface": e["surface"], "classification": e["classification"], "targetContract": _addr(e["target_contract"]),
                         "targetLabel": e["target_label"], "chain": e.get("chain", "ethereum"), "blockNumber": int(e["block_number"]),
                         "blockHash": e["block_hash"], "baseEasUid": e.get("base_eas_uid"), "sprint": e.get("sprint")})
        out.append({"slug": x["slug"], "name": name, "category": x["category"], "chain": x["chain"], "chainId": x["chainId"],
                    "url": x["url"], "evidenceBasis": x["evidenceBasis"], "easAttested": x["easAttested"],
                    "documentationComparison": x["documentationComparison"], "classification": x["classification"],
                    "sprints": x.get("sprints", []), "baseEasUids": x["baseEasUids"],
                    "badge": {"tier": tier, "label": BADGE_TIERS[tier][0], "svg": f"{BASE}/badges/{x['slug']}.svg", "live": f"{API}/v1/badges/{x['slug']}.svg"},
                    "primaryContract": x["primaryContract"], "targetLabel": x["targetLabel"], "controllerAddress": x["controllerAddress"],
                    "controllerKind": x["controllerKind"], "preflightArgs": x["preflightArgs"], "tokens": x["tokens"], "surfaces": surf})
    out.sort(key=lambda r: r["slug"])
    tiers = {}
    for r in out:
        tiers[r["badge"]["tier"]] = tiers.get(r["badge"]["tier"], 0) + 1
    doc = {"schema": PROTOCOLS_SCHEMA, "totals": {"protocols": len(out), "easAttested": sum(r["easAttested"] for r in out),
                                                  "rpcObserved": sum(r["evidenceBasis"] == "rpc_observed" for r in out),
                                                  "surfaces": sum(len(r["surfaces"]) for r in out), "badgeTiers": dict(sorted(tiers.items()))},
           "evidence": {"eas_attested": "Base-EAS-attested Sprint records: on-chain control plane compared with the protocol's documentation.",
                        "rpc_observed": "RPC-pinned records: on-chain control plane pinned at an archive block; documentation not assessed (documentationComparison: not_assessed); not EAS-attested."},
           "sentinelGuard": {"package": "packages/sentinel-guard (PactaSentinelGuard.sol)", "registry": REGISTRY, "eas": EAS_BASE, "schemaUid": EAS_SCHEMA_UID,
                             "bind": "bind(collateral, sprintId, easUid) with a Sprint id from `sprints` and its UID from `baseEasUids` (eas_attested protocols only; an unbound collateral can never have its cap increased)",
                             "guide": f"{BASE}/integrations/vault-factories/"},
           "protocols": out}
    t = doc["totals"]
    assert t["protocols"] == len(items_p := [x for x in items if x["kind"] == "protocol"]) == t["easAttested"] + t["rpcObserved"], t
    assert t["easAttested"] == sum(x["evidenceBasis"] == "eas_attested" for x in items_p), t
    return json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
