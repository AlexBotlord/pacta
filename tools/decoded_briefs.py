"""v4.6: the radar pre-execution briefs rendered from tools/briefs_decoded.json (schema pacta.decoded_briefs.v1); Sprint 27 adds the fifth, Sprint 28 the sixth.

tools/briefs_decoded.json is the decoder's output, committed byte-for-byte: scheduling logs, decoded calls, current vs new state,
verified sources (Sourcify), risk notes and `cast` reproduction commands. Every value in it was read at a finalized block
(Ethereum Mainnet or Base) on two independent public RPC endpoints that agreed. This module adds only the editorial frame
(headline, lede, badges, key-figure labels); every address, amount, block and transaction on the page comes from the JSON, and
every explorer link goes to the brief's own chain: Etherscan for chain id 1, Basescan for chain id 8453 (never Etherscan for a
Base brief). build_site.brief_page() adds the radar meta block, the post-ETA banner and the clearance callout around it.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from onboarding_scan import eip55  # noqa: E402  (pure keccak / EIP-55; never touches the network)

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "briefs_decoded.json")
SCHEMA = "pacta.decoded_briefs.v1"
CHAIN_BY_ID = {1: "ethereum", 8453: "base"}
ADDR_RE = re.compile(r"0x[0-9a-fA-F]{40}")
WAD = 10 ** 18

# Editorial frame only. Figures in the key-figure tiles are computed from the JSON in kpis() below.
EDITORIAL = {
    "lombard-ops-0xceee-0x2f2a-0x6404": {
        "title": "Pacta Governance Radar · Pre-Execution Brief — Lombard LBTC Ops 0xceee, 0x2f2a, 0x6404",
        "h1": "Lombard <code>LBTC</code> — Three Queued Proxy Upgrades Add a Per-Mint Deposit Fee",
        "lede": ("Pre-execution decode of three independent LombardTimeLock operations that upgrade AssetRouter, BTC.b (NativeLBTC) and "
                 "LBTC (StakedLBTC). The fee starts at 0, the three can execute in any order, and resuming paused LBTC transfers "
                 "no longer waits for the timelock."),
        "badges": [("badge-cyan", "Pre-execution brief"), ("badge-amber", "Order hazard: BTC.b before AssetRouter"),
                   ("badge-amber", "unpauseTransfers leaves the timelock")],
        "state_title": "Proxies: current vs queued implementation",
    },
    "beefy-base-op-0x3302": {
        "title": "Pacta Governance Radar · Pre-Execution Brief — Beefy CLM on Base Op 0x3302",
        "h1": "Beefy CLM <code>cowAeroBaseUSDC-VVV</code> on Base — Calm-Check Tolerance Widened to 25 Ticks",
        "lede": ("Pre-execution decode of one Base Mainnet timelock operation: setDeviation(25) widens how far the Aerodrome USDC/VVV "
                 "pool tick may sit from its TWAP before the strategy refuses to act. A parameter change, not a strategy upgrade."),
        "badges": [("badge-cyan", "Pre-execution brief"), ("badge-cyan", "Base Mainnet · chain id 8453"),
                   ("badge-amber", "Looser price-manipulation guard")],
        "state_title": "Strategy state at the pinned Base block",
    },
    "ethena-ops-0xb028-0xca05-0x108e-0x070a": {
        "title": "Pacta Governance Radar · Pre-Execution Brief — Ethena USDe Ops 0xb028, 0xca05, 0x108e, 0x070a",
        "h1": "Ethena <code>USDe</code> — Mint Caps Cut to 50M, USDm Delisted, Bridge Limits Reset, a Custodian Added",
        "lede": ("Pre-execution decode of four independent EthenaTimelockController operations on EthenaMinting and the USDe OFT "
                 "adapter (LayerZero). Three tighten or rebalance limits; one adds an externally owned account as a custodian."),
        "badges": [("badge-cyan", "Pre-execution brief"), ("badge-green", "Mint caps tightened"),
                   ("badge-amber", "New custodian is an EOA")],
        "state_title": "EthenaMinting and the USDe OFT adapter at the pin",
    },
    "yearn-v3-op-0x2a14": {
        "title": "Pacta Governance Radar · Pre-Execution Brief — Yearn V3 Op 0x2a14",
        "h1": "Yearn V3 — 8 Strategies Queued Across 6 Vaults with Max-Debt Caps",
        "lede": ("Pre-execution decode of one 16-call TimelockController batch: each of 8 inactive strategies is added outside the "
                 "default queue and given a max-debt cap, from 10,000 WETH to 10,000,000,000 USDC."),
        "badges": [("badge-cyan", "Pre-execution brief"), ("badge-amber", "yvFlexUSDC cap: in effect uncapped")],
        "state_title": "Vaults and strategies",
    },
    "etherfi-liquid-op-0xf0fb": {
        "title": "Pacta Governance Radar · Pre-Execution Brief — ether.fi Liquid Op 0xf0fb",
        "h1": "ether.fi Liquid — Strategist Merkle Roots Rotated on <code>liquidUSD</code>, <code>liquidETH</code> and <code>liquidBTC</code>",
        "lede": ("Pre-execution decode of one 5-call timelock batch on the Veda ManagerWithMerkleVerification contracts of three ether.fi "
                 "Liquid vaults: four live strategist roots are replaced and one is cleared. The roots' leaves are not onchain."),
        "badges": [("badge-cyan", "Pre-execution brief"), ("badge-amber", "Root leaves not onchain"),
                   ("badge-amber", "EOA strategist on liquidETH")],
        "state_title": "Managers, vaults and strategists at the pin",
    },
    "lombard-op-0xd07f": {
        "title": "Pacta Governance Radar · Pre-Execution Brief — Lombard AssetRouter Op 0xd07f",
        "h1": "Lombard <code>AssetRouter</code> — 2,000-Sat Deposit Fees on <code>LBTC</code> and <code>BTC.b</code>, Minimum Request Doubled",
        "lede": ("Pre-execution decode of one 5-call LombardTimeLock batch on the upgraded AssetRouter: the router-wide minimum doubles to "
                 "4,000 sats, every LBTC and BTC.b proof mint pays a fixed 2,000-sat deposit fee, and LBTC's redeem charge moves from "
                 "non-Bitcoin redeems to redeems to Bitcoin."),
        "badges": [("badge-cyan", "Pre-execution brief"), ("badge-amber", "New fee on every proof mint"),
                   ("badge-amber", "Fee above the operator range")],
        "state_title": "AssetRouter parameters: current vs queued",
    },
}


def load():
    with open(SRC, encoding="utf-8") as fh:
        d = json.load(fh)
    assert d["schema"] == SCHEMA, d["schema"]
    c = d["counts"]
    assert len(d["briefs"]) == c["briefs"] and sum(len(b["operations"]) for b in d["briefs"]) == c["operations"]
    assert sum(len(o["calls"]) for b in d["briefs"] for o in b["operations"]) == c["calls"]
    assert set(EDITORIAL) == {b["slug"] for b in d["briefs"]}
    return {b["slug"]: b for b in d["briefs"]}


def check_against_radar(b, item, brief_protocol):
    """The decoded brief and its radar.json item describe the same timelock operations on the same chain."""
    assert item is not None, b["slug"]
    assert item["brief"] == b["brief"] and item["protocol_slug"] == b["protocol_slug"] == brief_protocol, b["slug"]
    assert item.get("chain_id", 1) == b["chain_id"] and item["timelock"].lower() == b["timelock"]["address"].lower(), b["slug"]
    assert [o["op_id"] for o in item["operations"]] == [o["op_id"] for o in b["operations"]], b["slug"]
    assert item["min_delay_seconds"] == b["timelock"]["getMinDelay"], b["slug"]
    # a later radar refresh may find an operation executed (isOperationDone: eta cleared); otherwise the ETA is the decoded one
    assert all(o["eta"] == x["status"]["getTimestamp"] or (o["done"] and o["eta"] is None)
               for o, x in zip(item["operations"], b["operations"])), b["slug"]


def millions(wei):
    """Exact USDe (18 decimals) amounts in millions: 200000000 * 10**18 -> 200M (never rounded)."""
    assert wei % (WAD * 10 ** 6) == 0, wei
    return f"{wei // (WAD * 10 ** 6):,}M"


def mstr(s):
    """'25,000,000' -> '25M' (exact millions only)."""
    assert s.endswith(",000,000"), s
    return s[:-8] + "M"


NUM_WORD = {1: "One", 2: "Two", 3: "Three", 4: "Four"}


def adj(s):
    """86400 -> '1-day (86,400 s)'; 21600 -> '6-hour (21,600 s)'."""
    n, u = (s // 86400, "day") if s % 86400 == 0 else (s // 3600, "hour")
    assert n * (86400 if u == "day" else 3600) == s, s
    return f"{n}-{u} ({s:,} s)"


def dur(s):
    if s % 86400 == 0:
        n, u = s // 86400, "day"
    else:
        assert s % 3600 == 0, s
        n, u = s // 3600, "hour"
    return f"{n} {u}{'' if n == 1 else 's'} ({s:,} s)"


def round2(s):
    """'5,010.57415989616055714' -> '5,010.57' (display only; the exact value is in the title attribute)."""
    whole, _, frac = s.partition(".")
    return whole + ("." + (frac + "00")[:2] if frac else "")


def op_state(o):
    st = o["status"]
    if st["isOperationDone"]:
        return "executed"
    if st["isOperationReady"]:
        return "ready: delay elapsed, still unexecuted"
    return "pending" if st["isOperationPending"] else "not queued"


def render(b, item, bs):
    """(title, content HTML) for brief b; bs = the build_site module (E, short, hexref, term, EXPLORERS, CHAINS, U, EXT)."""
    E, short, EXT = bs.E, bs.short, bs.EXT
    ed = EDITORIAL[b["slug"]]
    ch = CHAIN_BY_ID[b["chain_id"]]
    chain_name = bs.CHAINS[ch][0]
    xname, xbase = bs.EXPLORERS[ch]
    pin = b["pinned_block"]
    tl = item["timelock"]                      # EIP-55 form from radar.json
    tl_l = tl.lower()
    tl_name = b["timelock"]["verified"]["sourcify"]["name"]
    names = {tl_l: f"{tl_name} (this timelock)"}
    names.update(target_names(b))

    def xa(a, label=None):
        """Address on the brief's own chain explorer (Etherscan or Basescan), EIP-55 checksummed."""
        a = eip55(a)
        text = E(label) if label else f'<span class="addr">{E(short(a))}</span>'
        return f'<a href="{xbase}/address/{E(a)}" target="_blank" rel="noopener" title="{E(a)}">{text}{EXT}</a>'

    def xtx(h):
        return f'<a href="{xbase}/tx/{E(h)}" target="_blank" rel="noopener" title="{E(h)}"><span class="addr">{E(short(h, 8, 6))}</span>{EXT}</a>'

    def xblock(n):
        return f'<a href="{xbase}/block/{n}" target="_blank" rel="noopener">#{n:,}{EXT}</a>'

    def arg(v):
        if isinstance(v, bool):
            return f"<code>{str(v).lower()}</code>"
        if isinstance(v, str) and ADDR_RE.fullmatch(v):
            return xa(v)
        if isinstance(v, list):
            return "[" + ", ".join(arg(x) for x in v) + "]"
        return f"<code>{E(str(v))}</code>"

    ops = b["operations"]
    label = lambda o: (o.get("label") or b["radar_title"].split(" — ", 1)[-1])
    cap = lambda s: s[:1].upper() + s[1:]
    etas = sorted({o["eta_utc"] for o in ops})
    eta = etas[0] if len(etas) == 1 else (f"{etas[0][:-4]}–{etas[-1][11:]}" if etas[0][:10] == etas[-1][:10] else f"{etas[0]} to {etas[-1]}")
    facts = {"delay": dur(b["timelock"]["getMinDelay"]), "eta": eta}

    # header + key figures
    out = ['<header>', '  <div>' + "".join(f'<span class="badge {c}">{E(t)}</span>' for c, t in ed["badges"]) + '</div>',
           f'  <h1>{ed["h1"]}</h1>', f'  <p>{E(ed["lede"])}</p>', '</header>', '', '<div class="meta-grid">']
    for k, v, s, ok in kpis(b, facts):
        out.append(f'  <div class="kpi"><div class="k">{E(k)}</div><div class="v">{E(v)}</div><div class="{"s-ok" if ok else "s"}">{E(s)}</div></div>')
    out.append('</div>')

    # 1. what is queued
    n_ops = len(ops)
    out += ['', '<h2>1. What Is Queued</h2>', '<div class="card">',
            f'  <p>{NUM_WORD[n_ops]} operation{"s are" if n_ops > 1 else " is"} queued on {xa(tl, tl_name)}, the {E(chain_name)} timelock '
            f'with a {E(adj(b["timelock"]["getMinDelay"]))} minimum delay. Every value on this page was read at {E(chain_name)} finalized block '
            f'{xblock(pin["block_number"])} ({E(pin["block_time_utc"])}, block hash '
            f'<span class="addr" title="{E(pin["block_hash"])}">{E(short(pin["block_hash"], 10, 6))}</span>) on '
            f'{pin["rpcs_cross_checked"]} independent public RPC endpoints that agreed.</p>', '  <ul>']
    for o in ops:
        n = len(o["calls"])
        out.append(f'    <li><strong>{E(cap(label(o)))}</strong>: operation {bs.hexref(o["op_id"], 8, 4)} · {n} call{"s" if n > 1 else ""} · '
                   f'ETA {E(o["eta_utc"])} · {E(op_state(o))} at the pin.</li>')
    out.append('  </ul>')
    by_tx = {}
    for o in ops:
        by_tx.setdefault(o["scheduled"]["tx"], []).append(o)

    def sched(tx, s):
        fn = s["function"] if not s["function"].startswith("0x") else f"selector {s['function']}"
        return f'transaction {xtx(tx)} at block {xblock(s["block"])} ({E(fn)}, sent by {xa(s["from"])} to {xa(s["to"])})'
    if len(by_tx) == 1:
        tx, os_ = next(iter(by_tx.items()))
        out.append(f'  <p>{f"All {n_ops} operations were" if n_ops > 1 else "The operation was"} scheduled in {sched(tx, os_[0]["scheduled"])}.</p>')
    else:
        out.append('  <p>Scheduled in:</p>\n  <ul>')
        for tx, os_ in by_tx.items():
            ids = ", ".join(f'<span class="addr" title="{E(o["op_id"])}">{E(short(o["op_id"], 6, 4))}</span>' for o in os_)
            out.append(f'    <li>{ids}: {sched(tx, os_[0]["scheduled"])}</li>')
        out.append('  </ul>')
    out.append('</div>')

    # 2. decoded calls
    out += ['', '<h2>2. Decoded Calls</h2>']
    for o in ops:
        pred = "none" if int(o["predecessor"], 16) == 0 else o["predecessor"]
        out += [f'<h3>{E(cap(label(o)))} · <span class="addr" title="{E(o["op_id"])}">{E(short(o["op_id"], 6, 4))}</span></h3>',
                '<div class="card">',
                f'  <p class="s">{len(o["calls"])} call{"s" if len(o["calls"]) > 1 else ""} · predecessor {E(pred)} · delay {o["delay"]:,} s · '
                f'ETA {E(o["eta_utc"])}</p>', '  <ol class="calls">']
        for c in o["calls"]:
            assert c["value"] == 0, (b["slug"], c)
            fname = c["function"].split("(", 1)[0]
            args = ", ".join(f'{E(k)} = {arg(v)}' for k, v in c["args"].items())
            out.append(f'    <li><code>{E(fname)}</code>({args}) on {xa(c["target"], names.get(c["target"].lower()))}'
                       f'{call_effect(b, o, c, E)}</li>')
        out += ['  </ol>', '</div>']

    # 3. protocol state
    out += ['', f'<h2>3. {E(ed["state_title"])}</h2>']
    out += STATE[b["slug"]](b, item, bs, xa, E)

    # 4. risk notes
    out += ['', '<h2>4. Risk Notes</h2>', '<div class="card">', '  <ul>']
    out += [f'    <li>{E(n)}</li>' for n in b["risk_notes"]]
    out += ['  </ul>', '</div>']

    # 5. reproduce
    rpc = bs.CHAINS[ch][2]
    decodes = [c["cast_decode"] for o in ops for c in o["calls"]]
    out += ['', '<h2>5. Reproduce</h2>', '<div class="card">',
            f'  <p>Every value above can be re-read at block #{pin["block_number"]:,} with Foundry <code>cast</code> against any {E(chain_name)} '
            f'archive node (<code>{E(rpc)}</code>).</p>',
            bs.U.accordion_item(f'<span>{len(b["reproduce"])} <code>cast</code> commands at {E(chain_name)} block #{pin["block_number"]:,}</span>',
                                bs.term("\n".join(b["reproduce"]), title=f"Reproduce on any {chain_name} archive node",
                                        what=f"Copy the {len(b['reproduce'])} cast commands")),
            bs.U.accordion_item(f'<span>Decode the {len(decodes)} queued call{"s" if len(decodes) > 1 else ""} offline (<code>cast calldata-decode</code>)</span>',
                                bs.term("\n".join(decodes), title="Offline calldata decode", what=f"Copy the {len(decodes)} calldata-decode commands")),
            '</div>']
    return ed["title"], "\n".join(out) + "\n"


