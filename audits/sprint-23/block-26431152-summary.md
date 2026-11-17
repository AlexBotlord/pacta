# Sprint 23 Protocol Commitment Summary — Block `26431152`

- **Ethereum Mainnet pin**: `26431152` (`0x1934eb0`), canonical block hash `0xfe2ed4e127f30bb42dd30c6fc1460a82d8438cff3a717ec89210805e55199a46`, timestamp `2026-11-17 00:22:47 UTC` (`1794874967`); the lower of the two endpoints' `finalized` heads (both `26431152`)
- **Base Mainnet pin**: `58422815` (`0x37b761f`), canonical block hash `0x5aced8e0d59eebe168d9dc8778d0305063a1a02f9ffd264774cbd75b3b979a51`, timestamp `2026-11-17 00:22:18 UTC` (`1794874938`); the lower of the two endpoints' `finalized` heads (both `58422815`)
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI). Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: `gateway.tenderly.co/public/mainnet` + `rpc.mevblocker.io` (Ethereum) and `mainnet.base.org` + `base-rpc.publicnode.com` (Base); the paired `eth_getBlockByNumber` header of each pin is logged with the evidence. Drift baselines were re-read at their original Sprint 7 / 8 blocks on `gateway.tenderly.co/public/mainnet` + `eth.drpc.org`. Verified sources are referenced by their Sourcify match status.
- **Result**: `19` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `18` aligned baselines, `1` parameter delta. `verifiedCount = 18` (`18` aligned baselines). `driftCount = 1` (`1` parameter delta), the same convention as Sprints 1–22 and `PactaSentinelGuard` (`driftCount != 0` means drift). Separately, the Part C post-snapshot drift re-scans found `0` of `3` previously attested protocols drifted across `11` checks (§7).
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); the Circle USDC (Base) records are read at the Base pin.
- **Reading an "aligned" stablecoin record**: aligned means the on-chain control plane matches what the issuer documents. Several issuers document single-role administration; aligned does not mean the token is free of administrator powers (each table states who holds them).

## 1. Circle USDC (Ethereum + Base) — Upgrades and Role Assignment Sit With Single Administrator Addresses, as the Token Design Documents

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **USDC (Ethereum) proxy admin** | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` | slot `keccak256("org.zeppelinos.proxy.admin")` | `0x807a96288A1A408dBC13DE2b1d087d10356395d2`: no contract code at `#26431152` (an externally owned key; no timelock or multisig contract); implementation `FiatTokenV2_2` `0x43506849D7C04F9138D1A2050bbF3A0c054402dd` (Sourcify match); `FiatTokenProxy` (Sourcify match); the EIP-1967 slots are unused |
| **USDC (Ethereum) `owner()`** | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` | `owner()` | `0xFcb19e6a322b27c06842A71e8c725399f049AE3a` (no code); `masterMinter()` = `MasterMinter` `0xE982615d461DD5cD06575BbeA87624fda4e3de17` (7,667 bytes; Sourcify match) whose `owner()` is `0xC1d9fe41D19Dd52cb3Ae5d1D3b0030B5D498c704` (no code); `pauser()` = `0x4914f61d25e5C567143774B76EdbF4D5109a8566` and `blacklister()` = `0x0A06BE16275B95a7d2567fBdAE118b36C7DA78F9` (no code); `rescuer()` = `0x0`; `paused() = false`; `version()` = "2" |
| **USDC (Base) proxy admin** | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | slot `keccak256("org.zeppelinos.proxy.admin")` | `0x4fc7850364958d97B4d3f5A08f79db2493f8cA44`: no contract code at Base `#58422815`; implementation `FiatTokenV2_2` `0x2Ce6311ddAE708829bc0784C967b7d77D19FD779` (Sourcify exact match); `FiatTokenProxy` (Sourcify exact match) |
| **USDC (Base) `owner()`** | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | `owner()` | `0x3ABd6f64A422225E61E435baE41db12096106df7` (no code); `masterMinter()` = `MasterMinter` `0x2230393EDAD0299b7E7B59F20AA856cD1bEd52e1` (Sourcify exact match) whose `owner()` is `0xb5bff84d169a72e76e94eC950da51Bac90b60284` (no code); `pauser()` = `0xD3571B3bc51CECFf49194AD67aFFFC648d5e07b4` and `blacklister()` = `0x1f2e3A640175d20ac31ed523B6733B977173E277` (no code); `rescuer()` = `0x0`; `paused() = false` |

