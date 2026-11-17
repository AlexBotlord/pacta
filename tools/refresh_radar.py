"""Refresh docs/api/v1/radar.json: live state of the queued timelock operations shown on the homepage radar.

Read-only JSON-RPC (stdlib only). Each chain is pinned to its current *finalized* block and every read is cross-checked on two
independent RPC endpoints; any disagreement aborts. Ethereum Mainnet items (chain_id 1) are read at `refreshed_at`, Base items
(chain_id 8453) at `refreshed_at_base`. The homepage "Last refreshed" line, the countdown ETAs and the explorer links (Etherscan
or Basescan) are built from this file, so they always state the exact block each item was observed at.

  python3 tools/refresh_radar.py                 # rewrite docs/api/v1/radar.json
  python3 tools/refresh_radar.py --out <path>    # write elsewhere (dry run)

Item order: ready first, then pending by ETA, then anything else, executed last.
"""

import argparse
import json
import os
import time
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "api", "v1", "radar.json")
# chain_id -> (key in radar.json, expected eth_chainId, two independent public RPC endpoints)
CHAINS = {1: ("refreshed_at", "0x1", ["https://rpc.mevblocker.io", "https://gateway.tenderly.co/public/mainnet"]),
          8453: ("refreshed_at_base", "0x2105", ["https://gateway.tenderly.co/public/base", "https://base-rpc.publicnode.com"])}
