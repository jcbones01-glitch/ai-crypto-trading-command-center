# AMS-DEP V2 Method Literature Audit

## Status

**SOURCE REVIEW FOR DESIGN — NOT METHOD APPROVAL**

This note supports Issue #44. It summarizes primary methodological literature
relevant to the V2 inference choice after AMS-DEP V1's finite-sample
false-rejection failure.

It does not select or approve a V2 method and does not authorize execution.

## 1. Dependent Wild Bootstrap

Primary source:
- Xiaofeng Shao (2010), "The Dependent Wild Bootstrap," Journal of the
  American Statistical Association 105(489), 218–235.

Relevant source claim:
- DWB was proposed for dependent time series as an extension of the wild
  bootstrap;
- it provides a dependence-aware alternative to block bootstrap methods;
- its theoretical development includes distribution approximation and
  variance estimation under dependence;
- the paper explicitly considers finite-sample performance with simulations.

Relevance:
The project needs inference that can tolerate dependence and
heteroskedasticity without relying solely on conventional long-bandwidth HAC
chi-square asymptotics.

Limit:
Shao's general results do not automatically certify this project's exact
14-column regression, 7/4/2 joint restrictions, five-segment calibration
geometry, state interactions, or future AMS-V1 row selection. Those details
must be frozen and tested.

## 2. Wild bootstrap in dynamic / heteroskedastic regression

Relevant literature:
- bootstrap work on autoregressions with conditional heteroskedasticity of
  unknown form reports asymptotic validity for wild-bootstrap variants and
  Monte Carlo improvements over conventional large-sample robust-standard-
  error approximations in the studied settings;
- work on serial-correlation tests in dynamic regression reports poor
  finite-sample control from asymptotic critical values in some
  heteroskedastic settings and examines wild bootstrap as a size-correction
  tool.

Relevance:
This directly supports taking V1's heteroskedastic/GARCH size failure
seriously and considering null-imposed bootstrap inference rather than simply
reusing asymptotic chi-square p-values.

Limit:
These are not exact replicas of AMS-DEP's hypothesis family or design.
Implementation must not borrow a bootstrap recipe without checking its
assumptions.

## 3. Bootstrap HAC tests for OLS

Relevant source:
- Francesco Bravo and Leslie G. Godfrey (2012), "Bootstrap HAC Tests for
  Ordinary Least Squares Regression," Oxford Bulletin of Economics and
  Statistics 74(6), 903–922.

Relevant source claim:
- proposes bootstrap HAC significance tests for OLS under unspecified
  heteroskedasticity/autocorrelation;
- reports Monte Carlo evidence of good finite-sample significance-level
  control and useful power relative to comparison procedures in its studied
  designs.

Relevance:
This is closer to the project's OLS/HAC setting than a generic bootstrap
citation and should be reviewed before freezing V2.

Limit:
The proposed method uses moving-block bootstrap/quasi-estimator machinery;
its suitability for exact-time gaps, multiple declared continuity segments,
and the six-slot AMS-DEP family must be independently determined.

## 4. Fixed-b HAC inference

Primary source:
- Nicholas M. Kiefer and Timothy J. Vogelsang (2005), "A New Asymptotic
  Theory for Heteroskedasticity-Autocorrelation Robust Tests," Econometric
  Theory 21(6), 1130–1164.

Relevant source claim:
- develops HAC robust test asymptotics with bandwidth modeled as a fixed
  proportion of sample size;
- unlike conventional asymptotics, the reference distribution explicitly
  reflects kernel and bandwidth choice.

Relevance:
V1 used a 168-hour Bartlett bandwidth and standard chi-square reference.
Because bandwidth is not negligible relative to each 2,000-hour synthetic
year block, fixed-b theory is a natural comparator.

Limit:
The project's multiple continuity segments and state/year interaction
structure complicate direct use. A fixed-b procedure cannot be adopted from
the paper title/abstract alone.

## 5. Why conventional HAC retuning is not preferred

