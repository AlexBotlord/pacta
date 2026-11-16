# Sprint 22 Protocol Commitment Summary — Block `26429396`

- **Ethereum Mainnet pin**: `26429396` (`0x19347d4`), canonical block hash `0x3fb83aa053c26ac6b98d634858da1b3c23bb65bae7a12f8f14d72d8273e16d71`, timestamp `2026-11-16 18:30:47 UTC` (`1794853847`); the lower of the two endpoints' `finalized` heads (both `26429396`)
- **Base Mainnet pin**: `58315414` (`0x379d296`), canonical block hash `0x5092b494a9f8555faecfaa0f49202536e0edcf26f2bdc6e25a563442258119cd`, timestamp `2026-11-16 18:24:18 UTC` (`1794853458`); the lower of the two endpoints' `finalized` heads
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI). Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: `gateway.tenderly.co/public/mainnet` + `rpc.mevblocker.io` (Ethereum) and `mainnet.base.org` + `base-rpc.publicnode.com` (Base); the paired `eth_getBlockByNumber` header of each pin is logged with the evidence. Drift baselines were re-read at their original Sprint 4 / 5 / 6 blocks on `gateway.tenderly.co/public/mainnet` + `eth.drpc.org`. Verified sources are referenced by their Sourcify match status.
- **Result**: `19` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `13` aligned baselines, `1` protective delta, `5` parameter deltas. `verifiedCount = 14` (`13` aligned baselines + `1` protective delta). `driftCount = 5` (`5` parameter deltas), the same convention as Sprints 1–21 and `PactaSentinelGuard` (`driftCount != 0` means drift). Separately, the Part C post-snapshot drift re-scans found `0` of `3` previously attested protocols drifted across `14` checks (§7).
- **Community research**: the Stake DAO, Resupply and YO Protocol findings were first reported through Pacta's Wave 1 bounty (merged, paid and granted under Apache-2.0); each section credits its researcher. Pacta re-read every value at its own pins.
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); the YO Protocol and Beefy Finance (Base) records are read at the Base pin.

## 1. Stake DAO — ProtocolTimelock Delay Is 5 Days, Not 48 Hours; Execution Is Not Permissionless; Treasury Safe Is 3-of-5

Origin: Wave 1 bounty Slot #1, reported by @veriton-dev (github.com/Fractal-Neurons/pacta/pull/27; merged, paid and granted under Apache-2.0). Every value below was re-read independently at the Sprint 22 pin.

| Contract / Check | Address | Selector | Observation at `#26429396` |
| :--- | :--- | :--- | :--- |
| **ProtocolTimelock `getMinDelay()`** | `0xb27afc7844988948FBd6210AeF4E1362bC2d8E6a` | `getMinDelay()` | `432000`s (`5` days); OpenZeppelin `TimelockController` (Sourcify exact match); its own admin (`DEFAULT_ADMIN_ROLE`); `protocolController()` = `0x2d8BcE1FaE00a959354aCD9eBf9174337A64d4fb` |
| **ProtocolTimelock `hasRole(EXECUTOR_ROLE, address(0))`** | `0xb27afc7844988948FBd6210AeF4E1362bC2d8E6a` | `hasRole(bytes32,address)` | `false`: execution is permissioned (open execution would need `address(0)` to hold `EXECUTOR_ROLE`); the Governance Safe `0xB0552b6860CE5C0202976Db056b5e3Cc4f9CC765` (`3`-of-`5`, v1.3.0, `3` modules enabled) holds `EXECUTOR_ROLE`, `PROPOSER_ROLE`, `CANCELLER_ROLE` and `GUARDIAN_ROLE`; the timelock itself does not hold `EXECUTOR_ROLE` |
| **ProtocolController `owner()`** | `0x2d8BcE1FaE00a959354aCD9eBf9174337A64d4fb` | `owner()` | ProtocolTimelock `0xb27afc7844988948FBd6210AeF4E1362bC2d8E6a`; `pendingOwner() = 0`; not a proxy (Sourcify exact match) |
| **Treasury Safe `getThreshold()`** | `0xF930EBBd05eF8b25B1797b9b2109DDC9B0d43063` | `getThreshold()` | `3`, with `5` owners (`3`-of-`5`, v1.3.0, no modules): the same five signers as the Governance Safe |

