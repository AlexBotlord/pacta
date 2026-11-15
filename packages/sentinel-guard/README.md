# `PactaSentinelGuard` — cap-increase tripwire for vault curators

`PactaSentinelGuard.sol` is an MIT, zero-dependency, non-custodial Solidity `^0.8.24` adapter. It **refuses a cap increase** (a new or larger collateral allocation) unless the collateral's Pacta control-plane attestation is healthy. It **never blocks a cap decrease or zeroing**, so curators and sentinels can always de-risk during an incident.

It holds no funds and moves nothing. Every check is a `view`, and the contract has no owner and no upgrade path. The `curator` (immutable) is the only address that can bind a collateral to its attestation.

## What "healthy" means against the deployed contracts

`attestationHealth(collateral)` returns `Healthy` only if all of the following hold:

1. **Binding.** The curator bound the collateral to a Pacta Sprint id and that Sprint's Base EAS attestation UID with `bind(collateral, sprintId, easUid)`. The published values are `onchain_anchoring.sprint_eas_attestations` in `https://pacta.wtf/api/v1/index.json`, or `sprints` / `baseEasUids` per protocol in `https://pacta.wtf/api/v1/protocols.json`.
2. **Registry receipt.** `PactaCommitmentRegistry` on Base, `0x35D21Bb4Df6586FE7759b5e57263ffeB3e1fd872`, has the Sprint recorded (`blockHash != 0`) with `driftCount == 0`.
   - The deployed registry stores one receipt per Sprint, so drift anywhere in that Sprint blocks increases. This is the conservative direction.
3. **EAS attestation.** The attestation at the EAS predeploy `0x4200000000000000000000000000000000000021` must:
   - exist with the bound UID;
   - use the Pacta schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83`;
   - be made by the registry's current `attester()` (`pacta.base.eth`, `0xcA4E2ff22B69A7284210c47BdeE21Aac1269da09` at deployment);
   - be neither revoked nor expired;
   - be no older than `maxStaleness`. The default is 30 days; the constructor accepts 1 to 365 days and the value is immutable.
4. **Payload cross-check.** The attestation data, `abi.encode(uint16 sprintId, uint64 chainId, uint64 blockNumber, bytes32 blockHash, uint8 verifiedCount, uint8 driftCount, bytes32 summarySha256, string prURI)`, must match the registry receipt: same sprint id, same block hash, same summary hash, and `driftCount == 0`.

Otherwise the result is one of these states, and a cap increase reverts with `UnhealthyAttestation(collateral, health)`:

| State | Meaning |
|---|---|
| `Unbound` | the collateral has no binding |
| `NotRecorded` | the registry has no receipt for the Sprint |
| `Drift` | the registry receipt has `driftCount > 0` |
| `MissingAttestation` | no attestation exists for the bound UID |
| `WrongSchema` | the attestation uses a schema other than Pacta's |
| `WrongAttester` | the attestation was not made by the registry's current attester |
| `Revoked` | the attestation was revoked |
| `Expired` | the attestation has passed its expiration time |
| `Stale` | the attestation is older than `maxStaleness` (or future-dated) |
| `DataMismatch` | the payload does not match the registry receipt, or is malformed |

## Integrations

**Morpho Vault V2**

```solidity
guard.checkMorphoV2AbsoluteCapIncrease(vault, collateral, idData, newAbsoluteCap);
```

Run this before a curator submits `increaseAbsoluteCap(idData, newAbsoluteCap)`, for example from a Safe transaction guard, a Zodiac module, or an off-chain Sentinel bot. It reads `absoluteCap(keccak256(idData))`. `decreaseAbsoluteCap` and sentinel `revoke` are never gated.

**Euler EVK**

```solidity
guard.checkEulerCapsChange(evault, collateral, newSupplyCap, newBorrowCap);
```

Run this before `setCaps`. EVK `AmountCap` values are resolved the way EVK does it: `0` means unlimited, so setting a cap to `0` counts as an increase. Lowering a cap never needs the attestation.

**Any vault factory** (Veda `BoringVault`, Lagoon, Upshift, Mellow, or your own manager)

```solidity
guard.validateCapIncrease(collateral, currentCap, newCap);
```

This returns when `newCap <= currentCap` and otherwise calls `requireHealthyAttestation(collateral)`.

**Off-chain monitoring.** Poll `attestationHealth(collateral)`. It never reverts on a malformed attestation payload.

The integration guide is at `https://pacta.wtf/integrations/vault-factories/`. Per-protocol status, badges and pinned surfaces are at `https://pacta.wtf/api/v1/protocols.json`.

## Test (offline)

```bash
forge test --use <path to solc 0.8.24> --offline
```

The suite has 20 tests, including 2 fuzz properties:
- decreases, equal caps and zeroing never revert, whatever the attestation state;
- increases always revert when the attestation is unhealthy.

It covers every health state, attester rotation, the Morpho Vault V2 absolute-cap path, and EVK `AmountCap` resolution. It uses no forge-std: cheatcodes are declared in the test file.
