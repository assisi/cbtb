'''
A library to assist with parsing and processing logs from casu output
'''

import yaml, os, fnmatch
import numpy as np

#{{{ read specific data series from file
def read_syncflash(cname, pth='./'):
    '''
    syncflash data is in the same directory as the casu log file; and takes
    a similar form, with datestamp in fname.
    look for the file that matches, and read all lines into an array.
    '''
    # find the first hit for this casu name
    found = False
    for fn in os.listdir(pth):
        if fnmatch.fnmatch(fn, '{}*.sync.log'.format(cname)):
            print "[I] found sync log {} -> {}".format(cname, fn)
            found = True
            break

    if not found:
        return None

    li = []
    with open(os.path.join(pth, fn), 'r') as f:
        for line in f:
            if len(line.split(';')) >=3:
                if line.strip('; \n').endswith('start'):
                    li.append(line)

    return li


def read_irs(cname, pth='./', verb=False, minlen=8, droptail=True):

    # find the first hit for this casu name
    fn = identify_log(cname, pth, verb=verb)

    # extract lines that are about temps, and about peltiers.
    # we'll store separately and let csvreaders on the job. (or numpy)

    ir_lines = []
    #temp_lines = []
    #peltier_lines = []
    skipped = 0
    with open(os.path.join(pth, fn), 'r') as f:
        for line in f:
            if line.startswith('ir_raw'):
                if len(line.split(';')) >= minlen:
                    ir_lines.append(line.strip())
                else:
                    skipped += 1
            # else ignore it

    if skipped:
        ss = " skipped {} lines (too short) |".format(skipped)
    else: ss = ""

    print "   [i]{} read {} ir lines from {}".format(ss, len(ir_lines), fn)
    # discard last one - very frequently malformed
    if droptail:
        ir_lines.pop()

    return ir_lines



def identify_log(cname, pth, verb=False):
    # find the first hit for this casu name
    for fn in os.listdir(pth):
        if fnmatch.fnmatch(fn, '*{}.csv'.format(cname)):
            if verb: print "[I] found casu log {} -> {}".format(cname, fn)
            return fn
    # got this far, not found
    return None

def read_temp_sensor_vals(cname, pth, minlen=7, droptail=True):
    fn = identify_log(cname, pth)

    print "[I] working on file '{}' (temp sensor data)".format(fn)
    print "    {}".format( os.path.join(pth, fn))


    # extract lines that are about temps
    # we'll store separately and let csvreaders on the job. (or numpy)
    temp_lines = []
    with open(os.path.join(pth, fn), 'r') as f:
        for line in f:
            if line.startswith('temp'):
                if len(line.split(';')) >= minlen:
                    temp_lines.append(line.strip())

    # discard last one - very frequently malformed
    if droptail:
        temp_lines.pop()

    return temp_lines

def read_air_data(cname, pth, droptail=True):
    fn = identify_log(cname, pth)
    # extract lines that are about LED states/changes
    air_lines = []
    with open(os.path.join(pth, fn), 'r') as f:
        for line in f:
            if line.startswith('airflow_ref;'):
                if len(line.split(';')) == 3:
                    air_lines.append(line)
            # else ignore it

    if droptail:
        air_lines.pop()
    return air_lines

def read_led_data(cname, pth, droptail=True):
    fn = identify_log(cname, pth)
    # extract lines that are about LED states/changes
    led_lines = []
    with open(os.path.join(pth, fn), 'r') as f:
        for line in f:
            if line.startswith('dled_ref;'):
                if len(line.split(';')) == 5:
                    led_lines.append(line)
            # else ignore it

    if droptail:
        led_lines.pop()
    return led_lines



def read_peltier_data(cname, pth):
    fn = identify_log(cname, pth)

    # extract lines that are about peltier state changes
    peltier_lines = []
    with open(os.path.join(pth, fn), 'r') as f:
        for line in f:
            if line.startswith('Peltier;'):
                if len(line.split(';')) == 4:
                    peltier_lines.append(line)
            # else ignore it

    return peltier_lines

def read_temps(cname, pth):
    '''
    for legacy, keep this func that reads two series together
    '''
    temp_lines = read_temp_sensor_vals(cname, pth)
    peltier_lines = read_peltier_data(cname, pth)
    return temp_lines, peltier_lines


def read_tstart_tstop(cname, pth):
    '''
    find the first and last line in log, as the t0 and tEnd bounds
    '''
    fn = identify_log(cname, pth)
    with open(os.path.join(pth, fn), 'r') as f:
        line1 = f.readline()
        last2 = tail(f, 2)


    # we take the last but one because sometimes the last line seems corrupted
    t_start = float(line1.split(";")[1])
    t_stop  = float(last2[0].split(";")[1])

    return t_start, t_stop



#}}}