def target_names(b):
    d, n = b["decoded"], {}
    if "upgrades" in d:
        for u in d["upgrades"]:
            n[u["proxyAdmin"]] = f'ProxyAdmin of {u["proxyName"]}'
            n[u["proxy"]] = u["proxyName"]
    if "strategy" in d:
        s = d["strategy"]
        n[s["strategy"]] = f'Beefy CLM strategy ({s["vaultSymbol"]})'
        n[s["vault"]] = s["vaultSymbol"]
    if "minting" in d:
        n[d["minting"]["address"]] = "EthenaMinting"
        n[d["oftAdapter"]["address"]] = "USDeOFTAdapter (LayerZero)"
        n.update({a: v["symbol"] for a, v in d["assets"].items()})
    if "router" in d:
        n[d["router"]["address"]] = d["router"]["name"]
        n.update({a: v["symbol"] for a, v in d["tokens"].items()})
    if "managers" in d:
        n.update({m: f'{v["vaultSymbol"]} manager' for m, v in d["managers"].items()})
        n.update({v["vault"]: v["vaultSymbol"] for v in d["managers"].values()})
    if "vaults" in d:
        n.update({a: v["symbol"] for a, v in d["vaults"].items()})
        n.update({s["strategy"]: s["strategyName"] for s in d["strategies"]})
    return {k.lower(): v for k, v in n.items()}


