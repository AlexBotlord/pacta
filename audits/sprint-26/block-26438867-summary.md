# Sprint 26 Protocol Commitment Summary — Block `26438867`

- **Ethereum Mainnet pin**: `26438867` (`0x1936cd3`), canonical block hash `0x6c477521320837df8611249a255cb7142052874937cddb9fe568f685763458ff`, timestamp `2026-11-18 02:11:35 UTC` (`1794967895`); the `finalized` head, both endpoints returning the same number and hash
- **Base Mainnet pin**: `58885628` (`0x38285fc`), canonical block hash `0x732b5472c93d5c4bf65f39440097e2b0143d5875cfec028646f7f06123a20094`, timestamp `2026-11-18 02:05:01 UTC` (`1794967501`); the `finalized` head, both endpoints returning the same number and hash
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI), bulk harvester v1.3. Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode` batched through Multicall3 at the pinned block, on two independent RPCs per chain with identical block hashes: `ethereum-rpc.publicnode.com` + `rpc.mevblocker.io` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base). Documentation: HTTP-200 first-party snapshots named by their SHA-256; every quote below is an exact substring of its snapshot's text and every value is re-derived from the pinned reads by the validator (no model output is trusted). The 38 targets added to the cohort after the pin (3f, aegis-yusd, alchemix-v3, anemoy-capital, ao-bridge, arrakis-modular, autofinance, concentrator, frankencoin, fx-protocol, grvt-bridge, hyperlane, idex-v1, k3-capital, makina, morpho-v1-base-sparkusdc-7bfa7c, morpho-v1-ethereum-steakusdt-beef04, morpho-v2-ethereum-armusdcs-a2eaad, morpho-v2-ethereum-bbqusdc-beeff2, morpho-v2-ethereum-senpyusdpst-8381a1, morpho-v2-ethereum-skymoneyusdtsavings-23f5e9, morpho-v2-ethereum-steakusdt-beef00, nodedao, noon, origami-finance, pancakeswap-amm-v3, shift-defi, sierra-protocol, sonic-gateway, stader, team-finance, tori-finance, uncx-network-v2, vesper-v1, wise-token, yield-basis, zama, zerobase-cedefi) were read at the same block numbers and hashes through two archive-capable endpoints per chain whose block hashes match the pin: `rpc.mevblocker.io` + `gateway.tenderly.co` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base).
- **Result**: `9` records for `8` protocols (`6` new; published protocols with a new record: Beefy Finance (Base), StakeWise V3 (osETH)) — `8` aligned baselines, `0` protective deltas, `1` parameter delta. `verifiedCount = 8`. `driftCount = 1`, the same convention as Sprints 1–25 and `PactaSentinelGuard` (`driftCount != 0` means drift).
- **RPC-pinned promotions (not attested)**: `44` further new protocols are published as RPC-pinned control-plane records at the same pins (listed below); the `4` RPC-pinned protocols already published move to these pins with every stated fact unchanged. They carry no Base EAS UID.
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); Base reads are taken at the Base pin.

## 1. Polygon Bridge — Polygon Bridge multisig: 5-of-9 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Polygon Bridge Safe** | `0xFa7D2a996aC6350f4b56C043112Da0366a59b74c` | `getThreshold()` | Polygon Bridge Safe 0xFa7D2a996aC6350f4b56C043112Da0366a59b74c (Ethereum): getThreshold() = 5 of getOwners() = 9 owners (Safe v1.4.1). (Ethereum `#26438867`) |

Classification: **aligned baseline** (1 record).
- '**$5/9$ Multisig** `0xFa7D2a996aC6350f4b56C043112Da0366a59b74c`' (docs.polygon.technology/pos/reference/commit-chain-multisigs.md) (snapshot sha256 `6e1a4a5b9c81e07151626920ea0cefb9785b7bf184771021f7fc23050dd987ff`)

## 2. Curve DEX (Ethereum) — Curve DEX (Ethereum) multisig: 5-of-9 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Curve DEX (Ethereum) Safe** | `0x467947EE34aF926cF1DCac093870f613C96B1E0c` | `getThreshold()` | Curve DEX (Ethereum) Safe 0x467947EE34aF926cF1DCac093870f613C96B1E0c (Ethereum): getThreshold() = 5 of getOwners() = 9 owners (Safe v1.3.0). (Ethereum `#26438867`) |