Classification: **aligned baseline** (4 records).
- `developers.circle.com` (USDC contract addresses): "Ethereum 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" and "Base 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913".
- Circle's token design (`circlefin/stablecoin-evm`, `doc/tokendesign.md`): the contract offers "a way to upgrade the contract so that bugs can be fixed or features added."; "`admin` - manage the proxy-level functionalities such as switching the implementation contract"; "`owner` - re-assign any of the roles except for `admin`"; "`masterMinter` - adds and removes minters and increases their minting allowance"; "`pauser` - pause the contract, which prevents all transfers, minting, and burning"; "`blacklister` - prevent all transfers to or from a particular address, and prevents that address from minting or burning". The documentation describes these roles without a multisig or timelock; on-chain each role is a single address without contract code, on both chains (five distinct addresses per chain).

Context (not scored): an address without code at the pin can be a hardware- or custody-controlled key; Pacta records what is on-chain, not Circle's off-chain key management.

## 2. Tether USDT — The Owner Is a 3-of-6 MultiSigWallet, Matching the Documented Multi-Signature Model

| Contract / Check | Address | Selector | Observation at `#26431152` |
| :--- | :--- | :--- | :--- |
| **TetherToken `getOwner()`** | `0xdAC17F958D2ee523a2206206994597C13D831ec7` | `getOwner()` | `MultiSigWallet` `0xC6CDE7C39eB2f0F0095F41570af89eFC2C1Ea828` (Sourcify match): `required() = 3`, `getOwners()` = `6` owners, `transactionCount() = 5,848`; `owner()` returns the same wallet (Sourcify match) |
| **TetherToken `deprecated()`** | `0xdAC17F958D2ee523a2206206994597C13D831ec7` | `deprecated()` | `false`; `upgradedAddress() = 0x0`; `paused() = false`; `basisPointsRate() = 0`, `maximumFee() = 0`. `addBlackList` / `destroyBlackFunds`, `pause` and `deprecate` are `onlyOwner` functions, i.e. they need 3 of the 6 multisig owners, with no timelock |

Classification: **aligned baseline** (2 records).
- `tether.to` (supported protocols): "USD₮ contract address: https://etherscan.io/token/0xdac17f958d2ee523a2206206994597c13d831ec7". FAQ: "Tether Tokens are created by having multiple Tether private authorization keys sign and broadcast creation transactions on the specific blockchain." and "Tether’s multi-signature (or multi-sig) model protects against a single person from authorizing Tether Tokens on their own, which would represent a single point of failure and a security risk."
- `tether.to` (terms of service): "Tether may suspend or terminate your access to the Site or any of the Services, freeze any Tether Tokens held by you, or terminate your Tether Token Wallet"; "blacklisting any Digital Tokens Address which holds Tether Tokens".

## 3. Frax USD (frxUSD / sfrxUSD) — frxUSD Upgrades Wait a 1-Day Timelock; sfrxUSD Upgrades Do Not; the Documented "AMO Timelock (msig)" Is a 3-of-6 Safe

| Contract / Check | Address | Selector / slot | Observation at `#26431152` |
| :--- | :--- | :--- | :--- |
| **frxUSD EIP-1967 admin** | `0xCAcd6fd266aF91b8AeD52aCCc382b4e165586E29` | slot `eip1967.proxy.admin` | `ProxyAdmin` `0x0b2C3dF006b2bd43cBCC60075e7a0bf314474eD6`, owned by `Timelock` `0xb898Ad2976b4d8f2E21521C9db16b7497825E503` (Sourcify exact match): `delay() = 86400`s (`1` day), `admin()` = Safe `0xfFFffF4F3baC444b2C0ecf2A1840d018bE783937` (`4`-of-`7`, v1.3.0, no modules), `pendingAdmin() = 0x0`; frxUSD's own `owner()` is the same Safe directly (`pendingOwner() = 0x0`); transparent proxy (Sourcify match), implementation `0x5c19D7C2838769ED3c5a1E506600940e62fF901F` |
| **sfrxUSD EIP-1967 admin** | `0xcf62F905562626CfcDD2261162a51fd02Fc9c5b6` | slot `eip1967.proxy.admin` | `ProxyAdmin` `0xeA0a6EC8114a0Af6Cf74Ca0036Ab31d892Df13cB`, owned directly by Safe `0xB1748C79709f4Ba2Dd82834B8c82D4a505003f27` (`3`-of-`5`, v1.3.0, no modules; no timelock); `timelockAddress()` = Safe `0x4b45D73b83686e69d08E61105FdB7F7b51f41Bc1` (`3`-of-`6`, v1.4.1, no modules); `asset()` = frxUSD; transparent proxy (Sourcify match), implementation `0xAad4A1D92053a62cE7a787641d8b4E5883e96700` |
| **AMO Timelock (msig) `getThreshold()`** | `0x831822660572bd54ebaa065C2acef662a6277D40` | `getThreshold()` | `3`, with `6` owners (`3`-of-`6` Safe, v1.3.0, no modules): a multisig, as the documentation labels it, with no timelock delay of its own |

