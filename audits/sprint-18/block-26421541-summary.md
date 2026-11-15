# Sprint 18 Protocol Commitment Summary — Block `26421541`

- **Ethereum Mainnet pin**: `26421541` (`0x1932925`), canonical block hash `0xfc2e93c53812cd390b29924a4e217bd4f75d77725bd2882968fb5b087a17150d`, timestamp `2026-11-15 16:16:23 UTC` (`1794759383`)
- **Base Mainnet pin** (Aerodrome Slipstream and Moonwell records): `57842915` (`0x3729ce3`), canonical block hash `0x7ae27f2be8e931c33ac284c8d5c548c8fd7a68f08e18bb372c70e2ca3b4bd129`, timestamp `2026-11-15 16:09:18 UTC` (`1794758958`)
- **Scanner**: Pacta Protocol Commitments DRI. Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: Ethereum `rpc.mevblocker.io` + `gateway.tenderly.co/public/mainnet`; Base `mainnet.base.org` + `base.drpc.org`. Drift baselines were re-read at their original Sprint 2 / 3 blocks on `gateway.tenderly.co/public/mainnet` + `rpc.mevblocker.io`.
- **Result**: `7` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `5` aligned baselines, `1` protective delta, `1` parameter delta. `verifiedCount = 6` (`5` aligned baselines + `1` protective delta). `driftCount = 1` (`1` parameter delta: the Moonwell pause guardian), the same convention as Sprints 1–17 and `PactaSentinelGuard` (`driftCount != 0` means drift). Separately, the Part C post-snapshot drift re-scans found `0` of `3` previously attested protocols drifted across `21` checks (§7).
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above)

## 1. Nexus Mutual — Governor: 3 Advisory Board Votes + 24-Hour Timelock

| Contract / Check | Address | Selector | Observation at `#26421541` |
| :--- | :--- | :--- | :--- |
| **`Governor.TIMELOCK_PERIOD()`** | `0xcafea6063d4Ec6b045d9676e58897C1f0882Ca32` | `TIMELOCK_PERIOD()` | `86400`s (`24` h); `VOTING_PERIOD() = 259200`s, `ADVISORY_BOARD_THRESHOLD() = 3`; EIP-1967 proxy, implementation `Governor` `0xcafea466bF6dEFe480cdd54056C020c63b7DA830` (Sourcify `exact_match`), admin = Registry |
| **`Registry`** | `0xcafea2c575550512582090AA06d0a069E7236b9e` | `getContractAddressByIndex(2)` | the Governor; `ADVISORY_BOARD_SEATS() = 5`; EIP-1967 proxy (implementation `Registry` `0xcafeaC64cBE73e6e8973b52cDAE8982DE6Fb500E`, Sourcify `exact_match`) whose admin is the Governor; `proxyOwner()` of all `10` module proxies resolved through `NXMaster.getLatestAddress` (`GV`, `P1`, `MR`, `TC`, `CO`, `SP`, `RA`, `AS`, `CI`, `LO`) |
| **Emergency pause** | `0xcafea2c575550512582090AA06d0a069E7236b9e` | `isEmergencyAdmin(address)` | `true` for `6` accounts (the `5` Advisory Board seat holders and `0x6fe2c2643cb5064951fb7dd87fbce4777fb146e3`, all EOAs), set together at block `23,689,684`; the verified source requires one admin to propose and a different admin to confirm a pause; `getPauseConfig() = 0` (not paused) |

Classification: **aligned baseline** — `docs.nexusmutual.io/governance/`: "Three votes in favour carry the proposal, at which point voting closes and the timelock starts." and "A 24-hour timelock runs before a carried proposal can be executed." The verified `Registry.upgradeContract` is `onlyGovernor`.
Context (not compared with documentation, not scored): the legacy `NXMaster` (`0x01BFd82675DBCc7762C84019cA518e701C0cD07e`; `emergencyAdmin()` = a `2`-of-`6` Safe, `isPause() = 0`) is owned (`proxyOwner()`) by the legacy Governance proxy `0x4A5C681dDC32acC6ccA51ac17e9d461e6be87900`, whose implementation is `TemporaryGovernance` (`0xcafeaf47dAc3aCBa0Aa0974DcA9195209DA6ef20`, Sourcify `exact_match`). Its `advisoryBoardMultisig()` (`0x51ad1265C8702c9e96Ea61Fe4088C2e22eD4418e`, a `3`-of-`5` Safe whose owners are the `5` Advisory Board seat holders) can execute any call through it without a timelock. The docs list NXMaster and Governance as legacy: "These contracts remain deployed to serve historical data and are not part of the current protocol flow".