Classification: **aligned baseline** (1 record).
- 'The EmergencyDAO is a **5-of-9 multisig** authorized for emergency interventions.' (docs.curve.finance/user/dao/emergency-dao.md) (snapshot sha256 `80fc56e7f1aa9424ab664bd1815799f40f2912e1ed094f20f8fe778601229640`)

## 3. Cooler Loans — Cooler Loans multisig: 4-of-8 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Cooler Loans Safe** | `0x245cc372C84B3645Bf0Ffe6538620B04a217988B` | `getThreshold()` | Cooler Loans Safe 0x245cc372C84B3645Bf0Ffe6538620B04a217988B (Ethereum): getThreshold() = 4 of getOwners() = 8 owners (Safe v1.3.0). (Ethereum `#26438867`) |

Classification: **aligned baseline** (1 record).
- 'Threshold: 4-of-8 on Mainnet.' (docs.olympusdao.finance/main/security/multisigs) (snapshot sha256 `5a4cd2c60fc7c2c51240730deda0a3a6a9569650018853c0f37385556cfe0d3d`)

## 4. IPOR Fusion — IPOR Fusion ERC1967Proxy: upgradeable (UUPS), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **IPOR Fusion ERC1967Proxy** | `0x1455717668fA96534f675856347A973fA907e922` | slot `eip1967.proxy.implementation` | IPOR Fusion ERC1967Proxy 0x1455717668fA96534f675856347A973fA907e922 (Base): EIP-1967 implementation slot = 0x378fEb2E96082FB965E2BB922AEE484d07c14014; upgradeable (EIP-1967 implementation exposing upgradeToAndCall (UUPS)). (Base `#58885628`) |

Classification: **aligned baseline** (1 record).
- 'The factory proxy stays at 0x1455717668fA96534f675856347A973fA907e922 ; its implementation is now IporFusionFactoryImpl 0x378fEb2E96082FB965E2BB922AEE484d07c14014 .' (ipor.io/developer-news/smart-contracts-2026-09-28-base) (snapshot sha256 `617015a980dadddbe87a4e126e9b10dac4d357e621c48b196c2c100cc5d6b3c2`)

## 5. YieldNest — YNSecurityCouncil (contract upgrades, role admin): 3-of-5 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **YNSecurityCouncil Safe** | `0xfcad670592a3b24869C0b51a6c6FDED4F95D6975` | `getThreshold()` | YNSecurityCouncil Safe 0xfcad670592a3b24869C0b51a6c6FDED4F95D6975 (Ethereum): getThreshold() = 3 of getOwners() = 5 owners (Safe v1.3.0). (Ethereum `#26438867`) |
| **YNDelegator Safe** | `0xDF51B7843817F76220C0970eF58Ba726630028eF` | `getThreshold()` | YNDelegator Safe 0xDF51B7843817F76220C0970eF58Ba726630028eF (Ethereum): getThreshold() = 2 of getOwners() = 4 owners (Safe v1.3.0). (Ethereum `#26438867`) |

Classification: **aligned baseline, parameter delta** (2 records).
- 'YNSecurityCouncil 3/5 0xfcad670592a3b24869C0b51a6c6FDED4F95D6975' / 'Contract Upgrades, role admin.' (docs.yieldnest.finance/security/roles.md) (snapshot sha256 `a9cf6d562151ea39606412a130c1736172098424e28c1db1538ae0890b23469c`)
- 'YNDelegator 2/3 0xDF51B7843817F76220C0970eF58Ba726630028eF' / 'Delegates the EigenPods to the operators' (docs.yieldnest.finance/security/roles.md) (snapshot sha256 `a9cf6d562151ea39606412a130c1736172098424e28c1db1538ae0890b23469c`)

Context (not scored): 'YNValidatorService 2/3 0x8e20eAf121154B69B7b880FA6c617c0175c4dE2e' also validates at this pin and is not attested this Sprint (YNSecurityCouncil (upgrades, role admin) is attested, and its controller would restate that record); 'YnDev 2/3 0xa08F39d30dc865CC11a49b6e5cBd27630D6141C3' also validates at this pin and is not attested this Sprint (YNSecurityCouncil (upgrades, role admin) is attested, and its controller would restate that record).

## 6. 3Jane Lending — 3Jane Lending Upgrades admin: 7-day minimum delay, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Upgrades admin timelock** | `0x3D3C41419Ab401cd25055E8f9421D7D96d887885` | `getMinDelay()` | Upgrades admin timelock 0x3D3C41419Ab401cd25055E8f9421D7D96d887885 (Ethereum): getMinDelay() = 604800s (7 d). (Ethereum `#26438867`) |

