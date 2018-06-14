import numpy as np
from scipy import stats

def vol_step(X, t, n):
    '''
    compute the volatility score at one step t,
    among the data set X, which is assumed to be 1 dimensional info
    about a population of size n.

    '''
    _X = np.array(X) # X should be list-like but work on a numpy array
    if t >= _X.shape[0]-1:
        raise RuntimeError, "cannot compute index past end of array"

    v = np.abs(_X[t] - _X[t+1]) / float(n)
    return v

def volatility(X, n):
    '''
    compute volatility index for entire experimental series X
    '''
    _X = np.array(X)
    t_max = _X.shape[0]
    _V = np.zeros(t_max-1)

    for t in xrange (t_max-1):
        _V[t] = vol_step(_X, t, n=n)
        #print _V[t], _X[t], _X[t+1]

    return (1.0 / (t_max-1.0) ) * _V.sum()

def _volatility_onefunc(X,n):
    ''' explicit form above; this does the same thing but harder to read! '''
    return np.abs(np.ediff1d(X)).sum() / float(n * len(X)-1)


def compute_threshold(n, onesided=True, pval=0.05, prob=0.5):
    '''
    for binomial test, at what point is it considered a significant
    cllective decision?
    '''
    # compute in a bit of a clunky way - compute all values until we find
    # the first level that exceeds the desired p value.
    ev = np.zeros((n+1,))
    for i, L in enumerate(xrange(n+1)):
        if onesided:
            p = stats.binom.sf(L-1, n, p=prob)
        else:
            raise NotImplementedError
        if p < pval:
            ev[i] = True

    nz = ev.nonzero()[0]
    if len(nz):
        return nz[0]
    else:
        return -1

def cdi(X, n):
    '''
    for a 1d data series X, presenting the number of a total of n animals
    on one side of a binary collective choice assay:
    compute the collective decision index

    '''
    # compute upper and lower thresholds.
    thr_upper = compute_threshold(n)
    thr_lower = n - thr_upper

    _X = np.array(X) # work on a numpy array for logic operators
    coll_decns = ((_X >= thr_upper) | (_X <= thr_lower))

    return coll_decns.mean()

def cdi_for_period(X, n, period_late_mins=10.0, dt=1.0):
    '''
    compute the collective decision index in data series for last plm mins

    X   1d time series of fraction decided to majority side.?
    ##ts  time indications, in sec
    plm duration to look for
    dt  sample interval in X ## (derivable from ts as well)
    '''
    samples_in_decn_period = int(period_late_mins * 60.0 / dt)

    # compute upper and lower thresholds.
    thr_upper = compute_threshold(n)
    thr_lower = n - thr_upper

    _X = np.array(X) # work on a numpy array for logic operators
    coll_decns = ((_X >= thr_upper) | (_X <= thr_lower))

    cd_period = coll_decns[-samples_in_decn_period:]
    return cd_period.mean()



def identify_winner(d, nbees, period_late_mins):
    '''
    make a judgement for L/R as the winning side, based on the data for
    the final args.period_late_mins
    '''
    # verify the most frequent interval among samples
    _dt = np.ediff1d(d[:,0])
    interval = float( stats.mode( _dt[_dt>0]).mode.mean())
    #interval = float(stats.mode(np.ediff1d(d[:,0]))[0])

    # decide which side won.
    samples_in_decn_period = int(period_late_mins * 60.0 / interval)
    late = d[-samples_in_decn_period:, :]
    L = late[:,1]
    R = late[:,2]
    winner = "L"
    if R.mean() > L.mean():
        winner = "R"

    if winner is "L":
        winfrac = d[:,1] / float(nbees)
    else:
        winfrac = d[:,2] / float(nbees)

    return winner, winfrac
