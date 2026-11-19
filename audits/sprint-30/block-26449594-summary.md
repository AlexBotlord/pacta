# Sprint 30 Protocol Commitment Summary — Block `26449594`

- **Ethereum Mainnet pin**: `26449594` (`0x19396ba`), canonical block hash `0xbe263d5b378dcb7c3c4e18bd8e388f0cb2dab1adacd83de2be58c9408b377287`, timestamp `2026-11-19 14:01:59 UTC` (`1795096919`); the `finalized` head, both endpoints returning the same number and hash
- **Base Mainnet pin**: `59532664` (`0x38c6578`), canonical block hash `0xff515cb7dd2fd4e2de0f326c6c78aaaf038978e80baf47e5711377db3c07c025`, timestamp `2026-11-19 14:01:48 UTC` (`1795096908`); the `finalized` head, both endpoints returning the same number and hash
- **Scanner**: Pacta by Fractal Neurons (Pacta Protocol Commitments DRI), bulk harvester v2.1. Read-only `eth_call` / `eth_getStorageAt` / `eth_getCode` batched through Multicall3 at the pinned block, on two independent RPCs per chain with identical block hashes: `ethereum-rpc.publicnode.com` + `rpc.mevblocker.io` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base). Documentation: HTTP-200 first-party snapshots named by their SHA-256; every quote below is an exact substring of its snapshot's text and every value is re-derived from the pinned reads by the validator (no model output is trusted). The 13 targets added after the pin (abracadabra-spell--rescore, curated-s30-metapool, goldfinch--rescore, iaero-protocol--rescore, jpy-defi--rescore, monolith-market--rescore, nuva--rescore, origin-superoeth-base--rescore, panoptic-v2--rescore, quickswap-v4--rescore, shift-defi--rescore, spectra-metavaults--rescore, vetro--rescore) were read at the same block numbers and hashes through two archive-capable endpoints per chain whose block hashes match the pin: `gateway.tenderly.co` + `eth.drpc.org` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base). The merged bounty records' values were re-read by their own check (`bounty-check-s30.json`) at the same block numbers and hashes through `gateway.tenderly.co` + `eth.drpc.org` (Ethereum), `base-rpc.publicnode.com` + `mainnet.base.org` (Base).
- **Result**: `23` records for `22` protocols (`1` new; published protocols with a new record: infiniFi, Inverse Finance (FiRM), Kelp DAO (rsETH), Polygon Bridge, Resolv (USR / RLP), Threshold Network (tBTC), Abracadabra Spell, Arrakis Modular, Exactly, Flying Tulip Lend, Goldfinch, iAero Protocol, JPY DeFi, KPK, Makina, Meta Pool ETH, NUVA, Panoptic V2, Shift DeFi, Spectra MetaVaults, VETRO) — `17` aligned baselines, `0` protective deltas, `6` parameter deltas. `verifiedCount = 17`. `driftCount = 6`, the same convention as Sprints 1–29 and `PactaSentinelGuard` (`driftCount != 0` means drift).
- **RPC-pinned promotions (not attested)**: `0` further new protocols are published as RPC-pinned control-plane records at the same pins (listed below); the `180` RPC-pinned protocols already published move to these pins with every stated fact unchanged. They carry no Base EAS UID. `15` published RPC-pinned protocols are documentation-compared for the first time and become Base-EAS protocols here (Abracadabra Spell, Arrakis Modular, Exactly, Flying Tulip Lend, Goldfinch, iAero Protocol, JPY DeFi, KPK, Makina, Meta Pool ETH, NUVA, Panoptic V2, Shift DeFi, Spectra MetaVaults, VETRO); their RPC-pinned records are retired.
- **On-chain anchoring**: to be attested on Base Mainnet EAS (`0x4200000000000000000000000000000000000021`) under canonical schema `0x7ff485bc1159dff3c70eefcb9dff2d65be990301760c2d53799e5a45e3badf83` (`chainId = 1`, the Ethereum pin above); Base reads are taken at the Base pin.

## 1. Bedrock (uniBTC) — Secure Mint precondition: adequacyRatio() 900 (existing supply x 0.9 vs reserves)

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Bedrock uniBTC VaultWithoutNative** | `0x047D41F2544B7F63A8e991aF2068a363d210d6Da` | `adequacyRatio()` | Bedrock VaultWithoutNative 0x047D41F2544B7F63A8e991aF2068a363d210d6Da (Ethereum): adequacyRatio() = 900, so checkReserve() evaluates existing supply * 900 / 1000 <= reserves before minting (feeders: reserve 0xc590D9fb8eE78a0909dFF341ccf717000b7b7fF2, supply 0xE542919E4b281f10b437F947c8Ba224DdfaBc716). The incoming mint amount is absent from this inequality, so ~111.1% is not a post-mint ceiling; separate per-asset caps and collateral-transfer checks in _mint() still apply, and uniBTC.mint() (0x004E9C3EF86bc1ca1f0bB5C7662861Ee93350568) performs no PoR check of its own. MANAGER_ROLE (setAdequacyRatio / setPoRFeeder) and PAUSER_ROLE are held by 0x9251fd3D79522bB2243a58FFf1dB43E25A495aaB, an account carrying 23-byte EIP-7702 delegation code. The vault and uniBTC share ProxyAdmin 0x029E4FbDAa31DE075dD74B2238222A08233978f6, owned by the 3-of-5 Safe 0xC9dA980fFABbE2bbe15d4734FDae5761B86b5Fc3, which also holds uniBTC's DEFAULT_ADMIN_ROLE. This record does not assert a reserve deficit. (Ethereum `#26449594`) |

Classification: **parameter delta** (1 record).
- 'Before any minting action occurs, the smart contract automatically checks reserve sufficiency using the on-chain Proof of Reserve feed. If reserves fall short, the mint transaction reverts.' (docs.bedrock.technology/security/secure-mint) (snapshot sha256 `edb8d068c9c91a5a67db2006b06944143e072fa13fcbdccce729aaca3a8f337b`)

## 2. infiniFi — InfiniFiCore GOVERNANCE_TOKEN_* roles: membership moved to a new holder since #26,425,374

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **InfiniFiCore** | `0xF6d48735EcCf12bDC1DF2674b1ce3fcb3bD25490` | `hasRole(bytes32,address)` | InfiniFiCore 0xF6d48735EcCf12bDC1DF2674b1ce3fcb3bD25490 (Ethereum): for GOVERNANCE_TOKEN_ADMIN, GOVERNANCE_TOKEN_MINTER and GOVERNANCE_TOKEN_BURNER, hasRole(0xee529A21Cea25EFDF527e85BB4c597603E14CcfC) = true and hasRole(0x579B18E60d0245c0F66Fa9463610b15E226Ae8FD) = false at this pin, the reverse at Pacta's published pin #26,425,374 (record infinifi-pause-role-admin-minor-roles-s20); getRoleAdmin of each is GOVERNANCE_TOKEN_ADMIN. The new holder is a contract (6,774 bytes of code). This record states the Core role membership and administration only: no token mint / burn route and no delay is inferred. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'Our Multisig is a 4/7 multisig and may be found here' (docs.infinifi.xyz/audits) (snapshot sha256 `cb257fe56e061e143d2d1f27a6f912456952d348e0ba18eab2a9a07744488447`)

## 3. Inverse Finance (FiRM) — Policy Committee Safe: 3-of-6 (docs: 5 of 9); 4-of-7 at #26,399,876

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Inverse Finance Policy Committee Safe** | `0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7` | `getThreshold()` | Inverse Finance Policy Committee Safe 0x4b6c63E6a94ef26E2dF60b89372db2d8e211F1B7 (Ethereum): getThreshold() = 3 of 6 owners at this pin. It was 4-of-7 at Pacta's surface pin #26,399,876 (record inverse-finance-firm-policy-safe) and already 3-of-6 at #26,406,106 and at the protocol's latest pin #26,441,165: the change falls between #26,399,876 and #26,406,106, not after #26,441,165. (Ethereum `#26449594`) |

Classification: **parameter delta** (1 record).
- '| **Policy Committee**   | 5 of 9 | Governance guardian role (can cancel proposals), manages reward rate policies, operates as BondsManager                        |' (docs.inverse.finance/inverse-finance/inverse-finance/governance/governance-overview.md) (snapshot sha256 `45abc7130be829413a5851a19b2fb85fdc2be31d69f8e062cb106b0a0ee3c1d3`)

## 4. Kelp DAO (rsETH) — LRTConfig OPERATOR_ROLE: one operator account revoked since #26,406,106

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Kelp LRTConfig** | `0x947Cb49334e6571ccBFEF1f1f1178d8469D65ec7` | `hasRole(bytes32,address)` | Kelp LRTConfig 0x947Cb49334e6571ccBFEF1f1f1178d8469D65ec7 (Ethereum): hasRole(OPERATOR_ROLE 0x97667070c54ef182b0f5858b034beac1b6f3089aa2d3188bb1e8929f4fa9b929, 0x7AAd74b7f0d60D5867B59dbD377a71783425af47) = false at this pin; true at Pacta's published pin #26,406,106 (record kelp-rseth-proxyadmin-10d-timelock-s14). The documented LRTConfig address is the contract read. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- '| LRTConfig               | 0x947Cb49334e6571ccBFEF1f1f1178d8469D65ec7     |' (raw.githubusercontent.com/Kelp-DAO/LRT-rsETH/main/README.md) (snapshot sha256 `a64f44a6b7f7a019abb7ce32c3c4b9d24fd478b73243c00d42e1620141e729a8`)

## 5. Polygon Bridge — RootChainManager + predicates: upgrades via a 0 s timelock run by the 5-of-9 Safe

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Polygon RootChainManagerProxy** | `0xA0c68C638235ee32657e8f720a23ceC1bFc77C77` | `proxyOwner()` | Polygon RootChainManagerProxy 0xA0c68C638235ee32657e8f720a23ceC1bFc77C77, ERC20PredicateProxy 0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf and EtherPredicateProxy 0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30 (Ethereum): proxyOwner() = TimelockController 0xCaf0aa768A3AE1297DF20072419Db8Bb8b5C8cEf on all three; its getMinDelay() = 0 at this pin and already 0 at Pacta's Sprint 26 pin #26,438,867 (record polygon-bridge-safe-threshold-s26): not a change since that pin. The 5-of-9 Safe 0xFa7D2a996aC6350f4b56C043112Da0366a59b74c holds PROPOSER_ROLE and EXECUTOR_ROLE on that timelock and DEFAULT_ADMIN_ROLE directly on the three bridge contracts. The documentation does disclose that multisigs control contract upgrades; no censorship incident is alleged. (Ethereum `#26449594`) |
| **Polygon commitchain token-mapping multisig** | `0x424bDE99FCfB68c5a1218fd3215caFfD031f19C4` | `getThreshold()` | Polygon custom ChildERC20 mapping Safe 0x424bDE99FCfB68c5a1218fd3215caFfD031f19C4 (Ethereum): getThreshold() = 4 of 13 owners; the multisig page lists it as a 4/8 Multisig. (Ethereum `#26449594`) |