Classification: **aligned baseline** (1 record).
- 'TimelockController (7d) | Upgrades admin' (docs.3jane.xyz/developers/addresses.md) (snapshot sha256 `53864633061a8fd910148a431e947ce2c8a422ff787407583ba0909375109544`)

Context (not scored): 'TimelockController (24h) | Parameters admin' also validates at this pin and is not attested this Sprint (the 7-day Upgrades admin timelock is attested, and its controller would restate that record).

## 7. Beefy Finance (Base) — CLM USDC-VVV strategy: the queued setDeviation(25) executed through the 6-hour timelock

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Beefy CLM strategy cowAeroBaseUSDC-VVV** | `0x03f6AFbcbf398E2362c93DDC846619f1b1b860d2` | `maxTickDeviation()` | Strategy 0x03f6AFbcbf398E2362c93DDC846619f1b1b860d2 (Base): maxTickDeviation() = 25 (was 9 when op 0x3302750e… was queued); owner() = strategyOwner timelock 0x3B60F7f25b09E71356cdFFC6475c222A466a2AC9 with getMinDelay() = 21600s (6 hours); isOperationDone(op) = true and isOperationPending(op) = false, both first read at Base #58,854,880 and again at the Sprint 26 pin. (Base `#58885628`) |

Classification: **aligned baseline** (1 record).
- docs.beefy.finance (contracts and timelocks): 'By default, a 6-hour timelock is configured for all strategy changes and upgrades.' / Pacta timelock radar brief beefy-base-op-0x3302 (decoded queued calldata): setDeviation(25) on the cowAeroBaseUSDC-VVV strategy, maxTickDeviation 9 -> 25.

## 8. StakeWise V3 (osETH) — StakeWise V3 (osETH) multisig: 4-of-7 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **StakeWise V3 (osETH) Safe** | `0x144a98cb1CdBb23610501fE6108858D9B7D24934` | `getThreshold()` | StakeWise V3 (osETH) Safe 0x144a98cb1CdBb23610501fE6108858D9B7D24934 (Ethereum): getThreshold() = 4 of getOwners() = 7 owners (Safe v1.3.0). (Ethereum `#26438867`) |

Classification: **aligned baseline** (1 record).
- 'Rejecting a transaction requires 4 of 7 committee members to co-sign.' (docs.stakewise.io/docs/governance/treasury) (snapshot sha256 `fcc7b62de21215945e9d160598e03d326342d0eac38d6d3d1be2856ce169830f`)

## 9. RPC-pinned promotions — 44 new protocols, documentation not compared

Each is published as an `rpc_observed` record (`docs/api/v1/rpc-pinned.json`): runtime bytecode, EIP-1967 slots and the first readable controller of the protocol's primary contract, at the pins above. No documentation parameter is compared, so none counts toward `verifiedCount` or `driftCount`.

