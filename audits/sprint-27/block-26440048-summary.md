# Sprint 27 Protocol Commitment Summary — Block `26440048`

- **Ethereum Mainnet pin**: `26440048` (`0x1937170`), canonical block hash `0x2c6e70ac6ce978ce5c457208ea6d953e60e92ebf2151578f46cbdd070baa54c6`, timestamp `2026-11-18 06:08:23 UTC` (`1794982103`); the `finalized` head, both endpoints returning the same number and hash
- **Base Mainnet pin**: `58956515` (`0x3839ae3`), canonical block hash `0x82af637fd7a689f4ea41c0ecd1a84a407ea93f2622b8e9c06184327d957129d0`, timestamp `2026-11-18 06:01:18 UTC` (`1794981678`); the `finalized` head, both endpoints returning the same number and hash
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI), bulk harvester v1.4. Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode` batched through Multicall3 at the pinned block, on two independent RPCs per chain with identical block hashes: `ethereum-rpc.publicnode.com` + `rpc.mevblocker.io` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base). Documentation: HTTP-200 first-party snapshots named by their SHA-256; every quote below is an exact substring of its snapshot's text and every value is re-derived from the pinned reads by the validator (no model output is trusted). The 78 targets read after the pin (added to the cohort, or left when the first pinning run was interrupted: 1inch-swap, 3f, abracadabra-spell, aegis-yusd, aera-v3, alchemix-v3, anemoy-capital, ao-bridge, arkis, arrakis-modular, aster-bridge, autofinance, avalon-superearn, bio-protocol, bitfi-basis, cian-yield-layer, concentrator, derive-v3-options, easedefi.org, eigenpie, ensuro, extra-finance-base, frankencoin, gondi-v3, grvt-bridge, hakka-finance, hop-protocol, hyperlane, iaero-protocol, idex-v1, k3-capital, kpk, ledgity-yield, legion, lighter-bridge, llama-airforce, makina, noon, opengdp-shared-security, origami-finance, origin-superoeth-base, pancakeswap-amm-v3, pickle, pirex, pooltogether-v3, ribbon, rockawayx, saturn, seamless-protocol-base, shift-defi, sierra-protocol, sonic-gateway, sosovalue-basis, spectra-metavaults, stafi, stakingverse, starknet-bridge, steer-protocol, superform-v2-base, symbiosis, tangent-finance, team-finance, theo-network-thusd, tori-finance, tornado-cash, treehouse-tree-teth, uncx-network-v2, unslashed, usdt0, veda, vesper-v1, world-chain-bridge, xdai-stake-bridge, yield-basis, zama, zerobase-cedefi, zora-bridge, ztln-p) were read at the same block numbers and hashes through two archive-capable endpoints per chain whose block hashes match the pin: `rpc.mevblocker.io` + `gateway.tenderly.co` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base).
- **Result**: `9` records for `8` protocols (`7` new; published protocols with a new record: Treehouse (TREE / tETH)) — `8` aligned baselines, `0` protective deltas, `1` parameter delta. `verifiedCount = 8`. `driftCount = 1`, the same convention as Sprints 1–26 and `PactaSentinelGuard` (`driftCount != 0` means drift).
- **RPC-pinned promotions (not attested)**: `82` further new protocols are published as RPC-pinned control-plane records at the same pins (listed below); the `48` RPC-pinned protocols already published move to these pins with every stated fact unchanged. They carry no Base EAS UID.
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); Base reads are taken at the Base pin.

## 1. Privacy Pools V1 — Privacy Pools V1 PoolVault proxy: upgradeable (UUPS), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Privacy Pools V1 PoolVault proxy** | `0x0Eb42804BF897662aF851370eaeAdcDBEC1b97ed` | slot `eip1967.proxy.implementation` | Privacy Pools V1 PoolVault proxy 0x0Eb42804BF897662aF851370eaeAdcDBEC1b97ed (Ethereum): EIP-1967 implementation slot = 0x5F89cD5c3610c2AD870B1b33126d209fECdb69c7; upgradeable (EIP-1967 implementation exposing upgradeToAndCall (UUPS)). (Ethereum `#26440048`) |

Classification: **aligned baseline** (1 record).
- 'PoolVault 0x0Eb42804BF897662aF851370eaeAdcDBEC1b97ed (UUPS proxy; implementation 0x5f89cd5c3610c2ad870b1b33126d209fecdb69c7)' (docs.privacypools.com/deployments/mainnet.md) (snapshot sha256 `001d3b8120f10b2a2fc8b23c6337039049323aff8a82f1136bb335591b68f45d`)

## 2. Equilibria — Equilibria timelock: 24-hour minimum delay, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Equilibria TimelockController** | `0xe2A63438747D2c71E14BdC2Cc222be89B1C11D03` | `getMinDelay()` | Equilibria TimelockController 0xe2A63438747D2c71E14BdC2Cc222be89B1C11D03 (Ethereum): getMinDelay() = 86400s (1 d). (Ethereum `#26440048`) |

Classification: **aligned baseline** (1 record).
- 'Following this process, an upgrade is made by the team, and the multi-sig signer proposes the upgrade with a 24-hour timelock.' (docs.equilibria.fi/security-and-risk/multi-sig-and-timelock.md) (snapshot sha256 `a99e3f55ab6cfcb726ba5c8d736aead75758b39d42fdac1a999415f690b31185`)

