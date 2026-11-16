"""Build the Pacta static site (docs/) from the data files, so counts can never drift.

  python3 tools/refresh_radar.py            # (live, read-only) refresh docs/api/v1/radar.json
  python3 tools/make_og.py --font-dir DIR   # (optional) re-render og-preview.png / favicon.png
  python3 tools/build_site.py               # writes docs/index.html, request/, briefs/*/ (from tools/briefs_src/),
                                            # llms.txt, robots.txt, sitemap.xml, .well-known/security.txt, .nojekyll
  python3 verify_site_v2.py                 # checks the result

Domain cutover: change BASE_URL below (one line) and rebuild; every absolute URL (canonical, Open Graph, X card,
sitemap, robots, security.txt, llms.txt, brief metadata) is derived from it.

Design (v3): institutional editorial + data terminal. Hairline structure, 2-4px radii, Paper (light) default with a
Slate (dark) theme, tabular numerals, no web fonts and no third-party requests. Every call to action stays in the
browser: there are no mailto: links (they are dead clicks without a desktop mail client); requests go through the
coverage-request builder (#request and /request/), which opens a pre-filled GitHub intake issue, a Gmail web compose
window, or copies the scope brief.
"""

import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import onboarding_render as OR  # noqa: E402
import build_b2a_feeds as B2A  # noqa: E402
import build_lookup as LK  # noqa: E402
import control_diff as CD  # noqa: E402  "What differs": changed vs matched parameters of flagged records
import graph_manifest as GM  # noqa: E402  docs/api/v1/graph-manifest.json (pacta.graph_manifest.v1)

BASE_URL = "https://pacta.wtf"   # cutover: "https://pacta.fractalneurons.com"
# Batch E: the $100 USDC capped bounty (pacta.wtf/bounties/). Issues #21-#24 on Fractal-Neurons/pacta, one per $25 slot; the
# issue text is tools/bounty_issues.json (verbatim, rendered on the page). Update the numbers here if GitHub assigns others.
BOUNTY_ISSUE_URLS = {1: "https://github.com/Fractal-Neurons/pacta/issues/21", 2: "https://github.com/Fractal-Neurons/pacta/issues/22",
                     3: "https://github.com/Fractal-Neurons/pacta/issues/23", 4: "https://github.com/Fractal-Neurons/pacta/issues/24"}

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOCS = os.path.join(ROOT, "docs")
BRIEF_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "briefs_src")
E = html.escape
CONTACT = "pacta@dri.network"
REPO = "https://github.com/Fractal-Neurons/pacta"
FN = "https://fractalneurons.com"
TITLE = "Pacta · Free pre-execution API for AI agents"
DESC = "Free pre-execution contract checks for AI agents. No API key, no wallet."
OG_TITLE = "Free pre-execution contract safety checks for AI agents"
H1 = "Free Pre-Execution Contract & Governance Safety API for AI Agents — Zero API Key, Zero Wallet, 1 Call"
API = "https://pacta-x402.pacta.workers.dev"          # live Cloudflare Worker (free launch: $0, no key, no wallet)
MCP_URL, OPENAPI_URL = API + "/mcp", API + "/openapi.json"
RATE_LIMIT = "60 requests / minute per caller"
# Visitor review P1: send an explicit User-Agent. Cloudflare's edge refuses some default library agents (error 1010) before
# the Worker runs, so every HTTP quickstart names one.
UA = "my-agent/1.0"
CURL = f'curl -s -A "{UA}"'
UA_NOTE = ("Send a User-Agent (curl -A, or headers={\"User-Agent\": ...} in Python): Cloudflare's edge refuses some default "
           "library agents with error 1010 before the API answers.")
EDITORIAL_INDEPENDENCE = ("Payment never alters a Pacta classification. A badge changes strictly when on-chain contract state or public "
                          "documentation aligns and is verified at a new finalized block.")
HERO_EXAMPLE = ("stader-labs-ethx", "ethereum", "0xA35b1B31Ce002FBF2058D22F30f95D405200A15b")   # (record slug, chain, ETHx token)
# Live checker presets: (label, chain, address). Public contracts; the ETHx token is an indexed record (Stader, sprint 12).
PREFLIGHT_PRESETS = [("USDC on Base", "base", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
                     ("USDC on Ethereum", "ethereum", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
                     ("Stader ETHx", "ethereum", "0xA35b1B31Ce002FBF2058D22F30f95D405200A15b")]
BRIEFS = {
    "ethena-ops-0x0ca0-0x1fe5": "Pre-execution brief: two queued Ethena timelock operations onboard RLUSD and USAT to EthenaMinting "
                                "at 200M / 20M USDe-per-block caps (1-day delay; ETAs 2026-11-14 10:20–10:22 UTC).",
    "etherfi-op-0x244e": "Pre-execution brief: ether.fi operation 0x244e…359f moves the EtherfiL1SyncPoolETH LayerZero V2 "
                         "delegate behind the 10-day EtherFiTimelock (ETA 2026-11-20 16:54 UTC).",
    "treehouse-op-0x2f11": "Pre-execution brief: a queued 5-day timelock operation upgrades the Treehouse TREE token (not tETH) "
                           "and installs a 5-of-7 Safe blacklister (ETA 2026-11-17 04:51 UTC).",
}
NAV = [("preflight", "Free API"), ("protocols/", "Protocols"), ("inspector", "Inspector"), ("radar", "Radar"), ("findings", "Findings"), ("index", "Index"), ("verify", "Verify"),
       ("pricing", "Pricing"), ("mcp/", "MCP"), ("bounties/", "Bounties"), ("faq", "FAQ")]
# Brand / RAG disambiguation (receipt/1817): the exact line in llms.txt, llms-full.txt, /llms/ and the Organization JSON-LD.
DISAMBIGUATION = B2A.DISAMBIGUATION
BRAND = B2A.BRAND
REMOTE_TOOLS_DOC, STDIO_TOOLS_DOC = B2A.REMOTE_TOOLS_DOC, B2A.STDIO_TOOLS_DOC
ORG_LD = {"@context": "https://schema.org", "@type": "Organization", "name": "Pacta by Fractal Neurons", "alternateName": ["Pacta", "pacta.base.eth"],
          "url": f"{BASE_URL}/", "logo": f"{BASE_URL}/logo-512.png", "image": f"{BASE_URL}/logo.svg", "sameAs": [REPO, "https://fractalneurons.com", "https://basescan.org/name-lookup-search?id=pacta.base.eth"],
          "parentOrganization": {"@type": "Organization", "name": "Fractal Neurons", "url": "https://fractalneurons.com"},
          "disambiguatingDescription": DISAMBIGUATION}
# Engagement tracks offered by the request builder (and linked from #pricing). key -> (title, price, unit, summary,
# GitHub dropdown option). Issuer work (24h clearance, continuous Aligned maintenance), the high-throughput API SLA and
# the free community queue. The public data itself (every indexed record, the timelock radar, briefs, /api/v1/*.json
# and llms.txt) is free and real-time for everyone: no paywall, no delay. The keys are the closed `tier=` enum that
# /request/?tier=… prefills; the GitHub dropdown option strings must match .github/ISSUE_TEMPLATE/request-scan.yml
# exactly (prefill is by value).
CLEARANCE_PRICE, MONITORING_PRICE = "$5,000 USDC", "$1,500 USDC / month"
TRACKS = {
    "clearance": ("24h Onboarding & Delta Clearance", CLEARANCE_PRICE, "flat",
                  "Archive-RPC control-plane verification, an upstream docs reconciliation PR and a Curator Diligence Dossier within a 24h SLA. "
                  "The resulting classification strictly follows verified on-chain and documentation evidence; payment never changes it.",
                  "24h Onboarding & Delta Clearance ($5,000 USDC flat)"),
    "continuous": ("Continuous Aligned Maintenance", "$1,500 USDC", "per month",
                   "Keeps the Base EAS Aligned attestation and Curator Diligence Dossier current across governance proposals, "
                   "signer rotations and timelock upgrades.",
                   "Continuous Aligned Maintenance ($1,500 USDC per month)"),
    "api_sla": ("Enterprise / High-Throughput API SLA", "Priced on scope", "",
                "For wallets, custodians and DeFAI agents that need more than 60 requests / minute or a dedicated SLA.",
                "Enterprise / High-Throughput API SLA (priced on scope)"),
    "community": ("Community queue", "Free", "",
                  "Standard public queue, unscheduled (typically 6–8 weeks). Curators and risk stewards always have free, "
                  "real-time access to pacta.wtf and llms.txt.",
                  "Community queue (free; unscheduled, typically 6–8 weeks)"),
}
DEFAULT_TRACK = "clearance"
PAID_TRACKS = ("clearance", "continuous", "api_sla")
# Settlement tracks in #req-pay (closed `settlement=` enum). Option A first: no transfer is needed to open intake.
# key -> (heading, sub-line, explanation, GitHub dropdown option)
SETTLEMENT = {
    "invoice": ("Option A — Formal Commercial Invoice (PDF) & Counterparty Settlement", "Recommended for protocol treasuries & CFOs",
                "Submit scope first (no upfront transfer required to open intake): Pacta issues a formal commercial invoice (PDF) "
                "and verified counterparty payment instructions upon scope confirmation — designed for foundation finance teams, "
                "legal review, and multi-signer treasury workflows.",
                "Option A: formal commercial invoice (PDF) and counterparty settlement"),
    "direct": ("Option B — Direct Express On-Chain USDC Settlement", "Immediate 24h turnaround",
               "USDC on Base or Ethereum to the Pacta treasury (direct settlement EOA) below; paste the transaction hash in the "
               "form and the 24-hour window starts once scope is confirmed.",
               "Option B: direct on-chain USDC settlement"),
}
DEFAULT_SETTLEMENT = "invoice"
TREASURY_LABEL = "Pacta treasury (direct settlement EOA)"     # an externally owned account: never a Safe / multisig
# Payment rail for the clearance offer. The treasury is an externally owned account (no contract code on Base or
# Ethereum), so the same key controls it on both chains; USDC contracts are Circle's native deployments.
USDC = {"Base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "Ethereum": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}
VULN_ROUTE = ("Exploit-sensitive vulnerabilities are never published here. They go through the protocol’s Immunefi or "
              "Cantina bounty programme, or to a partner audit firm under a 15% referral partnership.")
FINDINGS = [  # (record id, headline, explanation html, observed, documented, link, link label)
    ("ethena-minting-rlusd-usat-onboarding-ops",
     "New Ethena collateral can be approved on a 1-day timelock; the docs describe 7 days.",
     'Two queued operations onboard RLUSD and USAT at 200M / 20M USDe-per-block caps, the same as USDC / USDT, with '
     '<code>stablesDeltaLimit = 0</code>. <code>getMinDelay()</code> returns 86,400s.',
     ("Observed", "1d"), ("Docs", "7d"), "briefs/ethena-ops-0x0ca0-0x1fe5/", "Read the brief"),
    ("stader-ethx-manager-safe-and-timelock",
     "Stader’s Manager Safe is 3-of-6 on-chain; the docs say 3-of-5.",
     "The ETHx upgrade path itself sits behind a 7-day TimelockController, as documented. The difference is the Manager "
     "multisig’s signer set.",
     ("Observed", "3-of-6"), ("Docs", "3-of-5"), None, "View record"),
    ("curve-crvusd-factory-lending-owner-proxy",
     "crvUSD market creation now passes through a LendingOwnerProxy wrapper.",
     "ControllerFactory <code>admin()</code> is a LendingOwnerProxy whose <code>dao()</code> is the CurveOwnershipAgent "
     "(7-day Aragon vote), with a 5-of-9 EmergencyDAO. The docs still name the agent as the admin.",
     ("Observed", "LendingOwnerProxy"), ("Docs", "OwnershipAgent"), None, "View record"),
    ("inverse-firm-borrowcontroller-staleness-sentinel",
     "A zero staleness threshold switches FiRM’s oracle staleness check off for sDOLA; a queued 48h fix turns it on.",
     "<code>stalenessThreshold = 0</code> makes <code>isPriceStale</code> return false. A queued Timelock transaction sets "
     "86,500s.",
     ("Observed", "0 (off)"), ("Queued", "86,500s"), None, "View record"),
]


def short(h, a=6, b=4):
    return h[:a] + "…" + h[-b:]


def utc(t, secs_=False):
    return dt.datetime.fromtimestamp(t, dt.UTC).strftime("%Y-%m-%d %H:%M:%S UTC" if secs_ else "%Y-%m-%d %H:%M UTC")


def secs(s):
    """Exact compact duration: 0 -> 0s, 1 -> 1s, 86400 -> 1d, 129600 -> 1d 12h. Mirrors secs() in docs/app.js."""
    if s is None:
        return "—"
    s, parts = int(s), []
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if s >= n:
            q, s = divmod(s, n)
            parts.append(f"{q}{unit}")
    return " ".join(parts) or "0s"


def copy_btn(value, label="Copy", what=None):
    aria = what or ("Copy: " + (value if len(value) <= 60 else value[:57] + "…"))
    return f'<button class="copy" type="button" data-copy="{E(value)}" aria-label="{E(aria)}">{label}</button>'


def hexref(value, a=6, b=4):
    """Truncated hex for display, full value in title + copy button. Never lets a 42/66-char string break a layout."""
    return f'<span class="addr" title="{E(value)}">{E(short(value, a, b))}</span>{copy_btn(value)}'


ROBOTS_META = "index, follow, max-snippet:-1, max-image-preview:large"     # unrestricted indexing, snippets and grounding
ROBOTS_META_404 = "noindex, follow, max-snippet:-1, max-image-preview:large"   # 404.html: never index the not-found page itself


# S01: one policy for every generated page (meta CSP cannot carry frame-ancestors; send that as a response header at the edge)
CSP = ("default-src 'self';script-src 'self';style-src 'self' 'unsafe-inline';img-src 'self' data:;"
       "connect-src 'self' https://pacta-x402.pacta.workers.dev https://ethereum-rpc.publicnode.com https://base-rpc.publicnode.com "
       "https://eth.drpc.org https://mainnet.base.org;object-src 'none';base-uri 'self'")
THEME_JS = ('document.documentElement.className="js";try{if(localStorage.getItem("pacta-theme")==="slate")'
            'document.documentElement.dataset.theme="slate"}catch(e){}\n')


def head(title, desc, url, prefix="", og_title=OG_TITLE, og_type="website", image=f"{BASE_URL}/og-preview.png", extra="", robots=ROBOTS_META, rich=False):
    """Order matters: everything social/agent-relevant comes first and stays inside the first 1.2 KB.
    b.js is the first-party beacon (docs/b.js, < 1.5 KB): no cookies, no storage ids, no third parties, honours DNT."""
    t, d = E(title), E(desc)
    parts = [
        '<!doctype html><html lang="en"><head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{t}</title>",
        f'<meta name="description" content="{d}">',
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:type" content="{og_type}">',
        '<meta property="og:site_name" content="Pacta by Fractal Neurons">',
        f'<meta property="og:title" content="{E(og_title)}">',
        f'<meta property="og:description" content="{d}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{image}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{E(og_title)}">',
        f'<meta name="twitter:description" content="{d}">',
        f'<meta name="twitter:image" content="{image}">',
        f'<meta name="robots" content="{robots}">',
    ] + ([extra] if extra else []) + [
        f'<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">',
        f'<link rel="icon" href="{prefix}favicon.png" type="image/png" sizes="32x32">',
        '<meta name="referrer" content="strict-origin-when-cross-origin">',
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">',
    ] + ([   # homepage only (sub-pages keep <body> under 2.5 KB; browsers also fetch /favicon.ico and /apple-touch-icon.png from the root)
        f'<link rel="icon" href="{prefix}favicon.ico" sizes="any">',
        f'<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">',
        f'<link rel="alternate" type="application/atom+xml" href="{prefix}feed.xml" title="Pacta feed (Atom)">',
        f'<link rel="alternate" type="application/feed+json" href="{prefix}api/v1/feed.json" title="Pacta feed (JSON Feed)">',
    ] if rich else []) + [
        f'<link rel="stylesheet" href="{prefix}styles.css">',
        f'<link rel="alternate" type="text/markdown" href="{prefix}llms.txt"' + (' title="llms.txt">' if rich else '>'),
        f'<link rel="alternate" type="text/html" href="{prefix}llms/"' + (' title="llms.txt (HTML mirror)">' if rich else '>'),
        f'<script src="{prefix}theme.js"></script>',
        f'<script src="{prefix}app.js" defer></script>',
        f'<script src="{prefix}b.js" defer></script>',
        "</head>",
    ]
    return "\n".join(parts)


def livebar_etas(radar):
    """Every queued ETA as "eta|protocol;…" (ascending), so app.js can move "Next" past ETAs that have elapsed since the
    deterministic build; the no-JS text names the earliest ETA and is dated by the radar block."""
    pairs = sorted({(int(op["eta"]), it["protocol"]) for it in radar["items"] for op in it.get("operations", []) if op.get("eta")}
                   | {(int(it["eta"]), it["protocol"]) for it in radar["items"] if it.get("eta")})
    return ";".join(f"{eta}|{name.replace(';', ',').replace('|', '/')}" for eta, name in pairs)


def topbar(home=""):
    """home = "" on the homepage, "../" or "../../" on sub-pages."""
    links = "".join(f'<a href="{home}{k if k.endswith("/") else "#" + k}">{lbl}</a>' for k, lbl in NAV)   # "x/" = a page
    req = "#request" if home == "" else f"{home}request/"
    return (f'<a class="skip" href="#main">Skip to content</a>\n'
            f'<header class="topbar"><div class="wrap">'
            f'<a class="brand" href="{home or "./"}"><img src="{home}favicon.svg" alt="" width="24" height="24">PACTA<small>by Fractal Neurons</small></a>'
            f'<nav class="nav" aria-label="Sections">{links}</nav>'
            f'<div class="tools"><button class="tt" type="button" aria-label="Theme: Paper (switch to Slate)">'
            f'<span data-t="paper" class="on">Paper</span><span data-t="slate">Slate</span></button>'
            f'<a class="gh" href="{REPO}" target="_blank" rel="noopener" title="Source on GitHub: Fractal-Neurons/pacta">GitHub ↗</a>'
            f'<a class="btn sm primary" href="{req}">Request coverage</a></div>'
            f'</div></header>')


def footer(count_line, reg, home=""):
    return (f'<footer class="ftr"><div class="wrap">'
            f'<span class="ftr-brand"><img class="ftr-logo" src="{home}favicon.svg" alt="" width="18" height="18">Pacta by Fractal Neurons · pacta.base.eth · {E(count_line)}</span>'
            f'<nav aria-label="Footer"><a href="{home}mcp/">MCP</a><a href="{REPO}" target="_blank" rel="noopener">GitHub</a>'
            f'<a href="{COMMUNITY_URL}" target="_blank" rel="noopener">Community</a>'
            f'<a href="{home}api/v1/index.json">JSON feed</a><a href="{home}llms.txt">llms.txt</a><a href="{home}llms/">llms (HTML)</a>'
            f'<a href="https://basescan.org/address/{E(reg)}" target="_blank" rel="noopener">Base registry</a>'
            f'<a href="{home}bounties/">Bounties</a><a href="{home}leaderboard/">Leaderboard</a>'
            f'<a href="{home}.well-known/security.txt">security.txt</a>'
            f'<a href="{home}{"#request" if home == "" else "request/"}">Contact</a></nav>'
            f'</div></footer>')


def load():
    idx = json.load(open(os.path.join(DOCS, "api", "v1", "index.json")))
    radar = json.load(open(os.path.join(DOCS, "api", "v1", "radar.json")))
    m = idx["summary_metrics"]
    n = len(idx["entries"])
    assert m["records_indexed"] == n == m["parameter_deltas"] + m["protective_deltas"] + m["aligned_baselines"]
    assert m["sprints_completed"] == max(e["sprint"] for e in idx["entries"])
    check_index_chains(idx)
    return idx, radar


# RPC-pinned records (docs/api/v1/rpc-pinned.json): block-pinned read-only observations that are NOT EAS-attested (no sprint
# number, no summary document, no Base EAS UID). They get /protocols/<slug>/ pages next to the index.json Sprint records but
# never touch index.json, its counts or its EAS anchoring.
PINNED_SRC = os.path.join(DOCS, "api", "v1", "rpc-pinned.json")
PINNED_SCHEMA = "pacta.rpc_pinned_records.v1"
CHAINS = {"ethereum": ("Ethereum", "Ethereum Mainnet (chain id 1)", "$ETH_RPC_URL"), "base": ("Base", "Base Mainnet (chain id 8453)", "$BASE_RPC_URL")}
CHAIN_IDS = {"ethereum": 1, "base": 8453}
EXPLORERS = {"ethereum": ("Etherscan", "https://etherscan.io"), "base": ("Basescan", "https://basescan.org")}


def chain_of(e):
    """A record's chain: index.json records without a chain field are Ethereum Mainnet (Sprints 1-16)."""
    return e.get("chain", "ethereum")


def check_index_chains(idx):
    """index.json records may carry chain + rpc_env_var (both or neither); the pair must be one of CHAINS."""
    for e in idx["entries"]:
        assert ("chain" in e) == ("rpc_env_var" in e), e["id"]
        assert chain_of(e) in CHAINS and e.get("rpc_env_var", "$ETH_RPC_URL") == CHAINS[chain_of(e)][2], e["id"]


def record_chains(idx):
    return sorted({chain_of(e) for e in idx["entries"]}, key=list(CHAINS).index)


def explorer_link(e, kind="block"):
    """Block (or target address) on the record's own chain explorer."""
    name, url = EXPLORERS[chain_of(e)]
    ref = e["block_number"] if kind == "block" else e["target_contract"]
    return f'<a href="{url}/{"block" if kind == "block" else "address"}/{E(str(ref))}" target="_blank" rel="noopener">{name} ↗</a>'


def load_pinned(path=None):
    p = json.load(open(path or PINNED_SRC))
    assert p["schema"] == PINNED_SCHEMA and p["attestation"]["eas_attested"] is False and p["attestation"]["base_eas_uid"] is None
    for e in p["entries"]:
        assert e["provenance"] == "rpc_pinned" and e["base_eas_uid"] is None and "sprint" not in e and "summary_doc" not in e, e["id"]
        assert e["chain"] in CHAINS and e["rpc_env_var"] == CHAINS[e["chain"]][2], e["id"]
    return p


def is_pinned(e):
    return e.get("provenance") == "rpc_pinned"


def site_protocols(idx, pinned=None):
    """Every published /protocols/<slug>/ page, sorted by name: the index.json Sprint protocols (Base-EAS-anchored) plus the
    RPC-pinned protocols (routed by their own slug). {name: {"slug", "entries", "pinned"}}; names and slugs never collide."""
    pinned = load_pinned() if pinned is None else pinned
    out = {n: {"slug": protocol_slug(n), "entries": es, "pinned": False} for n, es in protocol_groups(idx).items()}
    for e in sorted(pinned["entries"], key=lambda e: e["id"]):
        assert e["protocol"] not in out or out[e["protocol"]]["pinned"], f'{e["protocol"]}: already an index.json protocol'
        out.setdefault(e["protocol"], {"slug": e["slug"], "entries": [], "pinned": True})["entries"].append(e)
    slugs = [v["slug"] for v in out.values()]
    assert len(slugs) == len(set(slugs)) and all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", x) for x in slugs), "protocol slug collision / shape"
    return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))


def counts(idx):
    m = idx["summary_metrics"]
    a = idx["onchain_anchoring"]
    eas = sorted(int(k) for k in a["sprint_eas_attestations"])
    assert eas == list(range(1, len(eas) + 1)), "sprint attestations must be contiguous from Sprint 1"
    s = m["sprints_completed"]
    pend = [n for n in range(1, s + 1) if n not in eas]                       # indexed but not yet attested
    later = [n for n in eas if n > s]                                           # attested, records not yet in the index
    rng = lambda xs: "" if not xs else (str(xs[0]) if len(xs) == 1 else f"{xs[0]}–{xs[-1]}")
    return {"sprints": s, "records": m["records_indexed"], "eas_n": len(eas), "eas_from": eas[0], "eas_to": eas[-1],
            "pending": rng(pend), "later": rng(later), "multi_txs": a["attestation_coverage"]["eas_multi_attest_txs"],
            "delta": m["parameter_deltas"], "protect": m["protective_deltas"], "aligned": m["aligned_baselines"],
            "chains": " + ".join(CHAINS[ch][1].split(" (")[0] for ch in record_chains(idx))}


def coverage_line(idx, pinned=None):
    """The site-wide coverage line (receipt/1818), derived from the data: protocols published, EAS-attested Sprint records (and the
    Sprints they come from: index.json sprints_completed, not the attestation count), RPC-observed records."""
    pinned = load_pinned() if pinned is None else pinned
    c = counts(idx)
    return (f'{len(site_protocols(idx, pinned))} Protocols ({c["records"]} Base EAS-Attested Records across {c["sprints"]} Sprints + '
            f'{len(pinned["entries"])} RPC-Observed Records)')


def org_ld_script():
    return '<script type="application/ld+json">' + json.dumps(ORG_LD, ensure_ascii=False, sort_keys=True).replace("</", "<\\/") + "</script>"


def app_ld_script(idx):
    """SoftwareApplication JSON-LD (homepage): the free pre-execution API / MCP server, priced $0, with the catalog size."""
    c = counts(idx)
    ld = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Pacta pre-execution contract & governance safety API",
          "applicationCategory": "DeveloperApplication", "operatingSystem": "Any (HTTP API, remote MCP)", "url": f"{BASE_URL}/",
          "description": f"Free pre-execution checks for AI agents: who can upgrade, pause or change a contract, how fast, with "
                         f"{len(site_protocols(idx))} block-pinned protocol records ({c['records']} Base-EAS-attested records).",
          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
          "publisher": {"@type": "Organization", "name": "Pacta by Fractal Neurons", "url": f"{BASE_URL}/"},
          "softwareHelp": f"{BASE_URL}/mcp/", "sameAs": [REPO]}
    return '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, sort_keys=True).replace("</", "<\\/") + "</script>"


