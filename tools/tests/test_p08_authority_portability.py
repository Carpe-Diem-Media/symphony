"""Unexecuted R1a regression source; no fixture or authentication authority.

The full suite remains behind the refusal-only launcher. These definitions
must not be run until a separately authorized source change implements an
independently accepted authentication mechanism and R1b releases execution.
"""

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

import p08_qualification_runner as policy

# A direct unittest import receives no admission. This call currently refuses
# before opening an audit log. Importing this module is prohibited under R1a.
policy.install_write_audit()

# Public baseline metadata only. No private fixture bytes or workstation paths.
# These are the 395 accepted-main leaves, not the 407-entry C0 fixture.
BASE_RECORDS = (
    ('.codex/skills/README.md', '100644', 1047, '1a3b62a239ca06290da2885fce012537eaed16a5', '956fff8ef65aefe3d89dad31289e0077799b2fa3df302a9e1ed08bbc0a71ca0a'),
    ('.codex/skills/commit/SKILL.md', '100644', 2758, 'f983fd36aca91680b33835685881d1a7ab61150a', '9ae4d43c64c9bed15e8b1e83183151bf8de23bf7fa5107ace8687f865c0aeefc'),
    ('.codex/skills/debug/SKILL.md', '100644', 4574, 'af2206ab64084da8f183fe615cbc2662314764d3', 'afdfa21e6bf915a6eb7a621bd4cf2c1b87b6ba90af32dd2a3064572718dd0924'),
    ('.codex/skills/land/SKILL.md', '100644', 2171, 'ce69deb7063dec2cc72093f56458d4d2da1fec14', '14af9393c08c6653963633656c9f06d372855de6268b8e5957c05c4a0acf7af4'),
    ('.codex/skills/land/land_watch.py', '100755', 19845, '9247aee4a52c70eaefe6fbb833434e00f1419719', 'f7a228af8309673594ee7d1a0ef8c5b7fd0e6abd879b0be3428e8b1126e3f6f0'),
    ('.codex/skills/linear/SKILL.md', '100644', 6666, '2f66ac8224a73ff6ec8325bdda3207ff7e32d3b5', '6254b1ed02fe672140e550b3792430f5c981ef5d0adc3ca03f3d775fb410b02d'),
    ('.codex/skills/pull/SKILL.md', '100644', 5015, 'fba76ad44fc864a599d76042d105f4f0283d3e5d', 'e8cb6f4dd40eb0baaad77a1e4a3791132f2f2032e89d3a2e57c52d7d49ae6a95'),
    ('.codex/skills/push/SKILL.md', '100644', 4708, '39f1cdc78c6241f0d0f4b29f912f232f43b1fda7', 'e8e7a6b07e819e5b271af1b15399bb5eb3142c5ba669808a6b5d3e0979ad0e74'),
    ('.codex/skills/release/SKILL.md', '100644', 1347, '669462534c740015ca45dbe54dc61c3d2a05d081', '4dd336c6ee3e41ad730a32f14af9e830d138704d1018637f96323af44644e9a1'),
    ('.codex/worktree_init.sh', '100755', 345, 'ee39abf02bd1f32d55a519d233fa7638a73e4d0a', 'cce49e067cec63a2bee90abc2b4a436d2ef8a05bb7c42305fdd3cf64aae30733'),
    ('.github/actions/setup-linux-elixir/action.yml', '100644', 2058, '9258b73487bc0655e2627c3ef32c44a21e0f8062', '7b6e0e7fb05b177d8f0522dacd131bca1e6befe07f52ca32d83f3b3803cc4411'),
    ('.github/media/elixir-screenshot.png', '100644', 115378, '850a5e712d4092fc761652653a8a6f6613209373', 'b023cb2e25ba144be6b64f1e522b06221a6297e214ec5419db13511331a2981d'),
    ('.github/media/symphony-demo-poster.jpg', '100644', 90558, '7dd6be2eabfad7fede4e132fc16618c8e5824c1e', '808d8367a378ea439bc53395e4e9fa703ef86fcd187e23af5c4bd419dfb1fb2b'),
    ('.github/media/symphony-demo.mp4', '100644', 30446771, '32b1f857f45eb901905ea24355b599fb417f53c5', '0baa5f6276ea9a790d8072e690c547ed02afb3f95312266d3f27a923d4f58ec1'),
    ('.github/pull_request_template.md', '100644', 537, '0f1a8bb7536f080d4ba518b7b6b7acdca0e6d4a0', '3eea4ddb45b9188a691273ef1aca5c1bb59924e06647f73cfc793f550780eb9f'),
    ('.github/workflows/b1-control.yml', '100644', 4127, '79382e2420fa9cc66d38c1ccffdc1258bd28e2c6', 'dc23550ef1fbc40540fcd3e437efc0f91955ab900d4819e8807c66d6efa43270'),
    ('.github/workflows/burrito-release.yml', '100644', 4209, 'ed8034490b9f5738a6200636061c7dff05643465', '8203a1a0cd2a16d063afd4334f18012bf7547eff0283cdf0d767796768e21a3c'),
    ('.github/workflows/make-all.yml', '100644', 12112, 'b1df739125623b0ad2c5c975a61ea82cd7855804', '2b3c77f99e19c0ce6d66c26b127542e85e35c84921de5d1563a10cd5e15c7c62'),
    ('.github/workflows/pr-description-lint.yml', '100644', 987, '5b7743be8f97125b1544ec1b9e5c747c5549ba9b', 'd1e8dd4c7a25c40b45270147d3509fc99122484bce4e2841cc2d208f78a5854a'),
    ('LICENSE', '100644', 11357, '261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64', 'c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4'),
    ('NOTICE', '100644', 551, '4face8c22b6bfaa19bbc37ad10294a916fe8e7da', '38c76eb8701e52953f63154a77b407667a6ee34c3a2a8785c8f8b2cd5494d09d'),
    ('README.md', '100644', 3988, 'cda696aecb515afec261217159de5fcf5a097f81', 'ca02b24550a558f954466074f2e2344280ccb0f2bd5c37cc83fbc2b5d0d6a29a'),
    ('SPEC.md', '100644', 93216, '08ec1b1208bc212702183b34b9dda1362157e0bb', '6b7ea6a48412221bc43f0cd4ac92bcf6c286eb34e9c920b75253b14c06ee4371'),
    ('docs/AGENT_ROUTER_REMEDIATION_MATRIX.md', '100644', 27903, '1ad730b4d2209ebe851e60c56c4821ccb82eac4f', 'eec19bdcc35f7fbdd9fad045d9b48c050bdfc2510aa6e022527ae19173253277'),
    ('docs/SYMPHONY_SKILLS_ADOPTION_AND_ROUTING_MATRIX_v1.0.2.md', '100644', 57066, '9615ab8e2ac8811faf7c98bc3abe5e760fdcb80d', 'f82ef79ef070959850693db7323990f78f903c550804f0887d3debd9043f1773'),
    ('docs/SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md', '100644', 126911, '5ef99584283850482df822e8935428477353797c', '65035de28e939f746be1db1e01b1e6966f64a3fc2da101400553672289ead1d7'),
    ('docs/superpowers/README.md', '100644', 744, '6a3dea853e86155589763a1645fdc6b536da3b2d', 'e9d006dbbea98b7e82258ecf14875869cf614b9a728b25c15f25c00370972377'),
    ('docs/superpowers/plans/2026-09-13-symphony-agent-router-dependency-orchestration.md', '100644', 14592, '821c0db078db73d38a308438978e02c90a52a5ad', '849ef2c527c393877a155044b4cccfd5775ac985dbde376e68ac28f225ab4832'),
    ('docs/superpowers/plans/2026-09-14-agent-router-remediation.md', '100644', 17900, '5738274d6b8f660f09e943ae83294ced84603b0f', 'acf62895d7bdc5988c4834982d75a506094209f301f8f9a667a76b5dc89aeb2f'),
    ('docs/superpowers/plans/2026-09-30-completion-proof-trust-boundary.md', '100644', 6830, '04032844325853ae81c451866f5be9fad288041a', '228abd979793861ed159e3d4ddd74010071d7c36b5a22d6b17032c4d188ce97f'),
    ('docs/superpowers/plans/2026-10-09-agent-runner-isolation-baseline-execution-ledger.md', '100644', 9083, '49a94a783ab8e21166c9a692156b87044865ab23', 'b2dde04de698f44e24970eab9bd4f61a01abbef71e54f2a0ae30a97a5742dd19'),
    ('docs/superpowers/plans/2026-10-17-h090-structural-hardening.md', '100644', 70354, '0e7aef5e85a4607a58eb6c815e3d7956196e5907', 'ff912cddd4f8eb0c98b23d7a06db69ec22bd6d75c261cccc054d8fe83c54d6e3'),
    ('docs/superpowers/plans/2026-10-18-h120a-governance-pre-gate.md', '100644', 76551, '5c5229da33831342024a5916c50e6523ce8cd7a7', '52ad6a7947f2ad4a31d5b332f44d68d863a0d03feb368eada7f6a2ac478db84a'),
    ('docs/superpowers/plans/2026-10-18-post-h120a-pre-h100-governance-materialization.md', '100644', 38525, '6109cc32c7463e597b894a25bc8ffa2f1394f1f1', '3586c5bec3111390fd09fc8f687dcbac8ced9eebfdaa4b80119b29c81d2f2c58'),
    ('docs/superpowers/plans/2026-10-19-h100-p0-submission-correlation-remediation.md', '100644', 13123, 'c7eea726e33941d5151ec2b91be7210058e740c5', 'f5eaa853328fc53887f4bc44c8aa1c2c5df56df9c081ef82c420a69511909741'),
    ('docs/superpowers/plans/2026-10-22-a3-plane-terminal-cursor-compatibility.md', '100755', 14413, '4dca235d73a29897ed88a3b384d95d414e8dc4c1', '226d7a3809033e5f6d632acd9a08fb3828762654cfa37e0d8a6d1116feea0f81'),
    ('docs/superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md', '100644', 231932, 'bdb2840e5ea4ca8c8912d6cada3287078bbb3c72', 'a1d5cdba65c19a09e86ed814a595e8bbae0c9dcfc97afe021ab67826db09ff68'),
    ('docs/superpowers/plans/2026-11-04-p08-host-evidence-implementation-plan.md', '100644', 68919, '83774a4185aab4908155abdc60a30a7081b76fbc', 'ac6debd05e32572fbae567a7300d643110007a6729b1adf975ed8d66985d9b94'),
    ('docs/superpowers/specs/2026-09-30-completion-proof-trust-design.md', '100644', 3130, 'ad235fab6dc17d114aef5d9db07f3d76be9dc077', '7df799761dfba603a2e6295b9f61b246c1f7a387f1c6accdad39dd772472b261'),
    ('docs/symphony-agent-router-dependency-proof.md', '100644', 8578, 'dedb6c6b27f8c512fa4713ce60038dd86f7b97ad', '929ca53d8cafa9ed8235a42d5b0fe4c8625d72c469bca4290d413d23fbbdacc2'),
    ('docs/symphony-hardening-playbook-v3/H-010_CRITICAL_TEST_AUTHORITY_EVIDENCE.md', '100644', 10916, '931bf13f96f3ee7899e803ed03c2b03e5f9a7e6f', 'caeac745a7aeb3a85b2d91e3240d27d5bb2875c76cb5b6878076bc4b6b0e4d1c'),
    ('docs/symphony-hardening-playbook-v3/H-020_PROVIDER_CAPABILITY_CONTRACT_EVIDENCE.md', '100644', 7099, 'f7750130b0a95cedce07ed2522cd5fdc7478475c', 'cf64d72071d11e69aea74423901029326cc5601d882d0ef882864b2fd933fc1d'),
    ('docs/symphony-hardening-playbook-v3/H-030_DURABLE_ATTEMPT_LINEAGE_EVIDENCE.md', '100644', 11819, '92605628806ddd8fcb4404d466a43d8e68bdb868', '09d1824171e0d3a85373ebd7f5460ae171e135e57aa8da39e13c4e81ef424e39'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_05_R2_MASTER_GATE_PLAN_ACCEPTANCE_2026-11-06.md', '100644', 9939, 'd2b166f40774521d1a1f3d4370cd634237e71a52', 'a60a8ae12e2ee79e6f57ac65d130c0b00173fd90f1292699043fbeba1ea8f26d'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_05_R2_SYNTHETIC_QUALIFICATION_PLAN_2026-11-06.md', '100644', 40903, '1fd0af3e23287bab8939876589abc064c5655b45', 'ae823f8f23f476fed092c0b120b8cea2e68bd8ef14053ac66eca89670cfcab4a'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_DRAFT_AUTHORIZATION.md', '100644', 7405, '7bcac52e873ff1f15f4814193106de09a3287485', 'bd4835f318ccae03c89e29db1e7fdff78cced4e615da4510aa9748662ad38b59'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_EVIDENCE_INTERIM_REVIEW.md', '100644', 4829, '0293121b1654678cc4b56d43e94e9f6d8ab732ff', '35fff9ef86b030e71ddad3af66ea07df239bd4be58c7f19d72f7444777b3d70f'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_F01_F04_CORRECTION_AUTHORIZATION.md', '100644', 1973, 'de5b365f01cd3c559c93170116e674b004533f52', '7bdf5284eaca68e34e31ea62d961ebe176378b0ebdce3a6fb4c19ba7fca2b873'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_F01_F04_REVIEW_RECEIVED.md', '100644', 7480, '3e64982383ab63016d191c21e32837d0f1c9e0c9', '4a4a9c04dd24fef4c19748376c5538e29bc297abc2dc5d2edf535ef6cf2e50a3'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_N01_N03_CORRECTION_AUTHORIZATION.md', '100644', 4305, 'f3578ff784ba694a883c1f179472640868ddfaf7', '3043897c8b8be28002b4ea13b5062148ddd95c4096d2fa5ff72e0a6e9c71fec9'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_N01_N03_REVIEW_RECEIVED.md', '100644', 23029, 'ea80eb3108f051c57cbed442b8601d9615d2cf06', '57d163a5f5d4bac9f414acccf137c45857f94323872086562c0e95c37d4d1e9f'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_R01_R03_CORRECTION_AUTHORIZATION.md', '100644', 3344, '6f42e4fdbb08a25a1a08be3926bf7971a77b7a2e', 'd6c141d8d88c78f9448cbfef6c616083a0f3901fc4bff3808ab31d817e0a4916'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_R01_R03_FINDINGS_RECEIVED.md', '100644', 5176, 'cda259fd8a5eec19d756e9f719d8db333aede521', '3efaf99632445912a5ed7d09fcdcff94063ce9633ebae7f992968b4aa33fb335'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B0_STATIC_SOURCE_FINAL_REVIEW.md', '100644', 5250, '5511cc44b57de4c46d5d53e4ba058040fe78ecc3', '16a3052dd8b9d31b72e3920a8885a73e4ce66b6f5a445dc62404ec2cf2c3a8c3'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_CONTROL_IMPLEMENTATION_R0.md', '100644', 23699, 'b559fddff56fcc03c30a69dddd3ce475310a6f10', 'c62dfe70407019c8367eba45056e0abd5a10a0d3ffa6fd166d7abdc277cf53b9'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_EVIDENCE_INDEX.md', '100644', 41907, '4d75f7fa17148433551e6be06924f50748627dc2', '4fe371abd4ddc5903ff6576701529c379bb25dec24fdf38cd368380f80bcc794'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R0_MASTER_REVIEW.md', '100644', 8694, '56319f273a88a1ac491aef265644b2571590542f', 'c0ce3815daf7930e79aa1e616d26d0413c82a9da140c9c72941608afb7711c1c'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R0_ORIGINAL.md', '100644', 25416, '144585d7a950d407308e68d507e35617824a55a6', 'eb2d1597227814c4a29392a3843474bc0e83e1cea0255c60f5814fb73daa638e'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R1_APPROVAL_REQUEST.md', '100644', 272, 'e795c81a2d6b2a69be605cf7bd9b5cbc3ddaab60', '99f3c3cecd121943fc42770a1cf9f619fbc664197e5f1b1f2d6277a58e2128d8'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R1_CORRECTION_PROPOSAL.md', '100644', 6283, 'f37b49ba0cd39349644290f56e02f01350b17d5e', '68cca3cfb794edcb7b5fd0b6440d6df6b91b8d21d7ee45ef6235fa9f5646809b'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R1_HUMAN_APPROVAL.txt', '100644', 19, '23f7f35413783b45852cc2a9266fe534cc6f670c', 'abc1eddf60e25e10e596ee21974fa00c62019bc57a46510e69688a83d336fa80'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R1_MASTER_REVIEW.md', '100644', 6633, 'b2e56b8bc642d1b1e530d3218a231fe356046140', 'ca3375e994123239bdb575708d76a4132defad591710ca4bdf6d5e3ea43fbe89'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R1_ORIGINAL.md', '100644', 42557, '415c99b827b426872dd36c8468f58350db459854', '1a8fe95ee1b6e2b90c36d7a0fbe91243fe61f4641c90f7b48615222cd52fb57e'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R1_PRE_REVIEW_RECEIVED.md', '100644', 6162, '300a09021f64be60a99b1e05b022fa723541859f', '884bedd88b21060ef85f8ddfdab1c61156c218eee0743bd634e1e08e4ae2051b'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R2_APPROVAL_REQUEST.md', '100644', 272, '616369805c703d7b53b160f38a0f07246191c40d', '44df8d26841028acd4bd0f52e8bb68be8ded69e9c7babc446538b9ac284d69d0'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R2_CORRECTION_PROPOSAL.md', '100644', 4297, '87bb99893e1133ef3ef79458586d27a71b1e3dc2', '7b666e5cc1238334227b4864c23177b91a5c4f1e90ad34f3168ca677d1c9653c'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R2_HUMAN_APPROVAL.txt', '100644', 188, '7af553bbdb9de703b3dea7f5511a7415c306d133', 'b78406a9052b3445b29c55efeae61bd03cf2dbbc3b907178720bbac7b5568d4a'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_R2_ORIGINAL.md', '100644', 51162, '63ecf479994fb2f08d53a82a2fcb99fcf6c491b6', 'e17af86eba90842163253dde581f1e7c0470acc8e158b4b0f726fbe09e1303ee'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_EVIDENCE_PRESERVATION_AUTHORIZATION.md', '100644', 13491, '9b45ade363c35816c094dcaf1069915c0ddd8481', 'b82582ba31f4e7739abbeac7bfe56dbdf03ff4fd7381c1cae1e9362491b0c8e1'),
    ('docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_R2_BOUNDARY_ADJUDICATION_RECEIVED.md', '100644', 25171, '0e32cb2259e87ebe1533dee6dc7c6c8c6a2f5685', 'e4a6058af4500f08f5f8418b38a20b703888477145dec06d9f15ee8ffe70e4ad'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_HERDR_QUALIFICATION_REFINEMENT.json', '100644', 26495, 'ebe3c1acca960ccb6a1f71bed02c9fee5804df16', 'b230efeaf840eef2bc4af90ed2e9be2afebc875d58f348dd17f6eaa632991b78'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_HERDR_QUALIFICATION_REFINEMENT_2026-11-03.md', '100644', 23993, '1f33baa3a940b7c7731e677303b8987d43366462', '3beb42d4cd42b1e4ed233d107a5859d8423fbc7614325b80ec6aa7c600cc8300'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_ACCEPTANCE_2026-11-02.md', '100644', 2378, 'f0be29391fd584f665da816079536c0bbb33bcd2', '0318dbd3c76b8c3407fe02a9c62e9013129477c853a9f677ffaf4f9009b7cd57'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_GOVERNANCE_RECONCILIATION_2026-11-02.md', '100644', 4434, '437175de2dcc491185a3775b276608fa9a16405a', 'a077d640650459a4881b1e77c9dc8fb35b3cf72f8a30be04c80dfa73984e8280'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json', '100644', 683322, '6cf92dbad8507d4e6c7553392b163fcac02b897d', 'a651b1574ec0a186f6b4cd9548787cf9b67009f6692268ce5a8d0669d9d0636a'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_PROJECTION.json', '100644', 2643, '1d4bfac04d7533049f6a07b0b6604680f9d9ded0', '190199804a6ce86e2bd574dda7f61f32cdeac2cfe6be5cde85dcde9bb93863bc'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_P08_HOST_EVIDENCE_SPEC.md', '100644', 226832, 'd4185d0f5aa4eacee3f7133db3a84648adffc160', 'b510eb0c8459c126d3b310d3d5c7225f9d8dda4559a16ff6704842a6fb69568d'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_SCANNER_GOVERNANCE_ADDENDUM_2026-11-03.md', '100644', 5619, '1371606b208da8df4c8bcc69387bb86153fec7a2', '8b3aade539270bed6c7a4647ff00e5aaf3bcb79a08cc0e5cc3a45a9eb45be34b'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_SCANNER_GOVERNANCE_PROJECTION.json', '100644', 7784, 'd754155b5a1391a885d5c6ade6bd5066a969ac10', '675b84627a5dade8f1c5689c5764572bb156652484f42b41f4f56b29f188a5d9'),
    ('docs/symphony-hardening-playbook-v4.1/GATE2_V1_CANDIDATE_VALIDATION_1.0.0.json', '100644', 6237, '72632e9f2d92d176668286016f2ed3dfda500d85', '0d67fe1c0c532294dd3e946618d5bfd40c3d5ce6f50804e4bd20823ae5f756b7'),
    ('docs/symphony-hardening-playbook-v4.1/GOVERNANCE_RECONCILIATION.md', '100644', 21083, '33312ade518ee613f4060083b2ee8cac279ddebc', '91f9cdf561a0204380f7e85d1c011ad772fec7b6567a4e1b3951158e2116478c'),
    ('docs/symphony-hardening-playbook-v4.1/GOVERNANCE_RECONCILIATION_2026-10-05.md', '100644', 13466, '9456660f5bc0e6c808848947fb314ff58c21afcf', 'bb1b996df8d14a9fb039fc7db62f73ee5d8e1aaf4d9762b6bca1d8c3f88ada2b'),
    ('docs/symphony-hardening-playbook-v4.1/H-070B_IMPLEMENTATION_EVIDENCE.md', '100644', 10416, 'a0c691bd70f0640e0ba8d39244ad9da7cc920500', 'e52d829a8a7a48cf4ff305c07902ad314e93200f7ca3e6abefbb2198f1c94c8a'),
    ('docs/symphony-hardening-playbook-v4.1/H-080B_IMPLEMENTATION_EVIDENCE.md', '100644', 18470, '91cad1eed2bbd3fc641cab2dd958a4d96b918c9f', 'fd463e8965b572d4bcc121840c10b220e78cca971b01e632339601f63da458ec'),
    ('docs/symphony-hardening-playbook-v4.1/H-080C_GOVERNANCE_MATERIALIZATION.md', '100644', 3211, 'a3e8889f5cf6654107d27f5351995659e505db0b', 'a0a8d7d74ee29537dbc48bf2b49fe3c2de3529e6ea787b3463e80f46b14ace82'),
    ('docs/symphony-hardening-playbook-v4.1/H-080C_IMPLEMENTATION_EVIDENCE.md', '100644', 27316, '6196178a2773ba125f1f0482197e2fc9723b5840', 'a94c9d52c943482796754ccb706add917c9f1da4943fbf2481ed3ff35b8cf633'),
    ('docs/symphony-hardening-playbook-v4.1/H-090_GOVERNANCE_MATERIALIZATION.md', '100644', 3102, '375ec9d112ad7fb2ffebed83046985cd91939568', '9b9bfaa67e50267d79a69d37d003822440fef45fe5284ffb6155f926440c9e7a'),
    ('docs/symphony-hardening-playbook-v4.1/H-090_STRUCTURAL_HARDENING_ASSESSMENT.md', '100644', 24203, 'f6e0e7cc792e823d169b9fd3fc5b97ab91dd570b', '30115634e2f567c7086a814b9871316c99181d9a6362d939c1a5d6c7cf650a37'),
    ('docs/symphony-hardening-playbook-v4.1/H-120A_GOVERNANCE_PRE_GATE.md', '100644', 58432, '191040b985ebeb7b22df3a3e0f469610b08ebb4e', '4d015043d2e247acfedd7bbaf0f826a0b650c4846d34342b2893e53eee2c4f29'),
    ('docs/symphony-hardening-playbook-v4.1/H100_P0_SUBMISSION_CORRELATION_IMPLEMENTATION.md', '100644', 5329, '95f9b7a3aab31a71f72d80847568909ff41c5b8d', 'faf49d3a544c2ad97095063cc87f28ae3569c2255331308dc384a6da2bb11565'),
    ('docs/symphony-hardening-playbook-v4.1/H100_TO_GATE2_EVIDENCE_AUTHORITY_CHECKPOINT_2026-11-06.md', '100644', 51689, '75957f6d2a7f1a344db8ae48b36cfc04f8cbe10a', '8ca5a80c4230e81e91856bdf66a76d8e7a27b1a7c89fc6b6ea079a33ab277590'),
    ('docs/symphony-hardening-playbook-v4.1/HARDENING_STATUS_LEDGER.md', '100644', 26712, '9830d546a803d6de8c5e24e1584c320945176afc', '9fe47f4a454c1e1b838a930c882665dd845da23a3650e15f98917e715f23c18f'),
    ('docs/symphony-hardening-playbook-v4.1/P-000_PLANE_PROVIDER_FEASIBILITY_EVIDENCE.md', '100644', 2846, '183a6b5ad1292e1e0502683bd38506ca6e72c902', '21d76fe0d7d922afcd70ef7274e16f59062ef8a72b27fb296a830f170a30c722'),
    ('docs/symphony-hardening-playbook-v4.1/P08_T04_D03_D04_SOURCE_EVIDENCE_CHECKPOINT_2026-11-09.md', '100644', 9524, 'e8da73adc40d1f9df6632587015aea496383a0d2', '22b151499a5a7acfe14ed8ea5de7b58938a5ce8e5779e5186275da4783a83bbb'),
    ('docs/symphony-hardening-playbook-v4.1/P08_T04_D03_D04_SOURCE_EVIDENCE_INDEX_2026-11-09.json', '100644', 15410, '2929fe30dea0fa4c92adbcaa118458565567f12f', 'd1162d2a8f4063c36e8f0e00d3a496d00a3487100ef589133318d310f3e1c607'),
    ('docs/symphony-hardening-playbook-v4.1/POST-H090_PRE-H120A_GOVERNANCE_MATERIALIZATION.md', '100644', 2369, 'a670bb03ee3fd7b5ca2fb83ceee6d20f5942bbec', 'e638a14ca27d20a66b15cf458979f1236b95c1dc1ae87c7ab1ed12216f08d55d'),
    ('docs/symphony-hardening-playbook-v4.1/POST-H120A_PRE-H100_GOVERNANCE_MATERIALIZATION.md', '100644', 5426, '67a3a6468caf5d5a30fc5ef71d6e39df8a31191e', 'ddc2e5dae716c5a9aae1580a42ff1e7c0d0f6674253d5580a30252eb0bd94195'),
    ('docs/symphony-hardening-playbook-v4.1/PRE-080C-01_DISPATCH_GUARD_GAP_REPLANNING_PROMPT.md', '100644', 4924, '22327d30c3f712241675777e894c8b886bc4a63a', '4780ac68742427a893dc6dc92dfc99e3bf9ea1ef6cf6ee62e36a6c25e26e0a82'),
    ('docs/symphony-hardening-playbook-v4.1/PRE-080C-01_PLANNER_AUTHORIZATION.md', '100644', 53009, '02bb421fdba6acc51e5e93267216408aa0956724', '6161e839ba43be4014eb4099e3f23a0c43cb49e323279d3891d2064798706040'),
    ('docs/symphony-hardening-playbook-v4.1/PRE-080C-01_PRODUCTION_EVIDENCE_ACQUISITION.md', '100644', 8661, '0bc0ecae68135e80a09829e88746f5ce08f3f3df', '64c2a75166df08a589a78cfc239a7ec71609df718cbb3e653c79813cbf9fdb10'),
    ('docs/symphony-hardening-playbook-v4.1/PRE-080C-02_PRODUCTION_RATE_EPOCH_CHARACTERIZATION.md', '100644', 10020, 'b69d46676d3286262bf7cab783654c10a08801bf', 'f3653fba5b49d306d971ef6d50c4ba72d557a015ff20c782f0f58fe3b308312d'),
    ('docs/symphony-hardening-playbook-v4.1/PRE-080C-03_GOVERNANCE_RECONCILIATION.md', '100644', 9474, '12847ef076256a42d511a5400e35b2ea4e0d4ee1', '1f2776f2a2310a6b483f2a04bdcebdf21c2a66953c2432621550f926b137d035'),
    ('docs/symphony-hardening-playbook-v4.1/PRE-H080C_RECONCILIATION_GATE.md', '100644', 8924, 'd2d8025aa947a65e0c5249029f1cebd6ecfd76de', '89798ecba7024c731cc635618b923f18d97d39e5ddd65b63210f0678bc276971'),
    ('docs/symphony-hardening-playbook-v4.1/README.md', '100644', 9590, 'c70ffa2b6644be09ce2abe67790bb4a254a2de85', 'b598a7fc6910b391fec273e990581a05b9d092bcbccd8287032547e539aeee0c'),
    ('docs/symphony-hardening-playbook-v4.1/V3_ACCEPTED_AUTHORITY.md', '100644', 1659, 'e2e26ca09ee141e1ccbb5c44c39f0ee48505817c', 'b401600d42811bd5cb2e76aaa58fb26f48f16b5bca96180470dc6e1cd4bed04f'),
    ('docs/symphony-hardening-playbook-v4.1/V4_1_GOVERNANCE_PROJECTION.json', '100644', 1530, '90b06bb63ba1950c916a0571ab0ce6fb297a5a98', '4dd3a92e46893b07edc1d691f20db60f969ccd94d036d2e3a9875994e028eadd'),
    ('docs/symphony-hardening-playbook-v4.1/V4_1_MASTER_ROADMAP.md', '100644', 125166, '4b0528bdc0647d889b42ebc478081d5b873898fe', 'd2966689ad6b9d50d52b5110c76698fdc8666cf748e921164cc34b3ad1edeaf9'),
    ('docs/symphony-hardening-playbook-v4.1/research/HERDR_GATE2_EVALUATION_2026-11-03.md', '100644', 63630, 'af7a3af7907658d9deda3a72bf666ad0016adb95', 'd7ffba65cdb640a7a4e45313667ce20c64d3fe1d5284020722f556b6c14cc892'),
    ('docs/symphony-smoke-board-review.md', '100644', 122, '0eaab456b7db1f185bfe357f52321d550224d08b', '2be917c896e3575d1228bc8a347401309280e95b5a7b19937f420e1dee0a3333'),
    ('docs/symphony-smoke-test-one.md', '100644', 113, 'ff9f057a3f9b1e377e4f95e788fbc68626dc45d0', 'fdf9ee46957674d68755410e99eea76076d675efe4fbe653f498c70da9f70510'),
    ('elixir/.formatter.exs', '100644', 117, '59e60a5c2e196da0f85854752146d94a2d584560', '735fb1587a22316dd160ff59e6b5a0977012122deed0d90ed3a43d3ba41c00af'),
    ('elixir/.gitattributes', '100644', 67, '6db95539d7d102c593a9be692aa82f9a2c0326d4', 'de9e55c039020a788fad34ab3e9d2d5a0dc22882b938906ee325febd1e366753'),
    ('elixir/.gitignore', '100644', 935, 'bdf8faee43c0336a7feee32923414239823ebb6f', '0a20c9eb02d5bd84de416e3592868ace49d2e84ae108b2e1b3285bd1daa90b38'),
    ('elixir/AGENTS.md', '100644', 3930, 'd10332b7cbb6b902d82d6a08d876307514190bc1', '5ef5d61ea61a6830b9e52c2359f98a515ce0afb2ab5e3e97c5c07c2f02ad80fd'),
    ('elixir/Makefile', '100644', 2541, '6b31af3677b554ce4599e2238c384872d1a7a6f1', 'ce4c51f15b4b75a38cad03937ef8b8dec44ee4c1b97c698369a69256235d7a2c'),
    ('elixir/README.md', '100644', 35253, 'a7d53688011fcd4665c3f829faf2f921367b4f9e', '0b4e54baa42f3226f85d6b5a7d44517864c2c913d206229c0aa989fcb994701c'),
    ('elixir/WORKFLOW.md', '100644', 2998, '1f7db32d1cdc8886a4039233a257601fa057868b', '9875f383fea7d9c961b1051920d15ac9c1935c318ec8272ad4c810354edff66a'),
    ('elixir/config/config.exs', '100644', 1106, '850908b1aff8a74acec645c08fcfec696e382311', 'ca80a618fb3c137481ffc07aece0e3fec6ba641dff5422662f1052454777daad'),
    ('elixir/docs/logging.md', '100644', 1827, '0cfc7509d0c4cb5e91c2e116380bfacee89ec881', 'b4c01da717287e051a15ed136847dd732614a808d729f16ff82ac9a13370c908'),
    ('elixir/docs/token_accounting.md', '100644', 9172, '2c6e107be2a0d44a91bca89e1265875a073622f1', '691c51c71685528a9e7a0f9d78e587a8c202d01ed14dc6c953c3f6c3489664ce'),
    ('elixir/lib/mix/tasks/governance.check.ex', '100644', 2473, 'e8dc7e3fb3b36ff4557c7aa1d453ee9426b91a55', 'c179f25fa7fd6b965c1200bedf5edffa1b0d8fa16aa67971528bd6a8539b13c2'),
    ('elixir/lib/mix/tasks/pr_body.check.ex', '100644', 6369, 'e2d6b68294d59bea3fab6ab1bcdef06dae5c306e', 'a85a551c670db03533d869815a76a0b47232e924ffb2ab348675f54ad76ffdd5'),
    ('elixir/lib/mix/tasks/specs.check.ex', '100644', 1489, '8f7d9e2429e1a7728cd0b6ef6debc4e7258129cb', 'ebdbab36f8982324aa0c1f203fc97bb63e3caf69efbe23a830a6f547fc7ecafa'),
    ('elixir/lib/mix/tasks/symphony.attempt_migrate.ex', '100644', 1885, '1bbb249347dedc265722c90f060de56033f0e225', 'ab038b5467f7eb38ddcf484b73aea8509d4afd90e60df19e072ad8d45e5b2391'),
    ('elixir/lib/mix/tasks/symphony.attempt_rearm.ex', '100644', 5674, '00d0a3a5824f2f0acf08b85aa9dfa4460e8a3705', '41e1e8ea4c84697df35f4aa1be2e2c55c0574152c4e33ab99b78e67eee613f92'),
    ('elixir/lib/mix/tasks/workspace.before_remove.ex', '100644', 3431, '8489f1de12337bea310d90c95eef8dab63e57da3', 'a80e11c01f8949c37445aa2379008e77df442860451f035b6a7028a5e9f89094'),
    ('elixir/lib/symphony_elixir.ex', '100644', 3022, 'b21c7bade62f41a29a76c3dfe81f862aead7f51c', '3aeccfcd1a26649cd5f8c48342f3e0dba05fedeec7eab3d88d93e1bc877c557f'),
    ('elixir/lib/symphony_elixir/agent_runner.ex', '100644', 51681, '54984269ce82fc24102dc64b362dc884b95f93e7', 'c91674da4a17ec5e3189383c7f7477ce69c2ecb42f4f38b1a9aaa9f6b4fd473a'),
    ('elixir/lib/symphony_elixir/agent_runtime.ex', '100644', 1608, 'aa6dbf34efadd5ee55f68ddaf3048825f3daf7ed', '358f83397f76bdfc9b92459ab26fb676fd14ea8a4965b4b54bcf5670b98ef3cc'),
    ('elixir/lib/symphony_elixir/agent_runtime/attempt_boundary.ex', '100644', 22458, '539363f3fb8587be7ac3dc15d09627ce87363d3f', '811f4a03858ddb3c65d35cbfafe1efe26fcc2c75e298bd9912ab659aea2118c6'),
    ('elixir/lib/symphony_elixir/agent_runtime/attempt_grant.ex', '100644', 7402, '9f8c32f2da99ab8460514a6f8b2f2ed0dc5bb9da', 'e8981da3822a9e3ac58bc7d3a0c85b99a21a892712d0dd2d787b5a7ca867dbd0'),
    ('elixir/lib/symphony_elixir/agent_runtime/attempt_ledger.ex', '100644', 73478, '651e2906c69bcddf5592de8e81f5c924454d234e', '9d99dc6e7222ffbf06868cc469e00be958bd2d18812ebe42642e5ce45a8cc4fb'),
    ('elixir/lib/symphony_elixir/agent_runtime/attempt_ledger_migration.ex', '100644', 29457, '0599935e14484edc5a05b1fd0541e659eebd3ea7', '55180e28ca3ebc47c53a2f8a629e767283370de80098edb65f6a5a01f6bf9f15'),
    ('elixir/lib/symphony_elixir/agent_runtime/attempt_policy.ex', '100644', 2521, 'c6d807d389bcff1fd20d7e1599ea3acad848cfc2', 'c0a1aa07d6803a4d66f6f275d498cb7e6e3b80ecfcd4564520c0b1b208a2ef16'),
    ('elixir/lib/symphony_elixir/agent_runtime/attempt_resource.ex', '100644', 6074, '31fed4bbc1ac9c2473b3801b851d886e3879a5ca', 'e9937d368f116dab4174575ef42cfa3f870398bcfede493907dcdf2fa1ae9264'),
    ('elixir/lib/symphony_elixir/agent_runtime/attempt_resource_ledger.ex', '100644', 42050, '03304ea00b63eb47a0b2ecfba2f26a005141527f', 'a04a258e374c49c70a2fc421f3512a73f93d2aa71028712f79dae20a0728b58c'),
    ('elixir/lib/symphony_elixir/agent_runtime/authority.ex', '100644', 7654, 'cb4f1fe861fc18a3a33d1970266cc9c71b8cdcf0', '344692ecc0f4537e87a29684ba2456b8edc191926c9b7500ee5f03444e9da066'),
    ('elixir/lib/symphony_elixir/agent_runtime/cleanup_evidence_ref.ex', '100644', 3421, 'ff95e81957358c4fecd83b92124a50e6347fe854', '89f1f05bdf814d0ed1a37d8d1c4af6a3b53d1eed389875cd48d7d98fac1db454'),
    ('elixir/lib/symphony_elixir/agent_runtime/codex.ex', '100644', 3364, 'f472067d32ef2a980dbac1f7fd22007e33c3d3ea', '43e33601931b8343b1b6a2cfa0245bc71c2d9becce98bd3bdffc108e69465758'),
    ('elixir/lib/symphony_elixir/agent_runtime/profile.ex', '100644', 12596, '9d745e070ba7335bba718f83a37a25374ffe83b0', '1a4676af0641f3fa1261d9a5e4641ffb879c871579eeca1ecb95b4de58da79d8'),
    ('elixir/lib/symphony_elixir/agent_runtime/quarantine_disposition.ex', '100644', 2613, '2c322727f440034a35dba53ddd0d1fcd3a4ca57a', '67e9fa9428164f0d66225183b5cb1d12fd43a7a319b80579385c5d2b0718bc6a'),
    ('elixir/lib/symphony_elixir/agent_runtime/recovery_generation.ex', '100644', 2037, '22f61a1621b901cc185692ec8dec49c701dd1e01', 'f1eb3a04b7bd18fe90bb528fa4f05d82910cc81ca4cd9e4c1481ea9eef114573'),
    ('elixir/lib/symphony_elixir/agent_runtime/route.ex', '100644', 3209, '51768a36d0fa296bd53d9ec331a688b400ac79e3', '29b28af63a211a5b288c2d779b25c96b47373294ed3ded3e720e1668f1f1fa74'),
    ('elixir/lib/symphony_elixir/agent_runtime/router.ex', '100644', 14173, '3d725a00ecc8d29fb6975fe8075a578e6ec069ea', 'af540224e64bb8efa7234fd519cf44ad3841940578c2850cad072e8618bc8a77'),
    ('elixir/lib/symphony_elixir/agent_runtime/runtime_attempt.ex', '100644', 4948, '733c22a158d2766e11ca43d00c1dc9de2fd06b7e', '69f7eecd174a489d6e5a3c6ebc6dbe5db76e59602baaa208b3a870cba370c6a8'),
    ('elixir/lib/symphony_elixir/agent_runtime/runtime_isolation.ex', '100644', 8638, '6eddd348bc4a4aac19cc1bfbf88059b58575c8d3', '0422158eb942e51ee9321bdbe8ff75f43226a27907e3d4afcf10264c6a572fb7'),
    ('elixir/lib/symphony_elixir/agent_runtime_supervisor.ex', '100644', 2650, '4f2df66f0e3bf6aad0a4f6fc0ae2ca2203c3c208', '2c3186b7a1ddaafffb0dcb16ccd9b85701372d3a97a76baddb4ea7ed26149836'),
    ('elixir/lib/symphony_elixir/asana/adapter.ex', '100644', 1831, '473e65eda0d6b6cb351b43fbd861359d5b2d2e87', '02c7b18b711ce41e4ad8de0a205455879f5ca1d51a4ffd10de2ed5911f4c2aeb'),
    ('elixir/lib/symphony_elixir/asana/agent_tool.ex', '100644', 5394, '84c24141bc5f9c2595e04b09baad8ac7ee22373e', '19201b8b3a62e3647f7d3ab7b1eb6e5273b10194e311097a4522a5308ddc52b7'),
    ('elixir/lib/symphony_elixir/asana/client.ex', '100644', 13665, '37f72b601572cc1cfc2907079649d037426f9a4b', 'e7b5d5214ea8d35dff4d6ad3211d7da2a33c3cdfd35e4856caba0691a053c817'),
    ('elixir/lib/symphony_elixir/cli.ex', '100644', 5800, '63f62b9cd6ebb4cdf0513794ae71db8d26979ef6', '90486e81fa92249fe0ce873f39a88f0a96e37ab31531f58c919d7beacff03702'),
    ('elixir/lib/symphony_elixir/codex/app_server.ex', '100644', 68776, '37a10d6a4cf0635462e8487232536dd4a9fb6f29', '8422f469e5306c4765cb1276b98791235d097567810ae0d016b176c7f90e1cea'),
    ('elixir/lib/symphony_elixir/codex/dynamic_tool.ex', '100644', 1541, '1240c9a4c77ed7d4704b78e26f060cc4bea99d84', '1470aec0df77c1403d737c36ceb41699a860c38eb5de4a1ece428f732fa5b0a3'),
    ('elixir/lib/symphony_elixir/codex/isolation_profile.ex', '100644', 65670, 'a15dd10a3b690860fb2d2ec16b7c050093709c18', '18c59c60065462a7c9eceec57f43880cf7c186b7e808c7c25c3d33df3cb8ea4d'),
    ('elixir/lib/symphony_elixir/config.ex', '100644', 10725, 'cb77d052ba64d2ed03ba55e77c868a11f8695248', 'da9675bf5d61b010725a9439e08573164ab4210a38bdd415620ca4fba5a200f2'),
    ('elixir/lib/symphony_elixir/config/schema.ex', '100644', 42243, 'd1dcb7cc02f997bac3976db0de44b492bd6bb329', 'bd3aa04387a3c1a60cd94870f2b39d3cbc2f2978922fbeb04754005b16767161'),
    ('elixir/lib/symphony_elixir/credential_boundary.ex', '100644', 20021, 'aa8c27d7760f4025cb475304994c4b97aef62e77', 'f95e919c0e03f48bd274ba24c342f620ab2a3460c719956b8db58f7bf74d8c35'),
    ('elixir/lib/symphony_elixir/dependency/graph.ex', '100644', 14335, '250bf031dbac9f54da69f58b8b92eeaeff557290', 'd9252605fcfb8274943b27d195102ae2c089b5ea1130d47253e7a526bb4324a2'),
    ('elixir/lib/symphony_elixir/dependency/guard.ex', '100644', 4751, '9e579362b8b48c29a28cdd460be2befabe745ead', '4b435ccc742f89ed2d65e4fdfb481db82c91ee1c059c4b43fcf30be12df3f7a7'),
    ('elixir/lib/symphony_elixir/dependency/policy.ex', '100644', 11524, 'ef2a8cb94027609bbb01db4287cfba533e2719cf', 'd79a80efa45d95e69ca478c88b0c7bf9203a016012c6333977cdaa4d0e4f5be0'),
    ('elixir/lib/symphony_elixir/github/adapter.ex', '100644', 2145, '5a770167ee9727a506fa8524f16a22a993fed536', 'b84d774fc2a89602640a376c7f8ca1a2ef98481ad815633dbd6ded6e5dffdde9'),
    ('elixir/lib/symphony_elixir/github/agent_tool.ex', '100644', 5488, '9b42aa767f22778d9b91d05ad29cc145a8ce722d', '57c2bd2ad39e74badaf4873a52cbb86d13b773ca1a00f6254daee2dc25ba244e'),
    ('elixir/lib/symphony_elixir/github/client.ex', '100644', 13063, '8bd63c1b737b7ab570f6bd0721b8921b6fc3ce5d', '45286b1b09d5dd1627e2fcb3784a4dceb5c667978f032c100ec9a62d5ce7c02d'),
    ('elixir/lib/symphony_elixir/github/source_control.ex', '100644', 24844, '4f63973ed391323ab3236158520a35a95fbcbf22', '5e14d9804fda53ffb54bff7785b41a3edbe30b2cfa287afddced06177e5ca4ee'),
    ('elixir/lib/symphony_elixir/gitlab/adapter.ex', '100644', 2135, '0689cde000629e38884e950ea9e591893c7bc23b', '0d8e355e932b87edfd213ab5df8f7ae2deac04d22e75a7e8f8dd55a3b340c9f4'),
    ('elixir/lib/symphony_elixir/gitlab/agent_tool.ex', '100644', 5436, 'b360a966eb4bc4099222354ca15136e1aa17da3e', 'c9e0096c45bf42cf1bf9f3b4e95f428bc9b531991d55f47a6953f010c88fc495'),
    ('elixir/lib/symphony_elixir/gitlab/client.ex', '100644', 13437, 'd34790a6018899a1a9b71b61993829a5d6a8a99c', '5864add0afa63a6d14006d361bcc1ad81b344d88247f06e0ed32a255864fd71a'),
    ('elixir/lib/symphony_elixir/governance/check.ex', '100644', 70367, 'e1946f2798eedd4fd16d5f0e025399221e408ab3', '0b6b4c0772009661b0dd79461d72d83198090615208059c9492d7305523287d1'),
    ('elixir/lib/symphony_elixir/host_evidence/p01_projection.ex', '100644', 15916, 'e9b3aab3fb840583cde9e5015fb9964b6ace0b27', 'ab75d85a4124ca3d4cdf02d14b0aea67018cd739707511e651b36b34c473e67e'),
    ('elixir/lib/symphony_elixir/http_server.ex', '100644', 2587, '5f947b880af91dc8edf2f6bce84870dae7d73321', '1b9a4b609ff66e97ee4771e610386daa6f6c8dc680dae6efc882ee21853de45e'),
    ('elixir/lib/symphony_elixir/jira/adapter.ex', '100644', 1830, 'a68ff3c28dc3f3abeeb4b8a00e1e9072a0aeb5a3', '0ab622518764ebca7d26e422b5926c0dfde9a4febb383bca2f7c5a169088458b'),
    ('elixir/lib/symphony_elixir/jira/agent_tool.ex', '100644', 5400, 'c33e0202c260e4fc4ce31c6949d9d8bf084c53d8', '4002c781b9ca5bdd7d289c8b7508fa2b7d2c63f686f0d9fcb31b01854371c267'),
    ('elixir/lib/symphony_elixir/jira/client.ex', '100644', 17367, 'e9847e5ecd403bfaf1e6f4ec8f2dbdfba3c378c5', '2d0188dec9219ebcf3b8bf2d8f85ac177af849aff5854111999b53de2cad1a33'),
    ('elixir/lib/symphony_elixir/linear/adapter.ex', '100644', 2465, '9e557c5e7a00f3efb0ad2e05ae463968b521b8af', 'ed5dcaedc6911b1780e1875283730e8da341529f04c4f80da9fdbc47ba1f64b7'),
    ('elixir/lib/symphony_elixir/linear/agent_tool.ex', '100644', 24544, '4bada19d434305cdd881d23db444ed8b773365f6', '4d9b23b3957cc3958324389ed85c9462166353c88efdc14316ba9af00d367a73'),
    ('elixir/lib/symphony_elixir/linear/client.ex', '100644', 29535, 'a255097ade948bf98bae0bf356800cda6cfff6ff', '5c0f560279381fca4e71d2db147e94afd8c9c1fd551ad00aa7107584865db21a'),
    ('elixir/lib/symphony_elixir/log_file.ex', '100644', 2235, 'ea3ad3f8c5b843a6a8e0502f0ce0454ab15b3874', 'c613c7cd0bb1095b076c65dc704c4c4aa28d7767ba20f4757e1cb1424dca5468'),
    ('elixir/lib/symphony_elixir/orchestrator.ex', '100644', 448900, '39f1dd2ca713cdca365a606c327cdd2c4a3953fe', '559d172f5dad767b1d7702f121620c2414ee221a42a704edf522241c0091a7e7'),
    ('elixir/lib/symphony_elixir/path_safety.ex', '100644', 2418, '9aa9067396ac94eee43bd504e59baff23f37c694', '15bd4f4eb57c296945c5f94a1f8c86e411ac10c843d6b0a8c01577f1a328656d'),
    ('elixir/lib/symphony_elixir/plane/adapter.ex', '100644', 23600, '8ba2923b92c7283b1b6be5228009d2ce5e27b207', 'ea722baa99c4cd57c2efd7272dfabf3716c8f2cc7d1b5cf0d7e9538211298959'),
    ('elixir/lib/symphony_elixir/plane/agent_tool.ex', '100644', 42117, '61f0ead0c3b41bcbc5aff5b9f07f03a10f5064d5', 'af20284cef4b7331f36a321cbf4c1da2af469dd798da5e97f310edad78bf740f'),
    ('elixir/lib/symphony_elixir/plane/client.ex', '100644', 34782, 'ba857bde56d4d5b9d1ef7caf8eac62183836f00c', '11d089ea1bb36e0b5548d09d30f31a593993d5b8335e25c11aca19abbe22d1d6'),
    ('elixir/lib/symphony_elixir/plane/dependency_reader.ex', '100644', 16467, 'b1ba60638192d9622dce2e73721d400d55819fee', '7aa8e9da9b005eecdcf593e7cc9be6ade1425393896738e4eed8e1a2716156a8'),
    ('elixir/lib/symphony_elixir/plane/project_contract.ex', '100644', 24184, 'dc5b050d1b25553dc86c9832d6a24431ec9e04ad', '5a820a656fa5791f26219ef3a268c42f1d9da6f841843dd2ab1fc512293e72b0'),
    ('elixir/lib/symphony_elixir/plane/read_scheduler.ex', '100644', 29096, '45fac64d3a65dc6d6e5efd677e48ee1142225aa2', '1ff4486914aa31995d26a9195acc11fb765a8e90c118002f872d3885962b89e7'),
    ('elixir/lib/symphony_elixir/plane/reconciliation_intent.ex', '100644', 2387, '9fef056fa717356d065a74d7757142f349069a0b', 'a0db652aae0926ac729725acfdb4de523ca51c7f824df3777d619fa9f069ca66'),
    ('elixir/lib/symphony_elixir/plane/req_finch_error_normalizer.ex', '100644', 1317, 'a46095a672f9b3371340f1c0450339d33886ea47', '28911f12f3f3f63b25a5692d863fbbf445e1b10d73dc42aaad3b2a757ecb92ff'),
    ('elixir/lib/symphony_elixir/plane/state_projection.ex', '100644', 13042, '76896fbbbc02b9ef5860ac37ca2a2930403ba56c', 'eefbb607c2b21245d839da541cf184db8ca27df1b3548be73b55c4e01e0d1372'),
    ('elixir/lib/symphony_elixir/plane/webhook_dedup_registry.ex', '100644', 4247, '6e4565d67afa853f241c9dc7bd47aa956e0c97c6', 'a1f5a3042682cd74da71f933657b779b569c1b5c0a1a460e6eff0bf6045373c1'),
    ('elixir/lib/symphony_elixir/plane/webhook_delivery.ex', '100644', 7769, '5533411f90413646a198d96acb733d3a97291caa', '19bebc4e8f00abd7434f86064eedd0a73330819c410635a63d5037e85433ae74'),
    ('elixir/lib/symphony_elixir/plane/webhook_ingress_metrics.ex', '100644', 1097, '19c4591d910b3e22402e7b74e01b23b2b90db072', 'eabea52b8206471fc28a624a72ae6ffc5a4a57a5f5a7c4effe5a2917b5239085'),
    ('elixir/lib/symphony_elixir/plane/webhook_signature.ex', '100644', 1496, '9f2878b438f2d9f8e05acdff80c2088dc100833d', '1cc823f9999133a052bfdf6c67e0061229be2ca49d28f182d42379a745902f7a'),
    ('elixir/lib/symphony_elixir/prompt_builder.ex', '100644', 6132, 'bade5d03c1087fda890a279a84dd99803b62360d', 'ecea031f4a2d2fcb8217a4e8f4581e01018481c7b0a5ebe220740f20e4f0a8ff'),
    ('elixir/lib/symphony_elixir/source_control.ex', '100644', 51096, 'ff20386a0dfac710118dcad6b8e1f40c2d7e89f1', 'eb0b55e6bebc005dbc26e0a440140f478dbe8419b637b4eb63756331eb7466eb'),
    ('elixir/lib/symphony_elixir/source_control/agent_tool.ex', '100644', 3124, '082a9e56f6add10780449561d02fd8e1177e1595', '5f6a6497dbed02cc06a53886d0474498b40d8a814c6df0828766d63024320f53'),
    ('elixir/lib/symphony_elixir/source_control/candidate_ref.ex', '100644', 3873, 'cd5bb540fe95a1d9351ade83e765b5267467096c', '82158f391c39ad312a9252b4d89e0ce30c91f087055c0c9353d0225cf591fdc3'),
    ('elixir/lib/symphony_elixir/source_control/candidate_verification.ex', '100644', 1172, '9d44c493fa0fe6c0473662133e372c39d67cf795', '11620a8df64e413816522919a69b02f0acc0e362054aa3402ecf07e66c0e3c27'),
    ('elixir/lib/symphony_elixir/source_control/merge_verification.ex', '100644', 1353, 'ce712fbe9ed57ac6545a694142ce6c8e2afcb4c9', '85d62df90510ffb7f2fadd0a8611d173dc4c7cef5a75cf387b22783e3d68275e'),
    ('elixir/lib/symphony_elixir/source_control/repository_probe.ex', '100644', 5565, '664354223839dc8ea294fc0b22b0fecbd2fb9664', 'b66f2f79593c059a5e4aa5e8c9f67f7801fda7728ebe4f36ce1e4fc36db48222'),
    ('elixir/lib/symphony_elixir/specs_check.ex', '100644', 5206, '4e445bc0a7712a76287b8de60134521f80d24a95', '062cdd6fa19b994942b0be205d0a3a0ec4ade080f6cd0f66bbf42d38d94b508e'),
    ('elixir/lib/symphony_elixir/ssh.ex', '100644', 3374, '0493adb0831064281d77dcc4f153122ac1134c26', '2a6f0c262e18389b55422c24705af9e4968d7f76fa536d07323c9df5c08d5309'),
    ('elixir/lib/symphony_elixir/status_dashboard.ex', '100644', 70726, 'e882a1896705f97900521499253fd8ffd810289a', '9d1819460578ca1aa15cb9d4dd4d2d80a0e5e4f3698b9b13984a24c10675a806'),
    ('elixir/lib/symphony_elixir/tracker.ex', '100644', 21538, '57276c193810af09a91b6ea171ea06ab671349ef', '6926883c30a23fc18ddc98baefa03df4c2dd96950e8466b5eceff8453ae05d03'),
    ('elixir/lib/symphony_elixir/tracker/capabilities.ex', '100644', 4885, '0e0d06caeb542d9b645c5937df5684e152b7c546', '67240f0019732076573b26562c36e1b6dcf98bbbea8a987baf8f077bd907ff13'),
    ('elixir/lib/symphony_elixir/tracker/issue.ex', '100644', 2572, 'd32b336975c092371e9284ac5e16fb2f33255c65', '95bfae13459612c41588085ba0ad746ede793441871af044678340ba82e5f8cd'),
    ('elixir/lib/symphony_elixir/tracker/memory.ex', '100644', 10260, '33362d230edd39049aee3a26e00d1bf676bc89a1', '193aa1c6066e4d7a0b5253d92491879cbe75184248928cf39cfa15f561de07d3'),
    ('elixir/lib/symphony_elixir/tracker/transition_policy.ex', '100644', 8154, '4db876216db04b179a5c14d446bb36dcd0722c2d', '81422701717e3cd2c91bd099ffb7e2a9d12030aca968f5cc8772520ab1e61c58'),
    ('elixir/lib/symphony_elixir/transition_coordinator.ex', '100644', 73675, '9278bd2fb58f234337beed767faa2a67f83c74ec', 'f5326a9a9df9e3c7ed93f5137f58c84367b50818a151d012f657d1186c65c3e5'),
    ('elixir/lib/symphony_elixir/work_control/authority_disposition.ex', '100644', 6851, 'f3ae65a43bd69d58590e16cdf6bb695c3db69be7', 'c7a4f164b1063e1ad9a954a08c3bd2e2b477cd680f961bd585d324153af33d7b'),
    ('elixir/lib/symphony_elixir/work_control/completion_proof.ex', '100644', 25945, '6ec7a102744c41c3f40b8b2befe6d9a811b4643e', '7764e1c88c7bb0b2c5d1e9dc542b30efa1b4128a7dd61465ab9b33c96106cdf3'),
    ('elixir/lib/symphony_elixir/work_control/guard_class.ex', '100644', 12688, '3f42f9fefc64e430c62edb82179216c0b8996686', '743d38ef2229854c827a82540021fb21e95b8db238f94b943e143a4ac704bfdf'),
    ('elixir/lib/symphony_elixir/work_control/lifecycle_assessment.ex', '100644', 15135, '9e82c4c0a36ca0dc86e445125f7ff2e7e1c60455', 'baa656016b06a9b9a93d55703b1bfb25939320407478b668dda7f3dd48f716d4'),
    ('elixir/lib/symphony_elixir/work_control/project_contract_evidence.ex', '100644', 6828, '3edfdf470ca769e2b7443c6e4cf719573be15c4f', 'ba4ed0b888d5a627023a7e9356b499316e1ffba32c534f3ec339a6df3fa0cdfe'),
    ('elixir/lib/symphony_elixir/work_control/provider_dispatch_witness.ex', '100644', 9353, '36819fbd2f3e9f6bacc02789d36bc945c0635be3', 'bf06577d93ac251ea371fab4476a7ddedc830d344f85dcc0d1eedfde55f4a39b'),
    ('elixir/lib/symphony_elixir/work_control/provider_mutation_envelope.ex', '100644', 8179, 'ac04e03ec8de191cd0513d08889e929bfe8e7cba', '99e5567076b09de227577019baf7163dc705ba832c412cd145d6bed3c71d73ce'),
    ('elixir/lib/symphony_elixir/work_control/provider_observation.ex', '100644', 12080, '56a9e6ef6614335f0482f7af80a693ec4bc6f39c', 'e348261a7a1d35e1af31d3406b72c527ddd55fca1ab193db77f68de324151545'),
    ('elixir/lib/symphony_elixir/work_control/provider_project_contract.ex', '100644', 21984, 'd4deac14a630880caf3d329c4fdbb612a81a3929', '49c0ca32a6442be86ca70b619263804a634e8ab8632bc1bdf429e971e4d53cb2'),
    ('elixir/lib/symphony_elixir/work_control/recovery_ledger.ex', '100644', 27282, '2cc708807b84273fd2ca44c34de014fbe3831aa7', '01180630a195bcd1ec3168411929e96b73b867d19e992bc85482d3a0e91e7076'),
    ('elixir/lib/symphony_elixir/work_control/semantic_transition_intent.ex', '100644', 5393, '54e8e9b183a63523a85eccae1ed7e4d223e2697f', '598759d0b995c02ff5245f0690c598534d1bf8684e3de82d1831c91aa3796b86'),
    ('elixir/lib/symphony_elixir/work_control/suspension_context.ex', '100644', 8085, '316894373e343764b50788b2efed16f329e8a986', '4638173ca8fbea83983e1612bab074126db1eb437f1d4a6d0b1153272316a16f'),
    ('elixir/lib/symphony_elixir/work_control/suspension_recovery.ex', '100644', 17213, '15454d679217339d3e2f3268122e44995f4a8dd1', '97be64072b22cb74c69f193d892d141a8dc7bb2e6bc813baa511fe92ccf06789'),
    ('elixir/lib/symphony_elixir/work_control/transition_attempt.ex', '100644', 22238, '1062732a1882b8370221c162a6c86b4eaa920467', '08b31fbbdc9c59bd09e0cffe3f667962ead335cdd76d57f4ba0c0441f5c4338f'),
    ('elixir/lib/symphony_elixir/work_control/transition_attempt_ledger.ex', '100644', 31402, '17656ac12cdd5718068690ba2ea9f9504fe8ff43', 'a8561afe0e3f524b62d82af3f9c3d40185b16e4e7f60109b7ff527f9a9cb8aed'),
    ('elixir/lib/symphony_elixir/work_control/work_item.ex', '100644', 9098, '68922e6f09152fe045a25fbaf5f556c284bc1402', '0d522f4a892870d47e96b4911b659ceaef50b14c693868a9b6a0f62b84f6f21d'),
    ('elixir/lib/symphony_elixir/work_control/workflow_lifecycle.ex', '100644', 11967, 'd3dee768b18d74196b72be0c6ab0eaf254c20d76', '39e76f5f9e2c16e78288166885bf00c8aa74c019410b6d5779705a3eeb976266'),
    ('elixir/lib/symphony_elixir/workflow.ex', '100644', 3004, '9c25cedd70635ccf798abed1c8d890e834d3c5d0', '7139901620b531bc1de03afdb7433001f8c14bec3505878316c642a3b2d2797b'),
    ('elixir/lib/symphony_elixir/workflow_store.ex', '100644', 4552, '9160a17ff07ac72693b5ac409017a3176d0fb65e', '5863443cbc9c027785c117050323e552ee9b8d47ff5f5b97f3f03bf4aed5a42c'),
    ('elixir/lib/symphony_elixir/workspace.ex', '100644', 75956, '39fe1d80cf73e9ba1b93d706f184a3f4382233e8', '9dc3787c6e97932515834e3e74a14a6633a3420e0005544ae4f38aa96fc3b7af'),
    ('elixir/lib/symphony_elixir/workspace/ownership.ex', '100644', 3636, '3be31665097cf6d8a3234c52c5b74f79a805f356', '19f9bff1298c372c14f1cfbb43055cdf7c10b171d58c8bae91a0365f53df6c3a'),
    ('elixir/lib/symphony_elixir/workspace/ownership_ledger.ex', '100644', 54310, '07394e1c7373bee234e8eeb4106748f3325bb1ac', 'a33fbaf9cee63e028f21b5471aeeb712d823dbe916ca8ed390068c359186b2bf'),
    ('elixir/lib/symphony_elixir_web/components/layouts.ex', '100644', 1928, '7cc0c0d95f6a975f0abbc8e9deb5c139aa39d48a', '4cb6bc3d1792301dfab050c6db5c7dd94cf6811bcb72616b2c221cba81d175c2'),
    ('elixir/lib/symphony_elixir_web/controllers/observability_api_controller.ex', '100644', 1802, 'da764f12dd8be88e1822ecd70f0210f1db05c717', '9c27cec903e3626e3801b75218e84e4ee9436f12c1722b95fef21bafeb232768'),
    ('elixir/lib/symphony_elixir_web/controllers/plane_webhook_controller.ex', '100644', 2040, 'ac2841cef819698c63c95c37f6dd87981a01f60b', 'ec56e8eef32033c1ca88d0bda4ebfae2f0542d2122d19384bfe8f28edb9db3e5'),
    ('elixir/lib/symphony_elixir_web/controllers/static_asset_controller.ex', '100644', 1250, 'd36a40c461680becc4979817578bc69d23598b41', '8873fdb7f77566bc3861484f1abd7f3f3b4636ec00ed7f42312a450797031c25'),
    ('elixir/lib/symphony_elixir_web/endpoint.ex', '100644', 677, 'be605b7db028ce8047c71b9680f3b499bdcbf93d', '4719c2adbbd327563b7dee7a232249a5f038679213bc5a01b963bd0688e4f26a'),
    ('elixir/lib/symphony_elixir_web/error_html.ex', '100644', 217, '5b2722a26b050431a2c7e710664eda1fcccc218c', '7e234c32db4b1be25acafb61da82b69aec1f4208224f0a426f15f0070ff9b344'),
    ('elixir/lib/symphony_elixir_web/error_json.ex', '100644', 258, '5babea4c28624d2f21e4d7842891536e5e62814d', '20fe5b02e418f18d3920452fa00ad6b07a3b329bf034e92521c3e3ec966b0de5'),
    ('elixir/lib/symphony_elixir_web/live/dashboard_live.ex', '100644', 21902, '022661125ee12eabe2317c88ea9dc3c5cc88a6c2', '754fead017f3e81296e3aaf6f0867f700697223f0e1201751e5512e449272e82'),
    ('elixir/lib/symphony_elixir_web/observability_pubsub.ex', '100644', 592, 'a3fead26f282ed100a2d3ee80c1beb294c061c11', 'e029dc6bc1167c901b7bf65d728278d2a3b43fa583df31157ec4a6af3820489a'),
    ('elixir/lib/symphony_elixir_web/plugs/plane_webhook_ingress.ex', '100644', 6323, '0594af7c6899433449bdc3b2b0b8d8c974234832', '2a05ace5853e2ef4cd0d1fd4c06127bf6e16749d7d76647d1e28cbbbe31175a5'),
    ('elixir/lib/symphony_elixir_web/plugs/request_parsers.ex', '100644', 1242, '1b750458cdcfc989ebdf7ed4ee8e06d253d822e9', '25503cbd7f239762b6bd693930895ccf634a4892c2145225b241d443abe00e6d'),
    ('elixir/lib/symphony_elixir_web/presenter.ex', '100644', 19611, '9355df7ba891525883da74af3f76bb68c304b3a0', '6f37870bc380539be694e264755eb45d4eafa70b04c06d7c2337b1a98e32a9d1'),
    ('elixir/lib/symphony_elixir_web/router.ex', '100644', 1885, 'a25a003021ce3f4756a3d2d4ad17608d676a6811', '9971147432849b5ed33aae4e8c8da6adfb5b611b4feb01d85ba4012c7edc5b14'),
    ('elixir/lib/symphony_elixir_web/static_assets.ex', '100644', 2092, '9d0f2d112482d3dc0f3bb5eb6f647a7dd8e3ac24', '8cf44ca96e0c041d8b57148fbb866335bfe788882624f42a33a52a657cdc5807'),
    ('elixir/mise.toml', '100644', 64, '1c3b6e5852d65e3e5d4d165fcdc674171eba66b4', 'af02077f68f2049cbca38eb229fbb1e99e0fd99897bc07670b5cf0f5b737c8f0'),
    ('elixir/mix.exs', '100644', 3161, 'f4c66cbfe68a0bbdf719fadece950470c2404f44', '011de984f2ade382b0e82159109b1f6446cc0e2adacf1168afd46db883aaab27'),
    ('elixir/mix.lock', '100644', 12978, 'b1972bd22d09debeb57ea90a123a67e36b7dc4c0', '930e2f918c0be22e02e384f869c92a9d125fb8fa059ef269666141f80e8691ae'),
    ('elixir/priv/static/dashboard.css', '100644', 8252, 'd5b453de10a5235bbf2c5d54de79553f525c2bf5', '2d1ded3d4349e4df93d8ba8d364208fecf6fbce5d36cbafdfc31af3582edecab'),
    ('elixir/priv/static/favicon.png', '100644', 17493, '01a738fc29f12459c895d1f27d89a075e1825391', '27913e982b8769bf1ddcdd2b47d0d395597e74ef8d5bca17ef2b428c08046f79'),
    ('elixir/prompts/builder.md', '100644', 442, '406cc4b2dcb980ff87b3a2565fe5fc4d9ee7d6f9', '854536166ec624f0e19388b24942ed116435c5c0e2a0ba2ce8296b692c73002d'),
    ('elixir/prompts/fixer.md', '100644', 422, '7f65ae28bc18fa01b2263d34a722146e5e04600b', 'f2b07fc27aa75f50e33931fd1a58d404f1985128de0d2df00431c2f0f53bcfc4'),
    ('elixir/prompts/planner.md', '100644', 549, 'a0869f395681cd44d96393413f55870ffef91a4b', '55656b19734353891e268836aec4d4bbf82bce798b2b8f02f8552e7bda2f7309'),
    ('elixir/prompts/reviewer.md', '100644', 474, 'e1a1c0edc996b89b2c3c446a18d2bbdc78a53a76', '9faecaa1a0343a1359915890bc3a6bd21df15eed1503add4db5e7138f6d63231'),
    ('elixir/test/fixtures/startup_workflow.md', '100644', 83, '7c2a5e256b5d5aafd61921f0c5a2fde5a29f0f0c', '31c3515604fb35f473cf18dab5be401a2cb63f2c2a40f47de56d0f883e74c163'),
    ('elixir/test/fixtures/status_dashboard_snapshots/backoff_queue.evidence.md', '100644', 1285, 'd231f4446ce792cfc766b068c451fa3b1f1eae10', 'ef8c8d891bbb60f5a831d84298409d52fc4433e347634fa4e0af6185690b36b7'),
    ('elixir/test/fixtures/status_dashboard_snapshots/backoff_queue.snapshot.txt', '100644', 1948, '59708399e74296b86e8601529ab559c2ba6a93c1', 'e2108cfec6a88cda848c52a7a39e1881a2e8b60f52aee455bd4e598cab9794f7'),
    ('elixir/test/fixtures/status_dashboard_snapshots/credits_unlimited.evidence.md', '100644', 974, 'dec3c8ec0c28d772ef16f06e3febe70fd3ebb40a', '0c108675a5261f0ae48853659ee22bbda7214411812522017ff9f08b721b511e'),
    ('elixir/test/fixtures/status_dashboard_snapshots/credits_unlimited.snapshot.txt', '100644', 1392, '99ebc459e422001cce66025e9e297ab8b8f74f63', '74b82f0f0bedf2732e1121c5f2f0b8760df1401e9633e209336d21bdba9fc946'),
    ('elixir/test/fixtures/status_dashboard_snapshots/idle.evidence.md', '100644', 792, '336bf4e323fe172ead87b11c8400cc56c5b8cd7d', '5c2c0bb21aa44a0662b6049a2c8551cdcdf13c93a1bb0da69aa15d0f0ca175b3'),
    ('elixir/test/fixtures/status_dashboard_snapshots/idle.snapshot.txt', '100644', 1067, '8c38d5fec460a4f6413d3d9257c70c831084e287', 'ab0889e49539409f2f623f31780d6c3319fd5b32bf594d1cf2409289de19b523'),
    ('elixir/test/fixtures/status_dashboard_snapshots/idle_with_dashboard_url.evidence.md', '100644', 830, '1072ad5115f199b50633180b4e7fdf3ad213e8bc', 'a2e8be5631e0920495e910fe77e7b5e265bb6c531ef243211c65eb5edf8adc95'),
    ('elixir/test/fixtures/status_dashboard_snapshots/idle_with_dashboard_url.snapshot.txt', '100644', 1126, '934df5e4d1e936cde0641aaa549715ead204e68a', '5cbd2d5a1bfaa0aa13d764a35c9b694be36dc2d309326b6f05d0d8a1c56c4fe6'),
    ('elixir/test/fixtures/status_dashboard_snapshots/super_busy.evidence.md', '100644', 1106, '30915a090ed600fe9941dca80e84ccc232b6534e', '532cb100942d4c0e099fceea6db40c72d2324d3d86ad401625378bf5c8a4f9ea'),
    ('elixir/test/fixtures/status_dashboard_snapshots/super_busy.snapshot.txt', '100644', 1612, '62b1d7ac0913b9ab8ce83295a7c2d5b5ab127769', 'c1844e6975ac07f0550e63b9e2e37dc068eb76af04fe0e4154afa648ae5e8e02'),
    ('elixir/test/mix/tasks/attempt_rearm_task_test.exs', '100644', 9250, '5286c2768901126790a0eb1eb29e42aa68d1f1de', 'db5b2dedcca6996f611d296c5dcaf88f31fbc3c535323d2a41f953b7d7e44323'),
    ('elixir/test/mix/tasks/pr_body_check_test.exs', '100644', 7502, '6f4cf71eb394bc180487bf7c321756950dd4b4d5', 'f50d975321a5f39c37d6592ef19ce6db165cdafc3b59b1f1c6c054fd95b50eac'),
    ('elixir/test/mix/tasks/specs_check_task_test.exs', '100644', 2725, '6909b5ad18b3b654792455866c021d51e699f3cf', 'efaefa8279cc508c0461f53e717fdba3838f55b76a4126b4fc2a4c42132304ea'),
    ('elixir/test/mix/tasks/workspace_before_remove_test.exs', '100644', 9284, '2bbcb3549b63dc2bc3d7e07fe4ebcb261d74f39b', '47f84bdc1a2473546b322e931b2c2a21451a0c86d9539620e9a2fb6a86731606'),
    ('elixir/test/support/live_e2e_docker/Dockerfile', '100644', 600, '974625c1cdae02fbfe2a8ea5fd8e87056f56d1f0', '4855afa61f5acf63b41e8bcdd64261142005f447c6538e5b6711b446f3b809d5'),
    ('elixir/test/support/live_e2e_docker/docker-compose.yml', '100644', 607, '31584538d9ede7ca9801de8b3a40bd31203bff91', '8e1dad6ffa2642a39e7647eeaef140d73fae04054e44e5dfd461a8058d82ceb7'),
    ('elixir/test/support/live_e2e_docker/live_worker_entrypoint.sh', '100644', 312, '3b70e6f4e4c4c372d73ceb5cfda9476455862f87', '4525db591e91b099df58cdffb374283b1a54ea1c8ed0ea60d38661bf4a8f753f'),
    ('elixir/test/support/live_e2e_docker/symphony-live-worker.conf', '100644', 188, '45cc12dc6d001ae776a10d9771e3bb1bcbc6ebed', '2a013011ad924f6fbcc31e56546d10d85e16962188b7b7e6e08c829e3b28a5b6'),
    ('elixir/test/support/live_proof_gate.exs', '100644', 3746, 'be11c40298785c2501e194079d5f33fdd9ac76b2', '7d498bbb7d9a323cd1ba9b406cc281fe05e9851929a5504562b178ede576be12'),
    ('elixir/test/support/snapshot_support.exs', '100644', 2308, '3ad5ed755bd4426b6e70987c2e66b7b3050f6cdc', '4c15c965c1fe8a06afedec2333fca9d2d20ce3a5d0407bed7d5ddc18ea74f858'),
    ('elixir/test/support/test_support.exs', '100644', 26390, '6656ba51017ce628b3e7db3165b3e8106323ab83', '767e7b7f6de707626b6a7430c53041eb4084372ea40773af3319bb27ccffefcd'),
    ('elixir/test/support/transition_coordinator_default_path_orchestrator.exs', '100644', 1023, '1d72966f33e18266ecc09cbac1435c032f5287d3', 'b2d3f0faa78cbf191f8b71f7635494e3be8dfff2c06a6f427ac7bc268d421e93'),
    ('elixir/test/symphony_elixir/agent_router_dependency_proof_test.exs', '100644', 33461, '43708adc81c758f1a854365aeae9b2da0f32dc2e', '4735f2699cd8e895f1ee3116b9afbc9c103085a13254b7ecbb6de7669db2ed28'),
    ('elixir/test/symphony_elixir/agent_router_orchestrator_test.exs', '100644', 29811, '20e1426be325c4c1920d36c1628de5e7f74eb01d', '28ed0ff9ed4aa8a0d0f6458c1719b2fa491400fad16a59280bc38826c9f57ee4'),
    ('elixir/test/symphony_elixir/agent_router_test.exs', '100644', 24488, '0fbd3ea5abd29656e3429ab0ba0db54d0e56dba7', '24c85f24baa83b42d2109af3c398a7662e036fec84f2af7dcd4f820eb0c1bdd7'),
    ('elixir/test/symphony_elixir/agent_runner_isolation_test.exs', '100644', 28076, '893ccd8605be0b6bc7bb47adf46769f10fe33d52', 'a2db5b66696b3363b8cee3b454832f5665c9da9cc3f7992c7d771f5c72c79029'),
    ('elixir/test/symphony_elixir/agent_runtime_test.exs', '100644', 36330, '54d351eeb177a97619ace1a225649889b987b5e2', '639dbc8fb1e2a729e06a5b4b2250ccf1f09e39acb2236095378bd6e343a49e61'),
    ('elixir/test/symphony_elixir/app_server_edge_test.exs', '100644', 31552, '3294a462a4d321d6df41c4d4b463c1d75d4b388b', '59fda4538aecb2eba0819d00385d298cd7b285fb76d3c3266466635251febaa7'),
    ('elixir/test/symphony_elixir/app_server_test.exs', '100644', 113435, 'be8e5534e7c29b897d617ffc145659d5fd0970c3', '0cd082d1e367e1647ef95d5018dd09aac4842b59b06f77f75e68c6d5e89e6a6e'),
    ('elixir/test/symphony_elixir/asana_adapter_test.exs', '100644', 15161, 'ea56955bb800c3bbdd91e796b36b78b28467a711', 'a488a7f9a05c51b5f2c0e3526fa839835ad7fe65f4f7e5c9b6793816647ab2c5'),
    ('elixir/test/symphony_elixir/asana_live_e2e_test.exs', '100644', 16825, 'db2e2f14665a4ecd555665c97f148e5cc3c07aa2', '31d4510dc3a1a3e29317271977bd71b7848ae549454acb987207b49072657e9d'),
    ('elixir/test/symphony_elixir/attempt_ledger_test.exs', '100644', 50476, '5f14a0e6e999b3d432b9a44c7b583ce72006fea7', 'acdef332d397759137c682b4daa6d1dfa17164253e1bce946fcdb953913a33a5'),
    ('elixir/test/symphony_elixir/attempt_policy_test.exs', '100644', 2535, 'c00f8e01e768d6bc729cc4846d23fab2f49cd687', 'aea49f26c3d841eb34d38f6f17d504870bbfd5f2fa29dcb7c32dfbba2c822356'),
    ('elixir/test/symphony_elixir/cli_test.exs', '100644', 4499, '4e42147936034af163cc2740538c1d67894d8dfc', '06a7ca5695d01deec81ccf049ceed0fd09c273b5d15c4c6a90a8797480006173'),
    ('elixir/test/symphony_elixir/config_identity_test.exs', '100644', 4263, 'e2fa441600331bfe4c4bab1f48a47828aa933f8e', '7b4266ba23906c39a5548a536bcb486ed8b7b4f8300eac4988a20d76ee8c0200'),
    ('elixir/test/symphony_elixir/core_test.exs', '100644', 85062, 'eb5d59a96dc70559afb92707100b28fe534ecc27', '87be22ed7ba1fc2fc1afc5ff88b43bb14cf1bc1eecb7b724ab98585cf54eeef6'),
    ('elixir/test/symphony_elixir/credential_boundary_test.exs', '100644', 15700, '86332d3ebd01508f05a8b547f3b11b9e2f02b046', 'e9e8dcac49096b12eef207e63a605a87b314c382d3e61428a44443662f8d1ac6'),
    ('elixir/test/symphony_elixir/credential_channel_enforcement_test.exs', '100644', 20110, '4098211d0e448816abe6195d1fb7d4ac6e1f503a', '17d12ab6cdb24b9e71ff128d84914463bce2ff6cb5968c11a88ef880cdafff8d'),
    ('elixir/test/symphony_elixir/dependency_completeness_test.exs', '100644', 10950, 'fb6355842fe225cba7810c4d38ae78e097b06f12', '430a1ffdab7ca382e75dad7e4cd78406dc214bf6886fbc2af4b4851bd389d3fc'),
    ('elixir/test/symphony_elixir/dependency_graph_test.exs', '100644', 8060, '2a3e070056abe7341a4250642f5e05e6a67b7269', '55d9ec425a7abdf3f4ddbbf65d956fa7184eb207bbb05a83bc5abb1ffc33bc23'),
    ('elixir/test/symphony_elixir/dependency_policy_test.exs', '100644', 9358, '35b3105cee88c20053d1e5ffebdc207f9c6c673a', '249f9dc324bd820a6416183f2219d784853b71ae641209eecea781ca714a2654'),
    ('elixir/test/symphony_elixir/dynamic_tool_test.exs', '100644', 27782, '607f2f3f302ecd0958a98273cbe49ea5a86eee4c', 'daf5f46a9bb5f849d6199902de7d8a1833d4b111d663e921c980438387d5b27d'),
    ('elixir/test/symphony_elixir/extensions_test.exs', '100644', 30480, '02ad2c627cb0168e8347fc9ca4de1f7f16afb150', '0da2f5078c3dfae888db6b575a0834504623d03f48a730f6d0f0fd36cb33ceb4'),
    ('elixir/test/symphony_elixir/gate2_attempt_boundary_test.exs', '100644', 29537, '4fba96cd0f1ee7ecefd49be8e3ea71accdaa5ee1', 'd6c7780c4c32a57c2271adcf10cedfbb3353f9f35c7320b5d0bfed0709f421b8'),
    ('elixir/test/symphony_elixir/gate2_attempt_compatibility_test.exs', '100644', 27072, '556fc825801ed8defb24e5f383eb5962615bfe3f', '5ca7c56a86c97d8dd69becc1f309273f70e8a081a8e9f48990e02a09dfe9701f'),
    ('elixir/test/symphony_elixir/gate2_attempt_config_test.exs', '100644', 19307, '10d50032705e89e5010ebd8d13045484424f3503', 'ac3529e93c7f396fd7742880573c16dc28d6a424a3a7148487ddc6ae2d1246af'),
    ('elixir/test/symphony_elixir/gate2_attempt_migration_test.exs', '100644', 48797, '186de11b9295c405adfd7d6bf5945de80a77f8fb', '44f405e99082994c8e007f3d908412cd57d4038ecf6922e1cefd8da29994d689'),
    ('elixir/test/symphony_elixir/gate2_attempt_resource_ledger_test.exs', '100644', 62749, 'ba4cd605f7ab8dd8ad08d1e3fb5526eba2d699d0', '5ba79bbb1b0badbe33489d3c7410b980c7e07650662406b7a259f8574953a801'),
    ('elixir/test/symphony_elixir/gate2_attempt_types_test.exs', '100644', 6852, '4271508c20f96b3f310bcf4ccdddf77a29cb5e8a', '7c0bf87a2a75787f5ebdca1aa588817e310350aa9c0b0d6100d7aa14c195b72e'),
    ('elixir/test/symphony_elixir/github_adapter_test.exs', '100644', 14798, '24758530aa20eb4033e986e7f7af87cb34f010ea', '52495b52cddc1942b750be076ad90ff7ddfed91dfdd77c2d8cd8eee1973bd825'),
    ('elixir/test/symphony_elixir/github_live_e2e_test.exs', '100644', 12750, '38fb7996276ea9678a5cb0124a21ac296005e615', '661f54c001ba549051c4eabceb8131ee6c5df06c9d1546f4bd957b61a213b4cb'),
    ('elixir/test/symphony_elixir/github_source_control_test.exs', '100644', 24037, 'c809bb4c1615846d062b98d99cadefce04ab3ad1', 'abfa5ccfb7b09e791bfb7759e08022fe685b6b19fd9f2a1203ac274578999bd5'),
    ('elixir/test/symphony_elixir/gitlab_adapter_test.exs', '100644', 16869, '9fc26ab08128ddd062d565d9dcf20c6114d52617', '9b0aaafeebf1a621c01fe269250c221aa2fad2f07e3c56bf51e01edd191d8229'),
    ('elixir/test/symphony_elixir/gitlab_live_e2e_test.exs', '100644', 14237, '6511c3ce6c8da603a5e2e4c600155c649f88f850', '6a3459bdfd796b9f85746a1d372edf7093dbbae7c482e7e9c2ac9ffe4a056cb0'),
    ('elixir/test/symphony_elixir/gitlab_redirect_test.exs', '100644', 2056, '60e81ee72e82402130976f37b0ea07bb8ac67230', 'b1d0a5d7bae0a3ea3aa35cca8ce2511a59df0349148797ae94c938a47f823d96'),
    ('elixir/test/symphony_elixir/governance_check_test.exs', '100644', 67644, '8b41344b78c7cb12c6f6ed9df0e6317da2962de8', '5edb596dfdeabbd70e0dd05931b6a705ca8986ebf7f4010bb18d3b3a02b18804'),
    ('elixir/test/symphony_elixir/guard_class_source_control_test.exs', '100644', 1517, 'ccbcb749b97154cbfc82f218f88f7c4de75c723b', '5aa1a665574f6337ad94ce3000cbb53510a42bb2ea7ab6c4a521407e2c7fcba6'),
    ('elixir/test/symphony_elixir/h080a_authority_fence_characterization_test.exs', '100644', 94956, '7627bb9ac55ab97956831e4c0209efa8bacd3b68', 'cde8e5575c6987eb246de9390bb7b88edc4877781abbcbff4756eddaf57f4ee4'),
    ('elixir/test/symphony_elixir/host_evidence/p01_projection_authority_test.exs', '100644', 5018, '25acd095eef9129b64049cea8981f60f580bfa27', '03da53e8fdc4b94fbd46398ed4571ccc97505d5280c68243aac752dd4884e094'),
    ('elixir/test/symphony_elixir/host_evidence/p01_projection_test.exs', '100644', 25819, 'e793692c0f18ac71a7c972bab747c82280d65ab7', '1f330710b1fe734992e325c376ec632c80301b3a0686f1e0ae2256e3160b610e'),
    ('elixir/test/symphony_elixir/jira_adapter_test.exs', '100644', 19694, 'c3f40844ad0cff966188471124e283288667bda6', '0fe4cfe22034a86df9c304609473abbee3525b2a1f12a942decf0dcf7aaa9a23'),
    ('elixir/test/symphony_elixir/jira_live_e2e_test.exs', '100644', 16410, 'bad1a97dd20bc2ec521761f2164958693b0703cb', '3d1121e66e22181a9aabd317a30b263e50bd98a97ed74dd97665c9265f6fbd27'),
    ('elixir/test/symphony_elixir/legacy_graph_test.exs', '100644', 2842, 'f99c6d843caafbf9b60354e21bd88e2c4901a2d9', '3b17de26b2571d2a7f8a5d48c596f61bfdb0ea3bc9e10982b7faf83e5784a028'),
    ('elixir/test/symphony_elixir/linear_client_test.exs', '100644', 13458, '404cb0a2e82cb7d0d807fb5913eeceaa98956c3f', 'bbf0c196dd6d8e24afd83575e65581952720b20c84a4b1f18cd704dc4294d190'),
    ('elixir/test/symphony_elixir/live_e2e_test.exs', '100644', 26136, '3223e4246c409d79cfe8175f7578bc361fe0d605', '86887171647fddbe9ea9bcad243a68b54ed5f74220646b88470a270b8eb04f9a'),
    ('elixir/test/symphony_elixir/live_proof_gate_test.exs', '100644', 2572, 'f56f701c5a0caf7f2d3a343731c58d3158b725de', 'fb2cd2c4ea579225f9573176bdd92b986c96518df6478af48a96fd6745eca5fe'),
    ('elixir/test/symphony_elixir/log_file_test.exs', '100644', 441, '0ae91522e5261fda1f7cf4ac9c9b9aed32b60227', '29ee649abed26c715a508f45449290496905f09b70de87eb0914f3117ef01618'),
    ('elixir/test/symphony_elixir/observability_contract_test.exs', '100644', 20289, '5c5e51b2164700973b7ed9797a458d3ba8cb8330', '4a6f8284e14d06af4de096551ecf75dc6ce113dae46031eabce8f9a9230de6af'),
    ('elixir/test/symphony_elixir/observability_pubsub_test.exs', '100644', 946, 'c9b1cffb322a5fcf8219ddd1266673efc0a6268b', 'd0d5a662d4701d7faec49b63c6a1586246aa374b29a1df80794db361ace472b9'),
    ('elixir/test/symphony_elixir/orchestrator_attempt_lineage_test.exs', '100644', 68836, 'cebe04d533b4f8409b80c087149c367326087f77', 'f0483ba1da99e3334ef21e03970620268da91c63438aa9b58f11e70ed1f86c3d'),
    ('elixir/test/symphony_elixir/orchestrator_plane_epoch_test.exs', '100644', 175192, 'd882bade7804f58b1b4f6a246df025c982f63133', 'e873a4fb2b718a99e9592f313dceaf4072c4f20b61e0c74aad6bcee8c3211e3e'),
    ('elixir/test/symphony_elixir/orchestrator_plane_webhook_test.exs', '100644', 2570, '826cea85b0f82c79e8692fb4ba96d4680cc3bb27', 'd14043a72b3a9fd4bacf419cffc1b538023e1acc863b1d571ef3eeae972a3087'),
    ('elixir/test/symphony_elixir/orchestrator_project_contract_test.exs', '100644', 20269, '9d120fc87dbf52038078465e68e1dc8bbd581a8f', '67ee86cdb700ae9b42ff62cb3d6e3adbd3ecab49643bf7823da0a1744e5e6bc8'),
    ('elixir/test/symphony_elixir/orchestrator_runtime_isolation_test.exs', '100644', 19240, '4735a381eadd67aca6a903ffabbbe379ebd808ae', 'a5759829d041e303d43fd376ac6211c4fdd0c0adcba69057cbe00364e152c062'),
    ('elixir/test/symphony_elixir/orchestrator_startup_reconciliation_test.exs', '100644', 92447, '15fe3ca250e7c304a21d9c93b0a1e1296a9cf976', '107d2a73c2177c5af85ffbaffc94f1e473ff5d63ce6831b73dedcbb6249e0dde'),
    ('elixir/test/symphony_elixir/orchestrator_status_test.exs', '100644', 65048, '9066a9292d08f32b51afa394fda9a402e23a94ba', '70f826564915f18fd9537ca8cf9a5856abb89c5369d7ddd369b5f5552531152e'),
    ('elixir/test/symphony_elixir/plane_adapter_test.exs', '100644', 36989, '88193945956d0ba734349bf5ea8e7d401b6397fb', '7a72c2ff2246f37e1da6704edd190dfb3f69e22d732483c310dbc686d265c702'),
    ('elixir/test/symphony_elixir/plane_agent_tool_test.exs', '100644', 65936, '65c9673967b8de7c1ab84c901ce8485a2db8100c', '019ecfb3a9b93b91d5a61052c09611d76932831110be4e74f9a79c0e24d3b027'),
    ('elixir/test/symphony_elixir/plane_client_req_policy_test.exs', '100644', 6150, '429d0f400fed3568dd2e555ee975c007d02d3192', '45c942daa2039f6b8b4d63741e8bf4e99c3113c6da1480a4a61ad1372f68372c'),
    ('elixir/test/symphony_elixir/plane_client_scheduler_test.exs', '100644', 6633, '29206d3dca3bbf634c58da6ac73e6d6f1f372a7a', '64e8dc6cbc27f4760297854ce9fc6cfcb2b69d10d587b2dfb041aba6e6b6772c'),
    ('elixir/test/symphony_elixir/plane_client_test.exs', '100644', 37572, '001469e40ec2427b6dc6c36f61bd6461f78d3342', 'd927238f94c135a1e4bd75a70b91cee24022ade687e9fc08cf68d575e5ff6b16'),
    ('elixir/test/symphony_elixir/plane_config_test.exs', '100644', 5575, 'f82d45413010e2f9b04c6a9a8720d7321ab51e36', '227dfa4a5c4a05a55ec572312fd2edbf608c0408476cc7c59c417eaac3e56cc7'),
    ('elixir/test/symphony_elixir/plane_dependency_reader_test.exs', '100644', 31381, '4dc17f1944e035204e68a06304665287d5130021', '2533794cc5f687a0666df645fe98716144c634cdc3f19914cddb95bca56d9365'),
    ('elixir/test/symphony_elixir/plane_project_contract_test.exs', '100644', 13777, 'fba06d91195ccccbb4569e9613c1df016cf046aa', '78803a8292f39325504096b52d3bb309184992acd849fc937ee1ab4407bf4f9b'),
    ('elixir/test/symphony_elixir/plane_read_scheduler_test.exs', '100644', 38196, 'de3c0d68d49e0ced8c4c8460586e6bb296cac5f8', 'd3d2cf7a17a1134184120c66fa1de7d0b0ce88794decbaf7902208f80230b0cf'),
    ('elixir/test/symphony_elixir/plane_state_projection_test.exs', '100644', 9605, '441a77052c02606197ada64cef53bc5255231ba9', '0efa7cd0d32b319b78a8cb703d03557c888086227197f2a702d46c7fd38b3328'),
    ('elixir/test/symphony_elixir/plane_webhook_test.exs', '100644', 27969, 'd86d11d1d4f26c8f279040d4fd675490ac1a35db', '6d486762c6bdcdfd6fbfcb4c495fa3a3cd392f99711adeea9ad9639291312685'),
    ('elixir/test/symphony_elixir/plane_work_control_test.exs', '100644', 3690, '263106074b0588b26374bc2c2740bad7158e40ac', '0bae8b1233196b452cab59743f87910499e430c22c762957bed932b289741c57'),
    ('elixir/test/symphony_elixir/pre_080c_02_production_rate_epoch_characterization_test.exs', '100644', 75687, 'f8c0b8bfc02c9c2ac4a8d02f53d244eb9b8d6fb5', 'af51461619e31635d6a5748e5fec8f8bfe974b15c5afc534e802c676c9aebd91'),
    ('elixir/test/symphony_elixir/pre_080c_production_evidence_acquisition_test.exs', '100644', 81278, 'b200c2123f9b020070d5d42e6a57dc90a072be36', '8b141579e3ac82d7faa519052dea3289dd149b7e379feec3fb3c161613655988'),
    ('elixir/test/symphony_elixir/profile_runtime_test.exs', '100644', 16350, '9d2a62b9ffd07dacbb5aebd0559b22142af89298', '5d42dd89205438d33603ab1b0706492e4ac3fe4b0bdd93cc64637a2489f16a24'),
    ('elixir/test/symphony_elixir/project_contract_evidence_test.exs', '100644', 10880, '130ad98b11ecc272d8593bf51b1ea63cbf8cd29b', '12e11886c77009d9be951f47cb561b111a24dcddddb20af9fcfaed7eedb34775'),
    ('elixir/test/symphony_elixir/provider_dispatch_witness_test.exs', '100644', 4638, 'b09273525af16f72b93f6e48d1c71037780c783d', '4afe6982c2908c3e5d0dc6a0928cea22370fbcbf7c4d015781a4c4052de3acf9'),
    ('elixir/test/symphony_elixir/provider_mutation_envelope_test.exs', '100644', 5099, 'c760447339d418a16bdaf034286fda3bf91f9486', '6b6cecd2af5300d1e7dc4f18e2cc21b27fb9b73cb4e198882efa43008b5b8b03'),
    ('elixir/test/symphony_elixir/provider_project_contract_config_test.exs', '100644', 3177, '24171966b47af05cb444bef53f24f47f1282f66e', 'a6791e196563661a763d19ed3bf450bfe121fa7e1c8eff1adf1f75c9248cf726'),
    ('elixir/test/symphony_elixir/provider_project_contract_test.exs', '100644', 15591, '2651bdbcee6e9f59e2dc74e7940bf1d1d6b43398', '36a5ccc1dcab1a935acb04f808ce9b408405dd453a68d38471bd5ac924503ff2'),
    ('elixir/test/symphony_elixir/rem_h080c_03_backlog_planning_dependency_route_coupling_test.exs', '100644', 32409, 'c136e79b336ea0a6d955b5db208e3c2244c7bac0', 'bb91e951b836ddcdd75f08d1848231f867f08640af70fc0cfd4361f8f634b224'),
    ('elixir/test/symphony_elixir/rem_h080c_candidate_evidence_recovery_test.exs', '100644', 17699, 'd198273761ab02ef0cdba8e6bbbf1be2a6714998', 'e3c7450f30bff0d0c65fbaa4181a860f96ea4bc4692019ac0972fefd602ee968'),
    ('elixir/test/symphony_elixir/rem_h080c_ready_to_merge_review_provenance_test.exs', '100644', 27737, '4306f4c1c3d0fe6c5b2b804c495850709cac6e55', '3b7795317bb5e43f559b9d35cbf376d13eef0835d0e9efbda005b332bece44cf'),
    ('elixir/test/symphony_elixir/rem_hi21_restart_gap_test.exs', '100644', 38334, 'a1a2ec13e97db80317e5b51039bae8fe7c7356be', 'aed7192a8dae6ba8c17b48be210d37eced35dcdcd83a0b8e468c55e5f67e9c1a'),
    ('elixir/test/symphony_elixir/retry_refresh_test.exs', '100644', 7246, '12d1a29722acc5dc8f80582a6e6562c4392494bc', '66dd0ae7adf198c9292d5703a1f2b93c7acc73322871815913113f2daa31b099'),
    ('elixir/test/symphony_elixir/role_prompt_test.exs', '100644', 8865, '17f84d0cd19e58574506775a4ac55e3f6ec7a571', 'd7fdae84957da14dbfabc1612c2fae2142baba94a5c216f3fdc1eb26eed663d8'),
    ('elixir/test/symphony_elixir/runtime_attempt_identity_test.exs', '100644', 15565, '39959ca3f8a3be1e580ba1933297f185f60c0a8b', '46e6a2781cffdc5083d3eaf735af3fd49997ab8549f6aab0b34646cc9c12b76b'),
    ('elixir/test/symphony_elixir/runtime_attempt_production_path_test.exs', '100644', 15603, '45e0b60d2b8308a7601fe99292531f861b3904d2', 'e25c4ee6dbb6ff3e8e1e1da5131b9ff423e8c2825e818728b37e7f15ab6e3fe1'),
    ('elixir/test/symphony_elixir/runtime_attempt_teardown_test.exs', '100644', 28169, '2d075b2881460d642adec225f71fe62030cc4330', 'e4b1bc1b21a5b7742775b2cc693e7160a38f922941926d5888c557c998e8b9a9'),
    ('elixir/test/symphony_elixir/runtime_authority_test.exs', '100644', 19300, 'cb474864f7bf1142eb0bd2bfa067489ad358f468', '896c2b3cfa7a42275d635dd2094664a847efb528e47ac83c10bd145b790ea67b'),
    ('elixir/test/symphony_elixir/runtime_isolation_actual_codex_test.exs', '100644', 31848, '12b629d9bc69e68dd53e71fecda272a59a5ca8d0', '3d7c70606b1a5b8086c4d34fab2c770bfee1213ee6f46e62c965b3f2714cef57'),
    ('elixir/test/symphony_elixir/runtime_isolation_test.exs', '100644', 15706, 'e4605fa70c017c665c872735ad456e73edf3e8ab', 'dc141c3d9c64aa24db66d82c9f9430c5789d9dc6e429f094a76ff8f99c3e7b08'),
    ('elixir/test/symphony_elixir/runtime_transition_authority_binding_test.exs', '100644', 19419, '59a2408d05e38283e946d1473d080552617cf9b0', '1293da958d5cc25f72f7a93a1b4706f4f39bb18d2bd71f3214f040441812ddf7'),
    ('elixir/test/symphony_elixir/source_control_agent_tool_test.exs', '100644', 6263, '45762d185440e4a3b794f7aaf7f99fff442584ab', 'cafeab578066b1f7b7d44e492513a82bd276810679846793d08a6aea9ef4331a'),
    ('elixir/test/symphony_elixir/source_control_candidate_ref_test.exs', '100644', 3135, 'ecf6cbc4a7a5e3bd08ad9cbd0b2772182788928f', '12749523a4d312bbdce675f27b9c623d2eb4ec7d899cde88bca80804b8b197cf'),
    ('elixir/test/symphony_elixir/source_control_coverage_test.exs', '100644', 19449, '742515a50c1747ab8762cca4c394e5cf15244802', '205ebaf43b6b0a07d8ad39e47cf7396638b70b3443e00fddb24529865335f267'),
    ('elixir/test/symphony_elixir/source_control_github_api_test.exs', '100644', 4954, 'cd63c09ae8e5044eefac0dbc02d1288f7e9d3f68', '94814af76ee572fcdee933e0af4868e0d16b78e400a8911cded82bb6bfd01821'),
    ('elixir/test/symphony_elixir/source_control_merge_verification_test.exs', '100644', 24712, 'b47eb8d75cee8a92c3ba9e73deed319101171c42', '375460d38e0643112bec3fa79c8437bfa05f077500123b96682f00efca3605cd'),
    ('elixir/test/symphony_elixir/source_control_test.exs', '100644', 23333, '9c1298f822baa26ff07b0c8bcde41d2b016e0303', 'fc36ea410e8ba240f243caa251dabc695ea4a7d0e981b36d6a52fcf02ee047a4'),
    ('elixir/test/symphony_elixir/specs_check_test.exs', '100644', 2092, 'd8c8de014db4cc5241613e9dbdc5267c14483a02', '35befadab7132a721ded3c3c6147e6ada95982b3b5091f60dfa2c8c4abbd2655'),
    ('elixir/test/symphony_elixir/ssh_test.exs', '100644', 6219, '9edc94f3afb212d3baaf980c5abdf9832d9aea31', 'f158f403a76ca408a9863e2acf784e2988581a7f3b4fef8786a79f315b6453b6'),
    ('elixir/test/symphony_elixir/status_dashboard_snapshot_test.exs', '100644', 11374, '762347285fc7bdf881e624f53fecf5d267dd7c10', '4eceb6cb46e14a549fa95bccd6b7dc6a01d8b8494c255f8d16a83ab16dcd5fa9'),
    ('elixir/test/symphony_elixir/suspension_recovery_test.exs', '100644', 13074, 'b1a0eb9f4f046d3a28ba4b2ebcd9b6cfbf2e9e72', 'c062fb17473b7fc4143e8998a5609b7bba72390909f52695751902273b604b2d'),
    ('elixir/test/symphony_elixir/tracker_capabilities_test.exs', '100644', 19613, '3c70be2b642137a6e9ca16f9e3e38c5d30c616f8', '867b24eefafb2b827c1e04f4f1dfd82dd69fc194692ecb7f436cccab74699cda'),
    ('elixir/test/symphony_elixir/tracker_memory_test.exs', '100644', 11126, '29499e1a76f434dae60352fb72931de6e96b1974', '16786dda8acbb48bba32903bf6757bcc9d0818e4399417cf3b890a4f1a6156d3'),
    ('elixir/test/symphony_elixir/tracker_read_attestation_test.exs', '100644', 8780, '0aa0bfe363971fe97ceedf13a4c5367fb12c20f9', '9bd376234cd0c8cb144660301445037de8c73da07652471a9adb4aef382b6776'),
    ('elixir/test/symphony_elixir/transition_attempt_ledger_test.exs', '100644', 35146, 'f85b7f52609278117bd4b6e104378a2d24886880', 'e0c8890f9861e8f69d38ab14edd6372842db345f35c9d9e904c54919220e30f2'),
    ('elixir/test/symphony_elixir/transition_coordinator_crash_windows_test.exs', '100644', 4733, 'abf783d9b18bcb269c995a96be3afce2f5681f8c', '801c1cf9541dd17a855b372e0b0265057c74f404bc55cc6390510179035cf933'),
    ('elixir/test/symphony_elixir/transition_coordinator_default_path_test.exs', '100644', 31003, 'a0d719aaf28991113dc465cbf6b6a9021c67bf26', 'c2a45a4cd46f937c63f055a14161c058d1d1342893550570f0d086ced50d7b36'),
    ('elixir/test/symphony_elixir/transition_coordinator_test.exs', '100644', 83170, 'e5e80236e77133ad6c3c1e5a3f24a547b50a1749', 'd931a423018f7d8ccf42ab78616ec998782ac9bc709f403f08c7fe46e2ce4892'),
    ('elixir/test/symphony_elixir/transition_freshness_test.exs', '100644', 9165, '3880c80ad96f6ca724fadc576b639ea9c63572ac', '077191258056581fdd3a2008325382ec0d948e58aae8ca8fe8ce5bf1d05d4082'),
    ('elixir/test/symphony_elixir/transition_policy_test.exs', '100644', 8941, '9da90a4c5b1e4de5025a1e9d52cb4df3de7539e8', '2c2d1caf979a2c05ddcbec32889a59be024dfa909cb44307fb40f7dbacc46805'),
    ('elixir/test/symphony_elixir/work_control_assessment_test.exs', '100644', 31955, 'b7539b644036f91e04369d3b54e4cf022a898912', 'ebe96b00409f23961024697dc6f6ae0c23e04adf3817a7088b127480b7ec221c'),
    ('elixir/test/symphony_elixir/work_control_recovery_ledger_test.exs', '100644', 32585, '2698f9c93784a1958b433f59c4daabcbb458d3cc', '25e12c5a04efe449d8c2c03dfd546f5012828ddb7c82cec3f2bc10496d141f18'),
    ('elixir/test/symphony_elixir/work_control_transition_attempt_test.exs', '100644', 20207, '3c4334fb899eae9163eb70f04b28bc384faf13ca', 'bf2a9908299fa314aee4878301bd328bf7cf5742c870948d8213420c19c07537'),
    ('elixir/test/symphony_elixir/work_control_work_item_test.exs', '100644', 10339, '46cd10213562af6ac4a671ddb519864ad385469d', '179d5e79247c2d6224a5f686c7582d5a6c7a0a2f93c7fecdf0b117208fb64508'),
    ('elixir/test/symphony_elixir/work_control_workflow_lifecycle_test.exs', '100644', 11379, 'd9f1c29e8635a1735b1fc8482453258e027fd4c9', 'cfe79b125c5b0a9fc0dc03c7faa9fa6fe361c9041c621933ed8d25da4dc93f96'),
    ('elixir/test/symphony_elixir/workspace_and_config_test.exs', '100644', 145980, '64880f18e2ec1f0782343d0714075983cb45cf55', '7c3a49681bf978950a4a4fb88a8ce6779eea1adc8a051e8412e0e87a9ca394df'),
    ('elixir/test/symphony_elixir/workspace_ownership_ledger_test.exs', '100644', 55274, '160a573cf7df3c94af1560c47ca658cab0a76456', '8f51db54d35d2993dabd5fd95e335de7927caa6344e5e2ff55a4fb5028ff0b25'),
    ('elixir/test/symphony_elixir/workspace_ownership_test.exs', '100644', 2106, 'db66bb836d9cbce449efef426743d8bdc7b62194', '8e37d312de9a080c3e66a1b097167d236e58e1fb466227a5a6cb0e3d0a45c234'),
    ('elixir/test/test_helper.exs', '100644', 278, '130453867b649b3217bd726388cb6121c26b6b6b', '0cee713585fa3b9b03ce689a0e77a012d6121479244b20ef29711b351fa40c9f'),
    ('tools/b1_control.py', '100644', 43946, 'fec9e6dc574dd6acccb875c9ff52f825a4e87250', '344217017d49ade4aec49423981b03520a209ccef3ec072f54be974e03af0654'),
    ('tools/b1_verify.py', '100644', 19370, '2584f5b587dac3f0d75f5fc7e4c24adb1936c929', '403ea2c32398f4c971bf9ef102da5bc0acca0720b0fa389782c122371e249090'),
    ('tools/tests/test_b1_control.py', '100644', 38968, 'df0d8303ae9cbfeaf9b4d24ffdf4992b7c597450', '4fcbf71925471347c2a28f7736e102b156bec9cac37b03532c041aba4de9d0ee'),
    ('tools/tests/test_b1_verify.py', '100644', 15318, 'b2fdfac94d443d6a9fc9150a6a470aa3eb55868f', '1fb5f67eca8b0249a3a602a7ef6130f8e3b5b7446193434705e71032ec512204'),
)

CASE_IDS = {
    "test_absent_release_refuses": "PB01",
    "test_malformed_release_descriptions_refuse": "PB02",
    "test_authority_flags_are_unauthenticated": "PB03",
    "test_well_formed_description_remains_unconfigured": "PB04",
    "test_environment_does_not_supply_authority": "PB05",
    "test_direct_run_results_are_ineligible": "PB06",
    "test_release_refusal_precedes_all_execution_effects": "PB07",
    "test_fixture_access_remains_unavailable": "PB08",
    "test_missing_or_modified_fixture_bytes_refuse": "PB09",
    "test_unknown_fixture_path_cannot_select_input": "PB10",
    "test_custody_assertions_do_not_establish_custody": "PB11",
    "test_fixed_profile_and_cli_selection": "PB12",
    "test_complete_inventory_is_structural_evidence_only": "PB13",
    "test_inventory_rejects_omissions_additions_and_duplicates": "PB14",
    "test_inventory_rejects_changed_preserved_and_inherited_files": "PB15",
    "test_inventory_rejects_aliases_modes_and_identity_changes": "PB16",
    "test_candidate_commit_cannot_be_unchanged_main": "PB17",
    "test_runtime_manifest_drift_or_absence_refuses": "PB18",
    "test_probe_ids_are_finite_without_execution_admission": "PB19",
    "test_profile_declares_no_positive_authentication": "PB20",
    "test_exact_inherited_oversized_entry_is_structural_evidence_only": "PB21",
    "test_oversized_entry_requires_all_five_exact_identity_fields": "PB22",
    "test_unapproved_oversized_entries_refuse_at_every_inventory_input": "PB23",
    "test_unapproved_sizes_remain_bounded": "PB24",
}


def tree_id(entries):
    """Independent Git tree serialization for synthetic inventory expectations."""
    root = {}
    for entry in entries:
        parts = entry["path"].split("/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = (entry["mode"], entry["git_blob"])

    def encode(node):
        items = []
        for name, value in node.items():
            if isinstance(value, dict):
                items.append((name + "/", b"40000 " + name.encode() + b"\0" + encode(value)))
            else:
                mode, blob = value
                items.append((name, mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(blob)))
        payload = b"".join(raw for unused, raw in sorted(items))
        return hashlib.sha1(b"tree " + str(len(payload)).encode() + b"\0" + payload).digest()
    return encode(root).hex()


class PortabilityTests(unittest.TestCase):
    def refuses(self, code, operation, *args):
        with self.assertRaises(policy.PreparationRefusal) as raised:
            operation(*args)
        self.assertEqual(code, raised.exception.code)

    def description(self):
        return policy.UntrustedReleaseDescription(
            profile_id=policy.PROFILE_ID, candidate_commit="1" * 40,
            candidate_tree="2" * 40, source_inventory_sha256="3" * 64,
            runtime_inventory_sha256=policy.RUNTIME_INVENTORY_SHA256,
            attempt_id="4" * 32, suite="verify")

    def inventory(self):
        base = [dict(zip(("path", "mode", "bytes", "git_blob", "sha256"), row))
                for row in BASE_RECORDS]
        package = []
        for path in policy.PACKAGE_PATHS:
            if path in policy.PRESERVED_FILES:
                entry = dict(policy.PRESERVED_FILES[path], path=path)
            else:
                raw = ("synthetic inventory entry: " + path).encode("ascii")
                entry = {"path": path, "mode": "100644", "bytes": len(raw),
                         "git_blob": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
                         "sha256": hashlib.sha256(raw).hexdigest()}
            package.append(entry)
        observed = sorted(base + package, key=lambda item: item["path"])
        inventory = {"schema": "p08-r1a-source-inventory-1",
                     "base_commit": policy.SOURCE_BASE_COMMIT, "base_tree": policy.SOURCE_BASE_TREE,
                     "candidate_commit": None, "candidate_tree": tree_id(observed),
                     "package_files": package, "tree_files": observed}
        return inventory, observed, base

    def test_absent_release_refuses(self):
        self.refuses("EXTERNAL_RELEASE_ABSENT", policy.require_authentic_release)

    def test_malformed_release_descriptions_refuse(self):
        for raw in (b"{", b"[]", b"{}", b'{"suite":"verify","suite":"gate"}', b"x" * 65537):
            with self.subTest(raw=raw[:32]):
                self.refuses("EXTERNAL_RELEASE_MALFORMED", policy.parse_release_description, raw)
        for value in (True, {}, "ACCEPTED", object()):
            self.refuses("EXTERNAL_RELEASE_MALFORMED", policy.require_authentic_release, value)

    def test_authority_flags_are_unauthenticated(self):
        for key, value in (("approved", True), ("status", "INDEPENDENT_STATIC_REVIEW_PASSED"),
                           ("authenticated", True), ("trust_anchor", "/tmp/author-selected")):
            self.refuses("EXTERNAL_RELEASE_UNAUTHENTICATED", policy.parse_release_description,
                         json.dumps({key: value}).encode("ascii"))

    def test_well_formed_description_remains_unconfigured(self):
        description = self.description()
        self.refuses("EXTERNAL_RELEASE_UNCONFIGURED", policy.require_authentic_release, description)
        raw = json.dumps({name: getattr(description, name) for name in description.__dataclass_fields__}).encode()
        parsed = policy.parse_release_description(raw)
        self.assertEqual(description, parsed)
        self.refuses("EXTERNAL_RELEASE_UNCONFIGURED", policy.require_authentic_release, parsed)

    def test_environment_does_not_supply_authority(self):
        with mock.patch.dict(os.environ, {"P08_APPROVED": "1", "P08_RELEASE_PATH": "/tmp/author-review.json"}):
            self.refuses("EXTERNAL_RELEASE_ABSENT", policy.require_authentic_release)

    def test_direct_run_results_are_ineligible(self):
        for value in (None, {"tests": 70, "result": "PASS"}, {"runner_hash": "a" * 64}):
            self.refuses("EXTERNAL_RELEASE_UNAUTHENTICATED", policy.require_execution_receipt, value)

    def test_release_refusal_precedes_all_execution_effects(self):
        with mock.patch.object(policy.ctypes, "CDLL", side_effect=AssertionError("library load")), \
             mock.patch.object(policy.os, "fork", side_effect=AssertionError("fork")), \
             mock.patch.object(Path, "open", side_effect=AssertionError("file open")), \
             mock.patch.object(policy.os, "open", side_effect=AssertionError("fd open")):
            for suite in ("verify", "gate", "portability"):
                with mock.patch.object(sys, "argv", ["runner", "--profile", policy.PROFILE_ID, "--suite", suite]):
                    self.refuses("EXTERNAL_RELEASE_ABSENT", policy.main)
            self.refuses("EXTERNAL_RELEASE_ABSENT", policy.install_write_audit)
            self.refuses("EXTERNAL_RELEASE_ABSENT", policy.fixture_bytes, "BASE_SOURCE_INVENTORY")

    def test_fixture_access_remains_unavailable(self):
        for logical_id in policy.FIXTURE_IDENTITIES:
            self.refuses("EXTERNAL_RELEASE_ABSENT", policy.fixture_bytes, logical_id)

    def test_missing_or_modified_fixture_bytes_refuse(self):
        for logical_id in policy.FIXTURE_IDENTITIES:
            self.refuses("FIXTURE_INPUT_MISSING", policy.check_fixture_bytes, logical_id, None)
            self.refuses("FIXTURE_INPUT_MISMATCH", policy.check_fixture_bytes, logical_id, b"substitute")

    def test_unknown_fixture_path_cannot_select_input(self):
        for value in ("/tmp/fixture.zip", "../BOOTSTRAP_REVIEW_ARCHIVE", "OTHER", True):
            self.refuses("FIXTURE_INPUT_UNKNOWN", policy.fixture_bytes, value)

    def test_custody_assertions_do_not_establish_custody(self):
        for observation in (None, {"mode": "0444", "uid": os.getuid()},
                            {"before_inode": 1, "after_inode": 2}, {"symlink": True},
                            {"writer_uid": 1000, "custodian_uid": 1000}):
            self.refuses("CUSTODY_UNESTABLISHED", policy.require_independent_custody, observation)

    def test_fixed_profile_and_cli_selection(self):
        self.assertEqual(policy.PROFILE_ID, policy.select_profile(policy.PROFILE_ID))
        self.refuses("PROFILE_UNSUPPORTED", policy.select_profile, "ANY_HOST")
        self.refuses("PROFILE_UNSUPPORTED", policy.select_profile, "/tmp/profile.json")
        for argv in (["--probe", "print('anything')"], ["--suite", "verify"],
                     ["--profile", policy.PROFILE_ID, "--suite", "arbitrary"]):
            self.refuses("PROFILE_ARGUMENTS_INVALID", policy.select_request, argv)

    def test_complete_inventory_is_structural_evidence_only(self):
        inventory, observed, base = self.inventory()
        self.assertEqual(395, len(base))
        self.assertEqual(policy.SOURCE_BASE_TREE, tree_id(base))
        self.assertEqual(406, len(observed))
        self.assertIsNone(policy.check_source_inventory(inventory, observed, base))
        self.refuses("EXTERNAL_RELEASE_ABSENT", policy.require_authentic_release)

    def test_exact_inherited_oversized_entry_is_structural_evidence_only(self):
        inventory, observed, base = self.inventory()
        entry = next(item for item in base if item["path"] == ".github/media/symphony-demo.mp4")
        self.assertEqual({
            "path": ".github/media/symphony-demo.mp4", "mode": "100644", "bytes": 30446771,
            "git_blob": "32b1f857f45eb901905ea24355b599fb417f53c5",
            "sha256": "0baa5f6276ea9a790d8072e690c547ed02afb3f95312266d3f27a923d4f58ec1",
        }, entry)
        self.assertEqual({entry["path"]: entry}, policy._entries([entry], 1))
        self.assertIsNone(policy.check_source_inventory(inventory, observed, base))
        self.refuses("EXTERNAL_RELEASE_ABSENT", policy.require_authentic_release)

    def test_oversized_entry_requires_all_five_exact_identity_fields(self):
        unused_inventory, unused_observed, base = self.inventory()
        entry = next(item for item in base if item["path"] == ".github/media/symphony-demo.mp4")
        for field, value in (("path", ".github/media/substitute.mp4"), ("mode", "100755"),
                             ("bytes", 30446770), ("bytes", 30446772),
                             ("git_blob", "a" * 40), ("sha256", "a" * 64)):
            with self.subTest(field=field, value=value):
                changed = dict(entry, **{field: value})
                self.refuses("SOURCE_INVENTORY_INVALID", policy._entries, [changed], 1)

    def test_unapproved_oversized_entries_refuse_at_every_inventory_input(self):
        for target in ("base", "observed", "tree_files", "package_files"):
            with self.subTest(target=target):
                inventory, observed, base = (copy.deepcopy(value) for value in self.inventory())
                entries = {"base": base, "observed": observed,
                           "tree_files": inventory["tree_files"],
                           "package_files": inventory["package_files"]}[target]
                entry = next(item for item in entries if item["path"] != ".github/media/symphony-demo.mp4")
                entry["bytes"] = 16777217
                self.refuses("SOURCE_INVENTORY_INVALID", policy.check_source_inventory,
                             inventory, observed, base)

    def test_unapproved_sizes_remain_bounded(self):
        unused_inventory, unused_observed, base = self.inventory()
        entry = next(item for item in base if item["path"] != ".github/media/symphony-demo.mp4")
        for size in (16777217, 30446771, 30446772, 1 << 128):
            with self.subTest(size=size):
                self.refuses("SOURCE_INVENTORY_INVALID", policy._entries,
                             [dict(entry, bytes=size)], 1)
        for size in (0, 16777216):
            bounded = dict(entry, bytes=size)
            self.assertEqual({bounded["path"]: bounded}, policy._entries([bounded], 1))

    def test_inventory_rejects_omissions_additions_and_duplicates(self):
        for field in ("package_files", "tree_files"):
            for mutation in ("missing", "duplicate", "extra"):
                inventory, observed, base = self.inventory()
                if mutation == "missing":
                    inventory[field].pop()
                elif mutation == "duplicate":
                    inventory[field].append(copy.deepcopy(inventory[field][0]))
                else:
                    entry = dict(inventory[field][0], path="unexpected.py")
                    inventory[field].append(entry)
                self.refuses("SOURCE_INVENTORY_INVALID", policy.check_source_inventory, inventory, observed, base)

    def test_inventory_rejects_changed_preserved_and_inherited_files(self):
        for category in ("preserved", "inherited"):
            inventory, observed, base = self.inventory()
            path = next(iter(policy.PRESERVED_FILES)) if category == "preserved" else base[0]["path"]
            for entry in inventory["tree_files"]:
                if entry["path"] == path:
                    entry["sha256"] = "f" * 64
            self.refuses("SOURCE_INVENTORY_INVALID", policy.check_source_inventory, inventory, observed, base)

    def test_inventory_rejects_aliases_modes_and_identity_changes(self):
        for field, value in (("path", "../alias"), ("path", "/tmp/alias"),
                             ("path", "tools//alias"), ("mode", "120000"),
                             ("bytes", True), ("git_blob", "0" * 40), ("sha256", "not-a-digest")):
            inventory, observed, base = self.inventory()
            inventory["package_files"][0][field] = value
            self.refuses("SOURCE_INVENTORY_INVALID", policy.check_source_inventory, inventory, observed, base)
        for field in ("base_commit", "base_tree", "candidate_tree"):
            inventory, observed, base = self.inventory()
            inventory[field] = "f" * 40
            self.refuses("SOURCE_INVENTORY_INVALID", policy.check_source_inventory, inventory, observed, base)

    def test_candidate_commit_cannot_be_unchanged_main(self):
        inventory, observed, base = self.inventory()
        inventory["candidate_commit"] = policy.SOURCE_BASE_COMMIT
        self.refuses("SOURCE_INVENTORY_INVALID", policy.check_source_inventory, inventory, observed, base)

    def test_runtime_manifest_drift_or_absence_refuses(self):
        self.refuses("RUNTIME_INPUTS_INCOMPLETE", policy.check_runtime_inventory, None, {})
        self.refuses("RUNTIME_INVENTORY_MISMATCH", policy.check_runtime_inventory, b"{}", {})

    def test_probe_ids_are_finite_without_execution_admission(self):
        self.assertEqual({"PB-EXEC-DENY-01", "PB-NET-DENY-01", "PB-WRITE-DENY-01"}, set(policy.PROBE_IDS))
        self.assertFalse(policy.permitted_argv([policy.PYTHON, "-I", "-S", "-B", "-c", "import socket"], "gate"))
        self.assertFalse(policy.permitted_argv(["/usr/bin/p08-unapproved"], "gate"))
        self.refuses("EXTERNAL_RELEASE_ABSENT", policy.require_authentic_release)

    def test_profile_declares_no_positive_authentication(self):
        raw = Path(__file__).with_name("p08-portability-profiles.json").read_bytes()
        profile = json.loads(raw)
        self.assertEqual("UNCONFIGURED", profile["authentication_mechanism"])
        self.assertEqual("UNAVAILABLE", profile["positive_admission_result"])
        self.assertEqual(list(policy.PACKAGE_PATHS), profile["package_paths"])
        self.assertEqual(98, profile["historical_case_count"])
        self.assertNotIn("approved", profile)


if __name__ == "__main__":
    policy.require_authentic_release()