## 3. ETH Strategy — ETH Strategy multisig: 3-of-5 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **ETH Strategy Safe** | `0xC53CCed6332D06972A7eaEDc64FDF6d4aF5220b8` | `getThreshold()` | ETH Strategy Safe 0xC53CCed6332D06972A7eaEDc64FDF6d4aF5220b8 (Ethereum): getThreshold() = 3 of getOwners() = 5 owners (Safe v1.4.1). (Ethereum `#26440048`) |

Classification: **aligned baseline** (1 record).
- 'The ETH Strategy Multisig (root authority) is a **3-of-5** Safe (v1.4.1). Five distinct EOA signers must produce 3 signatures to execute any governance action.' (docs.ethstrat.xyz/security-and-risk/decentralization-scorecard.md) (snapshot sha256 `0941c6b988874bb244ce8c522f16f7b8c8695c75f25f8d3ac4b2e7e0f9667ca5`)

## 4. Eclipse Bridge — Eclipse Bridge multisig: 3-of-5 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Eclipse Bridge Safe** | `0x7B2c1CbB33c53c3C6a695e36096AD2cfCE1c0efC` | `getThreshold()` | Eclipse Bridge Safe 0x7B2c1CbB33c53c3C6a695e36096AD2cfCE1c0efC (Ethereum): getThreshold() = 3 of getOwners() = 5 owners (Safe v1.3.0); it controls ERC1967Proxy 0x6055Dc6Ff1077eebe5e6D2BA1a1f53d7Ef8430dE. (Ethereum `#26440048`) |

Classification: **aligned baseline** (1 record).
- 'Our Canonical Bridge is governed by a 3-of-5 multisig.' (docs.eclipse.xyz/architecture/security-architecture-from-assumptions-to-guarantees.md) (snapshot sha256 `8502d1c2dfc59f317de0e2e042fc95acbd73e90c45cd81534d4742d21e15b15d`)

## 5. Gravity by Galxe Bridge — Gravity by Galxe Bridge multisig: 3-of-6 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Gravity by Galxe Bridge Safe** | `0xbD6e434dB90FD8AD4E28d85C133AD34cA6fbfB6D` | `getThreshold()` | Gravity by Galxe Bridge Safe 0xbD6e434dB90FD8AD4E28d85C133AD34cA6fbfB6D (Ethereum): getThreshold() = 3 of getOwners() = 6 owners (Safe v1.3.0). (Ethereum `#26440048`) |

Classification: **aligned baseline** (1 record).
- '**Administration.** Each contract is owned by a 3-of-6 Safe multisig (`0xeF936B0CaaAdfb439dd24F14411949694aB3C507` on Gravity L1, `0xbD6e434dB90FD8AD4E28d85C133AD34cA6fbfB6D` on Ethereum).' (docs.gravity.xyz/llms-full.txt) (snapshot sha256 `f838b1b3a5948d3c91ec8cb65cc284db5231aeeb22fc926ba80678ac98bf5d83`)

## 6. KUMA Protocol — KUMA Protocol multisig: 4-of-7 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **KUMA Protocol Safe** | `0xB5502747AABDCa21E832951b4caaF739dA33f450` | `getThreshold()` | KUMA Protocol Safe 0xB5502747AABDCa21E832951b4caaF739dA33f450 (Ethereum): getThreshold() = 4 of getOwners() = 7 owners (Safe v1.3.0). (Ethereum `#26440048`) |

Classification: **aligned baseline** (1 record).
- 'The multisig requires 4/7 signatures to execute a transaction.' (docs.kuma.bond/kuma-protocol/dao-and-governance/multisig.md) (snapshot sha256 `8f49542cb4d0f0aaef389b2a900c1eee427f62c61a497382674038c6c2dcbc50`)

## 7. Umia — Umia timelock: 2-day minimum delay, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Umia timelock** | `0xD0193fFAF565B6E530C1a6bbBb2FB13243f29177` | `getMinDelay()` | Umia timelock 0xD0193fFAF565B6E530C1a6bbBb2FB13243f29177 (Base): getMinDelay() = 172800s (2 d). (Base `#58956515`) |
| **UmiaMarketCore proxy** | `0x55975E430Cc54C63dff03B1E6d27Be574Ce229F6` | slot `eip1967.proxy.implementation` | UmiaMarketCore proxy 0x55975E430Cc54C63dff03B1E6d27Be574Ce229F6 (Base): EIP-1967 implementation slot = 0xBc35cB6cCc4BE46AA491960EBf5281cD5310c653; upgradeable (EIP-1967 implementation exposing upgradeToAndCall (UUPS)). (Base `#58956515`) |

Classification: **aligned baseline** (2 records).
- 'The protocol owner is a timelock with a two-day public delay.' (umia.finance/llms-full.txt) (snapshot sha256 `abd3cd70ada53d08ab648d98db438d8347b8e4a317c944f30e57c49247ad1e4f`)
- 'Our stance is that the core contracts stay upgradeable while the protocol is still being built.' (umia.finance/llms-full.txt) (snapshot sha256 `abd3cd70ada53d08ab648d98db438d8347b8e4a317c944f30e57c49247ad1e4f`)