def multi_tx_html(c):
    return " and ".join(f"{hexref(tx)} (Sprints {rng})" for rng, tx in c["multi_txs"].items())


def anchoring_text(c):
    """One sentence on Base anchoring, derived from the data (never hand-edited)."""
    t = f'{c["eas_n"]} Base EAS sprint attestations cover Sprints {c["eas_from"]}–{c["eas_to"]}'
    if c["pending"]:
        t += f'; Sprints {c["pending"]} are pinned by block hash and SHA-256 summary digest until batch-attested'
    if c["later"]:
        t += f'; Sprint{"s" if "–" in c["later"] else ""} {c["later"]} records join the public index after review'
    return t + "."


CLASS_LABEL = {"parameter_delta": ("delta", "Parameter delta"), "protective_delta": ("protect", "Protective delta"),
               "aligned_baseline": ("", "Aligned baseline"),
               # RPC-pinned records: on-chain control plane pinned at an archive block; documentation comparison not assessed
               "rpc_observed": ("observed", "RPC-observed baseline")}
CLASS_DEFINITIONS = ("parameter_delta (on-chain differs from docs), protective_delta (a change that strengthens controls), aligned_baseline "
                     "(on-chain matches docs), rpc_observed (on-chain control plane pinned at an archive block height over JSON-RPC; "
                     "documentation parameter comparison unassessed)")


def badge(c):
    cls, lbl = CLASS_LABEL.get(c, ("", "Aligned baseline"))
    return f'<span class="{("badge " + cls).strip()}">{lbl}</span>'


def dot(c):
    return f'<span class="dot {CLASS_LABEL.get(c, ("", ""))[0]}"></span>'


def cast_line(e):
    """Runnable cast commands for a record (full signature + all arguments). Mirrors castCmd() in docs/app.js."""
    rpc = f'--rpc-url "{e.get("rpc_env_var", "$ETH_RPC_URL")}"'
    if e["check_type"] == "eth_getStorageAt":
        first = f'cast storage {e["target_contract"]} \\\n  {e["selector_or_slot"]} \\\n  --block {e["block_number"]} {rpc}'
    else:
        args = (" " + " ".join(e["call_args"])) if e.get("call_args") else ""
        first = f'cast call {e["target_contract"]} \\\n  "{e["call_signature"]}"{args} \\\n  --block {e["block_number"]} {rpc}'
    extra = "".join(f'\ncast call {x["to"]} "{x["signature"]}" --block {e["block_number"]} {rpc}' for x in e.get("extra_calls", []))
    return f'{first}{extra}\ncast block {e["block_number"]} --field hash {rpc}\n# expect {e["block_hash"]}'


def term(cmd, title="Reproduce on any archive node"):
    return (f'<div class="term"><div class="term-h"><span>{E(title)}</span>'
            f'<button class="copy" type="button" data-copy-term aria-label="Copy command: {E(title)}">Copy command</button></div>'
            f'<pre>{E(cmd)}</pre></div>')


def proof_html(e):
    if e["base_eas_uid"]:
        return (f'<a href="https://base.easscan.org/attestation/view/{E(e["base_eas_uid"])}" target="_blank" rel="noopener">'
                f'Base EAS attestation {E(short(e["base_eas_uid"]))} ↗</a>')
    return 'Pending Base EAS batch attestation · pinned by block hash and summary SHA-256'


def multisig(text):
    seen = []
    for x in re.findall(r"\b\d+-of-\d+\b", text):
        if x not in seen:
            seen.append(x)
    return " · ".join(seen) if seen else None


def proxy_admin(text):
    m = re.search(r"ProxyAdmin \((0x[0-9a-fA-F]{40})\)", text) or re.search(r"admin\(\) = [A-Za-z ]*\((0x[0-9a-fA-F]{40})\)", text)
    return m.group(1) if m else None


def delay_cmp(e):
    o, d = e["observed_delay_seconds"], e["documented_delay_seconds"]
    if o is None and d is None:
        return '<span class="muted">No timelock delay in this record</span>'
    warn = o is not None and d is not None and o != d
    return (f'<span class="cmp"><span class="chip obs{" warn" if warn else ""}"><i>Observed</i><b>{secs(o)}</b></span>'
            f'<span class="vs">vs</span><span class="chip"><i>Docs</i><b>{secs(d)}</b></span></span>')


def utc_iso(ts):
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def what_differs_html(entries, compact=False):
    """Visitor review P1 (understanding): the "What differs" callout, right under the title / badge of every page (or inspector
    sheet) with a parameter_delta / protective_delta record: discrepant parameters first (the headline), matched ones below."""
    wd = CD.what_differs(entries)
    if not wd:
        return ""
    ch = "".join(f'<li data-wd-changed><b>{E(c["parameter"])}</b>: <span class="obs">{E(c["observed"])}</span> observed vs '
                 f'<span class="doc">{E(c["documented"])}</span> documented</li>' for c in wd["changed"])
    mt = "".join(f'<li data-wd-matched>{E(m["parameter"])}: {E(m["value"])}</li>' for m in wd["matched"])
    tag = "div" if compact else "section"
    return (f'<{tag} class="{"memo-sec " if not compact else ""}whatdiffers" data-what-differs><h2 class="wd-h">What differs</h2>'
            f'<p class="wd-l">Changed / discrepant</p><ul class="wd-changed">{ch}</ul>'
            + (f'<p class="wd-l">Matched</p><ul class="wd-matched">{mt}</ul>' if mt else "") + f'</{tag}>\n')


def editorial_box():
    """Visitor review P2: the editorial-independence firewall, shown before any paid issuer service."""
    return (f'<aside class="editorial" data-editorial-independence><h2>Editorial Independence &amp; Alignment Criteria</h2>'
            f'<p>{E(EDITORIAL_INDEPENDENCE)}</p><p class="s">Paid issuer services (24h clearance {E(CLEARANCE_PRICE)}, continuous maintenance '
            f'{E(MONITORING_PRICE)}) fund the verification work; the evidence, the free API and every classification above are the same for everyone.</p></aside>\n')

def sheet(e):
    """Specification sheet for one record (server-rendered default; docs/app.js renders the same structure)."""
    ms, pa = multisig(e["onchain_observed"]), proxy_admin(e["onchain_observed"])
    rows = [("Category", E(e["category"])),
            ("Target contract", f'{E(e["target_label"])} · {hexref(e["target_contract"])}'),
            ("Timelock delay", delay_cmp(e))]
    if ms:
        rows.append(("Safe quorum", f'<span class="mono">{E(ms)}</span>'))
    if pa:
        rows.append(("EIP-1967 ProxyAdmin", hexref(pa)))
    rows += [("Pinned block", f'{"" if chain_of(e) == "ethereum" else E(CHAINS[chain_of(e)][0]) + " "}<span class="num">#{e["block_number"]:,}</span> · Sprint {e["sprint"]} '
                              f'<span class="badge final">Scanner-pinned (L1 finalized)</span>'),
             ("Canonical block hash", hexref(e["block_hash"], 8, 6)),
             ("Proof", proof_html(e)),
             ("Summary", f'<a href="{REPO}/blob/main/{E(e["summary_doc"])}" target="_blank" rel="noopener">{E(os.path.basename(e["summary_doc"]))} ↗</a>'
                         f' · SHA-256 {hexref(e["summary_sha256"], 8, 4)}')]
    kv = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return (f'<div class="sheet-h"><h3>{E(e["protocol"])}</h3>{badge(e["classification"])}</div>'
            f'<p class="sheet-sub">{E(e["surface"])}</p>'
            + what_differs_html([e], compact=True) +
            f'<dl class="kv">{kv}</dl>'
            f'<p class="obs-text">{prose(e["onchain_observed"])}</p>'
            + term(cast_line(e)))


HEX64 = re.compile(r"0x[0-9a-fA-F]{64}(?![0-9a-fA-F])")


def prose(text):
    """Escape record prose for display; 32-byte hashes (tx / op / block ids) are shortened with the full value in a
    tooltip, so a 66-character token can never force a mid-hash wrap. The JSON feed keeps the full text."""
    out, last = [], 0
    for m in HEX64.finditer(text):
        out.append(E(text[last:m.start()]))
        out.append(f'<span class="hx" title="{m.group(0)}">{E(short(m.group(0), 8, 6))}</span>')
        last = m.end()
    out.append(E(text[last:]))
    return "".join(out)


def sorted_entries(idx):
    return sorted(idx["entries"], key=lambda e: (-e["sprint"], e["protocol"].lower()))


# Curator baskets: key -> (label, category regex (case-insensitive) or None, chain or None). A record / protocol joins every
# basket whose category regex matches or whose chain matches. Used by /protocols/ and the homepage inspector (app.js reads the
# same rules from the pills' data-basket-re / data-basket-chain attributes).
BASKETS = [("stable_rwa", "Stablecoins & RWA", r"stable|rwa|dollar|credit|treasur|cdp|reinsur|borrowing", None),
           ("eth_lst_lrt", "ETH LST / LRT", r"staking|restak|\blst\b|\blrt\b|validator", None),
           ("lending_vaults", "Curated Lending & Vaults", r"lend|vault|curat|yield|allocator|market", None),
           ("base", "Base Ecosystem", None, "base")]


def baskets_of(category, chains):
    out = []
    for k, _, rx, ch in BASKETS:
        if (rx and re.search(rx, category or "", re.I)) or (ch and ch in chains):
            out.append(k)
    return out


def basket_pills(attr="data-basket", rules=False):
    """All + the four baskets as a pill group; rules=True also carries the matching rule (for client-side hydrated records)."""
    pills = [f'<button type="button" {attr}="all" aria-pressed="true">All</button>']
    for k, lbl, rx, ch in BASKETS:
        extra = ((f' data-basket-re="{E(rx)}"' if rx else "") + (f' data-basket-chain="{ch}"' if ch else "")) if rules else ""
        pills.append(f'<button type="button" {attr}="{k}" aria-pressed="false"{extra}>{E(lbl)}</button>')
    return f'<div class="seg basket" role="group" aria-label="Curator baskets"><span class="seg-l">Basket</span>{"".join(pills)}</div>'


SAMPLE_SIZE = 12


def curated_sample(idx, n=SAMPLE_SIZE):
    """Deterministic flagship sample for the static homepage: the inspector default (Ethena) and Stader first, then round-robin
    over (chain, classification) buckets in sorted_entries order (one record per protocol), so Ethereum + Base parameter /
    protective deltas and aligned baselines are all represented. Returned in sorted_entries order."""
    ents = sorted_entries(idx)
    pick = [next(e for e in ents if e["protocol"].startswith("Ethena")), next(e for e in ents if e["protocol"].startswith("Stader"))]
    buckets = [(ch, cl) for cl in ("parameter_delta", "protective_delta", "aligned_baseline") for ch in ("ethereum", "base")]
    while len(pick) < n:
        added = False
        for ch, cl in buckets:
            if len(pick) >= n:
                break
            names = {x["protocol"] for x in pick}
            nxt = next((e for e in ents if chain_of(e) == ch and e["classification"] == cl and e["protocol"] not in names), None)
            if nxt is not None:
                pick.append(nxt)
                added = True
        if not added:
            break
    ids = {e["id"] for e in pick}
    return [e for e in ents if e["id"] in ids]


def inspector(idx, c):
    ents = curated_sample(idx)
    default = next(e for e in ents if e["protocol"].startswith("Ethena"))
    items = "".join(
        f'<li><a href="#r-{E(e["id"])}" data-id="{E(e["id"])}" data-class="{E(e["classification"])}"'
        f'{" aria-current=" + chr(34) + "true" + chr(34) if e is default else ""}>'
        f'{dot(e["classification"])}<span class="p">{E(e["protocol"])}</span><span class="sp">S{e["sprint"]}</span>'
        f'<span class="s">{E(e["surface"])}</span></a></li>'
        for e in ents)
    return f"""<section class="sec" id="inspector"><div class="wrap">
<div class="sec-head"><span class="n">01</span><h2>Control-plane inspector</h2><span class="aside">No wallet. Every value pinned to a block and reproducible.</span></div>
<div class="bench">
<div class="bench-side">
<div class="bench-search"><input id="insp-q" type="search" placeholder="Search protocol, contract or 0x address" aria-label="Search {c["records"]} indexed records" autocomplete="off">
{basket_pills("data-insp-basket", rules=True)}
<div class="bench-filter" role="group" aria-label="Filter by classification"><button type="button" data-f="all" aria-pressed="true">All</button><button type="button" data-f="parameter_delta" aria-pressed="false">Deltas</button><button type="button" data-f="protective_delta" aria-pressed="false">Protective</button><button type="button" data-f="aligned_baseline" aria-pressed="false">Aligned</button></div></div>
<ul class="bench-list" id="insp-list" data-sample="{len(ents)}">{items}</ul>
<div class="bench-count"><span id="insp-count">{len(ents)} of {c["records"]} records (curated sample)</span> <button type="button" class="linkish" data-insp-all>Show all {c["records"]} records</button></div>
</div>
<div class="sheet" id="insp-panel" aria-live="polite">{sheet(default)}</div>
</div>
</div></section>"""


def load_onboarding():
    p = os.path.join(DOCS, "api", "v1", "onboarding.json")
    return json.load(open(p)) if os.path.exists(p) else {"briefs": []}


def onboarding_section(onb):
    if not onb["briefs"]:
        return ""
    return f"""<section class="sec" id="onboarding"><div class="wrap">
<div class="sec-head"><span class="n">03</span><h2>Live onboarding verification briefs</h2><span class="aside">{len(onb["briefs"])} assets currently proposed as collateral · block-pinned</span></div>
<p class="sec-intro">Who can change each asset now in front of Aave and Euler governance, read at a canonical block on two RPC endpoints, with every call reproducible. Machine-readable: <a href="api/v1/onboarding.json">/api/v1/onboarding.json</a>.</p>
<div class="tbl-wrap"><table class="tbl radar"><thead><tr><th>Asset</th><th>Forum thread</th><th class="hide-m">Pinned block</th><th class="r">Brief</th></tr></thead>
<tbody>{OR.homepage_rows(onb)}</tbody></table></div>
</div></section>"""


def onboarding_page(b, idx):
    pin = b["pin"]
    cmd = OR.terms(b)
    content = OR.content(b, term(cmd, "Reproduce every value on any archive node"), CLEARANCE_PRICE)
    meta = (f'<dl class="memo-meta"><dt>Asset</dt><dd>{E(b["asset"])}</dd><dt>Venue</dt><dd>{E(b["venue"])}</dd>'
            f'<dt>Pinned block</dt><dd>{E(OR.CHAIN_NAME[b["chain"]])} <span class="num">#{pin["number"]:,}</span> · {E(utc(pin["timestamp"], True))} '
            f'<span class="badge final">Canonical (EIP-1898)</span></dd><dt>Block hash</dt><dd>{hexref(pin["hash"], 10, 6)}</dd>'
            f'<dt>Data</dt><dd><a href="../../api/v1/onboarding.json">/api/v1/onboarding.json</a> · slug <code>{E(b["slug"])}</code></dd></dl>')
    content = content.replace("</header>", "</header>\n" + meta, 1) + clearance_callout(b["asset"], b["slug"], b["forum"]["url"])
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    title = f'{b["asset"]}: onboarding verification brief'
    body = f"""<body>
{topbar("../../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../../">Pacta</a> / <a href="../../#onboarding">Onboarding briefs</a> / {E(b["slug"])}</div>
<article class="memo">
{content}</article>
<div class="memo-foot"><span>Read-only on-chain analysis. Not investment advice. Exploit-sensitive vulnerabilities are never published here; they go through Immunefi or Cantina bounty programmes.</span><a href="../../request/?tier=clearance">Clear these findings in 24h · {E(CLEARANCE_PRICE)} →</a></div>
</main>
{footer(count_line, reg, "../../")}
</body></html>
"""
    return head(title, OR.summary(b), f"{BASE_URL}/briefs/{b['slug']}/", prefix="../../", og_title=title, og_type="article") + "\n" + body


# ---- timelock operation state (radar.json, read at a finalized block) ----
# executed: isOperationDone; ready: the delay has elapsed at the finalized block and the op is still unexecuted
# (execute() is callable); pending: queued, delay not elapsed. Never "executed" while done is false.
LIVE_TIMELOCKS_URL = f"{API}/v1/briefs/live-timelocks?caller_agent=pacta-wtf-radar&requester_role=individual_user&caller_purpose=governance_monitoring"
OP_STATE_LABEL = {"executed": "EXECUTED", "ready": "READY · EXECUTABLE NOW", "pending": "PENDING", "unknown": "CANCELLED OR UNKNOWN", "mixed": "MIXED"}


def op_state(o):
    if o.get("done"):
        return "executed"
    if o.get("ready"):
        return "ready"
    return "pending" if o.get("pending") else "unknown"


def item_state(item):
    s = {op_state(o) for o in item["operations"]}
    return s.pop() if len(s) == 1 else "mixed"


def state_badge(state, ops):
    """Status badge; data-ops lets app.js re-check these operations live (textContent / class only)."""
    return (f'<span class="opstate {state}" data-opstate="{state}" data-ops="{" ".join(o["op_id"] for o in ops)}">'
            f'{E(OP_STATE_LABEL[state])}</span>')


def delay_text(seconds):
    return f"{seconds // 3600}h" if seconds % 3600 == 0 else secs(seconds)


def post_eta_banner(item, r):
    """Prominent post-ETA status at the top of a brief once any operation's delay has elapsed (or it was executed)."""
    st = item_state(item)
    if st not in ("ready", "executed", "mixed"):
        return ""
    n = len(item["operations"])
    blk = f'Finalized Block #{r["block_number"]:,}'
    if st == "executed":
        clause = f'{delay_text(item["min_delay_seconds"])} Delay Elapsed · Executed on L1 by {blk}'
        detail = f'isOperationDone = true for {"the operation" if n == 1 else f"all {n} operations"}'
    elif st == "ready":
        clause = f'{delay_text(item["min_delay_seconds"])} Delay Elapsed · Unexecuted on L1 at {blk}'
        detail = (f'isOperationPending = true and isOperationDone = false for {"the operation" if n == 1 else f"both operations" if n == 2 else f"all {n} operations"}: '
                  f'the timelock delay has elapsed, so execute() is callable, but {"it has" if n == 1 else "they have"} not been executed')
    else:
        clause = f'Operations differ · read at {blk}'
        detail = "; ".join(f'{short(o["op_id"], 6, 4)}: {OP_STATE_LABEL[op_state(o)]}' for o in item["operations"])
    return (f'<div class="poststatus {st}" id="post-eta-status" data-live-timelocks="{E(LIVE_TIMELOCKS_URL)}">'
            f'<span class="label">Post-ETA Live Status</span>'
            f'<p class="ps-head"><b>Post-ETA Verification:</b> {state_badge(st, item["operations"])} <span class="ps-clause">({E(clause)})</span></p>'
            f'<p class="s">{E(detail)}. Read at finalized block #{r["block_number"]:,} ({E(r["block_time_utc"])}) on '
            f'{r.get("rpcs_cross_checked", 2)} independent RPCs. <span class="live-line" data-live-line></span></p></div>\n')


def radar_counts(radar):
    """(pending operations, protocols with a pending operation, executed operations): an executed (isOperationDone) operation is
    never counted as queued."""
    ops = [(it["protocol"], o) for it in radar["items"] for o in it["operations"]]
    pend = [p for p, o in ops if not o.get("done")]
    return len(pend), len(set(pend)), sum(1 for _, o in ops if o.get("done"))


def radar_counts_text(radar):
    p, np_, x = radar_counts(radar)
    return (f'{p} pending operation{"s" if p != 1 else ""} across {np_} protocol{"s" if np_ != 1 else ""} · '
            f'{x} recently executed')


def radar_section(radar):
    r = radar["refreshed_at"]
    rows = []
    for it in radar["items"]:
        ops = ", ".join(f'<span class="hx" title="{o["op_id"]}">{short(o["op_id"], 6, 4)}</span>' for o in it["operations"])
        done = all(o.get("done") for o in it["operations"])
        rows.append(
            f'<tr data-radar-row="{"executed" if done else "pending"}"{" class=" + chr(34) + "is-executed" + chr(34) if done else ""}>'
            f'<td><b>{E(it["protocol"])}</b><span class="sub">{state_badge(item_state(it), it["operations"])}</span></td>'
            f'<td><span class="op">{E(it["title"])}</span><span class="sub">{E(it["summary"])}</span>'
            f'<span class="meta">Timelock {hexref(it["timelock"])} · Operation{"s" if len(it["operations"]) > 1 else ""} {ops}</span></td>'
            f'<td class="nowrap num hide-m">{secs(it["min_delay_seconds"])}</td>'
            + (f'<td class="nowrap"><span class="countdown" data-eta="{it["eta"]}">ETA {E(utc(it["eta"]))}</span><span class="sub">{E(utc(it["eta"]))}</span></td>' if it.get("eta") else
               f'<td class="nowrap"><span class="opstate executed">Executed</span><span class="sub">isOperationDone = true at block #{r["block_number"]:,}</span></td>') +
            f'<td class="r nowrap"><a href="{E(it["brief"])}">Read brief →</a></td></tr>')
    fresh = f'Pinned snapshot · observed {r["block_time_utc"]} (Mainnet finalized block #{r["block_number"]:,})'
    tls = "".join(f' · <a href="https://etherscan.io/address/{E(it["timelock"])}" target="_blank" rel="noopener">{E(it["protocol"])} timelock ↗</a>'
                  for it in radar["items"])
    live_note = (f'<p class="radar-live" data-radar-live><b>All queued operations are live Ethereum Mainnet timelock reads (zero demo data)</b>: '
                 f'read at finalized block <a href="https://etherscan.io/block/{r["block_number"]}" target="_blank" rel="noopener">#{r["block_number"]:,} ↗</a>'
                 f'{tls}.</p>')
    return f"""<section class="sec" id="radar" data-live-timelocks="{E(LIVE_TIMELOCKS_URL)}"><div class="wrap">
<div class="sec-head"><span class="n">02</span><h2>Queued timelock radar</h2><span class="aside"><span data-radar-counts>{E(radar_counts_text(radar))}</span> · <a href="feed.xml" data-feed-subscribe>Subscribe (RSS / JSON Feed — Slack compatible)</a></span></div>
{live_note}
<div class="tbl-wrap"><table class="tbl radar"><thead><tr><th>Protocol</th><th>Queued operation</th><th class="hide-m">Delay</th><th>Execution window</th><th class="r">Brief</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<div class="prov"><span class="badge final">Scanner-pinned (L1 finalized)</span><span data-snapshot-pinned>Snapshot pinned at {E(r["block_time_utc"])}<span class="obs-age" data-age="{r["block_timestamp"]}"></span></span><span data-last-recheck>Last live re-check: not yet</span><button type="button" class="btn sm" data-radar-refresh>Refresh</button><span class="snap-fallback" data-snapshot-fallback>Showing pinned historical snapshot</span><span>{E(fresh)}</span><span>State and ETAs read at that block on {r.get("rpcs_cross_checked", 2)} independent RPCs; READY means the delay has elapsed and the operation is still unexecuted. Countdowns run in your browser from each on-chain ETA.</span><span class="live-line" data-live-line></span></div>
</div></section>"""


def findings_section(idx):
    by_id = {e["id"]: e for e in idx["entries"]}
    slug_of = {e["id"]: v["slug"] for v in site_protocols(idx).values() for e in v["entries"]}
    rows = []
    for rid, h, expl, obs, doc, link, label in FINDINGS:
        e = by_id[rid]
        # the record's static protocol page (works without JS); with JS, data-open opens the hydrated index drawer in place
        href = link or f"protocols/{slug_of[rid]}/#{rid}"
        rows.append(
            f'<div class="frow"><div class="who">{E(e["protocol"])}<span class="sub">Sprint {e["sprint"]} · {E(e["category"])}</span>{badge(e["classification"])}</div>'
            f'<div><h3>{E(h)}</h3><p>{expl}</p></div>'
            f'<div class="cmpcol"><span class="chip obs{" warn" if e["classification"] == "parameter_delta" else ""}"><i>{obs[0]}</i><b>{E(obs[1])}</b></span>'
            f'<span class="chip"><i>{doc[0]}</i><b>{E(doc[1])}</b></span><a href="{E(href)}"{" data-open=" + chr(34) + E(rid) + chr(34) if not link else ""}>{label} →</a></div></div>')
    return f"""<section class="sec" id="findings"><div class="wrap">
<div class="sec-head"><span class="n">04</span><h2>Selected governance deltas</h2><span class="aside">What is on-chain versus what the docs say</span></div>
<div class="frows">{"".join(rows)}</div>
</div></section>"""