def call_effect(b, o, c, E):
    """One plain-language clause per decoded call, from the decoder's own annotations."""
    d = b["decoded"]
    if "change" in c and "from" in c["change"]:
        ch = c["change"]
        return f' — {E(c.get("asset", "Global"))}: {E(ch["from"])} to {E(ch["to"])} {E(ch["unit"])}'
    if "change" in c and "isSupportedAsset" in c["change"]:
        ch = c["change"]["isSupportedAsset"]
        return f' — {E(c["asset"])} delisted (isSupportedAsset {str(ch["from"]).lower()} to {str(ch["to"]).lower()})'
    if "rateLimits" in c:
        return "".join(f' — LayerZero eid {r["dstEid"]}: limit {E(r["limit"]["from"])} to {E(r["limit"]["to"])} USDe per '
                       f'{r["window"]["to"]:,} s (window unchanged; {E(round2(r["amountInFlightAtPin"]))} in flight at the pin)'
                       for r in c["rateLimits"])
    if "custodian" in c:
        k = c["custodian"]
        return (f' — {E(k["kind"])} ({k["codeBytes"]} bytes of code); isCustodianAddress = '
                f'{str(k["isCustodianAddress"]).lower()} at the pin')
    if "lombardChange" in c:
        x = c["lombardChange"]
        who = f'{x["tokenSymbol"]} ' if x.get("tokenSymbol") else ""
        return f' — {E(who)}{E(x["parameter"])}: {x["from"]:,} to {x["to"]:,} {E(x["unit"])}'
    if "root" in c:
        r = c["root"]
        to = "zero (cleared)" if int(r["to"], 16) == 0 else f'{r["to"][:6]}…{r["to"][-4:]}'
        return f' — {E(c["vaultSymbol"])}: {E(c["strategistKind"])} strategist root {E(r["from"][:6])}…{E(r["from"][-4:])} to {E(to)}'
    if "newMaxDebtUnits" in c:
        return f' — max debt {E(c["newMaxDebtUnits"])}'
    if c["function"].startswith("add_strategy"):
        s = next(s for s in d["strategies"] if s["strategy"] == c["args"]["new_strategy"])
        return f' — {E(s["vaultSymbol"])}: {E(s["strategyName"])}, not added to the default queue'
    if c["function"].startswith("setDeviation"):
        return f' — maxTickDeviation {d["strategy"]["maxTickDeviation"]} to {d["newMaxTickDeviation"]} ticks'
    if c["function"].startswith("upgradeAndCall"):
        u = next(u for u in d["upgrades"] if u["op_id"] == o["op_id"])
        assert u["initCalldataBytes"] == 0 and c["args"]["data"] == "0x"
        return f' — {E(u["proxyName"])} to the queued implementation; no initializer (empty data)'
    return ""


