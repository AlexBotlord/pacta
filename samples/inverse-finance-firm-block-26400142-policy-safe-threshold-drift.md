# Verified Control-Plane Drift: Inverse Finance (FiRM) Policy Committee Safe Threshold & Signer Rotation

- **Protocol**: Inverse Finance (FiRM) (`inverse-finance-firm`)
- **Target Contract**: `0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7` (`Policy Committee Safe`)
- **Chain ID**: `1` (Ethereum Mainnet)
- **Prior Pinned Pacta Block**: `26399876` (`0x8bf896b892683ff3267b88b367ab015a70cf5caf53542eb405f4f648f6bcde8a`)
- **Governing Rotation Block**: `26400142` (`0x30f8e960fa8ced601ff9dc60e88da16530da0e1ab07631af9b381b426dab229b`)
- **Governing Transaction Hash**: `0x46563d089a267b88b76a857994fedd6bf24fb5c3a31e201c5956879cd90fb39e`
- **Replay Finalized Block**: `26418033` (`0xda8ab82e66967d5952f31cfca199e96d188aaa1076d292bfe165caa07a7f71f1`)
- **Classification**: Post-Snapshot Governance Control-Plane Drift (`parameter_delta`)

---

## 1. Summary of Control-Plane Drift

In Pacta's Sprint 1 audit pinned at block `26399876`, the Policy Committee Safe (`0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7`) was observed with `getThreshold() = 4` and `getOwners().length = 7` (a `4-of-7` Gnosis Safe), already in `parameter_delta` relative to official governance documentation stating a `5-of-9` multisig.

At Ethereum Mainnet block `26400142` (tx `0x46563d089a267b88b76a857994fedd6bf24fb5c3a31e201c5956879cd90fb39e`), the Policy Committee executed an on-chain signer removal and quorum modification:
1. Removed signer `0x7efe8e14eCfcB3FF349253A9925A8818A8Ce5480` (emitted topic `0xf8d49fc529812e9a7c5c50e69c20f0dccc0db8fa95c98bc58cc9a4f1c1299eaf`).
2. Reduced signing threshold from `4` to `3` (emitted topic `0x610f7ff2b304ae8903c3de74c60c6ab1f7d6226b3f52c5161905bb5ad4039c93`).
3. Total active signers decreased from `7` to `6`.

The live on-chain control plane has therefore drifted to a **`3-of-6` Gnosis Safe**, increasing the discrepancy against official documentation (`5-of-9`).

---

## 2. On-Chain State Comparison

| Parameter | Documentation Claim | Pacta Pinned Baseline (Block 26399876) | Current Live State (Block 26418033) |
| :--- | :--- | :--- | :--- |
| **Multisig Threshold** | `5` | `4` | **`3`** |
| **Total Signers** | `9` | `7` | **`6`** |
| **Multisig Quorum** | `5-of-9` | `4-of-7` | **`3-of-6`** |
| **Removed Signer** | N/A | `0x7efe8e14eCfcB3FF349253A9925A8818A8Ce5480` present | **Removed at block 26400142** |

---

## 3. Official Documentation Citation (HTTP 200)

- **Documentation URL**: `https://docs.inverse.finance/inverse-finance/inverse-finance/governance/governance-overview.md`
- **Verbatim Quote**:
  > "| **Policy Committee**   | 5 of 9 | Governance guardian role (can cancel proposals), manages reward rate policies, operates as BondsManager |"

---

## 4. Deterministic Dual-RPC Replay Proof

Executed across two independent public archive RPC endpoints:
- **RPC 1**: `https://rpc.mevblocker.io`
- **RPC 2**: `https://eth-mainnet.public.blastapi.io`

### A. Threshold at Pinned Baseline Block (`26399876`)
```bash
cast call 0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7 "getThreshold()(uint256)" --block 26399876 --rpc-url https://rpc.mevblocker.io
# Output: 4

cast call 0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7 "getThreshold()(uint256)" --block 26399876 --rpc-url https://eth-mainnet.public.blastapi.io
# Output: 4
```

### B. Threshold at Current Finalized Block (`26418033`)
```bash
cast call 0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7 "getThreshold()(uint256)" --block 26418033 --rpc-url https://rpc.mevblocker.io
# Output: 3

cast call 0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7 "getThreshold()(uint256)" --block 26418033 --rpc-url https://eth-mainnet.public.blastapi.io
# Output: 3
```

### C. Active Signers at Block `26418033`
```bash
cast call 0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7 "getOwners()(address[])" --block 26418033 --rpc-url https://rpc.mevblocker.io
# Output: [0x52f63971afD2a32524c859C29943f9BEa38CA907, 0x3FcB35a1CbFB6007f9BC638D388958Bc4550cB28, 0x962228a90eaC69238c7D1F216d80037e61eA9255, 0x9F3614afb3Df9f899caDBFfaA05c6C908059F726, 0x6535020cCeB810Bdb3F3cA5e93dE2460FF7989BB, 0x2723723FDd3Db8ba2D6f0e1B333e90A7E60A0411]
```

### D. Governing Transaction Logs at Block `26400142`
```bash
cast logs --from-block 26400142 --to-block 26400142 --address 0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7 --rpc-url https://eth-mainnet.public.blastapi.io
# Emitted:
# 1. RemovedOwner(0x7efe8e14ecfcb3ff349253a9925a8818a8ce5480)
# 2. ChangedThreshold(3)
# 3. ExecutionSuccess(0x06a935c735a9e5d3ad1fe9d8a3bba90643021b3284fa836a37bb8f1d427960d4, 0)
```

---

## 5. Live Pacta Remote MCP Verification Snippet

```json
{
  "chain": "ethereum",
  "address": "0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7",
  "block": {
    "number": 26418224,
    "hash": "0x248fecf82b8798ad4d41b358355af7f78ab2da91b8eed5e02fd6ce0a9a493112"
  },
  "safe": {
    "threshold": 3,
    "owners": [
      "0x52f63971afD2a32524c859C29943f9BEa38CA907",
      "0x3FcB35a1CbFB6007f9BC638D388958Bc4550cB28",
      "0x962228a90eaC69238c7D1F216d80037e61eA9255",
      "0x9F3614afb3Df9f899caDBFfaA05c6C908059F726",
      "0x6535020cCeB810Bdb3F3cA5e93dE2460FF7989BB",
      "0x2723723FDd3Db8ba2D6f0e1B333e90A7E60A0411"
    ],
    "ownerCount": 6
  }
}
```

---

## 6. Apache-2.0 Contribution & Commercialization Grant

The contributor hereby grants to Pacta by Fractal Neurons perpetual, irrevocable, worldwide, non-exclusive, royalty-free, fully sublicensable rights under Apache-2.0 to ingest, Base EAS-attest, publish on `pacta.wtf`, format into commercial dossiers, and commercialize the verified control-plane observation record contained herein.