Classification: **aligned baseline** (3 records).
- `docs.frax.com` (frxUSD): "The Frax DAO retains ownership and ultimate control of the protocol and may amend or revoke delegated authority at any time." The control plane is held by Frax multisigs (frxUSD upgrades through the 1-day timelock, frxUSD and sfrxUSD roles directly); the documentation names no delay to compare.
- Addresses: "frxUSD Chain type Address Ethereum Native 0xCAcd6fd266aF91b8AeD52aCCc382b4e165586E29"; "sfrxUSD Chain type Address Ethereum Native 0xcf62F905562626CfcDD2261162a51fd02Fc9c5b6"; operations contracts: "AMO Timelock (msig) 0x831822660572bd54ebaa065C2acef662a6277D40".

Context (not scored): the documentation lists the Frax USD Comptroller as "N/A" on Ethereum. The legacy FRAX token and the FRAX (prev. FXS) asset are outside this record set.

## 4. PayPal USD (PYUSD) — Pausing and Asset Protection Sit With a Single Owner Role, Supply With the Documented SupplyControl Contract, Upgrades With the Proxy Admin, as Documented

| Contract / Check | Address | Selector / slot | Observation at `#26431152` |
| :--- | :--- | :--- | :--- |
| **PYUSD `defaultAdmin()`** | `0x6c3ea9036406852006290770BEdFcAbA0e23A0e8` | `defaultAdmin()` | `0x3Af3e85f4f97De7AD0f000B724Fb77fE5ffc024B` (no contract code at the pin), also returned by `owner()`: it holds `PAUSE_ROLE`, `ASSET_PROTECTION_ROLE` and `DEFAULT_ADMIN_ROLE` (`hasRole` = `true`), not `SUPPLY_CONTROLLER_MANAGER_ROLE` / `SUPPLY_CONTROLLER_ROLE` on the token; `defaultAdminDelay() = 10800`s (`3` hours before a new default admin can take over); no pending default admin; `paused() = false` |
| **PYUSD `supplyControl()`** | `0x6c3ea9036406852006290770BEdFcAbA0e23A0e8` | `supplyControl()` | `SupplyControl` `0x31d9bDEa6F104606C954f8FE6ba614F1BD347Ec3` (708-byte ERC-1967 proxy, implementation `0xFaB5891ED867a1195303251912013b92c4fc3a1D`; EIP-1967 admin slot unused): `getAllSupplyControllerAddresses()` lists `5` supply controllers; its `defaultAdmin()` is the same `0x3Af3e85f4f97De7AD0f000B724Fb77fE5ffc024B`, which holds `SUPPLY_CONTROLLER_MANAGER_ROLE` there |
| **PYUSD proxy admin** | `0x6c3ea9036406852006290770BEdFcAbA0e23A0e8` | slot `keccak256("org.zeppelinos.proxy.admin")` | `0xC94BcF6e1d8B3558E3B62e743630D50497E3851C` (no contract code), a different address from the default admin; `AdminUpgradeabilityProxy` (Sourcify match); implementation `PYUSD` `0x8C35CaA5FD5bDC64b6B11344aD57594A3676256a` (Sourcify exact match; its pinned `eth_getCode`, 18,334 bytes, equals Sourcify's runtime bytecode) |

Classification: **aligned baseline** (3 records).
- PYUSD contract documentation (`paxosglobal/pyusd-contract`, README): "In the event of a critical security threat, Paxos has the ability to pause transfers and approvals of the PYUSD token. The ability to pause is controlled by a single `owner` role," and "The `ASSET_PROTECTION_ROLE` can freeze and unfreeze the token balance of any address on chain." On-chain one address holds `PAUSE_ROLE` and `ASSET_PROTECTION_ROLE` and is the token's `owner()`; the implementation uses OpenZeppelin access-control roles rather than `Ownable`, and the roles are not enumerable, so other holders are not excluded.
- Same README: "PYUSD uses a separately deployed `SupplyControl` contract to control the token supply." "`SupplyControl` has a `SUPPLY_CONTROLLER_MANAGER_ROLE` which is responsible for managing addresses with the `SUPPLY_CONTROLLER_ROLE`, referred to as supplyControllers. Only supplyControllers can mint and burn tokens."; `docs.paxos.com` (PYUSD mainnet, Supply Control Contract Addresses): "Ethereum Mainnet 0x31d9bDEa6F104606C954f8FE6ba614F1BD347Ec3".
- Same README: "The proxy used here is AdminUpgradeabilityProxy from ZeppelinOS." "A new implementation contract can be set by calling `upgradeTo()` or `upgradeToAndCall()` on the proxy,"; contract address: "Interaction with PayPal USD is done at the address of the proxy at `0x6c3ea9036406852006290770bedfcaba0e23a0e8`." and `docs.paxos.com`: "Ethereum Mainnet 0x6c3ea9036406852006290770BEdFcAbA0e23A0e8".

Context (not scored): the PYUSD documentation describes single roles and does not claim a multisig or timelock; the role holders and the proxy admin are addresses without contract code at the pin. Pacta records what is on-chain, not Paxos' off-chain key management.

## 5. Uniswap V3 & Governance Timelock — 2-Day Timelock, 40M UNI Quorum and Timelock-Owned Factory as Documented; the Voting Period Is 40,320 Blocks (~5.6 Days), Not 7 Days (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26431152` |
| :--- | :--- | :--- | :--- |
| **Timelock `delay()`** | `0x1a9C8182C09F50C8318d769245beA52c32BE35BC` | `delay()` | `172800`s (`2` days; `MINIMUM_DELAY()` is also `172800`s, `GRACE_PERIOD()` `1209600`s); `admin()` = `GovernorBravoDelegator` `0x408ED6354d4973f66138C91495F2f2FCbd8724C3` (Sourcify exact match); no pending admin (Sourcify match) |
| **UniswapV3Factory `owner()`** | `0x1F98431c8aD98523631AE4a59f267346ea31F984` | `owner()` | `0xf2371551Fe3937Db7c750f4DfABe5c2fFFdcBf5A` (`V3OpenFeeAdapter`, Sourcify exact match), whose `owner()` is the Timelock and `FACTORY()` this factory; not a proxy (Sourcify match); fee tiers 100 / 500 / 3000 / 10000 with tick spacings 1 / 10 / 60 / 200 |
| **GovernorBravo `quorumVotes()`** | `0x408ED6354d4973f66138C91495F2f2FCbd8724C3` | `quorumVotes()` | `40000000000000000000000000` (`40,000,000` UNI); `proposalThreshold()` = `1,000,000` UNI; `timelock()` and `admin()` are the Timelock; implementation `0x53a328F4086d7C0F1Fa19e594c9b842125263026` |
| **GovernorBravo `votingPeriod()`** | `0x408ED6354d4973f66138C91495F2f2FCbd8724C3` | `votingPeriod()` | `40320` blocks: `483,840`s (`5.6` days) at Ethereum's 12-second slots; `votingDelay()` = `13140` blocks (~`1.83` days) |

Classification: **mixed** — `3` aligned baselines, `1` parameter delta.
- **aligned**: `developers.uniswap.org` (governance process, where `docs.uniswap.org` now redirects): "2-day timelock before execution (if passed)" and "Duration: 2-day waiting period, 7-day voting period, 2-day timelock (if passed)"
- **aligned**: deployments: "UniswapV3Factory 0x1F98431c8aD98523631AE4a59f267346ea31F984"; governance process: "2-day timelock before execution (if passed)" The factory's owner is a fee-adapter contract owned by the Timelock.
- **aligned**: governance process: "If the proposal receives 40M UNI in favor votes and passes, the associated onchain actions are queued for anyone to execute after the timelock period ends."
- **parameter delta**: governance process: "7-day voting period for the community to vote" and "Duration: 2-day waiting period, 7-day voting period, 2-day timelock (if passed)" On-chain the voting period is `40320` blocks, about `5.6` days at 12-second slots (it reaches 7 days only if about one slot in five is missed).

Context (not scored): the documented "2-day waiting period" corresponds to `votingDelay() = 13140` blocks (~`1.83` days at 12-second slots), reported, not scored. The published RPC-observed record's primary contract (`UniswapV3Factory`) and controller (`0xf2371551Fe3937Db7c750f4DfABe5c2fFFdcBf5A`) are kept.

## 6. Reserve Protocol (eUSD RToken) — Freeze Durations and the RSR Unstaking Delay Equal the Documented Yield DTF Defaults (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26431152` |
| :--- | :--- | :--- | :--- |
| **eUSD Main `shortFreeze()`** | `0x7697aE4dEf3C3Cd52493Ba3a6F57fc6d8c59108a` | `shortFreeze()` | `259200`s (`3` days); `frozen()`, `tradingPaused()` and `issuancePaused()` are `false`; eUSD `0xA0d69E286B938e21CBf7E51D71F6A4c8918f482F` `main()` = this Main, `version()` = "4.2.0"; ERC-1967 proxies (Sourcify match; Main Sourcify match), implementations `0x258ce833CF9AD19208372763A00aA1565Dd40b3C` / `0xc5bf686CfB85786fcFfF557297D4afF8F4e15e44`; EIP-1967 admin slot unused (UUPS) |
| **eUSD Main `longFreeze()`** | `0x7697aE4dEf3C3Cd52493Ba3a6F57fc6d8c59108a` | `longFreeze()` | `604800`s (`1` week) |
| **eUSD StRSR `unstakingDelay()`** | `0x18ba6e33ceb80f077DEb9260c9111e62f21aE7B8` | `unstakingDelay()` | `1209600`s (`2` weeks); `withdrawalLeak()` = `50000000000000000` (`5`%) (Sourcify match) |

Classification: **aligned baseline** (3 records).
- `docs.reserve.org` (Yield DTFs, advanced parameters): "Short freeze duration (s) The number of seconds a short freeze lasts. Governance can freeze forever. Default value: 259200 = 3 days"
- Same page: "Long freeze duration (s) The number of seconds a long freeze lasts. Long freezes can be disabled by removing all addresses associated with the role. Default value: 604800 = 1 week"
- Same page: "Unstaking delay (s) The unstaking delay is the number of seconds that all RSR unstakings must be delayed in order to account for stakers trying to frontrun defaults." "Default value: 1209600 = 2 weeks"; withdrawal leak: "Default value (mainnet): 5e16 = 5%".

Context (not scored): these are the documented deployment defaults (governance may change them); eUSD keeps them. Its `rewardRatio()` (StRSR and Furnace) is `1069666666666`, not the `1146076687500` default, inside the documented range ("Default value: 1146076687500 = a half-life of 7 days. Mainnet reasonable range: 1e11 to 1e14"). The published RPC-observed record's primary contract (eUSD) is kept.

## 7. Drift Re-Scans (Part C) — 0 of 3 Drifted

Every scored parameter of three of the oldest non-bounty records, read at its original pinned block (archive pair) and at `#26431152` (`audits/sprint-23/drift-rescan-26431152.json`); Ethereum mainnet only. `yearn-v3` is excluded while an open Wave 2 pull request concerns it.

| Protocol (record) | Check | Baseline block | Before | After |
| :--- | :--- | :--- | :--- | :--- |
| ethena-usde-susde | EthenaTimelockController getMinDelay() | `26401638` | `86400` | same |
| ethena-usde-susde | Dev Multisig Safe getThreshold() | `26401638` | `5` | same |
| ethena-usde-susde | Dev Multisig Safe getOwners().length | `26401638` | `10` | same |
| ether-fi-core-eeth-weeth | Upgrade Timelock getMinDelay() | `26401638` | `864000` | same |
| ether-fi-core-eeth-weeth | Operating Timelock getMinDelay() | `26401638` | `172800` | same |
| usual-money-usd0-usd0 | RegistryAccess defaultAdminDelay() | `26401725` | `1` | same |
| usual-money-usd0-usd0 | RegistryAccess pendingDefaultAdminDelay() newDelay | `26401725` | `0` | same |
| usual-money-usd0-usd0 | RegistryAccess pendingDefaultAdminDelay() schedule | `26401725` | `0` | same |
| usual-money-usd0-usd0 | RegistryAccess defaultAdmin() | `26401725` | `0x6e9d65ec80d69b1f508560bc7aea5003db1f7fb7` | same |
| usual-money-usd0-usd0 | Default Admin Safe getThreshold() | `26401725` | `8` | same |
| usual-money-usd0-usd0 | Default Admin Safe getOwners().length | `26401725` | `15` | same |

All `11` "before" values equal the values recorded in the original records (`ethena-admin-timelock-and-dev-safe` and `etherfi-core-timelocks`, Sprint 7; `usual-money-registry-access-delay`, Sprint 8). Unscored extras: the Ethena Dev Multisig and Usual Default Admin Safe owner sets are unchanged; ether.fi `LiquidityPool.getTotalPooledEther()` moved from `2276605532665571773764692` to `2278285163449958470000063` wei (deposits, not control plane).

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-17`). Checks are sampled getters, role checks, EIP-1967 / proxy slots and Safe parameters at the finalized pins above; it does not certify protocol-wide immutability, exhaustive authority coverage or exploitability, and it is not a smart-contract audit. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to the affected protocols. Pacta by Fractal Neurons publishes these records as documentation-comparison evidence, not as audits or investment advice.
