# AMS-DEP V2 Theory-Gap Matrix

## Status

**INDEPENDENT-REVIEW AID — NOT A METHOD SELECTION**

This matrix maps the actual AMS-DEP requirements to what has been verified in
the recovered statistical literature and to the unresolved theoretical work
that an independent reviewer must complete before V2 can be frozen.

Legend:
- **SUPPORTED IN PRINCIPLE** — the method family has theory directly relevant
  to this feature, but AMS-DEP still needs an exact specification.
- **PARTIAL / ADAPTATION REQUIRED** — related theory exists, but not for the
  repository's exact structure.
- **NOT YET ESTABLISHED** — no adequate mapping has been demonstrated for this
  project.
- **PROJECT GOVERNANCE** — not a statistical-theory question; must remain
  unchanged regardless of method.

## Matrix

| AMS-DEP requirement | Dependent Wild Bootstrap | fixed-b HAC | Independent reviewer must resolve |
| --- | --- | --- | --- |
| Serial dependence | **SUPPORTED IN PRINCIPLE.** DWB was designed for dependent time series through dependent multipliers. | **SUPPORTED IN PRINCIPLE.** fixed-b is HAC inference for serially dependent settings. | State exact dependence assumptions required for the chosen method and verify the synthetic DGPs fall within or deliberately stress them. |
| Heteroskedasticity | **PARTIAL / ADAPTATION REQUIRED.** Wild-bootstrap logic is relevant and regression adaptations exist, but the exact AMS-DEP residual/score construction is not frozen. | **SUPPORTED IN PRINCIPLE / FINITE-SAMPLE RISK.** HAC is intended to handle heteroskedasticity/autocorrelation; V1 shows standard reference inference is poorly calibrated in our finite sample. | Specify exact heteroskedasticity treatment and how it is reproduced in calibration. |
| 14-column fixed-regressor design | **PARTIAL / ADAPTATION REQUIRED.** Original Shao paper is broader smooth-function/mean theory; regression-specific follow-on work exists. | **SUPPORTED IN PRINCIPLE.** Kiefer–Vogelsang treat GMM/Wald-style restrictions, but not this exact design. | Demonstrate the chosen theorem/algorithm applies to the deterministic year/state columns and interaction structure. |
| 7 DEP restrictions jointly | **NOT YET ESTABLISHED for exact DWB construction.** | **SUPPORTED IN PRINCIPLE** through multi-restriction Wald/F-type fixed-b theory. | Give exact statistic and bootstrap/reference distribution for 7 restrictions. |
| 4 TIME restrictions jointly | **NOT YET ESTABLISHED for exact DWB construction.** | **SUPPORTED IN PRINCIPLE.** | Give exact statistic/reference procedure. |
| 2 STATE restrictions jointly | **NOT YET ESTABLISHED for exact DWB construction.** | **SUPPORTED IN PRINCIPLE.** | Give exact statistic/reference procedure. |
| Five synthetic continuity segments | **PARTIAL / ADAPTATION REQUIRED.** DWB can represent dependence through multiplier covariance and has irregular-time theory, but reset/independence across declared segments is not specified by the project. | **NOT YET ESTABLISHED** for a single fixed-b law over the project's segmented construction. | Decide whether segment contributions are independent, reset, pooled, stacked, or combined by another justified rule. |
| Future unequal empirical segments | **PARTIAL / ADAPTATION REQUIRED.** Irregular/missing-time results make DWB attractive, but exact regression mapping remains open. | **NOT YET ESTABLISHED** under current review. | Freeze segment treatment before any market-data execution. |
| Exact-hour gaps must not become adjacent rows | **SUPPORTED IN PRINCIPLE** only if multiplier covariance is based on actual time separation or segment boundaries, not compressed index distance. | **NOT YET ESTABLISHED** for project implementation. | Specify actual-time covariance/lag definition and prove gaps cannot be bridged silently. |
| Irregular observations | **SUPPORTED IN PRINCIPLE.** Shao explicitly studies irregular/missing observations, including nonlattice settings, but strongest direct theory varies by statistic. | **PARTIAL / ADAPTATION REQUIRED.** | State which exact irregular-time theorem is being relied on and why it covers the target statistic. |
| Kernel choice | **REQUIRED DESIGN CHOICE.** DWB covariance kernel is part of the method. | **REQUIRED DESIGN CHOICE.** fixed-b reference law depends on kernel. | Freeze kernel prospectively. |
| Bandwidth choice | **REQUIRED DESIGN CHOICE.** DWB bandwidth affects dependence approximation and first-order accuracy. | **REQUIRED DESIGN CHOICE.** b=M/T is central to the reference law and size–power behavior. | Freeze a theory-based rule; do not adopt lag 24 because it looked good after V1. |
| Multiplier distribution | **REQUIRED DESIGN CHOICE.** Gaussian multipliers are convenient but not uniquely required. | Not applicable in basic fixed-b implementation. | If DWB: freeze exact RNG distribution and covariance construction. |
| Null imposition | **NOT YET ESTABLISHED.** | **NOT YET ESTABLISHED** as a bootstrap issue; fixed-b still requires exact restricted-test formulation. | Specify how each DEP/TIME/STATE null is imposed without contaminating nuisance estimation. |
| Nuisance re-estimation | **NOT YET ESTABLISHED.** | Depends on exact fixed-b statistic/implementation. | Freeze whether the full/restricted model is re-estimated in each replicate or critical-value simulation. |
| Studentization | **NOT YET ESTABLISHED.** Follow-on regression literature shows studentization can matter materially. | Built into HAC t/F/Wald construction, but exact project statistic must be frozen. | Specify exact numerator/denominator/covariance calculation. |
| Critical values / p-values | Bootstrap empirical distribution possible, but exact finite-bootstrap convention is **NOT YET FROZEN**. | **NONSTANDARD REFERENCE LAW REQUIRED**; exact critical-value generation for the project's restriction dimensions is not frozen. | Freeze replication count or critical-value simulation/table procedure and +1/tie convention where relevant. |
| Six-test Holm family | **PROJECT GOVERNANCE.** Compatible in principle once six valid p-values exist. | **PROJECT GOVERNANCE.** Compatible in principle once six valid p-values exist. | Preserve six registered slots unless independent review identifies a statistical defect. |
| Cross-asset dependence between BTC/ETH p-values | Holm does not require independence for FWER control, but each marginal p-value must be valid. | Same. | Confirm no implementation change is needed; do not reduce six tests due cross-asset correlation. |
| Heavy-tail null stress | **CALIBRATION REQUIREMENT.** | **CALIBRATION REQUIREMENT.** | Freeze DGP before output. |
| Volatility-break null stress | **CALIBRATION REQUIREMENT.** | **CALIBRATION REQUIREMENT.** | Freeze DGP before output. |
| Endogenous AMS-V1 state construction | **NOT YET ESTABLISHED.** | **NOT YET ESTABLISHED.** | Require a full-pipeline generated-data integrity gate after numerical-core calibration. |
| 744-bar warm-up / row selection | **PROJECT PIPELINE REQUIREMENT.** | **PROJECT PIPELINE REQUIREMENT.** | Verify generated-data pipeline reproduces exact preregistered sample before empirical release. |
| Validation/OOS firewall | **PROJECT GOVERNANCE.** | **PROJECT GOVERNANCE.** | Must remain blocked regardless of V2 method. |
| Strategy/P&L interpretation | **OUT OF SCOPE FOR DEPENDENCE INFERENCE.** | **OUT OF SCOPE.** | Statistical rejection is not strategy authorization. |

