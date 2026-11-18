# Sprint 28 Protocol Commitment Summary — Block `26441165`

- **Ethereum Mainnet pin**: `26441165` (`0x19375cd`), canonical block hash `0x5182be2c61af5f48ed2ec43d3c177dedad257c4e966a7e384120829de73901d9`, timestamp `2026-11-18 09:52:23 UTC` (`1794995543`); the `finalized` head, both endpoints returning the same number and hash
- **Base Mainnet pin**: `59025642` (`0x384a8ea`), canonical block hash `0x8fc618f8e02aa1fd1c3bcf1300fd25e40291a0fcde351bd39ad8cb61781d5e12`, timestamp `2026-11-18 09:51:44 UTC` (`1794995504`); the `finalized` head, both endpoints returning the same number and hash
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI), bulk harvester v2.0. Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode` batched through Multicall3 at the pinned block, on two independent RPCs per chain with identical block hashes: `ethereum-rpc.publicnode.com` + `rpc.mevblocker.io` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base). Documentation: HTTP-200 first-party snapshots named by their SHA-256; every quote below is an exact substring of its snapshot's text and every value is re-derived from the pinned reads by the validator (no model output is trusted). The 11 targets added after the pin (bounty-s28-40-acres, bounty-s28-defi-saver, bounty-s28-firm-policy, bounty-s28-firm-staleness, bounty-s28-upshift, bounty-s28-vesper, bounty-s28-yearn, strata-markets--rescore, supernova-cl, usdt0--rescore, zircuit-staking--rescore) were read at the same block numbers and hashes through two archive-capable endpoints per chain whose block hashes match the pin: `rpc.mevblocker.io` + `gateway.tenderly.co` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base). The 1 targets added after the pin (idle) were read at the same block numbers and hashes through two archive-capable endpoints per chain whose block hashes match the pin: `rpc.mevblocker.io` + `eth.drpc.org` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base). The merged bounty records' values were re-read by their own check (`bounty-check-s28.json`) at the same block numbers and hashes through `rpc.mevblocker.io` + `eth.drpc.org` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base).
- **Result**: `17` records for `16` protocols (`11` new; published protocols with a new record: Inverse Finance (FiRM), Yearn V3, Strata Markets, Vesper V1, Zircuit Staking) — `9` aligned baselines, `1` protective delta, `7` parameter deltas. `verifiedCount = 10`. `driftCount = 7`, the same convention as Sprints 1–27 and `PactaSentinelGuard` (`driftCount != 0` means drift).
- **RPC-pinned promotions (not attested)**: `69` further new protocols are published as RPC-pinned control-plane records at the same pins (listed below); the `127` RPC-pinned protocols already published move to these pins with every stated fact re-read: world-chain-bridge's controller Safe is now 3-of-6 (was 3-of-8). They carry no Base EAS UID. `3` published RPC-pinned protocols are documentation-compared for the first time and become Base-EAS protocols here (Strata Markets, Vesper V1, Zircuit Staking); their RPC-pinned records are retired.
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); Base reads are taken at the Base pin.

## 1. Steakhouse Prime USDC (Base) — Steakhouse Prime USDC (Base) timelock: 7-day minimum delay, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Steakhouse Prime USDC (Base) MetaMorphoV1_1** | `0xBEEFE94c8aD530842bfE7d8B397938fFc1cb83b2` | `timelock()` | Steakhouse Prime USDC (Base) MetaMorphoV1_1 0xBEEFE94c8aD530842bfE7d8B397938fFc1cb83b2 (Base): timelock() = 604800s (7 d). (Base `#59025642`) |
| **Steakhouse Prime USDC (Base) MetaMorphoV1_1** | `0xBEEFE94c8aD530842bfE7d8B397938fFc1cb83b2` | `guardian()` | Steakhouse Prime USDC (Base) MetaMorphoV1_1 0xBEEFE94c8aD530842bfE7d8B397938fFc1cb83b2 (Base): guardian() = 0x894d59017Ed0F8dcd8f2B6e89a3C26eF76876D33 (a contract). (Base `#59025642`) |

Classification: **aligned baseline** (2 records).
- 'Steakhouse vaults 7-day timelocks (above the minimum, protocol-enforced 3-day timelock), forcing a 7-day delay between any proposed market into a Steakhouse vault and the ability to deploy deposited assets into the new market.' (www.steakhouse.financial/docs/risk-management/monitoring/vault-setup-and-controls) (snapshot sha256 `b615b95203bc08c4d05ebb5f340abafb80ba0fc540ab7b5b4538ab66a62a7f11`)
- 'Seeking to provide depositors with even more control over their funds and curated vaults, Steakhouse introduced the Aragon DAO guardian to enable vault depositors to veto critical actions made by the curator.' (www.steakhouse.financial/docs/risk-management/monitoring/vault-setup-and-controls) (snapshot sha256 `b615b95203bc08c4d05ebb5f340abafb80ba0fc540ab7b5b4538ab66a62a7f11`)

## 2. Wintermute Confidential WBTC (Ethereum) — Wintermute Confidential WBTC (Ethereum) multisig: 3-of-6 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Wintermute Confidential WBTC (Ethereum) Safe** | `0x4687E45bB5518a995913a24BB2816fe2031d74D8` | `getThreshold()` | Wintermute Confidential WBTC (Ethereum) Safe 0x4687E45bB5518a995913a24BB2816fe2031d74D8 (Ethereum): getThreshold() = 3 of getOwners() = 6 owners (Safe v1.4.1); it controls VaultV2 0x3d5EcCb62974178236A768A7ef14D3ce468Fbe91. (Ethereum `#26441165`) |

Classification: **aligned baseline** (1 record).
- '| Curator | [Safe Multisig 3/6](https://etherscan.io/address/0x4687e45bb5518a995913a24bb2816fe2031d74d8) |' (armitage.wintermute.com/llms-full.txt) (snapshot sha256 `1efcdb5fcc2471683b5b213c98d36ddaf1c9424054055e1fb1084ec76d6c3735`)

## 3. Asymmetry Finance — Asymmetry Finance SimpleProxy: upgradeable (UUPS), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Asymmetry Finance SimpleProxy** | `0x00000069aBbB0B1Ad6975bcF753eEe15D318A0BF` | slot `eip1967.proxy.implementation` | Asymmetry Finance SimpleProxy 0x00000069aBbB0B1Ad6975bcF753eEe15D318A0BF (Ethereum): EIP-1967 implementation slot = 0xb628B1fdbE8C01777aEa2bF3bd386df4Af84e8d3; upgradeable (EIP-1967 implementation exposing upgradeToAndCall (UUPS)). (Ethereum `#26441165`) |

Classification: **aligned baseline** (1 record).
- 'The Votium Strategy Contract (ERC1967 proxy) 0x00000069aBbB0B1Ad6975bcF753eEe15D318A0BF' (docs.asymmetry.finance/developers/contracts.md) (snapshot sha256 `5c3d72ea287f0b0b86ec13a56e2f43f030f7e1906495ab28d47842362dd66368`)

## 4. KyberSwap Classic — KyberSwap Classic KyberNetworkTokenV2 proxy: upgradeable (proxy admin), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **KyberSwap Classic KyberNetworkTokenV2 proxy** | `0xdeFA4e8a7bcBA345F687a2f1456F5Edd9CE97202` | slot `eip1967.proxy.implementation` | KyberSwap Classic KyberNetworkTokenV2 proxy 0xdeFA4e8a7bcBA345F687a2f1456F5Edd9CE97202 (Ethereum): EIP-1967 implementation slot = 0xe5E8E834086F1a964f9A089eB6Ae11796862e4CE, admin slot = 0x500180A94cB854e98770872AF4E4BB1dD67Af559; upgradeable (EIP-1967 implementation + admin slot (transparent proxy)). (Ethereum `#26441165`) |

Classification: **aligned baseline** (1 record).
- 'KNC is dynamic and can be upgraded or minted by KyberDAO to better support liquidity and growth.' (docs.kyberswap.com/governance/knc-token.md) (snapshot sha256 `17a3cce22e03a7def2c537d1070e82e5c8ec1f596e70632233c1c130910ebacc`)

## 5. MCDEX — DAO: 4-of-8 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **DAO Safe** | `0x38ca50c6E3391A5bf73c2504bd9Cd9c0b9D89053` | `getThreshold()` | DAO Safe 0x38ca50c6E3391A5bf73c2504bd9Cd9c0b9D89053 (Ethereum): getThreshold() = 4 of getOwners() = 8 owners (Safe v1.1.1); it controls AdminUpgradeabilityProxy 0x4e352cF164E64ADCBad318C3a1e222E9EBa4Ce42. (Ethereum `#26441165`) |

Classification: **aligned baseline** (1 record).
- 'DAO uses a multi-sig on each chain, and each multi-sig requires the confirmation of 4 out of 8 owners.' (docs.mux.network/protocol/contracts/contracts-dao.md) (snapshot sha256 `faf96e3a1c78e371b1a9d6ab15dc8a4e3d28bf94fed3e79952a74d054e1bd45e`)