SEL = {"getTimestamp": "0xd45c4435", "isOperationPending": "0x584b153e", "isOperationDone": "0x2ab0f529", "getMinDelay": "0xf27a0c92"}
# ops: (op_id, label or None). Timelock addresses are EIP-55 (a wrong-checksum mixed-case address is skipped by the live re-check).
OPS = [
    {"protocol": "Treehouse", "protocol_slug": "treehouse-tree-teth", "chain_id": 1,
     "title": "Treehouse TREE — UUPS upgrade adding Blacklistable",
     "summary": "Upgrades the TREE governance token (not tETH) and installs a 5-of-7 Safe as blacklister: a zero-delay transfer-freeze role after execution.",
     "timelock": "0x2225DAbFfC7F862c99477381E971E8B1FDaB467e", "brief": "briefs/treehouse-op-0x2f11/",
     "ops": [("0x2f11dcc36860f09b9ef94585589ced1798cef603d133efecd017ce7e544c451f", None)]},
    {"protocol": "Lombard", "protocol_slug": "lombard-lbtc", "chain_id": 1,
     "title": "Lombard — AssetRouter, BTC.b and LBTC upgrades adding a fixed deposit fee",
     "summary": "Three ProxyAdmin.upgradeAndCall ops (no init call) upgrade AssetRouter, BTC.b (NativeLBTC) and LBTC (StakedLBTC): a per-token "
                "deposit fee is split off every proof mint to treasury (OPERATOR_ROLE may set 100-1,000 sats, the timelock anything up to half "
                "the minimum), a router-wide minRequestAmount replaces depositMinAmount, and unpauseTransfers moves from DEFAULT_ADMIN_ROLE to MANAGER_ROLE.",
     "timelock": "0x055E84e7FE8955E2781010B866f10Ef6E1E77e59", "brief": "briefs/lombard-ops-0xceee-0x2f2a-0x6404/",
     "ops": [("0xceeeff86865f11b6de2c57d4901d3ec3313edf08be6ea664989d386cb1ab18eb", "AssetRouter upgrade adding a fixed deposit fee"),
             ("0x2f2a342465e4d964eb240db7c573dff2f57e35b9bd3ea3798987aa327c02dd81", "BTC.b token upgrade that charges the deposit fee on mint"),
             ("0x6404e599d016a5a5d60957a22db6919eb7409f28d7d3880cf78ac1313f167fff", "LBTC token upgrade; unpausing transfers moves to the manager role")]},
    {"protocol": "Beefy Finance (Base)", "protocol_slug": "beefy-finance-base", "chain_id": 8453,
     "title": "Beefy CLM USDC-VVV on Aerodrome — calm-check tolerance widened from 9 to 25 ticks",
     "summary": "setDeviation(25) on the cowAeroBaseUSDC-VVV strategy (owned by the timelock): maxTickDeviation 9 -> 25 ticks, the tolerance "
                "between the pool tick and its 120 s TWAP before the strategy acts, on a tick-spacing-50 Aerodrome pool. No code change.",
     "timelock": "0x3B60F7f25b09E71356cdFFC6475c222A466a2AC9", "brief": "briefs/beefy-base-op-0x3302/",
     "ops": [("0x3302750e18a4bff9508c6e93386a406df9aa8d36992188e76a08ecc76bfce208", None)]},
    {"protocol": "Ethena", "protocol_slug": "ethena-usde-susde", "chain_id": 1,
     "title": "Ethena USDe — mint caps cut to 50M per block, USDm delisted, a custodian added",
     "summary": "Four ops: global and per-asset maxMintPerBlock 200M -> 50M USDe on 8 assets; removeSupportedAsset(USDm); addCustodianAddress "
                "for an EOA not yet a custodian; USDe OFT adapter setRateLimits to 25M per hour on LayerZero eids 30339 (was 10M) and 30383 (was 30M).",
     "timelock": "0xE8Dc0Fab349EA169283C48Ccfd09d797E6DB7c94", "brief": "briefs/ethena-ops-0xb028-0xca05-0x108e-0x070a/",
     "ops": [("0xb0289f92009409e09b8b87150e10486ab753b7c13d049702caca3221a622d81a", "mint caps cut from 200M to 50M per block"),
             ("0xca0563b0bebee6c971db36df24ef8c5802ad4007f7fb42bff2f553141c8ed835", "USDm removed as mint collateral"),
             ("0x108ea49a961a00e8992ad4aed2e1faea43b0a47982e0c62d63f9db03ddb4d0f4", "bridge rate limits set to 25M per hour on two routes"),
             ("0x070a0ab4df4b4d69e23ed817c62481d267dae887ed7f7b5fbc7cffa5ff64228d", "a new custodian address added")]},
    {"protocol": "ether.fi", "protocol_slug": "ether-fi-core-eeth-weeth", "chain_id": 1,
     "title": "ether.fi — LayerZero V2 delegate moved behind the 10-day timelock",
     "summary": "EtherfiL1SyncPoolETH.setDelegate(EtherFiTimelock): protective hardening of the OApp's messaging configuration.",
     "timelock": "0x9f26d4C958fD811A1F59B01B86Be7dFFc9d20761", "brief": "briefs/etherfi-op-0x244e/",
     "ops": [("0x244e3f6c3df722246c471cee58804dd34c7703fce9cee1eadc1c5a85f171359f", None)]},
    {"protocol": "Yearn V3", "protocol_slug": "yearn-v3", "chain_id": 1,
     "title": "Yearn V3 — 8 new strategies added to 6 vaults with max-debt caps",
     "summary": "One 16-call batch: add_strategy(strategy, add_to_queue=false) then update_max_debt_for_strategy on yvUSDC-1, yvUSD, yvWETH-1, "
                "yvWETH-2, yvFlexUSDC and yvFlexWETH (Flex siUSD and wstETH lenders / loopers, USDC-to-yvUSDS-1 depositors). Caps range from "
                "10,000 WETH to 10B USDC (yvFlexUSDC, effectively uncapped).",
     "timelock": "0x88Ba032be87d5EF1fbE87336B7090767F367BF73", "brief": "briefs/yearn-v3-op-0x2a14/",
     "ops": [("0x2a14e386ce3da63615778466602757ea8dc25e8157aaee660213827a15efb5cf", None)]},
    {"protocol": "Ethena", "protocol_slug": "ethena-usde-susde", "chain_id": 1,
     "title": "Ethena USDe — RLUSD & USAT collateral onboarding",
     "summary": "Two queued EthenaMinting.addSupportedAsset calls onboard RLUSD and USAT at 200M / 20M USDe-per-block caps (stablesDeltaLimit = 0 bps).",
     "timelock": "0xE8Dc0Fab349EA169283C48Ccfd09d797E6DB7c94", "brief": "briefs/ethena-ops-0x0ca0-0x1fe5/",
     "ops": [("0x1fe5e3e892708310bbfcf50efc03a1b8e21e0d0042035d7e8315e0cd5f26d85b", None),
             ("0x0ca0fcc4856b87f3df9a74532bd60db58d1310c27c17e7d9bfa8a56846f57a90", None)]},
]
RANK = {"ready": 0, "pending": 1, "mixed": 2, "unknown": 3, "executed": 4}


