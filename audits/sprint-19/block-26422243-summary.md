# Sprint 19 Protocol Commitment Summary — Block `26422243`

- **Ethereum Mainnet pin**: `26422243` (`0x1932be3`), canonical block hash `0xbbe80f9ef9966a9d04cea23db216847f8c8fcc8d66f87c215dc7f712f0743410`, timestamp `2026-11-15 18:37:11 UTC` (`1794767831`)
- **Base Mainnet pin** (Aave V3 and Compound V3 records): `57886975` (`0x37348ff`), canonical block hash `0xf88ef5af0e0555ca6b7e28b325f5057163cb52d6ced0f509507613423c6ad277`, timestamp `2026-11-15 18:36:10 UTC` (`1794767770`)
- **Scanner**: Pacta Protocol Commitments DRI. Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: Ethereum `ethereum-rpc.publicnode.com` + `eth.drpc.org`; Base `mainnet.base.org` + `base.drpc.org`. Drift baselines were re-read at their original Sprint 4 / 5 blocks on `eth.drpc.org` + `gateway.tenderly.co/public/mainnet`.
- **Result**: `13` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `11` aligned baselines, `1` protective delta, `1` parameter delta. `verifiedCount = 12` (`11` aligned baselines + `1` protective delta). `driftCount = 1` (`1` parameter delta: the Rocket Pool security council leave time), the same convention as Sprints 1–18 and `PactaSentinelGuard` (`driftCount != 0` means drift). Separately, the Part C post-snapshot drift re-scans found `0` of `3` previously attested protocols drifted across `17` checks (§7).
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above)

## 1. Aave V3 (Base) — Level-1 Payloads Wait 1 Day; EMERGENCY_ADMIN Is the 4-of-7 Protocol Guardian

| Contract / Check | Address | Selector | Observation at Base `#57886975` |
| :--- | :--- | :--- | :--- |
| **`PayloadsController.getExecutorSettingsByAccessControl(1)`** | `0x2DC219E716793fb4b21548C0f009Ba3Af753ab01` | `getExecutorSettingsByAccessControl(uint8)` | executor `0x9390B1735def18560c509E2d0bc090E9d6BA257a` (ExecutorLvl1), delay `86400`s (`1` day); `MIN_EXECUTION_DELAY() = 86400`, `MAX_EXECUTION_DELAY() = 864000`, `GRACE_PERIOD() = 604800`; `MESSAGE_ORIGINATOR()` = Ethereum Governance V3 `0x9AEE0B04504CeF83A65AC3f0e838D0593BCb2BC7`, `ORIGIN_CHAIN_ID() = 1`; access level `2` has no executor on Base; `124` payloads created |
| **Protocol Guardian Safe** | `0x56C1a4b54921DEA9A344967a8693C7E661D72968` | `getThreshold()` / `getOwners()` | `4`-of-`7` Safe (v1.3.0); `ACLManager` (`0x43955b0899Ab7232E3a454cf84AedD22Ad46FD33`) `hasRole(EMERGENCY_ADMIN, Safe) = true`, `hasRole(POOL_ADMIN, Safe) = false` |
| **Upgrade / admin path** | `0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D` | `owner()` / `getACLAdmin()` | both ExecutorLvl1, whose `owner()` is the PayloadsController; ExecutorLvl1 holds `DEFAULT_ADMIN_ROLE` and `POOL_ADMIN`; the PayloadsController proxy admin `0xc85b1E333aecc99340b2320493Fe2d22b8734795` and the CrossChainController `0x529467C76f234F2bD359d7ecF7c660A2846b04e2` are owned by ExecutorLvl1 |

Classification: **aligned baseline** (2 records).
- `aave.com/docs` (governance): "compared with the 3-day vote and 1-day timelock of a Level 1 proposal". On Base, Level-1 payloads execute through ExecutorLvl1 only after the `86400`s delay; the verified PayloadsController requires `block.timestamp > queuedAt + delay`.
- Same page: "The Protocol Emergency Guardian is a 4 of 7 multi-signature wallet consisting of the following signers:" and "The Protocol Emergency Guardian holds the EMERGENCY_ ADMIN". The Base Safe is `4`-of-`7` with the `7` listed signers and holds `EMERGENCY_ADMIN`; per the ACL Manager docs, "Holders of this role can pause and unpause the pool or an individual reserve."