def index_rows(idx):
    rows = []
    for e in curated_sample(idx):
        search = " ".join(str(e.get(k, "")) for k in ("protocol", "category", "surface", "target_contract", "target_label", "onchain_observed", "classification", "sprint")).lower()
        rid = E(e["id"])
        proof = (f'<a href="https://base.easscan.org/attestation/view/{E(e["base_eas_uid"])}" target="_blank" rel="noopener">EAS ↗</a>'
                 if e["base_eas_uid"] else '<span class="muted">Hash-pinned</span>')
        rows.append(
            f'<tr data-class="{E(e["classification"])}" class="rec" data-id="{rid}" data-search="{E(search)}">'
            f'<td><b class="ell">{E(e["protocol"])}</b><span class="sub ell">{E(e["category"])}</span></td>'
            f'<td class="hide-s"><span class="ell">{E(e["target_label"])}</span><span class="sub">{hexref(e["target_contract"])}</span></td>'
            f'<td>{badge(e["classification"])}</td>'
            f'<td class="hide-m num nowrap">{secs(e["observed_delay_seconds"])} <span class="muted">/ {secs(e["documented_delay_seconds"])}</span></td>'
            f'<td class="hide-m nowrap"><span class="num">S{e["sprint"]} · #{e["block_number"]:,}</span><span class="sub">{proof}</span></td>'
            f'<td class="x"><a class="inspect-btn" href="#r-{rid}" aria-expanded="false" aria-controls="r-{rid}">Details</a></td></tr>')
        kv = (f'<dt>Pinned block</dt><dd>{E(CHAINS[chain_of(e)][1])} <span class="num">#{e["block_number"]:,}</span> · {explorer_link(e)} · {hexref(e["block_hash"], 8, 6)}</dd>'
              f'<dt>Delay</dt><dd>{delay_cmp(e)}</dd>'
              f'<dt>Summary</dt><dd><a href="{REPO}/blob/main/{E(e["summary_doc"])}" target="_blank" rel="noopener">Sprint {e["sprint"]} summary ↗</a></dd>'
              f'<dt>SHA-256</dt><dd>{hexref(e["summary_sha256"], 10, 6)}</dd>'
              f'<dt>Proof</dt><dd>{proof_html(e)}</dd>')
        rows.append(
            f'<tr class="drawer" id="r-{rid}"><td colspan="6"><div class="drawer-in">'
            f'<div><p class="drawer-title">{E(e["surface"])}</p><span class="label">On-chain observation</span><p class="obs-text">{prose(e["onchain_observed"])}</p>'
            f'<p class="obs-text"><span class="label">Documented</span><br>{prose(e["documented_reference"])}</p>'
            f'<p class="obs-text"><button class="linkish" type="button" data-inspect="{rid}">Open in inspector ↑</button></p></div>'
            f'<div><dl class="kv">{kv}</dl>{term(cast_line(e))}</div>'
            f'</div></td></tr>')
    return "\n".join(rows)


def index_section(idx, c, count_line):
    return f"""<section class="sec" id="index"><div class="wrap">
<div class="sec-head"><span class="n">05</span><h2>Public control-plane index</h2><span class="aside">{E(count_line)}</span></div>
<div class="ix-tools">
<input id="matrix-q" type="search" placeholder="Filter by protocol, contract, address or text" aria-label="Filter records" autocomplete="off">
<div class="seg" role="group" aria-label="Filter by classification">
<button type="button" data-class="all" aria-pressed="true">All<span class="num">{c["records"]}</span></button><button type="button" data-class="parameter_delta" aria-pressed="false">Parameter deltas<span class="num">{c["delta"]}</span></button><button type="button" data-class="protective_delta" aria-pressed="false">Protective<span class="num">{c["protect"]}</span></button><button type="button" data-class="aligned_baseline" aria-pressed="false">Aligned<span class="num">{c["aligned"]}</span></button>
</div>
<span class="ix-count" id="matrix-count">{SAMPLE_SIZE} of {c["records"]} records shown (curated sample)</span>
</div>
<div class="tbl-wrap"><table class="tbl" id="matrix">
<colgroup><col class="c-p"><col class="c-s"><col class="c-c"><col class="c-d"><col class="c-b"><col class="c-x"></colgroup>
<thead><tr><th>Protocol</th><th class="hide-s">Surface</th><th>Status</th><th class="hide-m">Delay obs / docs</th><th class="hide-m">Block / proof</th><th class="x"><span class="skip">Details</span></th></tr></thead>
<tbody data-sample="{SAMPLE_SIZE}">
{index_rows(idx)}
</tbody></table></div>
<p class="ix-more"><button type="button" class="btn" data-ix-all>Show all {c["records"]} records</button> <a href="protocols/">Browse all {len(site_protocols(idx))} protocol pages →</a> · searching or filtering loads every record from <a href="api/v1/index.json">/api/v1/index.json</a></p>
</div></section>"""


def verify_section(idx, c):
    reg, schema = idx["onchain_anchoring"]["commitment_registry"], idx["onchain_anchoring"]["eas_schema_uid"]
    cmd = (f"# 1) Pull the block-pinned index\n"
           f"curl -s {BASE_URL}/api/v1/index.json \\\n  | jq '.entries[] | {{protocol, sprint, block_number, classification}}'\n\n"
           f"# 2) Replay one record: Stader Manager Safe threshold\n"
           f'cast call 0xAAfb31780e4b9c95Bc920e388f4925A874cd07AF \\\n  "getThreshold()" \\\n  --block 26403676 --rpc-url "$ETH_RPC_URL"\n'
           f'cast block 26403676 --field hash --rpc-url "$ETH_RPC_URL"\n\n'
           f"# 3) Reference Foundry suite (offline; fork tests need ETH_RPC_URL)\n"
           f'forge test --no-match-test "testFork" -vv')
    return f"""<section class="sec" id="verify"><div class="wrap">
<div class="sec-head"><span class="n">06</span><h2>Don’t trust, verify</h2><span class="aside">Everything here replays against any archive node</span></div>
<div class="split">
<dl class="deflist">
<div><dt>{E(c["chains"])}</dt><dd>All {c["records"]} indexed records are pinned to a block number and its canonical block hash on their own chain; reads use EIP-1898 <code>requireCanonical</code>.</dd></div>
<div><dt>Open verifier spec</dt><dd>Each record lists the target contract, the full call signature and arguments (or EIP-1967 slot), the block and the block hash. Replay it with <code>cast</code> or raw <code>eth_call</code> / <code>eth_getStorageAt</code>.</dd></div>
<div><dt>On-chain anchoring on Base</dt><dd>{anchoring_text(c)} Multi-attest txs {multi_tx_html(c)} · Registry {hexref(reg)} (Sourcify verified) · EAS schema {hexref(schema)}.</dd></div>
<div><dt>Machine-readable</dt><dd><a href="api/v1/index.json">/api/v1/index.json</a> (schema <code>{E(idx["schema"])}</code>) · <a href="api/v1/radar.json">/api/v1/radar.json</a> · <a href="api/v1/onboarding.json">/api/v1/onboarding.json</a> · <a href="api/v1/proposals.json">/api/v1/proposals.json</a> · <a href="llms.txt">/llms.txt</a> · <a href="llms-full.txt">/llms-full.txt</a></dd></div>
<div><dt>For agents</dt><dd><a href=".well-known/agent.json">A2A Agent Card</a> · <a href=".well-known/mcp.json">MCP manifest</a> · <a href="SKILL.md">SKILL.md</a>. Read-only and free; optional x402 (Base USDC) live scans.</dd></div>
<div><dt>Reorg handling</dt><dd>Live monitoring uses a 64-block reorg-aware indexer: observations from orphaned blocks are retracted, never silently kept.</dd></div>
</dl>
{term(cmd, "Verify from your terminal")}
</div>
</div></section>"""


def pricing_section(idx, home=""):
    """#pricing: free for curators, risk teams and agents; paid work is for issuers only; one bar for high-throughput API users."""
    req = "#request" if home == "" else f"{home}request/"
    tq = (lambda k: "") if home == "" else (lambda k: f"?tier={k}")
    sp = site_protocols(idx)
    n_p, n_s = len(sp), sum(len(v["entries"]) for v in sp.values())
    free_lis = "".join(f"<li>{b}</li>" for b in [
        f"All {n_p} protocols ({n_s} block-pinned surfaces), live governance and timelock briefs, free and real-time; no key, no delay, no paywall",
        "Static JSON and LLM feeds: <code>/api/v1/*.json</code>, <code>llms.txt</code>, <code>llms-full.txt</code>, <code>SKILL.md</code>",
        f"<code>/v1/check/preflight</code> and the other live checks at {E(RATE_LIMIT)}; 5-minute edge cache on unpinned checks",
        f"Remote MCP ({E(REMOTE_TOOLS_DOC)}) at <code>{E(MCP_URL)}</code> and OpenAPI 3.1",
        "Curators, risk analysts, and due-diligence agents never pay"])
    free_plan = (f'<div class="plan feat"><span class="tier">Curators, Risk Teams &amp; AI Agents</span><h3>Free launch</h3>'
                 f'<div class="price">$0<small>Free · no API key · no wallet</small></div><ul>{free_lis}</ul>'
                 f'<a class="btn primary" href="{"" if home == "" else home}#preflight">Run a check in one call <span class="arr">→</span></a>'
                 f'<a class="plan-sub" href="{req}{tq("community")}" data-tier="community">Suggest a protocol for the free community queue →</a></div>')
    issuer_lis = "".join(f"<li>{b}</li>" for b in [
        "Archive-RPC control-plane verification of your proxy admins, Safes, roles and timelocks, pinned to a canonical block",
        "Upstream GitBook / docs reconciliation PR wherever documentation and on-chain state differ",
        "Base Mainnet EAS <i>Aligned</i> attestation in PactaCommitmentRegistry, clearing open <code>parameter_delta</code> flags",
        "Paste-ready Curator Diligence Dossier (PDF + JSON) for Morpho, Euler, Aave and Sky forum proposals",
        "Settle by formal commercial invoice (PDF) or directly in USDC on Base or Ethereum"])
    issuer_plan = (f'<div class="plan"><span class="tier">Collateral &amp; Protocol Issuers</span><h3>24h Onboarding &amp; Delta Clearance</h3>'
                   f'<div class="price">{E(CLEARANCE_PRICE)}<small>flat · 24h</small></div>'
                   f'<p class="addon">Then optional Continuous Aligned Maintenance: {E(MONITORING_PRICE)}</p><ul>{issuer_lis}</ul>'
                   f'<a class="btn" href="{req}{tq("clearance")}" data-tier="clearance" data-cta="pricing_clearance">Request Verification &amp; Reconciliation Dossier ({E(CLEARANCE_PRICE)}, 24h SLA) <span class="arr">→</span></a>'
                   f'<a class="plan-sub" href="{req}{tq("continuous")}" data-tier="continuous" data-cta="pricing_continuous">Continuous Aligned Maintenance ($1,500/mo) →</a></div>')
    bar = (f'<p class="plan-bar">Building a high-throughput wallet, custodian, or DeFAI agent needing &gt; 60 req/min or a dedicated SLA? '
           f'Use x402 metered endpoints or <a href="{req}{tq("api_sla")}" data-tier="api_sla" data-cta="pricing_api_sla">request an Enterprise API key →</a></p>')
    return f"""<section class="sec" id="pricing"><div class="wrap">
<div class="sec-head"><span class="n">07</span><h2>Pricing</h2><span class="aside">The API, MCP server and all public data are free. Paid work is for collateral and protocol issuers only.</span></div>
<div class="plans two">{free_plan}{issuer_plan}</div>
{bar}
{editorial_box()}
<p class="note">{E(VULN_ROUTE)}</p>
</div></section>"""


def protocol_options(idx, pinned=None):
    names = []
    for e in sorted_entries(idx):
        n = e["protocol"]
        if n not in names:
            names.append(n)
    pinned = load_pinned() if pinned is None else pinned
    names += [e["protocol"] for e in pinned["entries"] if e["protocol"] not in names]
    return sorted(set(names), key=str.lower)


def pay_panel(idx):
    """#req-pay: two settlement tracks, Option A (invoice) first and checked; app.js switches them (settlement=invoice|direct)."""
    treasury = idx["onchain_anchoring"]["treasury_admin"]
    rows = "".join(f'<dt>USDC on {k}</dt><dd>{hexref(v)}</dd>' for k, v in USDC.items())
    opts = "".join(
        f'<label class="pay-opt"><input type="radio" name="settlement" value="{k}"{" checked" if k == DEFAULT_SETTLEMENT else ""}>'
        f'<span><b>{E(h)}</b><span class="tag">{E(t)}</span><span class="sub">{E(x)}</span></span></label>'
        for k, (h, t, x, _) in SETTLEMENT.items())
    t0 = TRACKS[DEFAULT_TRACK]
    return (f'<div class="pay" id="req-pay"><span class="label">Settlement</span>'
            f'<p class="pay-sum" id="req-pay-sum">{E(t0[0])} · {E(t0[1])} {E(t0[2])}</p>'
            f'<div class="opts one settle" role="radiogroup" aria-label="Settlement track">{opts}</div>'
            f'<dl class="kv" id="req-direct"><dt>{E(TREASURY_LABEL)}</dt><dd><span class="mono full">{treasury}</span>{copy_btn(treasury)}</dd>{rows}</dl>'
            f'<p class="hint">Option B only: USDC to this externally owned account, the same address on Base and Ethereum. '
            f'Not a smart-contract wallet.</p></div>')


def request_builder(idx, home=""):
    tiers = "".join(
        f'<label><input type="radio" name="tier" value="{k}"{" checked" if k == DEFAULT_TRACK else ""}><span><b>{E(t)}</b>'
        f'{" · " + E(p) + (" " + E(u) if u else "")}<span class="sub">{E(sm)}</span></span></label>'
        for k, (t, p, u, sm, _) in TRACKS.items())
    slugs = {n: v["slug"] for n, v in site_protocols(idx).items()}
    protos = "".join(f'<label><input type="checkbox" name="protocol" value="{E(n)}"{f" data-slug={chr(34)}{slugs[n]}{chr(34)}" if n in slugs else ""}><span>{E(n)}</span></label>'
                     for n in protocol_options(idx))
    gh = f"{REPO}/issues/new?template=request-scan.yml&title=" + urllib.parse.quote("[Pacta Scope] ")
    gm = "https://mail.google.com/mail/?view=cm&fs=1&to=" + urllib.parse.quote(CONTACT) + "&su=" + urllib.parse.quote("Pacta 24h clearance request")
    return f"""<form class="req" id="req-form" autocomplete="off" data-treasury="{idx["onchain_anchoring"]["treasury_admin"]}">
<div class="req-form">
<fieldset><legend>Track</legend><div class="opts one">{tiers}</div></fieldset>
<fieldset><legend>Protocols in scope <span class="legend-note">· {len(protocol_options(idx))} indexed; add others below</span></legend><div class="opts scroll" id="req-protocols">{protos}</div></fieldset>
<div class="field"><label for="req-org">Organization or protocol</label><input id="req-org" name="org" type="text" placeholder="e.g. Example Labs, or the asset you issue"></div>
<div class="field"><label for="req-scope">Contracts, docs or portfolio</label><textarea id="req-scope" name="scope" placeholder="Public docs URL, mainnet addresses, or the collateral list you curate"></textarea><p class="hint">Public information only. Never paste keys or exploit details here.</p></div>
<div class="field" id="req-forum-field"><label for="req-forum">Forum proposal URL <span class="legend-note">· optional</span></label><input id="req-forum" name="forum" type="url" placeholder="https://… Morpho, Euler, Aave or Sky forum listing proposal"></div>
<div class="field" id="req-tx-field"><label for="req-tx">Payment transaction hash <span class="legend-note">· Option B · optional</span></label><input id="req-tx" name="tx" type="text" spellcheck="false" placeholder="0x… (Base or Ethereum)"><p class="hint" id="req-tx-hint">A 66-character hash starting with 0x.</p></div>
<div class="field"><label for="req-contact">How should we reach you?</label><input id="req-contact" name="contact" type="text" placeholder="Work email, Telegram or GitHub handle"></div>
</div>
<div class="req-out">
<span class="label">Scope brief</span>
<div class="term"><div class="term-h"><span>To: {CONTACT}</span><button class="copy" type="button" data-copy-from="req-brief" aria-label="Copy the request brief">Copy brief</button></div><pre id="req-brief">Choose a track and protocols; the brief updates as you type.</pre></div>
{pay_panel(idx)}
<div class="actions">
<a class="btn primary" id="req-gh" href="{E(gh)}" target="_blank" rel="noopener">Open a pre-filled GitHub intake issue <span class="arr">↗</span></a>
<a class="btn" id="req-gmail" href="{E(gm)}" target="_blank" rel="noopener">Compose in Gmail <span class="arr">↗</span></a>
<button class="btn" type="button" id="req-copy" data-copy-from="req-brief">Copy brief and address <span class="arr">⧉</span></button>
</div>
<p class="note">{E(VULN_ROUTE)}</p>
<p class="status" id="req-status" role="status" aria-live="polite"></p>
<div class="addrline">Or write to <b>{CONTACT}</b>{copy_btn(CONTACT, "Copy address")}</div>
</div>
</form>"""


def request_section(idx):
    return f"""<section class="sec" id="request"><div class="wrap">
<div class="sec-head"><span class="n">08</span><h2>Request coverage</h2><span class="aside">Builds a scope brief in your browser; nothing is sent until you choose a channel</span></div>
{request_builder(idx)}
</div></section>"""


def faq_section(c, r):
    qa = [
        ("What exactly is anchored on-chain?",
         f'{anchoring_text(c)} They are recorded by <code>pacta.base.eth</code> in PactaCommitmentRegistry (multi-attest txs {multi_tx_html(c)}); '
         f'each attestation commits to the sprint’s Ethereum block hash and summary SHA-256.'),
        ("Is the data free?",
         "Yes, and in real time. Every indexed record, the timelock radar, the briefs, /api/v1/index.json and llms.txt are free for vault "
         "curators, allocators and AI risk agents: no key, no delay and no paywall. Curators never pay."),
        ("What does the $5,000 clearance include?",
         "For collateral issuers onboarding an asset or clearing a <code>parameter_delta</code> flag: a canonical block-pinned control-plane audit, "
         "a GitBook / config reconciliation PR, a Base Mainnet EAS <i>Aligned</i> attestation and a Curator Diligence Dossier (PDF + JSON) "
         "ready to paste into Morpho, Euler, Aave or Sky forum proposals, in 24 hours, for $5,000 USDC flat. Continuous <i>Aligned</i> "
         "maintenance is optional at $1,500 USDC / month. Settle by formal commercial invoice (PDF) or directly in USDC."),
        ("How do I reproduce a record?",
         "Every record gives the contract, the call signature with all arguments (or the storage slot), the block and the canonical block hash. "
         "Copy its <code>cast</code> command from the inspector or the index and run it against any archive node."),
        ("What happens to exploit-sensitive findings?",
         E(VULN_ROUTE)),
        ("Do I need a wallet?",
         "No. The inspector, the radar, the briefs and the JSON feed are public and read-only. No wallet is needed for a clearance either: a commercial invoice (PDF) is the default; direct USDC settlement is optional."),
        ("How fresh is the radar?",
         f'The radar states the exact finalized block it was refreshed at (#{r["block_number"]:,}, {E(r["block_time_utc"])}); countdowns are computed '
         f'from each operation’s on-chain ETA. An ETA is when execution becomes possible, not a guarantee that it happens.'),
        ("What do the classifications mean?",
         "Parameter delta: on-chain state differs from the documentation. Protective delta: a change that strengthens controls. "
         "Aligned baseline: on-chain state matches the documentation at the pinned block."),
    ]
    items = "".join(f"<div><dt>{q}</dt><dd>{a}</dd></div>" for q, a in qa)
    return f"""<section class="sec" id="faq"><div class="wrap">
<div class="sec-head"><span class="n">09</span><h2>Questions &amp; methodology</h2></div>
<dl class="faq">{items}</dl>
</div></section>"""


def about_section(idx):
    return f"""<section class="sec" id="about"><div class="wrap">
<div class="sec-head"><span class="n">10</span><h2>About</h2></div>
<div class="about">
<p>Pacta is built by <a href="{FN}" target="_blank" rel="noopener">Fractal Neurons</a>, a research engineering firm. <i>Pacta sunt servanda</i>: agreements must be kept. We check that the people who control DeFi collateral keep the commitments their documentation makes, and we tell you before that changes.</p>
<dl class="deflist">
<div><dt>Contact</dt><dd><a href="#request">Request builder</a> · <span class="mono">{CONTACT}</span>{copy_btn(CONTACT, "Copy")}</dd></div>
<div><dt>Code &amp; data</dt><dd><a href="{REPO}" target="_blank" rel="noopener">{REPO.replace("https://", "")} ↗</a></dd></div>
<div><dt>For agents</dt><dd><a href="llms.txt">/llms.txt</a> · <a href="llms-full.txt">/llms-full.txt</a> · <a href="api/v1/proposals.json">/api/v1/proposals.json</a> · <a href=".well-known/agent.json">agent.json</a> · <a href="SKILL.md">SKILL.md</a></dd></div>
<div><dt>Security</dt><dd><a href=".well-known/security.txt">/.well-known/security.txt</a></dd></div>
</dl>
</div>
</div></section>"""


def quickstart_block():
    """Above-the-fold, copyable agent quickstarts. Remote MCP and curl come first: the npm package is not published yet."""
    claude = f"claude mcp add --transport http pacta {MCP_URL}"
    cursor = '{"mcpServers": {"pacta": {"url": "' + MCP_URL + '"}}}'
    curl = f'{CURL} "{API}/v1/check/preflight?chain=ethereum&address=0xA35b1B31Ce002FBF2058D22F30f95D405200A15b"'
    py = ('import json, urllib.request as u; r = u.Request("' + API + '/v1/check/preflight?chain=ethereum&address=0xA35b1B31Ce002FBF2058D22F30f95D405200A15b", '
          'headers={"User-Agent": "' + UA + '"}); print(json.load(u.urlopen(r))["verdict"])')
    snippet = lambda label, value: (f'<div class="qs-snip"><span class="qs-l">{label}</span><code class="mono">{E(value)}</code>{copy_btn(value)}</div>')
    return (f'<div class="qs-connect" id="connect"><h2 class="qs-h"><span class="tier">2 · Connect your agent (MCP / REST)</span></h2>'
            f'<div class="qs" aria-label="Agent quickstarts">'
            f'<div class="qs-item"><span class="tier">MCP · zero install</span><h3>Claude Code, Cursor, any MCP client</h3>'
            f'{snippet("Claude Code", claude)}{snippet("Cursor mcp.json", cursor)}{snippet("Any MCP client (Streamable HTTP)", MCP_URL)}</div>'
            f'<div class="qs-item"><span class="tier">REST · one call</span><h3>Pre-flight check</h3>{snippet("Shell", curl)}{snippet("Python (stdlib)", py)}'
            f'<p class="note">Returns a verdict, a 0–100 risk score with its confidence, proxy / admin / timelock breakdown and the pinned block. {E(UA_NOTE)}</p></div>'
            f'<div class="qs-item"><span class="tier">OpenAPI, Actions &amp; skills</span><h3>ChatGPT Actions, LangChain, skills</h3>'
            f'<p class="qs-links"><a href="{OPENAPI_URL}">openapi.json (3.1)</a><a href="SKILL.md">SKILL.md</a><a href="llms.txt">llms.txt</a>'
            f'<a href=".well-known/agent.json">agent.json</a><a href=".well-known/mcp.json">mcp.json</a></p>'
            f'<p class="note">$0 during the launch: no API key, no wallet, {E(RATE_LIMIT)}.</p></div>'
            f'</div></div>')


def hero_try(idx):
    """Visitor review P1 (first success): "1 · See a live check first" above the fold: a real pinned finding, a plain-English
    'What this tells you' and a one-click live check of the same protocol (the ETHx token; the free API cross-links the record)."""
    slug, chain, addr = HERO_EXAMPLE
    sp = site_protocols(idx)
    name, v = next((n, x) for n, x in sp.items() if x["slug"] == slug)
    wd = CD.what_differs(v["entries"])
    e = v["entries"][0]
    ch = wd["changed"][0]
    matched = "; ".join(f'{m["parameter"]} {m["value"]}' for m in wd["matched"][:2])
    head = f'{name}: the docs say {ch["documented"]}, the chain says {ch["observed"]}'
    explain = (f'Pacta read {name}\'s control plane at {CHAINS[chain][0]} block #{int(e["block_number"]):,} and compared it with the protocol\'s own '
               f'documentation. The {ch["parameter"].lower()} on-chain ({ch["observed"]}) differs from what the docs promise ({ch["documented"]})'
               + (f', while {matched.lower()} still matches' if matched else "") + '. An agent that trusts the docs alone would act on the wrong '
               f'assumption about who can change the protocol. The record is attested on Base (EAS) and every value is reproducible with cast.')
    return (f'<div class="hero-try" id="try" aria-label="See a live check first"><span class="tier">1 · See a live check first</span>'
            f'<h2 class="try-h">{E(head)}</h2>'
            f'<p class="try-finding"><span class="badge delta">Parameter delta</span> <b>Changed:</b> {E(ch["parameter"])} {E(ch["observed"])} observed vs '
            f'{E(ch["documented"])} documented' + (f' · <b>Matched:</b> {E(matched)}' if matched else "") + f' · pinned at block <span class="num">#{int(e["block_number"]):,}</span></p>'
            f'<p class="try-explain"><b>What this tells you:</b> {E(explain)}</p>'
            f'<p class="try-actions"><button class="btn primary" type="button" data-pf-chain="{chain}" data-pf-address="{addr}" data-pf-scroll>Run this check live (free, 1 click)</button>'
            f'<a class="btn" href="protocols/{slug}/">Full record →</a></p></div>')


def preflight_section():
    """Live checker: app.js calls the free API on an explicit click and renders text only (textContent)."""
    presets = "".join(f'<button class="btn sm" type="button" data-pf-chain="{c}" data-pf-address="{a}">{E(l)}</button>' for l, c, a in PREFLIGHT_PRESETS)
    return f"""<section class="sec" id="preflight"><div class="wrap">
<div class="sec-head"><span class="n">00</span><h2>Live pre-flight check</h2><span class="aside">The contract check runs only when you press Run (free API at {E(API)}). Pages count anonymous first-party aggregate pageviews: no cookies, no IP stored.</span></div>
<div class="pf" data-api="{API}">
<form class="pf-form" id="pf-form" autocomplete="off"><label>Chain<select name="chain"><option value="ethereum">Ethereum</option><option value="base">Base</option></select></label>
<label class="pf-addr">Contract address<input type="text" name="address" placeholder="0x…" maxlength="42" spellcheck="false" required></label>
<button class="btn primary" type="submit">Run pre-flight</button></form>
<div class="pf-presets"><span>Try:</span>{presets}</div>
<div class="pf-out" id="pf-out" aria-live="polite"><p class="note">The verdict, risk score, proxy, admin and timelock breakdown and the <code>cast</code> commands to verify it appear here.</p></div>
<noscript><p class="note">Without JavaScript, use the curl command above.</p></noscript>
</div>
</div></section>"""


