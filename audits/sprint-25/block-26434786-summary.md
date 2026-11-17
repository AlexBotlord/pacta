# Sprint 25 Protocol Commitment Summary — Block `26434786`

- **Ethereum Mainnet pin**: `26434786` (`0x1935ce2`), canonical block hash `0xb712439847099ec3e8b1617aafd1bc7ece29e22a88dc4e7c8afcf05e6944d987`, timestamp `2026-11-17 12:32:23 UTC` (`1794918743`); the lower of the two endpoints' `finalized` heads (both `26434786`)
- **Base Mainnet pin**: `58641783` (`0x37ecd77`), canonical block hash `0x897856027b5df4c28b13bbc5d6d13fdd6fe8d51ecf3c23b5f5802c454f09ce58`, timestamp `2026-11-17 12:32:12 UTC` (`1794918732`); the lower of the two endpoints' `finalized` heads (both `58641783`)
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI). Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: `eth.drpc.org` + `ethereum-rpc.publicnode.com` (Ethereum), `mainnet.base.org` + `base-rpc.publicnode.com` (Base).
- **Result**: `24` records for `6` protocols (`4` new, `2` converted from RPC-observed) — `22` aligned baselines, `2` parameter deltas. `verifiedCount = 22`. `driftCount = 2` (`2` parameter deltas), the same convention as Sprints 1–24 and `PactaSentinelGuard` (`driftCount != 0` means drift).
- **Part C (Section 3.4 dual chain + documentation re-scan)**: `0 of 3` reconciled or drifted across `23` checks (Section 7). A snapshot convergence would show co-occurrence only, never causation.
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); Base reads are taken at the Base pin.

## 1. LayerZero V2 — The Endpoint Is Immutable, a 5-of-9 Multisig Sets Defaults, and the Ethereum ↔ Base Default Pathway Matches on Both Sides

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **EndpointV2 EIP-1967 implementation** | `0x1a44076050125825900e736c501f859c50fE728c` | slot `eip1967.proxy.implementation` | `0x0` on Ethereum and Base: not a proxy (Sourcify match) |
| **EndpointV2 `owner()`** | `0x1a44076050125825900e736c501f859c50fE728c` | `owner()` | Ethereum: OneSig `0xBe010A7e3686FdF65E93344ab664D065A0B02478` (`threshold()` = `5` of `totalSigners()` = `9`); Base: OneSig `0xa0392d116D71ED3b75086194aBa6De3CD1e39B7E` (5 of 9, the same signer set). The owner registers message libraries and sets default libraries / configurations; no timelock |
| **Ethereum → Base default pathway** | `0xbB2Ea70C9E858123480642Cf96acbcCE1372dCe1` | `getAppUlnConfig(address(0), 30184)` | Ethereum `SendUln302` default to Base: `15` confirmations, `4` required DVNs, `0` optional; Base `ReceiveUln302` `0xc70AB6f32772f59fBfc23889Caf4Ba3376C84bAf` default from Ethereum (`30101`) at Base `#58641783`: the same `15` confirmations and `4` required DVNs |

Classification: **aligned baseline** (3 records).
- `docs.layerzero.network` (endpoint): 'The LayerZero Endpoint is the immutable, permissionless protocol entrypoint for sending and receiving omnichain messages.' / 'The LayerZero Endpoint is the single, immutable entry and exit point for cross‑chain messaging, built on five core modules:'
- Defaults and their owner: 'You should always set your DVN configuration explicitly. Defaults are placeholder configurations — they may be Dead DVNs that prevent message delivery, may include only a single DVN, and may change without notice.' / 'This default configuration can vary per channel, changing the placeholder block confirmations, the X‑of‑Y‑of‑N thresholds for verification, the Executor, and the message libraries.' / 'Once an application defines its channel’s X‑of‑Y‑of‑N security settings, those parameters are enforced at the protocol level indefinitely. Only the application delegate can update these configurations. There is no governance, upgrade mechanism, or external actor that can alter or disable a channel’s configuration once set, guaranteeing that security guarantees persist without relying on LayerZero.'
- Pathway: 'For a configuration to be considered valid, the Send Library configurations on Chain A must match the Receive Library configurations on Chain B.'

Context (not scored): the documentation's preset table ("A default pathway configuration will typically have one of the following preset Security Stack configurations within SendULN302") lists two-DVN presets; this pathway's defaults require four DVNs. The endpoint owner can repoint default libraries for every application that keeps the defaults, without delay; applications that pin their own libraries and configuration are not affected.

