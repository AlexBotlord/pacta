# Sprint 20 Protocol Commitment Summary — Block `26425374`

- **Ethereum Mainnet pin**: `26425374` (`0x193381e`), canonical block hash `0xfa22e277760f1df7134b0af20499d6305ee4e017219a917a61a78aa76e89382d`, timestamp `2026-11-16 05:04:23 UTC` (`1794805463`); the lower of the two endpoints' `finalized` heads (both `26425374`)
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI). Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs with identical results: `ethereum-rpc.publicnode.com` + `eth.drpc.org`; the paired `eth_getBlockByNumber` header of the pin is logged with the evidence. Drift baselines were re-read at their original Sprint 5 / 6 blocks on `eth.drpc.org` + `gateway.tenderly.co/public/mainnet`.
- **Result**: `18` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `14` aligned baselines, `1` protective delta, `3` parameter deltas. `verifiedCount = 15` (`14` aligned baselines + `1` protective delta). `driftCount = 3` (`3` parameter deltas: the Concrete vault-owner Safe threshold, the infiniFi pause / unpause role admin and the Puffer Community Multisig signer count), the same convention as Sprints 1–19 and `PactaSentinelGuard` (`driftCount != 0` means drift). Separately, the Part C post-snapshot drift re-scans found `0` of `3` previously attested protocols drifted across `15` checks (§7).
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above)

## 1. Concrete — Vault Upgrades Anchored to the Factory; Vault Owner and Manager Is a 1-of-2 Safe

| Contract / Check | Address | Selector | Observation at `#26425374` |
| :--- | :--- | :--- | :--- |
| **`ctDeltaWeETH` vault EIP-1967 admin slot** | `0xB9DC54c8261745CB97070CeFBE3D3d815aee8f20` | `0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103` | `ConcreteFactory` `0x0265d73a8E61F698d8EB0dfeb91Ddce55516844C`, which is also the vault's `factory()`, with `isRegisteredVault(vault) = true`; implementation `0xFB65336D4323BA79d07F7024c81B8B69E1781527`; `name()` = "Concrete Delta WeETH", asset weETH `0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee` |
| **Vault `DEFAULT_ADMIN_ROLE`** | `0xB9DC54c8261745CB97070CeFBE3D3d815aee8f20` | `getRoleMemberCount(bytes32)` | `0` members; every `*_ADMIN` role (vault-manager, allocator, withdrawal-manager, strategy-manager and hook-manager admins) has one member, the `2`-of-`3` Safe `0x70EBF87bA7a1517c204979e51979cfbf693364F9` |
| **Vault owner / `VAULT_MANAGER` Safe** | `0x8F5f1d40243b259cEB7aB44bA421Ff191bCD3381` | `getThreshold()` / `getOwners()` | `1`-of-`2` Safe; it is the vault `owner()`, the only `VAULT_MANAGER` member and the factory's `getFactoryManager()` |

Classification: **mixed** — `2` aligned baselines, `1` parameter delta.
- **aligned**: `docs.concrete.xyz` (architecture): "The factory is the immutable admin of every vault proxy." The vault's EIP-1967 admin slot holds the factory.
- **aligned**: same page: "The default OpenZeppelin DEFAULT_ADMIN_ROLE is intentionally unassigned at the vault." `getRoleMemberCount(0x00) = 0`.
- **parameter delta**: `docs.concrete.xyz` (risks and safety): "Separated roles. Vault operations are split across distinct roles. No single key has full control or can drain a vault." The vault owner (the gate for factory-driven vault upgrades), its only `VAULT_MANAGER` and the factory manager are one Safe whose threshold is `1`: either of its `2` signers acts alone.

Context (not scored): the factory's owner is the `3`-of-`5` Safe `0xdc29BD10CB9000dffBb5aAcD30606c66f07c866C`; the factory is bound to Concrete's tiered Timelock `0x4d575bF3d22c9cd34e4ac19084397d905741d195` (tier delays `172800` / `86400` / `43200`s), under which approving a new vault implementation or migration waits `86400`s; the vault and its strategy are not bound to that timelock. The vault's single strategy (`0xC8EA269d4Dba296f7fBbA812905C1B2EFe5dbE1c`, a multisig strategy) forwards assets to a `3`-of-`5` custody Safe. `managementFee()` and `performanceFee()` read `0`. The documentation describes a newer vault version (with `ROLE_ADMIN` / `PAUSER` roles and an unwind-cost cap) than the one this vault runs; that cap was not compared.

