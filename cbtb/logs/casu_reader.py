'''
A wrapper to handle reading data from casu logs into various different
fields, within a container object.

**LogDataOwner**
Assumes that log directory was created by the assisipy_utils/mgmt scripts,
(or at least with that structure).

**SingleLogDataOwner**
Does not assume much about the directory structure, only that the log was
created by assisipy.casu.Casu()


'''

'''
TODO:
    validate whether SingleLogDataOwner needs nodes= kw.
'''

import os
import process_logs as plg
import fnmatch, yaml

import numpy as np

#{{{ SingleLogDataOwner
class SingleLogDataOwner(object):
    '''
    The earlier LogDataOwner makes various assumptions about data organisation
    that are not always honoured, even if assisirun/deploy/collect_data tools
    were used.  This tool is a simplified version that requires only a single
    casu name, and only loads data for that one casu.
    '''
    dirs = ['F', 'FR', 'BR', 'B', 'BL', 'FL', ]

    def __init__(self, cname, logpath, ctype="phys", **kwargs):
        '''
        the data is expected to be in
        logpath/<timetamp->casu-xxx.csv
        - if the data has been pre-processed already, the csv file might
        exclude the timestamp.

        casu name in the form "casu-xxx" (but could be anything esp if in sim)
        ctype [sim or phys] data produced are not identical


        '''

        self.cname = cname
        self.pth = logpath
        self.ctype = ctype
        self.nchannels   = 6
        self.movavg_len  = kwargs.get('movavg_len', 61)
        self._settings = dict(kwargs)

        if not os.path.isdir(self.pth):
            print "[E] cannot read for {}".format(self.pth)
        else:
            print "[I] reading from {}".format(self.pth)


        self.data = {}
        self.data['ir'] = None
        self.data['temps'] = None
        self.data['pelt'] = None
        self.data['sync'] = None
        self.data['led'] = None
        self.data['air'] = None
        self.data['t_offset_temps'] = self._settings.get('t_offset_temps', 0)

        # makes an assumption that name is somethig like "casu-005"
        # and produces c3
        self.shortname = "c{}".format(self.cname.split('-')[-1].lstrip('0'))

    def read_data(self, ir=True, temp=True, pelt=True, sync=False,
                  all_led=False, air=False, nodes='all'):

        s1 = "# ===========  reading data for node '{}' ========== #".format(
            self.cname,)
        print s1
        print "# ===  file pth: '{}' ".format(self.pth)


        if temp is True:
            rng = range(1,10)
            if self.ctype == "sim":
                rng = range(1,6)
            temp_lines = plg.read_temp_sensor_vals(self.cname, self.pth,
                minlen=rng[-1] + 1)
            print "   [I] reading temp data {}, casu type={} ==> nfields={}".format(
                    self.cname, self.ctype, rng[-1])
            self.data['temps'] = np.loadtxt(
                    temp_lines, usecols=rng, delimiter=';')

        if pelt is True:
            pelt_lines = plg.read_peltier_data(self.cname, self.pth)
            #data_dir = os.path.join(self.pth, self.data_root, layer, cname)
            print "   [I] read peltier data {}, from {}/ ({} li)".format(
                    self.cname, os.path.relpath(self.pth, self.pth), len(pelt_lines))

            self.data['pelt'] = np.loadtxt(
                pelt_lines, usecols=(1,2,3), delimiter=';')

        if ir is True:
            ir_lines = plg.read_irs(self.cname, self.pth)
            self.data['ir'] = np.loadtxt(
                    ir_lines, usecols=xrange(1,8), delimiter=';')

        if sync is True:
            raise NotImplementedError("[E] without paths, probably used other framework. Not looking for syncflash file")
            #_sync_lines = plg.read_syncflash(self.cname, self.pth)
            #self.data['sync'] = np.loadtxt(
            #        _sync_lines, usecols=(0,1,), delimiter=';')


        if all_led is True:
            _led_lines = plg.read_led_data(self.cname, self.pth)
            self.data['led'] = np.loadtxt(
                _led_lines, usecols=xrange(1,5), delimiter=';')

        if air is True:
            _air_lines = plg.read_air_data(self.cname, self.pth)
            self.data['air'] = np.loadtxt(
                _air_lines, usecols=(1,2), delimiter=';')


        # get the extreme time values from log file
        self._t0, self._tEnd = plg.read_tstart_tstop(self.cname, self.pth)

        print "# {} #\n".format("=" * (len(s1) - 4))




    def compute_thresh(self, pre_skip=10, steps=50, fixed_offset=None):
        if self.data['ir'] is not None:
            thr = np.zeros((self.nchannels,))
            ir_raw = self.data['ir'][:, 1:1+self.nchannels]
            for i in xrange(self.nchannels):
                if fixed_offset is None:
                    _thr = plg.guess_ir_thresh(
                        ir_raw[:,i], gain=1.1, pre_skip=pre_skip, steps=steps)
                else:
                    _thr = plg.guess_ir_with_offset(
                        ir_raw[:,i], pre_skip=pre_skip, steps=steps, offset=fixed_offset)
                thr[i] = _thr

            self.data['thr']  = thr

    def show_threshs(self, dp=-3):
        if self.data['ir'] is not None:
            thr = self.data['thr']
            print "coarse thresholds - {}:".format(self.cname)
            print "  " + "\t  ".join([d for d in self.dirs[:self.nchannels]])
            print np.around(thr, dp), np.around([thr.min(), thr.max()], dp)

    def compute_hits(self):
        if self.data['ir'] is not None:
            # extract data for easier varnames
            ir_raw = self.data['ir'][:, 1:1+self.nchannels]
            thr = self.data['thr']

            above_thr = ir_raw[:, 0:self.nchannels] > thr[0:self.nchannels]
            hits = (above_thr).sum(axis=1)
            #hits = (ir_raw[:, 0:self.nchannels] > thr[0:self.nchannels]).sum(axis=1)
            ma_hits = plg.movavg2(hits, self.movavg_len) / float(self.nchannels)
            #ma_hits = plg.movingaverage(hits, self.movavg_len) / float(self.nchannels)
            self.data['above_thr'] = above_thr
            self.data['hits']      = hits
            self.data['ma_hits']   = ma_hits