#{{{ which_arena
def which_arena(proj_file, search_casu):
    '''
    find which arena the casu is in, within the assisi project proj
    '''

    #proj_file = os.path.join(p_root, depdir, pf)
    proj_dir = os.path.dirname(os.path.abspath(proj_file))
    with open(proj_file) as _f:
        project = yaml.safe_load(_f)

    af = project.get('arena')
    with open(os.path.join(proj_dir, af)) as _f:
        arena = yaml.safe_load(_f)

    for layer in sorted(arena):
        for _casu in arena[layer]:
            if _casu == search_casu:
                return layer

    # not found = return none.
    return None
#}}}


#{{{ further analysis tools
def guess_ir_thresh(ir_raw, gain=1.1, steps=50, pre_skip=5):
    thr = ir_raw[pre_skip:pre_skip+steps].max() * gain
    return thr
def guess_ir_with_offset(ir_raw, steps=50, pre_skip=5, offset=300):
    thr = ir_raw[pre_skip:pre_skip+steps].max() + offset
    return thr

def movingaverage(data, window_size):
    ''' from http://stackoverflow.com/a/11352216'''
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(data, window, 'same')

def movavg2(data, window_size):
    '''https://stackoverflow.com/a/34387987 faster than ma1 '''
    cs_vec = np.cumsum(np.insert(data, 0, 0))
    ma_vec = (cs_vec[window_size:] - cs_vec[:-window_size]) / float(window_size)
    # padding at start and end -- just take avg value for 1 window so the value
    # doesn't drop down with zeros.
    start_v = np.ones(window_size/2 ) * data[:window_size/2].mean()
    end_v   = np.ones(window_size/2) * data[-window_size/2:].mean()
    return np.concatenate( (start_v, ma_vec, end_v))





#}}}

#{{{ graphics / visualisation
def min_sec_fmtr(s, pos):
    '''
    for use with mpl, to show mins:secs on an axis. E.g.:
      from matplotlib.ticker import FuncFormatter
      fmtr = FuncFormatter(min_sec_fmtr)
      #fmtr = matplotlib.ticker.FuncFormatter(min_sec_fmtr)
      ax.xaxis.set_major_formatter(fmtr)

    '''
    sec = int(s) % 60
    mn = int(s) / 60
    return "{:3}:{:02}".format(mn, sec)
#}}}

#{{{ sample_signal
def sample_signal(raw, start_time=None, dt=0.1, t_offset=0.0, verb=0):
    ''' given an irregular sampled dataset, sample at a more regular rate
    to produce a parallelly readable series. If start_time is given, use
    this as a reference time. Otherwise, assume the first element of the
    first column is the reference point.

    '''
    # first compute the number of fields
    samples, cols = raw.shape
    if start_time is None:
        first_time = raw[0,0]
    else:
        first_time = start_time

    last_time  = raw[-1,0]
    max_time = last_time - first_time

    # can also pre-calculate the overall length of data based on
    # dt, so long as we see what the max time - min time is.
    num_samples = int(np.ceil(float(max_time) / dt))
    #print num_samples, cols
    sampled = np.zeros((num_samples, cols) )
    #latch = np.array(raw[0,:])

    # then latch one sample per step
    #t = -(0.9*dt) # internal progress
    t = -dt # internal progress
    i = 0
    timesteps = np.zeros((num_samples,))
    for tt in xrange(num_samples):
    #for tt in xrange(100):
        # have we gone past this sample? - if so, change mem

        elapsed = raw[i, 0] - first_time
        while elapsed < t:
            if verb > 1:
                print "moving past sample {} (t={}, elap={})".format(i, t, elapsed)
                print "  looking for data that is later than {} (t_rel={})".format(
                    raw[i, 0], raw[i, 0]-first_time )
            i += 1
            if i < raw.shape[0]:
                elapsed = raw[i, 0] - first_time
            else:
                i -= 1
                break
        if verb > 1: print "t=", t
        latched = np.array(raw[i, :])
        t += dt
        timesteps[tt] = t + t_offset
        sampled[tt,:] = np.array(latched)

        #if timesteps[tt] > 2750:
        #    break

    if verb: print "[I] sampled data, with %d rows, after %d moves and %d secs" % (tt, i, t)

    return sampled, timesteps

#}}}

#{{{ support utils
def tail(f, window=20):
    """
    Returns the last `window` lines of file `f` as a list.

    https://stackoverflow.com/a/7047765
    """
    if window == 0:
        return []
    BUFSIZ = 1024
    f.seek(0, 2)
    bytes = f.tell()
    size = window + 1
    block = -1
    data = []
    while size > 0 and bytes > 0:
        if bytes - BUFSIZ > 0:
            # Seek back one whole BUFSIZ
            f.seek(block * BUFSIZ, 2)
            # read BUFFER
            data.insert(0, f.read(BUFSIZ))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            data.insert(0, f.read(bytes))
        linesFound = data[0].count('\n')
        size -= linesFound
        bytes -= BUFSIZ
        block -= 1
    return ''.join(data).splitlines()[-window:]
#}}}