def kpis(b, F):
    """(label, value, sub-line, ok) for the four key-figure tiles; numbers from the JSON."""
    d, ops = b["decoded"], b["operations"]
    slug = b["slug"]
    if slug == "lombard-op-0xd07f":
        ch = {c["lombardChange"]["parameter"] + (c["lombardChange"]["tokenSymbol"] or ""): c["lombardChange"] for o in ops for c in o["calls"]}
        lo, hi = d["router"]["depositFeeOperatorRange"]
        mn = ch["minRequestAmount"]
        return [("Deposit fee per proof mint", f'{ch["depositFeeLBTC"]["to"]:,} sats', f'LBTC and BTC.b · {ch["depositFeeLBTC"]["from"]:,} today', False),
                ("Minimum request", f'{mn["from"]:,} to {mn["to"]:,} sats', "Router-wide · set first in the batch", False),
                ("Timelock delay", F["delay"], f"ETA {F['eta']}", False),
                ("Operator fee range", f"{lo:,}–{hi:,} sats", "The queued fee is above it: timelock only", True)]
    if slug.startswith("lombard"):
        ar = d["assetRouter"]
        return [("Operations", f"{len(ops)} proxy upgrades", "Independent · predecessor 0x0", False),
                ("Timelock delay", F["delay"], f"ETA {F['eta']}", False),
                ("Deposit fee at execution", "0 sats", "Operator range 100–1,000 sats", False),
                ("Minimum request", f"{ar['depositMinAmount(BTC.b)']:,} sats", "Unchanged · now minRequestAmount", True)]
    if slug.startswith("beefy"):
        s = d["strategy"]
        return [("maxTickDeviation", f"{s['maxTickDeviation']} to {d['newMaxTickDeviation']} ticks", f"Pool tick spacing {s['poolTickSpacing']}", False),
                ("Timelock delay", F["delay"], f"ETA {F['eta']}", False),
                ("isCalm() at the pin", str(s["isCalm"]).lower(), f"Tick {s['currentTick']:,} · TWAP {s['twapTick']:,}", True),
                ("Code change", "None", "setDeviation(int56) only", True)]
    if slug.startswith("ethena"):
        new = ops[0]["calls"][0]["args"]["_globalMaxMintPerBlock"]
        limits = [r for o in ops for c in o["calls"] for r in c.get("rateLimits", [])]
        cust = next(c for o in ops for c in o["calls"] if "custodian" in c)
        assert len({r["limit"]["to"] for r in limits}) == 1
        return [("Mint cap per block", f"{millions(d['minting']['globalMaxMintPerBlock'])} to {millions(new)} USDe",
                 f"Global + 8 assets · redeem {millions(d['minting']['globalMaxRedeemPerBlock'])} unchanged", True),
                ("Collateral", "USDm delisted", "removeSupportedAsset(USDm)", False),
                ("Bridge rate limits", f"{mstr(limits[0]['limit']['to'])} USDe / hour", " · ".join(f"eid {r['dstEid']} was {mstr(r['limit']['from'])}" for r in limits), False),
                ("New custodian", cust["custodian"]["kind"], "Not yet a custodian · check the owner", False)]
    if slug.startswith("etherfi-liquid"):
        calls = [c for o in ops for c in o["calls"]]
        cleared = [c for c in calls if int(c["root"]["to"], 16) == 0]
        kinds = sorted({s["kind"] for a, s in d["strategists"].items() if a not in d["managers"]})
        return [("Calls", f"{len(calls)} in one batch", f"setManageRoot on {len(d['managers'])} vaults", False),
                ("Timelock delay", F["delay"], f"ETA {F['eta']}", False),
                ("Roots replaced", f"{len(calls)} of {len(calls)} live", f"{len(cleared)} set to zero ({cleared[0]['vaultSymbol']})", False),
                ("Strategists", " + ".join(kinds), "plus the liquidUSD manager itself", False)]
    v = d["vaults"]
    top = max(d["strategies"], key=lambda s: s["newMaxDebt"] / 10 ** v[s["vault"]]["decimals"])
    return [("Calls", f"{len(ops[0]['calls'])} in one batch", f"{len(d['strategies'])} add_strategy + {len(d['strategies'])} max-debt caps", False),
            ("Timelock delay", F["delay"], f"ETA {F['eta']}", False),
            ("Largest cap", top["newMaxDebtUnits"], f"{v[top['vault']]['symbol']} holds {round2(v[top['vault']]['totalAssets']).split('.')[0]} {v[top['vault']]['assetSymbol']}", False),
            ("Default queue", "Not added", "add_to_queue = false", True)]


