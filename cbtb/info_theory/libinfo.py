'''
Wrappers for JIDT toolbox, using python interface.  Used to apply
transfer entropy and mutual information calculations, on ensemble data
series.
'''
import jpype, sys
import os.path

import numpy as np

# JIDT requires that the location of the JAR file is on the python path.
# I have it here..
sys.path.append( os.path.expanduser("~/projects/build-jidt/jidt/demos/python"))
jarLocation = os.path.expanduser("~/projects/build-jidt/infodynamics.jar")

#{{{ java toolbox setup
def init_jvm(jvmpath=None):
    if jpype.isJVMStarted():
        return
    jpype.startJVM(jpype.getDefaultJVMPath())

# taken from jidt code gdnerator
def prep_jidt():
    # Add JIDT jar library to the path
    # Start the JVM (add the "-Xmx" option with say 1024M if you get crashes due to not enough memory space)
    if not jpype.isJVMStarted(): # cope with ipython restart.
        jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=" + jarLocation)

#}}}
#{{{ handles to java class initialisers
def prep_ksg():
    calcClass = jpype.JPackage("infodynamics.measures.continuous.kraskov").MutualInfoCalculatorMultiVariateKraskov2
    calc = calcClass()
    return calc

def prep_MoG():
    calcClass = jpype.JPackage("infodynamics.measures.continuous.gaussian").MutualInfoCalculatorMultiVariateGaussian
    return calcClass()

def prep_te_ksg():
    calcClass = jpype.JPackage("infodynamics.measures.continuous.kraskov").TransferEntropyCalculatorKraskov
    return calcClass()

def prep_te_MoG():
    calcClass = jpype.JPackage("infodynamics.measures.continuous.gaussian").TransferEntropyCalculatorGaussian
    return calcClass()

#}}}

#{{{ slide_te_grp
def slide_te_grp(calc, lrng, D1, D2, samples=100, verb=False, prop="DELAY" , k=1, l=1):
    '''
    this function produces a list of transfer entropy measurements from D1->D2
    for several time delays or lags, as defiend in the list `lrng` (integers).
    D1 and D2 are expected to be ensembles.

    `calc` should be a transfer entropy object of JIDT
    `prop` needs to be set depending on the type of TE object.  See JIDT docs.
    `samples` is the number of surrogate samples produced for the confidence
    statistical test.

    returns a numpy array of the TE calc per time delay, and a numpy array
    of the significance of the TE per time delay.

    '''
    R = np.zeros_like(lrng, dtype=float)
    P = np.ones_like(lrng, dtype=float)
    calc_OK = True
    for i, L in enumerate(lrng):
        # initialise(int k, int k_tau, int l, int l_tau, int delay)
        # defautls/values used in paper are 1,1,1,1,X
        # but note we can still just set using the setProperty method.
        # note this operates on the parameter DELAY not TIME_DIFF
        #  Supply the sample data:
        if calc_OK:
            try:
                # Compute the estimate:
                if verb: print "[D] {}:={}".format(prop, L)

                if L < 0:
                    LL = -L
                    calc.setProperty(prop, str(LL))
                    calc.setProperty("l_HISTORY", str(l))
                    calc.setProperty("k_HISTORY", str(k))

                    # load a series /ensemble of data observations
                    calc.initialise()
                    calc.startAddObservations();
                    for d2, d1 in zip(D2, D1):
                        calc.addObservations(d2, d1)

                    calc.finaliseAddObservations()

                else:
                    calc.setProperty(prop, str(L))
                    calc.setProperty("l_HISTORY", str(l))
                    calc.setProperty("k_HISTORY", str(k))
                    calc.initialise()
                    # load a series /ensemble of data observations
                    calc.startAddObservations();
                    for d1, d2 in zip(D1, D2):
                        calc.addObservations(d1, d2)

                    calc.finaliseAddObservations()

                R[i] = calc.computeAverageLocalOfObservations()
                measDist = calc.computeSignificance(samples)
                P[i] = measDist.pValue
            except Exception as e:
                print "oops, gauss TE calc failure. Giving up calculations", e
                # give up with this series, the calculation needs debug
                calc_OK = False

        if verb: print "Lag tested: {:3}  TE: {:.4f} | {:.4f}".format(L, R[i])
    return R, P
#}}}
#{{{ apply TE - convenience wrapper to slide_te_grp + plot result
def apply_TE_peaklag(D1, D2, ax, lagrng, s_lag, k=1, l=1, samples=500, alpha=0.05):
    '''
    apply transfer entropy calculator (with MoG estimator) to data ensembles
    D1 and D2, for the time delays in lagrng, and plot on the matplotlib-like
    axes `ax`.  Fill circles for significant TE, empty circles for
    non-significant TE values.
    '''
    prep_jidt() # make sure toolbox ready
    te_mog = prep_te_MoG() # initialise a TE calculator object

    RG, PG, = slide_te_grp( # compute TE and significance for each l in lagrng
        te_mog, lagrng, D1, D2, samples=samples,
        prop="DELAY", l=l, k=k)
    #RG = RG / np.log(2) # convert to bits? (calc in nats)

    # plot with empty circles, and dashed line
    hh = ax.plot(s_lag, RG, ls='--', lw=2, marker='o',
                 mfc='none', ms=8.5, label=str(k))
    # for all significant TE, fill in markers
    clr = hh[0].get_color()
    ax.plot(s_lag[PG < alpha], RG[PG < alpha], 'o',
            mfc=clr, mew=2, color=clr, ms=8.5)
    ax.grid('on')

#}}}