V1's failure could tempt the project to:
- shorten the bandwidth;
- add prewhitening;
- swap kernels;
- change small-sample scaling.

Those may be legitimate methods in other settings, but choosing them after
seeing V1's results creates a new tuning path. A conventional-HAC V2 therefore
requires the same prospective specification and synthetic gate as a bootstrap
or fixed-b V2.

No post-result bandwidth search is authorized.

## 6. Important caution about bootstrap reliability

Bootstrap methods are not automatically exact or safe.

The literature contains finite-sample and theoretical analyses showing that
wild-bootstrap tests can perform poorly under some designs or require
specific assumptions.

Therefore:
- "bootstrap" is not a release criterion;
- the exact V2 bootstrap construction must be frozen;
- the V1 null DGPs must be retained;
- new heavy-tail/variance-break/gap stresses should be added before results;
- finite-sample size/power must still pass the project's gate.

## 7. Lo / Lo-MacKinlay connection

Andrew Lo and A. Craig MacKinlay's finite-sample methodology is the governing
research principle rather than a claim that their papers prescribe DWB or
fixed-b.

The applicable lesson is:
- examine size and power before empirical use;
- distinguish test calibration from market evidence;
- retain failures;
- do not interpret random-walk/dependence rejection as automatic profit.

The V1 failure is therefore preserved as evidence about the statistical
procedure.

## 8. Review recommendation

Issue #44 should not ask the reviewer merely, "Bootstrap or fixed-b?"

The reviewer should choose an exact method only after evaluating:
- null-imposition correctness;
- dependence/heteroskedasticity assumptions;
- composite joint restrictions;
- continuity segmentation;
- finite-sample calibration feasibility;
- bootstrap/fixed-b tuning choices;
- multiplicity;
- computational burden;
- compatibility with later endogenous AMS-V1 selection.

Preferred review order:

1. Shao DWB and relevant regression adaptations;
2. bootstrap HAC OLS methods;
3. fixed-b HAC theory;
4. conventional HAC revisions only with explicit theory.

No method advances to V2 execution until the complete numerical contract is
frozen.

## 9. Scite verification — 2026-09-19

The connected Scite literature index was used to verify exact bibliographic
records and citation-context evidence for the V2 method candidates.

### Exact primary records verified

- Lo and MacKinlay finite-sample Monte Carlo paper:
  DOI `10.3386/t0066`.
- Shao dependent wild bootstrap:
  DOI `10.1198/jasa.2009.tm08744`.
- Kiefer and Vogelsang fixed-b HAC theory:
  DOI `10.1017/S0266466605050565`.
- Bravo and Godfrey bootstrap HAC for OLS:
  DOI `10.1111/j.1468-0084.2011.00671.x`.
- Sun, Phillips and Jin optimal bandwidth/fixed-b testing:
  DOI `10.1111/j.0012-9682.2008.00822.x`.

### Design implications verified from abstracts/citation context

1. **DWB is not one parameter-free recipe.**
   Follow-on regression work citing Shao explicitly constructs dependent
   multiplier draws using a kernel covariance and a bandwidth parameter.
   Later variants also differ in whether the procedure is residual-based,
   score-based, blockwise, autoregressive, or otherwise adapted to the target
   statistic. Therefore Issue #44 must freeze the exact DWB construction,
   kernel, bandwidth, null imposition and segment behavior before V2 output.

2. **DWB has been extended to regression settings with serial correlation.**
   Djogbenou, Gonçalves and Perron,
   `10.1111/jtsa.12118`, considers bootstrap inference in regressions with
   serially correlated errors and its citation context describes a DWB based
   on smoothed dependent external draws. This supports DWB as a serious
   review candidate, but does not validate AMS-DEP's exact restrictions or
   segmentation.

3. **Bootstrap HAC for OLS is a distinct candidate, not synonymous with DWB.**
   Bravo and Godfrey's abstract explicitly frames the problem as OLS
   coefficient inference under unspecified heteroskedasticity and
   autocorrelation and uses moving-block-bootstrap/quasi-estimator machinery.
   The AMS-DEP reviewer should therefore compare this architecture with DWB
   rather than collapsing both into a generic "bootstrap" option.

