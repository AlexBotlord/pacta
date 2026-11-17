"""M7: one human-written "What differs" line per published protocol (<= 90 characters, whole words, balanced brackets).

The scorecard table shows this line; the expanded row and /protocols/<slug>/ keep the full verbatim evidence. Each line restates
the protocol's own pinned record (tools/scorecard.py finding / tools/control_diff.py what_differs); it never adds a claim the
record does not make. `check()` is asserted by the build and by verify_site_v2.py.
"""
import re

MAX = 90

SUMMARY = {
    "aave-v3-base": "Pause and unpause admin is the Aave Guardian 4-of-7 Safe, as documented",
    "aave-v3-gho": "ACL admin role, executor delay and Guardian Safe match the docs",
    "across-protocol-hubpool": "Only allow-listed proposers can submit root bundles, as documented",
    "aerodrome-finance-base": "Voter emergency council and epoch governor are the AerodromeMigration contract",
    "aerodrome-slipstream-base": "Pool factory owner and fee managers are the 3-of-7 team Safe, as documented",
    "axelar-network": "Deployment config lists an older gateway implementation; 3-day timelock with operator path",
    "balancer-v2-vault-timelock": "Authorizer admin role is the 6-of-11 DAO multisig, as documented",
    "bedrock-unieth": "Docs list an older restaking implementation; uniETH upgrades via a 3-of-5 Safe ProxyAdmin",
    "beefy-finance-base": "Timelock delay: docs 6 hours · chain none",
    "cap": "Access-control admin is a Timelock, not the multisig the docs name",
    "centrifuge-liquidity-pools-base": "OpsGuardian has no pause authority over Root, as documented",
    "chainlink-ccip": "Docs: only the MCMS proposes · chain: a 6-of-12 Safe can also propose",
    "circle-usdc": "USDC roles on Base are single admin addresses, as Circle documents",
    "coinbase-wrapped-staked-eth": "The exchange rate is set by a rate-limited updater, as documented",
    "compound-v3-base": "Base markets follow the Ethereum Timelock plus a 1-day local timelock",
    "compound-v3-comet": "Governor, 48-hour Timelock and Pause Guardian Safe match the docs",
    "concrete": "Vault and factory manager Safe runs at 1-of-2 despite documented role separation",
    "convex-finance": "Booster governance ownership chain matches the docs",
    "curve-finance-crvusd": "crvUSD factory admin is a LendingOwnerProxy; docs name the OwnershipAgent",
    "eigenlayer-core": "Core ProxyAdmin, executor Safe and 10-day Timelock match the docs",
    "enzyme-finance": "Timelock delay: docs none · chain 7 days (stricter)",
    "ethena-usde-susde": "Timelock delay: docs 7 days · chain 1 day",
    "ethena-usdtb": "USDtb PSM is owned by a 24-hour timelock, not the Dev multisig directly",
    "ether-fi-core-eeth-weeth": "10-day upgrade timelock; a queued LayerZero delegate change moves behind it",
    "ether-fi-liquid-veda-boringvault": "RolesAuthority owner and timelock wiring match the docs",
    "euler-v2-evk": "Factory upgrades wait 4 days in a timelock (DAO 4-of-8 proposes), as documented",
    "extra-finance-base": "Non-proxy lending pool with role-based admin; docs not assessed",
    "f-x-protocol-v2": "Treasury admin sits with the Ops and Emergency Safes, not the 3-day Timelock",
    "falcon-finance-usdf-susdf": "sUSDf cooldown is zero, so unstaking to USDf is instant, as documented",
    "fluid-instadapp": "Migration auth is live on four vaults, beyond the documented multisig scope",
    "frax-ether-sfrxeth": "frxETHMinter owner is the documented Comptroller",
    "frax-usd-frxusd": "Upgrades go through a 1-day timelock run by the 4-of-7 Frax Safe",
    "gearbox-v3-v3-1": "Timelock delay: docs 2 days · chain 36 hours",
    "grove-finance": "Allocator custody role admin is the Grove SubProxy under Sky governance",
    "infinifi": "Pause roles are administered by MINOR_ROLES_MANAGER; docs say GOVERNOR",
    "inverse-finance-firm": "Policy Committee Safe: docs 5-of-9 · chain 4-of-7",
    "kelp-dao-rseth": "ProxyAdmin sits behind a 10-day timelock; config admin Safe as documented",
    "layerzero-v2": "Endpoint is immutable; a 5-of-9 multisig sets the message defaults, as documented",
    "lido-steth-dual-governance": "Dual Governance timelock delays and committee Safes match the docs",
    "liquid-collective-lseth": "Upgrade and admin firewalls are run by 4-of-7 Safes, as documented",
    "liquity-v1-lusd": "Liquidation thresholds are 110% and 150% in Recovery Mode, as documented",
    "liquity-v2-bold": "Sampled owner and proxy slots match the docs",
    "lombard-lbtc": "Core ProxyAdmin wiring and 24-hour timelock match the docs",
    "m0-protocol-m": "MToken has no proxy slots: immutable core logic, as documented",
    "mantle-liquid-staking-meth-cmeth": "Timelock delay: docs none · chain 3 days (stricter)",
    "maple-finance-v2-syrup": "Proxy admin is the 4-of-7 DAO Safe; docs describe a 3-day GovernorTimelock",
    "mellow-protocol-lido-earn": "Curator Safe: docs 3-of-6 · chain 3-of-5",
    "metamorpho-re7-weth-vs-re7-usdt": "Re7 WETH vault has no guardian; its owner is a 2-of-4 Safe with a 3-day timelock",
    "moonwell-lending-base": "Pause guardian: docs 3-of-5 Security Council · chain 2-of-4 Safe",
    "morpho-blue-core": "Singleton owner and fee and LLTV bounds match the docs",
    "nexus-mutual": "Governance needs 3 Advisory Board votes plus a 24-hour timelock, as documented",
    "obol-network": "Supply: docs cap 500M · chain no cap; a 2-of-3 Safe holds the minter role",
    "ondo-finance-ousg-flux-finance": "OUSG instant mint limit: docs $50M · chain $100M per day",
    "origin-superoeth-base": "Vault proxy admin path runs through a 2-day timelock; docs not assessed",
    "paypal-usd-pyusd": "Pause and asset-protection roles sit with one key address, as documented",
    "pendle-finance-v2": "Markets send 80% of swap fees to the treasury and 20% to LPs, as documented",
    "puffer-finance-pufeth": "Community multisig: docs 3-of-6 · chain 3-of-7",
    "railgun": "0.25% shield fees; upgrades and pauses only via the on-chain protocol vote, as documented",
    "re": "Vault admin role sits only behind the timelock; docs say the Safe holds it too",
    "renzo-protocol-ezeth": "Restaking fee: docs 10% · chain 15%",
    "reserve-protocol-rtoken": "Long freeze is 1 week, the documented default",
    "resolv-usr-rlp": "USR admin-rules delay and request counters match the docs",
    "resupply": "Safe threshold: docs 3-of-4 · chain 3-of-5",
    "rocket-pool-reth": "Council leave notice: chain 28 days · RPIP-33 bound under 14 days",
    "safe-singleton-core": "v1.4.1 singleton and factory code match Safe's registry; singletons cannot be initialized",
    "seamless-protocol-base": "Non-proxy address provider with role-based admin; docs not assessed",
    "solv-protocol-solvbtc": "Beacon upgrades already wait 3 days in a timelock the docs say will be added",
    "spark-sky": "Addresses provider owner and governance delay match the docs",
    "ssv-network": "SSVNetwork owner is the DAO governance multisig, as documented",
    "stader-labs-ethx": "Manager Safe: docs 3-of-5 · chain 3-of-6",
    "stake-dao": "Timelock: docs 2 days · chain 5 days; Treasury Safe 3-of-5, not 4-of-7",
    "stake-link": "Governance timelock delay is 48 hours, as documented",
    "stakewise-v3-oseth": "Keeper oracle quorum, osETH fee and LTV settings match the docs",
    "stargate-v2": "Pools and treasurer are owned by a 5-of-7 multisig, as documented",
    "steakhouse-financial-ethereum": "steakUSDC guardian is its own Aragon DAO, as announced",
    "steakhouse-usdc-metamorpho-base": "MetaMorpho vault timelock is 7 days, as documented",
    "superform-v2-base": "SuperGovernor and vault aggregator control plane pinned; docs not assessed",
    "superstate-ustb-uscc": "USDC subscription fee and fund supply match the docs",
    "swell-sweth-rsweth": "7-day SwellTimelock, ProxyAdmins and reprice bounds match the docs",
    "symbiotic-core": "Core registries are non-upgradeable; factory Safes match the docs",
    "synthetix-v3-core": "Account NFT is owned by the CoreProxy, not a key or Safe, as documented",
    "tether-usdt": "Owner is a 3-of-6 MultiSigWallet, as documented",
    "threshold-network-tbtc": "tBTC timelock is 1 day; the WalletRegistry upgrade schedule is public",
    "treehouse-tree-teth": "TREE owner is a 5-day timelock; a blacklistable upgrade is queued",
    "uniswap-governance-timelock": "Voting period: docs 7 days · chain 5.6 days",
    "uniswap-v4": "Owner is the 2-day governance Timelock run by GovernorBravo, as documented",
    "usual-money-usd0-usd0": "Timelock delay: docs 3 days · chain 1 second",
    "wormhole-core-ntt": "Messages and upgrades need 13 of 19 guardians on Ethereum and Base, as documented",
    "yearn-v3": "Timelock delay: docs none · chain 7 days (stricter)",
    "yo-protocol": "Timelock delay: docs 2 days · chain none",
}


def problems(text):
    """Why a summary line would fail M7 (empty list = fine)."""
    out = []
    if not text or len(text) > MAX:
        out.append(f"length {len(text or '')} (max {MAX})")
    if "…" in text or "..." in text:
        out.append("ellipsis / cut")
    for o, c in ("()", "[]", "{}"):
        if text.count(o) != text.count(c):
            out.append(f"unbalanced {o}{c}")
    if text.count('"') % 2 or len(re.findall(r"(?<![A-Za-z])'|'(?![A-Za-z])", text)) % 2:
        out.append("unbalanced quotes")
    if re.search(r"0x[0-9a-fA-F]{6,}", text):
        out.append("raw address / hash")
    if text != text.strip() or "  " in text:
        out.append("whitespace")
    return out


def check(slugs):
    """Every published protocol has exactly one clean summary line."""
    missing = sorted(set(slugs) - set(SUMMARY))
    extra = sorted(set(SUMMARY) - set(slugs))
    bad = {s: problems(t) for s, t in SUMMARY.items() if problems(t)}
    return missing, extra, bad
