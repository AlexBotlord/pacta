# Sprint 17 Protocol Commitment Summary — Block `26418060`

- **Ethereum Mainnet pin**: `26418060` (`0x1931b8c`), canonical block hash `0x8914f5134a4488a812b61c1c7f479c3082d80f6fbe2f181abb9e5ef4ff973f3c`, timestamp `2026-11-15 04:38:47 UTC` (`1794717527`)
- **Base Mainnet pin** (Steakhouse USDC records only): `57635450` (`0x36f727a`), canonical block hash `0x78ddbdca540b630c823e1c79dcadbfc25dd957c60d1396f4c6b60f11f67a164f`, timestamp `2026-11-15 04:37:45 UTC` (`1794717465`)
- **Scanner**: `pacta-claude@dri.network`. Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode`, pinned by block hash (EIP-1898 `requireCanonical: true`) and replayed on two independent RPCs per chain with identical results: Ethereum `gateway.tenderly.co/public/mainnet` + `rpc.mevblocker.io`; Base `mainnet.base.org` + `base.drpc.org`
- **Result**: `7` records — `verifiedCount = 6` (`5` aligned baselines + `1` protective delta), `driftCount = 1` (parameter delta)
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above)

## 1. M0 Protocol (`$M`) — Immutable `MToken`, Docs-Listed TTG Governors

| Contract / Check | Address | Selector / Slot | Observation at `#26418060` |
| :--- | :--- | :--- | :--- |
| **`MToken` EIP-1967 implementation / admin slots** | `0x866A2BF4E572CbcF37D5071A7a58503Bfb36be1b` | `0x3608…2bbc` / `0xb531…6103` | both `0` — no EIP-1967 proxy; `name() = "M by M^0"`, `totalSupply() = 249,955,861.65 M`, `ttgRegistrar()` = `0x119FbeeDD4F4f4298Fb59B720d5654442b81ae2c`, `minterGateway()` = `0xf7f9638cb444D65e5A40bF5ff98ebE4ff319F04E` |
| **`Registrar.standardGovernor()`** | `0x119FbeeDD4F4f4298Fb59B720d5654442b81ae2c` | `standardGovernor()` | `0xB024aC5a7c6bC92fbACc8C3387E628a07e1Da016`; `emergencyGovernor()` = `0x886d405949F709bC3f4451491bDd07ff51Cdf90A`; `zeroGovernor()` = `0xa0DAFaEEA4A1d44534e1b9227e19CAE6358b80FE`; Registrar EIP-1967 implementation slot `0` |

Classification: **aligned baseline** (both). `docs.m0.org/raw/protocol/m-token.md`: "The `MToken` contract itself is designed to be immutable, meaning its core logic cannot be upgraded directly." The three governors equal the StandardGovernor / EmergencyGovernor / ZeroGovernor addresses listed in `docs.m0.org/raw/resources/addresses/m0-platform.md`.

## 2. Falcon Finance (`USDf` / `sUSDf`) — Instant Unstaking

| Contract / Check | Address | Selector | Observation at `#26418060` |
| :--- | :--- | :--- | :--- |
| **`sUSDf.cooldownDuration()`** | `0xc8CF6D7991f15525488b2A83Df53468D682Ba4B0` | `cooldownDuration()` | `0`; `asset()` = USDf `0xFa2B947eEc368f42195f24F36d2aF29f7c24CeC2`; `totalSupply()` = `33,273,012.15 sUSDf` (USDf `1,516,215,860.42`) |

Classification: **aligned baseline**. `docs.falcon.finance/mechanism/redemptions/`: "This is not to be confused with unstaking, where users can unstake their sUSDf and receive USDf in return immediately."
Context (not compared with documentation): USDf and sUSDf are EIP-1967 proxies (implementations `0x3aDf34C09DAC24E4BAeFB1b1df4C2992edC2b789`, `0x0D132bEE412E6619a4863AEEdad97541BfDa3F34`) whose admins `0x3Ef1127Fdf81B553066daE0FaEA58785A2AA6E14` / `0x16a2605C026BFe4f4B7f4471933714D9b2149AcE` both return `owner()` = Safe `0x1E482B60bf19Cb1cc859389e0eA3DED153f16Bd7` (`getThreshold() = 4` of `6` owners).

## 3. Solv Protocol (`SolvBTC`) — Safe Ownership; Upgrades Already Behind a 3-Day Timelock