# A protocol whose published name does not slug to its published slug (an RPC-pinned page converted to EAS-attested keeps
# both its name and its /protocols/ slug, so its graph anchor and page never change).
SLUG_OVERRIDES = {"Frax Ether (frxETH / sfrxETH)": "frax-ether-sfrxeth", "Re Protocol (reUSD / reUSDe)": "re",
                  "Balancer V2 Vault & TimelockAuthorizer": "balancer-v2-vault-timelock"}


def protocol_slug(name):
    return SLUG_OVERRIDES.get(name) or re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def protocol_groups(idx):
    groups = {}
    for e in idx["entries"]:
        groups.setdefault(e["protocol"], []).append(e)
    return {k: sorted(v, key=lambda e: (e["sprint"], e["id"])) for k, v in sorted(groups.items(), key=lambda kv: kv[0].lower())}


def radar_for(name, radar):
    key = name.lower()
    return [it for it in radar["items"] if it["protocol"].lower() in key or key.startswith(it["protocol"].lower())]


# ---- governance forum digest (read-only; CONTRACTS §3) ---------------------------------------------------------------
# Optional source data/forum-digest.json (written by the read-only Discourse poller). Missing = empty digest. The build
# republishes it at /api/v1/forum-digest.json with an addressIndex that lets the gateway attach discussions to a
# preflight response. Deterministic: no wall clock; ordering and filtering depend only on the inputs.
FORUM_DIGEST_SRC = os.path.join(ROOT, "data", "forum-digest.json")
FORUM_SCHEMA = "pacta.forum_digest.v1"
FORUM_FAMILIES = ("aave", "euler", "morpho", "sky", "compound", "lido", "arbitrum", "uniswap", "curve", "frax")
# The family is the first word of the protocol name, lowercased. Two indexed names start with a word that is not the
# forum family that governs them: MetaMorpho vaults (Morpho forum) and Spark (a Sky star; forum.sky.money).
FAMILY_ALIAS = {"metamorpho": "morpho", "spark": "sky"}
GOV_MAX = 5
_ISO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})")
_HOST = re.compile(r"[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+")


def protocol_family(name):
    words = re.findall(r"[a-z0-9]+", name.lower())
    w0 = words[0] if words else ""
    return FAMILY_ALIAS.get(w0, w0)


def empty_forum_digest():
    return {"schema": FORUM_SCHEMA, "generatedAt": None, "readOnly": True, "forums": {}, "discussions": []}


def _iso_or_none(v):
    return v if isinstance(v, str) and _ISO.fullmatch(v) else None


def _int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def _discussion(d):
    """One validated discussion (known keys only) or None. The url must be https on the discussion's own forum host."""
    if not isinstance(d, dict):
        return None
    forum, proto, tid, title, url = d.get("forum"), d.get("protocol"), _int(d.get("topicId")), d.get("title"), d.get("url")
    if not (isinstance(forum, str) and _HOST.fullmatch(forum) and isinstance(proto, str) and re.fullmatch(r"[a-z0-9-]{1,40}", proto)
            and tid is not None and isinstance(title, str) and title.strip() and isinstance(url, str)):
        return None
    pu = urllib.parse.urlsplit(url)
    if pu.scheme != "https" or pu.hostname != forum or pu.username or pu.password or pu.port:
        return None
    strs = lambda v: sorted({x.strip() for x in v if isinstance(x, str) and x.strip()})[:12] if isinstance(v, list) else []
    return {"forum": forum, "protocol": proto, "topicId": tid, "title": " ".join(title.split())[:300], "url": url,
            "createdAt": _iso_or_none(d.get("createdAt")), "lastPostedAt": _iso_or_none(d.get("lastPostedAt")),
            "postsCount": _int(d.get("postsCount")) or 0, "tags": strs(d.get("tags")), "riskTerms": strs(d.get("riskTerms"))}


def normalize_forum_digest(src):
    """Validate a pacta.forum_digest.v1 document; drop malformed discussions; deterministic order (forum, topicId)."""
    if not isinstance(src, dict) or src.get("schema") != FORUM_SCHEMA:
        raise ValueError(f"forum digest: schema must be {FORUM_SCHEMA}")
    forums = {}
    for host, f in sorted((src.get("forums") or {}).items()):
        if isinstance(host, str) and _HOST.fullmatch(host) and isinstance(f, dict) and isinstance(f.get("protocol"), str):
            forums[host] = {"protocol": f["protocol"], "lastPolledAt": _iso_or_none(f.get("lastPolledAt"))}
    seen, ds = set(), []
    for d in src.get("discussions") or []:
        n = _discussion(d)
        if n and (n["forum"], n["topicId"]) not in seen:
            seen.add((n["forum"], n["topicId"]))
            ds.append(n)
    ds.sort(key=lambda d: (d["forum"], d["topicId"]))
    return {"schema": FORUM_SCHEMA, "generatedAt": _iso_or_none(src.get("generatedAt")), "readOnly": True, "forums": forums, "discussions": ds}


def load_forum_digest(path=None):
    path = path or FORUM_DIGEST_SRC
    if not os.path.exists(path):
        return empty_forum_digest()
    with open(path) as fh:
        return normalize_forum_digest(json.load(fh))


def address_index(idx, pinned=None):
    """{"<chain>:0x<lower 40 hex>": family} from every target_contract in index.json (chain ethereum unless the entry says Base)
    and every RPC-pinned record's target and paired protocol contract (their own chain)."""
    pinned = load_pinned() if pinned is None else pinned
    out = {}
    for e in sorted(idx["entries"], key=lambda e: e["id"]) + sorted(pinned["entries"], key=lambda e: e["id"]):
        for a in (e.get("target_contract"), e.get("paired_contract")):
            a = str(a or "").lower()
            if not re.fullmatch(r"0x[0-9a-f]{40}", a):
                continue
            chain = "base" if str(e.get("chain", "")).lower() == "base" or e.get("chain_id") == 8453 else "ethereum"
            out.setdefault(f"{chain}:{a}", protocol_family(e["protocol"]))
    return dict(sorted(out.items()))


def forum_digest_doc(idx, digest, pinned=None):
    d = normalize_forum_digest(digest)
    d["addressIndex"] = address_index(idx, pinned)
    return d


def forum_digest_json(idx, digest, pinned=None):
    return json.dumps(forum_digest_doc(idx, digest, pinned), indent=2, ensure_ascii=False) + "\n"


def governance_discussions(name, digest):
    """At most GOV_MAX discussions of the protocol's family, newest lastPostedAt first (ties: higher topicId first)."""
    fam = protocol_family(name)
    ds = [d for d in normalize_forum_digest(digest)["discussions"] if d["protocol"] == fam]
    return sorted(ds, key=lambda d: (d["lastPostedAt"] or "", d["topicId"], d["forum"]), reverse=True)[:GOV_MAX]


def governance_section(name, digest, home="../../"):
    ds = governance_discussions(name, digest)
    if not ds:
        return ""
    rows = ""
    for d in ds:
        meta = f'{d["forum"]} · {d["postsCount"]} post{"" if d["postsCount"] == 1 else "s"}' + (f' · {", ".join(d["riskTerms"])}' if d["riskTerms"] else "")
        rows += (f'<tr><td><a href="{E(d["url"])}" target="_blank" rel="noopener nofollow">{E(d["title"])} ↗</a>'
                 f'<br><span class="muted">{E(meta)}</span></td><td class="num">{E((d["lastPostedAt"] or "—")[:10])}</td></tr>')
    hosts = ", ".join(sorted({d["forum"] for d in ds}))
    return (f'<section class="memo-sec" id="governance"><h2>Active governance discussions</h2>'
            f'<p>Most recently active public topics on {E(hosts)}, from a read-only digest '
            f'(<a href="{home}api/v1/forum-digest.json">/api/v1/forum-digest.json</a>). Pacta reads these forums and never posts to them.</p>'
            f'<div class="tbl-wrap"><table><thead><tr><th>Topic</th><th>Last post</th></tr></thead><tbody>{rows}</tbody></table></div></section>\n')


CONTROLLER_KIND = {"multisig_safe": "Safe", "timelock": "Timelock", "contract_controller": "Contract"}


def controller_dd(e):
    """Who controls an RPC-pinned record's target, as observed (kind, address, Safe quorum, owner of a controller contract)."""
    a, k, q, up = e.get("controller_address"), e.get("controller_kind"), e.get("safe_quorum"), e.get("upstream_controller")
    if not a:
        return "No single-key owner or admin getter (immutable or role-scoped modules)"
    lbl = f"{q} Safe" if k == "multisig_safe" and q else CONTROLLER_KIND.get(k, "Contract")
    out = f"{E(lbl)} {hexref(a)}"
    if up:
        uk = e.get("upstream_kind")
        ulbl = f"{q} Safe" if uk == "multisig_safe" and q else CONTROLLER_KIND.get(uk, "contract")
        out += f" · owned by {E(ulbl)} {hexref(up)}"
    return out


# ---- issuer conversion callouts (briefs + protocol pages) ----
# /request/?tier=…&protocol=<slug>[&forum=<url>][&settlement=invoice]: app.js prefills the request builder from these
# (closed enums, sanitised text, .value only). Aligned records never get a delta-remediation pitch.
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
# radar briefs -> the protocol page of the issuer they concern (the request builder checks that protocol)
BRIEF_PROTOCOL = {"ethena-ops-0x0ca0-0x1fe5": "ethena-usde-susde", "etherfi-op-0x244e": "ether-fi-core-eeth-weeth",
                  "treehouse-op-0x2f11": "treehouse-tree-teth"}


def request_href(tier, slug, forum=None, settlement=None, home="../../"):
    assert tier in TRACKS and SLUG_RE.fullmatch(slug), (tier, slug)
    q = f"tier={tier}&protocol={slug}"
    if forum:
        assert forum.startswith("https://") and len(forum) <= 300 and "@" not in forum.split("/")[2], forum
        q += "&forum=" + urllib.parse.quote(forum, safe="")
    if settlement:
        assert settlement in SETTLEMENT
        q += "&settlement=" + settlement
    return f"{home}request/?{q}"


def is_aligned_page(entries):
    """Only pages whose every record is an EAS-attested aligned_baseline get the maintenance (not the clearance) callout."""
    return all(e["classification"] == "aligned_baseline" and not is_pinned(e) for e in entries)


DOSSIER_CTA = "Request Verification & Reconciliation Dossier (24h SLA — resulting classification strictly follows verified on-chain & documentation evidence)"
FREE_NOTIFY_CTA = "Send a free public doc-update notification"


def clearance_callout(name, slug, forum=None, home="../../"):
    """Issuer path on delta / RPC-observed pages: the paid dossier buys verification work, never an outcome; the free public
    notification path sits next to it with equal weight."""
    return (f'<section class="memo-sec convert" id="issuer-clearance"><span class="label">For issuers and maintainers</span>'
            f'<h2>Maintaining {E(name)}? Verify and reconcile the record</h2>'
            f'<p>Two paths, both public. A free doc-update notification asks the maintainers to correct the documentation or the '
            f'on-chain parameter; anyone can send it. A Verification &amp; Reconciliation Dossier ({E(CLEARANCE_PRICE)} flat, 24h SLA) '
            f're-reads the multisig and timelock control planes on archive RPCs and prepares an upstream docs reconciliation PR. '
            f'Either way the classification only changes when the on-chain state or the documentation aligns at a new finalized block.</p>'
            f'<div class="convert-cta"><a class="btn" href="{E(request_href("community", slug, forum, home=home))}" data-cta="free_notify">'
            f'{E(FREE_NOTIFY_CTA)} <span class="arr">→</span></a>'
            f'<a class="btn" href="{E(request_href("clearance", slug, forum, home=home))}" data-cta="clearance">'
            f'{E(DOSSIER_CTA)} <span class="arr">→</span></a></div>'
            f'<p class="s">Need procurement paperwork? <a href="{E(request_href("clearance", slug, forum, "invoice", home))}" data-cta="clearance_invoice">'
            f'Request a commercial invoice (PDF)</a>.</p></section>\n')


def maintenance_callout(name, slug, home="../../"):
    return (f'<section class="memo-sec convert quiet" id="aligned-maintenance">'
            f'<h2>Operating {E(name)}? Maintain Continuous Aligned Status</h2>'
            f'<p>Keep your Base EAS Aligned Attestation and Curator Diligence Dossier continuously updated across governance proposals, '
            f'signer rotations, and timelock upgrades ($1,500 USDC/mo).</p>'
            f'<p class="convert-cta"><a href="{E(request_href("continuous", slug, home=home))}" data-cta="continuous">Request Continuous Aligned Maintenance ($1,500/mo) →</a>'
            f'<a href="{E(request_href("continuous", slug, settlement="invoice", home=home))}" data-cta="continuous_invoice">Invoice option</a></p></section>\n')


def snippet(text, title, label):
    return (f'<div class="term"><div class="term-h"><span>{E(title)}</span>'
            f'<button class="copy" type="button" data-copy-term aria-label="{E(label)} ({E(title)})">{E(label)}</button></div><pre>{E(text)}</pre></div>')


def badge_section(name, slug, tier):
    """Control-plane badge on protocol pages: an embed card when aligned, the amber status + clearance path when a delta.
    RPC-observed pages carry no badge card (their slate badge exists but makes no documentation claim)."""
    label = LK.BADGE_TIERS[tier][0]
    width = (len(LK.BADGE_TITLE) + len(label)) * 7 + 24
    img = f'<img class="cp-badge" src="../../badges/{slug}.svg" alt="{E(LK.BADGE_TITLE)}: {E(label)}" width="{width}" height="20">'
    live = f"{API}/v1/badges/{slug}.svg"
    if tier == "aligned":
        md = f"[![{LK.BADGE_TITLE}]({BASE_URL}/badges/{slug}.svg)]({BASE_URL}/protocols/{slug}/)"
        htm = f'<a href="{BASE_URL}/protocols/{slug}/"><img src="{BASE_URL}/badges/{slug}.svg" alt="{LK.BADGE_TITLE}: {label}" height="20"></a>'
        return (f'<section class="memo-sec badge-card" id="embed-badge"><h2>Embed Live Control-Plane Badge</h2>'
                f'<p class="badge-preview">{img}</p>'
                f'<p>Show {E(name)}\'s Base-EAS-attested <i>Aligned</i> control-plane status in a README, docs page or forum post. The badge links back to this record.</p>'
                f'{snippet(md, "Markdown", "Copy Markdown")}{snippet(htm, "HTML", "Copy HTML")}'
                f'<p class="s">Static badge: <code>{E(BASE_URL)}/badges/{E(slug)}.svg</code> (rebuilt with the site). Live edge badge: '
                f'<code>{E(live)}</code> (5-minute cache).</p></section>\n')
    if tier == "parameter_delta":
        href = request_href("clearance", slug, settlement="invoice")
        return (f'<section class="memo-sec badge-card delta" id="badge-status"><h2>Control-plane badge: Parameter Delta</h2>'
                f'<p class="badge-preview">{img}</p>'
                f'<p>This badge is amber because at least one Base-EAS-attested surface of {E(name)} differs from what the protocol documents. '
                f'It turns to the emerald <b>Aligned · Base EAS</b> shield only when the on-chain state or the documentation changes and '
                f'the two match at a new finalized block, whoever requests the re-check.</p>'
                f'<p><a class="btn" href="{E(request_href("community", slug))}" data-cta="badge_free_notify">{E(FREE_NOTIFY_CTA)} <span class="arr">→</span></a></p>'
                f'<p class="s">Badge: <code>{E(BASE_URL)}/badges/{E(slug)}.svg</code> · live: <code>{E(live)}</code>.</p></section>\n')
    return ""


BOUNTY_SUBMISSIONS_DIR = os.path.join(ROOT, "bounties", "submissions")


def bounty_credit(slug, lb=None, sub_dir=None):
    """The merged Wave 1 catch whose fixture names this published protocol (pactaSlug), with its hunter / PR / payout from the
    settlement ledger; None when no merged fixture points here. A fixture's pactaSlug is set only once a Sprint indexes the protocol
    (tools/apply_sprint<N>_attestation.py), so the credit appears together with the attested records."""
    d = sub_dir or BOUNTY_SUBMISSIONS_DIR
    hits = []
    for f_name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f_name.startswith("slot-") and f_name.endswith(".json"):
            f = json.load(open(os.path.join(d, f_name), encoding="utf-8"))
            if f.get("pactaSlug") == slug:
                hits.append(f)
    if not hits:
        return None
    assert len(hits) == 1, f"{slug}: {len(hits)} merged Wave 1 fixtures name this protocol"
    lb = lb or load_leaderboard()
    s = next(x for x in lb["wave1Settlements"] if x["slot"] == hits[0]["slot"])
    assert s["status"] == "verified" and hits[0].get("apacheGrant") is True, f"{slug}: credit needs a verified, Apache-2.0-granted catch"
    return {"slot": s["slot"], "hunter": s["hunter"], "pr": s["pr"], "payoutTxHash": s["payoutTxHash"] if tx_ok(s["payoutTxHash"]) else None}


def research_credit_html(slug, credit):
    """Provenance section crediting the researcher (EAS-attested pages only; the records stay Pacta's own pinned re-reads)."""
    if not credit:
        return ""
    h, pr, slot, tx = credit["hunter"], credit["pr"], credit["slot"], credit["payoutTxHash"]
    paid = (f' and paid $25.00 USDC (<a href="https://basescan.org/tx/{E(tx)}" target="_blank" rel="noopener" data-basescan-tx>tx {E(short(tx, 6, 4))} ↗</a>)'
            if tx else "")
    return (f'<section class="memo-sec" id="provenance" data-research-credit="{E(h)}"><h2>Provenance · research credit</h2>'
            f'<p>First reported by <a href="https://github.com/{E(h)}" target="_blank" rel="noopener">@{E(h)}</a> through the Pacta Wave 1 bounty '
            f'(<a href="{E(REPO)}/pull/{int(pr)}" target="_blank" rel="noopener">Slot #{int(slot)}, PR #{int(pr)}</a>), merged under the Apache-2.0 '
            f'grant{paid}. Pacta then re-read every value below on two independent RPCs at its own Sprint pin and compared it with the '
            f'documentation; the classifications and the Base EAS attestation are Pacta\'s. '
            f'See <a href="../../leaderboard/">the leaderboard</a>.</p></section>\n')


