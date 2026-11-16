# Sprint 21 Protocol Commitment Summary — Block `26427612`

- **Ethereum Mainnet pin**: `26427612` (`0x19340dc`), canonical block hash `0x1c5ef52eb0b586e49da2a11dc9f905cae4125008dc814d6781f53a142f6555ac`, timestamp `2026-11-16 12:32:23 UTC` (`1794832343`); the lower of the two endpoints' `finalized` heads (both `26427612`)
- **Base Mainnet pin**: `58203774` (`0x3781e7e`), canonical block hash `0x619b45ca763563ff11fc3246da1d039a7d0ab2780bedff6cb0428c9290a2cb10`, timestamp `2026-11-16 12:12:10 UTC` (`1794831130`); the lower of the two endpoints' `finalized` heads (both `58203774`)
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI). Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: `ethereum-rpc.publicnode.com` + `eth.drpc.org` (Ethereum) and `mainnet.base.org` + `base.drpc.org` (Base); the paired `eth_getBlockByNumber` header of each pin is logged with the evidence. Drift baselines were re-read at their original Sprint 4 / 9 blocks on `eth.drpc.org` + `gateway.tenderly.co/public/mainnet`.
- **Result**: `14` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `12` aligned baselines, `1` protective delta, `1` parameter delta. `verifiedCount = 13` (`12` aligned baselines + `1` protective delta). `driftCount = 1` (`1` parameter delta: the Aerodrome Voter's emergency council and epoch governor), the same convention as Sprints 1–20 and `PactaSentinelGuard` (`driftCount != 0` means drift). Separately, the Part C post-snapshot drift re-scans found `0` of `3` previously attested protocols drifted across `19` checks (§7).
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); the two Aerodrome records are read at the Base pin.

## 1. Coinbase Wrapped Staked ETH (cbETH) — Proxy Admin Separate from the Owner; Oracle Is the Rate-Limited ExchangeRateUpdater

| Contract / Check | Address | Selector | Observation at `#26427612` |
| :--- | :--- | :--- | :--- |
| **cbETH `FiatTokenProxy` admin slot** | `0xBe9895146f7AF43049ca1c1AE358B0541Ea49704` | `0x10d6a54a4754c8869d6886b5f5d7fbfa5b4522237ea5c60d11bc4e7a1ff9390b` | `0xEeE4Ac8A22a6b310c53d59a7d59b3E0336C19577` (also `admin()`), an externally owned account; implementation `StakedTokenV1` `0x31724cA0C982A31fbb5C57f4217AB585271fc9a5` (Sourcify exact match); the EIP-1967 implementation slot is empty (centre-tokens proxy layout) |
| **cbETH roles** | `0xBe9895146f7AF43049ca1c1AE358B0541Ea49704` | `owner()` / `pauser()` / `blacklister()` / `masterMinter()` | owner `0x4b8741C89ABFf2562e854899E24d67A36406eA03`, pauser `0x9596EAE1744997161ac094252e5020E9314BDCc2`, blacklister `0xBE3c68821D585Cf1552214897a1c091014B1EB0a`, masterMinter `0x7Dd4aa646b2e2850f9D809F9299E8E87AC97b77a` — four distinct externally owned accounts, none of them the proxy admin; `paused() = false` |
| **cbETH `oracle()`** | `0xBe9895146f7AF43049ca1c1AE358B0541Ea49704` | `oracle()` | `ExchangeRateUpdater` `0x9b37180d847B27ADC13C2277299045C1237Ae281` (Sourcify exact match, `6301` bytes), `owner()` = externally owned account `0xA57aFe0Ba93f6854ed1DCd58dCE301E10B15D1D6` |

Classification: **aligned baseline** (2 records).
- `github.com/coinbase/wrapped-tokens-os` (README): "The contract has an Owner, who can change the owner, pauser, blacklister, masterMinter, or oracle addresses. The owner can not change the proxyOwner address." The proxy admin (`proxyOwner`) and the token `owner()` are different addresses.
- Same README: "The wrapped staked tokens inherit from Centre's fiat token contract and add an oracle role that can set an exchangeRate." and "we'll utilize a seperate rate limited exchange rate updater contract to minimize operational load." `oracle()` is that updater contract.