## 2. Wormhole Core (NTT) — 13-of-19 Guardians Sign Messages and Upgrades, With No Admin Key, on Ethereum and Base

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Core `getGuardianSet(7)`** | `0x98f3c9e6E3fAce36bAAd05FE09d375Ef1464288B` | `getGuardianSet(uint32)` | current set `7`: `19` keys, no expiry; `quorum(19)` = `13` |
| **Core upgrade authority** | `0x98f3c9e6E3fAce36bAAd05FE09d375Ef1464288B` | slot `eip1967.proxy.implementation` | implementation `0x3c3d457f1522D3540AB3325Aa5f1864E34cBA9D0`; EIP-1967 admin slot `0x0` (no proxy admin); upgrades only through guardian-signed governance messages (`governanceChainId()` = `1`, `governanceContract()` = `0x…04`) |
| **Core `messageFee()`** | `0x98f3c9e6E3fAce36bAAd05FE09d375Ef1464288B` | `messageFee()` | `0` (publishing requires `msg.value == messageFee()`, so `0` means free, not disabled); TokenBridge sequence `704995` (live) |
| **Base core** | `0xbebdb6C8ddC678FfA9f8748f85C815C556Dd8ac6` | `getGuardianSet(uint32)` | at Base `#58641783`: the same set `7` (19 keys), quorum `13`, the same governance chain and contract, `messageFee()` `0`, implementation `0xFc0D459b8c299095Dee743645caAc8Ed3f9aBc4d`, no proxy admin |

Classification: **aligned baseline** (4 records).
- `wormhole.com/docs`: 'Once a sufficient delegate quorum is reached or once Guardians independently observe the event, signatures accumulate until the required 13-of-19 quorum is achieved.' / 'Some chains (such as Ethereum and Solana) are secured by all 19 Guardians.' / 'The Core Contract does not distinguish between chains with direct observation and delegated chains; it verifies only that a valid 13-of-19 VAA has been produced.'
- 'Governance is the process through which contract upgrades happen. Guardians manually vote on governance proposals that originate inside the Guardian Network and are then submitted to ecosystem contracts.' / 'This means that governance actions are held to the same security standard as the rest of the system. A two-thirds supermajority of the Guardians is required to pass any governance action.' / 'Governance messages can target any of the various wormhole modules, including the core contracts and all currently deployed Wrapped Token Transfers (WTT) contracts. When a Guardian signs such a message, its signature implies a vote on the action in question. Once more than two-thirds of the Guardians have signed, the message and governance action are considered valid.'
- 'There are no fees to publish a message except when publishing on Solana, but this is subject to change in the future.'
- '0xbebdb6C8ddC678FfA9f8748f85C815C556Dd8ac6' / 'The Core Contract does not distinguish between chains with direct observation and delegated chains; it verifies only that a valid 13-of-19 VAA has been produced.' / 'A two-thirds supermajority of the Guardians is required to pass any governance action.'

Context (not scored): governance actions take effect when 13 of 19 guardians sign; there is no timelock, and the documentation claims none. Per-token NTT manager contracts are not covered.

## 3. RAILGUN — Upgrades, Pauses and Fees Sit With the On-Chain Protocol Request Vote, as Documented