def protocol_page(name, entries, idx, radar, digest=None, slug=None):
    """Static, deterministic protocol safety record (no wall-clock time): every indexed surface with its pinned block.
    index.json Sprint records (Base-EAS-anchored) and RPC-pinned records (not EAS-attested) are labelled as such."""
    digest = load_forum_digest() if digest is None else digest
    slug = slug or protocol_slug(name)
    url = f"{BASE_URL}/protocols/{slug}/"
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    cat = entries[0]["category"]
    targets = sorted({e["target_contract"] for e in entries})
    first = entries[0]
    pinned = all(is_pinned(e) for e in entries)
    assert pinned or not any(is_pinned(e) for e in entries), f"{name}: mixed provenance"
    chains = sorted({e.get("chain", "ethereum") for e in entries}, key=list(CHAINS).index)
    chain_txt = " and ".join(CHAINS[ch][0] for ch in chains)
    n = len(entries)
    records = ""
    for e in entries:
        ch = CHAINS[e.get("chain", "ethereum")][0]
        prov = "RPC-pinned, not EAS-attested" if pinned else f'sprint {E(str(e["sprint"]))}'
        ctrl = f'<dt>Controller</dt><dd>{controller_dd(e)}</dd>' if pinned else ""
        doc_lbl = "Documentation (linked, not compared)." if pinned else "Documented."
        records += (f'<article class="memo-sec" id="{E(e["id"])}"><h2>{E(e["surface"])}</h2>'
                    f'<dl class="memo-meta"><dt>Status</dt><dd>{badge(e["classification"])}</dd>'
                    f'<dt>Target</dt><dd>{E(e["target_label"])} {hexref(e["target_contract"])} · {explorer_link(e, "address")}</dd>'
                    f'<dt>Pinned block</dt><dd>{ch} <span class="num">#{int(e["block_number"]):,}</span> · {explorer_link(e)} · {prov}</dd>'
                    f'<dt>Block hash</dt><dd>{hexref(e["block_hash"], 10, 6)}</dd>{ctrl}</dl>'
                    f'<p><b>Observed on-chain.</b> {E(e["onchain_observed"])}</p>'
                    f'<p><b>{doc_lbl}</b> {E(e["documented_reference"])}</p>'
                    f'{term(cast_line(e))}</article>\n')
    ops = ""
    for it in radar_for(name, radar):
        lis = "".join(f'<li><code class="mono">{E(o["op_id"])}</code> · {"ETA " + E(utc(o["eta"], True)) if o.get("eta") else "executed on-chain (isOperationDone = true)"} · {state_badge(op_state(o), [o])}</li>'
                      for o in it["operations"])
        ops += (f'<article class="memo-sec"><h2>Queued timelock operations</h2><p>{E(it["title"])}. {E(it["summary"])}</p>'
                f'<p>Timelock {hexref(it["timelock"])} · {secs(it["min_delay_seconds"])} minimum delay · <a href="../../{E(it["brief"])}">Pre-execution brief →</a></p>'
                f'<ul>{lis}</ul></article>\n')
    provenance = ""
    if pinned:
        provenance = (f'<section class="memo-sec" id="provenance"><h2>Provenance</h2><p>RPC-pinned {"record" if n == 1 else "records"}: read over public '
                      f'JSON-RPC at the {chain_txt} block shown below and independently re-read at the same block by a second Pacta seat. '
                      f'{"It is" if n == 1 else "They are"} <b>not EAS-attested</b>: no sprint number, no summary document and no Base EAS UID. '
                      f'Status <b>RPC-observed baseline</b>: the on-chain control plane is pinned at block height; whether it matches the '
                      f'protocol\'s documented parameters is <b>not assessed</b> here (the documentation is linked for reference). '
                      f'Machine-readable: <a href="../../api/v1/rpc-pinned.json">/api/v1/rpc-pinned.json</a>. The Base-EAS-attested Sprint records '
                      f'are in <a href="../../api/v1/index.json">/api/v1/index.json</a>.</p></section>\n')
    else:
        provenance = research_credit_html(slug, bounty_credit(slug))
    curl = f'{CURL} "{API}/v1/check/preflight?chain={first.get("chain", "ethereum")}&address={first["target_contract"]}"'
    surfaces = f'{n} indexed {"surface" if n == 1 else "surfaces"}'
    data_url = f"{BASE_URL}/api/v1/rpc-pinned.json" if pinned else f"{BASE_URL}/api/v1/index.json"
    ld = {"@context": "https://schema.org", "@type": "Dataset", "name": f"{name} control-plane safety record",
          "description": f"Block-pinned control-plane observations for {name} ({cat}): proxy admins, Safe quorums, roles and timelock delays, "
                         + (f"read over public JSON-RPC (RPC-pinned; not EAS-attested). {surfaces}." if pinned
                            else f"compared with the protocol's documentation. {surfaces}."),
          "url": url, "isAccessibleForFree": True, "keywords": [name, cat, "DeFi", "control plane", "timelock", "proxy admin", "Safe multisig"],
          "creator": {"@type": "Organization", "name": "Pacta by Fractal Neurons", "url": f"{BASE_URL}/"},
          "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": data_url}],
          "variableMeasured": [e["surface"] for e in entries],
          "spatialCoverage": "; ".join(CHAINS[ch][1] for ch in chains),
          "temporalCoverage": f"block {min(int(e['block_number']) for e in entries)}/{max(int(e['block_number']) for e in entries)}"}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Pacta", "item": f"{BASE_URL}/"},
        {"@type": "ListItem", "position": 2, "name": "Protocols", "item": f"{BASE_URL}/protocols/"},
        {"@type": "ListItem", "position": 3, "name": name, "item": url}]}
    ld_json = json.dumps(ld, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    crumbs_json = json.dumps(crumbs, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    title = f"{name}: control-plane safety record"
    desc = (f"Who can upgrade, pause or change {name}: {n} block-pinned control-plane {'check' if n == 1 else 'checks'} with "
            f"{'a cast reproduction' if n == 1 else 'cast reproductions'} and a free live pre-flight API.")
    pin_clause = (f"with its controller and timelock state pinned to a canonical {chain_txt} block over archive JSON-RPC (not EAS-attested; "
                  f"documentation parameters are linked, not compared)" if pinned
                  else f"{'' if n == 1 else 'each '}pinned to a canonical {chain_txt} block and compared with what the protocol documents")
    codes = ", ".join(f'<code class="mono">{E(t)}</code>' for t in targets)
    lede = (f'{n} indexed control-plane {"surface" if n == 1 else "surfaces"} for {E(name)}, {pin_clause}. '
            f'{"Contract" if len(targets) == 1 else "Contracts"}: {codes}.')
    forum = first.get("governance_url") if pinned else None
    tier = "rpc_observed" if pinned else ("aligned" if is_aligned_page(entries) else "parameter_delta")
    badge_html = badge_section(name, slug, tier)
    if is_aligned_page(entries):
        callout = maintenance_callout(name, slug)
        foot = f'<a href="{E(request_href("continuous", slug))}">Maintain Aligned status · {E(MONITORING_PRICE)} →</a>'
    else:
        callout = clearance_callout(name, slug, forum)
        foot = f'<a href="{E(request_href("clearance", slug, forum))}">Verification &amp; Reconciliation Dossier (24h SLA) →</a>'
    body = f"""<body>
{topbar("../../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../../">Pacta</a> / <a href="../">Protocols</a> / {E(name)}</div>
<article class="memo">
<header><span class="tier">{E(cat)}</span><h1>{E(title)}</h1>
<p class="lede">{lede}</p></header>
{what_differs_html(entries)}<section class="memo-sec"><h2>Check it live (free)</h2><p>The pre-flight API re-reads the controller, proxy and capabilities of a contract at the latest block. No key, no wallet.</p>
{term(curl, "Live pre-flight check")}<p>MCP: <code class="mono">{E(MCP_URL)}</code> · tool <code>pacta_check_preflight</code>. {E(UA_NOTE)}</p></section>
{provenance}{governance_section(name, digest)}{records}{ops}{editorial_box()}{badge_html}{callout}</article>
<div class="memo-foot"><span>Read-only on-chain analysis. Not investment advice. Exploit-sensitive vulnerabilities are never published here; they go through Immunefi or Cantina bounty programmes.</span>{foot}</div>
</main>
{footer(count_line, reg, "../../")}
<script type="application/ld+json">{ld_json}</script>
<script type="application/ld+json">{crumbs_json}</script>
</body></html>
"""
    return head(f"{name} control-plane safety · Pacta", desc, url, prefix="../../", og_title=title, og_type="article") + "\n" + body


def protocols_index_page(idx, sp=None):
    """/protocols/: every published protocol page (index.json Sprint protocols + RPC-pinned protocols), with provenance."""
    sp = site_protocols(idx) if sp is None else sp
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    n_surf = sum(len(v["entries"]) for v in sp.values())
    n_pin = sum(len(v["entries"]) for v in sp.values() if v["pinned"])

    def prov(v):
        if v["pinned"]:
            return '<span class="muted">RPC-pinned</span>'
        ss = sorted({e["sprint"] for e in v["entries"]})
        return f'Sprint{"s" if len(ss) > 1 else ""} {", ".join(str(x) for x in ss)} · Base EAS'

    def tier(v):
        return "rpc_observed" if v["pinned"] else ("aligned" if is_aligned_page(v["entries"]) else "parameter_delta")

    def attrs(n, v):
        chains = " ".join(sorted({e.get("chain", "ethereum") for e in v["entries"]}))
        text = " ".join([n, v["slug"], v["entries"][0]["category"], chains] + [e["target_contract"] for e in v["entries"]]).lower()
        bk = " ".join(baskets_of(v["entries"][0]["category"], chains.split()))
        return f' data-ptier="{tier(v)}" data-pchains="{E(chains)}" data-pbaskets="{bk}" data-psearch="{E(text)}"'

    n_tier = {t: sum(tier(v) == t for v in sp.values()) for t in ("aligned", "parameter_delta", "rpc_observed")}
    n_chain = {ch: sum(any(e.get("chain", "ethereum") == ch for e in v["entries"]) for v in sp.values()) for ch in ("ethereum", "base")}
    status = [("all", "All", len(sp)), ("aligned", "Aligned", n_tier["aligned"]), ("parameter_delta", "Parameter Delta", n_tier["parameter_delta"]),
              ("rpc_observed", "RPC-Observed", n_tier["rpc_observed"])]
    chain_pills = [("all", "All chains", len(sp)), ("ethereum", "Ethereum", n_chain["ethereum"]), ("base", "Base", n_chain["base"])]
    group = lambda kind, label, pills: (f'<div class="seg" role="group" aria-label="{label}" data-pgroup="{kind}"><span class="seg-l">{label}</span>'
                                        + "".join(f'<button type="button" data-pfilter-{kind}="{k}" aria-pressed="{"true" if k == "all" else "false"}">{E(lbl)}'
                                                  f'<span class="num">{cnt}</span></button>' for k, lbl, cnt in pills) + '</div>')
    # Visitor review P1 (discovery): Status x Chain x search, combinable; "Clear all" resets all three; 0 matches -> recovery prompt (app.js)
    tools = (f'<div class="ix-tools" data-pfilter-root><input id="proto-q" type="search" placeholder="Filter by name, token, category or 0x address" '
             f'aria-label="Filter protocols" autocomplete="off">{group("status", "Status", status)}{group("chain", "Chain", chain_pills)}'
             f'{basket_pills("data-pfilter-basket")}'
             f'<button type="button" class="linkish" id="proto-clear" hidden>Clear all</button>'
             f'<span class="ix-count" id="proto-count" aria-live="polite">{len(sp)} of {len(sp)} protocols shown</span>'
             f'<p class="ix-active" id="proto-active" aria-live="polite"></p></div>'
             f'<div class="ix-empty" id="proto-empty" hidden></div>')
    rows = "".join(f'<tr{attrs(n, v)}><td><a href="{v["slug"]}/">{E(n)}</a></td><td>{E(v["entries"][0]["category"])}</td>'
                   f'<td>{" · ".join(sorted({CHAINS[e.get("chain", "ethereum")][0] for e in v["entries"]}))}</td><td class="num">{len(v["entries"])}</td>'
                   f'<td>{" ".join(badge(cl) for cl in sorted({e["classification"] for e in v["entries"]}))}</td><td>{prov(v)}</td></tr>' for n, v in sp.items())
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Pacta by Fractal Neurons: protocol control-plane safety records", "numberOfItems": len(sp),
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE_URL}/protocols/{v['slug']}/", "name": n}
                              for i, (n, v) in enumerate(sp.items())]}
    ld_json = json.dumps(ld, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    body = f"""<body>
{topbar("../")}
<main id="main">
<section class="sec"><div class="wrap">
<div class="crumbs"><a href="../">Pacta</a> / Protocols</div>
<div class="sec-head"><span class="n">→</span><h1>Protocol safety records</h1><span class="aside">{len(sp)} protocols · {n_surf} block-pinned surfaces</span></div>
<p class="sec-intro">Who can upgrade, pause or change each protocol, pinned to canonical Ethereum and Base blocks. The {c["records"]} Sprint records are anchored on Base by EAS attestations; the {n_pin} RPC-pinned records are reproducible with <code>cast</code> but not yet EAS-attested. Check any other contract live and free with <code>/v1/check/preflight</code>.</p>
{tools}
<table class="ix" id="proto-table"><thead><tr><th>Protocol</th><th>Category</th><th>Chain</th><th>Surfaces</th><th>Status</th><th>Provenance</th></tr></thead><tbody>{rows}</tbody></table>
</div></section>
</main>
{footer(count_line, reg, "../")}
<script type="application/ld+json">{ld_json}</script>
</body></html>
"""
    return head("Protocol control-plane safety records · Pacta", f"Block-pinned control-plane safety records for {len(sp)} DeFi protocols.",
                f"{BASE_URL}/protocols/", prefix="../", og_title="Protocol control-plane safety records") + "\n" + body


def not_found_page(idx, sp=None):
    """docs/404.html: GitHub Pages serves it for any missing path, so every link is root-relative. data-nf on <main>
    makes the beacon (b.js) send not_found_404 (sanitised path, plus the slug for /protocols/<slug>/...) instead of page_load."""
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    n_protocols = len(site_protocols(idx) if sp is None else sp)
    claude = f"claude mcp add --transport http pacta {MCP_URL}"
    snippet = lambda label, value: f'<div class="qs-snip"><span class="qs-l">{label}</span><code class="mono">{E(value)}</code>{copy_btn(value)}</div>'
    body = f"""<body>
{topbar("/")}
<main id="main" class="memo-wrap" data-nf>
<div class="crumbs"><a href="/">Pacta</a> / Page not found</div>
<article class="memo">
<header><span class="tier">404 · Not found</span><h1>This page does not exist</h1>
<p class="lede">The link may be old or mistyped. Everything Pacta publishes is free and one click away.</p></header>
<section class="memo-sec"><h2>Where to go</h2>
<dl class="deflist">
<div><dt><a href="/protocols/">Protocol safety records →</a></dt><dd>Block-pinned control-plane records for {n_protocols} DeFi protocols, each with a <code>cast</code> reproduction.</dd></div>
<div><dt><a href="/#preflight">Run a free pre-flight check →</a></dt><dd>Who can upgrade, pause or change any contract on Ethereum or Base. No key, no wallet.</dd></div>
<div><dt><a href="/request/">Request coverage →</a></dt><dd>Issuers: a 24h onboarding &amp; delta clearance or continuous Aligned maintenance. High-throughput API SLAs.</dd></div>
<div><dt>For agents</dt><dd><a href="/llms.txt">llms.txt</a> · <a href="/SKILL.md">SKILL.md</a> · <a href="/.well-known/agent.json">agent.json</a> · <a href="/api/v1/index.json">/api/v1/index.json</a></dd></div>
</dl></section>
<section class="memo-sec"><h2>Remote MCP server (free)</h2>
<p>Six read-only inspection tools + one opt-in coverage / feature request tool (<code>pacta_submit_request</code>) over Streamable HTTP, zero install, led by <code>pacta_lookup_protocol</code> (resolve a protocol or token name first). Tool <code>pacta_check_preflight</code> runs the same check as the live checker on the homepage.</p>
{snippet("Any MCP client (Streamable HTTP)", MCP_URL)}{snippet("Claude Code", claude)}</section>
</article>
</main>
{footer(count_line, reg, "/")}
</body></html>
"""
    return head("Page not found · Pacta", "This page does not exist. Pacta: free pre-execution contract checks for AI agents.", f"{BASE_URL}/404.html",
                prefix="/", og_title="Page not found · Pacta", robots=ROBOTS_META_404) + "\n" + body


def page(idx, radar):
    c = counts(idx)
    r = radar["refreshed_at"]
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    later = [it for it in radar["items"] if it["eta"] and it["eta"] > r["block_timestamp"]]
    nxt = min(later or [it for it in radar["items"] if it.get("eta")] or radar["items"], key=lambda it: it.get("eta") or 0)
    n_ops = sum(len(it["operations"]) for it in radar["items"])
    n_ready = sum(op_state(o) == "ready" for it in radar["items"] for o in it["operations"])
    body = f"""<body>
{topbar()}
<main id="main">
<section class="hero"><div class="wrap">
<div class="eyebrow">For AI agents, agent builders, vault curators and risk teams</div>
<h1>{E(H1)}</h1>
<p class="statbar" data-statbar><b>{len(site_protocols(idx))}</b> protocols · <b>{c["records"]}</b> block-pinned checks · <b>{len({e["protocol"] for e in idx["entries"]})}</b> Base-EAS attested</p>
<form class="hero-check" data-hero-check autocomplete="off"><label class="skip-l" for="hero-address">Contract address</label>
<select name="chain" aria-label="Chain"><option value="ethereum">Ethereum</option><option value="base">Base</option></select>
<input id="hero-address" name="address" type="text" inputmode="text" spellcheck="false" placeholder="0x… contract address" aria-label="Contract address">
<button class="btn primary" type="submit">Run free check <span class="arr">→</span></button></form>
<p class="lede">Before an agent approves, deposits into or calls a contract, one request tells it who can change that contract (an EOA, a Safe, a timelock, or nobody), how fast, and whether it can pause, blacklist or upgrade. Every answer is pinned to a block hash and reproducible with <code>cast</code>.</p>
{hero_try(idx)}
{quickstart_block()}
<div class="ctas"><a class="btn primary" href="#preflight">Run a free check <span class="arr">→</span></a><a class="btn" href="protocols/">Protocol safety records</a><a class="btn" href="#inspector">Inspect a protocol</a></div>
<div class="livebar" data-etas="{E(livebar_etas(radar))}"><span class="dot live"></span><b>{E(radar_counts_text(radar))}.</b> {f'<span class="opstate ready lb-ready">{n_ready} READY · EXECUTABLE NOW</span> ' if n_ready else ""}<span class="lb-next">Next: <span class="lb-p">{E(nxt["protocol"])}</span>, <span class="countdown" data-eta="{nxt["eta"]}">ETA {E(utc(nxt["eta"]))}</span></span> <small class="lb-asof">(pinned snapshot: radar block {r["block_number"]:,}, observed <time datetime="{E(utc_iso(r["block_timestamp"]))}" data-observed="{r["block_timestamp"]}">{E(r["block_time_utc"])}</time><span class="obs-age" data-age="{r["block_timestamp"]}"></span>)</small> · <a href="#radar">Radar →</a></div>
<div class="ledger">
<div><b>{c["sprints"]}</b><span>Sprints completed</span><small>{E(c["chains"])} control-plane reviews</small></div>
<div data-protocol-count><b>{len(site_protocols(idx))}</b><span>Indexed protocols</span><small>{E(B2A.protocols_line(idx, load_pinned()).split(": ", 1)[1])}</small></div>
<div><b>{c["eas_n"]}</b><span>Base EAS attestations</span><small>Sprints {c["eas_from"]}–{c["eas_to"]}{"; " + c["pending"] + " hash-pinned" if c["pending"] else ""}{"; " + c["later"] + " records after review" if c["later"] else ""}</small></div>
<div><b>$0</b><span>Free launch API</span><small>{E(RATE_LIMIT)} · no key · no wallet</small></div>
</div>
</div></section>
{preflight_section()}
{inspector(idx, c)}
{radar_section(radar)}
{onboarding_section(load_onboarding())}
{findings_section(idx)}
{index_section(idx, c, count_line)}
{verify_section(idx, c)}
{pricing_section(idx)}
{request_section(idx)}
{faq_section(c, r)}
{about_section(idx)}
</main>
{footer(count_line, reg)}
{org_ld_script()}
{app_ld_script(idx)}
</body></html>
"""
    return head(TITLE, DESC, BASE_URL + "/", rich=True) + "\n" + body


def vault_factories_page(idx, sp):
    """/integrations/vault-factories/: the zero-cost Control-Plane & Role Map tab (api/v1/protocols.json), status badges and
    PactaSentinelGuard.sol wiring for vault factories and curators. Platform-neutral; no claim of any partner integration."""
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    tiers = {}
    for v in sp.values():
        t = "rpc_observed" if v["pinned"] else ("aligned" if is_aligned_page(v["entries"]) else "parameter_delta")
        tiers[t] = tiers.get(t, 0) + 1
    n_eas = sum(1 for v in sp.values() if not v["pinned"])
    url = f"{BASE_URL}/integrations/vault-factories/"
    title = "Vault factories: control-plane tab, status badges and PactaSentinelGuard"
    desc = "Free building blocks for vault factories and curators: a Control-Plane & Role Map tab from one static JSON file, embeddable status badges, and a cap-increase tripwire."
    js = ('const res = await fetch("https://pacta.wtf/api/v1/protocols.json");\n'
          'const { protocols } = await res.json();\n'
          'const p = protocols.find((x) => x.slug === "aave-v3-gho");\n'
          '// p.badge.svg, p.evidenceBasis ("eas_attested" | "rpc_observed"), p.classification, p.controllerAddress,\n'
          '// p.surfaces[i].blockNumber / blockHash, p.preflightArgs (for a live re-read)\n'
          'badgeImg.src = p.badge.svg;            // render text with textContent, never innerHTML\n'
          'statusCell.textContent = p.badge.label;')
    sol = ('PactaSentinelGuard guard = new PactaSentinelGuard(\n'
           f'    {reg}, // PactaCommitmentRegistry (Base)\n'
           '    0x4200000000000000000000000000000000000021, // EAS predeploy (Base)\n'
           '    curatorSafe,                                // binds collateral\n'
           '    0                                           // maxStaleness: 0 = 30 days (1 to 365 days)\n'
           ');\n'
           'guard.bind(collateral, sprintId, easUid);       // from protocols.json `sprints` / `baseEasUids`\n'
           'guard.validateCapIncrease(collateral, currentCap, newCap); // reverts only on an unhealthy increase')
    md = f"[![{LK.BADGE_TITLE}]({BASE_URL}/badges/aave-v3-gho.svg)]({BASE_URL}/protocols/aave-v3-gho/)"
    rows = "".join(f'<tr><td><img class="cp-badge" src="../../badges/{s_}.svg" alt="{E(LK.BADGE_TITLE)}: {E(LK.BADGE_TIERS[t][0])}" height="20"></td>'
                   f'<td class="num">{tiers.get(t, 0)}</td><td>{E(d)}</td></tr>'
                   for t, s_, d in (("aligned", "aave-v3-gho", "Every record is a Base-EAS-attested aligned baseline: on-chain state matches the documentation."),
                                    ("parameter_delta", "curve-finance-crvusd", "Base-EAS-attested; at least one surface differs from the documentation."),
                                    ("rpc_observed", "bedrock-unieth", "RPC-pinned only: control plane pinned at an archive block; documentation not assessed; not EAS-attested.")))
    plat = "".join(f"<tr><td><b>{E(a)}</b></td><td><code>{E(b)}</code></td><td>{E(d)}</td></tr>" for a, b, d in (
        ("Morpho Vault V2", "checkMorphoV2AbsoluteCapIncrease(vault, collateral, idData, newCap)",
         "Before a curator submits increaseAbsoluteCap. Reads absoluteCap(keccak256(idData)); decreaseAbsoluteCap and sentinel revoke are never gated."),
        ("Euler EVK", "checkEulerCapsChange(evault, collateral, newSupplyCap, newBorrowCap)",
         "Before setCaps. AmountCap 0 means unlimited, so setting a cap to 0 counts as an increase; lowering a cap never needs the attestation."),
        ("Veda (BoringVault), Lagoon, Upshift, Mellow", "validateCapIncrease(collateral, currentCap, newCap)",
         "In your cap-setting path: a manager or strategist module, a Safe transaction guard, or an off-chain approval bot."),
        ("Off-chain Sentinel bots", "attestationHealth(collateral)",
         "Poll the health state (it never reverts on a malformed attestation) and alert or de-risk.")))
    body = f"""<body>
{topbar("../../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../../">Pacta</a> / Integrations / Vault factories</div>
<article class="memo">
<header><span class="tier">Integrations</span><h1>{E(title)}</h1>
<p class="lede">Free building blocks for vault factories and curator tooling: a <b>Control-Plane &amp; Role Map</b> tab from one static JSON file, embeddable status badges, and <code>PactaSentinelGuard.sol</code>, an on-chain tripwire that refuses cap increases for collateral without a healthy Pacta attestation and never blocks a decrease.</p></header>
<section class="memo-sec" id="control-plane-tab"><h2>1. Control-Plane &amp; Role Map tab (free, no key)</h2>
<p><a href="../../api/v1/protocols.json">/api/v1/protocols.json</a> (schema <code>pacta.protocols.v1</code>) lists every published protocol record: {len(sp)} protocols, of which {n_eas} are Base-EAS-attested (<code>evidenceBasis: "eas_attested"</code>, documentation compared) and {len(sp) - n_eas} are RPC-observed only (<code>evidenceBasis: "rpc_observed"</code>, <code>documentationComparison: "not_assessed"</code>). Each record carries the checksummed target and controller, every pinned surface with its block number and block hash, the badge URLs and ready-to-use <code>preflightArgs</code>.</p>
{snippet(js, "JavaScript", "Copy JavaScript")}
<p>Show RPC-observed protocols as observed control planes only: never present them as aligned or as having a documentation delta. For a live re-read of any contract, call the free <code>{E(API)}/v1/check/preflight</code> with <code>preflightArgs</code>.</p></section>
<section class="memo-sec" id="badges"><h2>2. Control-plane status badges</h2>
<p>Static: <code>{E(BASE_URL)}/badges/&lt;slug&gt;.svg</code> (rebuilt with the site). Live: <code>{E(API)}/v1/badges/&lt;slug&gt;.svg</code> (5-minute cache, CORS open). Three tiers, per protocol page:</p>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Badge</th><th class="r">Protocols</th><th>Meaning</th></tr></thead><tbody>{rows}</tbody></table></div>
{snippet(md, "Markdown", "Copy Markdown")}</section>
<section class="memo-sec" id="sentinel-guard"><h2>3. PactaSentinelGuard.sol: refuse unhealthy cap increases, never block a decrease</h2>
<p>An MIT, zero-dependency, non-custodial Solidity <code>^0.8.24</code> contract (source and offline Foundry tests in <a href="{E(REPO)}/tree/main/packages/sentinel-guard"><code>packages/sentinel-guard</code></a>; not audited, review before production use). A cap increase passes only if the collateral's binding resolves to:</p>
<ul><li>a Sprint receipt in PactaCommitmentRegistry {hexref(reg)} on Base with <code>driftCount == 0</code> (the receipt covers the whole Sprint, so drift anywhere in it blocks increases);</li>
<li>a Base EAS attestation with the Pacta schema, made by the registry's current attester, not revoked or expired, younger than <code>maxStaleness</code> (default 30 days), whose payload matches the registry receipt.</li></ul>
<p>Decreases, equal caps and zeroing always pass, so curators and sentinels can de-risk during an incident. Pacta deploys no shared instance: each curator deploys one on Base, where the registry and EAS live (vaults on other chains can run the same checks from an off-chain bot), and binds collateral with Sprint ids and UIDs from <code>protocols.json</code>. RPC-observed protocols have no attestation to bind, so an increase guarded for them always reverts.</p>
{snippet(sol, "Solidity", "Copy Solidity")}
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Platform</th><th>Call</th><th>Where</th></tr></thead><tbody>{plat}</tbody></table></div></section>
</article>
<div class="memo-foot"><span>Read-only on-chain analysis. Not investment advice. No partner integration is implied: these are open building blocks.</span><a href="../../protocols/">Protocol records →</a></div>
</main>
{footer(count_line, reg, "../../")}
</body></html>
"""
    return head(f"{title} · Pacta", desc, url, prefix="../../", og_title=title, og_type="article") + "\n" + body


def request_page(idx):
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    desc = "The API is free for agents ($0, no key). Issuers: request a 24h onboarding & delta clearance ($5,000 USDC) or continuous Aligned maintenance."
    body = f"""<body>
{topbar("../")}
<main id="main">
<section class="sec" id="request"><div class="wrap">
<div class="crumbs"><a href="../">Pacta</a> / Request coverage</div>
<div class="sec-head"><span class="n">→</span><h1>Request coverage</h1><span class="aside">Nothing is sent until you choose a channel</span></div>
<p class="sec-intro">Agents do not need this page: the API, MCP server and all public data are free with no key (<a href="../#preflight">start here</a>). For a 24h onboarding &amp; delta clearance, continuous Aligned maintenance or a high-throughput API SLA, pick a track and the protocols you issue, run or hold. The scope brief builds in your browser; open it as a pre-filled GitHub intake issue, compose it in Gmail, or copy it with our address. Public data stays free either way.</p>
{request_builder(idx, "../")}
</div></section>
{pricing_section(idx, "../")}
</main>
{footer(count_line, reg, "../")}
</body></html>
"""
    return head("Request coverage · Pacta", desc, f"{BASE_URL}/request/", prefix="../", og_title="Request Pacta coverage") + "\n" + body


def brief_page(slug, desc, idx, radar):
    src = open(os.path.join(BRIEF_SRC, f"{slug}.html")).read()
    title = html.unescape(re.match(r"<!-- title: (.*?) -->\n", src).group(1))   # plain text; head() escapes once
    content = src.split("\n", 1)[1]
    item = next((it for it in radar["items"] if it["brief"].rstrip("/").endswith(slug)), None)
    r = radar["refreshed_at"]
    meta = ""
    if item:
        ops = " ".join(hexref(o["op_id"], 8, 4) for o in item["operations"])
        meta = (f'<dl class="memo-meta">'
                f'<dt>Protocol</dt><dd>{E(item["protocol"])}</dd>'
                f'<dt>Timelock</dt><dd>{hexref(item["timelock"])} · {secs(item["min_delay_seconds"])} minimum delay</dd>'
                f'<dt>Operation{"s" if len(item["operations"]) > 1 else ""}</dt><dd>{ops}</dd>'
                + (f'<dt>Execution window</dt><dd><span class="countdown" data-eta="{item["eta"]}">ETA {E(utc(item["eta"]))}</span> · {E(utc(item["eta"], True))}</dd>' if item.get("eta") else
                   f'<dt>Execution</dt><dd>Executed on-chain: isOperationDone = true at finalized block <span class="num">#{r["block_number"]:,}</span></dd>') +
                f'<dt>State</dt><dd>{state_badge(item_state(item), item["operations"])} at finalized block <span class="num">#{r["block_number"]:,}</span> ({E(r["block_time_utc"])}) '
                f'<span class="badge final">Scanner-pinned (L1 finalized)</span></dd></dl>')
    content = content.replace("</header>", "</header>\n" + meta, 1)
    if item:
        content = post_eta_banner(item, r) + content
    issuer = item["protocol"] if item else title
    content = content.rstrip("\n") + "\n" + clearance_callout(issuer, BRIEF_PROTOCOL[slug])
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    body = f"""<body>
{topbar("../../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../../">Pacta</a> / <a href="../../#radar">Timelock radar</a> / Pre-execution brief</div>
<article class="memo">
{content}</article>
<div class="memo-foot"><span>Read-only on-chain analysis. Not investment advice. Exploit-sensitive vulnerabilities are never published here; they go through Immunefi or Cantina bounty programmes.</span><a href="../../request/">Get briefs like this for your collateral →</a></div>
</main>
{footer(count_line, reg, "../../")}
</body></html>
"""
    return head(title, desc, f"{BASE_URL}/briefs/{slug}/", prefix="../../", og_title=title, og_type="article") + "\n" + body


# ---- Batch E: pacta.wtf/bounties/ ($100 USDC hard cap, 4 x $25 USDC slots) --------------------------------------------
BOUNTY_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bounty_issues.json")
BOUNTY_TEMPLATE = ".github/PULL_REQUEST_TEMPLATE/bounty_mismatch.md"
BOUNTY_TEMPLATE_URL = f"{REPO}/blob/main/{BOUNTY_TEMPLATE}"
BOUNTY_COMPARE_URL = f"{REPO}/compare/main...main?quick_pull=1&template=bounty_mismatch.md"
BOUNTY_TITLE = "Pacta Chain-Feed Mismatch Challenge ($100 USDC Hard-Cap · 7-Day Sprint Nov 15 – Nov 22, 2026)"
BOUNTY_SLOTS = {   # slot -> scope line (receipt/1825)
    1: "Ethereum Mainnet (chainId: 1, >=$25M TVL) unindexed control-plane parameter_delta #1",
    2: "Ethereum Mainnet (chainId: 1, >=$25M TVL) unindexed control-plane parameter_delta #2",
    3: "Base (8453) or Arbitrum One (42161) (>=$10M TVL) unindexed control-plane parameter_delta",
    4: "Live chain-feed drift catch on any of Pacta's 53 indexed protocols OR 4th unindexed (>=$15M TVL) mismatch",
}
# receipt/1827: the truthful settlement statement (word for word); the treasury is an externally owned account, never a Safe.
BOUNTY_PAYOUT = ("Paid in USDC on Base Mainnet within 48h of maintainer merge from Pacta treasury (0x4348DF1BEFAffcbA248B5118B1b782B1B2bdEd14) "
                 "once the winner comments their public Base 0x... address on the merged PR. Funds are not pre-escrowed in an automated contract; "
                 "zero automatic on-chain payouts.")
BOUNTY_PROOF = [   # the 6 required PR proof items (the PR template enforces them; tools/verify_bounty_submission.py checks them)
    ("chainId & contract address", "chainId (1, 8453 or 42161), the checksummed 0x target contract, the protocol name and a verifiable TVL reference (or the Pacta slug for indexed drift)."),
    ("Pinned finalized block", "The finalized blockNumber and its exact 32-byte blockHash (plus the prior pinned Pacta block / tx for post-snapshot drift)."),
    ("Deterministic dual-RPC cast proof", "The exact cast call / cast storage commands with --block <blockNumber> and their raw outputs, identical on 2 independent RPC endpoints."),
    ("Live official documentation claim (HTTP 200)", "A direct https:// URL to the protocol's official docs and the verbatim quote that conflicts with the on-chain state."),
    ("Pacta MCP output", "The JSON from pacta_lookup_protocol / pacta_check_preflight / pacta_scan_control_plane."),
    ("Apache-2.0 contribution & commercialization grant", "A checked confirmation granting Pacta by Fractal Neurons perpetual, irrevocable rights under Apache-2.0 to ingest, Base EAS-attest, publish on pacta.wtf, and commercialize the merged mismatch record."),
]
BOUNTY_RULES = [
    ("First valid merged PR wins", "it must pass deterministic CI and an independent dual-RPC archive replay at the pinned blockHash."),
    ("Max 1 open PR per contributor", "across all bounty slots at a time; Slots #1 and #2 must cover two distinct protocols."),
    ("Zero AI-slop", "fabricated RPC outputs, unpinned block reads, or broken / hallucinated doc URLs are closed and disqualified."),
    ("Strict ban on third-party spam", "never open unsolicited PRs, issues or comments in third-party repositories on Pacta's behalf; submissions are PRs to Fractal-Neurons/pacta only."),
    ("No public exploit PoCs", "governance and documentation parameter mismatches only; route security vulnerabilities via Immunefi / Cantina per /.well-known/security.txt."),
    ("Agent-assisted & autonomous-agent submissions welcome", "Human, agent-assisted, and autonomous-agent submissions are equally eligible under the exact "
     "same deterministic dual-RPC archive replay, HTTP 200 official-docs verification, and 1-open-PR-per-contributor rules (0 fabricated outputs)."),
]
BOUNTY_FIXTURE = "bounties/submissions/slot-<slot>-<protocol-slug>.json"


def bounty_hours(pr):
    """Length of the sprint window in hours (sprintWindow "<ISO start> to <ISO end>"): 168 for the 7-day sprint."""
    start, end = (dt.datetime.fromisoformat(x.strip().replace("Z", "+00:00")) for x in pr["sprintWindow"].split(" to "))
    return int((end - start).total_seconds() // 3600)


def load_bounties(path=None):
    d = json.load(open(path or BOUNTY_SRC))
    pr, issues = d["program"], d["issues"]
    assert pr["totalHardCapUsdc"] == 100 and pr["slots"] == 4 and pr["slotRewardUsdc"] == 25 and len(issues) == 4
    assert [i["slot"] for i in issues] == [1, 2, 3, 4] and all(i["rewardUsdc"] == 25 for i in issues)
    assert sum(i["rewardUsdc"] for i in issues) == pr["totalHardCapUsdc"] and set(BOUNTY_ISSUE_URLS) == {1, 2, 3, 4}
    assert pr["treasuryAddress"] == "0x4348DF1BEFAffcbA248B5118B1b782B1B2bdEd14"
    assert bounty_hours(pr) == 168, "the sprint window must be exactly 7 days (168 h)"
    return d


def md_inline(t):
    """Escape, then **bold**, *italic* and `code` (code spans are protected first, so bold may contain code)."""
    codes = []
    t = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or f"\x00{len(codes) - 1}\x00", t)
    t = E(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"<i>\1</i>", t)
    return re.sub("\x00(\\d+)\x00", lambda m: f"<code>{E(codes[int(m.group(1))], quote=False)}</code>", t)


def md_html(text):
    """The small Markdown subset the bounty issues use: ## / ### headings, paragraphs (one per line, as GitHub renders issue line
    breaks), - and 1. lists, --- rules and ``` fences. Deterministic; every text node is escaped."""
    out, lst, code = [], None, None
    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None
    for line in text.split("\n"):
        if code is not None:
            if line.startswith("```"):
                out.append(f'<pre class="term-pre"><code>{E(chr(10).join(code), quote=False)}</code></pre>')
                code = None
            else:
                code.append(line)
            continue
        if line.startswith("```"):
            close()
            code = []
        elif not line.strip():
            close()
        elif line.strip() == "---":
            close()
            out.append("<hr>")
        elif line.startswith("### "):
            close()
            out.append(f"<h4>{md_inline(line[4:])}</h4>")
        elif line.startswith("## "):
            close()
            out.append(f"<h3>{md_inline(line[3:])}</h3>")
        elif re.match(r"^- ", line) or re.match(r"^\d+\. ", line):
            kind = "ul" if line.startswith("- ") else "ol"
            if lst != kind:
                close()
                out.append(f"<{kind}>")
                lst = kind
            item = re.sub(r"^(?:- |\d+\. )", "", line)
            out.append(f"<li>{md_inline(item)}</li>")
        else:
            close()
            out.append(f"<p>{md_inline(line)}</p>")
    close()
    assert code is None, "unterminated code fence"
    return "\n".join(out)


def bounties_page(idx, radar, bounties=None, claims=None, lb=None):
    """docs/bounties/index.html: Wave 2 (100 x $1 USDC rolling pool, live counter) on top, then the Wave 1 Genesis Archive: the
    $100 USDC capped Chain-Feed Mismatch Challenge (4 x $25 USDC) with its settlement ledger and the issue text verbatim."""
    d = load_bounties() if bounties is None else bounties
    claims = load_wave2_claims() if claims is None else claims
    lb = load_leaderboard() if lb is None else lb
    n_protocols = len(json.load(open(os.path.join(DOCS, "api", "v1", "protocols.json")))["protocols"])
    pr = d["program"]
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    claude = f"claude mcp add --transport http pacta {MCP_URL}"
    slot_rows = "".join(f'<tr data-bounty-slot="{n}"><td class="num">#{n}</td><td class="num">$25 USDC</td><td>{E(BOUNTY_SLOTS[n])}</td>'
                        f'<td><a href="{E(BOUNTY_ISSUE_URLS[n])}" target="_blank" rel="noopener">Issue #{E(BOUNTY_ISSUE_URLS[n].rsplit("/", 1)[1])} ↗</a></td></tr>'
                        for n in (1, 2, 3, 4))
    proof = "".join(f"<li><b>{E(k)}.</b> {E(v)}</li>" for k, v in BOUNTY_PROOF)
    rules = "".join(f"<li><b>{E(k)}:</b> {E(v)}</li>" for k, v in BOUNTY_RULES)
    issues = "".join(f'<details class="bounty-issue" id="slot-{i["slot"]}" data-bounty-issue="{i["slot"]}"><summary>{E(i["title"])}</summary>'
                     f'<p class="s">GitHub: <a href="{E(BOUNTY_ISSUE_URLS[i["slot"]])}" target="_blank" rel="noopener">{E(BOUNTY_ISSUE_URLS[i["slot"]])} ↗</a> · labels: '
                     f'{E(", ".join(i["labels"]))}</p><div class="md">{md_html(i["body"])}</div></details>' for i in d["issues"])
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": f"Pacta bounties · Wave 2 Epoch {CURRENT_EPOCH}: {ACTIVE_EPOCH_SLOTS} × ${REWARD_USDC} USDC · Wave 1 Genesis Archive",
          "url": f"{BASE_URL}/bounties/",
          "isPartOf": {"@type": "WebSite", "name": "Pacta by Fractal Neurons", "url": f"{BASE_URL}/"},
          "about": "Capped USDC bounty for verified on-chain control-plane mismatch records", "publisher": ORG_LD}
    ld_json = json.dumps(ld, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    body = f"""<body>
{topbar("../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../">Pacta</a> / Bounties</div>
<article class="memo">
<header><span class="tier" data-bounty-pill>{FUNDED_UNENCUMBERED_SLOTS} Funded Slots Open Now · ${E(REWARD_USDC)} USDC / Merged Finding</span>
<p class="s" data-bounty-context>Epoch {CURRENT_EPOCH}: {ACTIVE_EPOCH_SLOTS}-slot target · {PROGRAM_CAP_SLOTS:,}-slot program · ${E(RING_FENCED_USDC)} ring-fenced for Wave 1 Slot #4</p><h1>Pacta bounties: verified on-chain control-plane mismatches</h1>
<p class="lede">Find a live on-chain control-plane fact that contradicts a protocol's official documentation: a proxy admin, timelock delay, multisig threshold, curator or guardian role that differs from what the docs say. <b>Wave 2</b> is a {PROGRAM_CAP_SLOTS:,}-gap perpetual program at <b>${E(REWARD_USDC)} USDC per merged net-new gap</b>, opened in epochs: <b>Epoch {CURRENT_EPOCH}</b> has a target cap of {ACTIVE_EPOCH_SLOTS} slots (${E(ACTIVE_EPOCH_CAP_USDC)} USDC), of which ${E(FUNDED_UNENCUMBERED_USDC)} USDC ({FUNDED_UNENCUMBERED_SLOTS} slots) is confirmed unencumbered on-chain now. <b>Wave 1</b> (4 × $25 USDC, Nov 15 – Nov 22, 2026) is archived below with its settlement ledger. Every hunter is credited on the <a href="../leaderboard/">hunter leaderboard</a>.</p></header>
{wave2_section_html(claims, n_protocols)}<section class="memo-sec" id="quickstart"><h2>1-line Remote MCP quickstart (free)</h2>
<div class="qs-snip"><span class="qs-l">Claude Code</span><code class="mono">{E(claude)}</code>{copy_btn(claude)}</div>
<p>Query <code>pacta_lookup_protocol</code> (confirm the target is unindexed: a miss carries <code>coverage_gap_hint</code>), <code>pacta_check_preflight</code> and <code>pacta_scan_control_plane</code>, then pin the reads with <code>cast</code> on two RPC endpoints. Indexed protocols: <a href="../api/v1/protocols.json">/api/v1/protocols.json</a>.</p></section>
<section class="memo-sec" id="wave-1"><h2>Wave 1 Genesis Archive · {E(BOUNTY_TITLE)}</h2>
<p class="s" data-wave1-snapshot><b>Historical Snapshot (Pinned at 53 Protocols on Nov 15)</b>: the Wave 1 terms below are archived verbatim and refer to Pacta&#x27;s index as it stood on Nov 15, 2026; Wave 2 targets the live index (<a href="../api/v1/protocols.json">/api/v1/protocols.json</a>).</p>
<p>Find a live on-chain control-plane fact that contradicts a protocol's official documentation (<code>parameter_delta</code>). Four slots, <b>4 × $25 USDC = $100 USDC</b> in total, first valid merged PR per slot wins. Organizer: {E(pr["organizer"])}. Window: Nov 15 – Nov 22, 2026 ({bounty_hours(pr)}h).</p>
<h3>Wave 1 Genesis Settlement Ledger</h3>
{wave1_ledger_html(lb)}
<p class="s">Settled amounts appear only once a Base payout transaction hash is recorded in <code>bounties/leaderboard.json</code> (<code>tools/stamp_wave1_payouts.py</code>); each links to BaseScan.</p></section>
<section class="memo-sec" id="slots"><h2>Wave 1 slots (4 × $25 USDC)</h2>
<table class="ix" data-bounty-slots><thead><tr><th>Slot</th><th>Reward</th><th>Scope</th><th>Issue</th></tr></thead><tbody>{slot_rows}</tbody></table>
<p>Total hard cap: <b>$100 USDC</b> across Slots #1–#4. Sprint window: <b>Nov 15 00:00 UTC – Nov 22 00:00 UTC, 2026</b> (<code>{E(pr["sprintWindow"])}</code>, {bounty_hours(pr)}h).</p></section>
<section class="memo-sec" id="payout"><h2>How the Wave 1 reward is paid</h2>
<p data-bounty-payout>{E(BOUNTY_PAYOUT)}</p>
<p class="s">The Pacta treasury <code class="mono">{E(pr["treasuryAddress"])}</code> is an externally owned account (EOA) on {E(pr["settlementChain"])}; settlement happens after deterministic dual-RPC replay verification and maintainer merge.</p></section>
<section class="memo-sec" id="proof"><h2>Wave 1 required PR proof (all 6)</h2>
<ol>{proof}</ol>
<p>Open the PR to <code>Fractal-Neurons/pacta</code> with the <a href="{E(BOUNTY_TEMPLATE_URL)}" target="_blank" rel="noopener">bounty_mismatch.md PR template ↗</a> (<a href="{E(BOUNTY_COMPARE_URL)}" target="_blank" rel="noopener">pre-filled PR ↗</a>). Each PR commits exactly one JSON fixture at <code data-bounty-fixture>{E(BOUNTY_FIXTURE)}</code> (keys: <a href="{E(REPO)}/blob/main/bounties/submissions/README.md" target="_blank" rel="noopener">bounties/submissions/README.md ↗</a>). Check both offline before you submit: <code>python3 tools/verify_bounty_submission.py --json {E(BOUNTY_FIXTURE)}</code> and <code>python3 tools/verify_bounty_submission.py --body PR_BODY.md</code> (deterministic field checks; maintainers re-run the dual-RPC replay and the HTTP 200 docs check).</p>
<p><b>Apache-2.0:</b> by checking the grant box you grant Pacta by Fractal Neurons perpetual, irrevocable rights under Apache-2.0 to ingest, Base EAS-attest, publish on pacta.wtf, and commercialize the merged mismatch record.</p></section>
<section class="memo-sec" id="rules"><h2>Wave 1 anti-slop, fair-play &amp; safety rules</h2><ul>{rules}</ul></section>
<section class="memo-sec" id="issues"><h2>Wave 1 issue text (verbatim)</h2><p class="s">The four Wave 1 GitHub issues (#21–#24), word for word.</p>{issues}</section>
</article>
<div class="memo-foot"><span>Governance and documentation mismatches only. Exploit-sensitive vulnerabilities are never published here; they go through Immunefi or Cantina bounty programmes.</span><a href="../protocols/">Indexed protocols →</a></div>
</main>
{footer(count_line, reg, "../")}
<script type="application/ld+json">{ld_json}</script>
</body></html>
"""
    return head(f"Bounties · Wave 2 Epoch {CURRENT_EPOCH}: {ACTIVE_EPOCH_SLOTS} × ${REWARD_USDC} USDC · Pacta",
                f"Wave 2: ${REWARD_USDC} USDC per merged net-new on-chain control-plane mismatch, paid in USDC on Base; Epoch {CURRENT_EPOCH} target cap {ACTIVE_EPOCH_SLOTS} slots of a {PROGRAM_CAP_SLOTS:,}-slot program; ${FUNDED_UNENCUMBERED_USDC} USDC confirmed unencumbered now. Wave 1 (4 × $25 USDC) archive and ledger.",
                f"{BASE_URL}/bounties/", prefix="../", og_title=f"Pacta bounties · Wave 2 Epoch {CURRENT_EPOCH}: {ACTIVE_EPOCH_SLOTS} × ${REWARD_USDC} USDC") + "\n" + body


# ---- Wave 2: 100 x $1 USDC rolling pool, Wave 1 Genesis ledger, /leaderboard/ and hunter badges ------------------------------
# Single source: tools/bounty_wave2.json (reward, slots, cap, settlement, categories); bounties/leaderboard.json (Wave 1 ledger,
# Wave 2 payouts, EAS credits); bounties/wave-2/<chain>-<slug>.json (merged claims, counted automatically).
WAVE2_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bounty_wave2.json")
WAVE2 = json.load(open(WAVE2_SRC))
REWARD_USDC = WAVE2["rewardUsdc"]                  # "1.00"
REWARD_ATOMIC = WAVE2["rewardAtomic"]              # 1_000_000 (USDC has 6 decimals)
PROGRAM_CAP_SLOTS = WAVE2["programCapSlots"]       # 1,000-gap perpetual program
CURRENT_EPOCH = WAVE2["currentEpoch"]              # epochs of 25-100 slots, opened one after another
ACTIVE_EPOCH_SLOTS = WAVE2["activeEpochSlots"]     # 25 in Epoch 1
ACTIVE_EPOCH_CAP_USDC = WAVE2["activeEpochCapUsdc"]  # "25.00"
PRIOR_EPOCH_SLOTS = WAVE2["priorEpochSlots"]       # slots filled in completed epochs (0 during Epoch 1)
# Public capacity claims follow confirmed, unencumbered on-chain USDC only (the epoch cap is a target, not a promise):
FUNDED_UNENCUMBERED_SLOTS = WAVE2["fundedUnencumberedSlots"]   # 2 today
FUNDED_UNENCUMBERED_USDC = WAVE2["fundedUnencumberedUsdc"]     # "2.00"
RING_FENCED_USDC, RING_FENCED_FOR = WAVE2["ringFencedUsdc"], WAVE2["ringFencedFor"]
PROGRAM_LABEL = WAVE2["program"]
USDC_BASE = WAVE2["settlement"]["tokenAddress"]
assert round(float(REWARD_USDC) * 10 ** WAVE2["settlement"]["decimals"]) == REWARD_ATOMIC
assert f"{REWARD_ATOMIC * ACTIVE_EPOCH_SLOTS / 10 ** 6:.2f}" == ACTIVE_EPOCH_CAP_USDC
assert 25 <= ACTIVE_EPOCH_SLOTS <= 100 and CURRENT_EPOCH >= 1 and 0 <= PRIOR_EPOCH_SLOTS
assert PRIOR_EPOCH_SLOTS + ACTIVE_EPOCH_SLOTS <= PROGRAM_CAP_SLOTS == 1000
assert 0 <= FUNDED_UNENCUMBERED_SLOTS <= ACTIVE_EPOCH_SLOTS and f"{REWARD_ATOMIC * FUNDED_UNENCUMBERED_SLOTS / 10 ** 6:.2f}" == FUNDED_UNENCUMBERED_USDC
EPOCH_REMAINING_USDC = f"{REWARD_ATOMIC * (ACTIVE_EPOCH_SLOTS - FUNDED_UNENCUMBERED_SLOTS) / 10 ** 6:.2f}"
assert WAVE2["settlement"]["chainId"] == 8453 and USDC_BASE == "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
assert WAVE2["settlement"]["treasuryKind"] == "EOA"
WAVE2_DIR = os.path.join(ROOT, *WAVE2["fixtureDir"].split("/"))
WAVE2_ISSUE_URL = WAVE2.get("wave2IssueUrl") or f"{REPO}/issues"
COMMUNITY_URL = WAVE2["communityUrl"]              # GitHub Discussions: announcements + builder / bounty Q&A
COMMUNITY_QA_URL = WAVE2["communityQaUrl"]         # the Builder & Bounty Q&A thread
assert COMMUNITY_URL == f"{REPO}/discussions" and COMMUNITY_QA_URL.startswith(COMMUNITY_URL + "/")
WAVE2_MASTER_ISSUE = os.path.join(ROOT, "bounties", "WAVE2-MASTER-ISSUE.md")
WAVE2_NAME_RE = re.compile(r"^(ethereum|base|arbitrum)-([a-z0-9]+(?:-[a-z0-9]+)*)\.json$")
LEADERBOARD_SRC = os.path.join(ROOT, "bounties", "leaderboard.json")
HUNTER_BADGE_DIR = os.path.join(DOCS, "badges", "hunters")
HUNTER_FILE_RE = re.compile(r"^[A-Za-z0-9_-]{1,39}$")             # badge file name (strict; no dots, slashes or traversal)
GITHUB_USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
FRAMEWORK_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,39}$")
TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
CHAIN_NAMES = {1: "Ethereum", 8453: "Base", 42161: "Arbitrum One"}
WAVE2_CATEGORY_TEXT = {
    "protocol_mismatch": "an unindexed protocol on Ethereum (1), Base (8453) or Arbitrum One (42161) with at least {tvl} of chain TVL that is not in "
                         "/api/v1/protocols.json, whose live control plane (proxy admin, timelock delay, Safe threshold, guardian or role) contradicts its "
                         "official documentation",
    "curated_vault_mismatch": "a curated vault or isolated market with at least {tvl} of vault TVL on Morpho (MetaMorpho), Euler V2 (EVK), Concrete, "
                              "Veda / BoringVault, Yearn V3, Pendle, Maple or Centrifuge, where the on-chain curator(), guardian(), owner(), timelock or "
                              "role admin contradicts the HTTP-200 official documentation",
    "post_pin_drift": "live control-plane drift on any of Pacta's {n} indexed protocols since its pinned blockNumber (cite the pactaSlug and the prior pin)",
}
WAVE2_PAYOUT = (f"Paid in USDC on Base Mainnet in weekly batches, within {WAVE2['settlement']['windowDays']} days of maintainer merge, from the Pacta "
                f"treasury ({WAVE2['settlement']['treasuryAddress']}, an externally owned account) directly to the basePayoutAddress committed in the "
                "merged bounties/wave-2 fixture: no post-merge comment needed. Funds are not pre-escrowed in an automated contract; zero automatic "
                "on-chain payouts.")
