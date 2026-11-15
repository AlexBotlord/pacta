// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Ethereum Attestation Service `Attestation` struct, field order as in `eas-contracts` (Common.sol).
struct Attestation {
    bytes32 uid; // A unique identifier of the attestation.
    bytes32 schema; // The unique identifier of the schema.
    uint64 time; // The time when the attestation was created (Unix timestamp).
    uint64 expirationTime; // The time when the attestation expires (Unix timestamp), 0 = never.
    uint64 revocationTime; // The time when the attestation was revoked (Unix timestamp), 0 = not revoked.
    bytes32 refUID; // The UID of the related attestation.
    address recipient; // The recipient of the attestation.
    address attester; // The attester / sender of the attestation.
    bool revocable; // Whether the attestation is revocable.
    bytes data; // Custom attestation data.
}

/// @title IEAS (read subset)
/// @notice EAS on Base (and every OP-Stack chain) is the predeploy at 0x4200000000000000000000000000000000000021.
///         `getAttestation` returns an all-zero struct for an unknown UID.
interface IEAS {
    function getAttestation(bytes32 uid) external view returns (Attestation memory);
}