#}}}

#{{{ LogDataOwner
class LogDataOwner(object):
    dirs = ['F', 'FR', 'BR', 'B', 'BL', 'FL', ]
    #dirs = ['F', 'FR', 'BR', 'B', 'BL', 'FL', 'TOP',]

    def __init__(self, spec, **kwargs):
        '''
        the data is expected to be in
        grp_base/base/label/
        if grp_base is not set, the base should be relative or canonical.
        '''

        self.spec = spec
        self.nchannels   = 6
        self.movavg_len  = kwargs.get('movavg_len', 61)
        self.grp_base    = kwargs.get('grp_base', "")
        self.shared_spec = kwargs.get('shared_spec', {})
        self.dep_dir     = kwargs.get('dep_dir', None)

        self.pth = os.path.join(self.grp_base, self.spec['base'], self.spec['label'])
        if not os.path.isdir(self.pth):
            print "[E] cannot read for {}".format(self.pth)
        else:
            print "[I] reading from {}".format(self.pth)

        # get the .assisi file
        if self.dep_dir is None:
            # assume default location as generated by assisipy_utils mgmt
            self.dep_dir = os.path.join(self.pth, "archive", "dep")

        for fn in os.listdir(self.dep_dir):
            if fnmatch.fnmatch(fn, "*.assisi"):
                print "[I] found assisi projecf file -> {}".format(fn)
                break
        self.proj_file = os.path.join(self.dep_dir, fn)
        self.proj_name = os.path.splitext(os.path.basename(self.proj_file))[0]
        self.data_root = "data_{}".format(self.proj_name)

        self.spec['layers'] = []
        self.nodes = {}
        # load ctype from shared spec first, then overwrite with local if def
        _scty = self.shared_spec.get('ctype', 'phys')
        ctype = self.spec.get('ctype', _scty)

        # load list of casus from shared first, then overwrite with local if def
        _scasus = self.shared_spec.get('casus', [])
        casu_list = self.spec.get('casus', _scasus)

        for cname in casu_list:
            layer = plg.which_arena(self.proj_file, cname)
            self.spec['layers'].append(layer)
            if layer is not None:
                data_dir = os.path.join(self.pth, self.data_root, layer, cname)
                self.nodes[cname] = {
                        'layer' : layer,
                        'data_dir': data_dir,
                        'ctype': ctype,
                        }

    def read_data(self, ir=True, temp=True, pelt=True, sync=True, all_led=False, nodes='all'):
        if nodes == 'all':
            nodelist = self.nodes.keys()
        else:
            nodelist = nodes

        for node in nodelist:
            s1 = "# ===========  reading data for node '{}' ========== #".format(node)
            print s1
            self.nodes[node]['ir'] = None
            self.nodes[node]['temps'] = None
            self.nodes[node]['pelt'] = None
            self.nodes[node]['sync'] = None
            self.nodes[node]['led'] = None
            self.nodes[node]['t_offset_temps'] = self.spec.get('t_offset_temps', 0)


            ddir = self.nodes[node].get('data_dir')

            if temp is True:
                rng = range(1,10)
                if self.nodes[node].get('ctype') == "sim":
                    rng = range(1,6)
                temp_lines = plg.read_temp_sensor_vals(node, ddir,
                    minlen=rng[-1] + 1)
                print "   [I] reading temp data {}, casu type={} ==> nfields={}".format(
                        node, self.nodes[node].get('ctype'), rng[-1])
                self.nodes[node]['temps'] = np.loadtxt(
                        temp_lines, usecols=rng, delimiter=';')

            if pelt is True:
                pelt_lines = plg.read_peltier_data(node, ddir)
                #data_dir = os.path.join(self.pth, self.data_root, layer, cname)
                print "   [I] read peltier data {}, from {}/ ({} li)".format(
                        node, os.path.relpath(ddir, self.pth), len(pelt_lines))

                self.nodes[node]['pelt'] = np.loadtxt(
                    pelt_lines, usecols=(1,2,3), delimiter=';')

            if ir is True:
                ir_lines = plg.read_irs(node, ddir)
                self.nodes[node]['ir'] = np.loadtxt(
                        ir_lines, usecols=xrange(1,8), delimiter=';')

            if sync is True:
                _sync_lines = plg.read_syncflash(node, ddir)
                self.nodes[node]['sync'] = np.loadtxt(
                        _sync_lines, usecols=(0,1,), delimiter=';')


            if all_led is True:
                _led_lines = plg.read_led_data(node, ddir)
                self.nodes[node]['led'] = np.loadtxt(
                    _led_lines, usecols=xrange(1,5), delimiter=';')

            print "# {} #\n".format("=" * (len(s1) - 4))





    def load_calib_thresh(self, calib_file="temp_calib_log"):
        '''
        if the file exists, attempt to read the values for each sensor
        (IRx6 or 7)

        file is yaml, formatted as dicts -
        <casu-name>:
            IR: [thr0, thr1, ...,]
            date: <readable date>
            date_raw: <unix timestamp>

        '''
        nodes_read = []
        for node in self.nodes.keys():
            ddir = self.nodes[node].get('data_dir')
            cf = os.path.join(ddir, calib_file)
            print node, ddir, os.path.exists(cf), cf
            with open(cf) as f:
                cal_raw = yaml.safe_load(f)

            # check the node name is right
            if node in cal_raw:
                nodes_read.append(node)
                ir_threshs = cal_raw[node].get('IR', [])
                thr = np.zeros((self.nchannels,))
                for i in xrange(self.nchannels):
                    #ir_raw = self.nodesd[node]['ir'][i, 1:]
                    thr[i] = ir_threshs[i]
                    if len(ir_threshs) < i+1:
                        # need to guess some then?
                        break
                self.nodes[node]['thr']  = thr

        print "[I] read thresholds for {} of {} nodes".format(
                len(nodes_read), len(self.nodes.keys()))
        if len(nodes_read) < len(self.nodes.keys()):
            for n in self.nodes.keys():
                if n not in nodes_read:
                    print "[W] did not read calibration data for {}".format(n)


    def compute_thresh(self, pre_skip=10, steps=50, fixed_offset=None):

        for node in self.nodes.keys():
            if self.nodes[node]['ir'] is not None:
                thr = np.zeros((self.nchannels,))
                ir_raw = self.nodes[node]['ir'][:, 1:1+self.nchannels]
                for i in xrange(self.nchannels):
                    #ir_raw = self.nodesd[node]['ir'][i, 1:]
                    if fixed_offset is None:
                        _thr = plg.guess_ir_thresh(
                                ir_raw[:,i], gain=1.1, pre_skip=pre_skip, steps=steps)
                    else:
                        _thr = plg.guess_ir_with_offset(
                                ir_raw[:,i], pre_skip=pre_skip, steps=steps, offset=fixed_offset)
                    thr[i] = _thr

                self.nodes[node]['thr']  = thr

    def show_threshs(self, dp=-3):
        for node in self.nodes.keys():
            if self.nodes[node]['ir'] is not None:
                thr = self.nodes[node]['thr']
                print "coarse thresholds - {}:".format(node)
                print "  " + "\t  ".join([d for d in self.dirs[:self.nchannels]])
                print np.around(thr, dp), np.around([thr.min(), thr.max()], dp)

    def compute_hits(self):
        for node in self.nodes.keys():
            if self.nodes[node]['ir'] is not None:
                # extract data for easier varnames
                ir_raw = self.nodes[node]['ir'][:, 1:1+self.nchannels]
                thr = self.nodes[node]['thr']
                above_thr = ir_raw[:, 0:self.nchannels] > thr[0:self.nchannels]
                hits = (above_thr).sum(axis=1)
                #hits = (ir_raw[:, 0:self.nchannels] > thr[0:self.nchannels]).sum(axis=1)
                ma_hits = plg.movingaverage(hits, self.movavg_len) / float(self.nchannels)
                self.nodes[node]['above_thr'] = above_thr
                self.nodes[node]['hits']      = hits
                self.nodes[node]['ma_hits']   = ma_hits

    def remove_node(self, key):
        '''
        if, for whatever reason, the data is judged not to be suitable to include
        in a given analysis, remove it so that looping over LDO object will
        be clean.

        '''
        if key in self.nodes:
            del self.nodes[key]
        else:
            print "[W] key '{}' not present.".format(key)
            pass


#}}}