## 6. DIEM Relay — DIEM Relay multisig: 2-of-2 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **DIEM Relay Safe** | `0x01Ea790410D9863A57771D992D2A72ea326DD7C9` | `getThreshold()` | DIEM Relay Safe 0x01Ea790410D9863A57771D992D2A72ea326DD7C9 (Base): getThreshold() = 2 of getOwners() = 2 owners (Safe v1.4.1). (Base `#59025642`) |

Classification: **aligned baseline** (1 record).
- 'Admin / operator 2-of-2 Safe — 0x01Ea790410D9863A57771D992D2A72ea326DD7C9' (diem-relay.com/docs) (snapshot sha256 `495bb1c547f88d09e1d5e4689fb7a2e83d49e4a5559772249f870ee62cf01f81`)

## 7. APY Finance — APY Finance APYPoolTokenProxy: upgradeable (proxy admin), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **APY Finance APYPoolTokenProxy** | `0xe18b0365D5D09F394f84eE56ed29DD2d8D6Fba5f` | slot `eip1967.proxy.implementation` | APY Finance APYPoolTokenProxy 0xe18b0365D5D09F394f84eE56ed29DD2d8D6Fba5f (Ethereum): EIP-1967 implementation slot = 0xDD0fC21319C4cA133A758f9893028Aac834e8493, admin slot = 0x7965283631253DfCb71Db63a60C656DEDF76234f; upgradeable (EIP-1967 implementation + admin slot (transparent proxy)). (Ethereum `#26441165`) |

Classification: **aligned baseline** (1 record).
- 'The liquidity pool contracts use a proxy pattern for upgradeability.' (docs.apy.finance/smart-contract-integration/liquidity-mining-pool.md) (snapshot sha256 `619bdd74f0d92eaaa656fe20f006a5c6865844ead760ea9e7b81281c99b0809c`)

## 8. Whales Market — Whales Market TransparentUpgradeableProxy: docs describe it as immutable, but it is an upgradeable proxy

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Whales Market TransparentUpgradeableProxy** | `0x1eCdB32e59e948C010a189a0798C674a2d0c6603` | slot `eip1967.proxy.implementation` | Whales Market TransparentUpgradeableProxy 0x1eCdB32e59e948C010a189a0798C674a2d0c6603 (Ethereum): EIP-1967 implementation slot = 0x623620b3Eff4e1A30e9f1154f88198Ab26952EeB, admin slot = 0xeB5E772919661F455619A4cABd9B2b64715505E6; upgradeable (EIP-1967 implementation + admin slot (transparent proxy)). (Ethereum `#26441165`) |

Classification: **parameter delta** (1 record).
- 'Your deposited funds will be sent to and stored in an escrow secured by **an immutable smart contract,**' (docs.whales.market/llms-full.txt) (snapshot sha256 `3e46b41a1b55dff30ab8e4148c4ec6c25f78b070c50b85818b05e0bfe723f428`)

## 9. Upshift — Vault ProxyAdmin multisig: docs state generally 4 of 6, the Safe is 2-of-3

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Upshift vault ProxyAdmin owner Safe** | `0x4107557d726933f0BcA591A4218Afc92978457F7` | `getThreshold()` | Upshift vault 0xE9B725010A9E419412ed67d0fA5f3A5f40159D32 (Ethereum): EIP-1967 admin slot = ProxyAdmin 0xB5fBf201A35327Ddd89986FfA60CF5A675B2bDbc, whose owner() = Safe 0x4107557d726933f0BcA591A4218Afc92978457F7 with getThreshold() = 2 of getOwners() = 3 owners; the vault's owner() is a separate Safe 0x17ab7568Cd5386DF6C8E4552438E32794D057cC1 (2-of-3). (Ethereum `#26441165`) |

Classification: **parameter delta** (1 record).
- 'Upgrades to the vault's code are approved by the ProxyAdmin multisig. It is generally a 4 of 6 Gnosis Safe with two signers each from the asset issuer, Upshift and the curator, so no single party can upgrade a vault alone.' (docs.upshift.finance/vault-architecture/risk-controls) (snapshot sha256 `f3a59246b1d08fc8ccc3e8b935bb4a015e2fd773e9db8d58af98da379945626f`)

## 10. 40 Acres (Base) — Lending vault proxy: docs call the contracts immutable, but it is an upgradeable proxy

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **40 Acres vault proxy (UUPS)** | `0x87f18b377e625b62c708D5f6EA96EC193558EFD0` | slot `eip1967.proxy.implementation` | 40 Acres proxy 0x87f18b377e625b62c708D5f6EA96EC193558EFD0 (Base): EIP-1967 implementation slot = 0xb43b30c405c61BC330227968635d130994450735; the implementation's proxiableUUID() = the EIP-1967 slot (UUPS), UPGRADE_INTERFACE_VERSION() = '5.0.0'; owner() = 0xfF16fd3D147220E6CC002a8e4a1f942ac41DBD23, a Safe 2-of-3. (Base `#59025642`) |

Classification: **parameter delta** (1 record).
- '40 Acres has completed four independent audits with Sherlock. Smart contracts are immutable and non-upgradeable post-deployment.' (docs.40acres.finance) (snapshot sha256 `5ff4b426e58b680e68f5e36ec1837e35d0f1d1674de981f70de38facba2c4b4c`)

## 11. DeFi Saver — AdminVault Owner multisig: docs state 3/5, the Safe is 3-of-6

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **DeFi Saver Owner Safe** | `0xBc841B0dE0b93205e912CFBBd1D0c160A1ec6F00` | `getThreshold()` | DFSRegistry 0x287778F121F134C66212FB16c9b53eC991D32f5b adminVault() = AdminVault 0xCCf3d848e08b94478Ed8f46fFead3008faF581fD; AdminVault.owner() = Safe 0xBc841B0dE0b93205e912CFBBd1D0c160A1ec6F00 (Ethereum) with getThreshold() = 3 of getOwners() = 6 owners (Safe v1.3.0). (Ethereum `#26441165`) |

Classification: **parameter delta** (1 record).
- 'Automation contracts are upgradeable, with any upgrades being locked behind a 24h timelock which can be activated by a 2/3 multisig (Admin) with actual upgrades initiable by a different 3/5 multisig (Owner).' (docs.defisaver.com/protocol/security-and-audits/admin-access-control) (snapshot sha256 `b389f1a251c423327bba0b6e01241d9f501e6a8c5b60aea035dc126d9eaedf81`)

## 12. Inverse Finance (FiRM) — BorrowController stalenessThreshold (sDOLA market): 86,500 s at the Sprint pin, 0 (check off) at the #26,406,106 pin

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **FiRM BorrowController** | `0x01ECA33e20a4c379Bd8A5361f896A7dd2bAE4ce8` | `stalenessThreshold(address)` | FiRM BorrowController 0x01ECA33e20a4c379Bd8A5361f896A7dd2bAE4ce8 (Ethereum): stalenessThreshold(sDOLA market 0xC45E9c231ab5D9Bd3F1131E7901B100D8D236C4d) = 86500s (24.03 h) at this pin. At Pacta's prior pin #26,406,106 (record inverse-firm-borrowcontroller-staleness-sentinel) it read 0, which switches the oracle staleness check off; the value read now equals the 86,500 s change that record observed queued. The docs describe a typical 1-24 hour range, not a hard maximum. (Ethereum `#26441165`) |

Classification: **protective delta** (1 record).
- 'Every collateral market on FiRM has a maximum allowed age for price data, typically set between 1-24 hours depending on the asset's oracle characteristics.' (docs.inverse.finance/inverse-finance/inverse-finance/products/firm/firm-security-and-safety.md) (snapshot sha256 `c9946f02ff3ce1555bf74daf68490d796af0f17a66057ba5c314c90c30e2d9c5`)

## 13. Yearn V3 — yChad governance Safe: documented signer 0x6F2A…eAD6 is no longer an owner

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **yChad Governance Safe** | `0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52` | `getOwners()` | yChad Safe 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52 (Ethereum): getThreshold() = 6 of getOwners() = 9 owners; 0x6F2A8Ee9452ba7d336b3fba03caC27f7818AeAD6 is not among getOwners(). (Ethereum `#26441165`) |

Classification: **parameter delta** (1 record).
- '| [0x6F2A8Ee9452ba7d336b3fba03caC27f7818AeAD6](https://etherscan.io/address/0x6F2A8Ee9452ba7d336b3fba03caC27f7818AeAD6) | Mariano Conti (nanexcool.com, prev. MakerDAO) |' (raw.githubusercontent.com/yearn/yearn-devdocs/master/docs/developers/security/multisig.md) (snapshot sha256 `ed21a11525d54f99ad0564be7b8ee378f1a97f3dccbc20302074e3d8663de595`)

## 14. Strata Markets — Strata Markets multisig: 2-of-3 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Strata Markets Safe** | `0x4be3749a0F6557b8fd98F3967e859DbD7C694eF4` | `getThreshold()` | Strata Markets Safe 0x4be3749a0F6557b8fd98F3967e859DbD7C694eF4 (Ethereum): getThreshold() = 2 of getOwners() = 3 owners (Safe v1.4.1). (Ethereum `#26441165`) |

