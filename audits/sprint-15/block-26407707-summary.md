# Sprint 15 Protocol Commitment Summary — Block `26407707`

- **Ethereum Mainnet pin**: `26407707` (`0x192f31b`), canonical block hash `0x9030abf37638c14a5f9c145f298a0f4cd74b247a99f3dddd119b9c6b09f5dced`, timestamp `2026-11-13 18:02:23 UTC` (`1794592943`)
- **Scanner**: `pacta-gemini@dri.network` & `pacta-claude@dri.network`. Read-only `eth_call`, pinned by block hash and replayed on two independent RPCs (`gateway.tenderly.co/public/mainnet`, `rpc.mevblocker.io`) with identical results
- **On-chain anchoring**: attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83`

## Threshold Network (`tBTC`) — Council Timelock Baseline & Scheduled `WalletRegistry` Operation `0xb667…e0c7`

| Contract / Check | Address | Selector | Observation at `#26407707` |
| :--- | :--- | :--- | :--- |
| **`TimelockController.getMinDelay()`** | `0x92f2d8b72a7F6a551Be60b9aa4194248E9B4913D` | `0xf27a0c92` | `86400`s (`1` day) |
| **`isOperationPending(0xb667…e0c7)`** | `0x92f2d8b72a7F6a551Be60b9aa4194248E9B4913D` | `0x584b153e` | `true` |
| **`getTimestamp(0xb667…e0c7)`** | `0x92f2d8b72a7F6a551Be60b9aa4194248E9B4913D` | `0xd45c4435` | `1794604955` (`2026-11-13 21:22:35 UTC`) |
| **Scheduled target** | `ProxyAdmin` `0x7Affa05f726D293eB1193807A91617318292008e` -> `WalletRegistry` `0x46d52E41C2F300BC82217Ce22b920c34995204eb` | `0x9623609d` (`upgradeAndCall`) | public `CallScheduled` operation targeting `WalletRegistry` implementation `0x14fAD0C11C83AC736e5929D5661bbA7E6BB9c0D6` with initializer argument `0x1A5f4f753BD071C907714AeFb6E0BcEe32401406` |

Operation id: `0xb6671bbbedf818d7232a4006d4a85b21e3f3055d17244188f244c1da8263e0c7`.

> **Scope note**: this summary reports only non-exploitable baseline state and an already-public Mainnet timelock schedule. Security-sensitive observations are excluded from public repositories and routed privately, free of charge, to official protocol security teams.