Context (not scored): the PayloadsController `guardian()` is the `5`-of-`9` Governance Guardian Safe `0x360c0a69Ed2912351227a0b745f890CB2eBDbcFe`; the docs describe a `5`-of-`9` Governance Emergency Guardian, but `4` of the `9` Base owners do not appear on the docs page (the page does not name a network for that list). Risk-steward and asset-listing roles were checked only for the address-book holders.

## 2. Compound V3 (Base) — Ethereum Timelock Governs Both Base Markets Through a 1-Day Local Timelock

| Contract / Check | Address | Selector | Observation at Base `#57886975` |
| :--- | :--- | :--- | :--- |
| **`BridgeReceiver.govTimelock()`** | `0x18281dfC4d00905DA1aaA6731414EABa843c468A` | `govTimelock()` | Ethereum Timelock `0x6d903f6003cca6255D85CcA4D3B5E5146dC33925` (`delay() = 172800`s on Ethereum); `localTimelock()` = `0xCC3E7c85Bb0EE4f09380e041fee95a0caeDD4a02`, messenger `0x4200000000000000000000000000000000000007`, `proposalCount() = 71`; the verified receiver rejects any message whose root sender is not `govTimelock` and queues every call in the local timelock |
| **Local Timelock** | `0xCC3E7c85Bb0EE4f09380e041fee95a0caeDD4a02` | `delay()` | `86400`s (`MINIMUM_DELAY() = 43200`, `MAXIMUM_DELAY() = 2592000`); `admin()` = the BridgeReceiver, `pendingAdmin() = 0` |
| **Comet markets** | `0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf` (`cUSDbCv3`), `0xb125E6687d4313864e53df431d5425969c15Eb2F` (`cUSDCv3`) | `governor()` / `pauseGuardian()` | both: governor = the local timelock, pause guardian = Safe `0x3cb4653F3B45F448D9100b118B75a1503281d2ee`; EIP-1967 admin `CometProxyAdmin` `0xbdE8F31D2DdDA895264e27DD990faB3DC87b372d`, whose `owner()` is the local timelock; Configurator `0x45939657d1CA34A8FA39A924B71D28Fe8431e581` `governor()` = the local timelock; no market is paused |
| **Pause Guardian Safe** | `0x3cb4653F3B45F448D9100b118B75a1503281d2ee` | `getThreshold()` / `getOwners()` | `5`-of-`9` Safe (v1.3.0) whose `9` owners equal, in the same order, those of the Ethereum Community Multi-Sig `0xbbf3f1421D886E9b2c5D716B5192aC998af2012c` (`5`-of-`9`) |

Classification: **aligned baseline** (2 records).
- `docs.compound.finance` (governance): "The Timelock on Mainnet is the administrator of all community sanctioned instances of Compound III." and "Local Timelocks have an additional delay before Comet admin functions can be called via proposal execution."
- Same page: "COMP token-holders designate the Pause Guardian address, which is held by the Community Multi-Sig" and "The only addresses that are allowed to call this function are the Governor and the Pause Guardian." The Base pause guardian is a separate Safe with the Community Multi-Sig's threshold and owner set.

Scope note: the address in the Sprint 19 brief (`0x9c4e…58bf`) is the bridged-USDC market (`symbol() = cUSDbCv3`, base token USDbC `0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA`); the native-USDC market `cUSDCv3` is `0xb125…Eb2F`. Both share the governor, pause guardian, ProxyAdmin and Configurator above.

## 3. Liquid Collective (LsETH) — 4-of-7 Administrative Multisig; 10% Service Fee

| Contract / Check | Address | Selector | Observation at `#26422243` |
| :--- | :--- | :--- | :--- |
| **River (LsETH) EIP-1967 admin slot** | `0x8c1BEd5b9a0928467c9B1341Da1D7BD5e10b6549` | `0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103` | Firewall `0x3A5b4db174a3CC17d8cE40C5B04272737195151b`, whose `getAdmin()` is Safe `0x8EE3fC0Bcd7B57429203751C5bE5fdf1AB8409f3` (`4`-of-`7`, v1.3.0); implementation `RiverV1` `0x0056f9ed62dAa4dc3F972340C92326AcCddd1a9D` (`version() = 1.3.0`); pause slot `0` (not paused) |
| **River `getAdmin()`** | `0x8c1BEd5b9a0928467c9B1341Da1D7BD5e10b6549` | `getAdmin()` | Firewall `0xd745A68c705F5aa75DFf528540678288ed2aD9eE`, whose `getAdmin()` is Safe `0xE3208Aa9d1186c1D1C8A5b76E794b2B68E6cb3a5` (`4`-of-`7`, the same `7` owners); `getPendingAdmin() = 0` |
| **Firewall executor** | `0xDE55C9dc78f985fE1502484Cb98EBfAB66A56B62` | `executorCanCall(bytes4)` | `2`-of-`3` Safe; on the upgrade Firewall it may call `pause()` but not `unpause()` or `upgradeTo(address)`; on the governance Firewall none of the three |
| **`River.getGlobalFee()`** | `0x8c1BEd5b9a0928467c9B1341Da1D7BD5e10b6549` | `getGlobalFee()` | `1000` basis points (the verified source divides by `10000`): `10.0`% |