## 2. Cap (cUSD) — 1-Day Timelock Holds Every Upgrade and the Access-Control Admin

| Contract / Check | Address | Selector | Observation at `#26425374` |
| :--- | :--- | :--- | :--- |
| **Cap Timelock `getMinDelay()`** | `0xD8236031d8279d82E615aF2BFab5FC0127A329ab` | `getMinDelay()` | `86400`s (`1` day); `PROPOSER_ROLE`, `EXECUTOR_ROLE` and `CANCELLER_ROLE` held by the Developer multisig `0xb8FC49402dF3ee4f8587268FB89fda4d621a8793` (`3`-of-`5` Safe); the timelock is its own admin |
| **AccessControl `DEFAULT_ADMIN_ROLE`** | `0x7731129a10d51e18cDE607C5C115F26503D2c683` | `getRoleMember(bytes32,uint256)` | `1` member, the Timelock; the Timelock is also the only holder of `grantAccess` / `revokeAccess`; the Developer multisig does not hold `DEFAULT_ADMIN_ROLE` |
| **cUSD upgrade role (`bytes4(0)` on cUSD)** | `0x7731129a10d51e18cDE607C5C115F26503D2c683` | `getRoleMemberCount(bytes32)` | `1` member, the Timelock, for cUSD `0xcCcc62962d17b8914c62D74FfB843d73B2a3cccC` (UUPS, implementation `0xbDaa34082F1a1a3c32190a672bC9dd1b69791b97`); the same single holder for stcUSD, AccessControl, Lender, Delegation, Oracle and FeeAuction |

Classification: **mixed** — `2` aligned baselines, `1` protective delta.
- **aligned**: `docs.cap.app` (access controls): "Critical administrative operations are routed through an OpenZeppelin TimelockController with a 1-day minimum delay (86,400 seconds)."
- **protective delta**: same page: "Roles are managed by the Access Control admin, currently set to Cap's multisig address". On-chain the admin is the Timelock, so the multisig can change roles only through the `1`-day delay.
- **aligned**: `docs.cap.app` (contracts / access controls): "The `bytes4(0)` selector is conventionally used for UUPS upgrade authorization (`_authorizeUpgrade`) across all upgradeable Cap contracts." The cUSD upgrade role has one holder, the Timelock.

Context (not scored): `0x99991c6AAbba5a096f24f250b73580F5179b9999` is the CAP governance token, not cUSD. Pausing cUSD (`pauseProtocol`) is open to the Developer multisig and two other addresses; `unpauseProtocol`, `rescueERC20`, `setWhitelist` and `setInsuranceFund` are held by the Developer multisig directly; the documentation names no holders for these.

## 3. infiniFi (iUSD / siUSD) — 7-Day and 1-Day Timelocks, 4/7 Multisig; Pause Roles Administered Outside GOVERNOR

| Contract / Check | Address | Selector | Observation at `#26425374` |
| :--- | :--- | :--- | :--- |
| **Long Timelock `getMinDelay()`** | `0x3D18480CC32B6AB3B833dCabD80E76CfD41c48a9` | `getMinDelay()` | `604800`s (`7` days); Short Timelock `0x4B174afbeD7b98BA01F50E36109EEE5e6d327c32` `86400`s; the Long Timelock holds `GOVERNOR` on InfiniFiCore `0xF6d48735EcCf12bDC1DF2674b1ce3fcb3bD25490` and owns the Gateway ProxyAdmin `0x21071E0f9D600571Ffe47873e95fffF2FAc9141c`; the only `PROPOSER_ROLE` / `CANCELLER_ROLE` member is the Team Multisig |
| **Team Multisig** | `0x80608f852D152024c0a2087b16939235fEc2400c` | `getThreshold()` / `getOwners()` | `4`-of-`7` Safe (v1.4.1), no modules, no guard |
| **`getRoleAdmin(UNPAUSE)` / `getRoleAdmin(PAUSE)`** | `0xF6d48735EcCf12bDC1DF2674b1ce3fcb3bD25490` | `getRoleAdmin(bytes32)` | both `keccak256("MINOR_ROLES_MANAGER")` (`0x9849206c…6512`), not `GOVERNOR`; `MINOR_ROLES_MANAGER` members: the Team Multisig and the Long Timelock |