| Protocol | Chain | Primary contract | Proxy | Controller |
| :--- | :--- | :--- | :--- | :--- |
| USDT0 | Ethereum | `0x6C96dE32CEa08842dcc4058c14d3aaAD7Fa41dee` | yes | contract controller `0x4de7096B2131E84Fd6b2042AD8cd9B4E43F728Fc` (3-of-5) |
| Veda | Ethereum | `0x5232bc0F5999f8dA604c42E1748A13a170F94A1B` | no | none readable |
| Tornado Cash | Ethereum | `0x77777FeDdddFfC19Ff86DB637967013e6C6A116C` | no | none readable |
| Lighter Bridge | Ethereum | `0x232CE3bd40fCd6f80f3d55A522d03f25Df784Ee2` | no | none readable |
| World Chain Bridge | Ethereum | `0x90BB48fe3310499Db36437dCAE642F721e32d094` | yes | contract controller `0xd7405BE7f3e63b094Af6C7C23D5eE33Fd82F872D` (3-of-8) |
| Aster Bridge | Ethereum | `0x604DD02d620633Ae427888d41bfd15e38483736E` | yes | multisig safe `0x1FE3Fe2Ddd19AB58B0c56054a5AF217Afb27eCEA` (4-of-7) |
| xDAI Stake Bridge | Ethereum | `0x0Ae055097C6d159879521C384F1D2123D1f195e6` | no | multisig safe `0x0DF05ADaC0159e215111696339AD4998e5871B3D` (3-of-5) |
| Starknet Bridge | Ethereum | `0xCa14007Eff0dB1f8135f4C25B34De49AB0d42766` | no | none readable |
| KPK | Ethereum | `0xbF3F63D8AC133B16d7D50C015036b33219Dd8D23` | yes | contract controller `0x5912d39421109E4bf3Dc8108b403b74773bc5379` |
| CIAN Yield Layer | Ethereum | `0xB13aa2d0345b0439b064f26B82D8dCf3f508775d` | yes | contract controller `0xf24955E9D0a05222373d4555f8831f7A05e83F62` (3-of-4) |
| Derive V3 Options | Ethereum | `0xB1D1eae60EEA9525032a6DCb4c1CE336a1dE71BE` | yes | contract controller `0xaA7b17C2539437Efa236FED262A5815358Ae2CC3` |
| RockawayX | Ethereum | `0x953972ea0C1703c58F09FB6fD2477Fdcf0FEe074` | yes | timelock `0x12917E06b55995e7a5D73681cE491774C73b7C6a` |
| Theo Network thUSD | Ethereum | `0xa3fE5c7596024E6811E14F029937D5bd8Ae485b3` | yes | timelock `0x2bB4b7E6E83FA6b77d0143dad631843cB73DCA02` |
| Saturn | Ethereum | `0x23238f20b894f29041f48D88eE91131C395Aaa71` | yes | contract controller `0xcf1072DA5f0D127AEf99136489BAd08bFa3D1A7D` |
| Avalon Superearn | Ethereum | `0x5c8D0C48810FD37A0A824D074ee290E64f7A8Fa2` | yes | contract controller `0x1792f73b586F3e931B51826195Ff015a23C86009` (4-of-5) |
| Aera V3 | Ethereum | `0x29722cC9a1cACff4a15914F9bC274B46F3b90B4F` | no | timelock `0xce75E223E6DbB0503D2B6f55bC5907d1A0372E2B` |
| BitFi Basis | Ethereum | `0xCdFb58c8C859Cb3F62ebe9Cf2767F9e036C7fb15` | yes | eoa `0xd931401B37c3A368505E7AE6dE700f2b0ad14ac6` |
| Zama | Ethereum | `0xA12CC123ba206d4031D1c7f6223D1C2Ec249f4f3` | no | none readable |
| Yield Basis | Ethereum | `0x01791F726B4103694969820be083196cC7c045fF` | no | none readable |
| Tori Finance | Ethereum | `0xd0580192E98eA6CEB9c7b6191Ed2E27560911697` | yes | multisig safe `0x0C6Bbfd2d5666d44bf28580eDEec0263692C8316` (3-of-5) |
| UNCX Network V2 | Ethereum | `0xaDB2437e6F65682B85F814fBc12FeC0508A7B1D0` | no | eoa `0x60e2E1b2a317EdfC870b6Fc6886F69083FB2099a` |
| Vesper V1 | Ethereum | `0x1b40183EFB4Dd766f11bDa7A7c3AD8982e998421` | no | multisig safe `0x9520b477Aa81180E6DdC006Fc09Fb6d3eb4e807A` (3-of-6) |
| AO Bridge | Ethereum | `0xfE08D40Eee53d64936D3128838867c867602665c` | yes | none readable |
| Concentrator | Ethereum | `0xb3Ad645dB386D7F6D753B2b9C3F4B853DA6890B8` | no | multisig safe `0xA0FB1b11ccA5871fb0225B64308e249B97804E99` (6-of-9) |
| PancakeSwap AMM V3 | Ethereum | `0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865` | no | contract controller `0x0f6f9A6dd9f065DC4455bb2B8e3F0CFFB6F2410c` (3-of-7) |
| Frankencoin | Ethereum | `0xDb861830D9Ae2d1fCF99fA0cfd3973de382B0B5b` | no | none readable |
| Sonic Gateway | Ethereum | `0xa1E2481a9CD0Cb0447EeB1cbc26F1b3fff3bec20` | yes | multisig safe `0x9Fe65a5418850015a9D8ad3Ca50d6a0B9769FbE0` (3-of-4) |
| Shift DeFi | Ethereum | `0x1d71c888961c4600cF0E31F6196b4dA7fE72e4B3` | yes | contract controller `0x83B975e5F33c0251eFEA5D355A91b3d8d58E6d9a` |
| ZEROBASE CeDeFi | Ethereum | `0xfAB99fCF605fD8f4593EDb70A43bA56542777777` | no | multisig safe `0xa14f20130E9a0a27D580FD30FD4bbF035a492AB2` (2-of-3) |
| Makina | Ethereum | `0x8d28A69328561eF9F171c58996fEcB9F494e070c` | yes | contract controller `0xEb78836D3aa3A0518A96fd7C9c549d0FFB7D6dA9` |
| 3F | Ethereum | `0x54F862fa0612A8709F6Dec4A7B39AF015CD4E82E` | no | none readable |
| Noon | Ethereum | `0xdA67B4284609d2d48e5d10cfAc411572727dc1eD` | yes | contract controller `0x55f39512cb43111A13E8440ee3e3602e72628239` |
| Arrakis Modular | Ethereum | `0x820FB8127a689327C863de8433278d6181123982` | no | multisig safe `0x5108EF86cF493905BcD35A3736e4B46DeCD7de58` (4-of-8) |
| Grvt Bridge | Ethereum | `0xAD29F2723fcdBcF665F210F25E06f97477e417cF` | no | none readable |
| K3 Capital | Ethereum | `0xdC47953c816531a8CA9E1D461AB53687d48EEA26` | yes | contract controller `0xAEb6bdd95c502390db8f52c8909F703E9Af6a346` (2-of-3) |
| Aegis YUSD | Ethereum | `0x4274cD7277C7bb0806Bd5FE84b9aDAE466a8DA0a` | no | multisig safe `0x4Fe78eF65BD8EDDED480efaB030BA680646503c8` (3-of-5) |
| Alchemix V3 | Ethereum | `0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF` | no | none readable |
| AUTOfinance | Ethereum | `0x2218F90A98b0C070676f249EF44834686dAa4285` | no | multisig safe `0x8b4334d4812C530574Bd4F2763FcD22dE94A969B` (6-of-11) |
| Hyperlane | Ethereum | `0x6D265C7dD8d76F25155F1a7687C693FDC1220D12` | no | none readable |
| Anemoy Capital | Ethereum | `0x8c213ee79581Ff4984583C6a801e5263418C4b86` | no | none readable |
| Team Finance | Ethereum | `0xCC4304A31d09258b0029eA7FE63d032f52e44EFe` | yes | multisig safe `0x088a012BF6d510aa923c814eA83807f75F7061A0` (2-of-4) |
| Sierra Protocol | Ethereum | `0xe1b1252652A2FF0CC3A4214eE73d9FeD1FEa5b4f` | no | eoa `0xbd0Ca95C5A104E14E60d0868667AF174D146C9FD` |
| Origami Finance | Ethereum | `0x07c5500359161b81eb0DfFF83097d5025D3cF5A2` | no | multisig safe `0x781B4c57100738095222bd92D37B07ed034AB696` (2-of-4) |
| IDEX V1 | Ethereum | `0xB705268213D593B8FD88d3FDEFF93AFF5CbDcfAE` | no | none readable |