Classification: **mixed** — `1` protective delta, `2` parameter deltas, `1` aligned baseline.
- **protective delta**: `docs.stakedao.org` (timelock): "Stake DAO's core contracts are protected by a governance timelock that enforces a 48-hour delay on all protocol changes." and "A proposer submits the operation with a minimum 48-hour delay" On-chain the minimum delay is `5` days, longer than documented.
- **parameter delta**: same page (role structure): Executor — "Can execute operations after delay (permissionless)"; Proposer — "Can schedule operations (governance multisig)". The proposer is the governance multisig as documented, but `EXECUTOR_ROLE` is not granted to `address(0)`, so execution is permissioned (OpenZeppelin `onlyRoleOrOpenRole`) rather than permissionless; the 3-of-5 Governance Safe holds `EXECUTOR_ROLE`. The timelock uses OpenZeppelin `AccessControl` without enumeration, so other `EXECUTOR_ROLE` holders are not excluded.
- **aligned**: same page: "The ProtocolTimelock contract owns the ProtocolController and all critical protocol parameters."; contract addresses: "PROTOCOL_CONTROLLER | `0x2d8BcE1FaE00a959354aCD9eBf9174337A64d4fb`".
- **parameter delta**: `docs.stakedao.org` (treasury): "All wallets use a 4-of-7 multisig structure." and "Ethereum | `0xf930ebbd05ef8b25b1797b9b2109ddc9b0d43063`". On-chain that wallet is `3`-of-`5`.

Context (not scored): veSDT `0x0C30476f66034E11782938DF8e4384970B6c9e8a` (listed as "veSDT (Sunset)") has `admin() = future_admin()` = the Governance Safe directly, not the ProtocolTimelock. Per the documentation, guardians can pause deposits and shut down gauges without the delay ("Can execute emergency security functions immediately"); withdrawals are documented to stay available.

## 2. Resupply — Core Owns the Protocol and the Voter Executes After 1 Day as Documented; the Main Multisig Is 3-of-5, Not 3 of 4

Origin: Wave 1 bounty Slot #2, reported by @scavenger-osan (github.com/Fractal-Neurons/pacta/pull/31; merged, paid and granted under Apache-2.0). Every value below was re-read independently at the Sprint 22 pin.

| Contract / Check | Address | Selector | Observation at `#26429396` |
| :--- | :--- | :--- | :--- |
| **Core `voter()`** | `0xc07e000044F95655c11fda4cD37F70A94d7e0a7d` | `voter()` | Voter `0x11111111063874cE8dC6232cb5C1C849359476E6`, whose `owner()` and `core()` are Core; Voter `executionDelay() = 86400`s (`1` day), `votingPeriod() = 604800`s (`1` week), `quorumPct() = 3000` of `MAX_PCT() = 10000` (`30`%), `minCreateProposalPct() = 100` (`1`%), `EXECUTION_DEADLINE() = 1814400`s (`3` weeks), `minTimeBetweenProposals() = 86400`s; Core `epochLength() = 604800`s (Sourcify match) |
| **Guardian operator proxy `guardian()`** | `0xA4745e0B1F40ab3DCFD98F381835De591a8974E3` | `guardian()` | Main Multisig `0xFE11a5009f2121622271e7dd0FD470264e076af6`; `owner()` = Core; ERC-1967 proxy, implementation `GuardianUpgradeable` `0x74C85620F1459862834A947dB9441911BCEBF066` (Sourcify match); the Treasury Manager operator proxy `0x4CF97a55d58Aad14C493A46C8151a0BFffb10403` has `manager()` = the same multisig and `owner()` = Core |
| **Main Multisig `getThreshold()`** | `0xFE11a5009f2121622271e7dd0FD470264e076af6` | `getThreshold()` | `3`, with `5` owners (`3`-of-`5`, v1.4.1, no modules) |
| **Registry `owner()`** | `0x10101010E0C3171D894B71B3400668aF311e7D94` | `owner()` | Core `0xc07e000044F95655c11fda4cD37F70A94d7e0a7d` (also `core()`) |