Classification: **mixed** — `2` aligned baselines, `1` parameter delta.
- **aligned**: `docs.infinifi.xyz` (audits): "Timelock Policy / 1 day timelock / 7 day timelock".
- **aligned**: same page: "Our Multisig is a 4/7 multisig and may be found here" (the link resolves to `0x8060…400c`).
- **parameter delta**: `docs.infinifi.xyz` (roles documentation) table: "PAUSE / Pause protocol functions / GOVERNOR / UNPAUSE / Unpause functions / GOVERNOR". On-chain both roles are administered by `MINOR_ROLES_MANAGER`, which the Team Multisig holds directly, so pause and unpause rights can be granted or revoked without the `7`-day `GOVERNOR` timelock.

Context (not scored): `GOVERNOR` has a second member, `FluidRewardsClaimer` `0xD0ec80032C0da717BD78B9569321D9069365241E` (verified source; it calls only a fixed rewards target), so not every `GOVERNOR` holder is a timelock. iUSD `0x48f9e38f3070AD8945DFEae3FA70987722E3D89c` and siUSD are not proxies.

## 4. stake.link (stLINK) — 48-Hour GovernanceTimelock, 6-of-8 Multisig, 15% / 5% Operator-Strategy Fees

| Contract / Check | Address | Selector | Observation at `#26425374` |
| :--- | :--- | :--- | :--- |
| **GovernanceTimelock `getMinDelay()`** | `0xb72d8F5213b3E52FAf13Aa074b03C4788e78349F` | `getMinDelay()` | `172800`s (`48` hours); `owner()` of StakingPool / stLINK `0xb8b295df2cd735b15BE5Eb419517Aa626fc43cD5`, PriorityPool, WithdrawalPool, FundFlowController, RebaseController, OperatorVCS and CommunityVCS (UUPS proxies); `PROPOSER_ROLE` and `CANCELLER_ROLE` held by the multisig; the timelock is its own admin |
| **Multisig** | `0xB351EC0FEaF4B99FdFD36b484d9EC90D0422493D` | `getThreshold()` / `getOwners()` | `6`-of-`8` Safe (v1.3.0), no modules, no guard |
| **OperatorVCS `getFees()`** | `0x4852e48215A4785eE99B640CACED5378Cc39D2A4` | `getFees()` | one fee, `1500` bps to the stLINK rewards pool `0x8753C00D1a94D04A01b931830011d882A3F8Cc72`; `operatorRewardPercentage() = 500`; CommunityVCS `0xAc12290b097f6893322F5430627e472131fBC1B5` `getFees()` = `1000` bps to the same pool |

Classification: **aligned baseline** (3 records).
- `docs.stake.link` (security and audits): "48-hour timelock. Actions executed by the multisig go through the GovernanceTimelock , which gives the community time to review pending changes."
- Same page: "6-of-8 multisig. Critical operations and treasury funds are controlled by a Gnosis Safe . Every transaction needs six of eight signers."
- `docs.stake.link` (FAQ) fee table: node operators `5%` / `0%`, SDL stakers `15%` / `10%` for the Node Operator / Community pool strategies.

Context (not scored): `0xA95C5ebB86E0dE73B4fB8c47A45B792CFeA28C23` is the SDL governance token (`owner()` = `0x0`), not stLINK. The RebaseController's `emergencyPauser()` is an externally owned account that can only close the pool; reopening needs the owner (the timelock).