Classification: **aligned baseline** (1 record).
- '**Operational Multisig** * 2-of-3 Gnosis Safe' (docs.strata.markets/technical-documentation/contracts-details.md) (snapshot sha256 `b474cb3cdbdb4112dfdb8ec63ec9ebe14b30e08b12aaf532601333a8b12c5f60`)

## 15. Vesper V1 — Pool governor multisig: docs state 3 of 5 signers, the Safe is 3-of-6

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Vesper governor Safe** | `0x9520b477Aa81180E6DdC006Fc09Fb6d3eb4e807A` | `getThreshold()` | Vesper governor Safe 0x9520b477Aa81180E6DdC006Fc09Fb6d3eb4e807A (Ethereum): getThreshold() = 3 of getOwners() = 6 owners (Safe v1.3.0); governor() of the Vesper pools 0xd1C117319B3595fbc39b471AB1fd485629eb05F2, 0x3aEd4dd0b5ba616156Fa352274670c18D2Ec2A81, 0x025a05f1967521806BB4c8a10Ba4b8c00A794F65 is this Safe, which is also the published controller of the VSP token record. (Ethereum `#26441165`) |

Classification: **parameter delta** (1 record).
- 'Multisig is a contract where n people vote on transaction before it gets executed. The Vesper multisig has 5 signers and requires 3 yes votes for a transaction to execute.' (docs.vesper.finance/vesper-pools-and-strategies/vespers-modular-pool-architecture) (snapshot sha256 `8b4fa43d283fb62fe3d080789787fd15c83002210baa0415e23d9e261069097b`)

## 16. Zircuit Staking — Zircuit Staking multisig: docs state 6-of-8, the Safe is 4-of-6

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Zircuit Staking Safe** | `0xC463EaC02572CC964D43D2414023E2c6B62bAF38` | `getThreshold()` | Zircuit Staking Safe 0xC463EaC02572CC964D43D2414023E2c6B62bAF38 (Ethereum): getThreshold() = 4 of getOwners() = 6 owners (Safe v1.3.0). (Ethereum `#26441165`) |

Classification: **parameter delta** (1 record).
- '`6/8` means at least six out of eight owners need to sign the message. * Multisig 1: `6/8`' (docs.zircuit.com/info/security/privileged-roles.md) (snapshot sha256 `28948601fd05a876dbfd391f3b60209514d9c81f97f627498bff858533c708c0`)

## 17. RPC-pinned promotions — 69 new protocols, documentation not compared

Each is published as an `rpc_observed` record (`docs/api/v1/rpc-pinned.json`): runtime bytecode, EIP-1967 slots and the first readable controller of the protocol's primary contract, at the pins above. No documentation parameter is compared, so none counts toward `verifiedCount` or `driftCount`.

| Protocol | Chain | Primary contract | Proxy | Controller |
| :--- | :--- | :--- | :--- | :--- |
| Hegic | Ethereum | `0x584bC13c7D411c00c01A62e8019472dE68768430` | no | none readable |
| StableHodl | Ethereum | `0x109D3042a3c682F94107b3818e93b3aDE2A47544` | yes | none readable |
| WOOFi Earn | Ethereum | `0x4691937a7508860F876c9c0a2a617E7d9E945D4B` | no | none readable |
| SynFutures V3 | Ethereum | `0x6e15A54B5EcAc17e58daDedDbe8506a7560252F9` | no | none readable |
| Wan Bridge | Ethereum | `0xfCeAAaEB8D564a9D0e71Ef36f027b9D162bC334e` | no | contract controller `0xA1223a59a55eAad135BCe9F513181C388072cC71` |
| Goldfinch | Ethereum | `0xdab396cCF3d84Cf2D07C4454e10C8A6F5b008D2b` | no | none readable |
| TokenWorks | Ethereum | `0xA1a196b5BE89Be04a2c1dc71643689CE013c22e5` | no | eoa `0x019817aD02a31B990433542097bE29D97613E8Cb` |
| Reflexer | Ethereum | `0x6243d8CEA23066d098a15582d81a598b4e8391F4` | no | contract controller `0xcb8479840A5576B1cafBb3FA7276e04Df122FDc7` |
| Taiko Bridge | Ethereum | `0x10dea67478c5F8C5E2D90e5E9B26dBe60c54d800` | yes | contract controller `0x75Ba76403b13b26AD1beC70D6eE937314eeaCD0a` |
| ICHI | Ethereum | `0x111111517e4929D3dcbdfa7CCe55d30d4B6BC4d6` | no | none readable |
| Sport.fun | Base | `0x16EE7ecAc70d1028E7712751E2Ee6BA808a7dd92` | yes | none readable |
| Trueo | Base | `0x21CFCFc3d8F98fC728f48341D10Ad8283F6EB7AB` | no | timelock `0x8963712Bc91aE8C64d96293ed9A1157344f6Fd04` |
| Gro | Ethereum | `0x3Ec8798B81485A254928B70CDA1cf0A2BB0B74D7` | no | multisig safe `0x359F4fe841f246a095a82cb26F5819E10a91fe0d` (3-of-7) |
| Blast pre-launch Farm | Ethereum | `0x5F6AE08B8AeB7078cf2F96AFb089D7c9f51DA47d` | yes | multisig safe `0x67CA7Ca75b69711cfd48B44eC3F64E469BaF608C` (5-of-5) |
| DeFIL | Ethereum | `0x09ce2B746C32528B7d864A1e3979Bd97d2f095AB` | no | contract controller `0x6B4F20B2259Eebb97945b6EF549a1c44FcA6Cd81` |
| friend.tech V1 | Base | `0x0bD4887f7D41B35CD75DFF9FfeE2856106f86670` | no | none readable |
| Ekubo | Ethereum | `0xe0e0e08A6A4b9Dc7bD67BCB7aadE5cF48157d444` | no | contract controller `0x1E0EF4162e42C9bF820c307218c4E41cCcA6E9CC` |
| SATO | Ethereum | `0x0000f07d2B5F1Ddf3244b8780F972f306EFd2888` | no | none readable |
| Quickswap V4 | Base | `0xC5396866754799B9720125B104AE01d935Ab9C7b` | no | multisig safe `0xDA1077c4b0dd6da1BDF166F30aa4BDbF517d637b` (3-of-5) |
| Nucleus | Ethereum | `0x52E4d8989fa8b3E1C06696e7b16DEf5d7707A0d1` | no | multisig safe `0x0000000000417626Ef34D62C4DC189b021603f2F` (3-of-5) |
| LandX Finance | Ethereum | `0x08A1C30BBB26425c1031ee9E43FA0B9960742539` | no | multisig safe `0xf44Bc45368Fb7f6ffC74C5545326Aa0F068b6d4c` (2-of-3) |
| Angle | Ethereum | `0x31429d1856aD1377A8A0079410B297e1a9e214c2` | no | none readable |
| Gamma | Ethereum | `0x6BeA7CFEF803D1e3d5f7C0103f7ded065644e197` | no | multisig safe `0xf2c58cca8ce82df7a2A4f7F936608d61f45a9a47` (3-of-5) |
| NFTX | Ethereum | `0x87d73E916D7057945c9BcD8cdd94e42A6F47f776` | no | none readable |
| LUSD ChickenBonds | Ethereum | `0xB9D7DdDca9a4AC480991865EfEf82E01273F79C3` | no | none readable |
| Saffron Vaults | Ethereum | `0xb753428af26E81097e7fD17f40c88aaA3E04902c` | no | none readable |
| BMX Freestyle | Base | `0x6D63921D8203044f6AbaD8F346d3AEa9A2719dDD` | yes | contract controller `0x5db3C638235b14520Ebd617267cAC0b108Be3157` (3-of-7) |
| Baseline Protocol | Ethereum | `0x9fDbDE76236998Dc2836FE67A9954eDE456A1D63` | no | none readable |
| ApeX Pro | Ethereum | `0x52A8845DF664D76C69d2EEa607CD793565aF42B8` | no | none readable |
| FlokiFi Locker | Ethereum | `0xcf0C122c6b73ff809C693DB761e7BaeBe62b6a2E` | no | eoa `0x000000000000000000000000000000000000dEaD` |
| flaunch | Base | `0x000000000D564D5be76f7f0d28fE52605afC7Cf8` | no | multisig safe `0x0646441c3eC556c1994420C3F9B0f31279BEfb6e` (3-of-5) |
| Unitus | Ethereum | `0x3B6564b5DA73A41d3A66e6558a98FD0e9E1e77ad` | yes | contract controller `0x22C34BdBE18A8bc8Edf7A6C69a03a5B2F2ed45F4` (3-of-5) |
| SOFA.org | Ethereum | `0x57B96D4aF698605563A4653D882635da59Bf11AF` | no | contract controller `0x5a8cDDa6CA37B284b32eF8D513Ef71Ddac553270` |
| CRETH2 | Ethereum | `0x2ba592F78dB6436527729929AAf6c908497cB200` | no | none readable |
| Hashport | Ethereum | `0x367e59b559283C8506207d75B0c5D8C66c4Cd4B7` | no | multisig safe `0x10AB2d9C085c816f43ccB0FB1b27d024224E36f1` (5-of-9) |
| Panoptic V2 | Ethereum | `0x0000000000000aDC9A108591e718F2aee963a2a7` | no | none readable |
| Nami | Ethereum | `0x0100000002935Dce071f4AFA607b961575672b4C` | no | multisig safe `0x892081a87803B32559afC0Ad7b28a39E657fD844` (4-of-7) |
| Punks Terminal | Ethereum | `0x000000000000A6fA31F5fC51c1640aAc76866750` | no | contract controller `0xb07603da6B63C936566F0A29856FbD52829b4605` |
| Interest Protocol | Ethereum | `0x2A54bA2964C8Cd459Dc568853F79813a60761B58` | yes | contract controller `0x3D9d8c08dC16Aa104b5B24aBDd1aD857e2c0D8C5` |
| Decentralized Euro | Ethereum | `0x5052D3Cc819f53116641e89b96Ff4cD1EE80B182` | no | none readable |
| Angstrom | Ethereum | `0x0000000aa232009084Bd71A5797d089AA4Edfad4` | no | none readable |
| Augur | Ethereum | `0x221657776846890989a759BA2973e427DfF5C9bB` | no | none readable |
| Peapods Finance | Ethereum | `0x02f92800F57BCD74066F5709F1Daa1A4302Df875` | no | none readable |
| deBridge | Ethereum | `0x43dE2d77BF8027e25dBD179B491e8d64f38398aA` | yes | contract controller `0xE4427af3555CD9303D728C491364FAdFDD7494Fe` (5-of-8) |
| ElfomoFi | Base | `0x64f8bE47A011DF0fAB47319d5De258D18E93f4ef` | no | multisig safe `0x1a0554f4832a0901709b9C13BBE459f72f7b9ACb` (3-of-5) |
| SMARDEX USDN | Ethereum | `0x656cB8C6d154Aad29d8771384089be5B5141f01a` | yes | multisig safe `0x1E3e1128F6bC2264a19D7a065982696d356879c5` (2-of-3) |
| LendFlare | Ethereum | `0xB620Be8a1949AA9532e6a3510132864EF9Bc3F82` | yes | eoa `0xc413AcBb126fa228d7E3d1943bA506b507C91aF7` |
| DxSale | Ethereum | `0xF063fE1aB7a291c5d06a86e14730b00BF24cB589` | no | none readable |
| DexFi Aggregator | Ethereum | `0x4C1a8a04577286Ce58d0723b1a90160F380E550A` | no | multisig safe `0x76e1736ea8Cda4d0Ed4923B8E119586716C5725f` (2-of-3) |
| Overtime | Ethereum | `0x90cE5720c17587D28E4Af120ae2d313B3BAD1722` | no | eoa `0x4dA7493C2CE2BEce36e75AaDdF39D5c041B6d468` |
| Outcome Finance | Ethereum | `0x0b8de441B26E36f461b2748919ed71f50593A67b` | no | none readable |
| Flexa | Ethereum | `0xfF20817765cB7f73d4bde2e66e067E58D11095C2` | no | contract controller `0x533a36b5e56C1f0361a53d4395F4F0c5f1AD63f8` |
| Lazy | Ethereum | `0xd53B68fB4eb907c3c1E348CD7d7bEDE34f763805` | no | none readable |
| Parallel Protocol V3 | Ethereum | `0x6c0aeceeDc55c9d55d8B99216a670D85330941c3` | no | none readable |
| Sommelier | Ethereum | `0xa670d7237398238DE01267472C6f13e5B8010FD1` | no | none readable |
| VETRO | Ethereum | `0xC8317A10385BE07901A4c9ee3d06E1D83AE378c9` | no | multisig safe `0x6649Ddb5c7e52348b73c8bBdD2A1cbA630b7AaEA` (3-of-6) |
| MortgageFi | Base | `0x1bE87D273d47C3832Ab7853812E9A995A4DE9EEA` | no | none readable |
| JPY DeFi | Ethereum | `0x6042755eCCa71A1Be9C7091441ca5bEaA6b520e4` | yes | none readable |
| King Protocol | Ethereum | `0x8F08B70456eb22f6109F57b8fafE862ED28E6040` | yes | none readable |
| BendDAO APE Staking | Ethereum | `0x0d02755a5700414B26FF040e1dE35D337DF56218` | yes | contract controller `0x859f6e05410893fe64BC84d92BdA773fF798cf66` |
| Fake World Assets V2 | Ethereum | `0xa0Df17B5aC76ABaBA36E1450E2cbCd18A620C845` | no | eoa `0x019817aD02a31B990433542097bE29D97613E8Cb` |
| Kine Finance | Ethereum | `0xbB7D94a423f4978545ecf73161f0678e8AfD1a92` | no | timelock `0x9E8e622e0bA0deE491Fbc42d1Bb12Ab947e2D03B` |
| Clipper | Ethereum | `0xd8F1460044925d2D5c723C7054cd9247027415B7` | no | multisig safe `0xD8Cc0304de58fCE5147796606Db14500d94b5EF2` (3-of-9) |
| Convergence Fi | Ethereum | `0xB0Afc8363b8F36E0ccE5D54251e20720FfaeaeE7` | yes | contract controller `0xF16d93ACF337de38ee55dfb2F2A276883FF59e89` (3-of-6) |
| GLIF | Base | `0xAeD7C2eD7Bb84396AfCB55fF72c8F8E87FFb68f3` | yes | multisig safe `0x5CC0FC29C893Bba884D3E073997C97Bf776dA9F3` (3-of-6) |
| DELV Yield | Ethereum | `0x62F161BF3692E4015BefB05A03a94A40f520d1c0` | no | none readable |
| DerivaDEX | Ethereum | `0x3A880652F47bFaa771908C07Dd8673A787dAEd3A` | no | none readable |
| Supernova CL | Ethereum | `0x44B7fBd4D87149eFa5347c451E74B9FD18E89c55` | no | multisig safe `0xB73494c3FB46Bf5cFC08f32A704fa180110d9226` (4-of-8) |
| Idle | Ethereum | `0x875773784Af8135eA0ef43b5a374AaD105c5D39e` | no | none readable |