| Contract / Check | Address | Selector | Observation at `#26418060` |
| :--- | :--- | :--- | :--- |
| **`SolvBTC.owner()`** | `0x7A56E1C57C7475CCf742a1832B028F0456652F97` | `0x8da5cb5b` | Safe `0x0c2Bc4d2698820e12E6eBe863E7b9E2650CD5b7D` (`getThreshold() = 3` of `5` owners); `name() = "Solv BTC"`, `totalSupply() = 2,397.43 SolvBTC` |
| **Upgrade path** | beacon `0xFc335FdA7E6a33329A83F4d5F578eC7d8A43DC4A` | EIP-1967 beacon slot `0xa3f0…3d50` | `implementation()` = `0xA4b6cf2BAaA235ab7Fe10EADB84b82460165B38F`; beacon `owner()` = `0x443628281E4f3E5b5A5D029B9a0D13900ae41578`, whose `admin()` = `0xfd4B809AD88db6Ca9dbB295A4B9d23bB0093f497` (`pendingAdmin() = 0`) |
| **`TimelockController.getMinDelay()`** | `0xfd4B809AD88db6Ca9dbB295A4B9d23bB0093f497` | `0xf27a0c92` | `259200`s (`3` days); the 3-of-5 Safe holds `PROPOSER_ROLE`, `EXECUTOR_ROLE` and `CANCELLER_ROLE`; the timelock holds its own `DEFAULT_ADMIN_ROLE` |

Classification: `owner()` **aligned baseline** — Solv docs (`docs.solv.finance/llms-full.txt`): "The permission model for updating business parameters (such as adding supported tokens, setting Oracle address, etc.) uses OpenZeppelin’s **Ownable** implementation, with the permission address being a Gnosis Safe multi-signature address." Upgrade timelock **protective delta** — the same docs: "The admin privileges for upgrades are assigned to a Gnosis Safe multi-signature address … The timelock mechanism will be added to further enhance security by introducing a delay between the upgrade proposal and execution." On-chain, the beacon owner is already administered by a 3-day `TimelockController`. The beacon owner's admin semantics are read from its `admin()` / `pendingAdmin()` getters; its source is not reviewed in this summary.

## 4. Steakhouse USDC MetaMorpho Vault (Base) — 7-Day Timelock; Guardian Is Not an On-Chain Multisig

| Contract / Check | Address | Selector | Observation at Base `#57635450` |
| :--- | :--- | :--- | :--- |
| **`timelock()`** | `0xbeeF010f9cb27031ad51e3333f9aF9C6B1228183` | `timelock()` | `604800`s (`7` days); `name() = "Steakhouse USDC"`, `symbol() = "steakUSDC"`, `asset()` = USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, `MORPHO()` = `0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb`, `totalAssets() = 102,512,832.83 USDC`; `owner()` = Safe `0x0A0e559bc3b0950a7e448F0d4894db195b9cf8DD` (`5` of `10`), `curator()` = Safe `0x827e86072B06674a077f592A531dcE4590aDeCdB` (`3` of `9`) |
| **`guardian()`** | `0xbeeF010f9cb27031ad51e3333f9aF9C6B1228183` | `guardian()` | `0x9e0FdDDa790651E6a05CD2dE69e624B94C04eAf5`: `eth_getCode = 0x` on Base `#57635450` and on Ethereum `#26418060`; `eth_getTransactionCount = 0` on Base |

Classification: `timelock()` **aligned baseline** — Steakhouse docs (`steakhouse.financial/docs/llms-full.txt`): "Steakhouse vaults 7-day timelocks (above the minimum, protocol-enforced 3-day timelock)". `guardian()` **parameter delta** — the same docs: Prime Vaults use "a 7-day action timelock enforced by an Aragon DAO guardian", and "Our Sentinel/Guardian roles are typically onchain Aragon multisigs that any vault depositor can use. When they're not, it's usually because a commercial distribution partner has taken on that role and intends to monitor it if needed." The docs list this vault (Prime Instant, Base, Morpho v1) with partner Coinbase. On-chain, the guardian has no contract code, so it is not an on-chain Aragon (or Safe) multisig; who holds it cannot be determined from chain state.

> **Scope note**: this summary reports only non-exploitable baseline state, parameter observations and quoted public documentation (documentation snapshots fetched `2026-11-15`). It does not certify protocol-wide immutability, exhaustive authority coverage or exploitability. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to official protocol security teams.
