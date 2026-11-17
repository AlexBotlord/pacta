# Sprint 24 Protocol Commitment Summary — Block `26433001`

- **Ethereum Mainnet pin**: `26433001` (`0x19355e9`), canonical block hash `0xa058ec92ccf0024822a76097f183d8e2d344d56e9539038c857e0cdaaa0ee5a7`, timestamp `2026-11-17 06:33:59 UTC` (`1794897239`); the lower of the two endpoints' `finalized` heads (both `26433001`)
- **Base Mainnet pin**: `58534152` (`0x37d2908`), canonical block hash `0x7b884f4d029427b5d15f71c50b128bd69ac7c6da6962ced946ca87b0b4e6e843`, timestamp `2026-11-17 06:33:26 UTC` (`1794897206`); the lower of the two endpoints' `finalized` heads (both `58534152`)
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI). Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: `gateway.tenderly.co/public/mainnet` + `rpc.mevblocker.io` (Ethereum), `mainnet.base.org` + `base-rpc.publicnode.com` (Base).
- **Result**: `23` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `21` aligned baselines, `2` parameter deltas. `verifiedCount = 21` (`21` aligned baselines). `driftCount = 2` (`2` parameter deltas), the same convention as Sprints 1–23 and `PactaSentinelGuard` (`driftCount != 0` means drift).
- **Part C (Section 3.4 dual chain + documentation re-scan)**: `0 of 3` reconciled or drifted across `18` checks; both re-scanned parameter deltas persist on chain and in the live documentation (Section 7).
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); the Centrifuge (Base) records and the Uniswap V4 Base record are read at the Base pin.

## 1. Steakhouse Financial (Ethereum) — steakUSDC, steakUSDT and steakPYUSD Share a 5-of-10 Owner Safe, a 7-Day Timelock and Aragon Guardian DAOs, as Documented

| Contract / Check | Address | Selector | Observation at `#26433001` |
| :--- | :--- | :--- | :--- |
| **Owner Safe `getThreshold()`** | `0x0A0e559bc3b0950a7e448F0d4894db195b9cf8DD` | `getThreshold()` | `5` of `10` owners (Safe v1.4.1, no guard); `owner()` of steakUSDC `0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB`, steakUSDT `0xbEef047a543E45807105E51A8BBEFCc5950fcfBa` and steakPYUSD `0xbEEF02e5E13584ab96848af90261f0C8Ee04722a` (MetaMorpho; steakUSDC Sourcify exact match); `curator()` of all three = Safe `0x827e86072B06674a077f592A531dcE4590aDeCdB` (`3` of `9`, v1.4.1); no pending owner |
| **steakUSDC `timelock()`** | `0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB` | `timelock()` | `604800`s (`7` days), no pending timelock change; steakUSDT and steakPYUSD also `604800`s |
| **steakUSDC `guardian()`** | `0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB` | `guardian()` | `0xaa0500198B4425DfC4E272FbE42C8E64E21fc03d`: the Aragon DAO that `steakusdc-guardian.dao.eth` resolves to on-chain; steakUSDT / steakPYUSD guardians `0xaeC761545Fd135db6d04D27C92BCB3951668c67F` / `0xCcFd0E9CEC732fb839fadDeCc72B6154530bC90f` (their own `*-guardian.dao.eth`); no pending guardian |
| **Guardian voting `minDuration()`** | `0x79864900a4d34fb7907De9fe404758de5a4956dE` | `minDuration()` | `86400`s (`1` day) on the steakUSDC guardian's token-voting plugin (`dao()` = that guardian); `UPDATE_VOTING_SETTINGS`, `UPGRADE_PLUGIN`, `ROOT` and `UPGRADE_DAO` permissions read `false` on all three guardian DAOs |

