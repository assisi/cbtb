'''

The example data comes from simulations of bees in a thermal environment
defined by robots that have a closed-loop between sensing bees nearby and the
local temperature.  See Mills et al (2015) [1] and also Schmickl et al (2009)
[2].

Four pairs of files are included, containing the counts of agent bees near the
left-hand robot at 30s intervals through a 20-min simulated experiment (since
the space is divided into two halves, a single recording defines the group
state).  There exist two populations of bees in each experiment, contained
within physically separated arenas.  In the linked_xxx files, the robots have a
"partner" robot in the other arena that they share sensory information with.
This means that the two bee groups can coordinate their collective behaviour.
In the sep_xxx files, there exists no such link: two bee groups act
independently.  Each file contains an (r, c) matrix, corresponding to r repeats,
each with c data samples at 30s intervals.

This example shows application of transfer entropy calculations over the
ensemble of time series results, from population 1 to population 2 and also
from 2 to 1.  The method examines time delay detection using the method shown
in Wibral et al (2013) [3], achieved using functions from the JIDT toolbox [4].


[1] Mills, R., Zahadat, P., Silva, F., Mliklic, D., Mariano, P., Schmickl, T.,
& Correia, L. (2015). Coordination of collective behaviours in spatially
separated agents. Procs. ECAL, 579-586.

[2] Schmickl, T., Thenius, R., Moeslinger, C., Radspieler, G., Kernbach, S.,
Szymanski, M., and Crailsheim, K. (2009). Get in touch: cooperative decision
making based on robot-to-robot collisions. Auton Agent Multi Agent Syst,
18(1):133--155.

[3] Wibral, M., Pampu, N., Priesemann, V., Siebenhuehner, F., Seiwert, H.,
Lindner, M., ... & Vicente, R. (2013). Measuring information-transfer delays.
PloS one, 8(2), e55809.

[4] Lizier, J. T. (2014). JIDT: An information-theoretic toolkit for studying
the dynamics of complex systems. Frontiers in Robotics and AI, 1, 11.


'''
import numpy as np
import matplotlib.pyplot as plt
import libinfo

if __name__ == "__main__":
    # select data to perform TE calcs on
    datapath = "data/"
    fnames = ["linked_12", "linked_6", "sep_16", "sep_8"]
    labels = ["coupled (12 agent)", "coupled (6 agent)",
              "sep (16 agent)", "sep (8 agent)", ]

    # settings for transfer entropy delay window
    lim = 10; lagrng = np.arange(1, +lim+1) # time delays to test (indices)
    k = 1; l = 1; # embedding
    s_lag = lagrng.astype(float)/60 * 30.0 # time delay in secs (not indices)


    # one row for each direction (X->Y, Y->X); one col for each data series
    plt.figure(1); plt.clf()
    fig, ax = plt.subplots(nrows=2, ncols=len(fnames), num=1, sharex=True, sharey=True)

    # for each
    for i, fn in enumerate(fnames):
        # load data
        X = np.loadtxt("{}/{}-pop1.csv".format(datapath, fnames[i]))
        Y = np.loadtxt("{}/{}-pop2.csv".format(datapath, fnames[i]))

        # compute TE in each direction, and plot
        libinfo.apply_TE_peaklag(X, Y, ax[0, i], lagrng, s_lag, k=k, alpha=0.05/float(len(lagrng)))
        libinfo.apply_TE_peaklag(Y, X, ax[1, i], lagrng, s_lag, k=k, alpha=0.05/float(len(lagrng)))

        # decoration
        ax[0,i].set_title(labels[i])
        ax[1,i].set_xlabel('time delay (mins)')

    ax[0,0].set_ylabel('TE (top -> bottom)')
    ax[1,0].set_ylabel('TE (bottom -> top)')
    fig.tight_layout()


