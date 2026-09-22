"""V2 engineering primitives. No calibration/market runner or release approval.

All inputs are explicit in-memory arrays. The numerical core cannot establish
input provenance. Only deterministic engineering fixtures are authorized now.
"""
from dataclasses import dataclass
import numpy as np
from scipy.linalg import cholesky_banded
from .dependence_statistics import InferenceError, RESTRICTIONS, _hour_grid, _integer, _vector

BOOTSTRAP_DRAWS = 4999
EXPERIMENT_VERSION = 2


def parzen(x):
    x = np.abs(np.asarray(x, dtype=np.float64))
    if not np.isfinite(x).all():
        raise InferenceError('nonfinite kernel coordinate')
    return np.where(x <= .5, 1-6*x*x+6*x*x*x,
                    np.where(x < 1, 2*(1-x)**3, 0.))


def segment_geometry(hours, segments):
    h = _hour_grid(hours, len(hours))
    seg = np.asarray(segments)
    if len(h) == 0 or seg.ndim != 1 or len(seg) != len(h) or seg.dtype.kind not in 'iu':
        raise InferenceError('aligned nonempty integer segments required')
    boundaries = np.r_[0, np.flatnonzero(seg[1:] != seg[:-1])+1, len(h)]
    if len(np.unique(seg[boundaries[:-1]])) != len(boundaries)-1:
        raise InferenceError('segment IDs may not recur')
    result = []
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        if int(h[end-1])-int(h[start])+1 > 100000:
            raise InferenceError('segment span exceeds 100000 hours')
        result.append((int(start), int(end), max(2., float(end-start)**.2)))
    return h, result


class ParzenGeometry:
    """Compact exact-hour kernel and segment-reset Gaussian square roots.

    Banded storage is in row-index diagonals, but every value is evaluated
    using actual hour separation. Missing hours are never compressed.
    """
    def __init__(self, hours, segments):
        self.hours, self.blocks = segment_geometry(hours, segments)
        self.bands, self.factors = [], []
        for start, end, ell in self.blocks:
            h = self.hours[start:end]
            n = end-start
            width = min(n-1, int(np.ceil(ell))-1)
            band = np.zeros((width+1,n))
            band[0] = 1.
            for d in range(1,width+1):
                band[d,:n-d] = parzen((h[d:]-h[:-d])/ell)
            # No jitter, eigenvalue clipping, ridge or silent PSD projection.
            try:
                factor = cholesky_banded(band, lower=True, check_finite=True)
            except np.linalg.LinAlgError as exc:
                raise InferenceError('multiplier covariance factorization failed') from exc
            self.bands.append(band)
            self.factors.append(factor)

    def meat(self, scores):
        scores = np.asarray(scores,dtype=np.float64)
        if scores.ndim != 2 or len(scores) != len(self.hours) or not np.isfinite(scores).all():
            raise InferenceError('finite aligned score matrix required')
        out = np.zeros((scores.shape[1],scores.shape[1]))
        for (start,end,_), band in zip(self.blocks,self.bands):
            g = scores[start:end]
            out += g.T@g
            for d in range(1,len(band)):
                cross = (g[d:]*band[d,:len(g)-d,None]).T@g[:-d]
                out += cross+cross.T
        if not np.isfinite(out).all():
            raise InferenceError('nonfinite Parzen meat')
        return (out+out.T)/2

    def multipliers(self, seed_path):
        """One independent SeedSequence per segment after the draw coordinate."""
        path = [_integer(v,'seed coordinate') for v in seed_path]
        if len(path) != 7 or path[1] != EXPERIMENT_VERSION:
            raise InferenceError('expected root/version/DGP/outer/asset/hypothesis/draw')
        out = np.empty(len(self.hours))
        for segment_index, ((start,end,_), factor) in enumerate(zip(self.blocks,self.factors)):
            rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(path+[segment_index])))
            z = rng.standard_normal(end-start)
            w = factor[0]*z
            for d in range(1,len(factor)):
                w[d:] += factor[d,:len(z)-d]*z[:-d]
            out[start:end] = w
        return out


@dataclass(frozen=True)
class Fit:
    coefficients: np.ndarray
    covariance: np.ndarray
    residuals: np.ndarray