Context (not scored): every cbETH role holder and the proxy admin is an externally owned account, as the README's design (an owner role, a "masterMinter cold key") implies; key custody is not observable on chain. The README describes "A proxy contract which is an exact duplicate of the proxy contract used be centre-tokens." (wording as published).

## 2. SSV Network — DAO Governance Multisig Owns Both UUPS Proxies; Operator-Fee Guardrails Set by the DAO

| Contract / Check | Address | Selector | Observation at `#26427612` |
| :--- | :--- | :--- | :--- |
| **SSVNetwork `owner()`** | `0xDD9BC35aE942eF0cFa76930954a156B3fF30a4E1` | `owner()` | SSV DAO Treasury `0xb35096b074fdb9bBac63E3AdaE0Bbde512B2E6b6` — `5`-of-`9` Safe (v1.3.0, no modules); `pendingOwner() = 0`; UUPS proxy (EIP-1967 implementation `0xa72a8F31163d74D708664493d09167dfa13008E9`, admin slot empty), `getVersion()` = "v2.0.0"; SSVNetworkViews `0xafE830B6Ee262ba11cce5F32fDCd760FFE6a66e4` has the same `owner()` |
| **SSVNetworkViews `getOperatorFeePeriods()`** | `0xafE830B6Ee262ba11cce5F32fDCd760FFE6a66e4` | `getOperatorFeePeriods()` | declaration period `1209600`s (`14` days), execution period `604800`s (`7` days); `getOperatorFeeIncreaseLimit() = 1000` (10.00%, basis points of 10,000) |

Classification: **aligned baseline** (2 records).
- `docs.ssv.network` (governance): "The first is execution of governance functions controlled by the governance multisig." The owner of both upgradeable network contracts is the address the smart-contracts page lists as "SSV DAO Treasury 0xb35096b074fdb9bBac63E3AdaE0Bbde512B2E6b6".
- `docs.ssv.network` (operator fees): "Between these two steps is a waiting period, called the declaration period, set by the DAO." and "The network also limits the percentage by which operators can increase their fee in each cycle." The documentation gives no numbers; the observed periods and limit are reported, not compared.

## 3. Grove Finance — Allocator Admin Is the Grove SubProxy; Freezer 2-of-5 and Relayer 4-of-7 Safes as Documented

| Contract / Check | Address | Selector | Observation at `#26427612` |
| :--- | :--- | :--- | :--- |
| **ALMProxy `hasRole(DEFAULT_ADMIN_ROLE, SubProxy)`** | `0x491EDFB0B8b608044e227225C715981a30F3A44E` | `hasRole(bytes32,address)` | `true` for Grove SubProxy `0x1369f7b2b38c76B6478c0f0E66D94923421891Ba`; the same on MainnetController `0xfd9dEA9a8D5B955649579Af482DB7198A392A9F5` and RateLimits `0x5F5cfCB8a463868E37Ab27B5eFF3ba02112dF19a`; `CONTROLLER` on the ALMProxy and RateLimits = the MainnetController; none of the three is a proxy |
| **MainnetController `hasRole(FREEZER, Freezer)`** | `0xfd9dEA9a8D5B955649579Af482DB7198A392A9F5` | `hasRole(bytes32,address)` | `true` for the documented Freezer `0xB0113804960345fd0a245788b3423319c86940e5`, a `2`-of-`5` Safe (v1.4.1, no modules) |
| **MainnetController `hasRole(RELAYER, Relayer)`** | `0xfd9dEA9a8D5B955649579Af482DB7198A392A9F5` | `hasRole(bytes32,address)` | `true` for the documented Relayer `0x0eEC86649E756a23CBc68d9EFEd756f16aD5F85f`, a `4`-of-`7` Safe (v1.4.1, no modules) |

