// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IMorphoVaultV2Caps
/// @notice Morpho Vault V2 cap getters (morpho-org/vault-v2). Cap ids are `keccak256(idData)`; caps change through
///         `increaseAbsoluteCap` (timelocked, curator submits) and `decreaseAbsoluteCap` (curator or sentinel).
interface IMorphoVaultV2Caps {
    function absoluteCap(bytes32 id) external view returns (uint256);
}

/// @title IEulerEVaultCaps
/// @notice Euler Vault Kit (EVK) governance getter. Caps are 16-bit `AmountCap` values: 0 means "no cap" (unlimited);
///         otherwise the amount is 10 ** (raw & 63) * (raw >> 6) / 100.
interface IEulerEVaultCaps {
    function caps() external view returns (uint16 supplyCap, uint16 borrowCap);
}