## 8. Treehouse (TREE / tETH) — TREE token: a 5-of-7 Safe can blacklist holders with no delay; docs state a 5-day timelock on every contract

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **TreehouseToken (TREE)** | `0x77146784315Ba81904d654466968e3a7c196d1f3` | `blacklister()` | TREE 0x77146784315Ba81904d654466968e3a7c196d1f3 (Ethereum): EIP-1967 proxy, implementation 0x0fedcbfEBc293Ad8048726B0F887e6C1126EffA6 since the timelock operation 0x2f11dcc3… executed at #26,439,293; blacklister() = 0x22261B4D6F629D8cF946C3524df86bF7222901F6, a Safe with getThreshold() = 5 of getOwners() = 7 owners and no delay of its own (0 s), so blacklisting needs no timelock; owner() = timelock 0x2225DAbFfC7F862c99477381E971E8B1FDaB467e with getMinDelay() = 432000s (5 days). (Ethereum `#26440048`) |

Classification: **parameter delta** (1 record).
- 'All Treehouse contracts are secured by a 5-day timelock, ensuring no critical action executes immediately and giving everyone a clear window to see and respond to upcoming updates.' (docs.treehouse.finance/protocol/tasset/security/timelock) / 'Token Contract: 0x77146784315Ba81904d654466968e3a7c196d1f3' (docs.treehouse.finance/protocol/tree-token); neither page names a blacklist or freeze role on TREE or the blacklister Safe. Pacta timelock radar brief treehouse-op-0x2f11 decoded the upgrade before it executed. (snapshot sha256 `baec4dd9875a13098d29e3f87b4ccc2ec18c9c4a3ecf0985d67d2a3898607cea`, `9ef7a5753799583ed50cc9c930da0b75eb9a8755c1136c875db663593b951028`)

## 9. RPC-pinned promotions — 82 new protocols, documentation not compared

Each is published as an `rpc_observed` record (`docs/api/v1/rpc-pinned.json`): runtime bytecode, EIP-1967 slots and the first readable controller of the protocol's primary contract, at the pins above. No documentation parameter is compared, so none counts toward `verifiedCount` or `driftCount`.