# Inner geometry of the official mark (docs/logo.svg, comments / whitespace stripped): embedded in every hunter badge.
LOGO_SVG_INNER = ('<g fill="none" stroke-linecap="round">'
                  + "".join(f'<circle cx="{x}" cy="{y}" r="185" stroke="#000" stroke-width="38"/>'
                            f'<circle cx="{x}" cy="{y}" r="185" stroke="#fff" stroke-width="18"/>'
                            for x, y in ((240, 240), (760, 240), (240, 760), (760, 760)))
                  + '</g><polygon points="500,15 985,500 500,985 15,500" fill="#fff" stroke="#000" stroke-width="12" stroke-linejoin="miter"/>'
                  '<polygon points="500,125 875,500 500,875 125,500" fill="#000"/>'
                  '<path fill="#fff" fill-rule="evenodd" d="M380,335H535C610,335 655,378 655,442.5C655,507 610,550 535,550H458V665H380Z'
                  'M458,400V485H525C560,485 578,468 578,442.5C578,417 560,400 525,400Z"/>')


def usdc(atomic):
    return f"${atomic / 10 ** 6:,.2f}"


def tx_ok(h):
    """A real Base transaction hash: 0x + 64 hex, not all zero. Anything else never counts as settled."""
    return isinstance(h, str) and bool(TX_RE.match(h)) and int(h, 16) != 0


def tvl_label(cat):
    v = WAVE2["categories"][cat]["minTvlUsd"]
    return f"${v // 1_000_000}M"


def load_leaderboard(path=None):
    d = json.load(open(path or LEADERBOARD_SRC))
    assert d["schema"] == "pacta.bounty_leaderboard.v1"
    w1 = d["wave1Settlements"]
    assert [s["slot"] for s in w1] == [1, 2, 3, 4] and [s["issue"] for s in w1] == [21, 22, 23, 24]
    assert all(f"{REPO}/issues/{s['issue']}" == BOUNTY_ISSUE_URLS[s["slot"]] for s in w1)
    for s in w1:
        assert s["status"] in ("verified", "in_review"), s
        assert s["payoutTxHash"] is None or tx_ok(s["payoutTxHash"]), f"slot {s['slot']}: payoutTxHash must be null or a real 0x + 64-hex tx"
        assert s["payoutTxHash"] is None or s["status"] == "verified", f"slot {s['slot']}: only a verified slot can be settled"
        if s["status"] == "verified":
            assert GITHUB_USER_RE.match(s["hunter"]) and isinstance(s["pr"], int) and s["protocol"] and s["chainId"] in CHAIN_NAMES, s
            assert s["agentFramework"] is None or FRAMEWORK_RE.match(s["agentFramework"]), s
            assert s["rewardUsdc"] == "25.00"
    for p in d["wave2Settlements"]:
        assert WAVE2_NAME_RE.match(p["fixture"]) and tx_ok(p["payoutTxHash"]), p
    assert all(GITHUB_USER_RE.match(h) and isinstance(n, int) and n >= 0 for h, n in d["easAttestations"].items())
    return d


def load_wave2_claims(path=None):
    """Merged Wave 2 claims (bounties/wave-2/*.json), sorted by file name. Shape-checked here (the full validator, with the
    duplicate guard against protocols.json at PR time, runs in CI: tools/verify_bounty_submission.py)."""
    d = path or WAVE2_DIR
    out = []
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not name.endswith(".json"):
            continue
        m = WAVE2_NAME_RE.match(name)
        f = json.load(open(os.path.join(d, name)))
        assert m and f.get("wave") == 2 and f.get("slug") == m.group(2) and CHAIN_NAMES.get(f.get("chainId")) is not None, name
        assert {1: "ethereum", 8453: "base", 42161: "arbitrum"}[f["chainId"]] == m.group(1), name
        assert f.get("category") in WAVE2["categories"] and GITHUB_USER_RE.match(str(f.get("hunter"))), name
        assert f.get("agentFramework") is None or FRAMEWORK_RE.match(f["agentFramework"]), name
        out.append({**f, "_file": name})
    assert len(out) <= PRIOR_EPOCH_SLOTS + FUNDED_UNENCUMBERED_SLOTS, \
        "Wave 2 merged claims cannot exceed the confirmed unencumbered on-chain capacity (raise fundedUnencumberedSlots after a confirmed top-up)"
    assert len({(c["chainId"], c["contractAddress"].lower()) for c in out}) == len(out) and len({c["slug"] for c in out}) == len(out)
    return out