## 5. Frax Ether (frxETH / sfrxETH) — Minter Owned by the Comptroller; 3-of-5 Lockbox Safe; 24-Hour Upgrade Timelock (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26425374` |
| :--- | :--- | :--- | :--- |
| **frxETHMinter `owner()`** | `0xbAFA44EFE7901E04E39Dad13167D089C559c1138` | `owner()` | Comptroller `0x8306300ffd616049FD7e4b0354a64Da835c1A81C` (`4`-of-`7` Safe), `nominatedOwner() = 0`; not upgradeable; still an authorised frxETH minter, alongside FraxEtherMinter V2 `0x7Bc6bad540453360F744666D625fec0ee1320cA3` (whose `timelockAddress()` and `operatorAddress()` are also the Comptroller) |
| **Ethereum multisig** | `0xB1748C79709f4Ba2Dd82834B8c82D4a505003f27` | `getThreshold()` / `getOwners()` | `3`-of-`5` Safe (v1.3.0); `owner()` of the frxETH lockbox `0x1c1649A38f4A3c5A0c4a24070f688C525AB7D6E6` and the sfrxETH lockbox `0xbBc424e58ED38dd911309611ae2d7A23014Bd960` |
| **Upgrade Timelock `delay()`** | `0xb898Ad2976b4d8f2E21521C9db16b7497825E503` | `delay()` | `86400`s (`MINIMUM_DELAY() = 7200`); `admin()` = `4`-of-`7` Safe `0xfFFffF4F3baC444b2C0ecf2A1840d018bE783937`; owner of ProxyAdmin `0x223a681fc5c5522c85C96157c0efA18cd6c5405c`, the EIP-1967 admin of both lockboxes |

Classification: **aligned baseline** (3 records).
- `docs.frax.com` (frxETH addresses): "Multisigs / Chain / Name / Contract / Ethereum / Comptroller / 0x8306300ffd616049FD7e4b0354a64Da835c1A81C".
- `docs.frax.com` (crosschain addresses, page source): "Each multisig below is the LayerZero delegate of the chain's OFTs and lockboxes, and their owner, except for the Ethereum frxUSD lockbox …" and "| Ethereum | … | 3 of 5 |" for `0xB1748C79709f4Ba2Dd82834B8c82D4a505003f27`.
- `docs.frax.com` (crosschain addresses): "The Timelock enforces a 24-hour delay on upgrades. The Timelock admin is a 4-of-7 Safe, which also owns the Ethereum frxUSD lockbox."

Context (not scored): the frxETH token's `owner()` / `timelock_address()` is FraxGovernanceTimelock `0x8412ebf45bAC1B340BbE8F318b928C466c4E39CA` (`delay() = 172800`s), whose `admin()` is the `3`-of-`5` Ethereum multisig; the documentation does not describe that timelock. The v1 minter's `withholdRatio()` is `980000` (98% of deposits withheld from validator deposits). sfrxETH is not upgradeable.

## 6. Puffer Finance (pufETH) — 7-Day Timelock; Community Multisig Is 3-of-7, Not 3-of-6 (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26425374` |
| :--- | :--- | :--- | :--- |
| **Timelock `delay()`** | `0x3C28B7c7Ba1A1f55c9Ce66b263B33B204f2126eA` | `delay()` | `604801`s (`MINIMUM_DELAY() = 604800`; the verified source accepts only delays above the minimum); `ACCESS_MANAGER()` = `0x8c1686069474410E6243425f4a10177a94EBEE11`, the `authority()` of PufferVault `0xD9A442856C234a39a81a089C06451EBAa4306a72` (UUPS, implementation `0x3b2fdFdEFE919dBcCE0bc5ac426097d5523B8AFA`), where vault and PufferModuleManager `upgradeToAndCall` map to role `0`, held by the Timelock |
| **Community Multisig** | `0x446d4d6b26815f9bA78B5D454E303315D586Cb2a` | `getThreshold()` / `getOwners()` | `3`-of-`7` Safe (v1.3.0); equals the Timelock's `COMMUNITY_MULTISIG()`; holds AccessManager role `1` (upgrader) with execution delay `0` |
| **Operations Multisig** | `0xC0896ab1A8cae8c2C1d27d011eb955Cca955580d` | `getThreshold()` / `getOwners()` | `3`-of-`6` Safe (v1.3.0); equals the Timelock's `OPERATIONS_MULTISIG()`; holds roles `22` and `77` (the vault's withdrawal-limit and exit-fee setters), not roles `0` or `1` |