Classification: **aligned baseline** (3 records).
- `docs.grove.finance` (Grove Allocator, permissions): "DEFAULT_ADMIN_ROLE Grants and revokes all other roles." The deployed-contracts page lists "Grove SubProxy ( GROVE_PROXY) 0x1369f7b2b38c76B6478c0f0E66D94923421891Ba" among "the governance addresses that administer Grove".
- Same pages: "FREEZER Emergency role that can revoke any relayer's access, effectively halting all automated operations." and "Freezer ( ALM_FREEZER) 0xB0113804960345fd0a245788b3423319c86940e5".
- Same pages: "RELAYER Assigned to the ALM Planner's offchain component. Can invoke DeFi operations on the controller" and "Relayer ( ALM_RELAYER) 0x0eEC86649E756a23CBc68d9EFEd756f16aD5F85f".

Context (not scored; read at the Base pin `#58203774`): on Base the ALM Proxy `0x9B746dBC5269e1DF6e4193Bcb441C0FbBF1CeCEe`, ForeignController `0x7f8408eBbBC3504F83eeDa52910dd75Eba92C955` and RateLimits `0xAc8BF0669223197ac8B94Cbb53E725e40B3919E8` give `DEFAULT_ADMIN_ROLE` to the Grove Executor `0x491EDFB0B8b608044e227225C715981a30F3A44E` (`delay() = 0`, `gracePeriod() = 604800`s), and the same Freezer and Relayer Safes (same addresses, same thresholds) hold `FREEZER` and `RELAYER` — as documented: "Payloads reach them from Ethereum through the governance relay: the receiver accepts the bridged message and the executor applies it." These contracts use OpenZeppelin `AccessControl` without enumeration, so the holders above are confirmed for the documented addresses; other holders are not excluded.

## 4. Re Protocol (reUSD / reUSDe) — 48-Hour Timelock Holds Token Admin and Upgrades; the ICL Admin Is the Timelock, Not the Safe

| Contract / Check | Address | Selector | Observation at `#26427612` |
| :--- | :--- | :--- | :--- |
| **reUSD `hasRole(DEFAULT_ADMIN_ROLE, Timelock)`** | `0x5086bf358635B81D8C47C66d1C8b9E567Db70c72` | `hasRole(bytes32,address)` | `true` (and `UPGRADER_ROLE`) for TimelockController `0x69dDEa332723cF5407151aAF68B9b076557FCA93`, `getMinDelay() = 172800`s (`48` hours); the same on reUSDe `0xdDC0f880ff6e4e22E4B74632fBb43Ce4DF6cCC5a`; the Safe holds neither role; UUPS (implementation `0xb5276c436F65913Cd5332DE745d04feDEb4a21D4`); the ICL holds `MINTER_ROLE` on reUSD |
| **reUSD ICL `hasRole(DEFAULT_ADMIN_ROLE, Safe)`** | `0x4691C475bE804Fa85f91c2D6D0aDf03114de3093` | `hasRole(bytes32,address)` | `false`; the Timelock holds `DEFAULT_ADMIN_ROLE` and `UPGRADER_ROLE` on this ICL (`shareToken()` = reUSD; implementation `0x06d4ACC104b974cD99bF22e4572f48A051E59670`); `getRoleAdmin(UPGRADER_ROLE) = DEFAULT_ADMIN_ROLE` |
| **Timelock `hasRole(PROPOSER_ROLE, Safe)`** | `0x69dDEa332723cF5407151aAF68B9b076557FCA93` | `hasRole(bytes32,address)` | `true`, and `EXECUTOR_ROLE` / `CANCELLER_ROLE`; the Timelock is its own admin; Safe `0x8eec10616802Ef639CA55c98ac856553fAdEfBaD` is `3`-of-`5` (v1.4.1, no modules) |

Classification: **mixed** — `2` aligned baselines, `1` protective delta.
- **aligned**: `docs.re.xyz` (smart contracts): "a 48-hour TimelockController holds DEFAULT_ADMIN_ROLE and UPGRADER_ROLE on the ShareToken" and "OpenZeppelin TimelockController enforcing a 2-day (172,800 second) delay between scheduling and executing privileged actions."
- **protective delta**: same page: "The Safe holds DEFAULT_ADMIN_ROLE on every ICL (Ethereum reUSD and reUSDe, Avalanche, Arbitrum, Base), alongside the chain's timelock." and "… so the Safe can grant itself ICL UPGRADER_ROLE with no delay". On the Ethereum reUSD ICL the Safe does not hold `DEFAULT_ADMIN_ROLE`; the Timelock does, so granting `UPGRADER_ROLE` there waits the `48`-hour delay.
- **aligned**: same page: "A Gnosis Safe ( 0x8eec10616802Ef639CA55c98ac856553fAdEfBaD) is the sole proposer, executor, and canceller on those timelocks"