def rpc(url, method, params):
    req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "pacta-site-radar/1.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = json.loads(r.read())
    if resp.get("id") != 1 or "error" in resp:
        raise RuntimeError(f"{method}: {resp.get('error')}")
    return resp["result"]


class Chain:
    """One chain pinned to a finalized block that both endpoints agree on (eth_chainId checked on both)."""

    def __init__(self, chain_id):
        self.key, want, self.rpcs = CHAINS[chain_id]
        for u in self.rpcs:
            if rpc(u, "eth_chainId", []) != want:
                raise RuntimeError(f"{u}: not chain {chain_id}")
        # consensus fields only (endpoints add their own extras, e.g. timestampMs); a lagging endpoint is met at the lower finalized block
        n = min(int(rpc(u, "eth_getBlockByNumber", ["finalized", False])["number"], 16) for u in self.rpcs)
        blocks = [rpc(u, "eth_getBlockByNumber", [hex(n), False]) for u in self.rpcs]
        fin = {k: blocks[0][k] for k in ("number", "hash", "timestamp")}
        if any({k: b[k] for k in fin} != fin for b in blocks):
            raise RuntimeError(f"RPC disagreement on finalized block {n}: {[{k: b[k] for k in fin} for b in blocks]}")
        self.pin = {"blockHash": fin["hash"], "requireCanonical": True}
        self.ts = int(fin["timestamp"], 16)
        self.meta = {"block_number": int(fin["number"], 16), "block_hash": fin["hash"], "block_timestamp": self.ts,
                     "block_time_utc": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(self.ts)), "tag": "finalized",
                     "rpcs_cross_checked": len(self.rpcs)}

    def both(self, method, params):
        a, b = (rpc(u, method, params) for u in self.rpcs)
        if a != b:
            raise RuntimeError(f"RPC disagreement on {method}: {a!r} vs {b!r}")
        return a

    def call(self, to, data):
        return int(self.both("eth_call", [{"to": to, "data": data}, self.pin]), 16)


def state(ops):
    s = {"executed" if o["done"] else "ready" if o["ready"] else "pending" if o["pending"] else "unknown" for o in ops}
    return s.pop() if len(s) == 1 else "mixed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    out_path = ap.parse_args().out
    chains = {cid: Chain(cid) for cid in sorted({o["chain_id"] for o in OPS} | {1})}
    items = []
    for o in OPS:
        ch = chains[o["chain_id"]]
        delay = ch.call(o["timelock"], SEL["getMinDelay"])
        ops = []
        for op, label in o["ops"]:
            ts = ch.call(o["timelock"], SEL["getTimestamp"] + op[2:])
            pending = ch.call(o["timelock"], SEL["isOperationPending"] + op[2:]) == 1
            done = ch.call(o["timelock"], SEL["isOperationDone"] + op[2:]) == 1
            # ready: the delay has elapsed at the finalized block and the op is still unexecuted (execute() is now callable).
            # Never "executed" unless isOperationDone is true.
            ops.append({"op_id": op, "eta": ts if ts > 1 else None, "pending": pending, "done": done,
                        "ready": bool(pending and not done and ts > 1 and ch.ts >= ts), **({"label": label} if label else {})})
        items.append({**{k: o[k] for k in ("protocol", "protocol_slug", "chain_id", "title", "summary", "timelock", "brief")},
                      "min_delay_seconds": delay, "operations": ops, "eta": min((x["eta"] for x in ops if x["eta"]), default=None)})
    items.sort(key=lambda it: (RANK[state(it["operations"])], it["eta"] or 0))   # stable: ready, pending by ETA, …, executed last
    out = {"schema": "pacta.radar.v1", "chain_id": 1, **{ch.key: ch.meta for ch in chains.values()}, "items": items}
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print({ch.key: ch.meta["block_number"] for ch in chains.values()},
          [(i["protocol"], i["chain_id"], i["eta"], state(i["operations"])) for i in items])


if __name__ == "__main__":
    main()