Classification: **parameter delta** (2 records).
- 'The existing multisigs do not have the capability to censor transactions, including bridge transactions.' (docs.polygon.technology/pos/reference/commit-chain-multisigs) (snapshot sha256 `904d3d83058b5979dd7f0f3e018b94b09f92d8497c83f3c7c2d3224777c1b685`)
- '4/8 Multisig 0x424bDE99FCfB68c5a1218fd3215caFfD031f19C4' (docs.polygon.technology/pos/reference/commit-chain-multisigs) (snapshot sha256 `904d3d83058b5979dd7f0f3e018b94b09f92d8497c83f3c7c2d3224777c1b685`)

## 6. Resolv (USR / RLP) — USR Counter SERVICE_ROLE: one service account revoked since #26,403,523

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Resolv USR Counter** | `0xa27a69Ae180e202fDe5D38189a3F24Fe24E55861` | `hasRole(bytes32,address)` | Resolv USR Counter 0xa27a69Ae180e202fDe5D38189a3F24Fe24E55861 (Ethereum): hasRole(SERVICE_ROLE 0xd8a7a79547af723ee3e12b59a480111268d8969c634e1a34a144d2c8b91d635b, 0x15CAd41e6BdCaDc7121ce65080489C92CF6de398) = false at this pin; true at Pacta's published pin #26,403,523 (record resolv-usr-default-admin-delay-and-safe). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'USR Counter, Ethereum 0xa27a69Ae180e202fDe5D38189a3F24Fe24E55861' (docs.resolv.xyz/litepaper/for-developers/smart-contracts) (snapshot sha256 `d0b43e4df5637c4a12bfebed9bf161aae11fee4738a1065df95194e5b1e842e4`)

## 7. Threshold Network (tBTC) — Timelock operation 0xb6671bbb: executed since #26,407,707; getMinDelay() still 86,400 s

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Threshold tBTC TimelockController** | `0x92f2d8b72a7F6a551Be60b9aa4194248E9B4913D` | `isOperationDone(bytes32)` | Threshold tBTC TimelockController 0x92f2d8b72a7F6a551Be60b9aa4194248E9B4913D (Ethereum): isOperationDone(0xb6671bbbedf818d7232a4006d4a85b21e3f3055d17244188f244c1da8263e0c7) = true and isOperationPending = false at this pin; pending at Pacta's published pin #26,407,707 (record threshold-tbtc-timelock-1d-walletregistry-op-0xb667). getMinDelay() = 86,400 s at both pins. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'Timelock Controller 0x92f2d8b72a7F6a551Be60b9aa4194248E9B4913D' (docs.threshold.network/contract-addresses/tbtc) (snapshot sha256 `7ba7bb0e959b33bb722afda9190a4493539559743ea44e03c52484d68a153ed2`)

## 8. Abracadabra Spell — Abracadabra Spell multisig: docs state 5-of-10, the Safe is 5-of-11

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Abracadabra Spell Safe** | `0x5f0DeE98360d8200b20812e174d139A1a633EDd2` | `getThreshold()` | Abracadabra Spell Safe 0x5f0DeE98360d8200b20812e174d139A1a633EDd2 (Ethereum): getThreshold() = 5 of getOwners() = 11 owners (Safe v1.3.0); it controls MagicInternetMoneyV1 0x99D8a9C45b2ecA8864373A26D1459e3Dff1e17F3. (Ethereum `#26449594`) |

Classification: **parameter delta** (1 record).
- 'The 5/10 multisign is composed of:' (docs.abracadabra.money/llms-full.txt) (snapshot sha256 `5b3240a20ae2ccf7e370bcf87bd7095f441c191aafccc85afdd6bbb10cc2bbdf`)

## 9. Arrakis Modular — Manager proxy and module beacons: timelock admin, getMinDelay() 172,800 s

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Arrakis TimelockController (manager proxy admin, module beacon owner)** | `0xAf6f9640092cB1236E5DB6E517576355b6C40b7f` | `getMinDelay()` | ArrakisMetaVaultFactory 0x820FB8127a689327C863de8433278d6181123982 (Ethereum): manager() = 0x2e6E879648293e939aA68bA4c6c129A1Be733bDA, whose EIP-1967 admin slot holds 0xAf6f9640092cB1236E5DB6E517576355b6C40b7f, a TimelockController with getMinDelay() = 172,800 s. The 5 module beacons whitelisted by the public and private module registries (0xE973Cf1e347EcF26232A95dBCc862AA488b0351b, 0xFf0474792DEe71935a0CeF1306D93fC1DCF47BD9, 0xdf4975A3515168f8c446aD4a2E974B89c64b6A38, 0x022a0C7dc85Fc3fF81f9f8Ef65Ae2813A062F556, 0x1436877899273D748eb433eFd6C437e37D627255) all have owner() = 0xAf6f9640092cB1236E5DB6E517576355b6C40b7f. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'Arrakis implements a 48-hour timelock on upgrades' (arrakis.finance/risks) (snapshot sha256 `6d01a39be9403a2fd37d0db66c9b2fe8bae4944bb325ea8abbb4e6e13c8d2196`)