Context (not scored): reUSD and reUSDe share one implementation. These contracts use OpenZeppelin `AccessControl` without enumeration; the holders above are confirmed for the documented addresses, other holders are not excluded. Only the Ethereum deployment was read.

## 5. Aerodrome Finance (Base) — Fee and Pause Roles on a 3-of-7 Safe; Emergency Council and Epoch Governor Now Point to a Migration Contract (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at Base `#58203774` |
| :--- | :--- | :--- | :--- |
| **PoolFactory `MAX_FEE()`** | `0x420DD381b31aEf6683db6B902084cB0FFECe40Da` | `MAX_FEE()` | `300` (3.00%; `stableFee() = 5`, `volatileFee() = 30`, basis points); `pauser()` = `feeManager()` = Safe `0xE6A41fE61E7a1996B59d508661e3f524d6A32075` (`3`-of-`7`, v1.3.0, no modules), also the Voter `governor()` and the FactoryRegistry `0x5C3F18F06CC09CA1910767A34a20F771039E37C0` `owner()`; `isPaused() = false`; not a proxy |
| **Voter `emergencyCouncil()` / `epochGovernor()`** | `0x16613524e02ad97eDfeF371bC883F2F5d6C480A5` | `emergencyCouncil()` | both `AerodromeMigration` `0x22a2F7340a3fB4C7C389D91eE954766B12476721` (Sourcify match; `MIGRATION_OPEN() = 1792620000`, `V2_VOTER()` = this Voter), whose `owner()` is Safe `0x42255e3C2d0b71a0b006243148fdF1a71d054cE0` (`3`-of-`7`, v1.5.0, no modules; the same `7` signers as the governor Safe) |

Classification: **mixed** — `1` aligned baseline, `1` parameter delta.
- **aligned**: `github.com/aerodrome-finance/contracts` (SPECIFICATION.md): "FeeManager: Can set a custom fee per pool, with a maximum fee of 3%" and "Pauser: Switch the pool's pause state (enabling/disabling pool swaps)" `MAX_FEE() = 300`.
- **parameter delta**: same repository (README): "EpochGovernor.sol A simple epoch-based governance contract used exclusively for adjusting emissions." and SPECIFICATION.md: "Managed NFTs can be deactivated, a process which prevents the NFT from voting and from receiving deposits (requires emergency council)." On-chain both roles resolve to the `AerodromeMigration` contract, which the published contracts documentation does not describe.

Context (not scored): the published RPC-observed record pairs the PoolFactory with the Voter; both stay the protocol's primary contract and controller.

## 6. Balancer V2 Vault & TimelockAuthorizer — Authorizer Admin Is the 6-of-11 DAO Multisig; the Vault Is Immutable (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26427612` |
| :--- | :--- | :--- | :--- |
| **Authorizer `getRoleMember(DEFAULT_ADMIN_ROLE, 0)`** | `0xA331D84eC860Bf466b4CdCcFb4aC09a1B43F3aE6` | `getRoleMember(bytes32,uint256)` | DAO Multi-sig `0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f`, the only member (`getRoleMemberCount = 1`), `6`-of-`11` Safe (v1.1.1, no modules); the Vault's `getAuthorizer()` is `AuthorizerWithAdaptorValidation` `0x6048A8c631Fb7e77EcA533Cf9C29784e482391e7`, whose `getActualAuthorizer()` is this Authorizer |
| **Vault `getPausedState()`** | `0xBA12222222228d8Ba445958a75a0704d566BF2C8` | `getPausedState()` | `paused = false`, `pauseWindowEndTime = 1626633407`, `bufferPeriodEndTime = 1629225407` (both before the pin); EIP-1967 implementation and admin slots empty (not a proxy) |

