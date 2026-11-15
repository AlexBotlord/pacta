#!/usr/bin/env python3
"""Validate offline ABI and parity; this does not authenticate the sources."""
import json
from pathlib import Path

f = json.loads((Path(__file__).parent / "fixture.json").read_text())
assert f["chainId"] == 1 and f["blockNumber"] == 26417900
assert len(f["rpc"]) == 2
for evidence in f["rpc"].values():
    assert evidence["block_hash"] == f["blockHash"]
    threshold = bytes.fromhex(evidence["threshold_raw"].removeprefix("0x"))
    owners = bytes.fromhex(evidence["owners_raw"].removeprefix("0x"))
    assert len(threshold) == 32 and int.from_bytes(threshold, "big") == 3
    assert len(owners) == 32 * 7 and int.from_bytes(owners[:32], "big") == 32
    assert int.from_bytes(owners[32:64], "big") == 5
    assert all(owners[i:i+12] == bytes(12) for i in range(64, len(owners), 32))
values = list(f["rpc"].values())
assert values[0] == values[1]
assert f["mcp"]["pacta_lookup_protocol"]["totalMatches"] == 0
scan = f["mcp"]["pacta_scan_control_plane"]
assert scan["block"]["hash"] == f["blockHash"]
assert scan["safe"]["threshold"] == 3 and scan["safe"]["ownerCount"] == 5
print("Fixture ABI, dual-RPC parity and MCP consistency verified offline")