Classification: **aligned baseline** (4 records).
- Steakhouse docs (vault setup and controls; legacy vaults): 'Steakhouse’s “owner” employs a Safe multisig with a quorum of five keys, meaning that five persons must coordinate to introduce any owner-level operations.' / 'Steakhouse USDC Stablecoin Prime Instant USDC Ethereum v1 0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB'.
- Timelock: 'All Steakhouse vaults have a timelock of 7-days allowing users to exit the vault if they disagree with a significant change (as shown in the diagram below).' / '| Timelock | 7 days | Shorter time frames do not give enough time for token holders to react on adverse parameter modifications |' / 'Steakhouse USDC Stablecoin Prime Instant USDC Ethereum v1 0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB'.
- Guardian (Steakhouse's Morpho forum announcement, linked from the docs): 'The new guardians will be the following: - [steakUSDC](https://app.aragon.org/#/daos/ethereum/steakusdc-guardian.dao.eth/dashboard)' / 'Veto Mechanism: Seeking to provide depositors with even more control over their funds and curated vaults, Steakhouse introduced the Aragon DAO guardian to enable vault depositors to veto critical actions made by the curator.'; voting: 'The voting period is one day leaving plenty of time for users to react (as the timelock is seven days).' / '* `UPDATE_VOTING_SETTINGS_PERMISSION_ID`, removing the ability of the DAO to update its settings; * `ROOT_PERMISSION_ID` on the DAO, removing the ability of the DAO to grant itself `UPDATE_VOTING_SETTINGS_PERMISSION_ID` again;'.

Context (not scored): the docs page also says "above the minimum, protocol-enforced 3-day timelock"; the verified MetaMorpho source's minimum timelock is 1 day (the vaults' 7 days is above both). Steakhouse files these Morpho v1 vaults under "Legacy Vaults"; the Base vault `steakhouse-usdc-metamorpho-base` is a separate Pacta protocol. Allocators (not compared: the documentation does not list them) can only reallocate within enabled markets and caps.

## 2. Uniswap V4 — The PoolManager Is Owned by the Governance Timelock and Its Protocol Fee Controller Is the Documented V4FeeAdapter

| Contract / Check | Address | Selector | Observation |
| :--- | :--- | :--- | :--- |
| **PoolManager (Ethereum) `owner()`** | `0x000000000004444c5dc75cB358380D2e3dE08A90` | `owner()` | Uniswap Governance `Timelock` `0x1a9C8182C09F50C8318d769245beA52c32BE35BC` (`delay()` = `172800`s = `MINIMUM_DELAY()`, `admin()` = `GovernorBravoDelegator` `0x408ED6354d4973f66138C91495F2f2FCbd8724C3`) at `#26433001`; `PoolManager` (Sourcify match), not a proxy |
| **PoolManager (Ethereum) `protocolFeeController()`** | `0x000000000004444c5dc75cB358380D2e3dE08A90` | `protocolFeeController()` | `V4FeeAdapter` `0x89A5D5bF00a27D55c02951E49078a5C5771051dB` (Sourcify exact match): `POOL_MANAGER()` = this PoolManager, `TOKEN_JAR()` = `0xf38521f130fcCF29dB1961597bc5d2B60F995f85`, `policy()` = `0x1cd822b70a0591420F65E94b9B3A0D0b0fB3a314` |
| **V4FeeAdapter `feeSetter()`** | `0x89A5D5bF00a27D55c02951E49078a5C5771051dB` | `feeSetter()` | the Timelock; `owner()` = the Timelock; the fee policy's `owner()` / `feeSetter()` = the Timelock |
| **PoolManager (Base) `protocolFeeController()`** | `0x498581fF718922c3f8e6A244956aF099B2652b2b` | `protocolFeeController()` | `V4FeeAdapter` `0xc53DD825dedBE7814562528A1A30e8e5BCbB4b55` at Base `#58534152` (`POOL_MANAGER()` = this PoolManager, `TOKEN_JAR()` = `0x9bD25e67bF390437C8fAF480AC735a27BcF6168c`; not verified on Sourcify); PoolManager `owner()` and the adapter's `owner()` = `0x31FAfd4889FA1269F7a13A66eE0fB458f27D72A9`, whose stored L1 owner is the Ethereum Timelock (messenger `0x4200…0007`) |

Classification: **aligned baseline** (4 records).
- `developers.uniswap.org` (v4 deployments; governance technical reference; governance overview): 'Ethereum: 1 Contract Address PoolManager 0x000000000004444c5dc75cB358380D2e3dE08A90' / 'The contracts below are actively deployed on Ethereum mainnet.' / 'Timelock 0x1a9C8182C09F50C8318d769245beA52c32BE35BC' / 'Uniswap Governance has specific controls under its domain, including: Spend funds from the treasury Set and activate the protocol fee'.
- Protocol fee (deployments; overview): 'V4FeeAdapter 0x89A5D5bF00a27D55c02951E49078a5C5771051dB' / 'Ethereum: 1 Contract Address PoolManager 0x000000000004444c5dc75cB358380D2e3dE08A90' / 'Each protocol component that generates fees (v2, v3, v4, UniswapX, Unichain, and others) routes those fees through an associated Fee Adapter contract.'; 'Governance can update which Releaser a TokenJar uses or adjust configuration on Fee Adapters, but the core contracts themselves are immutable.' / 'V4FeeAdapter 0x89A5D5bF00a27D55c02951E49078a5C5771051dB' / 'Timelock 0x1a9C8182C09F50C8318d769245beA52c32BE35BC'.
- Base: 'Base: 8453 Contract Address Deployer 0x076f84717f3601B8Cd177bb84b217A2679B38b7d TokenJar 0x9bD25e67bF390437C8fAF480AC735a27BcF6168c Releaser (OptimismBridgedResourceFirepit) 0xFf77c0ED0B6b13A20446969107E5867abc46f53a V3OpenFeeAdapter 0xaBEA76658b205696d49B5F91b2a03536cB8A3bE1 V4FeeAdapter 0xc53DD825dedBE7814562528A1A30e8e5BCbB4b55' / 'Base: 8453 Contract Address PoolManager 0x498581ff718922c3f8e6a244956af099b2652b2b' / 'Governance can update which Releaser a TokenJar uses or adjust configuration on Fee Adapters, but the core contracts themselves are immutable.'.

Context (not scored): the PoolManager owner's only powers are setting the protocol fee controller and transferring ownership; per-pool fee values are not compared. The Base cross-chain owner contract is not named in the documentation fetched. Uniswap V3 governance parameters are the separate `uniswap-governance-timelock` protocol.

## 3. Chainlink CCIP (Ethereum) — CCIP Contracts Are Owned by a 3-Hour RBACTimelock, as Documented; One of Its Three Proposers Is a 6-of-12 Safe, Not a ManyChainMultiSig

| Contract / Check | Address | Selector | Observation at `#26433001` |
| :--- | :--- | :--- | :--- |
| **Router `owner()`** | `0x80226fc0Ee2b096224EeAc085Bb9a8cba1146f7D` | `owner()` | `RBACTimelock` `0x44835bBBA9D40DEDa9b64858095EcFB2693c9449` (Sourcify match; `getMinDelay()` = `10800`s, `3` hours, for scheduled operations), which also owns the RMN proxy `0x411dE17f12D1A34ecC7F45f49844626267c75e81`, the `TokenAdminRegistry` and `CCIPHome`; `Router 1.2.0` (Sourcify match). Its `BYPASSER_ROLE` has `1` member, `ManyChainMultiSig` `0x117ec8aD107976e1dBCc21717ff78407Bc36aADc`, which can execute calls immediately through `bypasserExecuteBatch` (no schedule, no delay) |
| **RBACTimelock PROPOSER_ROLE** | `0x44835bBBA9D40DEDa9b64858095EcFB2693c9449` | `getRoleMember(PROPOSER_ROLE, i)` | `3` members: `ManyChainMultiSig` `0xE53289F32c8E690b7173aA33affE9B6B0CB0012F` (the MCMS the documentation links), a `GnosisSafeProxy` `0xD6597750bf74DCAEC57e0F9aD2ec998D837005bf` (Safe v1.3.0, `6` of `12` owners; also a canceller) and `ManyChainMultiSig` `0xD9757aA52907798d1aF2FDa7A6C0cC733E5aCf7e`; `1` bypasser (`ManyChainMultiSig` `0x117ec8aD107976e1dBCc21717ff78407Bc36aADc`) |
| **RMN `owner()`** | `0x0B047953451A207743fB62541B21199b95190602` | `owner()` | `RBACTimelock` `0x6608920e3F6b591EC3Cf15CA1DDf66fBE117F56A` (`getMinDelay()` = `10800`s for scheduled operations; admin = the main timelock; `BYPASSER_ROLE`: `1` member, `0x8C00Cc7cC37396e88BbFe66371341a59D1b5771F`, executing immediately through `bypasserExecuteBatch`); `getARM()` of the proxy; `RMN 2.1.0` (not verified on Sourcify); `isCursed()` = `false`; `2` authorized curse callers |
| **TokenAdminRegistry `owner()`** | `0xb22764f98dD05c789929716D677382Df22C05Cb6` | `owner()` | the main `RBACTimelock`; `TokenAdminRegistry 1.5.0` (Sourcify match); `Router.getArmProxy()` = `0x411dE17f12D1A34ecC7F45f49844626267c75e81` |

Classification: **mixed** — `3` aligned baselines, `1` parameter delta.
- **aligned**: CCIP upgradability: 'All configuration changes to CCIP-owned contracts must pass through a Role-Based Access Control Timelock (RBACTimelock) contract. Token pools are owned by token issuers, who configure them directly.' / 'The timelock then calls the target CCIP contracts with the specified changes.'
- **parameter delta**: 'All proposals originate from a ManyChainMultiSig (MCMS), which requires multiple independent signers to sign off.' / 'For example, you can view the Ethereum mainnet MCMS on Etherscan.' On-chain the RBACTimelock's PROPOSER_ROLE also includes a 6-of-12 Gnosis Safe, so not all proposals originate from a ManyChainMultiSig.
- **aligned**: RMN API reference: 'Uncurses one subject or an array of subjects. Owner-only.' / 'Curses one subject or an array of subjects. Callable by the owner or an authorized caller.' / 'The owner may update the implementation via setARM'
- **aligned**: CCIP Directory (Ethereum): 'Router 0x8022...6f7D' / 'RMN 0x411d...5e81' / 'Token admin registry 0xb227...5Cb6'

Context (not scored): the `3`-hour `getMinDelay()` applies to scheduled operations only. The verified `RBACTimelock` source's `bypasserExecuteBatch` lets a `BYPASSER_ROLE` (or admin-role) holder execute calls directly, with no schedule and no delay, and both timelocks have one bypasser at the pin, so the enforced floor on these contracts is `0`s through that route (the documentation names an "Explicit approval" bypass path in general terms). No CCIP page states the timelock delay or MCMS quorums (reported, not compared). Per-chain curses can be set by the authorized callers (one is a 0-delay RBACTimelock `0xD9aB1714Df2b5d0011B22f6D94812e7813Fa5795`); the global curse is off at the pin.

## 4. Obol Network (Ethereum) — 5-Day Timelock and 30,000 OBOL / 0.84% Governor Thresholds as Documented; the "Capped" OBOL Supply Has No On-Chain Cap

| Contract / Check | Address | Selector | Observation at `#26433001` |
| :--- | :--- | :--- | :--- |
| **TimelockController `getMinDelay()`** | `0xCdBf527842Ab04Da548d33EB09d03DB831381Fb0` | `getMinDelay()` | `432000`s (`5` days); `ObolGovernor` `0xcB1622185A0c62A80494bEde05Ba95ef29Fbf85c` holds PROPOSER / EXECUTOR / CANCELLER; `DEFAULT_ADMIN_ROLE`: the timelock itself and the deployer `0x02b5D1Fd67246c0513223D320901474aA20Bf973` (not the Governor) (Sourcify exact match) |
| **ObolGovernor `proposalThreshold()`** | `0xcB1622185A0c62A80494bEde05Ba95ef29Fbf85c` | `proposalThreshold()` | `30000` OBOL; quorum `84 / 10000` (`0.84`%); `votingDelay()` = `7200` blocks, `votingPeriod()` = `36000` blocks (block-number clock) (Sourcify exact match) |
| **ObolToken `totalSupply()`** | `0x0B010000b7624eb9B3DfBC279673C76E9D29D5F7` | `totalSupply()` | `500000000000000103303500000` (`500,000,000.0000001033035` OBOL); `MINTER_ROLE` and `DEFAULT_ADMIN_ROLE` held by Safe `0x42D201CC4d9C1e31c032397F54caCE2f48C1FA72` (`2` of `3`, v1.3.0), not the timelock; the verified source's `mint()` has no supply cap (Sourcify exact match) |
| **stOBOL WithdrawGate `delay()`** | `0x4094C8D36e40795Ca25BFe9451f158D30614666A` | `delay()` | `0`s (`DELAY_MAX()` = `2592000`s); `owner()` = Safe `0x7E90E03654732ABedF89Faf87f05BcD03ACEeFdC` (`1` of `2`, v1.4.1) (Sourcify exact match) |

Classification: **mixed** — `3` aligned baselines, `1` parameter delta.
- **aligned**: Obol docs (v1.8 Token House governance): 'After the voting period ends, if the proposal passes, there will be a 5-day timelock delay.'
- **aligned**: same page: 'During Week 3, a wallet holding at least 30,000 OBOL in voting power must publish the proposal on the Obol Governance Platform.' / 'The current definition for the OBOL Token House is 0.84% of minted supply.' / 'After publication, there is a 24-hour voting delay, during which the proposal can be canceled if necessary.'
- **parameter delta**: Obol docs (token distribution; OBOL token): 'The total supply is capped at 500 million tokens.' / 'The official token contract address of the OBOL Token is 0x0B010000b7624eb9B3DfBC279673C76E9D29D5F7' On-chain `mint()` is uncapped and a 2-of-3 Safe holds `MINTER_ROLE`; total supply is already marginally above 500M.
- **aligned**: unstaking guide: 'You can unstake at any time, there are no lockups' / 'https://etherscan.io/address/0x6590cBBCCbE6B83eF3774Ef1904D86A7B02c2fCC#writeContract' The gate's 1-of-2 owner Safe can raise the delay up to 30 days (context).

Context (not scored): the Governor and timelock figures come from the v1.8 docs (the current governance page says governance is paused off-chain; the contracts are live). The 24-hour voting delay is block-based (`7200` blocks).

## 5. Synthetix V3 Core — Core, USD, Account and Oracle Manager Proxies Are Owned as the Deployment Documentation Lists (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26433001` |
| :--- | :--- | :--- | :--- |
| **CoreProxy `owner()`** | `0xffffffaEff0B96Ea8e4f94b2253f31abdD875847` | `owner()` | Safe `0xEb3107117FEAd7de89Cd14D463D340A2E6917769` (`4` of `7`, v1.3.0; the pDAO in `synthetix-deployments`); `nominatedOwner()` = `0x0`; router implementation `0x58ce7364744e59402B3672D3Cf3Bb415a12441cD` (Sourcify exact match; non-EIP-1967 storage) |
| **USDProxy `owner()`** | `0xb2F30A7C980f052f02563fb518dcc39e6bf38175` | `owner()` | the CoreProxy; no nominated owner |
| **AccountProxy `owner()`** | `0x0E429603D3Cb1DFae4E6F52Add5fE82d96d77Dac` | `owner()` | the CoreProxy; no nominated owner |
| **OracleManagerProxy `owner()`** | `0x0aaF300E148378489a8A471DD3e9E53E30cb42e3` | `owner()` | the pDAO Safe; no nominated owner |

Classification: **aligned baseline** (4 records).
- Synthetix V3 deployment info (the `Synthetix-Gitbook-v3` source of the former V3 docs, pinned commit): 'CoreProxy 0xEb3107117FEAd7de89Cd14D463D340A2E6917769 n/a' / 'CoreProxy 0xffffffaEff0B96Ea8e4f94b2253f31abdD875847' / '[setting.pdao] defaultValue = "0xEb3107117FEAd7de89Cd14D463D340A2E6917769"'; 'USDProxy 0xffffffaEff0B96Ea8e4f94b2253f31abdD875847 n/a' / 'USDProxy 0xb2F30A7C980f052f02563fb518dcc39e6bf38175'; 'AccountProxy 0xffffffaEff0B96Ea8e4f94b2253f31abdD875847 n/a' / 'AccountProxy 0x0E429603D3Cb1DFae4E6F52Add5fE82d96d77Dac'; 'OracleManagerProxy 0xEb3107117FEAd7de89Cd14D463D340A2E6917769 n/a' / 'OracleManagerProxy 0x0aaF300E148378489a8A471DD3e9E53E30cb42e3'.

Context (not scored): the live docs site no longer covers V3; the V3 Ethereum deployment is being wound down (user entry points disabled) while the owner and upgrade path are unchanged. The pDAO Safe's 4-of-7 quorum has no address-scoped documentation (reported, not compared). The published RPC-observed record's primary contract (`CoreProxy`) and controller are kept.

## 6. Centrifuge V3 Root (Base) — The Root Contract Enforces a 48-Hour Delay, the ProtocolGuardian Is Its Ward and the OpsGuardian Is Not (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at Base `#58534152` |
| :--- | :--- | :--- | :--- |
| **Root `delay()`** | `0x7Ed48C31f2fdC40d37407cBaBf0870B2b688368f` | `delay()` | `172800`s (`48` hours); `paused()` = `false`; not a proxy (both EIP-1967 slots zero) (Sourcify exact match) |
| **Root `wards(ProtocolGuardian)`** | `0x7Ed48C31f2fdC40d37407cBaBf0870B2b688368f` | `wards(address)` | `1` for `ProtocolGuardian` `0xCEb7eD5d5B3bAD3088f6A1697738B60d829635c6` (Sourcify match), whose `root()` = Root and `safe()` = Safe `0x9711730060C73Ee7Fcfe1890e8A0993858a7D225` (`4` of `9`, v1.4.1) |
| **Root `wards(OpsGuardian)`** | `0x7Ed48C31f2fdC40d37407cBaBf0870B2b688368f` | `wards(address)` | `0` for `OpsGuardian` `0x055589229506Ee89645EF08ebE9B9a863486d0dE` (Sourcify match), whose `opsSafe()` = Safe `0xd21413291444C5c104F1b5918cA0D2f6EC91Ad16` (`2` of `7`, v1.4.1); neither Safe is a direct ward |

Classification: **aligned baseline** (3 records).
- `docs.centrifuge.io` (security and guardians; deployments): 'All privilege escalation through `Root` goes through a 48-hour timelock. Changes must be scheduled first, then can only be executed after the delay has passed. This gives the community visibility into upcoming changes and time to react before they take effect.' / 'The protocol is controlled by the `Root` contract, an immutable smart contract that holds admin (ward) access on all other contracts. `Root` has no direct external access. The only way to interact with it is through the guardian contracts, which mediate between governance multisigs and `Root`.' / 'Root 0x7Ed48C31f2fdC40d37407cBaBf0870B2b688368f'
- 'The protocol guardian is deployed at `0xCEb7eD5d5B3bAD3088f6A1697738B60d829635c6` on all networks.' / 'The `ProtocolGuardian` is controlled by the Protocol Safe multisig and handles emergency response and protocol-level changes, including pausing, upgrades, and cross-chain operations. Every transaction is verified by third-party signers from [Cantina](https://cantina.xyz/solutions/multisig-security). The protocol can respond to emergencies instantly, with full resumption requiring multisig consensus.' / '"protocolAdmin": "0x9711730060C73Ee7Fcfe1890e8A0993858a7D225",'
- 'The ops guardian is deployed at `0x055589229506Ee89645EF08ebE9B9a863486d0dE` on all networks.' / 'The `OpsGuardian` is controlled by a separate Ops Safe multisig and handles day-to-day operational tasks such as adapter initialization, network wiring, and pool creation. It has no pause authority.' / '"opsAdmin": "0xd21413291444C5c104F1b5918cA0D2f6EC91Ad16",'

Context (not scored): the 48-hour delay covers permissions newly scheduled through Root; Root's own settings and direct permissions are callable by its wards (the ProtocolGuardian exposes no path to them). Ward holders cannot be enumerated with `eth_call`; four candidates were checked. Neither Safe's quorum is documented (reported, not compared).

## 7. Section 3.4 Dual Chain + Documentation Re-Scan (Part C) — 0 of 3 Reconciled or Drifted

Every scored value of three of the oldest non-bounty records, read at its original pinned block (archive pair) and at `#26433001` (`audits/sprint-24/drift-rescan-26433001.json`), and the documented statement each record compares against, re-fetched (HTTP 200). `lido-steth-dual-governance` and `yearn-v3` are excluded while open bounty pull requests concern them.

| Record | Baseline | Checks | Chain | Documentation | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `renzo-ezeth-deposit-queue-fee` | Sprint 8 `#26401725` | 3 | unchanged | unchanged | persists |
| `eigenlayer-core-proxy-admin-and-timelock` | Sprint 9 `#26402160` | 8 | unchanged | unchanged | still aligned |
| `ondo-ousg-rate-limiter-and-flux-timelock` | Sprint 10 `#26403121` | 7 | unchanged | unchanged | persists |

- **Renzo (ezETH)**: `feeBasisPoints()` is still `1500` (15%) and the docs still say "Renzo charges a 10% fee on rewards generated via restaking." The parameter delta persists.
- **Ondo (OUSG)**: the instant-mint global limit is still `$100M` per day against the documented "$50M Global Limit"; redemption still matches ($50M), as do the Flux timelock (1 day) and its admin. The parameter delta persists.
- **EigenLayer**: the ProxyAdmin, the 1-of-2 Executor Multisig (timelock + 9-of-13 Community Multisig), the 10-day `getMinDelay()` and the PauserRegistry are unchanged and still listed in the README. Still aligned.

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-17`). Checks are sampled getters, role checks, proxy slots and Safe parameters at the finalized pins; role holders that cannot be enumerated with `eth_call` are stated as checked candidates only.
