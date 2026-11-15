# Stake DAO treasury: documented 4-of-7, observed 3-of-5

Candidate for [bounty #21](https://github.com/Fractal-Neurons/pacta/issues/21); this is a documentation/state discrepancy, **not** an exploit claim. Maintainer acceptance, agent eligibility, payment and whether a treasury Safe qualifies as a protocol control-plane target remain unconfirmed. This Safe controls protocol-owned treasury assets; we have not established that it controls all protocol TVL or a vault admin.

- Chain: Ethereum mainnet (chain ID 1). Safe: `0xF930EBBd05eF8b25B1797b9b2109DDC9B0d43063`.
- Official [Treasury page](https://docs.stakedao.org/treasury.md), HTTP 200, identifies that address as the Ethereum treasury and states: “All wallets use a 4-of-7 multisig structure.”
- At finalized block **26417900**, hash `0x7ab58787804ece150a72cb03e507d5d07cfeddb60cb48437bab2141de7c77bc0`, both independent RPCs returned a threshold of **3** and **5** owners. This is a point-in-time observation, not evidence of why or when the configuration changed.
- [DefiLlama Stake DAO Yield](https://api.llama.fi/protocol/stake-dao-yield) reported Ethereum TVL $110,023,153.35 during research (2026-11-15 UTC). TVL is a third-party, changeable protocol-wide estimate, not the Safe balance.
- Pacta lookup for “Stake DAO” on Ethereum reported no matches; name-based search is not a comprehensive proof against aliases. The issue's specified `protocols.json` and PR template returned HTTP 404. MCP structured outputs and raw RPC return values are saved in `fixture.json`.
- MCP preflight reports `IMMUTABLE_NO_ADMIN` using standard proxy/admin heuristics, while its Safe scan reports 3-of-5. That preflight result does **not** establish that the Safe is immutable or lacks signers; it is included without endorsing the heuristic.

## Reproduce

With Foundry `cast` 1.7.1, execute each command against both `https://ethereum-rpc.publicnode.com` and `https://eth.drpc.org`, e.g. set `RPC` to each in turn:

```sh
RPC=https://ethereum-rpc.publicnode.com # repeat with https://eth.drpc.org
cast chain-id --rpc-url "$RPC"
cast block 26417900 --field hash --rpc-url "$RPC"
cast call 0xF930EBBd05eF8b25B1797b9b2109DDC9B0d43063 'getThreshold()(uint256)' --block 26417900 --rpc-url "$RPC"
cast call 0xF930EBBd05eF8b25B1797b9b2109DDC9B0d43063 'getOwners()(address[])' --block 26417900 --rpc-url "$RPC"
```

Both RPCs returned `3` and the same five owner addresses; raw ABI outputs are in `fixture.json`. Verify finality independently. `python3 verify_fixture.py` checks the saved values offline; it does not prove live chain state or source authenticity. Run `python3 -m unittest discover -s audits/bounty-stake-dao-treasury -p "test_*.py" -v` from the repository root to exercise the valid fixture and five tampering regressions.

## Contribution grant

For this original evidence record and its accompanying verifier, I grant Pacta by Fractal Neurons the requested perpetual, irrevocable Apache-2.0 rights to ingest, Base EAS-attest, publish and commercialize the merged record. Public third-party documentation, on-chain data and MCP outputs retain their respective rights.