| Contract / Check | Address | Selector / slot | Observation at `#26434786` |
| :--- | :--- | :--- | :--- |
| **RailgunSmartWallet fees** | `0xFA7093CDD9EE6932B4eb2c9e1cde7CE00B1FA4b9` | `shieldFee()` | `25` and `unshieldFee()` `25` basis points (0.25%); `treasury()` = `0xE8A8B458BcD1Ececc6b6b58F80929b29cCecFF40` |
| **ProxyAdmin `owner()`** | `0x4F8E20f55f879beE7Bc010Bd6bD2138B34aC65c8` | `owner()` | the Delegator `0xB6d513f6222Ee92Fff975E901bd792E2513fB53B` (the wallet proxy's EIP-1967 admin is this ProxyAdmin) |
| **Delegator `owner()`** | `0xB6d513f6222Ee92Fff975E901bd792E2513fB53B` | `owner()` | the Voting contract `0xc480F68A3dcC3EdD82134FAB45C14A0FcF1dA3CC` |
| **Voting `SPONSOR_WINDOW()`** | `0xc480F68A3dcC3EdD82134FAB45C14A0FcF1dA3CC` | `SPONSOR_WINDOW()` | `2592000`s (30 days); execution opens `604800`s and closes `1209600`s after the vote is called; `QUORUM()` = `2000000000000000000000000` |

Classification: **aligned baseline** (4 records).
- `docs.railgun.org`: 'Any change to the smart contracts (including the governance, treasury, and voting contracts) requires the passing of a protocol request. The decentralized protocol request system is the only way in which upgrades to the RAILGUN protocol can be made.' / 'https://etherscan.io/address/0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9'
- 'https://etherscan.io/address/0xc480f68a3dcc3edd82134fab45c14a0fcf1da3cc'
- 'After submission, a 30-day Sponsorship Period begins where the request must reach a value determined by the smart contract.' / 'This must be done within 30-days of the protocol request going live or the proposal will become stale and unable to be executed.'
- 'The smart contracts take a 0.25% deduction per shield and unshield interaction which is then sent to the “treasury address”.' / 'Protocol deductions (0.25% on shield and unshield interactions) are sent directly on-chain to the treasury contract for that network.'

Context (not scored): there is no emergency pause; pausing also needs a vote. The Voting contract enforces its own execution window (no separate timelock); the documentation gives no numbers for it.

## 4. Axelar Network — Axelar Governance Controls the Gateway and the Interchain Token Service Through a 3-Day Timelock; the Deployment Config Lists the Previous Gateway Implementation

| Contract / Check | Address | Selector | Observation at `#26434786` |
| :--- | :--- | :--- | :--- |
| **AxelarGateway `implementation()` / `authModule()`** | `0x4F4495243837681061C4743b74B3eEdf548D56A5` | `authModule()` | `0x3d3C73E91B1b0C243f1437F2d8363b1D5B093BD0`, implementation `0x16C22cbDD77350b1AC88AdDA344F691c12f41960` (Sourcify match); the deployment config's `ethereum` entry lists implementation `0x99B5…4098` and auth module `0xE3B8…8AD0` |
| **AxelarGateway `governance()`** | `0x4F4495243837681061C4743b74B3eEdf548D56A5` | `governance()` | `AxelarServiceGovernance` `0x7Acbae6CBa67d78AAf69e47000884aE00F9B2525` (`governanceChain()` = "axelar") |
| **Governance `minimumTimeLockDelay()`** | `0x7Acbae6CBa67d78AAf69e47000884aE00F9B2525` | `minimumTimeLockDelay()` | `259200`s (3 days); `operator()` = `0xc8a8399c3D1207f4e109673be7047604737c1D56` (no contract code), which can run `executeOperatorProposal` immediately (no delay) for proposals Axelar governance approved |
| **InterchainTokenService `owner()`** | `0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C` | `owner()` | the governance contract; `paused()` = `false` |
| **Gateway `mintLimiter()`** | `0xCC940AE49C78F20E3F13F3cF37e996b98Ac3EC68` | `signerThreshold()` | `3` of `6` signer accounts |

Classification: **mixed** — `4` aligned baselines, `1` parameter delta.
- **aligned**: 'Axelar's contracts on other chains, such as the gateway, gas service and Interchain Token Service on EVM chains, are owned by governance contracts that only accept commands from Axelar governance.' / '"address": "0x7Acbae6CBa67d78AAf69e47000884aE00F9B2525",' / '"governanceAddress": "axelar10d07y265gmmuvt4z0w9aw880jnsr700j7v9daj",'
- **aligned**: '"minimumTimeDelay": 259200,' / '"operator": "0xc8a8399c3D1207f4e109673be7047604737c1D56",' / 'does the same, and can also approve proposals for an operator to execute without waiting for the timelock, so that changes can be coordinated with other network upgrades.'
- **aligned**: 'Axelar's contracts on other chains, such as the gateway, gas service and Interchain Token Service on EVM chains, are owned by governance contracts that only accept commands from Axelar governance.' / '0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C'
- **aligned**: '"threshold": 3,' / '"address": "0xCC940AE49C78F20E3F13F3cF37e996b98Ac3EC68",'
- **parameter delta**: the official deployment config (`axelar-contract-deployments`, `chains.ethereum.contracts.AxelarGateway`): '"implementation": "0x99B5FA03a5ea4315725c43346e55a6A6fbd94098"' / '"authModule": "0xE3B83f79Fbf01B25659f8A814945aB82186A8AD0"' On-chain the gateway now runs implementation `0x16C22cbDD77350b1AC88AdDA344F691c12f41960` with auth module `0x3d3C73E91B1b0C243f1437F2d8363b1D5B093BD0` (a stale listing, not a weaker control).

Context (not scored): the verified `AxelarServiceGovernance` source's `executeOperatorProposal` checks only the governance approval, not the timelock, so approved operator proposals have a `0`s execution floor. The gateway `pauser()` `0x72164D4448fe6cfA472946feDC71e83b4628B1aF` (no contract code) can pause and unpause without the timelock; the documentation fetched does not name it.

## 5. Bedrock (uniETH) — The uniETH Upgrade Admin and the 10% Fee Match the Documentation; the Documented Restaking Implementation Is Out of Date (converted from RPC-observed)

| Contract / Check | Address | Selector / slot | Observation at `#26434786` |
| :--- | :--- | :--- | :--- |
| **uniETH EIP-1967 admin** | `0xF1376bceF0f78459C0Ed0ba5ddce976F1ddF51F4` | slot `eip1967.proxy.admin` | `ProxyAdmin` `0xa5F2B6AB5B38b88Ba221741b3A189999b4c889C6`, `owner()` = Safe `0x3050620423f4dB43E1904815E898C466526387b8` (3-of-5, no guard); uniETH `owner()` = Safe `0xAeE017052DF6Ac002647229D58B786E380B9721A` (3-of-5) |
| **Staking `managerFeeShare()`** | `0x4beFa2aA9c305238AA3E0b5D17eB20C045269E9d` | `managerFeeShare()` | `100` per mille (10%); fee = rewards × share / 1000 in the verified source |
| **Restaking EIP-1967 implementation** | `0x3F4eaCeb930b0Edfa78a1DFCbaE5c5494E6e9850` | slot `eip1967.proxy.implementation` | `0x1e4D0A963953e7c08Fc7602B01e683547Fc4E518`, not the documented `0x9609Af0490b96D7AdD7EEa3554b1a944ee440262`; admin = the same ProxyAdmin |
| **EigenPod `podOwner()`** | `0x926720Ae39114D0e2043b79570A1e08f00D01cCE` | `podOwner()` | the restaking proxy `0x3F4eaCeb930b0Edfa78a1DFCbaE5c5494E6e9850` (`getTotalPods()` = `50`) |

Classification: **mixed** — `3` aligned baselines, `1` parameter delta.
- **aligned**: Bedrock's official repository (mainnet deployment): 'UNIVERSAL_ETH_ADDRESS: '0xF1376bceF0f78459C0Ed0ba5ddce976F1ddF51F4'' / 'PROXY_ADMIN: '0xa5F2B6AB5B38b88Ba221741b3A189999b4c889C6'' / 'Total supply of uniETH: https://etherscan.io/token/0xF1376bceF0f78459C0Ed0ba5ddce976F1ddF51F4'
- **aligned**: `docs.bedrock.technology` (fees): '10% commission on block rewards, transaction and MEV fees.' / 'Total ETH staked: https://etherscan.io/address/0x4beFa2aA9c305238AA3E0b5D17eB20C045269E9d'
- **parameter delta**: `docs.bedrock.technology` (uniETH contracts): 'Restaking proxy contract: https://etherscan.io/address/0x3f4eaceb930b0edfa78a1dfcbae5c5494e6e9850' / 'Restaking implementation: https://etherscan.io/address/0x9609af0490b96d7add7eea3554b1a944ee440262#code' On-chain the restaking proxy runs `0x1e4D0A963953e7c08Fc7602B01e683547Fc4E518` (an out-of-date listing after an upgrade, not a weaker control).
- **aligned**: 'EigenPod Manager a.k.a restaking contract is that securely manages eigenpod contract automatically, it enables all the asset management like unstake, rewards allocation etc.' / 'EigenPod: https://etherscan.io/address/0x926720Ae39114D0e2043b79570A1e08f00D01cCE' / 'RESTAKING_ADDRESS: '0x3F4eaCeb930b0Edfa78a1DFCbaE5c5494E6e9850'' / 'EIGENPOD_ADDRESS: '0x926720Ae39114D0e2043b79570A1e08f00D01cCE''

Context (not scored): no timelock sits on either Safe (no modules, no guard), and the documentation claims none. Safe `0xAeE017052DF6Ac002647229D58B786E380B9721A` also holds the restaking contract's `DEFAULT_ADMIN_ROLE`, which can upgrade its EigenPod beacon outside the ProxyAdmin. The published RPC-observed record's slug and primary contract (the uniETH token proxy) are kept; its label and controller are corrected.

## 6. Safe Smart Account (v1.4.1 Singleton) — The Singletons Are Locked and Their Code Matches Safe's Official Registry (converted from RPC-observed)

| Contract / Check | Address | Selector | Observation at `#26434786` |
| :--- | :--- | :--- | :--- |
| **Safe singleton `getThreshold()`** | `0x41675C099F32341bf84BFc5382aF534df5C7461a` | `getThreshold()` | `1` with `0` owners, so `setup()` (which requires threshold `0`) can never run; `VERSION()` = "1.4.1" |
| **Safe singleton code** | `0x41675C099F32341bf84BFc5382aF534df5C7461a` | `VERSION()` | `keccak256(runtime code)` = `0x1fe2df852ba3299d6534ef416eefa406e56ced995bca886ab7a553e6d0c5e1c4`; no proxy (both EIP-1967 slots `0`) |
| **SafeProxyFactory code** | `0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67` | slot `eip1967.proxy.implementation` | `0` (not a proxy); `keccak256(runtime code)` = `0x50c3cdc4074750a7a974204a716c999edd37482f907608d960b2b025ee0b3317`; no owner or admin in the verified source |
| **SafeL2 singleton** | `0x29fcB43b46531BcA003ddC8FCB67FFE91900C762` | `getThreshold()` | `1` with `0` owners (locked); `keccak256(runtime code)` = `0xb1f926978a0f44a2c0ec8fe822418ae969bd8c3f18d61e5103100339894f81ff` |

Classification: **aligned baseline** (4 records).
- `docs.safe.global` and the official `safe-deployments` registry (pinned commit): 'contracts. It cannot be initialized.' / 'As a singleton contract, it cannot be used directly as a Safe account but only through a Safe Proxy contract.'
- '"address": "0x41675C099F32341bf84BFc5382aF534df5C7461a",' / '"codeHash": "0x1fe2df852ba3299d6534ef416eefa406e56ced995bca886ab7a553e6d0c5e1c4"' / '"1": "canonical",' / 'You must share your singleton contract deployment addresses in the official public registry.'
- '"address": "0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67",' / '"codeHash": "0x50c3cdc4074750a7a974204a716c999edd37482f907608d960b2b025ee0b3317"' / '"1": "canonical",' / 'The Safe proxy factory contract provides a simple way to create a new proxy contract pointing to a singleton and executing a setup function in the newly deployed proxy all in one transaction.'
- '"address": "0x29fcB43b46531BcA003ddC8FCB67FFE91900C762",' / '"codeHash": "0xb1f926978a0f44a2c0ec8fe822418ae969bd8c3f18d61e5103100339894f81ff"' / '"1": "canonical",' / 'contracts. It cannot be initialized.'

Context (not scored): each Safe account's owners can migrate that account to another singleton; the singleton itself has no upgrade path. Bedrock's two Safes use this singleton (liveness).

## 7. Section 3.4 Dual Chain + Documentation Re-Scan (Part C) — 0 of 3 Reconciled or Drifted

Every scored value of three of the oldest non-bounty records, read at its original pinned block (archive pair) and at `#26434786` (`audits/sprint-25/drift-rescan-26434786.json`), and the documented statement each record compares against, re-fetched (HTTP 200).

| Record | Baseline | Checks | Chain | Documentation | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fx-protocol-v2-treasury-admin` | Sprint 2 `#26400152` | 17 | unchanged | unchanged | persists |
| `morpho-blue-singleton-owner` | Sprint 3 `#26401070` | 1 | unchanged | unchanged | still aligned |
| `maple-v2-syrup-ppm-admin` | Sprint 6 `#26401540` | 5 | unchanged | unchanged | persists |

- **f(x) Protocol v2**: the OpsSafe (6-of-9) and EmergencySafe (3-of-4) still hold `DEFAULT_ADMIN_ROLE` directly on all four ProtocolTreasury proxies, not the 3-day Timelock; the documentation still describes a mandatory 3-day timelock. The parameter delta persists.
- **Morpho Blue**: `owner()` is still the documented morpho.eth multisig. Still aligned. (Context: the documentation calls it a 5/9 multisig; on-chain it is 6-of-10 at both blocks, reported for a future record, not scored here.)
- **Maple (syrup)**: the Pool Permission Manager's proxy admin is still the 4-of-7 DAO Safe, not the GovernorTimelock (3-day default delay) the documentation describes. The parameter delta persists.

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations, verified-source references and quoted public documentation (documentation snapshots fetched `2026-11-17`). Checks are sampled getters, role checks, proxy slots and Safe parameters at the finalized pins; role holders that cannot be enumerated with `eth_call` are stated as checked candidates only.