Classification: **mixed** — `3` aligned baselines, `1` parameter delta.
- **aligned**: `docs.resupply.finance` (governance voting): "All contracts on Resupply will be owned by a main core contract with a separate voter contract that is able to execute any transactions as though it is core." Live parameters: "Execution delay after vote passes | 1 day", "Voting period | 1 week", "Quorum to pass | 30% of total weight", "Execution deadline | 3 weeks (after creation)".
- **aligned**: `docs.resupply.finance` (multisig and admin permissions): "The following roles are occupied by the Resupply main multisig." Guardian: "Can pause the protocol in an emergency"; "The proxies are owned by `Core` which means that upgrades can be performed only via successful governance vote."
- **parameter delta**: same page: "Multisig Members (3 of 4)" and contract addresses: "Multisig (3-of-4) | `0xFE11a5009f2121622271e7dd0FD470264e076af6`". On-chain the Main Multisig has `5` owners.
- **aligned**: multisig and admin permissions: "All Resupply contracts are owned by `Core`, which can authorize specific accounts (generically referred to as "operators") to call specified functions on protocol or non-protocol assets from the context of Core."; contract addresses: "Registry | `0x10101010E0C3171D894B71B3400668aF311e7D94`".

Context (not scored): the documentation's GitBook domain is `docs.resupply.finance`.

## 3. YO Protocol (Base) — Vault Upgrades Wait the 48-Hour Timelock, but the Approval Registry Is Owned Directly by the Admin Multisig

Origin: Wave 1 bounty Slot #3, reported by @kinshu7777 (github.com/Fractal-Neurons/pacta/pull/29; merged, paid and granted under Apache-2.0). Every value below was re-read independently at the Sprint 22 pin.

| Contract / Check | Address | Selector | Observation at Base `#58315414` |
| :--- | :--- | :--- | :--- |
| **YoApprovalRegistry `owner()`** | `0xB4b3F5C964A360bBd7201f72a55D0c48B8aD7021` | `owner()` | YO Admin Multisig `0x67b6F699F1c8040414032a3C2C88a54db144FCd2` (`4`-of-`6` Safe, v1.4.1, no modules), not the YO Timelock; `pendingOwner() = 0`; not a proxy (Sourcify exact match); it is the `approvalRegistry()` of yoETH `0x3A43AEC53490CB9Fa922847385D82fe25d0E9De7` and yoUSD `0x0000000f2eB9f69274678c76222B35eEc7588a65`; YoPoolRegistry, YoBridgeRouteRegistry, YoMorphoMarketRegistry, YoSwapPairRegistry and YoERC4626VaultRegistry are also owned directly by the Admin Multisig |
| **YO Timelock `getMinDelay()`** | `0x38cE5e45D0f5d03E83863bb19B3b1A272C186F48` | `getMinDelay()` | `172800`s (`48` hours); OpenZeppelin `TimelockController` (Sourcify match); the Admin Multisig holds `PROPOSER_ROLE`, `EXECUTOR_ROLE` and `CANCELLER_ROLE`; the timelock is its own admin |
| **yoETH ProxyAdmin `owner()`** | `0xd460CF1f5D764acAD1c3276c549EE5f1BB671473` | `owner()` | YO Timelock `0x38cE5e45D0f5d03E83863bb19B3b1A272C186F48`: yoETH's EIP-1967 admin is this ProxyAdmin (Sourcify match); yoUSD's ProxyAdmin `0x12E81209d180fF0b3FBFbfe8fA9fFdb5990e1073` is also owned by the Timelock; both vaults use implementation `0xc84a6E01BFF58996540F1ABC22355A9DFE0d78DC`; the vaults' `owner()` is the Admin Multisig |

