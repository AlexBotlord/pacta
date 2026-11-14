// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IPactaCommitmentRegistry
/// @notice Read-only view of the deployed PactaCommitmentRegistry on Base Mainnet
///         (0x35D21Bb4Df6586FE7759b5e57263ffeB3e1fd872; source: contracts/PactaCommitmentRegistry.sol in
///         github.com/Fractal-Neurons/pacta). The registry stores one block-pinned verification receipt per Pacta Sprint;
///         `sprintVerifications` is the compiler-generated getter of `mapping(uint16 => SprintVerification)`, so it returns
///         the struct fields as a tuple in declaration order.
interface IPactaCommitmentRegistry {
    function sprintVerifications(uint16 sprintId)
        external
        view
        returns (
            uint64 chainId,
            uint64 blockNumber,
            bytes32 blockHash,
            uint8 verifiedCount,
            uint8 driftCount,
            bytes32 summarySha256,
            uint32 githubPrNumber
        );

    /// @notice Tier 2 attester EOA (pacta.base.eth, 0xcA4E2ff22B69A7284210c47BdeE21Aac1269da09 at deployment); rotatable by
    ///         the registry's treasury role. Pacta's Base EAS attestations are made by this address.
    function attester() external view returns (address);
}