## 2. Enzyme Finance (v4) — Dispatcher Migration Timelock Is 7 Days, Not 0

| Contract / Check | Address | Selector | Observation at `#26421541` |
| :--- | :--- | :--- | :--- |
| **`Dispatcher.getMigrationTimelock()`** | `0xC3DC853dD716bd5754f421ef94fdCbac3902ab32` | `getMigrationTimelock()` | `604800`s (`7` days); in the verified source (Sourcify `exact_match`) `signalMigration` sets `executableTimestamp = block.timestamp + migrationTimelock` |
| **`Dispatcher.getOwner()`** | `0xC3DC853dD716bd5754f421ef94fdCbac3902ab32` | `getOwner()` | Safe `0xb270FE91e8E4b80452fBF1b4704208792A350f53` (`3`-of-`5`, v1.3.0); `getNominatedOwner() = 0`; `getCurrentFundDeployer()` = `0x4f1C53F096533C04d8157EFB6Bca3eb22ddC6360`, whose `getOwner()` is the same Safe |

Classification: **protective delta** — `specs.enzyme.finance` (fund lifecycle): "MigratorA waits for the `migrationTimelock` defined on the `Dispatcher` to pass. [NOTE: This is no longer used and is set to `0`]". On-chain the timelock is set to 7 days and is enforced on migrations. The specs also say "The owner is already the Enzyme Council." (no Council address or threshold is published); the owner is a 3-of-5 Safe that can call `setCurrentFundDeployer` / `setMigrationTimelock` without a delay.

## 3. Stargate V2 (Ethereum) — 5-of-7 OneSig Owns the V2 Contracts; the Planner Sets Fees

| Contract / Check | Address | Selector | Observation at `#26421541` |
| :--- | :--- | :--- | :--- |
| **`StargatePoolUSDC.owner()`** | `0xc026395860Db2d07ee33e05fE50ed7bD583189C7` | `0x8da5cb5b` | `OneSig` `0xBE634B030FEAaB661300667EaF82510a3a025413` (`threshold() = 5` of `7` signers, `VERSION() = 0.0.1`, Sourcify `exact_match`: executes threshold-signed Merkle roots that carry only an expiry, no delay); `TokenMessaging` (`0x6d6620eFa72948C5f68A3C8646d58C00d3f4A980`) and `Treasurer` (`0x1041D127b2d4BC700F0F563883bC689502606918`) `owner()` = the same OneSig |
| **Planner** | `0xc026395860Db2d07ee33e05fE50ed7bD583189C7` | `getAddressConfig()` | planner `0xe37f7c80ceD04c4F243C0Fd04A5510D663CB88b5` (an EOA) = `TokenMessaging.planner()` = `FeeLibV1USDC` (`0x52B35406CB2FB5e0038EdEcFc129A152a1f74087`) `owner()`; pool `status() = 1` |

Classification: **aligned baseline** — Stargate docs (`stargateprotocol.gitbook.io`): "From time to time, a vote may require a change to the Stargate protocol or its treasury that requires action via multisig."; the V2 README: "A Planner is a trusted entity that can allocate credit between chains off chain"; and "Fees within the Stargate protocol are dynamic, and are set by the AI Planning Module on a per pathway basis."
Context (not compared, not scored): the docs' "StargateDAO Multisig" on Ethereum, `0x65bb797c2B9830d891D87288F029ed8dACc19705` (a `3`-of-`5` Safe), is not the owner of these V2 contracts; the docs do not name the V2 owner.

## 4. Aerodrome Slipstream (Base) — CLFactory Owner and Fee Managers = Protocol Team 3-of-7 Safe

| Contract / Check | Address | Selector | Observation at Base `#57842915` |
| :--- | :--- | :--- | :--- |
| **`CLFactory.owner()`** | `0x5e7BB104d84c7CB9B682AaC2F3d509f5F406809A` | `0x8da5cb5b` | Safe `0xE6A41fE61E7a1996B59d508661e3f524d6A32075` (`3`-of-`7`, v1.3.0); `swapFeeManager()` and `unstakedFeeManager()` = the same Safe; `swapFeeModule()` = `0x090b2A6bb475c00e2256e2095A60887cD710803b`, `unstakedFeeModule()` = `0x0AD08370c76Ff426F534bb2AFFD9b5555338ee68`, `defaultUnstakedFee() = 100000`, `allPoolsLength() = 3684` |