def hunter_stats(lb, claims):
    """Per-hunter aggregates from the Wave 1 ledger + merged Wave 2 claims. Settled USDC counts ONLY payouts with a real tx hash."""
    paid2 = {p["fixture"]: p["payoutTxHash"] for p in lb["wave2Settlements"]}
    st = {}

    def add(handle, fw, proto_key, catch, settled_atomic, tx):
        h = st.setdefault(handle.lower(), {"handle": handle, "frameworks": [], "catches": [], "protocols": set(), "settled": 0, "txs": [],
                                           "eas": lb["easAttestations"].get(handle, 0)})
        if fw and fw not in h["frameworks"]:
            h["frameworks"].append(fw)
        h["catches"].append(catch)
        h["protocols"].add(proto_key)
        if tx:
            h["settled"] += settled_atomic
            h["txs"].append(tx)
    for s in lb["wave1Settlements"]:
        if s["status"] == "verified":
            tx = s["payoutTxHash"] if tx_ok(s["payoutTxHash"]) else None
            add(s["hunter"], s["agentFramework"], f"{s['chainId']}:{s['protocol'].lower()}",
                {"wave": 1, "label": f"Wave 1 · Slot #{s['slot']} · PR #{s['pr']}", "href": f"{REPO}/pull/{s['pr']}", "protocol": s["protocol"]},
                25 * 10 ** 6, tx)
    for c in claims:
        tx = paid2.get(c["_file"])
        add(c["hunter"], c.get("agentFramework"), f"{c['chainId']}:{c['slug']}",
            {"wave": 2, "label": f"Wave 2 · {c['_file']}", "href": f"{REPO}/blob/main/{WAVE2['fixtureDir']}/{c['_file']}", "protocol": c["protocol"]},
            REWARD_ATOMIC, tx if tx_ok(tx) else None)
    rows = sorted(st.values(), key=lambda h: (-len(h["catches"]), -len(h["protocols"]), -h["eas"], -h["settled"], h["handle"].lower()))
    rank, prev = 0, None
    for i, h in enumerate(rows):                    # standard competition ranking: equal metrics share a rank
        key = (len(h["catches"]), len(h["protocols"]), h["eas"], h["settled"])
        rank = rank if key == prev else i + 1
        h["rank"], prev = rank, key
    return rows


def framework_stats(rows):
    fw = {}
    for h in rows:
        for name in h["frameworks"] or ["not stated"]:
            f = fw.setdefault(name, {"name": name, "hunters": 0, "catches": 0, "protocols": set(), "settled": 0})
            f["hunters"] += 1
            f["catches"] += len(h["catches"])
            f["protocols"] |= h["protocols"]
            f["settled"] += h["settled"]
    return sorted(fw.values(), key=lambda f: (f["name"] == "not stated", -f["catches"], -len(f["protocols"]), f["name"]))


def hunter_badge_svg(handle, catches):
    """Deterministic static README badge for a hunter: the official Pacta mark + '<handle> · N verified'. Every dynamic string is
    XML-escaped and the handle must match HUNTER_FILE_RE (no traversal, no markup)."""
    from xml.sax.saxutils import escape, quoteattr
    import xml.etree.ElementTree as ET
    if not (isinstance(handle, str) and HUNTER_FILE_RE.fullmatch(handle)):
        raise ValueError(f"refusing hunter badge for handle {handle!r}")
    left, right = "Pacta hunter", f"{handle} · {catches} verified"
    lw = 24 + round(len(left) * 6.6) + 8
    rw = round(len(right) * 6.6) + 14
    label = f"{left}: {right} control-plane catch{'es' if catches != 1 else ''}"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{lw + rw}" height="20" viewBox="0 0 {lw + rw} 20" role="img" aria-label={quoteattr(label)}>'
           f"<title>{escape(label)}</title>"
           f'<rect width="{lw}" height="20" fill="#f4f4f2"/><rect x="{lw}" width="{rw}" height="20" fill="#14161a"/>'
           f'<rect x="0.5" y="0.5" width="{lw + rw - 1}" height="19" fill="none" stroke="#14161a"/>'
           f'<svg x="4" y="2" width="16" height="16" viewBox="0 0 1000 1000">{LOGO_SVG_INNER}</svg>'
           f'<g font-family="Verdana,DejaVu Sans,Geneva,sans-serif" font-size="11">'
           f'<text x="24" y="14" fill="#14161a">{escape(left)}</text><text x="{lw + 7}" y="14" fill="#ffffff">{escape(right)}</text></g></svg>\n')
    ET.fromstring(svg)                               # valid XML or the build fails
    return svg


def hunter_badge_path(handle, base=None):
    """docs/badges/hunters/<handle>.svg, refusing any handle that is not a plain file name inside the badge directory."""
    base = os.path.realpath(base or HUNTER_BADGE_DIR)
    if not (isinstance(handle, str) and HUNTER_FILE_RE.fullmatch(handle)):
        raise ValueError(f"refusing hunter badge path for {handle!r}")
    p = os.path.realpath(os.path.join(base, handle + ".svg"))
    if os.path.dirname(p) != base:
        raise ValueError(f"hunter badge path escapes {base}: {p}")
    return p


def write_hunter_badges(rows, base=None):
    base = base or HUNTER_BADGE_DIR
    os.makedirs(base, exist_ok=True)
    keep = set()
    for h in rows:
        p = hunter_badge_path(h["handle"], base)
        with open(p, "w") as fh:
            fh.write(hunter_badge_svg(h["handle"], len(h["catches"])))
        keep.add(os.path.basename(p))
    for name in os.listdir(base):                    # deterministic directory: drop badges of hunters no longer listed
        if name.endswith(".svg") and name not in keep and HUNTER_FILE_RE.fullmatch(name[:-4]):
            os.remove(os.path.join(base, name))


def badge_markdown(handle):
    return f"[![Pacta hunter: {handle}]({BASE_URL}/badges/hunters/{handle}.svg)]({BASE_URL}/leaderboard/#hunter-{handle.lower()})"


def share_x_href(h):
    n = len(h["catches"])
    text = (f"GitHub hunter {h['handle']}: {n} verified on-chain control-plane catch{'es' if n != 1 else ''} on the Pacta hunter leaderboard "
            f"(Pacta by Fractal Neurons)")
    return "https://x.com/intent/tweet?" + urllib.parse.urlencode({"text": text, "url": f"{BASE_URL}/leaderboard/#hunter-{h['handle'].lower()}"})


def settled_cell(atomic, txs, pending="$0.00 (pending settlement)"):
    if not txs:
        return f'<span class="s" data-settled="pending">{E(pending)}</span>'
    links = " ".join(f'<a href="https://basescan.org/tx/{E(t)}" target="_blank" rel="noopener" data-basescan-tx>tx {E(short(t, 6, 4))} ↗</a>'
                     for t in dict.fromkeys(txs))
    return f'<b data-settled="{atomic}">{usdc(atomic)} USDC</b> <span class="s">{links}</span>'


def wave1_ledger_html(lb):
    rows = []
    for s in lb["wave1Settlements"]:
        issue = f'<a href="{E(BOUNTY_ISSUE_URLS[s["slot"]])}" target="_blank" rel="noopener">Issue #{s["issue"]} ↗</a>'
        if s["status"] != "verified":
            rows.append(f'<tr data-w1-slot="{s["slot"]}"><td class="num">#{s["slot"]}</td><td>{issue}</td><td>—</td><td>—</td><td>—</td>'
                        f'<td class="num">${E(s["rewardUsdc"])} USDC</td><td>{E(s["statusNote"] or "In review")}</td><td>—</td></tr>')
            continue
        tx = s["payoutTxHash"] if tx_ok(s["payoutTxHash"]) else None
        status = "Settled on Base" if tx else "Verified · settlement pending"
        rows.append(f'<tr data-w1-slot="{s["slot"]}"><td class="num">#{s["slot"]}</td><td>{issue}</td>'
                    f'<td><a href="{E(REPO)}/pull/{s["pr"]}" target="_blank" rel="noopener">PR #{s["pr"]} ↗</a></td>'
                    f'<td><a href="https://github.com/{E(s["hunter"])}" target="_blank" rel="noopener">@{E(s["hunter"])}</a></td>'
                    f'<td>{E(s["protocol"])} <span class="s">({E(CHAIN_NAMES[s["chainId"]])})</span></td>'
                    f'<td class="num">${E(s["rewardUsdc"])} USDC</td><td>{E(status)}</td>'
                    f'<td>{settled_cell(25 * 10 ** 6, [tx] if tx else [])}</td></tr>')
    return ('<table class="ix" data-wave1-ledger><thead><tr><th>Slot</th><th>Issue</th><th>PR</th><th>Hunter</th><th>Protocol</th><th>Reward</th>'
            f'<th>Status</th><th>Settled (Base USDC)</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')


def wave2_master_issue_md(n_protocols):
    """bounties/WAVE2-MASTER-ISSUE.md: the single rolling GitHub issue, verbatim (the H1 is the issue title). Generated from
    tools/bounty_wave2.json so the numbers can never drift from the site."""
    s = WAVE2["settlement"]
    cats = "\n".join(f"{i}. **{WAVE2['categories'][c]['label']} (`{c}`):** "
                     + WAVE2_CATEGORY_TEXT[c].format(tvl=tvl_label(c) if WAVE2["categories"][c]["minTvlUsd"] else "", n=n_protocols) + "."
                     for i, c in enumerate(WAVE2["categories"], 1))
    rules = "\n".join(f"- {r}." for r in WAVE2["rules"])
    return f"""# {WAVE2['title']}

**{PROGRAM_LABEL}.** Slots open in epochs of 25–100, one after another, up to {PROGRAM_CAP_SLOTS:,} slots in total. **Epoch {CURRENT_EPOCH} target cap: {ACTIVE_EPOCH_SLOTS} × ${REWARD_USDC} USDC = ${ACTIVE_EPOCH_CAP_USDC} USDC.** Confirmed unencumbered on-chain now: **${FUNDED_UNENCUMBERED_USDC} USDC ({FUNDED_UNENCUMBERED_SLOTS} slots)**; ${RING_FENCED_USDC} USDC in the treasury is separately ring-fenced for {RING_FENCED_FOR}, and the remaining ${EPOCH_REMAINING_USDC} of Epoch {CURRENT_EPOCH} target capacity unlocks as confirmed Base USDC top-ups land. Paid on {s['network']} (chainId {s['chainId']}, USDC `{USDC_BASE}`). One fixture per PR, first valid merged PR per target wins. Live counter: https://pacta.wtf/bounties/#wave-2 · Hunter leaderboard: https://pacta.wtf/leaderboard/

**Net-new only.** A finding qualifies only if it is not already published in https://pacta.wtf/api/v1/protocols.json when the PR is opened; `post_pin_drift` must be read at a block strictly after Pacta's latest pinned block for that protocol.

## What counts (one of three categories)

{cats}

Targets already in https://pacta.wtf/api/v1/protocols.json are only eligible as `post_pin_drift`. Each target (chain + contract address, and slug) can be claimed once across the whole pool.

## How to submit

1. Run the free Pacta MCP server (`claude mcp add --transport http pacta {MCP_URL}`) and keep the JSON of `pacta_lookup_protocol`, `pacta_check_preflight` or `pacta_scan_control_plane` for your target (`mcpProof`).
2. Pin a finalized block and read the contract with `cast call` / `cast storage --block <blockNumber>` on two independent RPC endpoints (identical outputs).
3. Commit exactly **one** new file, `{WAVE2['fixtureDir']}/<chain>-<slug>.json` (`<chain>` = `ethereum`, `base` or `arbitrum`), with your GitHub `hunter` name, optional `agentFramework` and your EIP-55 `basePayoutAddress`. The schema is in `{WAVE2['fixtureDir']}/README.md`.
4. Check it offline: `python3 tools/verify_bounty_submission.py --json {WAVE2['fixtureDir']}/<chain>-<slug>.json`
5. Open the PR. CI (`verify-bounty-pr`) accepts only a PR that adds that single JSON file and validates it with the validator from the base branch; maintainers then re-run the dual-RPC archive replay and the HTTP 200 docs check before merging.

## Payout

{WAVE2_PAYOUT}

## Questions

Ask in Community Q&A (GitHub Discussions): {COMMUNITY_URL}. Questions about targets, fixtures or the MCP tools go to the Builder & Bounty Q&A thread: {COMMUNITY_QA_URL}

## Rules

- Up to {WAVE2['maxOpenPrsPerContributor']} concurrent open CI-passing PRs per contributor; unlimited sequential slots once merged.
- Human, agent-assisted and autonomous-agent submissions are equally eligible under the same deterministic checks.
- Zero AI-slop: fabricated RPC outputs, unpinned reads or broken documentation URLs are closed and disqualified.
- Governance and documentation mismatches only: route security vulnerabilities via Immunefi / Cantina per https://pacta.wtf/.well-known/security.txt.

Every fixture also sets `apache2CommercialGrant: true` and accepts the four fixture rules (`rulesAccepted`):

{rules}
"""


def write_wave2_master_issue(idx, path=None):
    n = len(json.load(open(os.path.join(DOCS, "api", "v1", "protocols.json")))["protocols"])
    with open(path or WAVE2_MASTER_ISSUE, "w") as fh:
        fh.write(wave2_master_issue_md(n))


def wave2_section_html(claims, n_protocols):
    claimed = len(claims)
    cats = "".join(f'<li data-wave2-category="{c}"><b>{E(WAVE2["categories"][c]["label"])}</b> (<code>{c}</code>'
                   + (f', ≥ {tvl_label(c)} TVL' if WAVE2["categories"][c]["minTvlUsd"] else "") + "): "
                   + E(WAVE2_CATEGORY_TEXT[c].format(tvl=tvl_label(c) if WAVE2["categories"][c]["minTvlUsd"] else "", n=n_protocols)) + ".</li>"
                   for c in WAVE2["categories"])
    rows = "".join(f'<tr data-wave2-claim="{E(c["_file"])}"><td class="num">#{i}</td><td><a href="{E(REPO)}/blob/main/{E(WAVE2["fixtureDir"])}/{E(c["_file"])}" '
                   f'target="_blank" rel="noopener"><code>{E(c["_file"])}</code> ↗</a></td><td>{E(c["protocol"])}</td><td><code>{E(c["category"])}</code></td>'
                   f'<td><a href="https://github.com/{E(c["hunter"])}" target="_blank" rel="noopener">@{E(c["hunter"])}</a></td>'
                   f'<td>{E(c.get("agentFramework") or "—")}</td></tr>' for i, c in enumerate(claims, 1))
    table = (f'<table class="ix" data-wave2-claims><thead><tr><th>Slot</th><th>Fixture</th><th>Target</th><th>Category</th><th>Hunter</th><th>Agent framework</th>'
             f'</tr></thead><tbody>{rows}</tbody></table>' if claims else '<p class="s" data-wave2-claims-empty>No Wave 2 slots claimed yet: the first merged fixture takes Slot #1.</p>')
    m_issue = re.fullmatch(re.escape(REPO) + r"/issues/(\d+)", WAVE2_ISSUE_URL)
    issue_label = f"Master issue #{m_issue.group(1)} ↗" if m_issue else "GitHub issues ↗"
    master = md_html(wave2_master_issue_md(n_protocols).split("\n", 2)[2])
    in_epoch = claimed - PRIOR_EPOCH_SLOTS
    return f"""<section class="memo-sec" id="wave-2"><h2>Wave 2 · Epoch {CURRENT_EPOCH}: {ACTIVE_EPOCH_SLOTS} × ${E(REWARD_USDC)} USDC · {PROGRAM_CAP_SLOTS:,}-slot program</h2>
<p class="w2-counter" data-wave2-counter="{in_epoch}" data-wave2-program="{claimed}"><b>{in_epoch} / {ACTIVE_EPOCH_SLOTS} Epoch {CURRENT_EPOCH} Slots Claimed</b> · target cap ${E(ACTIVE_EPOCH_CAP_USDC)} USDC · <b>${E(FUNDED_UNENCUMBERED_USDC)} USDC ({FUNDED_UNENCUMBERED_SLOTS} slots) confirmed unencumbered on-chain now</b><br>{PROGRAM_CAP_SLOTS:,}-Gap Perpetual Program · ${E(REWARD_USDC)} USDC / Merged Net-New Gap · {claimed} / {PROGRAM_CAP_SLOTS:,} program slots merged</p>
<p data-wave2-epochs>Slots open in epochs of 25–100, up to {PROGRAM_CAP_SLOTS:,} in total. Epoch {CURRENT_EPOCH} target cap: {ACTIVE_EPOCH_SLOTS} × ${E(REWARD_USDC)} USDC = ${E(ACTIVE_EPOCH_CAP_USDC)} USDC. <span data-wave2-capacity>${E(FUNDED_UNENCUMBERED_USDC)} USDC ({FUNDED_UNENCUMBERED_SLOTS} slots) is confirmed unencumbered on-chain now; ${E(RING_FENCED_USDC)} USDC in the treasury is separately ring-fenced for {E(RING_FENCED_FOR)}, and the remaining ${E(EPOCH_REMAINING_USDC)} of Epoch {CURRENT_EPOCH} target capacity unlocks as confirmed Base USDC top-ups land.</span> <b>Net-new only:</b> a finding qualifies only if it is not already published in <a href="../api/v1/protocols.json">/api/v1/protocols.json</a> when the PR is opened, and <code>post_pin_drift</code> must be read at a block strictly after Pacta&#x27;s latest pinned block for that protocol.</p>
<p>One slot per merged, verified control-plane mismatch, in one of three categories:</p>
<ol>{cats}</ol>
<p>Targets already in <a href="../api/v1/protocols.json">/api/v1/protocols.json</a> qualify only as <code>post_pin_drift</code>; each target (chain + contract address, and slug) can be claimed once across the pool.</p>
<h3>Throughput &amp; settlement</h3>
<ul><li>Up to <b>{WAVE2["maxOpenPrsPerContributor"]} concurrent open CI-passing PRs per contributor</b>; unlimited sequential slots once merged.</li>
<li data-wave2-payout>{E(WAVE2_PAYOUT)}</li></ul>
<h3>Submit</h3>
<p>Commit exactly one new file, <code data-wave2-fixture>{E(WAVE2["fixtureDir"])}/&lt;chain&gt;-&lt;slug&gt;.json</code> (<code>&lt;chain&gt;</code> = ethereum, base or arbitrum; schema: <a href="{E(REPO)}/blob/main/{E(WAVE2["fixtureDir"])}/README.md" target="_blank" rel="noopener">{E(WAVE2["fixtureDir"])}/README.md ↗</a>), with a live Pacta <code>/mcp</code> proof (<code>mcpProof</code>), a dual-RPC <code>cast</code> proof pinned with <code>--block</code>, the official docs quote and your EIP-55 <code>basePayoutAddress</code>. Check it offline with <code>python3 tools/verify_bounty_submission.py --json {E(WAVE2["fixtureDir"])}/&lt;chain&gt;-&lt;slug&gt;.json</code>. CI accepts only a PR that adds that single JSON file and runs the validator from the base branch. Rolling issue: <a href="{E(WAVE2_ISSUE_URL)}" target="_blank" rel="noopener" data-wave2-issue>{issue_label}</a> · ranked hunters: <a href="../leaderboard/">Hunter leaderboard →</a></p>
<p data-community>Questions about a target, a fixture or the MCP tools? Ask in <a href="{E(COMMUNITY_URL)}" target="_blank" rel="noopener">Community Q&amp;A (Discussions) ↗</a>, in the <a href="{E(COMMUNITY_QA_URL)}" target="_blank" rel="noopener">Builder &amp; Bounty Q&amp;A thread ↗</a>.</p>
<h3>Claimed slots</h3>
{table}
<details class="bounty-issue" id="wave-2-issue" data-wave2-issue-text><summary>{E(WAVE2["title"])}</summary><div class="md">{master}</div></details></section>
"""