class FixedOLS:
    """Cache only X-dependent SVD algebra; refit beta/residuals/HAC each draw."""
    def __init__(self, design):
        x = np.asarray(design,dtype=np.float64)
        if x.ndim != 2 or not np.isfinite(x).all():
            raise InferenceError('finite design matrix required')
        self.n,self.p = x.shape
        if self.n <= self.p or self.p == 0:
            raise InferenceError('OLS needs more rows than columns')
        self.scales = np.linalg.norm(x,axis=0)
        if np.any(self.scales <= 0) or not np.isfinite(self.scales).all():
            raise InferenceError('invalid column norm')
        self.x = x/self.scales
        u,s,vt = np.linalg.svd(self.x,full_matrices=False)
        if s[-1] <= 1e-12*s[0] or s[0]/s[-1] > 1e8:
            raise InferenceError('unidentified or ill-conditioned design')
        self.solver = (vt.T/s)@u.T
        self.bread = (vt.T/s**2)@vt

    def fitted(self, target):
        y = _vector(target,'target')
        if len(y) != self.n:
            raise InferenceError('unaligned target')
        b = self.solver@y
        residual = y-self.x@b
        if not np.isfinite(b).all() or not np.isfinite(residual).all():
            raise InferenceError('nonfinite OLS output')
        return b,residual

    def fit(self, target, geometry):
        b,u = self.fitted(target)
        meat = geometry.meat(self.x*u[:,None])
        cov = (self.bread@meat@self.bread)*self.n/(self.n-self.p)
        cov /= self.scales[:,None]*self.scales[None,:]
        cov = (cov+cov.T)/2
        if not np.isfinite(cov).all():
            raise InferenceError('nonfinite covariance')
        eig = np.linalg.eigvalsh(cov)
        if eig[0] < -1e-12*np.max(np.abs(eig)) or np.any(np.diag(cov)<0):
            raise InferenceError('invalid covariance')
        return Fit(b/self.scales,cov,u)


def wald(fit, hypothesis):
    if hypothesis not in RESTRICTIONS:
        raise InferenceError('unregistered restriction')
    ix = RESTRICTIONS[hypothesis]
    if len(fit.coefficients) != 14:
        raise InferenceError('registered 14-column model required')
    cov = fit.covariance[np.ix_(ix,ix)]
    b = fit.coefficients[list(ix)]
    eig = np.linalg.eigvalsh(cov)
    if eig[0] <= 0 or eig[-1]/eig[0] > 1e12:
        raise InferenceError('singular or ill-conditioned restriction covariance')
    value = float(b@np.linalg.solve(cov,b))
    if not np.isfinite(value) or value < 0:
        raise InferenceError('invalid Wald statistic')
    return value


def restricted_components(design,target,geometry,hypothesis):
    if hypothesis not in RESTRICTIONS:
        raise InferenceError('unregistered restriction')
    x = np.asarray(design,dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 14:
        raise InferenceError('registered 14-column model required')
    keep = [i for i in range(14) if i not in RESTRICTIONS[hypothesis]]
    # Selecting free columns implements the stated zero restrictions exactly;
    # it is not dropping unidentified columns from the unrestricted model.
    reduced = FixedOLS(x[:,keep])
    _, residual = reduced.fitted(target)
    fitted = np.asarray(target,dtype=float)-residual
    centered = residual.copy()
    for start,end,_ in geometry.blocks:
        centered[start:end] -= centered[start:end].mean()
    return fitted,centered


def count_exceedances(observed, statistics):
    """None/nonfinite/negative marks an invalid requested draw; never redraw."""
    if not np.isfinite(observed) or observed < 0:
        raise InferenceError('invalid observed statistic')
    invalid=exceed=0
    for value in statistics:
        if value is None or not np.isfinite(value) or value < 0:
            invalid += 1
            exceed += 1
        elif value >= observed:
            exceed += 1
    return exceed,invalid


def bootstrap_p_value(observed, statistics):
    if len(statistics) != BOOTSTRAP_DRAWS:
        raise InferenceError('exactly 4999 requested draws required')
    exceed,invalid = count_exceedances(observed,statistics)
    return {'raw_p':(1+exceed)/(BOOTSTRAP_DRAWS+1), 'invalid_draws':invalid,
            'requested_draws':BOOTSTRAP_DRAWS, 'invalid_fraction':invalid/BOOTSTRAP_DRAWS}


def engineering_fixture(design,target,hours,segments,hypothesis,draws=8):
    """Bounded code/oracle exercise, not a calibration sample or p-value."""
    draws = _integer(draws,'engineering draws',1)
    if draws > 32:
        raise InferenceError('engineering fixture limited to 32 draws')
    geometry = ParzenGeometry(hours,segments)
    model = FixedOLS(design)
    observed = wald(model.fit(target,geometry),hypothesis)
    fitted,residual = restricted_components(design,target,geometry,hypothesis)
    stats=[]
    for b in range(draws):
        weights=geometry.multipliers([2026092001,2,0,0,0,tuple(RESTRICTIONS).index(hypothesis),b])
        try:
            stats.append(wald(model.fit(fitted+residual*weights,geometry),hypothesis))
        except (InferenceError,np.linalg.LinAlgError):
            stats.append(None)
    exceed,invalid=count_exceedances(observed,stats)
    return {'classification':'ENGINEERING_ONLY_NOT_CALIBRATION','p_value':None,
            'draws':draws,'invalid_draws':invalid,'exceedances':exceed}