Classification: **aligned baseline** — Aerodrome `PERMISSIONS.md`: "Protocol Team" "Multisig at 0xE6A41fE61E7a1996B59d508661e3f524d6A32075", "Fee Manager" "Protocol team"; the Slipstream deploy constants (`script/constants/Base.json`) name the same Safe as `poolFactoryOwner` and `feeManager`.
Context (not compared, not scored): the Voter (`0x16613524e02ad97eDfeF371bC883F2F5d6C480A5`) reports `governor()` = the same Protocol Team Safe and `emergencyCouncil()` = `epochGovernor()` = `AerodromeMigration` (`0x22a2F7340a3fB4C7C389D91eE954766B12476721`, Sourcify match; `owner()` = a `3`-of-`7` Safe, v1.5.0), not the security page's Council `0x99249b10593fCa1Ae9DAE6D4819F1A6dae5C013D` (a `3`-of-`7` Safe). The docs announce: "In 2026, Aerodrome will merge with Velodrome ... to become Aero".

## 5. Euler V2 (EVK) — FactoryGovernor Behind a 4-Day Timelock (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26421541` |
| :--- | :--- | :--- | :--- |
| **`GenericFactory.upgradeAdmin()`** | `0x29a56a1b8214D9Cf7c5561811750D5cBDb45CC8e` | `upgradeAdmin()` | `FactoryGovernor` `0x2F13256E04022d6356d8CE8C53C7364e13DC1f3d`; `implementation()` = `0x8Ff1C814719096b61aBf00Bb46EAd0c9A529Dd7D` |
| **`FactoryGovernor` roles** | `0x2F13256E04022d6356d8CE8C53C7364e13DC1f3d` | `getRoleMember(bytes32,uint256)` | `DEFAULT_ADMIN_ROLE`: `1` member, `TimelockController` `0xfb034c1C6c7F42171b2d1Cb8486E0f43ED07A968`; `PAUSE_GUARDIAN_ROLE`: `3` members (`0xB1345E7A4D35FB3E6bF22A32B3741Ae74E5Fba27`, a `2`-of-`6` Safe; `0xff217004BdD3A6A592162380dc0E6BbF143291eB`; `0xcC6451385685721778E7Bd80B54F8c92b484F601`); `UNPAUSE_ADMIN_ROLE`: the `2`-of-`6` Safe |
| **`TimelockController.getMinDelay()`** | `0xfb034c1C6c7F42171b2d1Cb8486E0f43ED07A968` | `0xf27a0c92` | `345600`s (`4` days); `PROPOSER_ROLE`: Safe `0xcAD001c30E96765aC90307669d578219D4fb1DCe` (`4`-of-`8`); `EXECUTOR_ROLE`: open (`address(0)`); `CANCELLER_ROLE`: that Safe and Safe `0xb3b84e8320250Afe7a5fb313Ee32B52982b73c53` (`2`-of-`3`); the timelock is its own `DEFAULT_ADMIN_ROLE` |
| **EthereumVaultConnector** | `0x0C9a3dd6b8F28529d72d7f9cE918D493519EE383` | EIP-1967 slots, `owner()`, `admin()` | both slots `0`; `owner()` and `admin()` revert (`21,989` bytes of code) |

Classification: **aligned baseline** — `docs.euler.finance`: "`FactoryGovernor` is installed as the `upgradeAdmin` of the EVK factory." and "The deployed EVC is immutable"; the Euler forum (Euler Foundation, 2025-11-06): "The signer set will be updated to 6 Euler Labs signers and 2 Foundation Directors, with a 4/8 threshold." The 4-day delay matches `EVAULT_FACTORY_TIMELOCK_MIN_DELAY = 4 days` in the official `evk-periphery` deployment script; the prose docs state no delay.