def state_lombard(b, item, bs, xa, E):
    d, out = b["decoded"], []
    tl = item["timelock"].lower()
    for u in d["upgrades"]:
        assert u["proxyAdminOwner"].lower() == tl and u["initCalldataBytes"] == 0
        cur, new, sd = u["currentImplementation"], u["newImplementation"], u["sourceDiff"]
        files = " · ".join(f'{os.path.basename(f["file"])} +{f["linesAdded"]} / -{f["linesRemoved"]}' for f in sd["projectFilesChanged"])
        lib = f'{sd["libraryFilesChanged"]} OpenZeppelin library files changed, {len(sd["filesAdded"])} added'
        abi = lambda xs: ", ".join(f'<code>{E(x.split(" ", 1)[1].split("(", 1)[0])}</code>' for x in xs) or "none"
        out += [f'<h3>{E(u["proxyName"])}</h3>', '<dl class="memo-meta">',
                f'<dt>Proxy</dt><dd>{xa(u["proxy"])}</dd>',
                f'<dt>ProxyAdmin</dt><dd>{xa(u["proxyAdmin"])} · OpenZeppelin {E(u["proxyAdminVersion"])} · owned by this timelock</dd>',
                f'<dt>Implementation now</dt><dd>{xa(cur["address"])} · {E(cur["sourcify"]["name"])} · Sourcify {E(cur["sourcify"]["match"])}</dd>',
                f'<dt>Queued implementation</dt><dd>{xa(new["address"])} · {E(new["sourcify"]["name"])} · Sourcify {E(new["sourcify"]["match"])} '
                f'(verified {E(new["sourcify"]["verifiedAt"][:10])})</dd>',
                '<dt>Initializer</dt><dd>None: upgradeAndCall with empty data</dd>',
                f'<dt>Source diff</dt><dd>{E(files)}; {E(lib)}</dd>',
                f'<dt>ABI added</dt><dd>{abi(sd["abiAdded"])}</dd>',
                f'<dt>ABI removed</dt><dd>{abi(sd["abiRemoved"])}</dd>', '</dl>']
    ar = d["assetRouter"]
    assert ar["depositFee(BTC.b) before the upgrade"] == "reverts"
    out.append(f'<p>At the pin, AssetRouter <code>depositMinAmount(BTC.b)</code> = {ar["depositMinAmount(BTC.b)"]:,} sats and '
               f'<code>depositFee(BTC.b)</code> reverts: the function only exists after the AssetRouter upgrade, which is why the BTC.b '
               f'upgrade must not execute first (see Risk Notes).</p>')
    return out


