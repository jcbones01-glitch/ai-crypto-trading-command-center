# Research Governance Implementation Pack — 2026-09-19

Status: **DESIGN SPECIFICATION / NO NEW AUTHORIZATION**

This document converts the 2026-09-19 Deep Research findings into concrete future repository additions.

Nothing in this file changes current AMS-DEP permissions.

## Priority architecture additions

### P0 — Research Object Registry

Proposed future paths:
- `docs/RESEARCH_OBJECT_REGISTRY.md`
- `schemas/research_object.schema.json`

Purpose:
- canonical research identity;
- hypothesis/mechanism lineage;
- specification hashes;
- code SHAs;
- dataset permissions;
- protected-sample exposure;
- test-family identity;
- approval status;
- artifact linkage.

Example:

```json
{
  "schema_version": "1.0",
  "research_object_id": "AMS-EXAMPLE-001-V1",
  "parent_object_id": null,
  "type": "HYPOTHESIS",
  "status": "PROPOSED",
  "title": "Example only",
  "mechanism": "Pre-specified economic mechanism",
  "hypothesis": "Pre-specified falsifiable statement",
  "test_family_id": "FAMILY-001",
  "preregistration": {
    "spec_hash": null,
    "created_at_utc": "2026-09-19T00:00:00Z"
  },
  "data_permissions": ["SYNTHETIC_ONLY"],
  "protected_sample_exposure": [],
  "implementation": {
    "git_sha": null,
    "code_hash": null
  },
  "statistical_plan": {
    "primary_metric": null,
    "alpha": 0.05,
    "multiplicity_method": "HOLM"
  },
  "authorization_scope": [],
  "approvals": [],
  "artifacts": []
}
```

Required invariant:
A result cannot exist without a registered object.

## P0 — Search / Exposure Ledger

Proposed future paths:
- `docs/SEARCH_EXPOSURE_LEDGER.md`
- `schemas/exposure_event.schema.json`

Every generated or tested idea should record:
- timestamp;
- actor/agent identity;
- research object;
- hypothesis family;
- variant identity;
- parameterization;
- dataset accessed;
- partition accessed;
- protected data exposure;
- result observed;
- whether downstream work was influenced;
- disposition.

Required invariant:
Failed, abandoned and duplicate hypotheses remain part of the recorded search budget.

## P0 — Feature Registry

Proposed future paths:
- `docs/FEATURE_REGISTRY.md`
- `schemas/feature.schema.json`

Example:

```yaml
schema_version: "1.0"
feature_id: "FEATURE_EXAMPLE_V1"
status: "PROPOSED"

source:
  dataset_id: "DATASET_ID"
  fields: ["raw_field"]
  dataset_hash: null
  provider: null

definition:
  formula: "explicit_formula"
  units: "unit"
  lookback: "8h"
  transformation: "none"

point_in_time:
  availability_timestamp_field: "published_at"
  minimum_lag: "0s"
  forward_fill: false
  staleness_limit: "8h"

missing_data:
  policy: "DROP"
  imputation_authorized: false

research:
  mechanism: "Why this feature might contain information"
  authorized_uses: ["SYNTHETIC_TEST"]
  prohibited_uses: ["VALIDATION", "OOS", "LIVE"]

implementation:
  parser_version: null
  code_sha: null

certification:
  status: "UNCERTIFIED"
  reviewer: null
```

Required invariant:
No predictive feature enters research before its point-in-time availability and provenance are defined.

## P0 — Multiple-Testing Control Policy

Proposed path:
- `docs/MULTIPLE_TESTING_CONTROL.md`

The policy should require:
- explicit hypothesis-family registration;
- total tested-variant accounting;
- confirmatory vs exploratory classification;
- FWER correction for confirmatory families where appropriate;
- FDR reporting for exploratory families;
- raw and adjusted significance reporting;
- search-history preservation;
- holdout exposure accounting;
- trial-aware performance diagnostics;
- independent replication before promotion.

### CI-testable governance metrics

