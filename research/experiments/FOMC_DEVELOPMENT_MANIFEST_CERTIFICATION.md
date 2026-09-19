# FOMC Development Manifest Certification

## Certification status

**CERTIFIED FOR DEVELOPMENT-ONLY DESCRIPTIVE RESEARCH**

This certification freezes the Federal Reserve FOMC statement event set before any crypto return analysis is performed.

## Evidence

- Source workflow: `Gate 2 FOMC Development Manifest`
- Workflow run: `35424288287`
- Source commit: `74e3c390ff384858a62b21ae27ea354026033e9f`
- Workflow conclusion: `success`
- Artifact ID: `10577972982`
- Artifact name: `gate2-fomc-development-manifest`
- Artifact digest: `sha256:7785634aed70e42840f32ee46acb387c72a1bb181345c104c6d9494e5d182e61`
- Full manifest JSON SHA-256: `e0fd8e03e420c9b170ce48265e08157ff22c0fb0fbd9e16019bd69bb902ad62f`
- Frozen compact manifest SHA-256 at construction: `e829ac54700bdd46a8faf4de631684aaa0b126c25910a34c203f4ef2645be2eb`

## Frozen event dataset

- Protocol: `event-dataset-v1`
- Dataset ID: `fd5021aa2ff2f01ceaa2f5e060d08db8e0825cc27e1bde147e8eb5948ee14e11`
- Record count: `37`
- First market availability: `2017-09-20T18:00:00Z`
- Last market availability: `2021-12-15T19:00:00Z`
- Development window: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`
- Validation/OOS accessed: `False`

The official indexes yielded 42 total FOMC-statement links across calendar years 2017–2021. Five 2017 statements precede the pre-existing Development start, leaving 37 eligible events. Per-index discovery was 8 / 8 / 8 / 10 / 8 for 2017 / 2018 / 2019 / 2020 / 2021.

## Scope

This dataset is authorized only for Development-period descriptive research and future preregistered Development hypotheses.

It does **not** authorize:
- Validation access;
- locked OOS access;
- policy-stance or sentiment labels;
- retrospective LLM classification of statement text;
- a directional trading strategy;
- paper trading;
- live trading;
- leverage or exchange credentials.

## Important source-vintage limitation

The manifest hashes the Federal Reserve pages as retrieved during this certification run. Those hashes make the present archive representation auditable, but they do not prove that every byte of each current page is identical to the byte representation visible at the historical release instant.

Therefore Foundation V1 may safely use the certified **release timestamps and event identities** for descriptive event timing. Historical text classification, NLP sentiment, or LLM interpretation remains locked until text-vintage semantics are separately reviewed and certified.

## Next permitted step

Preregister a Development-only descriptive event study before examining crypto returns around these 37 events. The event study must use this frozen event set and the already certified BTCUSDT/ETHUSDT hourly Development data. It must not create or promote a trading strategy.