def state_beefy(b, item, bs, xa, E):
    s, new = b["decoded"]["strategy"], b["decoded"]["newMaxTickDeviation"]
    tl = item["timelock"].lower()
    assert s["owner"].lower() == tl and s["beaconOwnerOwner"]["address"].lower() == tl and s["beaconImplementation"]["sourcify"] is None
    disp = ", ".join(f"<code>{E(k)}</code>" for k, ok in s["implementationDispatches"].items() if ok)
    return ['<dl class="memo-meta">',
            f'<dt>Strategy</dt><dd>{xa(s["strategy"])} · beacon proxy · owned by this timelock</dd>',
            f'<dt>Vault</dt><dd>{xa(s["vault"])} · {E(s["vaultName"])} (<code>{E(s["vaultSymbol"])}</code>) · owner {xa(s["vaultOwner"])}</dd>',
            f'<dt>Pool</dt><dd>{xa(s["pool"])} · {E(s["token0Symbol"])} / {E(s["token1Symbol"])} on Aerodrome · tick spacing {s["poolTickSpacing"]}</dd>',
            f'<dt>maxTickDeviation</dt><dd>{s["maxTickDeviation"]} ticks now; {new} ticks once the operation executes</dd>',
            f'<dt>TWAP interval</dt><dd>{s["twapInterval"]} s · position width {s["positionWidth"]}</dd>',
            f'<dt>isCalm()</dt><dd>{str(s["isCalm"]).lower()} at the pin: tick {s["currentTick"]:,}, TWAP tick {s["twapTick"]:,} '
            f'({abs(s["currentTick"] - s["twapTick"])} tick{"" if abs(s["currentTick"] - s["twapTick"]) == 1 else "s"} apart)</dd>',
            f'<dt>Paused</dt><dd>{str(s["paused"]).lower()}</dd>',
            f'<dt>Beacon</dt><dd>{xa(s["eip1967Beacon"])} · {E(s["beaconVerified"]["sourcify"]["name"])} · Sourcify {E(s["beaconVerified"]["sourcify"]["match"])}</dd>',
            f'<dt>Beacon implementation</dt><dd>{xa(s["beaconImplementation"]["address"])} · not verified on Sourcify; {disp} are in its dispatch table</dd>',
            f'<dt>Beacon owner</dt><dd>{xa(s["beaconOwner"])} · {E(s["beaconOwnerVerified"]["sourcify"]["name"])} '
            f'(Sourcify {E(s["beaconOwnerVerified"]["sourcify"]["match"])}), owned by this timelock: implementation swaps also wait '
            f'{item["min_delay_seconds"]:,} s</dd>', '</dl>']