4. **Fixed-b changes the reference distribution, not merely the covariance
   estimate.**
   Kiefer–Vogelsang model HAC bandwidth as a fixed proportion of sample size,
   yielding a nonstandard limiting distribution that incorporates smoothing
   choices. Sun–Phillips–Jin likewise studies studentized time-series
   regression tests with truncation lag `M=bT` and nonstandard fixed-b
   limits. This is directly relevant to V1's large-bandwidth/reference-law
   mismatch.

5. **Finite-sample HAC over-rejection is independently documented.**
   Hartigan, `10.1016/j.csda.2017.09.007`, states in its abstract that HAC
   test statistics are known to reject too frequently in finite samples and
   studies alternative covariance estimation. This is consistent with, but
   does not prove the cause of, the project's V1 synthetic failure.

6. **The Lo/Lo-MacKinlay methodological lesson remains calibration first.**
   Scite verifies the NBER working paper record for the finite-sample
   variance-ratio Monte Carlo investigation. The project continues to use its
   methodological principle—measure finite-sample size/power before empirical
   interpretation—without claiming that Lo/MacKinlay prescribed DWB,
   fixed-b, or the AMS-DEP implementation.

### Access limitation

Scite indexed the exact primary records, but full text was not available
through the connected account for the Shao, Kiefer–Vogelsang, and
Bravo–Godfrey articles. The Lo–MacKinlay record resolves to open access, but
Scite did not expose readable indexed body text in this session.

Accordingly, this repository **does not claim formula-level certification**
from Scite for those papers. Exact implementation details still require
either an independently reviewed full-text derivation or another
authoritative accessible source before V2 can be frozen.

### Resulting gate decision

Scite verification strengthens the case that DWB and fixed-b are legitimate
methods to review, but it does **not** resolve the independent design choice.

Issue #44 remains:
`INSUFFICIENT_EVIDENCE_FOR_DESIGN_FREEZE`
until an independent reviewer supplies the exact mathematical V2 contract or
rejects these candidates.

## Bibliographic references

- Lo, A. W. and MacKinlay, A. C. (1988), "The Size and Power of the Variance
  Ratio Test in Finite Samples: A Monte Carlo Investigation," NBER Technical
  Working Paper 66. DOI: 10.3386/t0066.
- Shao, X. (2010), "The Dependent Wild Bootstrap," JASA 105(489), 218–235.
  DOI: 10.1198/jasa.2009.tm08744.
- Kiefer, N. M. and Vogelsang, T. J. (2005), "A New Asymptotic Theory for
  Heteroskedasticity-Autocorrelation Robust Tests," Econometric Theory
  21(6), 1130–1164. DOI: 10.1017/S0266466605050565.
- Bravo, F. and Godfrey, L. G. (2012), "Bootstrap HAC Tests for Ordinary
  Least Squares Regression," Oxford Bulletin of Economics and Statistics
  74(6), 903–922. DOI: 10.1111/j.1468-0084.2011.00671.x.
- Djogbenou, A., Gonçalves, S. and Perron, B. (2015), "Bootstrap Inference in
  Regressions with Estimated Factors and Serial Correlation," Journal of Time
  Series Analysis 36(3), 481–502. DOI: 10.1111/jtsa.12118.
- Hartigan, L. (2018), "Alternative HAC covariance matrix estimators with
  improved finite sample properties," Computational Statistics & Data
  Analysis 119, 55–73. DOI: 10.1016/j.csda.2017.09.007.
- Sun, Y., Phillips, P. C. B. and Jin, S. (2008), "Optimal Bandwidth
  Selection in Heteroskedasticity–Autocorrelation Robust Testing,"
  Econometrica 76(1), 175–194. DOI: 10.1111/j.0012-9682.2008.00822.x.

Additional dynamic-regression/wild-bootstrap literature should be checked in
full before its exact algorithms are incorporated. Bibliographic, abstract
and citation-context review is not treated as formula certification.
