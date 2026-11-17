"""Protocol scorecards (Website Edge v3): one canonical grade per protocol and a deterministic 5-factor control-plane rosette.

Every value is derived at build time from Pacta's published records only: index.json (Base-EAS-attested Sprint records) and
rpc-pinned.json (RPC-observed records), their onchain_observed evidence text and structured fields (observed_delay_seconds,
is_eip1967_proxy, safe_quorum), plus tools/graph_controller_facts.json. No value is entered by hand. A factor that the published
evidence does not decide is "Not determined" (a hollow slice), never a guess; slice 5 is "Uncompared" (hollow) for every
RPC-observed protocol, whose documentation Pacta has not assessed.

Grades (protocol level): DELTA (any parameter_delta record), PROTECTIVE (no parameter delta, at least one protective_delta),
ALIGNED (every record an aligned baseline), OBSERVED (RPC-pinned only). A protocol whose record carries "reconciledFrom" provenance
(a former delta reconciled at a later attested block) is ALIGNED with the "Reconciled" sub-pill and a before / after trail."""
import re

GRADES = {"delta": ("DELTA", "Docs and chain differ"), "protective": ("PROTECTIVE", "Chain stronger than documented"),
          "aligned": ("ALIGNED", "Docs and chain match"), "observed": ("OBSERVED", "Chain pinned; docs not assessed")}
FACTORS = [("upgrade", "Upgradeability"), ("timelock", "Timelock floor"), ("quorum", "Signer quorum"),
           ("emergency", "Emergency / freeze scope"), ("parity", "Docs-vs-chain parity")]
STATE_LABEL = {"g": "Strong", "b": "Moderate", "a": "Weak", "n": "Not determined", "u": "Uncompared"}
DAY = 86400

_NOF = re.compile(r"\b(\d{1,2})-of-(\d{1,2})\b")
_DELAY = re.compile(r"\b(?:getMinDelay\(\)|delay\(\)|MINIMUM_DELAY\(\)|MIN_DELAY\(\)|minDelay\(\)|executionDelay\(\)|TIMELOCK_PERIOD\(\)|"
                    r"timelockDelay\(\)|getMinimumDelay\(\))\s*(?:returns\s*|=\s*)([\d,]+)\s*s\b")
_SINGLE = re.compile(r"no contract code|externally owned|\bEOA\b")
_GOVERNOR = re.compile(r"\bGovernor(?:Bravo|Alpha|Omega)?\b|\bDAO governance\b")
_PROXY = re.compile(r"EIP-1967 (?:admin|implementation) (?:slot )?(?:=|resolves|is)|ProxyAdmin|AdminUpgradeabilityProxy|"
                    r"TransparentUpgradeableProxy|ERC-1967 prox|UUPS|zeppelinos\.proxy\.admin|upgradeTo")
_IMMUTABLE = re.compile(r"\bimmutable\b|ownership renounced|owner\(\) = 0x0\b|not a proxy|no proxies")   # zero EIP-1967 slots alone is not immutability
_EMERGENCY = re.compile(r"\bpause|\bblacklist|\bfreez|PAUSE_ROLE|ASSET_PROTECTION|\bdeprecate|\bguardian\b|pauseGuardian", re.I)


def grade(classifications, easattested, reconciled=False):
    if not easattested:
        return "observed"
    cl = set(classifications)
    if "parameter_delta" in cl:
        return "delta"
    if "protective_delta" in cl:
        return "protective"
    return "aligned"