def state_ethena(b, item, bs, xa, E):
    d, ops = b["decoded"], b["operations"]
    tl = item["timelock"].lower()
    m = d["minting"]
    assert m["owner"].lower() == tl and d["oftAdapter"]["owner"].lower() == tl
    new = {c["args"]["asset"].lower(): c["args"]["_maxMintPerBlock"] for c in ops[0]["calls"] if "asset" in c["args"]}
    delisted = {c["args"]["asset"].lower() for o in ops for c in o["calls"] if c["function"].startswith("removeSupportedAsset")}
    rows = [f'<tr><td>Global</td><td>{millions(m["globalMaxMintPerBlock"])}</td><td>{millions(ops[0]["calls"][0]["args"]["_globalMaxMintPerBlock"])}</td>'
            f'<td>{millions(m["globalMaxRedeemPerBlock"])}</td></tr>']
    for a, v in d["assets"].items():
        assert v["isSupportedAsset"] and v["isActive"]
        q = millions(new[a]) + ("; then delisted" if a in delisted else "")
        rows.append(f'<tr><td>{xa(a, v["symbol"])}</td><td>{millions(v["maxMintPerBlock"])}</td><td>{E(q)}</td><td>{millions(v["maxRedeemPerBlock"])}</td></tr>')
    limits = [r for o in ops for c in o["calls"] for r in c.get("rateLimits", [])]
    lrows = [f'<tr><td>{r["dstEid"]}</td><td>{E(r["limit"]["from"])}</td><td>{E(r["limit"]["to"])}</td>'
             f'<td title="{E(r["amountInFlightAtPin"])}">{E(round2(r["amountInFlightAtPin"]).split(".")[0])}</td></tr>' for r in limits]
    cust = next(c for o in ops for c in o["calls"] if "custodian" in c)
    return ['<div class="card">',
            f'  <p>{xa(m["address"], "EthenaMinting")} (Sourcify {E(m["verified"]["sourcify"]["match"])}) and the '
            f'{xa(d["oftAdapter"]["address"], "USDe OFT adapter")} (Sourcify {E(d["oftAdapter"]["verified"]["sourcify"]["match"])}) are both owned by '
            f'this timelock. USDe amounts per block:</p>',
            '  <table><thead><tr><th>Asset</th><th>Mint cap now</th><th>Queued</th><th>Redeem cap</th></tr></thead>',
            '  <tbody>' + "".join(rows) + '</tbody></table>',
            '  <p>USDe OFT adapter (LayerZero) rate limits, USDe per hour:</p>',
            '  <table><thead><tr><th>Route (eid)</th><th>Limit now</th><th>Queued</th><th>In flight at the pin</th></tr></thead>',
            '  <tbody>' + "".join(lrows) + '</tbody></table>',
            f'  <p>Queued custodian {xa(cust["args"]["custodian"])}: an {E(cust["custodian"]["kind"])} with {cust["custodian"]["codeBytes"]} bytes of code, '
            f'isCustodianAddress = {str(cust["custodian"]["isCustodianAddress"]).lower()} at the pin. Minted collateral is routed to custodian '
            f'addresses, so check who controls it before the ETA.</p>', '</div>']


def state_yearn(b, item, bs, xa, E):
    d = b["decoded"]
    v = d["vaults"]
    roles = {tuple(x["timelockHolds"]) for x in v.values()}
    assert len(roles) == 1 and {x["timelockRoles"] for x in v.values()} == {143}
    assert all(s["currentParams"]["activation"] == 0 and s["strategyAsset"] == v[s["vault"]]["asset"] and not s["addToQueue"] for s in d["strategies"])
    srows = [f'<tr><td><b>{E(s["vaultSymbol"])}</b><br>{E(s["strategyName"])} {xa(s["strategy"])}</td><td>{E(s["newMaxDebtUnits"])}</td>'
             f'<td title="{E(s["strategyTotalAssets"])}">{E(round2(s["strategyTotalAssets"]))}</td></tr>' for s in d["strategies"]]
    vrows = [f'<tr><td>{xa(a, x["symbol"])}</td><td>{E(x["assetSymbol"])} · v{E(x["apiVersion"])}</td>'
             f'<td title="{E(x["totalAssets"])}">{E(round2(x["totalAssets"]))}</td></tr>' for a, x in v.items()]
    return ['<div class="card">',
            f'  <p>None of the {len(d["strategies"])} strategies is active today (activation = 0), each uses its vault\'s asset, and none joins '
            f'the default withdrawal queue.</p>',
            '  <table><thead><tr><th>Vault · strategy</th><th>New max debt</th><th>In strategy now</th></tr></thead>',
            '  <tbody>' + "".join(srows) + '</tbody></table>',
            '  <table><thead><tr><th>Vault</th><th>Asset · API</th><th>Total assets</th></tr></thead>',
            '  <tbody>' + "".join(vrows) + '</tbody></table>',
            f'  <p>On every vault this timelock holds {", ".join(f"<code>{E(r)}</code>" for r in sorted(next(iter(roles))))} '
            f'(roles bitmask 143), so execution needs no other role. Funds move only when a DEBT_MANAGER, which this timelock is not, '
            f'calls update_debt up to the new max debt.</p>', '</div>']


