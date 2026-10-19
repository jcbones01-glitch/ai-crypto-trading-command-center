# Research Library Integration Index

Status: **DOCUMENTATION / GOVERNANCE CONTEXT ONLY — NO NEW RESEARCH OR TRADING AUTHORIZATION**

This index registers the completed AI Trading Research Playbook review packages with the repository without changing any frozen AMS-DEP specification, release gate, protected-data permission, or trading authority.

## Authority boundary

The repository's current machine-readable AMS-DEP release gate remains controlling. This research library:

- does not authorize synthetic holdout execution;
- does not authorize BTC/ETH AMS-DEP market-data execution;
- does not authorize Validation/OOS access;
- does not authorize strategy P&L;
- does not authorize paper or live trading;
- does not modify frozen V2 code, DGPs, seeds, thresholds, multiplicity, bandwidth, or invalid-draw policy.

Literature and source review can motivate future proposals, but only a separate prospective research object and the applicable release process can authorize an experiment.

## Master playbook

The current master source is `AI_Trading_Research_Playbook_v1.2.md` in the ChatGPT project sources. Its SHA-256 fingerprint is recorded in the machine-readable registry below. The full playbook is not duplicated into this first repository integration commit.

## Completed review packages

| ID | Project-source artifact | Completion meaning |
| --- | --- | --- |
| R01 | `R01_Bootstrap_Applicability_Review.md` | Exact-method applicability reviewed; unresolved theory retained; frozen V2 not changed |
| R02 | `R02_Order_Flow_Replication_and_Data_Feasibility_Review.md` | Cont-style OFI replication/data requirements reviewed; predictive usefulness unresolved |
| R03 | `R03_Exchange_Fragmentation_Review.md` | Fragmentation/executability confounds reviewed; current arbitrage not established |
| R04 | `R04_Crypto_Carry_and_Market_Stress_Review.md` | Dated-futures basis research design reviewed; incremental predictive value unresolved |
| R05 | `R05_Selection_and_Backtest_Overfitting_Review.md` | Project-wide selection/search accounting reviewed; implementation gaps retained |
| D01-D03 | `D01_D03_Data_Source_Feasibility_Review.md` | Initial ALFRED/Coin Metrics feasibility reviewed; source-specific PIT/license/access issues retained |
| OA | `Oxford_Analytica_Intake_Geopolitical_Scenario_Framework.md` | Public-source geopolitical/regulatory scenario governance framework; no proprietary OA report reviewed |
| V01 | `V01_MIT_Adaptive_Markets_Course_Review.md` | MIT/Lo Adaptive Markets source extraction; no strategy validation |
| V02 | `V02_LSE_Demystifying_Cryptocurrency_Review.md` | Makarov/LSE market-structure extraction; R03 corroboration only |
| V03 | `V03_MIT_Finance_AI_and_Human_Behavior_Review.md` | AI decision-support/human-oversight extraction; no autonomous capital authority |

## Machine-readable registry

`../../research/intake/research_source_registry_v1.json` records package status, project-source artifact names, source-file SHA-256 fingerprints, unresolved boundaries, and authorization scope.

The registry is an **intake/catalog artifact**, not a release gate and not a substitute for preregistration.

## Next integration phase

Future implementation should proceed only after re-checking the current repository state and deduplicating against existing architecture/governance work. Candidate future artifacts already identified by the completed reviews include:

- global research search/exposure ledger;
- research object registry;
- point-in-time data/feature registry;
- source-specific data qualification objects;
- bounded proposed experiments for R02/R03/R04 only after separate approval;
- capability-based agent permissions.

Do not implement those merely because they appear in this index. Each should be separately scoped against the current repository and active release gates.
