// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {PactaSentinelGuard} from "../contracts/PactaSentinelGuard.sol";
import {Attestation} from "../contracts/interfaces/IEAS.sol";

/// @dev Foundry cheatcodes used here (signatures as in Foundry's Vm.sol); no forge-std, runs fully offline.
interface Vm {
    function prank(address msgSender) external;
    function warp(uint256 newTimestamp) external;
    function expectRevert(bytes calldata revertData) external;
    function expectRevert(bytes4 revertData) external;
}

// ---- mocks: the deployed registry's getter shape, EAS getAttestation, Morpho Vault V2 / Euler EVK cap getters ----
contract MockRegistry {
    struct Rec {
        uint64 chainId;
        uint64 blockNumber;
        bytes32 blockHash;
        uint8 verifiedCount;
        uint8 driftCount;
        bytes32 summarySha256;
        uint32 githubPrNumber;
    }

    mapping(uint16 => Rec) internal recs;
    address public attester = 0xcA4E2ff22B69A7284210c47BdeE21Aac1269da09;

    function setRecord(uint16 id, bytes32 blockHash, uint8 driftCount, bytes32 sha) external {
        recs[id] = Rec(1, 23_800_000, blockHash, 3, driftCount, sha, 7);
    }

    function setAttester(address a) external {
        attester = a;
    }

    function sprintVerifications(uint16 id) external view returns (uint64, uint64, bytes32, uint8, uint8, bytes32, uint32) {
        Rec memory r = recs[id];
        return (r.chainId, r.blockNumber, r.blockHash, r.verifiedCount, r.driftCount, r.summarySha256, r.githubPrNumber);
    }
}

contract MockEAS {
    mapping(bytes32 => Attestation) internal atts;

    function set(Attestation memory a, bytes32 key) external {
        atts[key] = a;
    }

    function getAttestation(bytes32 uid) external view returns (Attestation memory) {
        return atts[uid];
    }
}

contract MockMorphoVaultV2 {
    mapping(bytes32 => uint256) public absoluteCap;

    function setCap(bytes memory idData, uint256 cap) external {
        absoluteCap[keccak256(idData)] = cap;
    }
}

contract MockEVault {
    uint16 internal s;
    uint16 internal b;

    function setCaps(uint16 s_, uint16 b_) external {
        s = s_;
        b = b_;
    }

    function caps() external view returns (uint16, uint16) {
        return (s, b);
    }
}

