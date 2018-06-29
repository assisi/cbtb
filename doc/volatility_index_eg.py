import numpy as np

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


# define some examples
n = 12

# oscillating signal -- maximal
Losc1 = [n if i % 2 ==0 else 0 for i in xrange(18)]
# oscillating more slowly
Losc2 = [n if i % 4 < 2 else 0 for i in xrange(50)]

# Smaller oscillations, every 2
Losc3 = [n if i % 4 < 2 else n/2 for i in xrange(20)]

# a single transition, either slowly...
L1ramp = n * np.ones(50,)
L1ramp[0:n+1] = range(0,n+1)
# or quickly...
L1step = n * np.ones(50,)
L1step[25:] = 0

# two transitions
L2 = np.zeros(50,)
L2[0:20] = n
L2[20:25] = 0
L2[25:] = n

# constant readings
Cn = n * np.ones(50,)
Cn2 = n/2 * np.ones(50,)
C0 = 0  * np.ones(50,)

print "======\nMany changes in population decision give high metric values:"
print "{:.4f}\t".format(volatility(Losc1, n)), "n 0 n 0 ...    : Full swing every step"
print "{:.4f}\t".format(volatility(Losc2, n)), "n n 0 0 n n ...: Full swing every other step"
print "{:.4f}\t".format(volatility(Losc3, n)), "n n n/2 n/2 n n ... "
print "\n======\nThe form of change is not relevant, only the magnitude:"
print "{:.4f}\t".format(volatility(L1step, n)), "One 100%% step change in 50 steps"
print "{:.4f}\t".format(volatility(L1ramp, n)), "One 100%% ramp change over 50 steps"
print "{:.4f}\t".format(volatility(L2, n)), "Two full transitions in 50 steps"

print "\n=======\nConstant situations should measure zeros:"
print "{:.4f}\t".format(volatility(Cn, n)), "Constant =n"
print "{:.4f}\t".format(volatility(C0, n)), "Constant =0"
print "{:.4f}\t".format(volatility(Cn2, n)), "Constant =n/2"