def state_etherfi_liquid(b, item, bs, xa, E):
    d, ops = b["decoded"], b["operations"]
    tl = item["timelock"].lower()
    p = d["proposer"]
    assert p["proposerIsSafe"] and p["executorIsSafe"] and not p["executorOpen"]
    mrows = []
    for m, v in d["managers"].items():
        assert int(v["owner"], 16) == 0 and v["timelockCanSetRoot"] and not v["isPaused"]
        mrows.append(f'<tr><td>{xa(v["vault"], v["vaultSymbol"])}<br>{E(v["vaultName"])}</td><td title="{E(v["totalSupply"])}">{E(round2(v["totalSupply"]))}</td>'
                     f'<td>{xa(m)} · Sourcify {E(v["verified"]["sourcify"]["match"])}</td><td>{xa(v["authority"])}</td></tr>')
    root = lambda h: f'<span class="addr" title="{E(h)}">{"zero" if int(h, 16) == 0 else E(h[:10] + "…" + h[-4:])}</span>'
    crows = [f'<tr><td>{E(c["vaultSymbol"])}</td><td>{xa(c["args"]["strategist"])}<br>{E(c["strategistKind"])}</td>'
             f'<td>{root(c["root"]["from"])}</td><td>{root(c["root"]["to"])}</td></tr>' for o in ops for c in o["calls"]]
    return ['<div class="card">',
            f'  <p>Each vault is run by a Veda ManagerWithMerkleVerification contract whose owner() is the zero address; its authority lets '
            f'{xa(tl, "this timelock")} call setManageRoot. None of the three managers is paused at the pin. Vault shares outstanding:</p>',
            '  <table><thead><tr><th>Vault</th><th>Shares (totalSupply)</th><th>Manager</th><th>Authority</th></tr></thead>',
            '  <tbody>' + "".join(mrows) + '</tbody></table>',
            '  <p>Strategist roots, live at the pin and queued:</p>',
            '  <table><thead><tr><th>Vault</th><th>Strategist</th><th>Root now</th><th>Queued root</th></tr></thead>',
            '  <tbody>' + "".join(crows) + '</tbody></table>',
            f'  <p>The batch was scheduled by the {p["threshold"]}-of-{p["owners"]} Safe {xa(p["address"])} (Safe {E(p["version"])}), which is this '
            f'timelock\'s proposer, canceller and executor; the executor role is not open to everyone.</p>', '</div>']


def state_lombard_fees(b, item, bs, xa, E):
    d, ops = b["decoded"], b["operations"]
    tl = item["timelock"].lower()
    r, p = d["router"], d["proposer"]
    assert r["defaultAdmin"].lower() == tl and r["owner"].lower() == tl and r["timelockIsDefaultAdmin"] and not r["timelockIsOperator"]
    assert p["proposerIsTxTo"] and p["executorIsTxTo"] and not p["executorOpen"]
    rows = []
    for o in ops:
        for c in o["calls"]:
            x = c["lombardChange"]
            tok = xa(x["token"], x["tokenSymbol"]) if x.get("token") else "Router-wide"
            rows.append(f'<tr><td><code>{E(x["parameter"])}</code></td><td>{tok}</td><td>{x["from"]:,} sats</td><td>{x["to"]:,} sats</td>'
                        f'<td>{E(x["meaning"])}</td></tr>')
    impl = r["implementation"]
    lo, hi = r["depositFeeOperatorRange"]
    return ['<div class="card">',
            f'  <p>{xa(r["address"], "AssetRouter")} runs implementation {xa(impl["address"])} ({E(impl["sourcify"]["name"])}, Sourcify '
            f'{E(impl["sourcify"]["match"])}). Its owner() and defaultAdmin() are {xa(tl, "this timelock")} (defaultAdminDelay '
            f'{r["defaultAdminDelay"]} s); an OPERATOR_ROLE holder may only set deposit fees from {lo:,} to {hi:,} sats. Amounts are in '
            f'satoshis (8 decimals).</p>',
            '  <table><thead><tr><th>Parameter</th><th>Token</th><th>Now</th><th>Queued</th><th>What it charges or limits</th></tr></thead>',
            '  <tbody>' + "".join(rows) + '</tbody></table>',
            f'  <p>The batch was scheduled by the {p["threshold"]}-of-{p["owners"]} Safe {xa(p["address"])} (Safe {E(p["version"])}), which is '
            f'this timelock\'s proposer, canceller and executor; the executor role is not open to everyone.</p>', '</div>']


STATE = {"lombard-ops-0xceee-0x2f2a-0x6404": state_lombard, "beefy-base-op-0x3302": state_beefy,
         "ethena-ops-0xb028-0xca05-0x108e-0x070a": state_ethena, "yearn-v3-op-0x2a14": state_yearn,
         "etherfi-liquid-op-0xf0fb": state_etherfi_liquid, "lombard-op-0xd07f": state_lombard_fees}