| Protocol | Chain | Primary contract | Proxy | Controller |
| :--- | :--- | :--- | :--- | :--- |
| Dolomite | Ethereum | `0x003Ca23Fd5F0ca87D01F6eC6CD14A8AE60c2b97D` | no | contract controller `0xC2B66E247daE5Ee749Ae1d827190115F3653dE06` |
| edgeX Bridge | Ethereum | `0xB0076DE78Dc50581770BBa1D211dDc0aD4F2a241` | yes | none readable |
| Zircuit Staking | Ethereum | `0xF047ab4c75cebf0eB9ed34Ae2c186f3611aEAfa6` | no | contract controller `0xacAA4Dde6c4fB90BB1948904f0308296f7C74252` |
| NodeDAO | Ethereum | `0xd7C049CD4ba216679ecC04Eb2767cC5E39812121` | yes | timelock `0x16F692525f3b8c8a96F8c945D365Da958Fb5735B` |
| SushiSwap V3 | Ethereum | `0xc35DADB65012eC5796536bD9864eD8773aBc74C4` | no | eoa `0xf87BC5535602077d340806D71f805EA9907a843D` |
| Piku Finance | Ethereum | `0x2E4039E8E31475d65DC00293C366FDBfBBC02DC3` | no | multisig safe `0x27d12198852acA3FECb86F55832D8944cc7c6a56` (2-of-3) |
| Ring Few | Ethereum | `0x7D86394139bf1122E82FDF45Bb4e3b038A4464DD` | no | none readable |
| Drakewell USDdw | Ethereum | `0x2B5895b716311A1eaC8f93fB88C56aF9eC8C1A69` | no | none readable |
| Avant avETH | Ethereum | `0x9469470C9878bf3d6d0604831d9A3A366156f7EE` | no | eoa `0xd4d23209aaE8630bf386b7393763a5b7865e57cb` |
| D2 Finance | Ethereum | `0x07Dff4087b43c4A759f4Fc69511c26d51929dAF4` | no | multisig safe `0xBB856548bCD0EBa1749c2336244139F1dbE93498` (2-of-3) |
| Paradex Bridge | Ethereum | `0xb32E10022FFBeDfE10bc818a1C7e67D9d87e0fa7` | yes | none readable |
| Meta Pool ETH | Ethereum | `0x48AFbBd342F64EF8a9Ab1C143719b63C2AD81710` | yes | contract controller `0x806F870ee04A2CC8bf2aD053BAa5ed9999A1f182` (3-of-6) |
| Multichain | Ethereum | `0x9Fb9a33956351cf4fa040f65A13b835A3C8764E3` | no | contract controller `0xe95fD76CF16008c12FF3b3a937CB16Cd9Cc20284` |
| UltraYield Vaults | Ethereum | `0x8ECC0B419dfe3AE197BC96f2a03636b5E1BE91db` | yes | none readable |
| Chamber Vaults | Ethereum | `0xca1207647Ff814039530D7d35df0e1Dd2e91Fa84` | yes | multisig safe `0x5a76f841bFe5182f04bf511fC0Ecf88C27189FCB` (3-of-5) |
| Metric V1 | Ethereum | `0x2a53833cc95548cf52c7b159110e22D3a9018f32` | no | multisig safe `0xa082C768B1C40f5e980b75959D85cF245AFF0FAE` (3-of-5) |
| Cronos zkEVM Bridge | Ethereum | `0x28Ff2E4dD1B58efEB0fC138602A28D5aE81e44e2` | yes | eoa `0x65b5cFaad25c39063A248684DA546cAB1Cc46cf5` |
| Ankr | Ethereum | `0x8290333ceF9e6D528dD5618Fb97a76f268f3EDD4` | no | none readable |
| Lista Lending | Ethereum | `0xf820fB4680712CD7263a0D3D024D5b5aEA82Fd70` | yes | timelock `0xa18ae79AEDA3e711E0CD64cfe1Cd06402d400D61` |
| Strata Markets | Ethereum | `0x3d7d6fdf07EE548B939A80edbc9B2256d0cdc003` | yes | contract controller `0x30A17d6bcBDBF1579d6fBBA453aCf776D01fbb50` |
| GETH | Ethereum | `0x3802c218221390025BCEABBaD5D8C59F40eB74B8` | no | none readable |
| Harvest Finance | Ethereum | `0xa0246c9032bC3A600820415aE600c6388619A14D` | no | none readable |
| StakeStone STONE | Ethereum | `0x1D88713b483A8E45cfF0e5CD7c2e15E5Fab4534d` | no | none readable |
| Syntropia | Ethereum | `0x1b2CB79a4564206f53Ba80b4d780F251b4Ae6765` | yes | contract controller `0x78AC58ED54018F5ccd5F5De2D7c0AE40800f2cf4` |
| Brickken | Ethereum | `0x0A638F07ACc6969abF392bB009f216D22aDEa36d` | no | none readable |
| XSY | Base | `0xBA515304d8153c4b162dC79f867E152DF9c127eb` | yes | multisig safe `0xB237EB3c71a0f351BD121b0C467248473fbC2ccA` (3-of-4) |
| Anvil | Ethereum | `0xAEEAa594e7dc112D67b8547fe9767a02c15B5597` | no | none readable |
| Morph Bridge | Ethereum | `0xDc71366EFFA760804DCFC3EDF87fa2A6f1623304` | yes | contract controller `0x31110622D6CA24c9FF307d6ae1715F16E47F16A0` |
| Yuzu Money | Ethereum | `0x224e90591A2d63fb66E677D0561Ea4A6Ad1F098D` | yes | contract controller `0x1af1878e8d9E7263236529eCAdAcD345781538d0` |
| Bancor V3 | Ethereum | `0x1F573D6Fb3F13d689FF844B4cE37794d79a7FF1C` | no | contract controller `0xa489C2b5b36835A327851Ab917A80562B5AFC244` |
| Exactly | Ethereum | `0x310A2694521f75C7B2b64b5937C16CE65C3EFE01` | yes | contract controller `0x3866eA62494597A5EDeA4A97f9429f82b9d7Ca34` |
| YieldFi | Ethereum | `0x19Ebd191f7A24ECE672ba13A302212b5eF7F35cb` | yes | contract controller `0xE26E1D2ae51dcB89E382CA7400b080e6632117B9` |
| Badger DAO | Ethereum | `0x3472A5A71965499acd81997a54BBA8D852C6E53d` | no | none readable |
| Index Coop | Ethereum | `0x0954906da0Bf32d5479e25f46056d22f08464cab` | no | none readable |
| DODO AMM | Ethereum | `0x43Dfc4159D86F3A37A5A4B3D4580b888ad7d4DDd` | no | none readable |
| Juicebox V1 | Ethereum | `0x3abF2A4f8452cCC2CF7b4C1e4663147600646f66` | no | contract controller `0xee2eBCcB7CDb34a8A822b589F9E8427C24351bfc` |
| Blur Bids | Ethereum | `0x5283D291DBCF85356A21bA090E6db59121208b44` | no | multisig safe `0x6e596823A8c9c48Eb6Fa4aB2208F34B97453A327` (5-of-5) |
| Monolith Market | Ethereum | `0x6D961c9DCF1AD73566822BA4B087892e3839B849` | no | none readable |
| cBridge | Ethereum | `0x4F9254C83EB525f9FCf346490bbb3ed28a81C667` | no | eoa `0xb22DC759f194F5d00F1981Bf47AB5C3572562C96` |
| Flying Tulip Lend | Ethereum | `0x5DD1A7A369e8273371d2DBf9d83356057088082c` | no | multisig safe `0x1118e1c057211306a40A4d7006C040dbfE1370Cb` (3-of-5) |
| Metronome Synth | Ethereum | `0x2Ebd53d035150f328bd754D6DC66B99B0eDB89aa` | no | multisig safe `0xd1DE3F9CD4AE2F23DA941a67cA4C739f8dD9Af33` (3-of-5) |
| Aura | Ethereum | `0xC0c293ce456fF0ED870ADd98a0828Dd4d2903DBF` | no | none readable |
| Native Credit Pool | Ethereum | `0xe3D41d19564922C9952f692C5Dd0563030f5f2EF` | no | contract controller `0x9b9Dc7c56e18cfdA57D402CA7Ded491b1544DC56` (3-of-5) |
| MorpheusAI | Ethereum | `0x47176B2Af9885dC6C4575d4eFd63895f7Aaa4790` | yes | multisig safe `0x1FE04BC15Cf2c5A2d41a0b3a96725596676eBa1E` (5-of-9) |
| Synapse Cross Chain Bridge | Ethereum | `0x0f2D719407FdBeFF09D87557AbB7232601FD9F29` | no | multisig safe `0x67F60b0891EBD842Ebe55E4CCcA1098d7Aac1A55` (2-of-3) |
| Royco V2 | Ethereum | `0x7cC6fB28eC7b5e7afC3cB3986141797ffc27253C` | yes | none readable |
| Metis Bridge | Ethereum | `0x9E32b13ce7f2E80A01932B42553652E053D6ed8e` | no | none readable |
| Orderly Bridge | Ethereum | `0xABD4C63d2616A5201454168269031355f4764337` | no | none readable |
| dYdX V3 | Ethereum | `0x92D6C1e31e14520e676a687F0a93788B716BEff5` | no | contract controller `0x64c7d40c07EFAbec2AafdC243bF59eaF2195c6dc` |
| ADI Bridge | Ethereum | `0x8B1484d57abBE239bB280661377363b03c89CaEa` | yes | none readable |
| NUVA | Ethereum | `0x50AE1e4A612A4623b747aEeFb30aFBA82804e12c` | yes | timelock `0xDEa75A312b2F99b5A7558c4636897b39C195E241` |
| Wildcat Protocol | Ethereum | `0xfEB516d9D946dD487A9346F6fee11f40C6945eE4` | no | multisig safe `0xC15bE5214978d1fc509ECdd4f9D5BC067C94D9Ae` (3-of-5) |
| InceptionLRT (Isolated Restaking) | Ethereum | `0x814CC6B8fd2555845541FB843f37418b05977d8d` | yes | contract controller `0xB81e55e7Ee6B286aF6abFEa4eFad83f7BA4D1f1e` |
| The Idols | Ethereum | `0x9416bA76e88D873050A06e5956A3EBF10386b863` | no | none readable |
| FermiSwap | Ethereum | `0xb1076fE3AB5e28005C7c323Bac5AC06a680d452e` | no | none readable |
| cVault Finance | Ethereum | `0x62359Ed7505Efc61FF1D56fEF82158CcaffA23D7` | no | eoa `0x5A16552f59ea34E44ec81E58b3817833E9fD5436` |
| Injective Bridge | Ethereum | `0xe28b3B32B6c345A34Ff64674606124Dd5Aceca30` | no | none readable |
| PoolTogether V3 | Ethereum | `0x0cEC1A9154Ff802e7934Fc916Ed7Ca50bDE6844e` | no | none readable |
| Pickle | Ethereum | `0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5` | no | contract controller `0xbD17B1ce622d73bD438b9E658acA5996dc394b0d` (2-of-6) |
| Easedefi.org | Ethereum | `0xEa5eDef1287AfDF9Eb8A46f9773AbFc10820c61c` | no | none readable |
| OpenGDP Shared Security | Ethereum | `0x54e44DbB92dBA848ACe27F44c0CB4268981eF1CC` | yes | timelock `0x275ac9C64eF372f528F7c87D3a987D1e3d76Ca65` |
| Legion | Ethereum | `0xa0BeB0A8C765482c128a2986c063AF5C3171ff2F` | no | contract controller `0x4a7aCA57A685c9E893F60a716415E5e588500533` (2-of-3) |
| Hakka Finance | Ethereum | `0x0E29e5AbbB5FD88e28b2d355774e73BD47dE3bcd` | no | multisig safe `0xF2B8f214Dc81b849ed3BDCAEdA6c8c39625c500A` (2-of-4) |
| Abracadabra Spell | Ethereum | `0x090185f2135308BaD17527004364eBcC2D37e5F6` | no | multisig safe `0xDF2C270f610Dc35d8fFDA5B453E74db5471E126B` (2-of-3) |
| Zora Bridge | Base | `0x1111111111166b7FE7bd91427724B487980aFc69` | no | none readable |
| Arkis | Ethereum | `0xEA623eebd9c5bFd56067e36C89Db0C13e6c70ba8` | yes | contract controller `0x324adD185708E4Cc85546085849a27b9Ba75f0Bb` |
| Steer Protocol | Ethereum | `0xCEBF1A54A9Ce703FC80967760b5A6cbDb4111099` | yes | contract controller `0xEB2D829FFbE494FC6535b0E4EB807EFd4b6BF0Bd` (2-of-5) |
| Stafi | Ethereum | `0xef3A930e1FfFFAcd2fc13434aC81bD278B0ecC8d` | no | none readable |
| Eigenpie | Ethereum | `0x20b70E4A1883b81429533FeD944d7957121c7CAB` | yes | contract controller `0xaF69B55b083AB19893D5Ff18213b3E67875E01F3` (3-of-7) |
| Gondi V3 | Ethereum | `0xf65B99CE6DC5F6c556172BCC0Ff27D3665a7d9A8` | no | eoa `0xE9c9Ef882f534a21d74b084845348044d03aca85` |
| Spectra MetaVaults | Base | `0x64FCC3A02eeEba05Ef701b7eed066c6ebD5d4E51` | yes | contract controller `0xAA8578C937f8Ce1eDb10477817FfA424EdfAE6fc` |
| Hop Protocol | Ethereum | `0xc5102fE9359FD9a28f877a67E36B0F050d81a3CC` | no | timelock `0xeeA8422a08258e73c139Fc32a25e10410c14bd7a` |
| SoSoValue Basis | Base | `0x624e2e7fDc8903165F64891672267AB0FCB98831` | no | none readable |
| Ribbon | Ethereum | `0x6123B0049F904d730dB3C36a31167D9d4121fA6B` | no | none readable |
| Tangent Finance | Ethereum | `0x214C8A1023B30032a2Eded109146658C6D6F2781` | no | multisig safe `0x461B62CB3A7e9Df8f800aE058AE92F855F2c27Ca` (3-of-5) |
| Unslashed | Ethereum | `0xE0e05c43c097B0982Db6c9d626c4eb9e95C3b9ce` | no | none readable |
| Symbiosis | Ethereum | `0xd38BB40815d2B0c2d2c866e0c72c5728ffC76dd9` | no | none readable |
| Pirex | Ethereum | `0xc55126051B22eBb829D00368f4B12Bde432de5Da` | no | none readable |
| Bio Protocol | Ethereum | `0xcb1592591996765Ec0eFc1f92599A19767ee5ffA` | no | multisig safe `0xE57a09C3fdFb6bD2B8Ebc46E0FF884876fae60Fd` (3-of-6) |
| ZTLN-P | Ethereum | `0xfEd3D6557Dc46A1B25d0A6F666513Cb33835864B` | yes | none readable |
| iAero Protocol | Base | `0x7ee8964160126081cebC443a42482E95e393e6A8` | no | none readable |
| Ledgity Yield | Ethereum | `0x482dF7483a52496F4C65AB499966dfcdf4DDFDbc` | no | multisig safe `0x30Fa557608017afB6E8e4ABe8027787C00473FF0` (2-of-3) |