Classification: **mixed** — `2` aligned baselines, `1` parameter delta.
- **aligned**: `docs.puffer.fi` (multisig): "The timelock enforces that important function calls and upgrades must go through a 7-day delay before being executed."
- **parameter delta**: same page: "Puffer's Community Multisig is a 3-of-6 multisig composed of reputable and aligned Ethereum community members and auditing firms. The community multisig can bypass the timelock delay and has veto rights over actions initiated by the operations multisig." On-chain the Safe has `7` owners with threshold `3`.
- **aligned**: same page: "Puffer's Operations Multisig is a 3-of-6 multisig operated by the team."

Context (not scored): the published RPC-observed record's label for the vault ("PufferVaultV2") predates the current verified implementation (PufferVaultV5). The Timelock's `pauserMultisig()` is a `1`-of-`9` Safe; `6` of the `7` Community Multisig owners also sign it.

## 7. Drift Re-Scans (Part C) — 0 of 3 Drifted

Every scored parameter of three earlier attested protocols, read at its original pinned block (archive pair) and at `#26425374` (`audits/sprint-20/drift-rescan-26425374.json`):

| Protocol (record) | Check | Baseline block | Before | After |
| :--- | :--- | :--- | :--- | :--- |
| MetaMorpho Re7 (`metamorpho-re7-weth-guardian-parity`) | Re7 WETH `owner()` | `26401405` | `0xE86399fE6d7007FdEcb08A2ee1434Ee677a04433` | same |
| | owner Safe `getThreshold()` / `getOwners().length` | `26401405` | `2` / `4` | `2` / `4` |
| | Re7 WETH `timelock()` | `26401405` | `259200` | `259200` |
| | Re7 WETH `guardian()` / `pendingGuardian()` | `26401405` | `0x0` / `(0x0, 0)` | `0x0` / `(0x0, 0)` |
| | Re7 USDT (peer) `guardian()` | `26401405` | `0x2F80ba89362f86a9acC71BFfE5EcF4997F52BDd4` | same |
| Liquity V2 (`liquity-v2-bold-immutability`) | BOLD `owner()`, Governance `owner()` | `26401540` | `0x0` / `0x0` | `0x0` / `0x0` |
| | CollateralRegistry EIP-1967 implementation slot | `26401540` | `0x0` | `0x0` |
| Maple Finance (`maple-v2-syrup-ppm-admin`) | PoolPermissionManager EIP-1967 admin slot | `26401540` | Maple DAO Safe `0xd6d4Bcde6c816F17889f1Dd3000aF0261B03a196` | same |
| | Maple DAO Safe `getThreshold()` / `getOwners().length` | `26401540` | `4` / `7` | `4` / `7` |
| | Globals `governor()` | `26401540` | GovernorTimelock `0x2eFFf88747EB5a3FF00d4d8d0f0800E306C0426b` | same |
| | GovernorTimelock `defaultTimelockParameters()` delay | `26401540` | `259200` | `259200` |

All `15` "before" values equal the values recorded in Sprints 5 and 6. Unscored extras, all unchanged: the two Safes' owner sets, the Re7 WETH `curator()` (`0x0`), BOLD's empty EIP-1967 implementation slot and code size, the PoolPermissionManager implementation slot, and the GovernorTimelock execution window (`172800`s) and `MIN_DELAY()` (`86400`s).

Correction to the Sprint 6 record text (the attested value is unaffected): the Maple record writes "GovernorTimelock … getMinDelay = 259200s". This GovernorTimelock has no `getMinDelay()` (the call reverts at both blocks); the `259200`s delay is the first word of `defaultTimelockParameters()`, which this re-scan reads.

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-16`). It does not certify protocol-wide immutability, exhaustive authority coverage or exploitability. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to the affected protocols. Pacta by Fractal Neurons publishes these records as documentation-comparison evidence, not as audits or investment advice.
