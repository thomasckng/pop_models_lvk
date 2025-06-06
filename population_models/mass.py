import numpy as np
from numba import njit

# @njit
def smoothing(m, mmin, delta):
    p            = np.zeros(m.shape, dtype = np.float64)
    idx          = (m > mmin) & (m < mmin + delta)
    shifted_mass = (m[idx] - mmin) / delta
    exponent     = 1. / shifted_mass - 1. / (1. - shifted_mass)
    p[idx]       = 1./(1.+np.exp(exponent))
    p[m >= mmin + delta] = 1.
    return p

# @njit
def smoothing_float(m, mmin, delta):
    if m > mmin + delta:
        p = 1.
    elif m < mmin:
        p = 0.
    else:
        shifted_mass = (m - mmin) / delta
        exponent     = 1. / shifted_mass - 1. / (1. - shifted_mass)
        p            = 1./(1.+np.exp(exponent))
    return p

# Primary mass
# @njit
def powerlaw_truncated(m, alpha, mmin, mmax):
    p = m**-alpha * (alpha-1.)/(mmin**(1.-alpha)-mmax**(1.-alpha))
    p[m < mmin] = 0.
    p[m > mmax] = 0.
    return p

# @njit
def _powerlaw_smoothed_unnorm(m, alpha, mmax, mmin, delta):
    return powerlaw_truncated(m, alpha, mmin, mmax)*smoothing(m, mmin, delta)
    
# @njit
def powerlaw_smoothed(m, alpha=3.5, mmax=90, mmin=5, delta=5):
    x  = np.linspace(mmin, mmax, 1000)
    dx = x[1]-x[0]
    n  = np.sum(_powerlaw_smoothed_unnorm(x, alpha, mmax, mmin, delta)*dx)
    return _powerlaw_smoothed_unnorm(m, alpha, mmax, mmin, delta)/n

def broken_powerlaw_smoothed(m, alpha1=3.5, alpha2=2.5, mmax=90, mmin=5, delta=5, b=0.5):
    x  = np.linspace(mmin, mmax, 1000)
    dx = x[1]-x[0]

    mbreak = mmin + b*(mmax - mmin)

    # First part
    p1 = _powerlaw_smoothed_unnorm(x[x < mbreak], alpha1, mmax, mmin, delta)
    # Second part
    p2 = _powerlaw_smoothed_unnorm(x[x >= mbreak], alpha2, mmax, mmin, delta)

    # Combine
    p = np.zeros_like(x)
    p[x < mbreak] = p1
    p[x >= mbreak] = p2

    n = np.sum(p*dx)

    result = np.zeros_like(m, dtype=np.float64)
    mask1 = m < mbreak
    mask2 = ~mask1
    result[mask1] = _powerlaw_smoothed_unnorm(m[mask1], alpha1, mmax, mmin, delta) / n
    result[mask2] = _powerlaw_smoothed_unnorm(m[mask2], alpha2, mmax, mmin, delta) / n
    return result

# @njit
def peak(m, mu, sigma):
    return np.exp(-0.5*(m-mu)**2/sigma**2)/(np.sqrt(2*np.pi)*sigma)

# @njit
def _peak_smoothed_unnorm(m, mu, sigma, mmin, delta):
    return peak(m, mu, sigma)*smoothing(m, mmin, delta)

# @njit
def peak_smoothed(m, mu, sigma, mmin, delta, mmax = 100.):
    x  = np.linspace(mmin, mmax, 1000)
    dx = x[1]-x[0]
    n  = np.sum(_peak_smoothed_unnorm(x, mu, sigma, mmin, delta)*dx)
    return _peak_smoothed_unnorm(m, mu, sigma, mmin, delta)/n

# @njit
def plpeak(m, alpha=3.5, mmin=5, mmax=90, delta=5, mu=35, sigma=5, w=0.2):
    return (1.-w)*powerlaw_smoothed(m, alpha, mmax, mmin, delta) + w*peak_smoothed(m, mu, sigma, mmin, delta)

# mass ratio
q_norm = np.linspace(0,1,1001)[1:]
dq     = q_norm[1]-q_norm[0]

# Primary mass
@njit
def powerlaw_massratio_truncated(q, beta):
    return q**beta * (beta+1.)

@njit
def _powerlaw_massratio_for_normalisation(q, m1, beta, mmin, delta):
    return powerlaw_massratio_truncated(q, beta)*smoothing(m1*q, mmin, delta)

@njit
def _powerlaw_massratio_unnorm(q, m1, beta, mmin, delta):
    return powerlaw_massratio_truncated(q, beta)*smoothing(m1*q, mmin, delta)

@njit
def _powerlaw_massratio(q, m1, beta, mmin, delta):
    norm = np.sum(_powerlaw_massratio_for_normalisation(q_norm, m1, beta, mmin, delta)*dq)
    return _powerlaw_massratio_unnorm(q, m1, beta, mmin, delta)/norm

@njit
def powerlaw_massratio(q, m1, beta, mmin, delta):
    return _powerlaw_massratio_unnorm(q, m1, beta, mmin, delta).flatten()

# LVK
@njit
def _plpeak_lvk_unnorm(m, alpha, mmin, mmax, delta, mu, sigma, weight):
    return ((1.-weight)*powerlaw_truncated(m, alpha, mmin, mmax) + weight*peak(m, mu, sigma))*smoothing(m, mmin, delta)

# LVK
@njit
def plpeak_lvk(m, alpha, mmin, mmax, delta, mu, sigma, weight):
    x  = np.linspace(mmin, mmax, 1000)
    dx = x[1]-x[0]
    n  = np.sum(_plpeak_lvk_unnorm(x, alpha, mmin, mmax, delta, mu, sigma, weight)*dx)
    return _plpeak_lvk_unnorm(m, alpha, mmin, mmax, delta, mu, sigma, weight)/n