## 10. Published RPC-pinned protocols moved to the Sprint 27 pins

- Extra Finance (Base): `0xBB505c54D71E9e599cB8435b4F0cEEc05fC71cbD` (Base) — bytecode keccak256 `0x2bda3204356bb12a5b68e82c0408773da0a9c311b37996552ee4e9e6756623e8`, EIP-1967 slots and controller unchanged at `#58956515`.
- Origin Protocol (SuperOETHb Base): `0xDBFeFD2e8460a6Ee4955A68582F85708BAEA60A3` (Base) — bytecode keccak256 `0x1ab9c11f4c97800cad045510e6c2ceafc40074dd151fd1ed56bd75c61a0b0421`, EIP-1967 slots and controller unchanged at `#58956515`.
- Seamless Protocol (Base): `0x0E02EB705be325407707662C6f6d3466E939f3a0` (Base) — bytecode keccak256 `0x22818496ed85629596372dcbe81fbc48c729489bdf829e198040b0f06fc4f58f`, EIP-1967 slots and controller unchanged at `#58956515`.
- Superform Core v2 (Base): `0xB5396ef2bF8CA360cEB4166b77AFb2bed20e74d4` (Base) — bytecode keccak256 `0x4dfe0bcd9f94f3d29d1dbbce22b6eb4192acf8d3108cc253ab28a51ec7caeff4`, EIP-1967 slots and controller unchanged at `#58956515`.
- 3F: `0x54F862fa0612A8709F6Dec4A7B39AF015CD4E82E` (Ethereum) — bytecode keccak256 `0x4690b1cca8e819c6cf7d976ae8e296e41138d1a2d722c8d07b3394d431fc226e`, EIP-1967 slots and controller unchanged at `#26440048`.
- Aegis YUSD: `0x4274cD7277C7bb0806Bd5FE84b9aDAE466a8DA0a` (Ethereum) — bytecode keccak256 `0x673a34bc4b7ddbb2aaf2ff848f3fe7734a98331af20f2f0f55bca5dd131c39ff`, EIP-1967 slots and controller unchanged at `#26440048`.
- Aera V3: `0x29722cC9a1cACff4a15914F9bC274B46F3b90B4F` (Ethereum) — bytecode keccak256 `0xf4d329ab04c7cdbab16fe48996f83e05fbbdb9222305402bc9049c842ec5cfe7`, EIP-1967 slots and controller unchanged at `#26440048`.
- Alchemix V3: `0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF` (Ethereum) — bytecode keccak256 `0x7ed5fbbd93fd174456aa5a52eab2c19ac15bbb6e07f08667b859ac41819f5208`, EIP-1967 slots and controller unchanged at `#26440048`.
- Anemoy Capital: `0x8c213ee79581Ff4984583C6a801e5263418C4b86` (Ethereum) — bytecode keccak256 `0x7d02f853cd5ee5a6aa0a08213618a6f3c3d594d4c030be909d0e894b6a37c749`, EIP-1967 slots and controller unchanged at `#26440048`.
- AO Bridge: `0xfE08D40Eee53d64936D3128838867c867602665c` (Ethereum) — bytecode keccak256 `0x53c0835906d5b2eed9f973e77d7c785956ea1d182c80679951ae09c4cfaa13c1`, EIP-1967 slots and controller unchanged at `#26440048`.
- Arrakis Modular: `0x820FB8127a689327C863de8433278d6181123982` (Ethereum) — bytecode keccak256 `0x176874457b5b43c103a1f9c14b3d3d70e062df3a08fb6d56e95decf4372d57b6`, EIP-1967 slots and controller unchanged at `#26440048`.
- Aster Bridge: `0x604DD02d620633Ae427888d41bfd15e38483736E` (Ethereum) — bytecode keccak256 `0x0959a24babb02d4d6c6ef27aaec9c34e824a2c55d24b13a8b3dae8401138e1c4`, EIP-1967 slots and controller unchanged at `#26440048`.
- AUTOfinance: `0x2218F90A98b0C070676f249EF44834686dAa4285` (Ethereum) — bytecode keccak256 `0x851c7bea863541332656d77df23c217c5013416390dcefce9992f95655446c1e`, EIP-1967 slots and controller unchanged at `#26440048`.
- Avalon Superearn: `0x5c8D0C48810FD37A0A824D074ee290E64f7A8Fa2` (Ethereum) — bytecode keccak256 `0xe5e3693157141608a301682c8c228c0277eac7efc0b98b57f874ca49752b5fd8`, EIP-1967 slots and controller unchanged at `#26440048`.
- BitFi Basis: `0xCdFb58c8C859Cb3F62ebe9Cf2767F9e036C7fb15` (Ethereum) — bytecode keccak256 `0x168f6bb27d4410c24923a1fa9ccad3e18530a1bdaa23935960b410be0aa1409c`, EIP-1967 slots and controller unchanged at `#26440048`.
- CIAN Yield Layer: `0xB13aa2d0345b0439b064f26B82D8dCf3f508775d` (Ethereum) — bytecode keccak256 `0xe56c30257588d9d02e1a523887f333c31fb17cc1f0b6ffc871685d836403c24f`, EIP-1967 slots and controller unchanged at `#26440048`.
- Concentrator: `0xb3Ad645dB386D7F6D753B2b9C3F4B853DA6890B8` (Ethereum) — bytecode keccak256 `0xce1d4da3ce85dfe2287a99b988ea0393a3d3c08472adbb065266e798585682f2`, EIP-1967 slots and controller unchanged at `#26440048`.
- Derive V3 Options: `0xB1D1eae60EEA9525032a6DCb4c1CE336a1dE71BE` (Ethereum) — bytecode keccak256 `0x4b19308ff101c086627922584dfdf6fb6f57828ecd7b0d5e84cea7cc36e2ca2b`, EIP-1967 slots and controller unchanged at `#26440048`.
- Frankencoin: `0xDb861830D9Ae2d1fCF99fA0cfd3973de382B0B5b` (Ethereum) — bytecode keccak256 `0x9dacc056e5f2d59b75a9c9ae8a3cd5134abf7bfb675462f50c12ab777603cc62`, EIP-1967 slots and controller unchanged at `#26440048`.
- Grvt Bridge: `0xAD29F2723fcdBcF665F210F25E06f97477e417cF` (Ethereum) — bytecode keccak256 `0x61f4a7aa2e0a3dcc40aa8314f37f612c0d4705c416a2bbe73430f130a25297c5`, EIP-1967 slots and controller unchanged at `#26440048`.
- Hyperlane: `0x6D265C7dD8d76F25155F1a7687C693FDC1220D12` (Ethereum) — bytecode keccak256 `0xa88000255e1f96de07122238840c31fd0b48f520430ff6dd78b7100dfc738358`, EIP-1967 slots and controller unchanged at `#26440048`.
- IDEX V1: `0xB705268213D593B8FD88d3FDEFF93AFF5CbDcfAE` (Ethereum) — bytecode keccak256 `0x41a6bbcc6ebf380d013e5bf81e1f04f14177e26857360fdb5fb0d96ab290b6a3`, EIP-1967 slots and controller unchanged at `#26440048`.
- K3 Capital: `0xdC47953c816531a8CA9E1D461AB53687d48EEA26` (Ethereum) — bytecode keccak256 `0xf44809e3d915cd908b4db54ad7e3de8d0923d8c68119d754ef9566c10573fd5e`, EIP-1967 slots and controller unchanged at `#26440048`.
- KPK: `0xbF3F63D8AC133B16d7D50C015036b33219Dd8D23` (Ethereum) — bytecode keccak256 `0xb42b049d6057086c893bdf4bb08f8b6c9bfdbe3ab5c506495470d81a87e7be3f`, EIP-1967 slots and controller unchanged at `#26440048`.
- Lighter Bridge: `0x232CE3bd40fCd6f80f3d55A522d03f25Df784Ee2` (Ethereum) — bytecode keccak256 `0x509f7c0bd6c3e1d958030033e1e1e3ae1be166bbbefd2e8d8835fa72ba1a4236`, EIP-1967 slots and controller unchanged at `#26440048`.
- Makina: `0x8d28A69328561eF9F171c58996fEcB9F494e070c` (Ethereum) — bytecode keccak256 `0xe341d27c127cb10717cc907341d920ba2279dfd64657892fb9411607895a2e08`, EIP-1967 slots and controller unchanged at `#26440048`.
- Noon: `0xdA67B4284609d2d48e5d10cfAc411572727dc1eD` (Ethereum) — bytecode keccak256 `0xc961838fce3287ae2c0a9677e4ae834840d6c90947f96e286d88b13299c04900`, EIP-1967 slots and controller unchanged at `#26440048`.
- Origami Finance: `0x07c5500359161b81eb0DfFF83097d5025D3cF5A2` (Ethereum) — bytecode keccak256 `0x62d6e97082d84feec6a1fb354b9279aa8ceb6b7ffaf88d1bb82e9225bf1553e3`, EIP-1967 slots and controller unchanged at `#26440048`.
- PancakeSwap AMM V3: `0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865` (Ethereum) — bytecode keccak256 `0x8191d3ab1d55d3da9822199f28865415c99566b6f1aee4a4b16713f57930678c`, EIP-1967 slots and controller unchanged at `#26440048`.
- RockawayX: `0x953972ea0C1703c58F09FB6fD2477Fdcf0FEe074` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26440048`.
- Saturn: `0x23238f20b894f29041f48D88eE91131C395Aaa71` (Ethereum) — bytecode keccak256 `0x6d0ce32ba65bd273fcbdc767be5fd8924abd4ce0d6fb5c84ba39c28be05d2457`, EIP-1967 slots and controller unchanged at `#26440048`.
- Shift DeFi: `0x1d71c888961c4600cF0E31F6196b4dA7fE72e4B3` (Ethereum) — bytecode keccak256 `0xd07150498af17b4f1d7cef45227180255479fe3e1f529a027ffd6a716023e904`, EIP-1967 slots and controller unchanged at `#26440048`.
- Sierra Protocol: `0xe1b1252652A2FF0CC3A4214eE73d9FeD1FEa5b4f` (Ethereum) — bytecode keccak256 `0x1151e0ba784b3fe266ae02886e6435603745e3e3b288a9f5ad182737b0faa1ac`, EIP-1967 slots and controller unchanged at `#26440048`.
- Sonic Gateway: `0xa1E2481a9CD0Cb0447EeB1cbc26F1b3fff3bec20` (Ethereum) — bytecode keccak256 `0x23a1472fa83f7542cf6eecb7637465cd72aa2470d206dd81dcfe9d1db4e8c633`, EIP-1967 slots and controller unchanged at `#26440048`.
- Starknet Bridge: `0xCa14007Eff0dB1f8135f4C25B34De49AB0d42766` (Ethereum) — bytecode keccak256 `0x7ef33cd5b6004a6c025dee0df472999ec54227ba2a7ab0b612537ca5219ee275`, EIP-1967 slots and controller unchanged at `#26440048`.
- Team Finance: `0xCC4304A31d09258b0029eA7FE63d032f52e44EFe` (Ethereum) — bytecode keccak256 `0x17404120e429d743f170be02a42dd5018a3d340863ef7c7bf41db1baab1a1cd7`, EIP-1967 slots and controller unchanged at `#26440048`.
- Theo Network thUSD: `0xa3fE5c7596024E6811E14F029937D5bd8Ae485b3` (Ethereum) — bytecode keccak256 `0xc8ff19e35002275bcbf9f8eede7c2030293c871666ff06c9eb19933826d81271`, EIP-1967 slots and controller unchanged at `#26440048`.
- Tori Finance: `0xd0580192E98eA6CEB9c7b6191Ed2E27560911697` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26440048`.
- Tornado Cash: `0x77777FeDdddFfC19Ff86DB637967013e6C6A116C` (Ethereum) — bytecode keccak256 `0x7bb3883a4af95ea24983177dbcb682a021f389b77835ed266bfa30bda271c77b`, EIP-1967 slots and controller unchanged at `#26440048`.
- UNCX Network V2: `0xaDB2437e6F65682B85F814fBc12FeC0508A7B1D0` (Ethereum) — bytecode keccak256 `0x9ef6c8d303308ae4c0cfd6466aff6fd25946facfdeb76992707386a34ae5879f`, EIP-1967 slots and controller unchanged at `#26440048`.
- USDT0: `0x6C96dE32CEa08842dcc4058c14d3aaAD7Fa41dee` (Ethereum) — bytecode keccak256 `0xe5e3693157141608a301682c8c228c0277eac7efc0b98b57f874ca49752b5fd8`, EIP-1967 slots and controller unchanged at `#26440048`.
- Veda: `0x5232bc0F5999f8dA604c42E1748A13a170F94A1B` (Ethereum) — bytecode keccak256 `0xf349ba5ac81eb0f8ad05e353e581928b157ebce878db155eaea6f4534cb5fe2b`, EIP-1967 slots and controller unchanged at `#26440048`.
- Vesper V1: `0x1b40183EFB4Dd766f11bDa7A7c3AD8982e998421` (Ethereum) — bytecode keccak256 `0xba07561c735fba86dbd82e49796f72808ddf1b2f8c0d202aeaff2b05cd98eb0b`, EIP-1967 slots and controller unchanged at `#26440048`.
- World Chain Bridge: `0x90BB48fe3310499Db36437dCAE642F721e32d094` (Ethereum) — bytecode keccak256 `0xfa8c9db6c6cab7108dea276f4cd09d575674eb0852c0fa3187e59e98ef977998`, EIP-1967 slots and controller unchanged at `#26440048`.
- xDAI Stake Bridge: `0x0Ae055097C6d159879521C384F1D2123D1f195e6` (Ethereum) — bytecode keccak256 `0xc142222c43ea630db16763d6dd8e619a9cecc3bf121785475841cdc9f94361b7`, EIP-1967 slots and controller unchanged at `#26440048`.
- Yield Basis: `0x01791F726B4103694969820be083196cC7c045fF` (Ethereum) — bytecode keccak256 `0xb6dd52f54a35ee897ad6edc361c7dd1ce400f92031dc4b536514bf984f327777`, EIP-1967 slots and controller unchanged at `#26440048`.
- Zama: `0xA12CC123ba206d4031D1c7f6223D1C2Ec249f4f3` (Ethereum) — bytecode keccak256 `0xf172c8c96f8ba07e22f43c9bd9f1d3b96d1dbae326c61b388b4fbd7b517f9123`, EIP-1967 slots and controller unchanged at `#26440048`.
- ZEROBASE CeDeFi: `0xfAB99fCF605fD8f4593EDb70A43bA56542777777` (Ethereum) — bytecode keccak256 `0x5ea0a98719770123cf8cb56ed504a5975019e01868505874dc2fb31b034a7cfe`, EIP-1967 slots and controller unchanged at `#26440048`.