Classification: **aligned baseline** (2 records).
- `docs.liquidcollective.io` (ETH FAQs): "An administrative multisig is made up of a variety of Liquid Collective ecosystem participants." Upgrades and admin setters of River go through Firewalls administered by `4`-of-`7` Safes.
- Same page: "The Liquid Collective protocol charges a service fee set at 10.0% of network rewards."

Context (not scored): each Firewall's `getAdmin()` is a Safe directly, and neither Safe has a module enabled, so upgrades, admin setters and unpause execute without a delay; the docs give no threshold or delay. The deployments page names v1.2.1 while River reports `1.3.0`.

## 4. Ethena USDtb — Single Admin, No Timelock (Anchorage); PSM Owned by a 24-Hour Timelock

| Contract / Check | Address | Selector | Observation at `#26422243` |
| :--- | :--- | :--- | :--- |
| **`USDtb.owner()`** | `0xC139190F447e929f090Edeb554D95AbB8b18aC1C` | `owner()` | `0xd93826BB299765c87D13AeBa2A7E5d9B27A03956` (no code), which also holds `DEFAULT_ADMIN_ROLE` and owns the ProxyAdmin `0x3C405F68d5C6eCE868e5646cAC926679839aCd68`; implementation `AnchorageTokenUSDtb` `0x9D6d77a21702b9AFcF924983fbFB84AAAAe79589`; `MINTER_BURNER_ROLE`, `BLOCKLISTER_ROLE` and `PAUSER_ROLE` are each held by one address without code; the former Ethena admin Safe `0xe897D8620D5EbA2C8ecAAF0aDa191a23230aB8Ec` no longer holds `DEFAULT_ADMIN_ROLE`; `paused() = false`; supply `318,164,251.46` USDtb |
| **`USDtb PSM.owner()`** | `0x73E35C5c35A274E34AdE6EB13cC7f62aEE323728` | `owner()` | `EthenaTimelockController` `0xE8Dc0Fab349EA169283C48Ccfd09d797E6DB7c94` (`getMinDelay() = 86400`s), which also holds the PSM `DEFAULT_ADMIN_ROLE` (the Dev multisig does not); `asset()` = USDtb, `isSwapEnabled() = true` |
| **Dev multisig** | `0x3B0AAf6e6fCd4a7cEEf8c92C32DFeA9E64dC1862` | `getThreshold()` / `getOwners()` | `5`-of-`10` Safe (v1.3.0) holding `PROPOSER_ROLE`, `CANCELLER_ROLE` and `EXECUTOR_ROLE` on the timelock |

Classification:
- **aligned baseline** — the USDtb token: first-party `ethena-labs/ethena-usdtb-contest` README: "An upgradeable ERC20 with mint and burn functionality and various transfer states that is controlled by a single admin address." and "The admin address can change the state at any time, without a timelock." `docs.ethena.fi`: "As of October 2025, USDtb is issued by Anchorage Digital Bank." On-chain the token is administered by one address with no timelock, and the implementation is Anchorage's.
- **protective delta** — the PSM: `docs.ethena.fi` key addresses list the Dev multisig ("5/11 signers.") as "Owner of Ethena's deployed mainnet smart contracts & able to modify contract parameters." On-chain the PSM owner is a timelock with a `24`-hour minimum delay on scheduled operations, for which the Dev multisig is a proposer.

Context (not scored): the timelock also lets the Dev multisig execute a whitelist of PSM selectors immediately (limit and fee setters, adding and disabling benefactors, disabling swaps or collateral). Custodian changes, `rescueFunds`, role grants and peg changes are not whitelisted and wait `24` hours. The Dev multisig has `10` owners at this block versus the documented `5/11`. Whether the USDtb admin and role addresses are custodial (MPC / HSM) keys cannot be told from chain state.