## Key deductions

### 1. DWB's strongest practical advantage for this project

DWB has an explicit mechanism for representing temporal dependence through
the covariance of auxiliary multipliers and was designed with irregular
temporal configurations in mind.

That makes it potentially attractive for exact-time gaps.

But that advantage is conditional on implementing time separation correctly.
A DWB implementation that simply generates multiplier dependence by compressed
row index would violate the project's continuity semantics.

### 2. fixed-b's strongest practical advantage for this project

fixed-b directly targets the failure mode in which smoothing/bandwidth is not
negligible but a conventional normal/chi-square reference law ignores it.

It also naturally includes multi-restriction HAC Wald/F-type statistics.

Its largest unresolved difficulty here is segment geometry: the repository
does not yet have a justified definition of a single sample-size/bandwidth
ratio or limiting law for multiple declared continuity segments with unequal
lengths.

### 3. Why lag 24 remains diagnostic only

The V1 diagnostic observed much better null calibration at lag 24 than lag
168.

That observation is useful for diagnosing the V1 failure but cannot become a
V2 primary bandwidth merely by selection.

A V2 bandwidth rule must be derived prospectively from:
- theory;
- a frozen automatic rule; or
- an independently justified test-loss criterion

before the new calibration outcomes are generated.

### 4. Why no method is ready to freeze yet

The missing piece is not broad statistical legitimacy.

Both DWB and fixed-b are established method families.

The missing piece is an exact, reviewable mapping from one of those families
to:
- the 14-column design;
- 7/4/2 restrictions;
- segmented exact-time data;
- later endogenous AMS-V1 state selection;
- finite-sample calibration rules.

Until that mapping is supplied independently, method selection would remain
underspecified.

## Required reviewer closure conditions

Issue #44 can move from
`INSUFFICIENT_EVIDENCE_FOR_DESIGN_FREEZE`
only if the reviewer supplies, for one primary method:

1. an exact theorem/assumption mapping or a defensible finite-sample
   calibration rationale where asymptotic mapping is incomplete;
2. exact statistic;
3. exact segmentation/gap rule;
4. exact kernel/bandwidth or equivalent tuning rule;
5. exact null-imposition/nuisance-estimation procedure;
6. exact critical-value/p-value machinery;
7. exact RNG and replication policy where applicable;
8. exact invalid-case policy;
9. frozen synthetic calibration + holdout design;
10. explicit confirmation that actual BTC/ETH AMS-DEP results remain unseen.

## Current state

**NO METHOD SELECTED.**

**NO V2 EXECUTION AUTHORIZED.**

**EMPIRICAL RELEASE REMAINS BLOCKED BY THE MACHINE-READABLE RELEASE GATE.**