contract PactaSentinelGuardTest {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    bytes32 internal constant SCHEMA = 0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83;
    address internal constant ATTESTER = 0xcA4E2ff22B69A7284210c47BdeE21Aac1269da09;
    address internal constant CURATOR = address(0xC0FFEE);
    address internal constant COLLATERAL = address(0xC011A7);
    uint16 internal constant SPRINT = 12;
    bytes32 internal constant UID = keccak256("pacta sprint 12 attestation");
    bytes32 internal constant BLOCK_HASH = keccak256("block 23800000");
    bytes32 internal constant SHA = keccak256("sprint 12 summary");
    uint256 internal constant T0 = 1_794_600_000;

    MockRegistry internal reg;
    MockEAS internal eas;
    PactaSentinelGuard internal guard;

    function setUp() public {
        vm.warp(T0);
        reg = new MockRegistry();
        eas = new MockEAS();
        guard = new PactaSentinelGuard(address(reg), address(eas), CURATOR, 0);
        reg.setRecord(SPRINT, BLOCK_HASH, 0, SHA);
        eas.set(_att(UID, SCHEMA, uint64(T0 - 1 days), 0, 0, ATTESTER, _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        vm.prank(CURATOR);
        guard.bind(COLLATERAL, SPRINT, UID);
    }

    // ---- helpers ----
    function _data(uint16 id, bytes32 bh, uint8 drift, bytes32 sha) internal pure returns (bytes memory) {
        return abi.encode(id, uint64(1), uint64(23_800_000), bh, uint8(3), drift, sha, "https://github.com/Fractal-Neurons/pacta/pull/7");
    }

    function _att(bytes32 uid, bytes32 schema, uint64 time, uint64 exp, uint64 rev, address attester, bytes memory data)
        internal
        pure
        returns (Attestation memory a)
    {
        a.uid = uid;
        a.schema = schema;
        a.time = time;
        a.expirationTime = exp;
        a.revocationTime = rev;
        a.attester = attester;
        a.recipient = ATTESTER;
        a.revocable = true;
        a.data = data;
    }

    function _eq(PactaSentinelGuard.Health got, PactaSentinelGuard.Health want, string memory what) internal pure {
        require(got == want, what);
    }

    function _unhealthy(PactaSentinelGuard.Health h) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(PactaSentinelGuard.UnhealthyAttestation.selector, COLLATERAL, h);
    }

    /// @dev Every de-risking direction passes whatever the attestation health.
    function _assertDecreasesAlwaysPass() internal view {
        guard.validateCapIncrease(COLLATERAL, 1_000e6, 999e6);
        guard.validateCapIncrease(COLLATERAL, 1_000e6, 0);
        guard.validateCapIncrease(COLLATERAL, 1_000e6, 1_000e6);
        guard.validateCapIncrease(COLLATERAL, 0, 0);
        guard.validateCapIncrease(COLLATERAL, type(uint256).max, 0);
    }

    // ---- constructor / bindings ----
    function test_constructor_bounds() public {
        require(guard.maxStaleness() == 30 days, "default staleness");
        require(new PactaSentinelGuard(address(reg), address(eas), CURATOR, 1 days).maxStaleness() == 1 days, "min");
        require(new PactaSentinelGuard(address(reg), address(eas), CURATOR, 365 days).maxStaleness() == 365 days, "max");
        vm.expectRevert(abi.encodeWithSelector(PactaSentinelGuard.MaxStalenessOutOfBounds.selector, 1 days - 1));
        new PactaSentinelGuard(address(reg), address(eas), CURATOR, 1 days - 1);
        vm.expectRevert(abi.encodeWithSelector(PactaSentinelGuard.MaxStalenessOutOfBounds.selector, 365 days + 1));
        new PactaSentinelGuard(address(reg), address(eas), CURATOR, 365 days + 1);
        vm.expectRevert(PactaSentinelGuard.ZeroAddress.selector);
        new PactaSentinelGuard(address(0), address(eas), CURATOR, 0);
        vm.expectRevert(PactaSentinelGuard.ZeroAddress.selector);
        new PactaSentinelGuard(address(reg), address(0), CURATOR, 0);
        vm.expectRevert(PactaSentinelGuard.ZeroAddress.selector);
        new PactaSentinelGuard(address(reg), address(eas), address(0), 0);
    }

    function test_only_curator_binds() public {
        vm.expectRevert(PactaSentinelGuard.NotCurator.selector);
        guard.bind(COLLATERAL, SPRINT, UID);
        vm.expectRevert(PactaSentinelGuard.NotCurator.selector);
        guard.unbind(COLLATERAL);
        vm.prank(CURATOR);
        vm.expectRevert(PactaSentinelGuard.InvalidBinding.selector);
        guard.bind(address(0), SPRINT, UID);
        vm.prank(CURATOR);
        vm.expectRevert(PactaSentinelGuard.InvalidBinding.selector);
        guard.bind(COLLATERAL, 0, UID);
        vm.prank(CURATOR);
        vm.expectRevert(PactaSentinelGuard.InvalidBinding.selector);
        guard.bind(COLLATERAL, SPRINT, bytes32(0));
    }

    // ---- healthy ----
    function test_healthy_allows_increase() public view {
        _eq(guard.attestationHealth(COLLATERAL), PactaSentinelGuard.Health.Healthy, "healthy");
        guard.requireHealthyAttestation(COLLATERAL);
        guard.validateCapIncrease(COLLATERAL, 1_000e6, 2_000e6);
        guard.validateCapIncrease(COLLATERAL, 0, type(uint256).max);
        _assertDecreasesAlwaysPass();
    }

    // ---- every unhealthy state blocks increases and never blocks decreases ----
    function _expectBlocked(PactaSentinelGuard.Health h) internal {
        _eq(guard.attestationHealth(COLLATERAL), h, "health");
        _assertDecreasesAlwaysPass();
        vm.expectRevert(_unhealthy(h));
        guard.validateCapIncrease(COLLATERAL, 1_000e6, 1_000e6 + 1);
    }

    function test_unbound() public {
        vm.prank(CURATOR);
        guard.unbind(COLLATERAL);
        _expectBlocked(PactaSentinelGuard.Health.Unbound);
    }

    function test_sprint_not_recorded() public {
        reg.setRecord(SPRINT, bytes32(0), 0, SHA);
        _expectBlocked(PactaSentinelGuard.Health.NotRecorded);
    }

    function test_registry_drift_blocks() public {
        reg.setRecord(SPRINT, BLOCK_HASH, 1, SHA);
        _expectBlocked(PactaSentinelGuard.Health.Drift);
    }

    function test_missing_attestation() public {
        eas.set(_att(bytes32(0), SCHEMA, uint64(T0), 0, 0, ATTESTER, _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        _expectBlocked(PactaSentinelGuard.Health.MissingAttestation);
    }

    function test_uid_mismatch() public {
        eas.set(_att(keccak256("other"), SCHEMA, uint64(T0), 0, 0, ATTESTER, _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        _expectBlocked(PactaSentinelGuard.Health.MissingAttestation);
    }

    function test_wrong_schema() public {
        eas.set(_att(UID, keccak256("other schema"), uint64(T0), 0, 0, ATTESTER, _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        _expectBlocked(PactaSentinelGuard.Health.WrongSchema);
    }

    function test_wrong_attester_and_rotation() public {
        eas.set(_att(UID, SCHEMA, uint64(T0), 0, 0, address(0xBAD), _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        _expectBlocked(PactaSentinelGuard.Health.WrongAttester);
        // after an attester rotation in the registry, attestations by the new attester are the healthy ones
        reg.setAttester(address(0xBAD));
        _eq(guard.attestationHealth(COLLATERAL), PactaSentinelGuard.Health.Healthy, "rotated");
    }

    function test_revoked() public {
        eas.set(_att(UID, SCHEMA, uint64(T0 - 1 days), 0, uint64(T0 - 1), ATTESTER, _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        _expectBlocked(PactaSentinelGuard.Health.Revoked);
    }

    function test_expired() public {
        eas.set(_att(UID, SCHEMA, uint64(T0 - 1 days), uint64(T0), 0, ATTESTER, _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        _expectBlocked(PactaSentinelGuard.Health.Expired);
    }

    function test_stale_after_max_staleness() public {
        vm.warp(T0 - 1 days + 30 days);
        _eq(guard.attestationHealth(COLLATERAL), PactaSentinelGuard.Health.Healthy, "exactly 30 days");
        vm.warp(T0 - 1 days + 30 days + 1);
        _expectBlocked(PactaSentinelGuard.Health.Stale);
    }

    function test_future_dated_attestation_is_stale() public {
        eas.set(_att(UID, SCHEMA, uint64(T0 + 1), 0, 0, ATTESTER, _data(SPRINT, BLOCK_HASH, 0, SHA)), UID);
        _expectBlocked(PactaSentinelGuard.Health.Stale);
    }

    function test_data_mismatches() public {
        bytes[5] memory bad = [
            _data(SPRINT + 1, BLOCK_HASH, 0, SHA),
            _data(SPRINT, keccak256("other block"), 0, SHA),
            _data(SPRINT, BLOCK_HASH, 2, SHA),
            _data(SPRINT, BLOCK_HASH, 0, keccak256("other summary")),
            bytes(hex"deadbeef")
        ];
        for (uint256 i = 0; i < bad.length; i++) {
            eas.set(_att(UID, SCHEMA, uint64(T0 - 1 days), 0, 0, ATTESTER, bad[i]), UID);
            _expectBlocked(PactaSentinelGuard.Health.DataMismatch);
        }
    }

    // ---- fuzz: polarity safety ----
    function testFuzz_decrease_or_equal_never_reverts(uint256 currentCap, uint256 newCap, uint8 state) public {
        if (newCap > currentCap) (currentCap, newCap) = (newCap, currentCap);
        if (state % 3 == 0) reg.setRecord(SPRINT, BLOCK_HASH, 1, SHA);
        else if (state % 3 == 1) {
            vm.prank(CURATOR);
            guard.unbind(COLLATERAL);
        } else vm.warp(T0 + 400 days);
        guard.validateCapIncrease(COLLATERAL, currentCap, newCap);
    }

    function testFuzz_increase_blocked_when_unhealthy(uint256 currentCap, uint256 delta) public {
        if (currentCap == type(uint256).max) currentCap--;
        if (delta == 0) delta = 1;
        uint256 newCap = delta > type(uint256).max - currentCap ? type(uint256).max : currentCap + delta;
        reg.setRecord(SPRINT, BLOCK_HASH, 1, SHA);
        vm.expectRevert(_unhealthy(PactaSentinelGuard.Health.Drift));
        guard.validateCapIncrease(COLLATERAL, currentCap, newCap);
    }

    // ---- Morpho Vault V2 ----
    function test_morpho_v2_absolute_cap() public {
        MockMorphoVaultV2 vault = new MockMorphoVaultV2();
        bytes memory idData = abi.encode("collateral", COLLATERAL);
        vault.setCap(idData, 1_000e6);
        guard.checkMorphoV2AbsoluteCapIncrease(address(vault), COLLATERAL, idData, 5_000e6);
        reg.setRecord(SPRINT, BLOCK_HASH, 1, SHA);
        vm.expectRevert(_unhealthy(PactaSentinelGuard.Health.Drift));
        guard.checkMorphoV2AbsoluteCapIncrease(address(vault), COLLATERAL, idData, 1_000e6 + 1);
        guard.checkMorphoV2AbsoluteCapIncrease(address(vault), COLLATERAL, idData, 0);
        guard.checkMorphoV2AbsoluteCapIncrease(address(vault), COLLATERAL, idData, 1_000e6);
        guard.checkMorphoV2AbsoluteCapIncrease(address(vault), COLLATERAL, idData, 1);
    }

    // ---- Euler EVK ----
    function test_euler_amount_cap_resolution() public view {
        require(guard.resolveEulerAmountCap(0) == type(uint256).max, "0 = unlimited");
        // mantissa 100, exponent 2: 10**2 * 100 / 100 = 100
        require(guard.resolveEulerAmountCap(uint16((100 << 6) | 2)) == 100, "100");
        // mantissa 1023, exponent 63 does not overflow
        require(guard.resolveEulerAmountCap(type(uint16).max) == 10 ** 63 * 1023 / 100, "max");
    }

    function test_euler_caps_change() public {
        MockEVault ev = new MockEVault();
        uint16 small = uint16((100 << 6) | 6); // 1e6
        uint16 big = uint16((100 << 6) | 9); // 1e9
        ev.setCaps(small, small);
        guard.checkEulerCapsChange(address(ev), COLLATERAL, big, small);
        reg.setRecord(SPRINT, BLOCK_HASH, 1, SHA);
        vm.expectRevert(_unhealthy(PactaSentinelGuard.Health.Drift));
        guard.checkEulerCapsChange(address(ev), COLLATERAL, big, small);
        vm.expectRevert(_unhealthy(PactaSentinelGuard.Health.Drift));
        guard.checkEulerCapsChange(address(ev), COLLATERAL, 0, small); // 0 = unlimited: an increase
        // lowering either cap (or leaving it) never needs the attestation
        guard.checkEulerCapsChange(address(ev), COLLATERAL, uint16((100 << 6) | 3), small);
        guard.checkEulerCapsChange(address(ev), COLLATERAL, small, small);
        ev.setCaps(0, 0);
        guard.checkEulerCapsChange(address(ev), COLLATERAL, small, small); // from unlimited to finite: a decrease
    }
}