| Control | Metric | Desired condition |
|---|---|---|
| Search accounting | tested / registered hypotheses | 1.0 |
| Unauthorized exposure | protected reads | 0 |
| Confirmatory multiplicity | adjusted primary p-values | required |
| Exploratory multiplicity | q-values | reported |
| Search inflation | trials / mechanisms / variants | always reported |
| Null calibration | false discoveries under synthetic null | within declared budget |
| Holdout integrity | pre-release exposure count | 0 |
| Replication | independent replication status | explicit |
| Variant dependence | pairwise correlation | reported |
| Selection collapse | discovery vs OOS effect ratio | monitored |

## P0 — Agent Security Model

Proposed future paths:
- `docs/AGENT_SECURITY_MODEL.md`
- `policies/agent_capabilities.yaml`

Core rule:

[
oxed{	ext{Researcher} 
eq 	ext{Approver} 
eq 	ext{Risk Manager} 
eq 	ext{Executor}}
]

This separation must be technical, not merely prompt-based.

### Capability matrix

| Capability | Hypothesis Agent | Skeptic | Auditor | Risk Agent | Execution Agent |
|---|---:|---:|---:|---:|---:|
| Read public literature | Yes | Yes | Yes | Optional | No |
| Read Development summaries | Yes | Yes | Yes | Yes | No |
| Read protected Validation/OOS | No by default | No by default | Explicit release only | Authorized monitoring only | No |
| Draft hypotheses | Yes | Falsification only | No | No | No |
| Change frozen thresholds | No | No | No | No | No |
| Approve own evidence | No | No | No | No | No |
| Submit orders | No | No | No | No | Future bounded authority only |

### Security properties

Future implementation should use:
- default-deny permissions;
- separate credentials/scopes;
- immutable audit events;
- spec-hash binding;
- explicit release tokens;
- expiration/revocation;
- no hidden protected-data access;
- no shared all-powerful agent credential.

## P1 — Governance Validators

Proposed path:
- `src/research_governance/`

Future validators should enforce:
- schema validity;
- object ID uniqueness;
- immutable lineage;
- valid spec/code hashes;
- authorization scopes;
- append-only exposure history;
- no unauthorized partition access;
- no promotion without required approvals.

No P1 code should be wired into frozen AMS-DEP execution without a separate review.

## P1 — Null-Strategy Research-Process Battery

Purpose:
Test the scientific process, not just strategies.

Procedure:
1. Generate deterministic zero-edge synthetic strategies/signals.
2. Submit them through the same search and ranking process.
3. Apply the same multiple-testing machinery.
4. Apply the same promotion rules.
5. Measure false promotions.
6. Fail the governance test if false discovery exceeds the declared error budget.

This should eventually become a CI or certification test for agentic research tooling.

## P1 — Edge-Health Contract

Proposed path:
- `docs/EDGE_HEALTH_ENGINE.md`

Before any future paper/live strategy authorization, predefine prospective monitoring for:
- net returns;
- spread/fees/slippage;
- funding/financing;
- drawdown;
- turnover;
- exposure;
- tail losses;
- signal frequency;
- fill quality;
- latency;
- feature drift;
- market-state distribution;
- strategy-vs-validation divergence.

Default allowed actions:
- MAINTAIN
- REDUCE
- SUSPEND
- RETIRE

Not automatically authorized:
- retune;
- increase leverage;
- modify model;
- re-enable suspended strategy;
- treat live data as clean OOS after adaptation.

## P2 — Minimal Exchange Simulator Specification

Proposed path:
- `docs/MINIMAL_EXCHANGE_SIMULATOR.md`

Initial scope should remain deliberately limited:
- bid/ask spread;
- maker/taker fee model;
- deterministic slippage configuration;
- available depth;
- partial fills;
- rejection/cancellation;
- latency;
- funding where relevant;
- venue-specific contract metadata.

Later only:
- queue position;
- learned impact;
- adversarial agents;
- detailed liquidation mechanics;
- cross-venue routing.

No exchange simulator should be interpreted as evidence that simulator-trained RL will transfer to live markets.

## Reproducibility contract for future ML / AI research

Any future ML/LLM/RL experiment should record at minimum:

### Data
- dataset ID/version/hash;
- exact date range;
- universe construction;
- survivorship policy;
- timestamp alignment;
- point-in-time availability;
- missing data;
- exchange outages;
- delistings/contract changes.