def leaderboard_page(idx, lb, claims):
    rows = hunter_stats(lb, claims)
    fws = framework_stats(rows)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    hrows = []
    for h in rows:
        hid = f"hunter-{h['handle'].lower()}"
        md = badge_markdown(h["handle"])
        catches = "<br>".join(f'<a href="{E(c["href"])}" target="_blank" rel="noopener">{E(c["label"])} ↗</a> <span class="s">{E(c["protocol"])}</span>'
                              for c in h["catches"])
        hrows.append(f'<tr id="{E(hid)}" data-hunter="{E(h["handle"])}"><td class="num">{h["rank"]}</td>'
                     f'<td><a href="https://github.com/{E(h["handle"])}" target="_blank" rel="noopener">@{E(h["handle"])}</a><div class="s">{catches}</div></td>'
                     f'<td>{E(", ".join(h["frameworks"]) or "not stated")}</td><td class="num">{len(h["catches"])}</td><td class="num">{len(h["protocols"])}</td>'
                     f'<td class="num">{h["eas"]}</td><td>{settled_cell(h["settled"], h["txs"])}</td>'
                     f'<td><img class="cp-badge" src="../badges/hunters/{E(h["handle"])}.svg" alt="Pacta hunter: {E(h["handle"])}" height="20">'
                     f'<div class="lb-share">{copy_btn(md, "Copy badge Markdown")}'
                     f'<a class="copy" href="{E(share_x_href(h))}" target="_blank" rel="noopener" data-share-x>Share on X ↗</a></div></td></tr>')
    frows = "".join(f'<tr data-framework="{E(f["name"])}"><td>{E(f["name"])}</td><td class="num">{f["hunters"]}</td><td class="num">{f["catches"]}</td>'
                    f'<td class="num">{len(f["protocols"])}</td><td>{usdc(f["settled"]) + " USDC" if f["settled"] else "$0.00 (pending settlement)"}</td></tr>'
                    for f in fws)
    total_settled = sum(h["settled"] for h in rows)
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "Pacta hunter leaderboard", "url": f"{BASE_URL}/leaderboard/",
          "isPartOf": {"@type": "WebSite", "name": "Pacta by Fractal Neurons", "url": f"{BASE_URL}/"},
          "about": "Verified on-chain control-plane mismatch catches by bounty hunters and agent frameworks", "publisher": ORG_LD}
    ld_json = json.dumps(ld, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    body = f"""<body>
{topbar("../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../">Pacta</a> / <a href="../bounties/">Bounties</a> / Leaderboard</div>
<article class="memo">
<header><span class="tier">Bounties · hunter leaderboard</span><h1>Pacta hunter leaderboard</h1>
<p class="lede">Every verified on-chain control-plane mismatch merged through the <a href="../bounties/">Pacta bounties</a>, credited to its GitHub hunter and agent framework. Ranked by verified catches, then protocols covered, Base EAS attestations and settled Base USDC. Settled USDC counts only payouts with a Base transaction hash (linked to BaseScan).</p></header>
<section class="memo-sec" id="hunters"><h2>Hunters</h2>
<table class="ix" data-leaderboard><thead><tr><th>Rank</th><th>Hunter</th><th>Agent framework</th><th>Verified catches</th><th>Protocols covered</th><th>Base EAS attestations</th><th>Settled Base USDC</th><th>README badge</th></tr></thead><tbody>{"".join(hrows)}</tbody></table>
<p class="s">{len(rows)} hunters · {sum(len(h["catches"]) for h in rows)} verified catches · settled so far: {usdc(total_settled)} USDC. Wave 1 ledger: <a href="../bounties/#wave-1">/bounties/#wave-1</a>; Wave 2 pool: <a href="../bounties/#wave-2">/bounties/#wave-2</a>.</p></section>
<section class="memo-sec" id="frameworks"><h2>Agent frameworks</h2>
<table class="ix" data-frameworks><thead><tr><th>Framework</th><th>Hunters</th><th>Verified catches</th><th>Protocols covered</th><th>Settled Base USDC</th></tr></thead><tbody>{frows}</tbody></table>
<p class="s">The framework is what the hunter declared (<code>agentFramework</code> in the Wave 2 fixture); "not stated" when none was given.</p></section>
<section class="memo-sec" id="badges"><h2>README badges</h2>
<p data-community>Questions or a catch to discuss: <a href="{E(COMMUNITY_URL)}" target="_blank" rel="noopener">Community Q&amp;A (Discussions) ↗</a> · <a href="{E(COMMUNITY_QA_URL)}" target="_blank" rel="noopener">Builder &amp; Bounty Q&amp;A thread ↗</a></p>
<p>Each hunter has a static badge at <code>{E(BASE_URL)}/badges/hunters/&lt;handle&gt;.svg</code>, rebuilt with the site. <b>Copy badge Markdown</b> puts a linked badge in your clipboard for a GitHub README; <b>Share on X</b> opens a pre-filled post.</p></section>
</article>
<div class="memo-foot"><span>Governance and documentation mismatches only. Exploit-sensitive vulnerabilities are never published here; they go through Immunefi or Cantina bounty programmes.</span><a href="../bounties/">Bounties →</a></div>
</main>
{footer(count_line, reg, "../")}
<script type="application/ld+json">{ld_json}</script>
</body></html>
"""
    return head("Hunter leaderboard · Pacta bounties", "Verified on-chain control-plane catches by hunter and agent framework, with settled Base USDC and README badges.",
                f"{BASE_URL}/leaderboard/", prefix="../", og_title="Pacta hunter leaderboard") + "\n" + body


def mcp_page(idx):
    """docs/mcp/index.html (pacta.wtf/mcp/): a static landing page for people and tools that open /mcp on the site. The MCP
    endpoint itself is the Streamable-HTTP JSON-RPC server on the Worker (MCP_URL); this page only documents it."""
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    claude = f"claude mcp add --transport http pacta {MCP_URL}"
    cursor = json.dumps({"mcpServers": {"pacta": {"url": MCP_URL}}}, indent=2)
    tools = "".join(f"<li><code>{E(t)}</code></li>" for t in B2A.REMOTE_TOOLS)
    starter = "https://github.com/Fractal-Neurons/defi-control-plane-mcp"
    rest = f'{CURL} "{API}/v1/check/preflight?chain=base&address=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"'
    py = ('import json, urllib.request as u; r = u.Request("' + API + '/v1/check/preflight?chain=base&address=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", '
          'headers={"User-Agent": "' + UA + '"}); print(json.load(u.urlopen(r))["verdict"])')
    body = f"""<body>
{topbar("../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../">Pacta</a> / MCP</div>
<article class="memo">
<header><span class="tier">Remote MCP · free · zero install</span><h1>Pacta MCP server</h1>
<p class="lede">The live Model Context Protocol endpoint is <code data-mcp-endpoint>{E(MCP_URL)}</code>: Streamable HTTP, JSON-RPC 2.0, stateless (no session), <b>no API key and no wallet</b>, {E(RATE_LIMIT)}. This page on pacta.wtf only documents it; point your MCP client at the endpoint above.</p></header>
<section class="memo-sec" id="install"><h2>Install</h2>
<div class="qs-snip"><span class="qs-l">Claude Code</span><code class="mono">{E(claude)}</code>{copy_btn(claude)}</div>
<div class="qs-snip"><span class="qs-l">Cursor (mcp.json)</span><code class="mono">{E(json.dumps({"mcpServers": {"pacta": {"url": MCP_URL}}}))}</code>{copy_btn(cursor, "Copy JSON")}</div>
<p>Optional attribution: <code>caller_agent</code>, <code>requester_role</code> and <code>caller_purpose</code> (non-personal; omitted fields never block a call; see <a href="../SKILL.md">SKILL.md</a>).</p>
<div class="qs-snip"><span class="qs-l">REST (curl)</span><code class="mono">{E(rest)}</code>{copy_btn(rest)}</div>
<div class="qs-snip"><span class="qs-l">Python (stdlib)</span><code class="mono">{E(py)}</code>{copy_btn(py)}</div>
<p class="s">{E(UA_NOTE)}</p></section>
<section class="memo-sec" id="tools"><h2>Tools ({E(B2A.REMOTE_TOOLS_DOC)})</h2><ul>{tools}</ul>
<p>Indexed protocols: <a href="../api/v1/protocols.json">/api/v1/protocols.json</a> · machine-readable server card: <a href="../.well-known/mcp.json">/.well-known/mcp.json</a> · REST twin and OpenAPI 3.1: <a href="{E(OPENAPI_URL)}" target="_blank" rel="noopener">openapi.json ↗</a></p></section>
<section class="memo-sec" id="starter"><h2>Starter kit &amp; help</h2>
<p>Ready-to-copy client configs and stdlib examples: <a href="{E(starter)}" target="_blank" rel="noopener">Fractal-Neurons/defi-control-plane-mcp ↗</a>. Questions: <a href="{E(COMMUNITY_QA_URL)}" target="_blank" rel="noopener">Community Q&amp;A (Discussions) ↗</a>.</p></section>
</article>
<div class="memo-foot"><span>Read-only on-chain analysis. Not investment advice.</span><a href="../#preflight">Try the free pre-flight check →</a></div>
</main>
{footer(count_line, reg, "../")}
</body></html>
"""
    return head("Pacta MCP server · free remote MCP endpoint", "Free remote MCP server for DeFi control-plane checks: Streamable HTTP, no API key, no wallet.",
                f"{BASE_URL}/mcp/", prefix="../", og_title="Pacta MCP server") + "\n" + body

def llms(idx, radar):
    c = counts(idx)
    a = idx["onchain_anchoring"]
    r = radar["refreshed_at"]
    lines = [
        "# Pacta by Fractal Neurons", "",
        DISAMBIGUATION, "",
        f"> {BRAND}: free pre-execution contract and governance safety API for AI agents (launch: $0, no API key, no wallet), plus block-pinned DeFi control-plane snapshots and timelock alerts. {coverage_line(idx)}.", "",
        "Pacta checks who can change the rules of DeFi protocols (proxy admins, timelock delays, Safe quorums, roles) and compares that with what the protocols document. Every record is a read-only on-chain observation pinned to a block number and canonical block hash on its chain (" + counts(idx)["chains"] + ").", "",
        "## Free API for agents (launch: $0, no API key, no wallet)",
        f"- Remote MCP (Streamable HTTP, zero install): {MCP_URL} · Claude Code: `claude mcp add --transport http pacta {MCP_URL}` · Cursor: `{{\"mcpServers\": {{\"pacta\": {{\"url\": \"{MCP_URL}\"}}}}}}`. Tools ({REMOTE_TOOLS_DOC}): {', '.join(B2A.REMOTE_TOOLS)}. Local stdio server: {STDIO_TOOLS_DOC}.",
        "- " + B2A.CALLER_FIELDS_DOC,
        "- " + B2A.protocols_line(idx, load_pinned()),
        f"- One call: `{CURL} \"{API}/v1/check/preflight?chain=ethereum&address=0x...\"` ({UA_NOTE}) returns a verdict (IMMUTABLE_NO_ADMIN, TIMELOCK_PROTECTED, ZERO_DELAY_TIMELOCK_RISK, MULTISIG_NO_TIMELOCK, INSTANT_EOA_ADMIN_RISK, UNDEPLOYED_OR_EOA, UNCLASSIFIED_CONTRACT_CONTROLLER), a 0-100 risk score, proxy / admin / timelock breakdown and pause / blacklist / upgrade capabilities, pinned to a block hash.",
        f"- [{B2A.LOOKUP_URL}?q=ethena]({B2A.LOOKUP_URL}?q=ethena): free protocol / token name lookup (MCP tool pacta_lookup_protocol). {B2A.LOOKUP_DOC}",
        f"- {B2A.REQUEST_DOC}",
        f"- [{BASE_URL}/bounties/]({BASE_URL}/bounties/): {B2A.BOUNTIES_DOC}",
        f"- [{BASE_URL}/bounties/#wave-2]({BASE_URL}/bounties/#wave-2): {B2A.WAVE2_DOC}",
        f"- [{BASE_URL}/leaderboard/]({BASE_URL}/leaderboard/): {B2A.LEADERBOARD_DOC}",
        f"- [{B2A.COMMUNITY_URL}]({B2A.COMMUNITY_URL}): {B2A.COMMUNITY_DOC}",
        f"- [{OPENAPI_URL}]({OPENAPI_URL}): OpenAPI 3.1 for ChatGPT Actions, LangChain and OpenAPI tools; every route takes GET query parameters or a POST JSON body. {RATE_LIMIT}; free during the launch (pricingMode free_launch), x402 v1 + v2 ready.",
        f"- [{BASE_URL}/protocols/]({BASE_URL}/protocols/): per-protocol control-plane safety records.",
        f"- [{BASE_URL}/integrations/vault-factories/]({BASE_URL}/integrations/vault-factories/): free building blocks for vault factories and curators (Morpho Vault V2, Euler EVK, Veda BoringVault, Lagoon, Upshift, Mellow): a Control-Plane & Role Map tab from /api/v1/protocols.json, status badges (/badges/<slug>.svg; live {API}/v1/badges/<slug>.svg), and PactaSentinelGuard.sol, a cap-increase tripwire that never blocks a decrease.", "",
        "## Agent feeds",
        f"- [{BASE_URL}/llms-full.txt]({BASE_URL}/llms-full.txt): complete single-file reference (feeds, MCP tools, x402, anchoring, every record, proposal and queued operation).",
        f"- [{BASE_URL}/api/v1/proposals.json]({BASE_URL}/api/v1/proposals.json): schema `pacta.governance_proposals_feed.v1`; live Aave / Euler / Morpho / Sky proposals mapped to block-pinned observations.",
        f"- [{BASE_URL}/.well-known/agent.json]({BASE_URL}/.well-known/agent.json) (A2A Agent Card) · [{BASE_URL}/.well-known/mcp.json]({BASE_URL}/.well-known/mcp.json) (MCP manifest) · [{BASE_URL}/SKILL.md]({BASE_URL}/SKILL.md) (portable agent skill).", "",
        "## Data",
        f"- [{BASE_URL}/api/v1/index.json]({BASE_URL}/api/v1/index.json): schema `{idx['schema']}`; `summary_metrics` (sprints_completed={c['sprints']}, records_indexed={c['records']}, parameter_deltas={c['delta']}, protective_deltas={c['protect']}, aligned_baselines={c['aligned']}); each entry has id, protocol, category, sprint, block_number, block_hash, classification, surface, target_contract, target_label, check_type, selector_or_slot, call_signature, call_args, repro_calldata, onchain_observed, documented_reference, observed/documented delay seconds, summary_doc, summary_sha256, base_eas_uid.",
        f"- [{BASE_URL}/api/v1/rpc-pinned.json]({BASE_URL}/api/v1/rpc-pinned.json): schema `{PINNED_SCHEMA}`; {len(load_pinned()['entries'])} RPC-pinned control-plane records on Ethereum and Base (block number + hash, cast reproduction). NOT EAS-attested: no sprint, summary document or Base EAS UID.",
        f"- [{BASE_URL}/api/v1/protocols.json]({BASE_URL}/api/v1/protocols.json): schema `pacta.protocols.v1`; every published protocol (33 Base-EAS-attested, 20 RPC-observed with documentationComparison not_assessed) with badge tier and URLs, Sprint ids and EAS UIDs, controller and every pinned surface (block number + hash).",
        f"- [{BASE_URL}/api/v1/radar.json]({BASE_URL}/api/v1/radar.json): queued timelock operations, refreshed at finalized block {r['block_number']} ({r['block_time_utc']}); each operation carries pending / done / ready (delay elapsed, still unexecuted).",
        f"- [{BASE_URL}/api/v1/forum-digest.json]({BASE_URL}/api/v1/forum-digest.json): schema `{FORUM_SCHEMA}`; read-only digest of active governance forum topics plus `addressIndex` (chain:address -> protocol family).", "",
        "## Live pre-execution briefs",
    ] + [f"- [{BASE_URL}/briefs/{k}/]({BASE_URL}/briefs/{k}/): {v}" for k, v in BRIEFS.items()] + [
        "", "## Live onboarding verification briefs (assets proposed as collateral; block-pinned)",
        f"- [{BASE_URL}/api/v1/onboarding.json]({BASE_URL}/api/v1/onboarding.json): schema `pacta.onboarding_briefs.v1`; every check with call, calldata, raw result and decoded value; role maps replayed from events.",
    ] + [f"- [{BASE_URL}/briefs/{b['slug']}/]({BASE_URL}/briefs/{b['slug']}/): {OR.summary(b)} ({b['forum']['name']} #{b['forum']['topic']}; {OR.CHAIN_NAME[b['chain']]} block {b['pin']['number']})"
         for b in load_onboarding()["briefs"]] + [
        f"- [{BASE_URL}/demos/swapio-x402/]({BASE_URL}/demos/swapio-x402/): 90-second x402 storyboard (TreasuryGuard) with a live, on-chain-verified Base USDC settlement receipt.", "",
        "## Methodology",
        "- Scanner seats replay read-only eth_call / eth_getStorageAt at the cited block (two independent archive RPCs); an isolated verifier seat re-checks selectors, EIP-55 checksums, EIP-1967 slots and arithmetic offline.",
        f"- Classifications: {CLASS_DEFINITIONS}.",
        f"- {VULN_ROUTE}", "",
        "## Access",
        "- Free and real-time for everyone, including vault curators, allocators and AI risk agents: every indexed record, the timelock radar, the briefs, /api/v1/*.json and this file. No key, no delay, no paywall; curators never pay.", "",
        "## On-chain anchoring (Base, chain id 8453)",
        f"- PactaCommitmentRegistry: `{a['commitment_registry']}` (Sourcify verified); attester `pacta.base.eth` (`{a['attester_eoa']}`).",
        f"- EAS schema: `{a['eas_schema_uid']}`. {anchoring_text(c)}",
    ] + [f"- Multi-attest tx, Sprints {r_}: `{tx}`" for r_, tx in c["multi_txs"].items()] + [
        "- Per-sprint attestation UIDs: `onchain_anchoring.sprint_eas_attestations` in /api/v1/index.json; each record's `base_eas_uid`.", "",
        "## Engagements (collateral and protocol issuers only; curators, risk teams and agents never pay)",
        f"- 24h Onboarding & Delta Clearance: {CLEARANCE_PRICE} flat. Archive-RPC control-plane verification, an upstream GitBook / docs reconciliation PR and a Curator Diligence Dossier (PDF + JSON) for Morpho, Euler, Aave and Sky forum proposals, within a 24h SLA. The resulting classification strictly follows verified on-chain and documentation evidence: a parameter_delta flag changes only when the chain or the docs align at a new finalized block. Free alternative: a public doc-update notification ({BASE_URL}/request/?tier=community). Request: {BASE_URL}/request/?tier=clearance",
        f"- Continuous Aligned Maintenance: {MONITORING_PRICE}. Keeps the Aligned attestation and dossier current across governance proposals, signer rotations and timelock upgrades. Request: {BASE_URL}/request/?tier=continuous",
        f"- High-throughput API (> 60 requests / minute or a dedicated SLA): x402 metered endpoints, or an Enterprise API key priced on scope: {BASE_URL}/request/?tier=api_sla",
        f"- Settlement, Option A (recommended for protocol treasuries): a formal commercial invoice (PDF) with verified counterparty payment instructions, issued on scope confirmation; no upfront transfer is needed to open intake.",
        f"- Settlement, Option B (direct express): USDC on Base (`{USDC['Base']}`) or Ethereum (`{USDC['Ethereum']}`) to the Pacta treasury (direct settlement EOA) `{a['treasury_admin']}` (an externally owned account; the same address on both chains).",
        "- Community queue: free, unscheduled (typically 6–8 weeks).",
        f"- Request: {BASE_URL}/request/ (builds a scope brief; opens a pre-filled GitHub intake issue or Gmail compose, or copies the brief). Prefill: `?tier=clearance|continuous|api_sla&protocol=<slug>&forum=<https URL>&settlement=invoice|direct`.", "",
        "## x402 API (live; free during the launch)",
        f"- On-demand scans of contracts outside the index. Free launch: every route answers HTTP 200 at $0 with no payment header (pricingMode free_launch); the x402 flow below applies only when the operator switches pricingMode to x402_paid. Live gateway: {B2A.X402_URL} (Cloudflare Worker, x402Versions [1, 2]: v1 network `base` with `X-PAYMENT` / `X-PAYMENT-RESPONSE`, v2 network `{B2A.X402_NETWORK_V2}` with `PAYMENT-REQUIRED` / `PAYMENT-SIGNATURE` / `PAYMENT-RESPONSE`; USDC on Base, payTo `{B2A.PAY_TO}`, maxTimeoutSeconds {B2A.X402_MAX_TIMEOUT_S}). Routes (x402_paid prices): `GET /v1/check/preflight?chain=&address=` ($0.01), `GET /v1/scan/control-plane?chain=&address=` ($0.10), `GET /v1/scan/timelock-op?chain=&timelock=&opId=` ($0.25), `GET /v1/scan/proposal-diff?forum=&topicId=` ($0.15), `GET /v1/briefs/live-timelocks` ($0.10); free `/health`, `/.well-known/x402` (Bazaar discovery), `/v1/sample/control-plane`. A bare GET (no query) or zero-byte POST with no payment header on a paid route returns HTTP 402 with both challenges; the Bazaar extension carries a JSON Schema draft 2020-12 schema.",
        f"- Remote MCP: {MCP_URL} (free, no install). Local stdio server (from a clone of the repo; npm publication pending): set `PACTA_X402_URL={B2A.X402_URL}` to enable the scan tools; in x402_paid mode pay with `xPaymentHeader` (v1) or `paymentSignatureHeader` (v2). The MCP client does not re-check receipts on-chain (onchainReceiptVerified: false); the gateway does.",
        f"- Gateway settlement guard: {B2A.X402_GATEWAY_GUARD_NOTE}", "",
        "## Contact",
        f"- {CONTACT} · {REPO} · {FN} · security: {BASE_URL}/.well-known/security.txt", "",
    ]
    return "\n".join(lines)


def llms_html(idx, text):
    """docs/llms/index.html: the exact llms.txt text in a semantic HTML page (some chat URL fetchers only accept text/html)."""
    c = counts(idx)
    count_line = coverage_line(idx)
    reg = idx["onchain_anchoring"]["commitment_registry"]
    alt = f'<link rel="alternate" type="text/plain" href="{BASE_URL}/llms.txt" title="llms.txt (plain text)">'
    ld = org_ld_script()
    body = f"""<body>
{topbar("../")}
<main id="main" class="memo-wrap">
<div class="crumbs"><a href="../">Pacta</a> / llms.txt</div>
<article class="memo">
<header><span class="tier">For agents</span><h1>llms.txt (HTML mirror)</h1>
<p class="lede">The same text as <a href="../llms.txt">/llms.txt</a> (plain text), rendered as HTML for fetchers that only read web pages. The complete single-file reference is <a href="../llms-full.txt">/llms-full.txt</a>.</p></header>
<pre class="llms" data-llms-mirror>{E(text)}</pre>
</article>
</main>
{footer(count_line, reg, "../")}
{ld}
</body></html>
"""
    return head("llms.txt · Pacta (HTML mirror)", "Pacta llms.txt as HTML: free pre-execution contract checks for AI agents, feeds, MCP and data.",
                f"{BASE_URL}/llms/", prefix="../", og_title="Pacta llms.txt", extra=alt) + "\n" + body


ROBOTS_TXT = "User-agent: *\nAllow: /\n\nSitemap: https://pacta.wtf/sitemap.xml\n"


def feed_items(idx, radar):
    """Feed entries, newest Sprint first, then the radar: (id, title, url, updated ISO-8601 UTC, summary text). Dates come from the
    data (index generated_at for Sprint attestations, the radar's finalized block time for timelock items), never the wall clock."""
    import datetime as _dt
    iso = lambda ts: _dt.datetime.fromtimestamp(int(ts), _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    gen = idx["generated_at"]
    uids = idx["onchain_anchoring"]["sprint_eas_attestations"]
    by_sprint = {}
    for e in idx["entries"]:
        by_sprint.setdefault(int(e["sprint"]), []).append(e)
    out = []
    for n in sorted(by_sprint, reverse=True):
        es = by_sprint[n]
        names = sorted({e["protocol"] for e in es})
        cls = [e["classification"] for e in es]
        uid = uids.get(str(n))
        out.append((f"{BASE_URL}/#sprint-{n}", f"Sprint {n} Base EAS attestation: {len(es)} records, {len(names)} protocols",
                    f"https://base.easscan.org/attestation/view/{uid}" if uid else f"{BASE_URL}/api/v1/index.json", gen,
                    f"{', '.join(names)}. {cls.count('aligned_baseline')} aligned, {cls.count('protective_delta')} protective delta, "
                    f"{cls.count('parameter_delta')} parameter delta. Summary: {REPO}/blob/main/{es[0]['summary_doc']}"))
    r = radar["refreshed_at"]
    for it in radar["items"]:
        done = all(o.get("done") for o in it["operations"])
        out.append((f"{BASE_URL}/{it['brief'].strip('/')}/#radar", f"{it['protocol']} timelock: {'executed' if done else 'pending'} · {it['title']}",
                    f"{BASE_URL}/{it['brief'].strip('/')}/", iso(r["block_timestamp"]),
                    f"{it['summary']} Read at finalized Ethereum block #{r['block_number']:,}."))
    return out


def atom_feed(idx, radar):
    items = feed_items(idx, radar)
    upd = max(i[3] for i in items)
    X_ = lambda s: E(s)
    entries = "".join(f'  <entry>\n    <id>{X_(i)}</id>\n    <title>{X_(t)}</title>\n    <link href="{X_(u)}"/>\n    <updated>{d}</updated>\n'
                      f'    <summary>{X_(s)}</summary>\n  </entry>\n' for i, t, u, d, s in items)
    return ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n'
            f'  <id>{BASE_URL}/feed.xml</id>\n  <title>Pacta: Sprint attestations and timelock radar</title>\n'
            f'  <subtitle>Block-pinned DeFi control-plane records (Base EAS) and queued timelock operations</subtitle>\n'
            f'  <link rel="self" href="{BASE_URL}/feed.xml"/>\n  <link href="{BASE_URL}/"/>\n  <updated>{upd}</updated>\n'
            f'  <author><name>Pacta by Fractal Neurons</name><uri>{BASE_URL}/</uri></author>\n{entries}</feed>\n')


def json_feed(idx, radar):
    items = feed_items(idx, radar)
    return json.dumps({"version": "https://jsonfeed.org/version/1.1", "title": "Pacta: Sprint attestations and timelock radar",
                       "home_page_url": f"{BASE_URL}/", "feed_url": f"{BASE_URL}/api/v1/feed.json",
                       "description": "Block-pinned DeFi control-plane records (Base EAS) and queued timelock operations",
                       "authors": [{"name": "Pacta by Fractal Neurons", "url": f"{BASE_URL}/"}], "language": "en",
                       "items": [{"id": i, "title": t, "url": u, "date_published": d, "content_text": s} for i, t, u, d, s in items]},
                      indent=1, ensure_ascii=False) + "\n"
# RFC 9309: "User-agent: *" + "Allow: /" already admits every crawler. No bot-name stanzas: an explicit Google-Extended
# stanza tripped a naive opt-out matcher in Gemini's url_context fetcher even when paired with Allow: /.


SITE_DATE_FALLBACK = "2026-11-15"


def site_date(idx, radar, pinned=None, onb=None):
    """The sitemap <lastmod>: the newest YYYY-MM-DD in the pinned data (index.json generated_at, the radar's finalized block
    time, rpc-pinned.json / onboarding.json generated_at), never the wall clock, so a rebuild after 00:00 UTC is byte-identical."""
    cands = [idx.get("generated_at"), (radar.get("refreshed_at") or {}).get("block_time_utc"),
             (pinned or {}).get("generated_at"), (onb or {}).get("generated_at")]
    days = [c[:10] for c in cands if isinstance(c, str) and re.match(r"^\d{4}-\d{2}-\d{2}", c)]
    return max(days) if days else SITE_DATE_FALLBACK


def main():
    idx, radar = load()
    today = site_date(idx, radar, load_pinned(), load_onboarding())     # deterministic (Codex F3): no wall-clock date

    def w(rel, text):
        p = os.path.join(DOCS, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(text)
    w("index.html", page(idx, radar))
    w("request/index.html", request_page(idx))
    for slug, desc in BRIEFS.items():
        w(f"briefs/{slug}/index.html", brief_page(slug, desc, idx, radar))
    onb = load_onboarding()
    for b in onb["briefs"]:
        w(f"briefs/{b['slug']}/index.html", onboarding_page(b, idx))
    pinned = load_pinned()                        # docs/api/v1/rpc-pinned.json (RPC-pinned, not EAS-attested)
    B2A.write_all(DOCS, idx, radar, onb, pinned)  # proposals.json, llms-full.txt, .well-known/{agent,mcp}.json, SKILL.md
    llms_text = llms(idx, radar)
    w("llms.txt", llms_text)
    w("llms/index.html", llms_html(idx, llms_text))
    sp = site_protocols(idx, pinned)
    LK.write_all(ROOT, DOCS, sp, onb, radar, BRIEF_PROTOCOL)   # api/v1/lookup.json + packages/mcp-server/src/lookup.mjs catalog
    GM.write(ROOT, DOCS)                          # api/v1/graph-manifest.json: durable protocol graph (from protocols/index/rpc-pinned.json)
    digest = load_forum_digest()                  # data/forum-digest.json (optional; missing = empty digest)
    w("api/v1/forum-digest.json", forum_digest_json(idx, digest, pinned))
    for name, v in sp.items():
        w(f"protocols/{v['slug']}/index.html", protocol_page(name, v["entries"], idx, radar, digest, v["slug"]))
    w("protocols/index.html", protocols_index_page(idx, sp))
    w("integrations/vault-factories/index.html", vault_factories_page(idx, sp))
    claims = load_wave2_claims()
    w("bounties/index.html", bounties_page(idx, radar, claims=claims))
    lb = load_leaderboard()
    w("leaderboard/index.html", leaderboard_page(idx, lb, claims))
    w("mcp/index.html", mcp_page(idx))
    write_hunter_badges(hunter_stats(lb, claims))
    write_wave2_master_issue(idx)
    w("404.html", not_found_page(idx, sp))       # GitHub Pages serves it for any missing path
    w("robots.txt", ROBOTS_TXT)
    w("theme.js", THEME_JS)                       # theme bootstrap (render-blocking, same origin): no inline JS anywhere
    w("feed.xml", atom_feed(idx, radar))
    w("api/v1/feed.json", json_feed(idx, radar))
    urls = ["/", "/request/", "/llms.txt", "/api/v1/index.json", "/api/v1/radar.json"] + [f"/briefs/{k}/" for k in BRIEFS] + \
        [f"/briefs/{b['slug']}/" for b in load_onboarding()["briefs"]] + (["/api/v1/onboarding.json"] if load_onboarding()["briefs"] else []) + \
        ["/api/v1/proposals.json", "/api/v1/rpc-pinned.json", "/api/v1/lookup.json", "/api/v1/protocols.json", "/api/v1/graph-manifest.json", "/integrations/vault-factories/", "/llms/", "/llms-full.txt", "/SKILL.md", "/.well-known/agent.json", "/.well-known/mcp.json",
         "/demos/swapio-x402/", "/bounties/", "/leaderboard/", "/mcp/", "/protocols/", "/feed.xml", "/api/v1/feed.json"] + [f"/protocols/{v['slug']}/" for v in sp.values()]
    w("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f"  <url><loc>{BASE_URL}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    w(".well-known/security.txt", f"Contact: mailto:{CONTACT}\nExpires: 2027-11-13T00:00:00.000Z\nPreferred-Languages: en\n"
      f"Canonical: {BASE_URL}/.well-known/security.txt\nPolicy: {BASE_URL}/#faq\n")
    w(".nojekyll", "")    # GitHub Pages: serve dot-directories such as /.well-known/
    c = counts(idx)
    print(f"built: {c['sprints']} sprints, {c['records']} records; radar block {radar['refreshed_at']['block_number']}; base {BASE_URL}")


if __name__ == "__main__":
    main()