Classification: **mixed** — `2` aligned baselines, `1` parameter delta.
- **parameter delta**: `docs.yo.xyz` (YO V2 Security Framework): "Approval Registry: Onchain, timelocked caps on how much of each asset a vault may approve to each contract" and "Every path a dollar can take is written into immutable adapters and timelocked registries"; the same page: "The Approval Registry fixes, onchain and behind the timelock, the maximum of each asset a given vault can approve to a given contract" On-chain the YoApprovalRegistry's `owner()` is the Admin Multisig, with no timelock delay in between.
- **aligned**: same page: "… with a mandatory 48-hour delay and sign-off from a 4-of-6 multi-sig of geographically distributed signers."; contract addresses: "YO Timelock 0x38cE5e45D0f5d03E83863bb19B3b1A272C186F48 EVMs Authority that gates contracts upgrades behind a 48 hr timelock."
- **aligned**: contract addresses: "YO Timelock 0x38cE5e45D0f5d03E83863bb19B3b1A272C186F48 EVMs Authority that gates contracts upgrades behind a 48 hr timelock." and "YO Admin Multisig 0x67b6F699F1c8040414032a3C2C88a54db144FCd2 EVMs Overall manager for all yoVaults, including contract upgrades, and whitelisting new protocols and pools."

Context (not scored): the RolesAuthority `0x9524e25079b1b04D904865704783A5aA0202d44D` (both vaults' `authority()`) and the Vault Registry are also owned by the Admin Multisig. Whether a registry owner can change caps without the Timelock depends on each registry's owner-only functions (this summary records ownership, not exploitability).

## 4. Across Protocol (HubPool) — Root-Bundle Bond 0.45 ABT and an Allow-Listed Proposer, as Documented (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26429396` |
| :--- | :--- | :--- | :--- |
| **HubPool `bondAmount()`** | `0xc186fA914353c44b2E33eBE05f21846F1048bEda` | `bondAmount()` | `450000000000000000` (`0.45` ABT); `bondToken()` = Across Bond Token `0xee1DC6BCF1Ee967a350e9aC6CaaAA236109002ea`; `liveness() = 1800`s; `paused() = false`; `identifier()` = "ACROSS-V2"; `owner()` = Safe `0xB524735356985D2f267FA010D681f061DfF03715` (`3`-of-`5`, v1.3.0, `1` module); not a proxy (Sourcify match) |
| **Across Bond Token `proposers(address)`** | `0xee1DC6BCF1Ee967a350e9aC6CaaAA236109002ea` | `proposers(address)` | `true` for the current root-bundle proposer `0xf7bAc63fc7CEaCf0589F25454Ecf5C2ce904997c`, `false` for `address(0)`; `name()` = "Across Bond Token", `hubPool()` = the HubPool, `owner()` = the HubPool owner Safe (Sourcify exact match: `transferFrom` into the HubPool requires an allow-listed proposer) |

Classification: **aligned baseline** (2 records).
- `docs.across.to` (security model): "Proposing a root bundle ~0.45 ABT" and "The bond amount is configurable via the HubPool contract's bondAmount() function."; disputing root bundles: "const HUBPOOL = "0xc186fA914353c44b2E33eBE05f21846F1048bEda"".
- Same page: "The Across Bond Token is a custom ERC-20 that functions similarly to WETH." "ABT has an additional property: it restricts which addresses may propose root bundles to the HubPool."

Context (not scored): the documentation does not state the challenge period in seconds ("Bundles are proposed every ~1.5 hours minimum. After proposal, they enter a challenge period where anyone can dispute them."); on-chain `liveness() = 1800`s is reported, not compared. The documentation does not describe the HubPool owner Safe; it stays the protocol's published controller.

## 5. Beefy Finance (Base) — Dev Multisig 3-of-6 and a 6-Hour Strategy-Owner Timelock as Documented; the Vault-Owner Timelock Has No Delay (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at Base `#58315414` |
| :--- | :--- | :--- | :--- |
| **BeefyFeeConfig `owner()`** | `0xfc69704cC3cAac545cC7577009Ea4AA04F1a61Eb` | `owner()` | Beefy dev multisig `0x6FfaCA7C3B38Ec2d631D86e15f328ee6eF6C6226` (`3`-of-`6` Safe, v1.3.0, no modules); transparent proxy (Sourcify exact match), implementation `0xAb35d11199216c7F7368080Cf41beD8f3AbBc4E4`, EIP-1967 admin = ProxyAdmin `0x2b0C9702A4724f2BFe7922DB92c4082098533c62` |
| **strategyOwner timelock `getMinDelay()`** | `0x3B60F7f25b09E71356cdFFC6475c222A466a2AC9` | `getMinDelay()` | `21600`s (`6` hours); OpenZeppelin `TimelockController` (Sourcify exact match); the dev multisig holds `PROPOSER_ROLE`, `EXECUTOR_ROLE` and `CANCELLER_ROLE`; the timelock is its own admin; it owns the FeeConfig's ProxyAdmin |
| **vaultOwner timelock `getMinDelay()`** | `0x09D19184F46A32213DF06b981122e06882B61309` | `getMinDelay()` | `0`s; OpenZeppelin `TimelockController` (Sourcify exact match); the dev multisig holds `PROPOSER_ROLE`, `EXECUTOR_ROLE` and `CANCELLER_ROLE`; the timelock is its own admin |

Classification: **mixed** — `2` aligned baselines, `1` parameter delta.
- **aligned**: `docs.beefy.finance` (contracts and timelocks): "It is a 3 of 6 multisig" and "the dev multisig is set as either the direct owner of Beefy's contracts or as the owner of the timelock which in turn owns Beefy's contracts."; Base address book (linked from that page: "Vault and strategy owner addresses can be found in the addressbook under the Beefy protocol files."): "const devMultisig = '0x6FfaCA7C3B38Ec2d631D86e15f328ee6eF6C6226';"
- **aligned**: same page: "By default, a 6-hour timelock is configured for all strategy changes and upgrades."; address book: "strategyOwner: '0x3B60F7f25b09E71356cdFFC6475c222A466a2AC9',"
- **parameter delta**: same page: "Beefy ensures that all privileged functions and upgrades are protected by standardised smart contract timelocks." and "By default, a 6-hour timelock is configured for all strategy changes and upgrades."; address book: "vaultOwner: '0x09D19184F46A32213DF06b981122e06882B61309'," On-chain the vault-owner timelock's minimum delay is `0`s.

Context (not scored): the published RPC-observed record pairs BeefyFeeConfig with the dev multisig; both stay the protocol's primary contract and controller.

## 6. Liquity V1 (LUSD) — Ownership Renounced on Every Core Contract, No Proxies; 110% / 150% Ratios and 0.5% Fee Floors as Documented

| Contract / Check | Address | Selector | Observation at `#26429396` |
| :--- | :--- | :--- | :--- |
| **TroveManager `owner()`** | `0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2` | `owner()` | `0x0` (renounced); the same for BorrowerOperations, StabilityPool, ActivePool, DefaultPool, PriceFeed, SortedTroves, CollSurplusPool, LQTYStaking, CommunityIssuance and HintHelpers; none of these `11` contracts, the LUSD token `0x5f98805A4E8be255a32880FDeC7F6728C6568bA0` or the LQTY token `0x6DEA81C8171D0bA574754EF6F8b412F2Ed88c54D` has an EIP-1967 implementation or admin slot set |
| **TroveManager `MCR()`** | `0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2` | `MCR()` | `1100000000000000000` (`110`%); `CCR() = 1500000000000000000` (`150`%) |
| **TroveManager `BORROWING_FEE_FLOOR()`** | `0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2` | `BORROWING_FEE_FLOOR()` | `5000000000000000` (`0.5`%); `MAX_BORROWING_FEE() = 50000000000000000` (`5`%); `REDEMPTION_FEE_FLOOR() = 5000000000000000` (`0.5`%); `MIN_NET_DEBT() = 1800` LUSD + `LUSD_GAS_COMPENSATION() = 200` LUSD = `2,000` LUSD minimum debt |

Classification: **aligned baseline** (3 records).
- `docs.liquity.org` (Liquity V1, general): "Liquity as a protocol is non-custodial, immutable, and governance-free." and "No. Liquity has no admin key, and nobody can alter the rules of the system in any way. The smart contract code is completely immutable."; technical resources: "| troveManager | 0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2 |"
- Borrowing: "This is a protocol parameter that is set to `110%`."; Recovery Mode: "During Recovery Mode, Troves with a collateral ratio below 150% can be liquidated."
- Borrowing: "The fee rate is confined to a range between `0.5%` and `5%`" and "A minimum debt of `2,000 LUSD` is required."; redemptions: "Under normal operation, the redemption fee is given by the formula `(baseRate + 0.5%) * ETHdrawn`"

Context (not scored): the LUSD token ("LUSD Stablecoin") is wired to the documented TroveManager, StabilityPool and BorrowerOperations, and the TroveManager to the documented BorrowerOperations, StabilityPool and LUSD token; `getEntireSystemColl() = 71378482662720910653702` wei of ETH. Liquity V1 is distinct from the indexed Liquity V2 (BOLD).

## 7. Drift Re-Scans (Part C) — 0 of 3 Drifted

Every scored parameter of three of the oldest non-bounty records, read at its original pinned block (archive pair) and at `#26429396` (`audits/sprint-22/drift-rescan-26429396.json`); Ethereum mainnet only:

| Protocol (record) | Check | Baseline block | Before | After |
| :--- | :--- | :--- | :--- | :--- |
| mellow-protocol-lido-earn | Curator Safe getThreshold() | `26401312` | `3` | same |
| mellow-protocol-lido-earn | Curator Safe getOwners().length | `26401312` | `5` | same |
| mellow-protocol-lido-earn | earnETH hasRole(DEFAULT_ADMIN_ROLE, Lazy Vault Admin Safe) | `26401312` | `1` | same |
| mellow-protocol-lido-earn | earnUSD hasRole(DEFAULT_ADMIN_ROLE, Lazy Vault Admin Safe) | `26401312` | `1` | same |
| mellow-protocol-lido-earn | Lazy Vault Admin Safe getThreshold() | `26401312` | `5` | same |
| mellow-protocol-lido-earn | Lazy Vault Admin Safe getOwners().length | `26401312` | `8` | same |
| mellow-protocol-lido-earn | Timelock getMinDelay() | `26401312` | `0` | same |
| fluid-instadapp | VaultFactory isVaultAuth(Vault 76, 0x4F6F..D49e) | `26401405` | `1` | same |
| fluid-instadapp | VaultFactory isVaultAuth(Vault 110, 0x4F6F..D49e) | `26401405` | `1` | same |
| fluid-instadapp | VaultFactory isVaultAuth(Vault 111, 0x4F6F..D49e) | `26401405` | `1` | same |
| fluid-instadapp | VaultFactory isVaultAuth(Vault 144, 0x4F6F..D49e) | `26401405` | `1` | same |
| liquity-v2-bold | BOLD owner() | `26401540` | `0x0000000000000000000000000000000000000000` | same |
| liquity-v2-bold | Governance owner() | `26401540` | `0x0000000000000000000000000000000000000000` | same |
| liquity-v2-bold | CollateralRegistry EIP-1967 implementation slot | `26401540` | `0x0000000000000000000000000000000000000000000000000000000000000000` | same |

All `14` "before" values equal the values recorded in the original records (`mellow-lido-earn-curator-quorum`, Sprint 4; `fluid-instadapp-vault-factory-auth`, Sprint 5; `liquity-v2-bold-immutability`, Sprint 6). Unscored extras, all unchanged: the two Mellow Safes' owner sets and `earnETH` `hasRole(DEFAULT_ADMIN_ROLE, Timelock)`.

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-16`). Checks are sampled getters, role checks, EIP-1967 / proxy slots and Safe parameters at the finalized pins above; it does not certify protocol-wide immutability, exhaustive authority coverage or exploitability, and it is not a smart-contract audit. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to the affected protocols. Pacta by Fractal Neurons publishes these records as documentation-comparison evidence, not as audits or investment advice.