### Model
- algorithm;
- hyperparameters;
- random seed;
- library versions;
- model checkpoint;
- training code SHA.

### Validation
- train/validation/OOS partitions;
- purge/embargo rules where needed;
- search budget;
- hyperparameter trials;
- model-selection criterion;
- multiplicity adjustment.

### LLM-specific
- provider/model/version;
- release date;
- known cutoff where available;
- system/user prompts;
- temperature/sampling parameters;
- retrieval corpus;
- retrieval timestamps;
- tool permissions;
- web access;
- output parser/version.

### Execution
- spread;
- fees;
- slippage;
- impact;
- latency;
- fill assumptions;
- funding/financing;
- order type;
- turnover.

### Results
- gross metrics;
- net metrics;
- confidence intervals;
- regime/state breakdown;
- ablations;
- baseline comparisons;
- robustness tests;
- failed variants;
- artifact hashes.

## Required baselines for future ML / AI research

Complex models should not be evaluated in isolation.

Minimum future baseline family should normally include, when scientifically relevant:
- no-signal/null strategy;
- buy-and-hold or passive benchmark;
- simple historical-mean/naive forecast;
- linear/regularized regression;
- simple momentum/reversal baseline;
- tree/boosting baseline for tabular features;
- cost-unaware vs cost-aware comparison;
- model without the proposed new feature;
- model without LLM/agent component;
- fixed-rule execution baseline for RL execution.

A complex model should demonstrate incremental value over simpler baselines **net of costs**.

## Economic significance contract

Future research should distinguish:

[
	ext{Statistical significance}
]

from

[
	ext{Economic significance}.
]

A result should not be called economically useful unless the expected improvement survives:
- fees;
- bid/ask spread;
- slippage;
- impact;
- funding/financing;
- turnover;
- capacity;
- tail risk;
- operational constraints.

Where applicable:

[
	ext{Net Edge}
=
	ext{Gross Forecast Value}
-
	ext{Implementation Costs}
-
	ext{Risk Penalties}.
]

## Cybersecurity / operational-resilience requirements for future execution

Before any broker/exchange connectivity is considered, specify:
- isolated API credentials;
- least privilege;
- withdrawal disabled where possible;
- secret rotation;
- kill switch;
- rate limits;
- position/notional caps;
- order-frequency caps;
- stale-data halt;
- exchange-outage halt;
- model-health halt;
- dependency pinning;
- signed releases;
- supply-chain scanning;
- immutable incident logs;
- recovery procedure;
- manual emergency stop.

Agentic systems additionally require:
- prompt-injection resistance;
- untrusted-data boundaries;
- tool allowlists;
- structured outputs;
- no secret exposure to language models;
- deterministic validation before actions.

## Recommended implementation order

### Phase 0 — documentation only
Current document set and evidence ledger.

### Phase 1 — governance schemas
- Research Object Registry
- Search/Exposure Ledger
- Feature Registry
- Multiple-Testing Policy
- Agent Security Model

### Phase 2 — validators
- schema validation;
- append-only exposure history;
- authorization validation;
- null-strategy research-process tests.

### Phase 3 — research automation
Proposal-only:
- literature agent;
- hypothesis agent;
- skeptic;
- experiment agent;
- statistical auditor.

No protected-data or execution permission.

### Phase 4 — execution-science preparation
- edge-health contract;
- exchange-simulator specification;
- deterministic paper-execution research.

### Phase 5 — portfolio/risk/execution
Only after separate evidence-based authorization.

## Explicit non-goals now

Do not build yet:
- unrestricted autonomous trader;
- production RL trader;
- self-modifying strategy loop;
- live broker adapter;
- live leverage optimizer;
- large agent swarm;
- unrestricted LLM market-data/web agent with order access;
- production HFT/order-book engine.

## Repository firewall

All future work inspired by this pack must preserve:

```text
NO change to frozen AMS-DEP specifications
NO threshold weakening
NO protected Validation/OOS exposure
NO unauthorized market-data execution
NO strategy P&L without release
NO paper/live trading without release
NO retroactive deletion of failed research
NO treating green software tests as research approval
```
