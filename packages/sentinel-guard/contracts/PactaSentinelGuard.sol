// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IPactaCommitmentRegistry} from "./interfaces/IPactaCommitmentRegistry.sol";
import {IEAS, Attestation} from "./interfaces/IEAS.sol";
import {IMorphoVaultV2Caps, IEulerEVaultCaps} from "./interfaces/IVaultCaps.sol";

/// @title PactaSentinelGuard
/// @notice Zero-dependency, non-custodial tripwire for vault curators: it refuses a cap INCREASE (a new or larger
///         collateral allocation) unless the collateral's Pacta control-plane attestation is healthy, and it NEVER
///         blocks a cap decrease or zeroing, so curators and sentinels can always de-risk during an incident.
/// @dev    Holds no funds and moves nothing; every check is a view. Integrations:
///         - Morpho Vault V2: `checkMorphoV2AbsoluteCapIncrease(vault, collateral, idData, newCap)` before a curator submits
///           `increaseAbsoluteCap` (e.g. from a Safe guard / Zodiac module or an off-chain Sentinel bot).
///         - Euler EVK: `checkEulerCapsChange(evault, collateral, newSupplyCap, newBorrowCap)` before `setCaps`.
///         - Any vault factory (Veda BoringVault, Lagoon, Upshift, Mellow): `validateCapIncrease(collateral, cur, next)`.
///         Health, against the deployed contracts:
///         1. the curator bound the collateral to a Pacta Sprint id and its Base EAS attestation UID;
///         2. PactaCommitmentRegistry (Base, 0x35D21Bb4Df6586FE7759b5e57263ffeB3e1fd872) has that Sprint recorded with
///            driftCount == 0 (the receipt covers the whole Sprint, so any drift in it blocks increases);
///         3. the EAS attestation (Base predeploy 0x4200000000000000000000000000000000000021) exists, uses the Pacta schema,
///            was made by the registry's current attester, is not revoked or expired, is younger than `maxStaleness`,
///            and its data (sprintId, blockHash, driftCount, summarySha256) matches the registry receipt.
contract PactaSentinelGuard {
    enum Health {
        Healthy,
        Unbound,
        NotRecorded,
        Drift,
        MissingAttestation,
        WrongSchema,
        WrongAttester,
        Revoked,
        Expired,
        Stale,
        DataMismatch
    }

    struct Binding {
        uint16 sprintId;
        bytes32 easUid;
    }

    /// @notice keccak256(abi.encodePacked(schema, address(0), true)) of the Pacta Sprint schema registered on Base EAS.
    bytes32 public constant PACTA_SCHEMA_UID = 0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83;
    uint256 public constant DEFAULT_MAX_STALENESS = 30 days;
    uint256 public constant MIN_MAX_STALENESS = 1 days;
    uint256 public constant MAX_MAX_STALENESS = 365 days;

    IPactaCommitmentRegistry public immutable registry;
    IEAS public immutable eas;
    /// @notice The only address that can bind collateral to a Sprint / attestation (immutable; no owner, no upgrade).
    address public immutable curator;
    uint256 public immutable maxStaleness;

    mapping(address collateral => Binding) public bindings;

    event CollateralBound(address indexed collateral, uint16 indexed sprintId, bytes32 indexed easUid);
    event CollateralUnbound(address indexed collateral);

    error ZeroAddress();
    error NotCurator();
    error InvalidBinding();
    error MaxStalenessOutOfBounds(uint256 maxStaleness);
    error UnhealthyAttestation(address collateral, Health health);

    /// @param maxStaleness_ 0 selects DEFAULT_MAX_STALENESS (30 days); otherwise 1 to 365 days.
    constructor(address registry_, address eas_, address curator_, uint256 maxStaleness_) {
        if (registry_ == address(0) || eas_ == address(0) || curator_ == address(0)) revert ZeroAddress();
        uint256 s = maxStaleness_ == 0 ? DEFAULT_MAX_STALENESS : maxStaleness_;
        if (s < MIN_MAX_STALENESS || s > MAX_MAX_STALENESS) revert MaxStalenessOutOfBounds(maxStaleness_);
        registry = IPactaCommitmentRegistry(registry_);
        eas = IEAS(eas_);
        curator = curator_;
        maxStaleness = s;
    }

    modifier onlyCurator() {
        if (msg.sender != curator) revert NotCurator();
        _;
    }

    // ---- bindings (curator) ----

    function bind(address collateral, uint16 sprintId, bytes32 easUid) external onlyCurator {
        if (collateral == address(0) || sprintId == 0 || easUid == bytes32(0)) revert InvalidBinding();
        bindings[collateral] = Binding(sprintId, easUid);
        emit CollateralBound(collateral, sprintId, easUid);
    }

    /// @notice Removing a binding can only make increases stricter (an unbound collateral is unhealthy).
    function unbind(address collateral) external onlyCurator {
        delete bindings[collateral];
        emit CollateralUnbound(collateral);
    }

    // ---- health ----

    /// @notice The collateral's attestation health; never reverts for a malformed attestation payload.
    function attestationHealth(address collateral) public view returns (Health) {
        Binding memory b = bindings[collateral];
        if (b.sprintId == 0) return Health.Unbound;
        (, , bytes32 blockHash, , uint8 driftCount, bytes32 summarySha256, ) = registry.sprintVerifications(b.sprintId);
        if (blockHash == bytes32(0)) return Health.NotRecorded;
        if (driftCount != 0) return Health.Drift;
        Attestation memory a = eas.getAttestation(b.easUid);
        if (a.uid == bytes32(0) || a.uid != b.easUid) return Health.MissingAttestation;
        if (a.schema != PACTA_SCHEMA_UID) return Health.WrongSchema;
        if (a.attester != registry.attester()) return Health.WrongAttester;
        if (a.revocationTime != 0) return Health.Revoked;
        if (a.expirationTime != 0 && a.expirationTime <= block.timestamp) return Health.Expired;
        if (a.time > block.timestamp || block.timestamp - a.time > maxStaleness) return Health.Stale;
        try this.decodeAttestationData(a.data) returns (uint16 sId, bytes32 bh, uint8 dc, bytes32 sha) {
            if (sId != b.sprintId || bh != blockHash || dc != 0 || sha != summarySha256) return Health.DataMismatch;
        } catch {
            return Health.DataMismatch;
        }
        return Health.Healthy;
    }

    /// @notice Decodes the Pacta Sprint attestation payload
    ///         abi.encode(uint16 sprintId, uint64 chainId, uint64 blockNumber, bytes32 blockHash, uint8 verifiedCount,
    ///         uint8 driftCount, bytes32 summarySha256, string prURI) and returns the fields the guard cross-checks.
    function decodeAttestationData(bytes calldata data)
        external
        pure
        returns (uint16 sprintId, bytes32 blockHash, uint8 driftCount, bytes32 summarySha256)
    {
        (sprintId, , , blockHash, , driftCount, summarySha256, ) =
            abi.decode(data, (uint16, uint64, uint64, bytes32, uint8, uint8, bytes32, string));
    }

    function requireHealthyAttestation(address collateral) public view {
        Health h = attestationHealth(collateral);
        if (h != Health.Healthy) revert UnhealthyAttestation(collateral, h);
    }

    // ---- cap checks: increases need a healthy attestation; decreases and zeroing always pass ----

    function validateCapIncrease(address collateral, uint256 currentCap, uint256 newCap) public view {
        if (newCap <= currentCap) return;
        requireHealthyAttestation(collateral);
    }

    /// @notice Morpho Vault V2: check `increaseAbsoluteCap(idData, newAbsoluteCap)` against the vault's current cap.
    function checkMorphoV2AbsoluteCapIncrease(address vault, address collateral, bytes calldata idData, uint256 newAbsoluteCap)
        external
        view
    {
        validateCapIncrease(collateral, IMorphoVaultV2Caps(vault).absoluteCap(keccak256(idData)), newAbsoluteCap);
    }

    /// @notice Euler EVK: check `setCaps(newSupplyCap, newBorrowCap)`. AmountCap 0 means unlimited, so setting a cap to 0
    ///         is an increase (to unlimited) and needs a healthy attestation, while lowering a cap never does.
    function checkEulerCapsChange(address evault, address collateral, uint16 newSupplyCap, uint16 newBorrowCap) external view {
        (uint16 supplyCap, uint16 borrowCap) = IEulerEVaultCaps(evault).caps();
        if (resolveEulerAmountCap(newSupplyCap) > resolveEulerAmountCap(supplyCap)
            || resolveEulerAmountCap(newBorrowCap) > resolveEulerAmountCap(borrowCap)) {
            requireHealthyAttestation(collateral);
        }
    }

    /// @notice EVK AmountCap decoding (AmountCapLib.resolve): 0 -> type(uint256).max, else 10 ** (raw & 63) * (raw >> 6) / 100.
    function resolveEulerAmountCap(uint16 raw) public pure returns (uint256) {
        if (raw == 0) return type(uint256).max;
        unchecked {
            return 10 ** (uint256(raw) & 63) * (uint256(raw) >> 6) / 100;
        }
    }
}