def _snip(text, m, width=70):
    a, b = max(0, m.start() - width // 2), min(len(text), m.end() + width // 2)
    return ("…" if a else "") + text[a:b].strip() + ("…" if b < len(text) else "")


def factors(records, easattested, g, facts=()):
    """The five factor states (g / b / a / n / u) with the evidence that decided each. records: the protocol's published records
    (index.json or rpc-pinned.json entries); facts: graph_controller_facts entries of its contracts."""
    texts = [(r.get("id"), str(r.get("onchain_observed") or "")) for r in records]
    out = {}
    # 2: timelock floor (minimum enforced delay observed anywhere in the protocol's records / facts)
    delays = []
    for r in records:
        if isinstance(r.get("observed_delay_seconds"), int):
            delays.append((r["observed_delay_seconds"], f'{r.get("id")}: observed_delay_seconds = {r["observed_delay_seconds"]}'))
    for rid, t in texts:
        for m in _DELAY.finditer(t):
            delays.append((int(m.group(1).replace(",", "")), f"{rid}: {_snip(t, m)}"))
    for f in facts:
        if isinstance(f.get("timelock_min_delay"), int):
            delays.append((f["timelock_min_delay"], f'controller fact: getMinDelay() = {f["timelock_min_delay"]}s'))
    if delays:
        d, ev = min(delays)
        st = "g" if d >= 2 * DAY else "b" if d >= 3600 else "a"
        out["timelock"] = (st, f"{_dur(d)} minimum observed delay", ev)
    else:
        out["timelock"] = ("n", "No enforced delay in the published records", None)
    # 3: signer quorum (lowest threshold of any controlling Safe; a key without contract code counts as 1-of-1)
    quorum = []
    for rid, t in texts:
        for m in _NOF.finditer(t):
            k, nn = int(m.group(1)), int(m.group(2))
            if 1 <= k <= nn:
                quorum.append((k, f"{k}-of-{nn}", f"{rid}: {_snip(t, m)}"))
        for m in _SINGLE.finditer(t):
            quorum.append((1, "a single key", f"{rid}: {_snip(t, m)}"))
    for f in facts:
        if f.get("safe_threshold"):
            quorum.append((f["safe_threshold"], f'{f["safe_threshold"]}-of-{f.get("safe_owners")}', "controller fact: Safe getThreshold()"))
    if quorum:
        k, lbl, ev = min(quorum, key=lambda q: (q[0], q[1]))
        st = "g" if k >= 3 else "b" if k == 2 else "a"
        out["quorum"] = (st, f"Lowest controlling quorum: {lbl}", ev)
    else:
        gov = next(((rid, t, m) for rid, t in texts for m in [_GOVERNOR.search(t)] if m), None)
        out["quorum"] = (("g", "DAO Governor (token vote)", f"{gov[0]}: {_snip(gov[1], gov[2])}") if gov
                         else ("n", "No signer quorum in the published records", None))
    # 1: upgradeability (an upgradeable proxy is as strong as the delay / quorum gating it; immutable is strong)
    prox = next(((rid, t, m) for rid, t in texts for m in [_PROXY.search(t)] if m), None)
    if prox is None and any(r.get("is_eip1967_proxy") for r in records):
        prox = next((r.get("id"), "is_eip1967_proxy = true", None) for r in records if r.get("is_eip1967_proxy"))
    imm = next(((rid, t, m) for rid, t in texts for m in [_IMMUTABLE.search(t)] if m), None)
    if prox:
        ev = f"{prox[0]}: {_snip(prox[1], prox[2]) if prox[2] else prox[1]}"
        ts, qs = out["timelock"][0], out["quorum"][0]
        if ts == "g":
            out["upgrade"] = ("g", "Upgradeable behind a ≥48h delay", ev)
        elif ts == "b":
            out["upgrade"] = ("b", "Upgradeable behind a 1h–47h delay", ev)
        elif ts == "a" or qs == "a":
            out["upgrade"] = ("a", "Upgradeable with no enforced delay", ev)
        else:
            out["upgrade"] = ("n", "Upgradeable; the gating delay is not in the published records", ev)
    elif imm:
        out["upgrade"] = ("g", "Immutable or ownership renounced", f"{imm[0]}: {_snip(imm[1], imm[2])}")
    else:
        out["upgrade"] = ("n", "Upgrade path not in the published records", None)
    # 4: emergency / freeze scope (pause / blacklist / freeze authority and who holds it)
    em = next(((rid, t, m) for rid, t in texts for m in [_EMERGENCY.search(t)] if m), None)
    if em:
        ev = f"{em[0]}: {_snip(em[1], em[2])}"
        qs = out["quorum"][0]
        if qs == "a":
            out["emergency"] = ("a", "Pause / freeze authority with a single key or 1-of-N", ev)
        elif qs in ("g", "b"):
            out["emergency"] = ("g", "Pause / freeze authority scoped behind a multi-signer controller", ev)
        else:
            out["emergency"] = ("n", "Pause / freeze authority present; holder not determined", ev)
    else:
        out["emergency"] = ("n", "No pause / freeze authority in the published records", None)
    # 5: docs-vs-chain parity (the grade; never colored without a Base-EAS-attested documentation comparison)
    out["parity"] = (("u", "Uncompared: documentation not assessed (RPC-observed)", None) if not easattested else
                     ("a", "Documentation differs from the chain (parameter delta)", None) if g == "delta" else
                     ("g", "Chain matches or is stronger than the documentation", None))
    return [{"key": k, "label": lbl, "state": out[k][0], "value": out[k][1], "evidence": out[k][2]} for k, lbl in FACTORS]


def _dur(s):
    if s >= DAY and s % 3600 == 0:
        d, h = divmod(s // 3600, 24)
        return f"{d}d" + (f" {h}h" if h else "")
    if s >= 3600:
        return f"{s / 3600:g}h"
    return f"{s}s"


def aria(fs, name=None):
    return ((f"{name} control-plane rosette: " if name else "Control-plane rosette: ")
            + "; ".join(f'{f["label"]} {STATE_LABEL[f["state"]].lower()}' for f in fs))


def rosette_svg(fs, size=28, name=None):
    """28x28 inline SVG: five 72-degree slices clockwise from 12 o'clock (factor order); hollow dashed outline for n / u."""
    import math
    c, r = size / 2, size / 2 - 1.5
    parts = []
    for i, f in enumerate(fs):
        a0, a1 = math.radians(-90 + 72 * i + 1.5), math.radians(-90 + 72 * (i + 1) - 1.5)
        x0, y0, x1, y1 = c + r * math.cos(a0), c + r * math.sin(a0), c + r * math.cos(a1), c + r * math.sin(a1)
        d = f"M{c:.1f} {c:.1f}L{x0:.1f} {y0:.1f}A{r:.1f} {r:.1f} 0 0 1 {x1:.1f} {y1:.1f}Z"
        parts.append(f'<path class="r-{f["state"]}" d="{d}"/>')
    return (f'<svg class="rosette" width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img" '
            f'aria-label="{_esc(aria(fs, name))}">{"".join(parts)}</svg>')


def _esc(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