## 5. Pendle Finance V2 — 80% of Swap Fees to the Treasury, 20% to LPs; 5% YT Yield Fee (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26422243` |
| :--- | :--- | :--- | :--- |
| **`PendleMarketFactory.reserveFeePercent()`** | `0x6d247b1c044fA1E22e6B04fA9F71Baf99EB29A9f` | `reserveFeePercent()` | `80` (`maxReserveFeePercent() = 100`); `treasury()` = `0x8270400d528c34e1596EF367eeDEc99080A1b592`; `yieldContractFactory()` = `0x3E6EBa46AbC5ab18ED95F6667d8B2fd4020E4637`; `owner()` = PendleGovernanceProxy `0x2aD631F72fB16d91c4953A7f4260A97C2fE2f31e`, `pendingOwner() = 0`; EIP-1967 proxy (implementation `0xE7a7477c636EbC2eD7C1968b5Fac5eaF29Ff6C0C`, admin ProxyAdmin `0xA28c08f165116587D4F3E708743B4dEe155c5E64`) |
| **`PendleYieldContractFactory.interestFeeRate()`** | `0x3E6EBa46AbC5ab18ED95F6667d8B2fd4020E4637` | `interestFeeRate()` | `50000000000000000` (`5`%, `1e18` = `100`%); `rewardFeeRate()` the same; maxima `200000000000000000` (`20`%); `owner()` = Safe `0x8119EC16F0573B7dAc7C0CB94EB504FB32456ee1` |
| **Governance** | `0x8119EC16F0573B7dAc7C0CB94EB504FB32456ee1` | `getThreshold()` / `getOwners()` | `3`-of-`5` Safe (v1.4.1): owner of the ProxyAdmin and of the yield contract factory, and `DEFAULT_ADMIN_ROLE` on the PendleGovernanceProxy; `GUARDIAN` (pause) is held by `6` addresses without code |

Classification: **aligned baseline** (2 records).
- `docs.pendle.finance` (fees): "20% of all swap fees are given to LP providers of the pool as yield." In the verified market math the reserve share `reserveFeePercent / 100` of each swap fee goes to the treasury, so `80` leaves `20`% to LPs.
- Same page: "Pendle collects a 5% fee from all yield accrued (including points) by all YT in existence"; the live factory charges `5`%.

Context (not scored): the 3-of-5 Safe acts without a delay (through the GovernanceProxy and the ProxyAdmin, both read above). A `TimelockController` `0x68d8D192dF476bC01895E16b0ED3945673d777AC` (`getMinDelay() = 172800`s) exists, but neither the market factory nor the yield contract factory is behind it (their admin and owners are read above). The docs make no multisig or timelock claim. The previous RPC-observed record read `VotingEscrowPendleMainchain` (`0x4f30A9D41B80ecC5B94306AB4364951AE3170210`, `owner()` = the same Safe), which Pendle's deployment file now lists as deprecated.

## 6. Rocket Pool (rETH) — 1-Week Upgrade Delay and 51% oDAO Quorum; Security Council Leave Time 28 Days (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26422243` |
| :--- | :--- | :--- | :--- |
| **`RocketDAOProtocolSettingsSecurity.getUpgradeDelay()`** | `0xC9D771AaF504F33bB3C8a7E67eA9f1881F837cFf` | `getUpgradeDelay()` | `604800`s (`1` week); `getUpgradeVetoQuorum() = 0.33e18`, `getQuorum() = 0.51e18`, `getVoteTime() = 1209600`, `getExecuteTime() = 2419200`; the address is `RocketStorage.getAddress(keccak256("contract.address" ‖ "rocketDAOProtocolSettingsSecurity"))` |
| **`RocketDAONodeTrustedSettingsMembers.getQuorum()`** | `0xdA1AB39e62E0A5297AF44C7064E501b0613f0D01` | `getQuorum()` | `0.51e18` (`51`%); `RocketDAONodeTrusted.getMemberCount() = 9` |
| **`RocketDAOProtocolSettingsSecurity.getLeaveTime()`** | `0xC9D771AaF504F33bB3C8a7E67eA9f1881F837cFf` | `getLeaveTime()` | `2419200`s (`28` days) |
| **`RocketStorage`** | `0x1d8f8f00cfa6758d7bE78336684788Fb0ee0Fa46` | `getDeployedStatus()` / `getGuardian()` | `true` (the guardian can no longer write storage); guardian `0x0cCF14983364A7735d369879603930Afe10df21e` (no code); both DAO bootstrap modes disabled; security council (`0x84aE6D61Df5c6ba7196b5C76Bcb112B8a689aD37`) `getMemberCount() = 1`: Safe `0x6C565aF34f15dE064b56afEdF7B0F59C15bB20FE` (`2`-of-`3`, v1.4.1); `RocketDAONodeTrustedUpgrade` (`0x9290AA076a2F1418a4E414E3D83AE03cA8E1ad10`) `getTotal() = 2` |