## 6. Moonwell Lending (Base) — TemporalGovernor 24-Hour Delay, Security Council 3-of-5; Pause Guardian 2-of-4 (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at Base `#57842915` |
| :--- | :--- | :--- | :--- |
| **`Unitroller.admin()`** | `0xfBb21d0380beE3312B33c4353c8936a0F13EF26C` | `0xf851a440` | `TemporalGovernor` `0x8b621804a7637b781e2BbD58e256a591F2dF7d51` (`pendingAdmin() = 0`); `comptrollerImplementation()` = `0x73D8A3bF62aACa6690791E57EBaEE4e1d875d8Fe` |
| **`TemporalGovernor`** | `0x8b621804a7637b781e2BbD58e256a591F2dF7d51` | `proposalDelay()` | `86400`s (`24` h); `owner()` = Safe `0x446342AF4F3bCD374276891C6bb3411bf2F8779E` (`3`-of-`5`); `allTrustedSenders(2)` (Wormhole chain id of Ethereum) = [`0x8769B70ac7c93AF0e75de0D69877709B66d75838`]; `allTrustedSenders(16)` (Moonbeam) = [] |
| **`Unitroller.pauseGuardian()`** | `0xfBb21d0380beE3312B33c4353c8936a0F13EF26C` | `pauseGuardian()` | Safe `0x5B710010586C1b728B047c3E42473c700eeA4026` (`2`-of-`4`, v1.4.1); `1` of its `4` owner addresses is also an owner of the `3`-of-`5` Safe above; `borrowCapGuardian()` = `supplyCapGuardian()` = Safe `0x08eDEbFFaE68970DCf751baa826182b3a4aCFC05` (`2`-of-`4`) |

Classification: TemporalGovernor delay and Security Council **aligned baseline** — Moonwell DAO Constitution: "**Cross-chain Timelock Period**: 24 hours." and "Performing any Emergency Action requires a 3-of-5 approval from the Security Council." Pause guardian **parameter delta** — the same section: "The Security Council has the power to execute any pause functionality, or perform other required actions with no delay ... Performing any Emergency Action requires a 3-of-5 approval from the Security Council." On-chain the Comptroller's pause guardian is a separate 2-of-4 Safe.
Context (not compared, not scored): `permissionlessUnpauseTime() = 2592000`s (`30` days), while the developer docs in `moonwell-contracts-v2` describe a pause blocking proposals "for a period of ten days, until the contract automatically unpauses"; the only trusted sender is the Ethereum MultichainGovernor, while the governance pages still describe proposals "executed on Moonbeam".

## 7. Drift Re-Scans (Part C) — 0 of 3 Drifted

Every scored parameter of the three earliest non-bounty attested protocols, read at its original pinned block (archive pair) and at `#26421541`:

| Protocol (record) | Check | Baseline block | Before | After |
| :--- | :--- | :--- | :--- | :--- |
| f(x) Protocol v2 (`fx-protocol-v2-treasury-admin`) | `hasRole(DEFAULT_ADMIN_ROLE, OpsSafe)` on the 4 ProtocolTreasury proxies (wstETH, WBTC, sfrxETH, weETH) | `26400152` | `true` ×4 | `true` ×4 |
| | `hasRole(DEFAULT_ADMIN_ROLE, EmergencySafe)` on the same 4 | `26400152` | `true` ×4 | `true` ×4 |
| | `hasRole(DEFAULT_ADMIN_ROLE, Timelock)` on the same 4 | `26400152` | `false` ×4 | `false` ×4 |
| | OpsSafe `getThreshold()` / `getOwners().length` | `26400152` | `6` / `9` | `6` / `9` |
| | EmergencySafe `getThreshold()` / `getOwners().length` | `26400152` | `3` / `4` | `3` / `4` |
| | Timelock `getMinDelay()` | `26400152` | `259200` | `259200` |
| ether.fi Liquid / Veda BoringVault (`etherfi-liquid-veda-roles-authority`) | AccountantWithRateProviders `authority()` | `26401070` | RolesAuthority `0x485Bde66Bb668a51f2372E34e45B1c6226798122` | same |
| | RolesAuthority `owner()` | `26401070` | TimelockController `0xD829F278016b90FEc735F9A12Bf8b75E06102C89` | same |
| | TimelockController `getMinDelay()` | `26401070` | `86400` | `86400` |
| Morpho Blue Core (`morpho-blue-singleton-owner`) | `owner()` | `26401070` | `0xcBa28b38103307Ec8dA98377ffF9816C164f9AFa` | same |

All 21 "before" values equal the values recorded in Sprints 2 and 3. Unscored extra: the OpsSafe and EmergencySafe owner sets are identical before and after (Sprint 2 recorded only the counts). Not re-checked: the Morpho Blue "sampled fee/LLTV bounds" named in the Sprint 3 record are not itemized there, so they are outside this comparison.

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-15`). It does not certify protocol-wide immutability, exhaustive authority coverage or exploitability. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to official protocol security teams.