## 10. Exactly — Auditor upgrade path: ProxyAdmin owned by a timelock, getMinDelay() 86,400 s

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Exactly TimelockController (owner of the Auditor's ProxyAdmin)** | `0x92024C4bDa9DA602b711B9AbB610d072018eb58b` | `getMinDelay()` | Exactly Auditor 0x310A2694521f75C7B2b64b5937C16CE65C3EFE01 (Ethereum): EIP-1967 admin slot = ProxyAdmin 0x3866eA62494597A5EDeA4A97f9429f82b9d7Ca34; ProxyAdmin owner() = 0x92024C4bDa9DA602b711B9AbB610d072018eb58b, a TimelockController with getMinDelay() = 86,400 s. The access-control page lists the Auditor among the contracts the TimelockController can upgrade. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'The timelock period is 24 hours' (docs.exact.ly/security/access-control.md) (snapshot sha256 `cfffa897037c5903b8012a77b7eada1f9a385ad923f5b2141c1c8461e59bf8f7`)

## 11. Flying Tulip Lend — Treasury Safe (FT owner): 3-of-5

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Flying Tulip treasury Safe** | `0x1118e1c057211306a40A4d7006C040dbfE1370Cb` | `getThreshold()` | Flying Tulip treasury Safe 0x1118e1c057211306a40A4d7006C040dbfE1370Cb (Ethereum): getThreshold() = 3 of 5 owners. It is owner() of the FT token 0x5DD1A7A369e8273371d2DBf9d83356057088082c. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- '| `0x1118e1c057211306a40A4d7006C040dbfE1370Cb` |  3/5      | Msig, treasury   | PutManager, Marketplace  |' (docs.flyingtulip.com/llms.txt) (snapshot sha256 `b407fe18323f94cda6a83980f367bcf869dfef8ccade3651562a3c1ba7c9eb1a`)

## 12. Goldfinch — Goldfinch multisig: docs state 6-of-10, the Safe is 6-of-12

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Goldfinch Council multisig (governance signers of the protocol)** | `0xBEb28978B2c755155f20fd3d09Cb37e300A6981f` | `getThreshold()` | Goldfinch Safe 0xBEb28978B2c755155f20fd3d09Cb37e300A6981f (Ethereum): getThreshold() = 6 of getOwners() = 12 owners (Safe v1.1.1). (Ethereum `#26449594`) |

Classification: **parameter delta** (1 record).
- 'The Goldfinch Council is a 6-of-10 multisig with 10 members who represent all stakeholders of the protocol' (docs.goldfinch.finance/goldfinch/goldfinch-v1/governance.md) (snapshot sha256 `95025f16f08373b00f6cd57b159d1d2c0835c3aec5e2e5c4675d81bc74c62370`)

## 13. iAero Protocol — iAero Protocol multisig: 3-of-4 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **iAero Protocol Safe** | `0x1039CB48254a3150fC604d4B9ea08F66f4739D37` | `getThreshold()` | iAero Protocol Safe 0x1039CB48254a3150fC604d4B9ea08F66f4739D37 (Base): getThreshold() = 3 of getOwners() = 4 owners (Safe v1.4.1); it controls StakedIAERO 0x44D8172b95a208082327f58c5b42269d48a34847. (Base `#59532664`) |

Classification: **aligned baseline** (1 record).
- 'xiAERO's owner is the protocol Safe, a 3-of-4 multisig (`0x1039CB48254a3150fC604d4B9ea08F66f4739D37`)' (docs.iaero.finance/llms-full.txt) (snapshot sha256 `e4fbb4b8fc34b14f82873c0471ca5b65d13425a8135a136e76806622329f34a9`)

## 14. JPY DeFi — JPY DeFi timelock: 12-hour minimum delay, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Governance TimelockController queueing upgrades of the dToken and Strategy layers** | `0xf27de84F11E089B838769EDFcFf9872BC45c84Fe` | `getMinDelay()` | JPY DeFi TimelockController 0xf27de84F11E089B838769EDFcFf9872BC45c84Fe (Ethereum): getMinDelay() = 43200s (12 h). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'Ordinary configuration changes and upgrades to JPY DeFi's proprietary layers are proposed by a multisig and executed through a 12-hour TimelockController.' (jpydf.gitbook.io/jpy-defi/governance/governance-and-timelock.md) (snapshot sha256 `3a0e770864e9d6db0d460cd17a8323748b44513495f3f33152b898c51f1a816d`)

## 15. KPK — Security Council Safe (vault owner and sentinel): 5-of-8

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **KPK Security Council Safe** | `0x8b884f80B3B839F52b6cE168f133e7a5D1f0A537` | `getThreshold()` | KPK Security Council Safe 0x8b884f80B3B839F52b6cE168f133e7a5D1f0A537 (Ethereum): getThreshold() = 5 of 8 owners. The documentation names it the owner and sentinel of the KPK vaults (legacy v1 vaults excepted). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'Security Council Safe (5/8), [`0x8b884f80B3B839F52b6cE168f133e7a5D1f0A537`]' (docs.kpk.io/llms-full.txt) (snapshot sha256 `5e8e0a31a6106fc778289f49538b59a20d2d218669bf7d11844329757c47c727`)

## 16. Makina — Upgrade role (6): DAO multisig execution delay 172,800 s

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Makina AccessManager** | `0x0fCEfa3f1047F35521A49cD8B06faBd588665d7F` | `getAccess(uint64,address)` | Makina AccessManager 0x0fCEfa3f1047F35521A49cD8B06faBd588665d7F (Ethereum): getAccess(6, DAO multisig 0x62244C74e1d09b3D86EF7342d354b5D7770bDE10) = member since 1779354899, execution delay 172,800 s; getRoleGuardian(6) = 7. The HubCoreFactory 0x8d28A69328561eF9F171c58996fEcB9F494e070c's EIP-1967 admin is ProxyAdmin 0xEb78836D3aa3A0518A96fd7C9c549d0FFB7D6dA9, whose owner() is the AccessManager. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- '`INFRA_UPGRADE_ROLE` is held by the DAO with a **2-day execution delay**' (docs.makina.finance/llms-full.txt) (roles table: INFRA_UPGRADE_ROLE = 6) (snapshot sha256 `d373a6b9c77d67a38e679037564db2074a78af4956870ae896e85a7ed12ebbb9`)

## 17. Meta Pool ETH — spETH upgrade admin: the documented ProxyAdmin, owned by the DAO Admin Safe (3-of-6)

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Meta Pool ProxyAdmin (spETH, Liquid Unstake Pool, MetaPoolETH)** | `0x806F870ee04A2CC8bf2aD053BAa5ed9999A1f182` | `owner()` | Meta Pool spETH 0xD06f6a56c5f599cB375B616DF306f32B7F6f4A0E (Ethereum): EIP-1967 proxy (implementation 0xD3dB79D2D00A6B82531D8Ccf65C376d9eE9513aC), admin slot = ProxyAdmin 0x806F870ee04A2CC8bf2aD053BAa5ed9999A1f182. The same ProxyAdmin administers the published target (MetaPoolETH 0x48AFbBd342F64EF8a9Ab1C143719b63C2AD81710) and the documented Liquid Unstake Pool 0xdF261F967E87B2aa44e18a22f4aCE5d7f74f03Cc. ProxyAdmin owner() = 0x24D9664Ba8384D94499d6698ab285b69E879D971, a 3-of-6 Safe: the contract list names both addresses (Proxy Admin; SAFE Multisig (DAO Admin)). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'Proxy Admin Address: 0x806F870ee04A2CC8bf2aD053BAa5ed9999A1f182' (docs.metapool.app/llms-full.txt) (snapshot sha256 `fee6e7f83aee61a1dce9cba52945146eda278d9ee40a222736d4f316b6b724ce`)

## 18. NUVA — DedicatedVaultRouter upgrade authority: timelock, getMinDelay() 172,800 s

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **NUVA TimelockController (owner of the DedicatedVaultRouter)** | `0xDEa75A312b2F99b5A7558c4636897b39C195E241` | `getMinDelay()` | NUVA DedicatedVaultRouter 0x50AE1e4A612A4623b747aEeFb30aFBA82804e12c (Ethereum) is an EIP-1967 proxy (implementation 0x027207E16E2BB920dc89AA9FeF7826e23091588a, admin slot zero: upgrades are authorized by owner()); owner() = 0xDEa75A312b2F99b5A7558c4636897b39C195E241, a TimelockController with getMinDelay() = 172,800 s. (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'every upgrade is subject to a 48-hour timelock before it takes effect' (nuva.finance/docs/security-trust) (snapshot sha256 `6355d6e698a55aeebb666029893c6eaf19e3360e651c7828ce4d44f3818b10f3`)

## 19. Panoptic V2 — Panoptic V2 RiskEngineProxy: upgradeable (proxy admin), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Panoptic V2 RiskEngineProxy** | `0x000000000000ffE5eFdB5AE76b9200263C58b4c0` | slot `eip1967.proxy.implementation` | Panoptic V2 RiskEngineProxy 0x000000000000ffE5eFdB5AE76b9200263C58b4c0 (Ethereum): EIP-1967 implementation slot = 0x000000000000f69c150aFEa8Cc4f8fC4462AdBB4, admin slot = 0x22BD5EC2Ee6685C373781420E12c1426dd7776F2; upgradeable (EIP-1967 implementation + admin slot (transparent proxy)). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'Pools retain a fixed RiskEngine proxy address; an authorized implementation upgrade can change their risk policy in place.' (panoptic.xyz/docs/contracts/parameters.md) (snapshot sha256 `64017b7ea060ba5bf707590d20bff0c5db5b42ba1dd73e0b4640bda1d76fd70a`)

## 20. Shift DeFi — Shift DeFi multisig: 2-of-6 Safe, as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Shift DeFi Safe** | `0x4cC8D45644eCCD8cA77DBF3A8E3eE2dBf4596983` | `getThreshold()` | Shift DeFi Safe 0x4cC8D45644eCCD8cA77DBF3A8E3eE2dBf4596983 (Ethereum): getThreshold() = 2 of getOwners() = 6 owners (Safe v1.4.1). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'The Emergency & Reshuffling Multisig uses Safe v1.4.1 with a 2-of-6 signature threshold and 2 proposers.' (docs.shiftdefi.com/security/multisig-and-timelock.md) (snapshot sha256 `bcaebb6ca1c5dd313e14a9bd6c1d809b905ad970aac33bdba5543ad21da58026`)

## 21. Spectra MetaVaults — Spectra MetaVaults TransparentUpgradeableProxy: upgradeable (proxy admin), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **Spectra MetaVaults TransparentUpgradeableProxy** | `0x16b28223b607B4D90e2eC628fdC1a0AD9Ee1f6B8` | slot `eip1967.proxy.implementation` | Spectra MetaVaults TransparentUpgradeableProxy 0x16b28223b607B4D90e2eC628fdC1a0AD9Ee1f6B8 (Ethereum): EIP-1967 implementation slot = 0x47a9B7E7E1bf368D2e0f3053Dde9270DD8E48eEA, admin slot = 0xf300d5032D7F607f1C5a54BA70b93bAA62172f20; upgradeable (EIP-1967 implementation + admin slot (transparent proxy)). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- 'MetaVault contracts use a proxy pattern — the addresses below are the proxy addresses that users and integrators should interact with.' (dev.spectra.finance/docs/metavaults/deployed-contracts.md) (snapshot sha256 `89d72773429b0d6c9dd18b132e9b635d2f1d35dd1ae0bf8b5bccfa82a3d1747c`)

## 22. VETRO — VETRO contract: upgradeable (proxy admin), as documented

| Contract / Check | Address | Selector / slot | Observation |
| :--- | :--- | :--- | :--- |
| **VETRO contract** | `0xDaD503f8B9d42bb7af3AfC588358D30163e4416F` | slot `eip1967.proxy.implementation` | VETRO contract 0xDaD503f8B9d42bb7af3AfC588358D30163e4416F (Ethereum): EIP-1967 implementation slot = 0x07Ee70DFd5a74d4a038Ff6AAE1d31Ca2C71F4DF1, admin slot = 0x83B2435d9A30b7463B3Ba997ba47a14B73149e2A; upgradeable (EIP-1967 implementation + admin slot (transparent proxy)). (Ethereum `#26449594`) |

Classification: **aligned baseline** (1 record).
- '**Upgradeable proxy patterns** using ERC-7201 namespaced storage for safe upgrade paths' (docs.vetro.org/llms-full.txt) (snapshot sha256 `297c5c971c2e24fb2bd1bb42b4d5207c55c8825b93b685476c3e3eb7408964d3`)

## 23. RPC-pinned promotions — 0 new protocols, documentation not compared

Each is published as an `rpc_observed` record (`docs/api/v1/rpc-pinned.json`): runtime bytecode, EIP-1967 slots and the first readable controller of the protocol's primary contract, at the pins above. No documentation parameter is compared, so none counts toward `verifiedCount` or `driftCount`.

| Protocol | Chain | Primary contract | Proxy | Controller |
| :--- | :--- | :--- | :--- | :--- |

## 24. Published RPC-pinned protocols moved to the Sprint 30 pins

- Extra Finance (Base): `0xBB505c54D71E9e599cB8435b4F0cEEc05fC71cbD` (Base) — bytecode keccak256 `0x2bda3204356bb12a5b68e82c0408773da0a9c311b37996552ee4e9e6756623e8`, EIP-1967 slots and controller unchanged at `#59532664`.
- Origin Protocol (SuperOETHb Base): `0xDBFeFD2e8460a6Ee4955A68582F85708BAEA60A3` (Base) — bytecode keccak256 `0x1ab9c11f4c97800cad045510e6c2ceafc40074dd151fd1ed56bd75c61a0b0421`, EIP-1967 slots and controller unchanged at `#59532664`.
- Seamless Protocol (Base): `0x0E02EB705be325407707662C6f6d3466E939f3a0` (Base) — bytecode keccak256 `0x22818496ed85629596372dcbe81fbc48c729489bdf829e198040b0f06fc4f58f`, EIP-1967 slots and controller unchanged at `#59532664`.
- Superform Core v2 (Base): `0xB5396ef2bF8CA360cEB4166b77AFb2bed20e74d4` (Base) — bytecode keccak256 `0x4dfe0bcd9f94f3d29d1dbbce22b6eb4192acf8d3108cc253ab28a51ec7caeff4`, EIP-1967 slots and controller unchanged at `#59532664`.
- 3F: `0x54F862fa0612A8709F6Dec4A7B39AF015CD4E82E` (Ethereum) — bytecode keccak256 `0x4690b1cca8e819c6cf7d976ae8e296e41138d1a2d722c8d07b3394d431fc226e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Aegis YUSD: `0x4274cD7277C7bb0806Bd5FE84b9aDAE466a8DA0a` (Ethereum) — bytecode keccak256 `0x673a34bc4b7ddbb2aaf2ff848f3fe7734a98331af20f2f0f55bca5dd131c39ff`, EIP-1967 slots and controller unchanged at `#26449594`.
- Aera V3: `0x29722cC9a1cACff4a15914F9bC274B46F3b90B4F` (Ethereum) — bytecode keccak256 `0xf4d329ab04c7cdbab16fe48996f83e05fbbdb9222305402bc9049c842ec5cfe7`, EIP-1967 slots and controller unchanged at `#26449594`.
- Alchemix V3: `0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF` (Ethereum) — bytecode keccak256 `0x7ed5fbbd93fd174456aa5a52eab2c19ac15bbb6e07f08667b859ac41819f5208`, EIP-1967 slots and controller unchanged at `#26449594`.
- Anemoy Capital: `0x8c213ee79581Ff4984583C6a801e5263418C4b86` (Ethereum) — bytecode keccak256 `0x7d02f853cd5ee5a6aa0a08213618a6f3c3d594d4c030be909d0e894b6a37c749`, EIP-1967 slots and controller unchanged at `#26449594`.
- AO Bridge: `0xfE08D40Eee53d64936D3128838867c867602665c` (Ethereum) — bytecode keccak256 `0x53c0835906d5b2eed9f973e77d7c785956ea1d182c80679951ae09c4cfaa13c1`, EIP-1967 slots and controller unchanged at `#26449594`.
- Aster Bridge: `0x604DD02d620633Ae427888d41bfd15e38483736E` (Ethereum) — bytecode keccak256 `0x0959a24babb02d4d6c6ef27aaec9c34e824a2c55d24b13a8b3dae8401138e1c4`, EIP-1967 slots and controller unchanged at `#26449594`.
- AUTOfinance: `0x2218F90A98b0C070676f249EF44834686dAa4285` (Ethereum) — bytecode keccak256 `0x851c7bea863541332656d77df23c217c5013416390dcefce9992f95655446c1e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Avalon Superearn: `0x5c8D0C48810FD37A0A824D074ee290E64f7A8Fa2` (Ethereum) — bytecode keccak256 `0xe5e3693157141608a301682c8c228c0277eac7efc0b98b57f874ca49752b5fd8`, EIP-1967 slots and controller unchanged at `#26449594`.
- BitFi Basis: `0xCdFb58c8C859Cb3F62ebe9Cf2767F9e036C7fb15` (Ethereum) — bytecode keccak256 `0x168f6bb27d4410c24923a1fa9ccad3e18530a1bdaa23935960b410be0aa1409c`, EIP-1967 slots and controller unchanged at `#26449594`.
- CIAN Yield Layer: `0xB13aa2d0345b0439b064f26B82D8dCf3f508775d` (Ethereum) — bytecode keccak256 `0xe56c30257588d9d02e1a523887f333c31fb17cc1f0b6ffc871685d836403c24f`, EIP-1967 slots and controller unchanged at `#26449594`.
- Concentrator: `0xb3Ad645dB386D7F6D753B2b9C3F4B853DA6890B8` (Ethereum) — bytecode keccak256 `0xce1d4da3ce85dfe2287a99b988ea0393a3d3c08472adbb065266e798585682f2`, EIP-1967 slots and controller unchanged at `#26449594`.
- Derive V3 Options: `0xB1D1eae60EEA9525032a6DCb4c1CE336a1dE71BE` (Ethereum) — bytecode keccak256 `0x4b19308ff101c086627922584dfdf6fb6f57828ecd7b0d5e84cea7cc36e2ca2b`, EIP-1967 slots and controller unchanged at `#26449594`.
- Frankencoin: `0xDb861830D9Ae2d1fCF99fA0cfd3973de382B0B5b` (Ethereum) — bytecode keccak256 `0x9dacc056e5f2d59b75a9c9ae8a3cd5134abf7bfb675462f50c12ab777603cc62`, EIP-1967 slots and controller unchanged at `#26449594`.
- Grvt Bridge: `0xAD29F2723fcdBcF665F210F25E06f97477e417cF` (Ethereum) — bytecode keccak256 `0x61f4a7aa2e0a3dcc40aa8314f37f612c0d4705c416a2bbe73430f130a25297c5`, EIP-1967 slots and controller unchanged at `#26449594`.
- Hyperlane: `0x6D265C7dD8d76F25155F1a7687C693FDC1220D12` (Ethereum) — bytecode keccak256 `0xa88000255e1f96de07122238840c31fd0b48f520430ff6dd78b7100dfc738358`, EIP-1967 slots and controller unchanged at `#26449594`.
- IDEX V1: `0xB705268213D593B8FD88d3FDEFF93AFF5CbDcfAE` (Ethereum) — bytecode keccak256 `0x41a6bbcc6ebf380d013e5bf81e1f04f14177e26857360fdb5fb0d96ab290b6a3`, EIP-1967 slots and controller unchanged at `#26449594`.
- K3 Capital: `0xdC47953c816531a8CA9E1D461AB53687d48EEA26` (Ethereum) — bytecode keccak256 `0xf44809e3d915cd908b4db54ad7e3de8d0923d8c68119d754ef9566c10573fd5e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Lighter Bridge: `0x232CE3bd40fCd6f80f3d55A522d03f25Df784Ee2` (Ethereum) — bytecode keccak256 `0x509f7c0bd6c3e1d958030033e1e1e3ae1be166bbbefd2e8d8835fa72ba1a4236`, EIP-1967 slots and controller unchanged at `#26449594`.
- Noon: `0xdA67B4284609d2d48e5d10cfAc411572727dc1eD` (Ethereum) — bytecode keccak256 `0xc961838fce3287ae2c0a9677e4ae834840d6c90947f96e286d88b13299c04900`, EIP-1967 slots and controller unchanged at `#26449594`.
- Origami Finance: `0x07c5500359161b81eb0DfFF83097d5025D3cF5A2` (Ethereum) — bytecode keccak256 `0x62d6e97082d84feec6a1fb354b9279aa8ceb6b7ffaf88d1bb82e9225bf1553e3`, EIP-1967 slots and controller unchanged at `#26449594`.
- PancakeSwap AMM V3: `0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865` (Ethereum) — bytecode keccak256 `0x8191d3ab1d55d3da9822199f28865415c99566b6f1aee4a4b16713f57930678c`, EIP-1967 slots and controller unchanged at `#26449594`.
- RockawayX: `0x953972ea0C1703c58F09FB6fD2477Fdcf0FEe074` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26449594`.
- Saturn: `0x23238f20b894f29041f48D88eE91131C395Aaa71` (Ethereum) — bytecode keccak256 `0x6d0ce32ba65bd273fcbdc767be5fd8924abd4ce0d6fb5c84ba39c28be05d2457`, EIP-1967 slots and controller unchanged at `#26449594`.
- Sierra Protocol: `0xe1b1252652A2FF0CC3A4214eE73d9FeD1FEa5b4f` (Ethereum) — bytecode keccak256 `0x1151e0ba784b3fe266ae02886e6435603745e3e3b288a9f5ad182737b0faa1ac`, EIP-1967 slots and controller unchanged at `#26449594`.
- Sonic Gateway: `0xa1E2481a9CD0Cb0447EeB1cbc26F1b3fff3bec20` (Ethereum) — bytecode keccak256 `0x23a1472fa83f7542cf6eecb7637465cd72aa2470d206dd81dcfe9d1db4e8c633`, EIP-1967 slots and controller unchanged at `#26449594`.
- Starknet Bridge: `0xCa14007Eff0dB1f8135f4C25B34De49AB0d42766` (Ethereum) — bytecode keccak256 `0x7ef33cd5b6004a6c025dee0df472999ec54227ba2a7ab0b612537ca5219ee275`, EIP-1967 slots and controller unchanged at `#26449594`.
- Team Finance: `0xCC4304A31d09258b0029eA7FE63d032f52e44EFe` (Ethereum) — bytecode keccak256 `0x17404120e429d743f170be02a42dd5018a3d340863ef7c7bf41db1baab1a1cd7`, EIP-1967 slots and controller unchanged at `#26449594`.
- Theo Network thUSD: `0xa3fE5c7596024E6811E14F029937D5bd8Ae485b3` (Ethereum) — bytecode keccak256 `0xc8ff19e35002275bcbf9f8eede7c2030293c871666ff06c9eb19933826d81271`, EIP-1967 slots and controller unchanged at `#26449594`.
- Tori Finance: `0xd0580192E98eA6CEB9c7b6191Ed2E27560911697` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26449594`.
- Tornado Cash: `0x77777FeDdddFfC19Ff86DB637967013e6C6A116C` (Ethereum) — bytecode keccak256 `0x7bb3883a4af95ea24983177dbcb682a021f389b77835ed266bfa30bda271c77b`, EIP-1967 slots and controller unchanged at `#26449594`.
- UNCX Network V2: `0xaDB2437e6F65682B85F814fBc12FeC0508A7B1D0` (Ethereum) — bytecode keccak256 `0x9ef6c8d303308ae4c0cfd6466aff6fd25946facfdeb76992707386a34ae5879f`, EIP-1967 slots and controller unchanged at `#26449594`.
- USDT0: `0x6C96dE32CEa08842dcc4058c14d3aaAD7Fa41dee` (Ethereum) — bytecode keccak256 `0xe5e3693157141608a301682c8c228c0277eac7efc0b98b57f874ca49752b5fd8`, EIP-1967 slots and controller unchanged at `#26449594`.
- Veda: `0x5232bc0F5999f8dA604c42E1748A13a170F94A1B` (Ethereum) — bytecode keccak256 `0xf349ba5ac81eb0f8ad05e353e581928b157ebce878db155eaea6f4534cb5fe2b`, EIP-1967 slots and controller unchanged at `#26449594`.
- World Chain Bridge: `0x90BB48fe3310499Db36437dCAE642F721e32d094` (Ethereum) — bytecode keccak256 `0xfa8c9db6c6cab7108dea276f4cd09d575674eb0852c0fa3187e59e98ef977998`, EIP-1967 slots and controller unchanged at `#26449594`.
- xDAI Stake Bridge: `0x0Ae055097C6d159879521C384F1D2123D1f195e6` (Ethereum) — bytecode keccak256 `0xc142222c43ea630db16763d6dd8e619a9cecc3bf121785475841cdc9f94361b7`, EIP-1967 slots and controller unchanged at `#26449594`.
- Yield Basis: `0x01791F726B4103694969820be083196cC7c045fF` (Ethereum) — bytecode keccak256 `0xb6dd52f54a35ee897ad6edc361c7dd1ce400f92031dc4b536514bf984f327777`, EIP-1967 slots and controller unchanged at `#26449594`.
- Zama: `0xA12CC123ba206d4031D1c7f6223D1C2Ec249f4f3` (Ethereum) — bytecode keccak256 `0xf172c8c96f8ba07e22f43c9bd9f1d3b96d1dbae326c61b388b4fbd7b517f9123`, EIP-1967 slots and controller unchanged at `#26449594`.
- ZEROBASE CeDeFi: `0xfAB99fCF605fD8f4593EDb70A43bA56542777777` (Ethereum) — bytecode keccak256 `0x5ea0a98719770123cf8cb56ed504a5975019e01868505874dc2fb31b034a7cfe`, EIP-1967 slots and controller unchanged at `#26449594`.
- ADI Bridge: `0x8B1484d57abBE239bB280661377363b03c89CaEa` (Ethereum) — bytecode keccak256 `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`, EIP-1967 slots and controller unchanged at `#26449594`.
- Ankr: `0x8290333ceF9e6D528dD5618Fb97a76f268f3EDD4` (Ethereum) — bytecode keccak256 `0x0c0a59b206d3675604c0d605ecbf7ec2c7deedaee03fd40f9f94e4bd7e954798`, EIP-1967 slots and controller unchanged at `#26449594`.
- Anvil: `0xAEEAa594e7dc112D67b8547fe9767a02c15B5597` (Ethereum) — bytecode keccak256 `0x429a8e131784eb8288d76e76719f82390c239cc6c473298627c6524c61706197`, EIP-1967 slots and controller unchanged at `#26449594`.
- Arkis: `0xEA623eebd9c5bFd56067e36C89Db0C13e6c70ba8` (Ethereum) — bytecode keccak256 `0xddb2c9db76f64c21284e72e3ac43a2e9c263034b5b317504860a5adce96d91e7`, EIP-1967 slots and controller unchanged at `#26449594`.
- Aura: `0xC0c293ce456fF0ED870ADd98a0828Dd4d2903DBF` (Ethereum) — bytecode keccak256 `0x29fa14ed566cfc96628bfb573316782856bc583b0b3079fa524d13a38dd0d58b`, EIP-1967 slots and controller unchanged at `#26449594`.
- Avant avETH: `0x9469470C9878bf3d6d0604831d9A3A366156f7EE` (Ethereum) — bytecode keccak256 `0x9591b0f9a962e55ec9d4ab889638af7d31a3368e23618ee5599a609dcc1159fd`, EIP-1967 slots and controller unchanged at `#26449594`.
- Badger DAO: `0x3472A5A71965499acd81997a54BBA8D852C6E53d` (Ethereum) — bytecode keccak256 `0x2dda0f3a6bee3e5768e41adb77021f8f5653897a1c65a5f106265b17fa2c299b`, EIP-1967 slots and controller unchanged at `#26449594`.
- Bancor V3: `0x1F573D6Fb3F13d689FF844B4cE37794d79a7FF1C` (Ethereum) — bytecode keccak256 `0xf1495e99bb63cf244df1a4e88c356e556d15497028e15842edccb032e3463bb4`, EIP-1967 slots and controller unchanged at `#26449594`.
- Bio Protocol: `0xcb1592591996765Ec0eFc1f92599A19767ee5ffA` (Ethereum) — bytecode keccak256 `0x4a3a20ab3b6b8cfc24ee0663b951d7c9139f6c9f92e11c5e9efb31557c3aa986`, EIP-1967 slots and controller unchanged at `#26449594`.
- Blur Bids: `0x5283D291DBCF85356A21bA090E6db59121208b44` (Ethereum) — bytecode keccak256 `0xeb2957414f3daa1495aa331973f631de8ee6c87994fc4a612da20a97f4e14150`, EIP-1967 slots and controller unchanged at `#26449594`.
- Brickken: `0x0A638F07ACc6969abF392bB009f216D22aDEa36d` (Ethereum) — bytecode keccak256 `0xdf740b7eec2ee1e88020370781c03aab1b04dc55a1dc622b48cb7002ce87fb8e`, EIP-1967 slots and controller unchanged at `#26449594`.
- cBridge: `0x4F9254C83EB525f9FCf346490bbb3ed28a81C667` (Ethereum) — bytecode keccak256 `0x2f20f33e040f6be6f03b13a42e4c0b28a9834690ddfbf919a9a49b95007aadd3`, EIP-1967 slots and controller unchanged at `#26449594`.
- Chamber Vaults: `0xca1207647Ff814039530D7d35df0e1Dd2e91Fa84` (Ethereum) — bytecode keccak256 `0x1154b4431256a941501d558a4d3a3fd001a431840461ac32435cd878b90946ac`, EIP-1967 slots and controller unchanged at `#26449594`.
- Cronos zkEVM Bridge: `0x28Ff2E4dD1B58efEB0fC138602A28D5aE81e44e2` (Ethereum) — bytecode keccak256 `0xee8a105971995661291a9f284262a87abf2381b3cdc93b2c8fbeffe4cd636dd9`, EIP-1967 slots and controller unchanged at `#26449594`.
- cVault Finance: `0x62359Ed7505Efc61FF1D56fEF82158CcaffA23D7` (Ethereum) — bytecode keccak256 `0x35d8cb7adaa6c80bfac8896682d5aeb4d367bb2c199f42e1732957b245219caf`, EIP-1967 slots and controller unchanged at `#26449594`.
- D2 Finance: `0x07Dff4087b43c4A759f4Fc69511c26d51929dAF4` (Ethereum) — bytecode keccak256 `0x86b6dc26240e014376e03dac6bdfc333b63e56ee7506e1000786f8c33a6fb8c0`, EIP-1967 slots and controller unchanged at `#26449594`.
- DODO AMM: `0x43Dfc4159D86F3A37A5A4B3D4580b888ad7d4DDd` (Ethereum) — bytecode keccak256 `0xa3ed78c2deb7d2c3197c7f1f83847c7a2e806273099255078f11d84387b70ab9`, EIP-1967 slots and controller unchanged at `#26449594`.
- Dolomite: `0x003Ca23Fd5F0ca87D01F6eC6CD14A8AE60c2b97D` (Ethereum) — bytecode keccak256 `0xf7ff557bf8276c5cc8a12bce5ceca435a0ca9094cc6c5ac7548b5a5395aa2a07`, EIP-1967 slots and controller unchanged at `#26449594`.
- Drakewell USDdw: `0x2B5895b716311A1eaC8f93fB88C56aF9eC8C1A69` (Ethereum) — bytecode keccak256 `0xbb70cbce5814331e91f8533edb5153fbccaa65f6ab99f5baf5d9d766c4888309`, EIP-1967 slots and controller unchanged at `#26449594`.
- dYdX V3: `0x92D6C1e31e14520e676a687F0a93788B716BEff5` (Ethereum) — bytecode keccak256 `0x09b771bde251cc95f8d1cb964497c7170f300839a72eda826deecc7df0142ddb`, EIP-1967 slots and controller unchanged at `#26449594`.
- Easedefi.org: `0xEa5eDef1287AfDF9Eb8A46f9773AbFc10820c61c` (Ethereum) — bytecode keccak256 `0x614b8db3fa7d70d7f8369ff9cca21049df4bf56aef08bce338c66e82dfa1e1a1`, EIP-1967 slots and controller unchanged at `#26449594`.
- edgeX Bridge: `0xB0076DE78Dc50581770BBa1D211dDc0aD4F2a241` (Ethereum) — bytecode keccak256 `0xde5d6e9d24143b30c748d881d84f897a424b86c8a931badaa1ca8b4dd7e4051e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Eigenpie: `0x20b70E4A1883b81429533FeD944d7957121c7CAB` (Ethereum) — bytecode keccak256 `0x02f54b576cbf2fd200517ffc5f9cdbd7c08314e9eb8002043e355001fa4e373f`, EIP-1967 slots and controller unchanged at `#26449594`.
- FermiSwap: `0xb1076fE3AB5e28005C7c323Bac5AC06a680d452e` (Ethereum) — bytecode keccak256 `0xba367f88fc2257711f741c9f6c4bca4b20e1030ab06635bbb903b0bf052d2638`, EIP-1967 slots and controller unchanged at `#26449594`.
- GETH: `0x3802c218221390025BCEABBaD5D8C59F40eB74B8` (Ethereum) — bytecode keccak256 `0xb5e0d7b2fb71f8589a2298f1e39888d6f7df1f3cf7338f44ce9f64337a724b1a`, EIP-1967 slots and controller unchanged at `#26449594`.
- Gondi V3: `0xf65B99CE6DC5F6c556172BCC0Ff27D3665a7d9A8` (Ethereum) — bytecode keccak256 `0x5a24688c56b5bd15d41e7fad9201ef8472da0b86cbda8ede7713b58ce6b09600`, EIP-1967 slots and controller unchanged at `#26449594`.
- Hakka Finance: `0x0E29e5AbbB5FD88e28b2d355774e73BD47dE3bcd` (Ethereum) — bytecode keccak256 `0x3cfb96debb564e364f4c21b2f07a940c6fcfc7557c0e33f948af2b2c937ad7c0`, EIP-1967 slots and controller unchanged at `#26449594`.
- Harvest Finance: `0xa0246c9032bC3A600820415aE600c6388619A14D` (Ethereum) — bytecode keccak256 `0x9c1795bb8a1ae198f6f98c74e4c0cebb6726da3b592ccda396ab78ee30c65fed`, EIP-1967 slots and controller unchanged at `#26449594`.
- Hop Protocol: `0xc5102fE9359FD9a28f877a67E36B0F050d81a3CC` (Ethereum) — bytecode keccak256 `0x4e5daef6a4c9a066d1d4f6c3e77a1eaefae7117c725cba2328ddb399d2260fe2`, EIP-1967 slots and controller unchanged at `#26449594`.
- InceptionLRT (Isolated Restaking): `0x814CC6B8fd2555845541FB843f37418b05977d8d` (Ethereum) — bytecode keccak256 `0x4d9be648c5bf39973670d9f8b481d5d0b971e6a2db2deccc6b98cde21c5dd83e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Index Coop: `0x0954906da0Bf32d5479e25f46056d22f08464cab` (Ethereum) — bytecode keccak256 `0x72b69cf0962b8043d955eb54b5ec4dcdefed60b1c8ecd2581003bdd4e916559e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Injective Bridge: `0xe28b3B32B6c345A34Ff64674606124Dd5Aceca30` (Ethereum) — bytecode keccak256 `0x2860075dbbe8adda4739434d6accb0f815f6c16d66c1334920c2dde5cdf67f48`, EIP-1967 slots and controller unchanged at `#26449594`.
- Juicebox V1: `0x3abF2A4f8452cCC2CF7b4C1e4663147600646f66` (Ethereum) — bytecode keccak256 `0xf28bae363907eeebbed68f7f0b0efc447d495263f180b6ff3e161f81f75be328`, EIP-1967 slots and controller unchanged at `#26449594`.
- Ledgity Yield: `0x482dF7483a52496F4C65AB499966dfcdf4DDFDbc` (Ethereum) — bytecode keccak256 `0xe71d9a8dc2039e8ad5f38dc0f95409ec914ee7cba1c413374a11fba65d7941af`, EIP-1967 slots and controller unchanged at `#26449594`.
- Legion: `0xa0BeB0A8C765482c128a2986c063AF5C3171ff2F` (Ethereum) — bytecode keccak256 `0xf7924ec4706f7b92b773d73078c1f3d26580e4954d342f283018d7a713bb6186`, EIP-1967 slots and controller unchanged at `#26449594`.
- Lista Lending: `0xf820fB4680712CD7263a0D3D024D5b5aEA82Fd70` (Ethereum) — bytecode keccak256 `0xc2294082827c06324e557e6b62fea89d83df6541b0f7926531eda3ce3676ee8c`, EIP-1967 slots and controller unchanged at `#26449594`.
- Metis Bridge: `0x9E32b13ce7f2E80A01932B42553652E053D6ed8e` (Ethereum) — bytecode keccak256 `0x9a833fe40ae2176ba5d50fbb57f2ad20f4189097772a9180c30bb9114526b55c`, EIP-1967 slots and controller unchanged at `#26449594`.
- Metric V1: `0x2a53833cc95548cf52c7b159110e22D3a9018f32` (Ethereum) — bytecode keccak256 `0xe34ec675aad2fc67175956d951b49d182c1289638daa4438fbf80d2ade12291e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Metronome Synth: `0x2Ebd53d035150f328bd754D6DC66B99B0eDB89aa` (Ethereum) — bytecode keccak256 `0xe2a3917cd8f22f7a6d01aedf941b9982b15af8484a9578939a24c93fd7b1fdff`, EIP-1967 slots and controller unchanged at `#26449594`.
- Monolith Market: `0x6D961c9DCF1AD73566822BA4B087892e3839B849` (Ethereum) — bytecode keccak256 `0x67cab37d1c7a97e5bd64e10a5e6283e14f2384165e1ba55ed4f0a51aaf8fcc96`, EIP-1967 slots and controller unchanged at `#26449594`.
- Morph Bridge: `0xDc71366EFFA760804DCFC3EDF87fa2A6f1623304` (Ethereum) — bytecode keccak256 `0x44107d7c70e67e04d35d77455d5755c94d4897196e4ea9a341c1a6d864a6d4d5`, EIP-1967 slots and controller unchanged at `#26449594`.
- MorpheusAI: `0x47176B2Af9885dC6C4575d4eFd63895f7Aaa4790` (Ethereum) — bytecode keccak256 `0x53c0835906d5b2eed9f973e77d7c785956ea1d182c80679951ae09c4cfaa13c1`, EIP-1967 slots and controller unchanged at `#26449594`.
- Multichain: `0x9Fb9a33956351cf4fa040f65A13b835A3C8764E3` (Ethereum) — bytecode keccak256 `0x6a3d203c440e54090e1d8f2dfdb9aa32e0df4b7dd5bfd02d11889f3bd9534492`, EIP-1967 slots and controller unchanged at `#26449594`.
- Native Credit Pool: `0xe3D41d19564922C9952f692C5Dd0563030f5f2EF` (Ethereum) — bytecode keccak256 `0xde357882f2c0a539e8abef1c3c091bf56874c09a141eef9534dd62372e91e93c`, EIP-1967 slots and controller unchanged at `#26449594`.
- NodeDAO: `0xd7C049CD4ba216679ecC04Eb2767cC5E39812121` (Ethereum) — bytecode keccak256 `0x19d55c6b37ed536e4412158686e2df774d0e754dbb580b5f87923c7049d0ac0a`, EIP-1967 slots and controller unchanged at `#26449594`.
- OpenGDP Shared Security: `0x54e44DbB92dBA848ACe27F44c0CB4268981eF1CC` (Ethereum) — bytecode keccak256 `0xde741c264ec7f60e744da6731a699d17530b431a41d2e2ebe7476abc11261e92`, EIP-1967 slots and controller unchanged at `#26449594`.
- Orderly Bridge: `0xABD4C63d2616A5201454168269031355f4764337` (Ethereum) — bytecode keccak256 `0xb3151f817a0cbf213614631b397dd981aa4c3cd2c95a20a5ddf7f9ebdcbbff1c`, EIP-1967 slots and controller unchanged at `#26449594`.
- Paradex Bridge: `0xb32E10022FFBeDfE10bc818a1C7e67D9d87e0fa7` (Ethereum) — bytecode keccak256 `0xee8a105971995661291a9f284262a87abf2381b3cdc93b2c8fbeffe4cd636dd9`, EIP-1967 slots and controller unchanged at `#26449594`.
- Pickle: `0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5` (Ethereum) — bytecode keccak256 `0xbadea4d643e7f84de7258a99ccfade16a9cd5e39c9e4b9f9f35876e469a2fe76`, EIP-1967 slots and controller unchanged at `#26449594`.
- Piku Finance: `0x2E4039E8E31475d65DC00293C366FDBfBBC02DC3` (Ethereum) — bytecode keccak256 `0x1be95a2ec43076d7ce5cd1d0d5261f9bb409e9022e46cc6495ffd1dd7bcf6f0c`, EIP-1967 slots and controller unchanged at `#26449594`.
- Pirex: `0xc55126051B22eBb829D00368f4B12Bde432de5Da` (Ethereum) — bytecode keccak256 `0x574a98b7bd30da9de3edfb7134b4e9dd5b4bbc011bb85a984aa06dae0e350f53`, EIP-1967 slots and controller unchanged at `#26449594`.
- PoolTogether V3: `0x0cEC1A9154Ff802e7934Fc916Ed7Ca50bDE6844e` (Ethereum) — bytecode keccak256 `0x308fc5e8970ed67ffebcc8dafff6333492ace6d3282ba6ef3b1092959a2da25c`, EIP-1967 slots and controller unchanged at `#26449594`.
- Ribbon: `0x6123B0049F904d730dB3C36a31167D9d4121fA6B` (Ethereum) — bytecode keccak256 `0x06f86d51347023f4971c0638f8cb71cbd7b4de3b92a825904205dd2486591d59`, EIP-1967 slots and controller unchanged at `#26449594`.
- Ring Few: `0x7D86394139bf1122E82FDF45Bb4e3b038A4464DD` (Ethereum) — bytecode keccak256 `0x5126b02f7eec0470df7780456cdcee61bc47bf7bf574f213674c66393fd50ae9`, EIP-1967 slots and controller unchanged at `#26449594`.
- Royco V2: `0x7cC6fB28eC7b5e7afC3cB3986141797ffc27253C` (Ethereum) — bytecode keccak256 `0x18f95d772587f01e910a390c7b48d767fbfa7726584405e8277da572b72f9386`, EIP-1967 slots and controller unchanged at `#26449594`.
- SoSoValue Basis: `0x624e2e7fDc8903165F64891672267AB0FCB98831` (Base) — bytecode keccak256 `0x48ac29a5246889375862706cb6369924947b6cf20bf05b904b04324c8536506a`, EIP-1967 slots and controller unchanged at `#59532664`.
- Stafi: `0xef3A930e1FfFFAcd2fc13434aC81bD278B0ecC8d` (Ethereum) — bytecode keccak256 `0xcfb26d9dee1cbb07d16138dc589dff327bc820f608c7d6142789f9b2d94d9922`, EIP-1967 slots and controller unchanged at `#26449594`.
- StakeStone STONE: `0x1D88713b483A8E45cfF0e5CD7c2e15E5Fab4534d` (Ethereum) — bytecode keccak256 `0x7b5f00e12c193572cdda46010ef6bf30df8c68c1974d9aad61c8935ce091d9ca`, EIP-1967 slots and controller unchanged at `#26449594`.
- Steer Protocol: `0xCEBF1A54A9Ce703FC80967760b5A6cbDb4111099` (Ethereum) — bytecode keccak256 `0x1e71c4a5b01c61a4b1a4afa98257a085e472bfc63a362efa77be9a23e714cdc9`, EIP-1967 slots and controller unchanged at `#26449594`.
- SushiSwap V3: `0xc35DADB65012eC5796536bD9864eD8773aBc74C4` (Ethereum) — bytecode keccak256 `0x2908b9ac88489ac1ed7dbc2d6ff5c0832b56dc8f5408e4992b9c7c6a24bb337a`, EIP-1967 slots and controller unchanged at `#26449594`.
- Symbiosis: `0xd38BB40815d2B0c2d2c866e0c72c5728ffC76dd9` (Ethereum) — bytecode keccak256 `0x145131033c93e676112c82aa230328dfc8dd0ac596f59e4ed90ee5045adcdd20`, EIP-1967 slots and controller unchanged at `#26449594`.
- Synapse Cross Chain Bridge: `0x0f2D719407FdBeFF09D87557AbB7232601FD9F29` (Ethereum) — bytecode keccak256 `0x14b9c77780d7daf560bdab14dea33da9fa0bc59eb71b6a1d230de99b6ee0500f`, EIP-1967 slots and controller unchanged at `#26449594`.
- Syntropia: `0x1b2CB79a4564206f53Ba80b4d780F251b4Ae6765` (Ethereum) — bytecode keccak256 `0xdc8d9306a3726daedf8bb0db4da810ed5af2b6ab034e593737a83531a2e7d327`, EIP-1967 slots and controller unchanged at `#26449594`.
- Tangent Finance: `0x214C8A1023B30032a2Eded109146658C6D6F2781` (Ethereum) — bytecode keccak256 `0xf5dab7b6b40557238eaad60b7369bfb50c9329ff47046216a93497aa14cb9771`, EIP-1967 slots and controller unchanged at `#26449594`.
- The Idols: `0x9416bA76e88D873050A06e5956A3EBF10386b863` (Ethereum) — bytecode keccak256 `0x1fc5a38d54c637a235d4a0fd7c57ec4ae5c3c148ec7a038d9715f89a1330cdce`, EIP-1967 slots and controller unchanged at `#26449594`.
- UltraYield Vaults: `0x8ECC0B419dfe3AE197BC96f2a03636b5E1BE91db` (Ethereum) — bytecode keccak256 `0xe428fca70a96823c60ffaa430edc8cc501377a4709bdb3a070d024d616d81ff5`, EIP-1967 slots and controller unchanged at `#26449594`.
- Unslashed: `0xE0e05c43c097B0982Db6c9d626c4eb9e95C3b9ce` (Ethereum) — bytecode keccak256 `0x76b55d62d6e6d762eaa121e1cd4d14100f2d08c36d299b970d06a973dc86fb90`, EIP-1967 slots and controller unchanged at `#26449594`.
- Wildcat Protocol: `0xfEB516d9D946dD487A9346F6fee11f40C6945eE4` (Ethereum) — bytecode keccak256 `0x3622afdfc583101952ff6e608d76f9c897d2767297315962d97f8b3a2cc2df56`, EIP-1967 slots and controller unchanged at `#26449594`.
- XSY: `0xBA515304d8153c4b162dC79f867E152DF9c127eb` (Base) — bytecode keccak256 `0xa403fa29cda49311b973967ea91292c75ab23dd093a8444ae680d9099fac817a`, EIP-1967 slots and controller unchanged at `#59532664`.
- YieldFi: `0x19Ebd191f7A24ECE672ba13A302212b5eF7F35cb` (Ethereum) — bytecode keccak256 `0xcb948150f62f6105c4bab1c9fa409ee4a30c35405b1622d203d440a703ece90e`, EIP-1967 slots and controller unchanged at `#26449594`.
- Yuzu Money: `0x224e90591A2d63fb66E677D0561Ea4A6Ad1F098D` (Ethereum) — bytecode keccak256 `0xb516ec422f5c3709db0ba2ff716d5e06daaec61bf753989303aa3679d5163095`, EIP-1967 slots and controller unchanged at `#26449594`.
- Zora Bridge: `0x1111111111166b7FE7bd91427724B487980aFc69` (Base) — bytecode keccak256 `0xd8511363feac51319c3a08c4ad471f451c5c8d137878cbb0e0472fd976421cd5`, EIP-1967 slots and controller unchanged at `#59532664`.
- ZTLN-P: `0xfEd3D6557Dc46A1B25d0A6F666513Cb33835864B` (Ethereum) — bytecode keccak256 `0xf480c2a32f387d87861f5e505e80169f59eb402333618d51f49d70a724388374`, EIP-1967 slots and controller unchanged at `#26449594`.
- Angle: `0x31429d1856aD1377A8A0079410B297e1a9e214c2` (Ethereum) — bytecode keccak256 `0xb2b4462244cc70f518bca0e36112dc4932b72128f6ceeb7408c0ede78cb94a1d`, EIP-1967 slots and controller unchanged at `#26449594`.
- Angstrom: `0x0000000aa232009084Bd71A5797d089AA4Edfad4` (Ethereum) — bytecode keccak256 `0x528182e66a441545ea3ba1dede4e6063f23acd4ada4036c24b9fa2f254bc4ed1`, EIP-1967 slots and controller unchanged at `#26449594`.
- ApeX Pro: `0x52A8845DF664D76C69d2EEa607CD793565aF42B8` (Ethereum) — bytecode keccak256 `0xe223553d1494126fcfef118f62fdf0d99adeb4845469f967f193d468d79aa5a2`, EIP-1967 slots and controller unchanged at `#26449594`.
- Augur: `0x221657776846890989a759BA2973e427DfF5C9bB` (Ethereum) — bytecode keccak256 `0xa75cc1804fa75f619fa67eee93ddf254251f9690bd78af4a2f59e6bf6a195331`, EIP-1967 slots and controller unchanged at `#26449594`.
- Baseline Protocol: `0x9fDbDE76236998Dc2836FE67A9954eDE456A1D63` (Ethereum) — bytecode keccak256 `0xe3a0b45b4ce46850f120cc127182598eed3e806f86c25755fea84623b4573c8d`, EIP-1967 slots and controller unchanged at `#26449594`.
- BendDAO APE Staking: `0x0d02755a5700414B26FF040e1dE35D337DF56218` (Ethereum) — bytecode keccak256 `0xfc1ea81db44e2de921b958dc92da921a18968ff3f3465bd475fb86dd1af03986`, EIP-1967 slots and controller unchanged at `#26449594`.
- Blast pre-launch Farm: `0x5F6AE08B8AeB7078cf2F96AFb089D7c9f51DA47d` (Ethereum) — bytecode keccak256 `0x82dee1d830a79106921dc73f0ebb4758243a04f29c5346ba4f82f58b81ffef72`, EIP-1967 slots and controller unchanged at `#26449594`.
- BMX Freestyle: `0x6D63921D8203044f6AbaD8F346d3AEa9A2719dDD` (Base) — bytecode keccak256 `0x4d9be648c5bf39973670d9f8b481d5d0b971e6a2db2deccc6b98cde21c5dd83e`, EIP-1967 slots and controller unchanged at `#59532664`.
- Clipper: `0xd8F1460044925d2D5c723C7054cd9247027415B7` (Ethereum) — bytecode keccak256 `0xe059da78dcedae60d32ef3865b8af77702c451736a2d129fe2e3cf8c8d91b6e0`, EIP-1967 slots and controller unchanged at `#26449594`.
- Convergence Fi: `0xB0Afc8363b8F36E0ccE5D54251e20720FfaeaeE7` (Ethereum) — bytecode keccak256 `0xc88eb359bcda37312f65801074d04313c015d1cef388769f2c9245265653e6fa`, EIP-1967 slots and controller unchanged at `#26449594`.
- CRETH2: `0x2ba592F78dB6436527729929AAf6c908497cB200` (Ethereum) — bytecode keccak256 `0x52b508080c903feaa0b873467c07dde6f8a88f6efc88b4dd898636433e0a42f0`, EIP-1967 slots and controller unchanged at `#26449594`.
- deBridge: `0x43dE2d77BF8027e25dBD179B491e8d64f38398aA` (Ethereum) — bytecode keccak256 `0xfc1ea81db44e2de921b958dc92da921a18968ff3f3465bd475fb86dd1af03986`, EIP-1967 slots and controller unchanged at `#26449594`.
- Decentralized Euro: `0x5052D3Cc819f53116641e89b96Ff4cD1EE80B182` (Ethereum) — bytecode keccak256 `0xbfc14b0f709d49dacaf7c3262532ff2f700b716306c54d340a4196673322847d`, EIP-1967 slots and controller unchanged at `#26449594`.
- DeFIL: `0x09ce2B746C32528B7d864A1e3979Bd97d2f095AB` (Ethereum) — bytecode keccak256 `0x3b6ce2514862cb6b6d5d37979a693a0d4f7252ce4e5f4f132441aaa1a9c30ad4`, EIP-1967 slots and controller unchanged at `#26449594`.
- DELV Yield: `0x62F161BF3692E4015BefB05A03a94A40f520d1c0` (Ethereum) — bytecode keccak256 `0xf9a3a5f11360d59f975ee3b3a133cea72978503c3940d56d12f7abdb16d42d52`, EIP-1967 slots and controller unchanged at `#26449594`.
- DerivaDEX: `0x3A880652F47bFaa771908C07Dd8673A787dAEd3A` (Ethereum) — bytecode keccak256 `0x90459b94bf726acfb040ffb9f897868235160693e9bc9f2e2aa70d67f7bd6ca2`, EIP-1967 slots and controller unchanged at `#26449594`.
- DexFi Aggregator: `0x4C1a8a04577286Ce58d0723b1a90160F380E550A` (Ethereum) — bytecode keccak256 `0xed42fb03822a5d6d75695946a6eb1eb92cda4bc668f61635fdf710d5de8e83ef`, EIP-1967 slots and controller unchanged at `#26449594`.
- DxSale: `0xF063fE1aB7a291c5d06a86e14730b00BF24cB589` (Ethereum) — bytecode keccak256 `0x08d525afaf352be3b9eeb0eea7d588fcb7ea55e5e52829d107c97ded4fcd32e6`, EIP-1967 slots and controller unchanged at `#26449594`.
- Ekubo: `0xe0e0e08A6A4b9Dc7bD67BCB7aadE5cF48157d444` (Ethereum) — bytecode keccak256 `0xf3d28accb94c26334e15376aa2b13b0e5bb57b69b207e08f4538ae9884d5633b`, EIP-1967 slots and controller unchanged at `#26449594`.
- ElfomoFi: `0x64f8bE47A011DF0fAB47319d5De258D18E93f4ef` (Base) — bytecode keccak256 `0x3911795ad7e9d471583ebe7aeb1021703890f7ca55a10b8ee8ca91e55ba70565`, EIP-1967 slots and controller unchanged at `#59532664`.
- Fake World Assets V2: `0xa0Df17B5aC76ABaBA36E1450E2cbCd18A620C845` (Ethereum) — bytecode keccak256 `0xd07b0280e4e25689956cff42290d843739714308e6fbe693017cede05c2c52fd`, EIP-1967 slots and controller unchanged at `#26449594`.
- Flexa: `0xfF20817765cB7f73d4bde2e66e067E58D11095C2` (Ethereum) — bytecode keccak256 `0xa0cfa14c1f8ef49585b024e29601a34bbeb675337a94833b2df167782cebbdf5`, EIP-1967 slots and controller unchanged at `#26449594`.
- FlokiFi Locker: `0xcf0C122c6b73ff809C693DB761e7BaeBe62b6a2E` (Ethereum) — bytecode keccak256 `0x62f6a27beef672562e73fb0f3dcc4efb0d16b16cf4daeddb5c9cd8e17f58d6f8`, EIP-1967 slots and controller unchanged at `#26449594`.
- friend.tech V1: `0x0bD4887f7D41B35CD75DFF9FfeE2856106f86670` (Base) — bytecode keccak256 `0x358aa3e7ee950f58863c601550d37477d36b1dd76c1ce15342ac6649acf9caa8`, EIP-1967 slots and controller unchanged at `#59532664`.
- Gamma: `0x6BeA7CFEF803D1e3d5f7C0103f7ded065644e197` (Ethereum) — bytecode keccak256 `0x35be488840b51a9788e28175818703d2764395e5e22fd5ebfda92d575b2020aa`, EIP-1967 slots and controller unchanged at `#26449594`.
- GLIF: `0xAeD7C2eD7Bb84396AfCB55fF72c8F8E87FFb68f3` (Base) — bytecode keccak256 `0x749f3b692400fa750c12cd525331ae1eda236ca25ac3033b739b8ff04abf3c1e`, EIP-1967 slots and controller unchanged at `#59532664`.
- Gro: `0x3Ec8798B81485A254928B70CDA1cf0A2BB0B74D7` (Ethereum) — bytecode keccak256 `0x3ab25059e82d964ea1bcb4653362e7f690d2a3256437df181fe0e7f62f0b0bb2`, EIP-1967 slots and controller unchanged at `#26449594`.
- Hashport: `0x367e59b559283C8506207d75B0c5D8C66c4Cd4B7` (Ethereum) — bytecode keccak256 `0xeeb7d0101f0146330d8919b003a624ee842dbacac36f4e788d2b272f48d8582d`, EIP-1967 slots and controller unchanged at `#26449594`.
- Hegic: `0x584bC13c7D411c00c01A62e8019472dE68768430` (Ethereum) — bytecode keccak256 `0xdec18c0951427319cc61da2d7548a2a4f32d2ad07de25868f528e2753602bb61`, EIP-1967 slots and controller unchanged at `#26449594`.
- ICHI: `0x111111517e4929D3dcbdfa7CCe55d30d4B6BC4d6` (Ethereum) — bytecode keccak256 `0x33c88004b04cc3a91c6c2907e8399ce7ff2acd319c1476c49e299026878e98ad`, EIP-1967 slots and controller unchanged at `#26449594`.
- Idle: `0x875773784Af8135eA0ef43b5a374AaD105c5D39e` (Ethereum) — bytecode keccak256 `0xbc16c4da1501fb5bac4256c7478866dfb011e3aa1c11bf04090c5637cbdcb1e0`, EIP-1967 slots and controller unchanged at `#26449594`.
- Interest Protocol: `0x2A54bA2964C8Cd459Dc568853F79813a60761B58` (Ethereum) — bytecode keccak256 `0x6273eddb91b574c664e91f6e38caf04527f5172f452b419a25f858c6a6f16265`, EIP-1967 slots and controller unchanged at `#26449594`.
- Kine Finance: `0xbB7D94a423f4978545ecf73161f0678e8AfD1a92` (Ethereum) — bytecode keccak256 `0x1240a7f0370dbc9f26bbc60420e4e1034b2008607b7fb39f0948d4fa31870d95`, EIP-1967 slots and controller unchanged at `#26449594`.
- King Protocol: `0x8F08B70456eb22f6109F57b8fafE862ED28E6040` (Ethereum) — bytecode keccak256 `0xf8c4135b5cd64765ef0eab5ea7559c47552279ee03eca8241f981cc597f5c777`, EIP-1967 slots and controller unchanged at `#26449594`.
- LandX Finance: `0x08A1C30BBB26425c1031ee9E43FA0B9960742539` (Ethereum) — bytecode keccak256 `0xb612e6bd581e8e2b7889e1ce264314531cea3c5503db7e8520c0f550d6ce4f96`, EIP-1967 slots and controller unchanged at `#26449594`.
- Lazy: `0xd53B68fB4eb907c3c1E348CD7d7bEDE34f763805` (Ethereum) — bytecode keccak256 `0x1fc427a9bc54ebdc7a32d32b519126d28cd2ef37ce526cca3a51e2ca9cee7150`, EIP-1967 slots and controller unchanged at `#26449594`.
- LendFlare: `0xB620Be8a1949AA9532e6a3510132864EF9Bc3F82` (Ethereum) — bytecode keccak256 `0xf62bd5d649a541bbef0e8aecef588c949b55a8103eccdb0c8bcd07fdf803dd69`, EIP-1967 slots and controller unchanged at `#26449594`.
- LUSD ChickenBonds: `0xB9D7DdDca9a4AC480991865EfEf82E01273F79C3` (Ethereum) — bytecode keccak256 `0x6640959990cc7cea35e6eb879bdbc5b131a512820345b4adc887c97c6d6396d9`, EIP-1967 slots and controller unchanged at `#26449594`.
- MortgageFi: `0x1bE87D273d47C3832Ab7853812E9A995A4DE9EEA` (Base) — bytecode keccak256 `0x185cf047b846a3513a3de1ebeba7c30fa0ccbe85f838a616ebccd8363e3b5973`, EIP-1967 slots and controller unchanged at `#59532664`.
- Nami: `0x0100000002935Dce071f4AFA607b961575672b4C` (Ethereum) — bytecode keccak256 `0x96259673a3d3296a129cce355d4b938bf40d7162e379c966116a22e224828023`, EIP-1967 slots and controller unchanged at `#26449594`.
- NFTX: `0x87d73E916D7057945c9BcD8cdd94e42A6F47f776` (Ethereum) — bytecode keccak256 `0x2dda0f3a6bee3e5768e41adb77021f8f5653897a1c65a5f106265b17fa2c299b`, EIP-1967 slots and controller unchanged at `#26449594`.
- Nucleus: `0x52E4d8989fa8b3E1C06696e7b16DEf5d7707A0d1` (Ethereum) — bytecode keccak256 `0xb2e2580f6bee3b141fb4c2cfca77558a0ac1bf0c77dc0ec41c2d6e85f18d7ab7`, EIP-1967 slots and controller unchanged at `#26449594`.
- Outcome Finance: `0x0b8de441B26E36f461b2748919ed71f50593A67b` (Ethereum) — bytecode keccak256 `0xa10d4eb25d8cec9207b66506981e4af2f9900f06311949d2fa7beed6f8a198f9`, EIP-1967 slots and controller unchanged at `#26449594`.
- Overtime: `0x90cE5720c17587D28E4Af120ae2d313B3BAD1722` (Ethereum) — bytecode keccak256 `0x2a2b42ae5730efe6b72757400473ea6427d7d8640d35cd3c04fbdf2f2d6d7925`, EIP-1967 slots and controller unchanged at `#26449594`.
- Parallel Protocol V3: `0x6c0aeceeDc55c9d55d8B99216a670D85330941c3` (Ethereum) — bytecode keccak256 `0xe9660e0bc6bc7ea780091375b4d40a45d4afa77164cd837d3bc73eb237b40b6b`, EIP-1967 slots and controller unchanged at `#26449594`.
- Peapods Finance: `0x02f92800F57BCD74066F5709F1Daa1A4302Df875` (Ethereum) — bytecode keccak256 `0xc2df238df0d1f82b78333acfffa06600f20d55e6f2fa5b2ac05ce38526bd642c`, EIP-1967 slots and controller unchanged at `#26449594`.
- Punks Terminal: `0x000000000000A6fA31F5fC51c1640aAc76866750` (Ethereum) — bytecode keccak256 `0x5b8a9e982541c73da95a997139f197f575910a6037f34cb1e04d8567c019faf1`, EIP-1967 slots and controller unchanged at `#26449594`.
- Quickswap V4: `0xC5396866754799B9720125B104AE01d935Ab9C7b` (Base) — bytecode keccak256 `0x7822b724506fdf3f88058e04b74d0c754a8e09f5db1964fdc2ceb9977967b153`, EIP-1967 slots and controller unchanged at `#59532664`.
- Reflexer: `0x6243d8CEA23066d098a15582d81a598b4e8391F4` (Ethereum) — bytecode keccak256 `0x91b7369444e24b10e4d84904b059edc29aab786ca7c8061b5a501321c4a3cb5f`, EIP-1967 slots and controller unchanged at `#26449594`.
- Saffron Vaults: `0xb753428af26E81097e7fD17f40c88aaA3E04902c` (Ethereum) — bytecode keccak256 `0xd9f71ccdd211bba48b76ead02c0de837b0a34f07e693e367a32eff3860357a36`, EIP-1967 slots and controller unchanged at `#26449594`.
- SATO: `0x0000f07d2B5F1Ddf3244b8780F972f306EFd2888` (Ethereum) — bytecode keccak256 `0x0cb886792429db1b1f330dedc575160e709e659159b0b9477858b3965102cf42`, EIP-1967 slots and controller unchanged at `#26449594`.
- SMARDEX USDN: `0x656cB8C6d154Aad29d8771384089be5B5141f01a` (Ethereum) — bytecode keccak256 `0xfd1a8f7693ff598e9b2e993e7d30c57c12d773b948753d9edfd6761e8daeb4de`, EIP-1967 slots and controller unchanged at `#26449594`.
- SOFA.org: `0x57B96D4aF698605563A4653D882635da59Bf11AF` (Ethereum) — bytecode keccak256 `0x88056442963f4b4ba95bbdf2e92e6f4e89bfb34f82171e8837ecd7d4ffd1cc78`, EIP-1967 slots and controller unchanged at `#26449594`.
- Sommelier: `0xa670d7237398238DE01267472C6f13e5B8010FD1` (Ethereum) — bytecode keccak256 `0xe32339c16126933800abbc98e317903e5d17d0c0940813c63d51458593ef1d36`, EIP-1967 slots and controller unchanged at `#26449594`.
- Sport.fun: `0x16EE7ecAc70d1028E7712751E2Ee6BA808a7dd92` (Base) — bytecode keccak256 `0xe45965360fef796d68818c710054832bb0b9e09c72dc7783f6ebb633197bcddf`, EIP-1967 slots and controller unchanged at `#59532664`.
- StableHodl: `0x109D3042a3c682F94107b3818e93b3aDE2A47544` (Ethereum) — bytecode keccak256 `0xee8a105971995661291a9f284262a87abf2381b3cdc93b2c8fbeffe4cd636dd9`, EIP-1967 slots and controller unchanged at `#26449594`.
- Supernova CL: `0x44B7fBd4D87149eFa5347c451E74B9FD18E89c55` (Ethereum) — bytecode keccak256 `0x502e5730b9eb2b3afa6c7b8453c61c842dccac09c1a4cf4147ebb151e5184f3e`, EIP-1967 slots and controller unchanged at `#26449594`.
- SynFutures V3: `0x6e15A54B5EcAc17e58daDedDbe8506a7560252F9` (Ethereum) — bytecode keccak256 `0xb26a9e2b05c6cfb4165a2c2ea3fc8490f4b8dfbeb7e67cb1cc05687b7ed293de`, EIP-1967 slots and controller unchanged at `#26449594`.
- Taiko Bridge: `0x10dea67478c5F8C5E2D90e5E9B26dBe60c54d800` (Ethereum) — bytecode keccak256 `0x26e751b9fd68f5207c6d2b35f2871bc22c1b05e9d20368c10257dc04ca67f46e`, EIP-1967 slots and controller unchanged at `#26449594`.
- TokenWorks: `0xA1a196b5BE89Be04a2c1dc71643689CE013c22e5` (Ethereum) — bytecode keccak256 `0xdbe822093f1c9e3d148657d5122e03958449aea91b271863b5cd42c5be206a86`, EIP-1967 slots and controller unchanged at `#26449594`.
- Trueo: `0x21CFCFc3d8F98fC728f48341D10Ad8283F6EB7AB` (Base) — bytecode keccak256 `0xfe3d734a191abf6ae6a0b7f0519e4fda8631b2f47bdb1b3561433fdf2c862feb`, EIP-1967 slots and controller unchanged at `#59532664`.
- Unitus: `0x3B6564b5DA73A41d3A66e6558a98FD0e9E1e77ad` (Ethereum) — bytecode keccak256 `0xaf9c9da08abecebd75f6ed4d1aa7e423b553ce9ca8d2fd83c025e684b72f6534`, EIP-1967 slots and controller unchanged at `#26449594`.
- Wan Bridge: `0xfCeAAaEB8D564a9D0e71Ef36f027b9D162bC334e` (Ethereum) — bytecode keccak256 `0xd0cf0742bd64c1e960f924480430b6614def86d82463b5cb878836ff12274abe`, EIP-1967 slots and controller unchanged at `#26449594`.
- WOOFi Earn: `0x4691937a7508860F876c9c0a2a617E7d9E945D4B` (Ethereum) — bytecode keccak256 `0xee7b6a4b8c8f92fbca7423f575329f7935dd6c6e3b744490b702a238a41dd4e0`, EIP-1967 slots and controller unchanged at `#26449594`.