## 18. Published RPC-pinned protocols moved to the Sprint 28 pins

- Extra Finance (Base): `0xBB505c54D71E9e599cB8435b4F0cEEc05fC71cbD` (Base) — bytecode keccak256 `0x2bda3204356bb12a5b68e82c0408773da0a9c311b37996552ee4e9e6756623e8`, EIP-1967 slots and controller unchanged at `#59025642`.
- Origin Protocol (SuperOETHb Base): `0xDBFeFD2e8460a6Ee4955A68582F85708BAEA60A3` (Base) — bytecode keccak256 `0x1ab9c11f4c97800cad045510e6c2ceafc40074dd151fd1ed56bd75c61a0b0421`, EIP-1967 slots and controller unchanged at `#59025642`.
- Seamless Protocol (Base): `0x0E02EB705be325407707662C6f6d3466E939f3a0` (Base) — bytecode keccak256 `0x22818496ed85629596372dcbe81fbc48c729489bdf829e198040b0f06fc4f58f`, EIP-1967 slots and controller unchanged at `#59025642`.
- Superform Core v2 (Base): `0xB5396ef2bF8CA360cEB4166b77AFb2bed20e74d4` (Base) — bytecode keccak256 `0x4dfe0bcd9f94f3d29d1dbbce22b6eb4192acf8d3108cc253ab28a51ec7caeff4`, EIP-1967 slots and controller unchanged at `#59025642`.
- 3F: `0x54F862fa0612A8709F6Dec4A7B39AF015CD4E82E` (Ethereum) — bytecode keccak256 `0x4690b1cca8e819c6cf7d976ae8e296e41138d1a2d722c8d07b3394d431fc226e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Aegis YUSD: `0x4274cD7277C7bb0806Bd5FE84b9aDAE466a8DA0a` (Ethereum) — bytecode keccak256 `0x673a34bc4b7ddbb2aaf2ff848f3fe7734a98331af20f2f0f55bca5dd131c39ff`, EIP-1967 slots and controller unchanged at `#26441165`.
- Aera V3: `0x29722cC9a1cACff4a15914F9bC274B46F3b90B4F` (Ethereum) — bytecode keccak256 `0xf4d329ab04c7cdbab16fe48996f83e05fbbdb9222305402bc9049c842ec5cfe7`, EIP-1967 slots and controller unchanged at `#26441165`.
- Alchemix V3: `0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF` (Ethereum) — bytecode keccak256 `0x7ed5fbbd93fd174456aa5a52eab2c19ac15bbb6e07f08667b859ac41819f5208`, EIP-1967 slots and controller unchanged at `#26441165`.
- Anemoy Capital: `0x8c213ee79581Ff4984583C6a801e5263418C4b86` (Ethereum) — bytecode keccak256 `0x7d02f853cd5ee5a6aa0a08213618a6f3c3d594d4c030be909d0e894b6a37c749`, EIP-1967 slots and controller unchanged at `#26441165`.
- AO Bridge: `0xfE08D40Eee53d64936D3128838867c867602665c` (Ethereum) — bytecode keccak256 `0x53c0835906d5b2eed9f973e77d7c785956ea1d182c80679951ae09c4cfaa13c1`, EIP-1967 slots and controller unchanged at `#26441165`.
- Arrakis Modular: `0x820FB8127a689327C863de8433278d6181123982` (Ethereum) — bytecode keccak256 `0x176874457b5b43c103a1f9c14b3d3d70e062df3a08fb6d56e95decf4372d57b6`, EIP-1967 slots and controller unchanged at `#26441165`.
- Aster Bridge: `0x604DD02d620633Ae427888d41bfd15e38483736E` (Ethereum) — bytecode keccak256 `0x0959a24babb02d4d6c6ef27aaec9c34e824a2c55d24b13a8b3dae8401138e1c4`, EIP-1967 slots and controller unchanged at `#26441165`.
- AUTOfinance: `0x2218F90A98b0C070676f249EF44834686dAa4285` (Ethereum) — bytecode keccak256 `0x851c7bea863541332656d77df23c217c5013416390dcefce9992f95655446c1e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Avalon Superearn: `0x5c8D0C48810FD37A0A824D074ee290E64f7A8Fa2` (Ethereum) — bytecode keccak256 `0xe5e3693157141608a301682c8c228c0277eac7efc0b98b57f874ca49752b5fd8`, EIP-1967 slots and controller unchanged at `#26441165`.
- BitFi Basis: `0xCdFb58c8C859Cb3F62ebe9Cf2767F9e036C7fb15` (Ethereum) — bytecode keccak256 `0x168f6bb27d4410c24923a1fa9ccad3e18530a1bdaa23935960b410be0aa1409c`, EIP-1967 slots and controller unchanged at `#26441165`.
- CIAN Yield Layer: `0xB13aa2d0345b0439b064f26B82D8dCf3f508775d` (Ethereum) — bytecode keccak256 `0xe56c30257588d9d02e1a523887f333c31fb17cc1f0b6ffc871685d836403c24f`, EIP-1967 slots and controller unchanged at `#26441165`.
- Concentrator: `0xb3Ad645dB386D7F6D753B2b9C3F4B853DA6890B8` (Ethereum) — bytecode keccak256 `0xce1d4da3ce85dfe2287a99b988ea0393a3d3c08472adbb065266e798585682f2`, EIP-1967 slots and controller unchanged at `#26441165`.
- Derive V3 Options: `0xB1D1eae60EEA9525032a6DCb4c1CE336a1dE71BE` (Ethereum) — bytecode keccak256 `0x4b19308ff101c086627922584dfdf6fb6f57828ecd7b0d5e84cea7cc36e2ca2b`, EIP-1967 slots and controller unchanged at `#26441165`.
- Frankencoin: `0xDb861830D9Ae2d1fCF99fA0cfd3973de382B0B5b` (Ethereum) — bytecode keccak256 `0x9dacc056e5f2d59b75a9c9ae8a3cd5134abf7bfb675462f50c12ab777603cc62`, EIP-1967 slots and controller unchanged at `#26441165`.
- Grvt Bridge: `0xAD29F2723fcdBcF665F210F25E06f97477e417cF` (Ethereum) — bytecode keccak256 `0x61f4a7aa2e0a3dcc40aa8314f37f612c0d4705c416a2bbe73430f130a25297c5`, EIP-1967 slots and controller unchanged at `#26441165`.
- Hyperlane: `0x6D265C7dD8d76F25155F1a7687C693FDC1220D12` (Ethereum) — bytecode keccak256 `0xa88000255e1f96de07122238840c31fd0b48f520430ff6dd78b7100dfc738358`, EIP-1967 slots and controller unchanged at `#26441165`.
- IDEX V1: `0xB705268213D593B8FD88d3FDEFF93AFF5CbDcfAE` (Ethereum) — bytecode keccak256 `0x41a6bbcc6ebf380d013e5bf81e1f04f14177e26857360fdb5fb0d96ab290b6a3`, EIP-1967 slots and controller unchanged at `#26441165`.
- K3 Capital: `0xdC47953c816531a8CA9E1D461AB53687d48EEA26` (Ethereum) — bytecode keccak256 `0xf44809e3d915cd908b4db54ad7e3de8d0923d8c68119d754ef9566c10573fd5e`, EIP-1967 slots and controller unchanged at `#26441165`.
- KPK: `0xbF3F63D8AC133B16d7D50C015036b33219Dd8D23` (Ethereum) — bytecode keccak256 `0xb42b049d6057086c893bdf4bb08f8b6c9bfdbe3ab5c506495470d81a87e7be3f`, EIP-1967 slots and controller unchanged at `#26441165`.
- Lighter Bridge: `0x232CE3bd40fCd6f80f3d55A522d03f25Df784Ee2` (Ethereum) — bytecode keccak256 `0x509f7c0bd6c3e1d958030033e1e1e3ae1be166bbbefd2e8d8835fa72ba1a4236`, EIP-1967 slots and controller unchanged at `#26441165`.
- Makina: `0x8d28A69328561eF9F171c58996fEcB9F494e070c` (Ethereum) — bytecode keccak256 `0xe341d27c127cb10717cc907341d920ba2279dfd64657892fb9411607895a2e08`, EIP-1967 slots and controller unchanged at `#26441165`.
- Noon: `0xdA67B4284609d2d48e5d10cfAc411572727dc1eD` (Ethereum) — bytecode keccak256 `0xc961838fce3287ae2c0a9677e4ae834840d6c90947f96e286d88b13299c04900`, EIP-1967 slots and controller unchanged at `#26441165`.
- Origami Finance: `0x07c5500359161b81eb0DfFF83097d5025D3cF5A2` (Ethereum) — bytecode keccak256 `0x62d6e97082d84feec6a1fb354b9279aa8ceb6b7ffaf88d1bb82e9225bf1553e3`, EIP-1967 slots and controller unchanged at `#26441165`.
- PancakeSwap AMM V3: `0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865` (Ethereum) — bytecode keccak256 `0x8191d3ab1d55d3da9822199f28865415c99566b6f1aee4a4b16713f57930678c`, EIP-1967 slots and controller unchanged at `#26441165`.
- RockawayX: `0x953972ea0C1703c58F09FB6fD2477Fdcf0FEe074` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26441165`.
- Saturn: `0x23238f20b894f29041f48D88eE91131C395Aaa71` (Ethereum) — bytecode keccak256 `0x6d0ce32ba65bd273fcbdc767be5fd8924abd4ce0d6fb5c84ba39c28be05d2457`, EIP-1967 slots and controller unchanged at `#26441165`.
- Shift DeFi: `0x1d71c888961c4600cF0E31F6196b4dA7fE72e4B3` (Ethereum) — bytecode keccak256 `0xd07150498af17b4f1d7cef45227180255479fe3e1f529a027ffd6a716023e904`, EIP-1967 slots and controller unchanged at `#26441165`.
- Sierra Protocol: `0xe1b1252652A2FF0CC3A4214eE73d9FeD1FEa5b4f` (Ethereum) — bytecode keccak256 `0x1151e0ba784b3fe266ae02886e6435603745e3e3b288a9f5ad182737b0faa1ac`, EIP-1967 slots and controller unchanged at `#26441165`.
- Sonic Gateway: `0xa1E2481a9CD0Cb0447EeB1cbc26F1b3fff3bec20` (Ethereum) — bytecode keccak256 `0x23a1472fa83f7542cf6eecb7637465cd72aa2470d206dd81dcfe9d1db4e8c633`, EIP-1967 slots and controller unchanged at `#26441165`.
- Starknet Bridge: `0xCa14007Eff0dB1f8135f4C25B34De49AB0d42766` (Ethereum) — bytecode keccak256 `0x7ef33cd5b6004a6c025dee0df472999ec54227ba2a7ab0b612537ca5219ee275`, EIP-1967 slots and controller unchanged at `#26441165`.
- Team Finance: `0xCC4304A31d09258b0029eA7FE63d032f52e44EFe` (Ethereum) — bytecode keccak256 `0x17404120e429d743f170be02a42dd5018a3d340863ef7c7bf41db1baab1a1cd7`, EIP-1967 slots and controller unchanged at `#26441165`.
- Theo Network thUSD: `0xa3fE5c7596024E6811E14F029937D5bd8Ae485b3` (Ethereum) — bytecode keccak256 `0xc8ff19e35002275bcbf9f8eede7c2030293c871666ff06c9eb19933826d81271`, EIP-1967 slots and controller unchanged at `#26441165`.
- Tori Finance: `0xd0580192E98eA6CEB9c7b6191Ed2E27560911697` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26441165`.
- Tornado Cash: `0x77777FeDdddFfC19Ff86DB637967013e6C6A116C` (Ethereum) — bytecode keccak256 `0x7bb3883a4af95ea24983177dbcb682a021f389b77835ed266bfa30bda271c77b`, EIP-1967 slots and controller unchanged at `#26441165`.
- UNCX Network V2: `0xaDB2437e6F65682B85F814fBc12FeC0508A7B1D0` (Ethereum) — bytecode keccak256 `0x9ef6c8d303308ae4c0cfd6466aff6fd25946facfdeb76992707386a34ae5879f`, EIP-1967 slots and controller unchanged at `#26441165`.
- USDT0: `0x6C96dE32CEa08842dcc4058c14d3aaAD7Fa41dee` (Ethereum) — bytecode keccak256 `0xe5e3693157141608a301682c8c228c0277eac7efc0b98b57f874ca49752b5fd8`, EIP-1967 slots and controller unchanged at `#26441165`.
- Veda: `0x5232bc0F5999f8dA604c42E1748A13a170F94A1B` (Ethereum) — bytecode keccak256 `0xf349ba5ac81eb0f8ad05e353e581928b157ebce878db155eaea6f4534cb5fe2b`, EIP-1967 slots and controller unchanged at `#26441165`.
- World Chain Bridge: `0x90BB48fe3310499Db36437dCAE642F721e32d094` (Ethereum) — bytecode keccak256 `0xfa8c9db6c6cab7108dea276f4cd09d575674eb0852c0fa3187e59e98ef977998`, EIP-1967 slots and controller unchanged at `#26441165`; the controller Safe is now 3-of-6 (was 3-of-8).
- xDAI Stake Bridge: `0x0Ae055097C6d159879521C384F1D2123D1f195e6` (Ethereum) — bytecode keccak256 `0xc142222c43ea630db16763d6dd8e619a9cecc3bf121785475841cdc9f94361b7`, EIP-1967 slots and controller unchanged at `#26441165`.
- Yield Basis: `0x01791F726B4103694969820be083196cC7c045fF` (Ethereum) — bytecode keccak256 `0xb6dd52f54a35ee897ad6edc361c7dd1ce400f92031dc4b536514bf984f327777`, EIP-1967 slots and controller unchanged at `#26441165`.
- Zama: `0xA12CC123ba206d4031D1c7f6223D1C2Ec249f4f3` (Ethereum) — bytecode keccak256 `0xf172c8c96f8ba07e22f43c9bd9f1d3b96d1dbae326c61b388b4fbd7b517f9123`, EIP-1967 slots and controller unchanged at `#26441165`.
- ZEROBASE CeDeFi: `0xfAB99fCF605fD8f4593EDb70A43bA56542777777` (Ethereum) — bytecode keccak256 `0x5ea0a98719770123cf8cb56ed504a5975019e01868505874dc2fb31b034a7cfe`, EIP-1967 slots and controller unchanged at `#26441165`.
- Abracadabra Spell: `0x090185f2135308BaD17527004364eBcC2D37e5F6` (Ethereum) — bytecode keccak256 `0x4169bd96e19721db3ba26a56552118421ef3fc613a28ac9605e3abf54d3a1d74`, EIP-1967 slots and controller unchanged at `#26441165`.
- ADI Bridge: `0x8B1484d57abBE239bB280661377363b03c89CaEa` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26441165`.
- Ankr: `0x8290333ceF9e6D528dD5618Fb97a76f268f3EDD4` (Ethereum) — bytecode keccak256 `0x0c0a59b206d3675604c0d605ecbf7ec2c7deedaee03fd40f9f94e4bd7e954798`, EIP-1967 slots and controller unchanged at `#26441165`.
- Anvil: `0xAEEAa594e7dc112D67b8547fe9767a02c15B5597` (Ethereum) — bytecode keccak256 `0x429a8e131784eb8288d76e76719f82390c239cc6c473298627c6524c61706197`, EIP-1967 slots and controller unchanged at `#26441165`.
- Arkis: `0xEA623eebd9c5bFd56067e36C89Db0C13e6c70ba8` (Ethereum) — bytecode keccak256 `0xddb2c9db76f64c21284e72e3ac43a2e9c263034b5b317504860a5adce96d91e7`, EIP-1967 slots and controller unchanged at `#26441165`.
- Aura: `0xC0c293ce456fF0ED870ADd98a0828Dd4d2903DBF` (Ethereum) — bytecode keccak256 `0x29fa14ed566cfc96628bfb573316782856bc583b0b3079fa524d13a38dd0d58b`, EIP-1967 slots and controller unchanged at `#26441165`.
- Avant avETH: `0x9469470C9878bf3d6d0604831d9A3A366156f7EE` (Ethereum) — bytecode keccak256 `0x9591b0f9a962e55ec9d4ab889638af7d31a3368e23618ee5599a609dcc1159fd`, EIP-1967 slots and controller unchanged at `#26441165`.
- Badger DAO: `0x3472A5A71965499acd81997a54BBA8D852C6E53d` (Ethereum) — bytecode keccak256 `0x2dda0f3a6bee3e5768e41adb77021f8f5653897a1c65a5f106265b17fa2c299b`, EIP-1967 slots and controller unchanged at `#26441165`.
- Bancor V3: `0x1F573D6Fb3F13d689FF844B4cE37794d79a7FF1C` (Ethereum) — bytecode keccak256 `0xf1495e99bb63cf244df1a4e88c356e556d15497028e15842edccb032e3463bb4`, EIP-1967 slots and controller unchanged at `#26441165`.
- Bio Protocol: `0xcb1592591996765Ec0eFc1f92599A19767ee5ffA` (Ethereum) — bytecode keccak256 `0x4a3a20ab3b6b8cfc24ee0663b951d7c9139f6c9f92e11c5e9efb31557c3aa986`, EIP-1967 slots and controller unchanged at `#26441165`.
- Blur Bids: `0x5283D291DBCF85356A21bA090E6db59121208b44` (Ethereum) — bytecode keccak256 `0xeb2957414f3daa1495aa331973f631de8ee6c87994fc4a612da20a97f4e14150`, EIP-1967 slots and controller unchanged at `#26441165`.
- Brickken: `0x0A638F07ACc6969abF392bB009f216D22aDEa36d` (Ethereum) — bytecode keccak256 `0xdf740b7eec2ee1e88020370781c03aab1b04dc55a1dc622b48cb7002ce87fb8e`, EIP-1967 slots and controller unchanged at `#26441165`.
- cBridge: `0x4F9254C83EB525f9FCf346490bbb3ed28a81C667` (Ethereum) — bytecode keccak256 `0x2f20f33e040f6be6f03b13a42e4c0b28a9834690ddfbf919a9a49b95007aadd3`, EIP-1967 slots and controller unchanged at `#26441165`.
- Chamber Vaults: `0xca1207647Ff814039530D7d35df0e1Dd2e91Fa84` (Ethereum) — bytecode keccak256 `0x1154b4431256a941501d558a4d3a3fd001a431840461ac32435cd878b90946ac`, EIP-1967 slots and controller unchanged at `#26441165`.
- Cronos zkEVM Bridge: `0x28Ff2E4dD1B58efEB0fC138602A28D5aE81e44e2` (Ethereum) — bytecode keccak256 `0xee8a105971995661291a9f284262a87abf2381b3cdc93b2c8fbeffe4cd636dd9`, EIP-1967 slots and controller unchanged at `#26441165`.
- cVault Finance: `0x62359Ed7505Efc61FF1D56fEF82158CcaffA23D7` (Ethereum) — bytecode keccak256 `0x35d8cb7adaa6c80bfac8896682d5aeb4d367bb2c199f42e1732957b245219caf`, EIP-1967 slots and controller unchanged at `#26441165`.
- D2 Finance: `0x07Dff4087b43c4A759f4Fc69511c26d51929dAF4` (Ethereum) — bytecode keccak256 `0x86b6dc26240e014376e03dac6bdfc333b63e56ee7506e1000786f8c33a6fb8c0`, EIP-1967 slots and controller unchanged at `#26441165`.
- DODO AMM: `0x43Dfc4159D86F3A37A5A4B3D4580b888ad7d4DDd` (Ethereum) — bytecode keccak256 `0xa3ed78c2deb7d2c3197c7f1f83847c7a2e806273099255078f11d84387b70ab9`, EIP-1967 slots and controller unchanged at `#26441165`.
- Dolomite: `0x003Ca23Fd5F0ca87D01F6eC6CD14A8AE60c2b97D` (Ethereum) — bytecode keccak256 `0xf7ff557bf8276c5cc8a12bce5ceca435a0ca9094cc6c5ac7548b5a5395aa2a07`, EIP-1967 slots and controller unchanged at `#26441165`.
- Drakewell USDdw: `0x2B5895b716311A1eaC8f93fB88C56aF9eC8C1A69` (Ethereum) — bytecode keccak256 `0xbb70cbce5814331e91f8533edb5153fbccaa65f6ab99f5baf5d9d766c4888309`, EIP-1967 slots and controller unchanged at `#26441165`.
- dYdX V3: `0x92D6C1e31e14520e676a687F0a93788B716BEff5` (Ethereum) — bytecode keccak256 `0x09b771bde251cc95f8d1cb964497c7170f300839a72eda826deecc7df0142ddb`, EIP-1967 slots and controller unchanged at `#26441165`.
- Easedefi.org: `0xEa5eDef1287AfDF9Eb8A46f9773AbFc10820c61c` (Ethereum) — bytecode keccak256 `0x614b8db3fa7d70d7f8369ff9cca21049df4bf56aef08bce338c66e82dfa1e1a1`, EIP-1967 slots and controller unchanged at `#26441165`.
- edgeX Bridge: `0xB0076DE78Dc50581770BBa1D211dDc0aD4F2a241` (Ethereum) — bytecode keccak256 `0xde5d6e9d24143b30c748d881d84f897a424b86c8a931badaa1ca8b4dd7e4051e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Eigenpie: `0x20b70E4A1883b81429533FeD944d7957121c7CAB` (Ethereum) — bytecode keccak256 `0x02f54b576cbf2fd200517ffc5f9cdbd7c08314e9eb8002043e355001fa4e373f`, EIP-1967 slots and controller unchanged at `#26441165`.
- Exactly: `0x310A2694521f75C7B2b64b5937C16CE65C3EFE01` (Ethereum) — bytecode keccak256 `0xa9429b2c0132dcfd5c68d4df832f4d00b7b51a5a22844f6fcf7aa3a1e94ae2af`, EIP-1967 slots and controller unchanged at `#26441165`.
- FermiSwap: `0xb1076fE3AB5e28005C7c323Bac5AC06a680d452e` (Ethereum) — bytecode keccak256 `0xba367f88fc2257711f741c9f6c4bca4b20e1030ab06635bbb903b0bf052d2638`, EIP-1967 slots and controller unchanged at `#26441165`.
- Flying Tulip Lend: `0x5DD1A7A369e8273371d2DBf9d83356057088082c` (Ethereum) — bytecode keccak256 `0x8062c2d6646f1c459825821c9d1e582052bd2e7089367d7087545cf6bab8f4c3`, EIP-1967 slots and controller unchanged at `#26441165`.
- GETH: `0x3802c218221390025BCEABBaD5D8C59F40eB74B8` (Ethereum) — bytecode keccak256 `0xb5e0d7b2fb71f8589a2298f1e39888d6f7df1f3cf7338f44ce9f64337a724b1a`, EIP-1967 slots and controller unchanged at `#26441165`.
- Gondi V3: `0xf65B99CE6DC5F6c556172BCC0Ff27D3665a7d9A8` (Ethereum) — bytecode keccak256 `0x5a24688c56b5bd15d41e7fad9201ef8472da0b86cbda8ede7713b58ce6b09600`, EIP-1967 slots and controller unchanged at `#26441165`.
- Hakka Finance: `0x0E29e5AbbB5FD88e28b2d355774e73BD47dE3bcd` (Ethereum) — bytecode keccak256 `0x3cfb96debb564e364f4c21b2f07a940c6fcfc7557c0e33f948af2b2c937ad7c0`, EIP-1967 slots and controller unchanged at `#26441165`.
- Harvest Finance: `0xa0246c9032bC3A600820415aE600c6388619A14D` (Ethereum) — bytecode keccak256 `0x9c1795bb8a1ae198f6f98c74e4c0cebb6726da3b592ccda396ab78ee30c65fed`, EIP-1967 slots and controller unchanged at `#26441165`.
- Hop Protocol: `0xc5102fE9359FD9a28f877a67E36B0F050d81a3CC` (Ethereum) — bytecode keccak256 `0x4e5daef6a4c9a066d1d4f6c3e77a1eaefae7117c725cba2328ddb399d2260fe2`, EIP-1967 slots and controller unchanged at `#26441165`.
- iAero Protocol: `0x7ee8964160126081cebC443a42482E95e393e6A8` (Base) — bytecode keccak256 `0x9b19c0cef8b1e7180ecec6871610f3bfb910f13197ba9a5851f2ff9987a8d0ca`, EIP-1967 slots and controller unchanged at `#59025642`.
- InceptionLRT (Isolated Restaking): `0x814CC6B8fd2555845541FB843f37418b05977d8d` (Ethereum) — bytecode keccak256 `0x4d9be648c5bf39973670d9f8b481d5d0b971e6a2db2deccc6b98cde21c5dd83e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Index Coop: `0x0954906da0Bf32d5479e25f46056d22f08464cab` (Ethereum) — bytecode keccak256 `0x72b69cf0962b8043d955eb54b5ec4dcdefed60b1c8ecd2581003bdd4e916559e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Injective Bridge: `0xe28b3B32B6c345A34Ff64674606124Dd5Aceca30` (Ethereum) — bytecode keccak256 `0x2860075dbbe8adda4739434d6accb0f815f6c16d66c1334920c2dde5cdf67f48`, EIP-1967 slots and controller unchanged at `#26441165`.
- Juicebox V1: `0x3abF2A4f8452cCC2CF7b4C1e4663147600646f66` (Ethereum) — bytecode keccak256 `0xf28bae363907eeebbed68f7f0b0efc447d495263f180b6ff3e161f81f75be328`, EIP-1967 slots and controller unchanged at `#26441165`.
- Ledgity Yield: `0x482dF7483a52496F4C65AB499966dfcdf4DDFDbc` (Ethereum) — bytecode keccak256 `0xe71d9a8dc2039e8ad5f38dc0f95409ec914ee7cba1c413374a11fba65d7941af`, EIP-1967 slots and controller unchanged at `#26441165`.
- Legion: `0xa0BeB0A8C765482c128a2986c063AF5C3171ff2F` (Ethereum) — bytecode keccak256 `0xf7924ec4706f7b92b773d73078c1f3d26580e4954d342f283018d7a713bb6186`, EIP-1967 slots and controller unchanged at `#26441165`.
- Lista Lending: `0xf820fB4680712CD7263a0D3D024D5b5aEA82Fd70` (Ethereum) — bytecode keccak256 `0xc2294082827c06324e557e6b62fea89d83df6541b0f7926531eda3ce3676ee8c`, EIP-1967 slots and controller unchanged at `#26441165`.
- Meta Pool ETH: `0x48AFbBd342F64EF8a9Ab1C143719b63C2AD81710` (Ethereum) — bytecode keccak256 `0x4d9be648c5bf39973670d9f8b481d5d0b971e6a2db2deccc6b98cde21c5dd83e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Metis Bridge: `0x9E32b13ce7f2E80A01932B42553652E053D6ed8e` (Ethereum) — bytecode keccak256 `0x9a833fe40ae2176ba5d50fbb57f2ad20f4189097772a9180c30bb9114526b55c`, EIP-1967 slots and controller unchanged at `#26441165`.
- Metric V1: `0x2a53833cc95548cf52c7b159110e22D3a9018f32` (Ethereum) — bytecode keccak256 `0xe34ec675aad2fc67175956d951b49d182c1289638daa4438fbf80d2ade12291e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Metronome Synth: `0x2Ebd53d035150f328bd754D6DC66B99B0eDB89aa` (Ethereum) — bytecode keccak256 `0xe2a3917cd8f22f7a6d01aedf941b9982b15af8484a9578939a24c93fd7b1fdff`, EIP-1967 slots and controller unchanged at `#26441165`.
- Monolith Market: `0x6D961c9DCF1AD73566822BA4B087892e3839B849` (Ethereum) — bytecode keccak256 `0x67cab37d1c7a97e5bd64e10a5e6283e14f2384165e1ba55ed4f0a51aaf8fcc96`, EIP-1967 slots and controller unchanged at `#26441165`.
- Morph Bridge: `0xDc71366EFFA760804DCFC3EDF87fa2A6f1623304` (Ethereum) — bytecode keccak256 `0x44107d7c70e67e04d35d77455d5755c94d4897196e4ea9a341c1a6d864a6d4d5`, EIP-1967 slots and controller unchanged at `#26441165`.
- MorpheusAI: `0x47176B2Af9885dC6C4575d4eFd63895f7Aaa4790` (Ethereum) — bytecode keccak256 `0x53c0835906d5b2eed9f973e77d7c785956ea1d182c80679951ae09c4cfaa13c1`, EIP-1967 slots and controller unchanged at `#26441165`.
- Multichain: `0x9Fb9a33956351cf4fa040f65A13b835A3C8764E3` (Ethereum) — bytecode keccak256 `0x6a3d203c440e54090e1d8f2dfdb9aa32e0df4b7dd5bfd02d11889f3bd9534492`, EIP-1967 slots and controller unchanged at `#26441165`.
- Native Credit Pool: `0xe3D41d19564922C9952f692C5Dd0563030f5f2EF` (Ethereum) — bytecode keccak256 `0xde357882f2c0a539e8abef1c3c091bf56874c09a141eef9534dd62372e91e93c`, EIP-1967 slots and controller unchanged at `#26441165`.
- NodeDAO: `0xd7C049CD4ba216679ecC04Eb2767cC5E39812121` (Ethereum) — bytecode keccak256 `0x19d55c6b37ed536e4412158686e2df774d0e754dbb580b5f87923c7049d0ac0a`, EIP-1967 slots and controller unchanged at `#26441165`.
- NUVA: `0x50AE1e4A612A4623b747aEeFb30aFBA82804e12c` (Ethereum) — bytecode keccak256 `0x2d708ed89e980db61d00892059af7092b260a2889b6b6f3e86c16d90b3b13228`, EIP-1967 slots and controller unchanged at `#26441165`.
- OpenGDP Shared Security: `0x54e44DbB92dBA848ACe27F44c0CB4268981eF1CC` (Ethereum) — bytecode keccak256 `0xde741c264ec7f60e744da6731a699d17530b431a41d2e2ebe7476abc11261e92`, EIP-1967 slots and controller unchanged at `#26441165`.
- Orderly Bridge: `0xABD4C63d2616A5201454168269031355f4764337` (Ethereum) — bytecode keccak256 `0xb3151f817a0cbf213614631b397dd981aa4c3cd2c95a20a5ddf7f9ebdcbbff1c`, EIP-1967 slots and controller unchanged at `#26441165`.
- Paradex Bridge: `0xb32E10022FFBeDfE10bc818a1C7e67D9d87e0fa7` (Ethereum) — bytecode keccak256 `0xee8a105971995661291a9f284262a87abf2381b3cdc93b2c8fbeffe4cd636dd9`, EIP-1967 slots and controller unchanged at `#26441165`.
- Pickle: `0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5` (Ethereum) — bytecode keccak256 `0xbadea4d643e7f84de7258a99ccfade16a9cd5e39c9e4b9f9f35876e469a2fe76`, EIP-1967 slots and controller unchanged at `#26441165`.
- Piku Finance: `0x2E4039E8E31475d65DC00293C366FDBfBBC02DC3` (Ethereum) — bytecode keccak256 `0x1be95a2ec43076d7ce5cd1d0d5261f9bb409e9022e46cc6495ffd1dd7bcf6f0c`, EIP-1967 slots and controller unchanged at `#26441165`.
- Pirex: `0xc55126051B22eBb829D00368f4B12Bde432de5Da` (Ethereum) — bytecode keccak256 `0x574a98b7bd30da9de3edfb7134b4e9dd5b4bbc011bb85a984aa06dae0e350f53`, EIP-1967 slots and controller unchanged at `#26441165`.
- PoolTogether V3: `0x0cEC1A9154Ff802e7934Fc916Ed7Ca50bDE6844e` (Ethereum) — bytecode keccak256 `0x308fc5e8970ed67ffebcc8dafff6333492ace6d3282ba6ef3b1092959a2da25c`, EIP-1967 slots and controller unchanged at `#26441165`.
- Ribbon: `0x6123B0049F904d730dB3C36a31167D9d4121fA6B` (Ethereum) — bytecode keccak256 `0x06f86d51347023f4971c0638f8cb71cbd7b4de3b92a825904205dd2486591d59`, EIP-1967 slots and controller unchanged at `#26441165`.
- Ring Few: `0x7D86394139bf1122E82FDF45Bb4e3b038A4464DD` (Ethereum) — bytecode keccak256 `0x5126b02f7eec0470df7780456cdcee61bc47bf7bf574f213674c66393fd50ae9`, EIP-1967 slots and controller unchanged at `#26441165`.
- Royco V2: `0x7cC6fB28eC7b5e7afC3cB3986141797ffc27253C` (Ethereum) — bytecode keccak256 `0x18f95d772587f01e910a390c7b48d767fbfa7726584405e8277da572b72f9386`, EIP-1967 slots and controller unchanged at `#26441165`.
- SoSoValue Basis: `0x624e2e7fDc8903165F64891672267AB0FCB98831` (Base) — bytecode keccak256 `0x48ac29a5246889375862706cb6369924947b6cf20bf05b904b04324c8536506a`, EIP-1967 slots and controller unchanged at `#59025642`.
- Spectra MetaVaults: `0x64FCC3A02eeEba05Ef701b7eed066c6ebD5d4E51` (Base) — bytecode keccak256 `0x9b0bffdffad18ebe65d4dda55e9d75c663e39719112ed2c7fe6800d04c80ae64`, EIP-1967 slots and controller unchanged at `#59025642`.
- Stafi: `0xef3A930e1FfFFAcd2fc13434aC81bD278B0ecC8d` (Ethereum) — bytecode keccak256 `0xcfb26d9dee1cbb07d16138dc589dff327bc820f608c7d6142789f9b2d94d9922`, EIP-1967 slots and controller unchanged at `#26441165`.
- StakeStone STONE: `0x1D88713b483A8E45cfF0e5CD7c2e15E5Fab4534d` (Ethereum) — bytecode keccak256 `0x7b5f00e12c193572cdda46010ef6bf30df8c68c1974d9aad61c8935ce091d9ca`, EIP-1967 slots and controller unchanged at `#26441165`.
- Steer Protocol: `0xCEBF1A54A9Ce703FC80967760b5A6cbDb4111099` (Ethereum) — bytecode keccak256 `0x1e71c4a5b01c61a4b1a4afa98257a085e472bfc63a362efa77be9a23e714cdc9`, EIP-1967 slots and controller unchanged at `#26441165`.
- SushiSwap V3: `0xc35DADB65012eC5796536bD9864eD8773aBc74C4` (Ethereum) — bytecode keccak256 `0x2908b9ac88489ac1ed7dbc2d6ff5c0832b56dc8f5408e4992b9c7c6a24bb337a`, EIP-1967 slots and controller unchanged at `#26441165`.
- Symbiosis: `0xd38BB40815d2B0c2d2c866e0c72c5728ffC76dd9` (Ethereum) — bytecode keccak256 `0x145131033c93e676112c82aa230328dfc8dd0ac596f59e4ed90ee5045adcdd20`, EIP-1967 slots and controller unchanged at `#26441165`.
- Synapse Cross Chain Bridge: `0x0f2D719407FdBeFF09D87557AbB7232601FD9F29` (Ethereum) — bytecode keccak256 `0x14b9c77780d7daf560bdab14dea33da9fa0bc59eb71b6a1d230de99b6ee0500f`, EIP-1967 slots and controller unchanged at `#26441165`.
- Syntropia: `0x1b2CB79a4564206f53Ba80b4d780F251b4Ae6765` (Ethereum) — bytecode keccak256 `0xdc8d9306a3726daedf8bb0db4da810ed5af2b6ab034e593737a83531a2e7d327`, EIP-1967 slots and controller unchanged at `#26441165`.
- Tangent Finance: `0x214C8A1023B30032a2Eded109146658C6D6F2781` (Ethereum) — bytecode keccak256 `0xf5dab7b6b40557238eaad60b7369bfb50c9329ff47046216a93497aa14cb9771`, EIP-1967 slots and controller unchanged at `#26441165`.
- The Idols: `0x9416bA76e88D873050A06e5956A3EBF10386b863` (Ethereum) — bytecode keccak256 `0x1fc5a38d54c637a235d4a0fd7c57ec4ae5c3c148ec7a038d9715f89a1330cdce`, EIP-1967 slots and controller unchanged at `#26441165`.
- UltraYield Vaults: `0x8ECC0B419dfe3AE197BC96f2a03636b5E1BE91db` (Ethereum) — bytecode keccak256 `0xe428fca70a96823c60ffaa430edc8cc501377a4709bdb3a070d024d616d81ff5`, EIP-1967 slots and controller unchanged at `#26441165`.
- Unslashed: `0xE0e05c43c097B0982Db6c9d626c4eb9e95C3b9ce` (Ethereum) — bytecode keccak256 `0x76b55d62d6e6d762eaa121e1cd4d14100f2d08c36d299b970d06a973dc86fb90`, EIP-1967 slots and controller unchanged at `#26441165`.
- Wildcat Protocol: `0xfEB516d9D946dD487A9346F6fee11f40C6945eE4` (Ethereum) — bytecode keccak256 `0x3622afdfc583101952ff6e608d76f9c897d2767297315962d97f8b3a2cc2df56`, EIP-1967 slots and controller unchanged at `#26441165`.
- XSY: `0xBA515304d8153c4b162dC79f867E152DF9c127eb` (Base) — bytecode keccak256 `0xa403fa29cda49311b973967ea91292c75ab23dd093a8444ae680d9099fac817a`, EIP-1967 slots and controller unchanged at `#59025642`.
- YieldFi: `0x19Ebd191f7A24ECE672ba13A302212b5eF7F35cb` (Ethereum) — bytecode keccak256 `0xcb948150f62f6105c4bab1c9fa409ee4a30c35405b1622d203d440a703ece90e`, EIP-1967 slots and controller unchanged at `#26441165`.
- Yuzu Money: `0x224e90591A2d63fb66E677D0561Ea4A6Ad1F098D` (Ethereum) — bytecode keccak256 `0xb516ec422f5c3709db0ba2ff716d5e06daaec61bf753989303aa3679d5163095`, EIP-1967 slots and controller unchanged at `#26441165`.
- Zora Bridge: `0x1111111111166b7FE7bd91427724B487980aFc69` (Base) — bytecode keccak256 `0xd8511363feac51319c3a08c4ad471f451c5c8d137878cbb0e0472fd976421cd5`, EIP-1967 slots and controller unchanged at `#59025642`.
- ZTLN-P: `0xfEd3D6557Dc46A1B25d0A6F666513Cb33835864B` (Ethereum) — bytecode keccak256 `0xf480c2a32f387d87861f5e505e80169f59eb402333618d51f49d70a724388374`, EIP-1967 slots and controller unchanged at `#26441165`.