## 10. Published RPC-pinned protocols moved to the Sprint 26 pins

- Extra Finance (Base): `0xBB505c54D71E9e599cB8435b4F0cEEc05fC71cbD` (Base) — bytecode keccak256 `0x2bda3204356bb12a5b68e82c0408773da0a9c311b37996552ee4e9e6756623e8`, EIP-1967 slots and controller unchanged at `#58885628`.
- Origin Protocol (SuperOETHb Base): `0xDBFeFD2e8460a6Ee4955A68582F85708BAEA60A3` (Base) — bytecode keccak256 `0x1ab9c11f4c97800cad045510e6c2ceafc40074dd151fd1ed56bd75c61a0b0421`, EIP-1967 slots and controller unchanged at `#58885628`.
- Seamless Protocol (Base): `0x0E02EB705be325407707662C6f6d3466E939f3a0` (Base) — bytecode keccak256 `0x22818496ed85629596372dcbe81fbc48c729489bdf829e198040b0f06fc4f58f`, EIP-1967 slots and controller unchanged at `#58885628`.
- Superform Core v2 (Base): `0xB5396ef2bF8CA360cEB4166b77AFb2bed20e74d4` (Base) — bytecode keccak256 `0x4dfe0bcd9f94f3d29d1dbbce22b6eb4192acf8d3108cc253ab28a51ec7caeff4`, EIP-1967 slots and controller unchanged at `#58885628`.
