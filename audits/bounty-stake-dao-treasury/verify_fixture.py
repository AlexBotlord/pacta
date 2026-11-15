#!/usr/bin/env python3
"""Validate offline consistency only; external sources are not authenticated."""
import json
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(f):
    address = "0xf930ebbd05ef8b25b1797b9b2109ddc9b0d43063"
    block_hash = "0x7ab58787804ece150a72cb03e507d5d07cfeddb60cb48437bab2141de7c77bc0"
    require(f["chainId"] == 1 and f["blockNumber"] == 26417900, "chain/block mismatch")
    require(f["treasurySafe"].lower() == address and f["blockHash"] == block_hash, "address/hash mismatch")
    require(len(f["rpc"]) == 2, "expected two RPC records")
    decoded = []
    for evidence in f["rpc"].values():
        require(evidence["block_hash"] == block_hash, "RPC block hash mismatch")
        threshold = bytes.fromhex(evidence["threshold_raw"].removeprefix("0x"))
        owners = bytes.fromhex(evidence["owners_raw"].removeprefix("0x"))
        require(len(threshold) == 32 and int.from_bytes(threshold, "big") == 3, "threshold mismatch")
        require(len(owners) == 32 * 7 and int.from_bytes(owners[:32], "big") == 32, "invalid ABI offset or length")
        require(int.from_bytes(owners[32:64], "big") == 5, "invalid ABI owner count")
        rows = [owners[i:i + 32] for i in range(64, len(owners), 32)]
        require(all(row[:12] == bytes(12) for row in rows), "invalid ABI address padding")
        decoded.append(["0x" + row[12:].hex() for row in rows])
    values = list(f["rpc"].values())
    require(values[0] == values[1] and decoded[0] == decoded[1], "RPC data differs")
    lookup = f["mcp"]["pacta_lookup_protocol"]
    require(lookup["totalMatches"] == 0 and lookup["query"] == "Stake DAO" and lookup["filters"]["chain"] == "ethereum", "lookup mismatch")
    preflight = f["mcp"]["pacta_check_preflight"]
    require(preflight["chainId"] == 1 and preflight["chain"] == "ethereum", "preflight chain mismatch")
    require(preflight["address"].lower() == address and preflight["pinnedBlock"] == 26417900 and preflight["pinnedBlockHash"] == block_hash, "preflight address/block mismatch")
    scan = f["mcp"]["pacta_scan_control_plane"]
    require(scan["chain"] == "ethereum" and scan["address"].lower() == address, "scan chain/address mismatch")
    require(scan["block"]["number"] == 26417900 and scan["block"]["hash"] == block_hash, "scan block mismatch")
    require(scan["safe"]["threshold"] == 3 and scan["safe"]["ownerCount"] == 5, "scan threshold/count mismatch")
    require([x.lower() for x in scan["safe"]["owners"]] == decoded[0], "RPC/MCP owner mismatch")


def main():
    try:
        fixture = json.loads((Path(__file__).parent / "fixture.json").read_text())
        verify(fixture)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Fixture validation failed: {exc}", file=sys.stderr)
        return 1
    print("Fixture ABI, dual-RPC parity and MCP fields match offline; sources not authenticated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