Classification: **aligned baseline** (2 records).
- `docs.balancer.fi` (multisig): "DAO Multi-sig 0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f open in new window 6/11 DAO Signers DAO administrative permissions" and "Ethereum DAO Multisig — Authorizer admin on Mainnet"
- Same page: "The core of Balancer smart contracts are immutable and do not use proxies or other upgrade mechanisms."

Context (not scored): the Vault's authorizer `0x6048A8c631Fb7e77EcA533Cf9C29784e482391e7` is an `AuthorizerWithAdaptorValidation` wrapper, not a `TimelockAuthorizer`; the timelock getters (`getRoot()`, `getRootTransferDelay()`) revert on it. The protocol keeps its published name, slug, primary contract and controller.

## 7. Drift Re-Scans (Part C) — 0 of 3 Drifted

Every scored parameter of three earlier attested protocols, read at its original pinned block (archive pair) and at `#26427612` (`audits/sprint-21/drift-rescan-26427612.json`); Ethereum mainnet only (`compound-v3-base` is not read):

| Protocol (record) | Check | Baseline block | Before | After |
| :--- | :--- | :--- | :--- | :--- |
| convex-finance | Booster owner() | `26401312` | `0x3cE6408F923326f81A7D7929952947748180f1E6` | same |
| convex-finance | BoosterOwner owner() | `26401312` | `0x256e1bbA846611C37CF89844a02435E6C098b86D` | same |
| convex-finance | Secondary owner owner() | `26401312` | `0xa3C5A1e09150B75ff251c1a7815A07182c3de2FB` | same |
| convex-finance | DAO Multisig getThreshold() | `26401312` | 3 | same |
| convex-finance | DAO Multisig getOwners().length | `26401312` | 5 | same |
| compound-v3-comet | cUSDCv3 governor() | `26402160` | `0x6d903f6003cca6255D85CcA4D3B5E5146dC33925` | same |
| compound-v3-comet | cWETHv3 governor() | `26402160` | `0x6d903f6003cca6255D85CcA4D3B5E5146dC33925` | same |
| compound-v3-comet | Timelock delay() | `26402160` | 172800 | same |
| compound-v3-comet | Timelock admin() | `26402160` | `0x309a862bbC1A00e45506cB8A802D1ff10004c8C0` | same |
| compound-v3-comet | cUSDCv3 pauseGuardian() | `26402160` | `0xbbf3f1421D886E9b2c5D716B5192aC998af2012c` | same |
| compound-v3-comet | cWETHv3 pauseGuardian() | `26402160` | `0xbbf3f1421D886E9b2c5D716B5192aC998af2012c` | same |
| compound-v3-comet | Community Pause Safe getThreshold() | `26402160` | 5 | same |
| compound-v3-comet | Community Pause Safe getOwners().length | `26402160` | 9 | same |
| aave-v3-gho | ACLManager hasRole(DEFAULT_ADMIN_ROLE, Executor Lvl 1) | `26402160` | 1 | same |
| aave-v3-gho | PayloadsController getExecutorSettingsByAccessControl(1).executor | `26402160` | `0x5300A1a15135EA4dc7aD5a167152C01EFc9b192A` | same |
| aave-v3-gho | PayloadsController getExecutorSettingsByAccessControl(1).delay | `26402160` | 86400 | same |
| aave-v3-gho | ACLManager hasRole(EMERGENCY_ADMIN, Protocol Guardian Safe) | `26402160` | 1 | same |
| aave-v3-gho | Protocol Guardian Safe getThreshold() | `26402160` | 4 | same |
| aave-v3-gho | Protocol Guardian Safe getOwners().length | `26402160` | 7 | same |

All `19` "before" values equal the values recorded in the original records (`convex-booster-governance-chain`, Sprint 4; `compound-v3-comet-timelock-and-pause-safe` and `aave-v3-gho-acl-manager-and-executor-lvl1`, Sprint 9). Unscored extras, all unchanged: the three Safes' owner sets and GHO `totalSupply()`.

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-16`). Checks are sampled getters, EIP-1967 / proxy slots and Safe parameters at the finalized pins above; it does not certify protocol-wide immutability, exhaustive authority coverage or exploitability, and it is not a smart-contract audit. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to the affected protocols. Pacta by Fractal Neurons publishes these records as documentation-comparison evidence, not as audits or investment advice.