Classification:
- **aligned baseline** — `rpips.rocketpool.net` RPIP-60: upgrades wait for `upgrade_delay` "(initially set to 1 week)"; on-chain `604800`s.
- **aligned baseline** — `docs.rocketpool.net` (oDAO proposals): "it is currently set to at least **51%** of the total member pool."; on-chain `0.51e18` with `9` members.
- **parameter delta** — RPIP-33 parameter table, `members.leave.time`: "How long a member must give notice for before manually leaving the security council" with the bound "< 14 days". On-chain the notice period is `2419200`s (`28` days), outside the documented bound; no later RPIP changes this parameter.

Context (not scored): `docs.rocketpool.net` (pDAO) says security council members "have the ability to propose and execute changes without delay"; the council currently has one member, a `2`-of-`3` Safe, so its `51`% quorum and the `33`% upgrade veto both rest on that Safe.

## 7. Drift Re-Scans (Part C) — 0 of 3 Drifted

Every scored parameter of the three next-oldest non-bounty attested protocols, read at its original pinned block (archive pair) and at `#26422243` (`audits/sprint-19/drift-rescan-26422243.json`):

| Protocol (record) | Check | Baseline block | Before | After |
| :--- | :--- | :--- | :--- | :--- |
| Convex Finance (`convex-booster-governance-chain`) | Booster `owner()` | `26401312` | `0x3cE6408F923326f81A7D7929952947748180f1E6` | same |
| | `0x3cE6…f1E6.owner()` | `26401312` | `0x256e1bbA846611C37CF89844a02435E6C098b86D` | same |
| | `0x256e…b86D.owner()` | `26401312` | DAO Multisig `0xa3C5A1e09150B75ff251c1a7815A07182c3de2FB` | same |
| | Booster `feeManager()` | `26401312` | DAO Multisig | same |
| | DAO Multisig `getThreshold()` / `getOwners().length` | `26401312` | `3` / `5` | `3` / `5` |
| Mellow Protocol / Lido Earn (`mellow-lido-earn-curator-quorum`) | Curator Safe `getThreshold()` / `getOwners().length` | `26401312` | `3` / `5` | `3` / `5` |
| | `hasRole(DEFAULT_ADMIN_ROLE, Lazy Vault Admin Safe)` on earnETH and earnUSD | `26401312` | `true` ×2 | `true` ×2 |
| | Lazy Vault Admin Safe `getThreshold()` / `getOwners().length` | `26401312` | `5` / `8` | `5` / `8` |
| | Lazy Vault Admin Timelock `getMinDelay()` | `26401312` | `0` | `0` |
| Fluid / Instadapp (`fluid-instadapp-vault-factory-auth`) | VaultFactory `isVaultAuth(vault, Team Multisig)` for Vaults 76, 110, 111, 144 | `26401405` | `true` ×4 | `true` ×4 |

All `17` "before" values equal the values recorded in Sprints 4 and 5. Unscored extras: the Convex DAO Multisig owner set is identical before and after; all `5` Curator Safe owners are owners of the Lazy Vault Admin Safe before and after.

Correction to the Sprint 5 summary text (the attested Sprint 5 record scores `isVaultAuth` only and is unaffected): the Fluid Team Multisig `0x4F6F977aCDD1177DCD81aB83074855EcB9C2D49e` is described there as a "3-of-5 Gnosis Safe". It is an Avocado Multisig: `getThreshold()` reverts, and `requiredSigners() = 6`, `signersCount() = 12` both at the Sprint 5 block and at `#26422243` (unchanged).

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-15`). It does not certify protocol-wide immutability, exhaustive authority coverage or exploitability. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to the affected protocols.
