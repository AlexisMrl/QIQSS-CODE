import numpy as np
from copy import copy, deepcopy
import matplotlib.pyplot as plt

# "abstract"
class AtomSegment(object):
    ''' An AtomSegment is an elementary segment.
    It has a name and a number of parameters defined by the length of 'param_vals'. 
    Every parameters has a label at its corresponding index in param_lbls.
    If there is only one paramters, param_vals and param_lbls are still lists.
    Name reserved:
    - '_compensation'
    
    '''
    def __init__(self, name, param_vals, duration, param_lbls):
        # type: str, list, list, float
        self.name = name
        if not isinstance(param_vals, tuple):
            param_vals = (param_vals,)
        self.param_vals = param_vals           # tuple or list of float
        self.param_lbls = param_lbls           # tuple or list of float
        self.duration = duration # total duration
    
    def _paramIndex(self, label):
        # return the index corresponding to 'label'
        index = self.param_lbls.index(label)
        return index

    def get(self, label):
        if label not in self.param_lbls + ['duration']:
            raise KeyError('The parameter must be a string among: {} or \'duration\'.'.format(self.param_lbls))
        if label == 'duration':
            return self.duration
        else:
            return self.param_vals[self._paramIndex(label)]

    def set(self, label, new_value):
        if label not in self.param_lbls + ['duration']:
            raise KeyError('The parameter must be a string among: {} or \'duration\'.'.format(self.param_lbls))
        if label == 'duration':
            self.duration = new_value
        else:
            tmp_list = list(self.param_vals)
            tmp_list[self._paramIndex(label)] = new_value
            self.param_vals = tuple(tmp_list)

    def getDuration(self):
        # another way to get duration: AtomSegment.get('duration')
        return float(self.duration)

    def info(self):
        return {'type':type(self).__name__,
                'name':self.name,
                'duration':self.duration,
                'parameters':self.param_lbls,
                'values':self.param_vals}
        
    ## sample rate or atom dependant methods ##
    def getMarkWave(self, sample_rate, part=(0.,1.), marker_low_high=(0,1)):
        duration = self.getDuration()
        mark = np.full(int(sample_rate*duration), marker_low_high[0], dtype=np.uint8)
        mark[int(part[0]*sample_rate*duration):int(part[1]*sample_rate*duration)] = marker_low_high[1]
        return mark
    
    def getWave(self, sample_rate):
        """ Returns the wave as a numpy array for the given sample rate """
        pass
    def getArea(self):
        """ Returns the integral of the atom """
        pass

    def getAbsMax(self, sample_rate):
        return max(abs(self.getWave(sample_rate)))


class Constant(AtomSegment):
    default_name = 'const'
    param_lbls = ['value']
    def __init__(self, name=default_name,
                 value=.0,
                 duration=.0):
        self.name = name
        super(Constant, self).__init__(name, value, duration, self.param_lbls)

    def getWave(self, sample_rate):
        value, duration = self.get('value'), self.get('duration')
        return np.full(int(duration*sample_rate), value)

    def getArea(self):
        return self.get('duration')*self.get('value')
        

class Ramp(AtomSegment):
    default_name = 'ramp'
    param_lbls = ['start', 'finish']
    def __init__(self, name=default_name,
                 start_finish=(.0,.0), 
                 duration=.0):
        # type: str, tuple[float, float], float
        super(Ramp, self).__init__(name, start_finish, duration, self.param_lbls)

    def getWave(self, sample_rate):
        wav = np.linspace(self.get('start'), self.get('finish'), int(self.duration*sample_rate))
        return wav

    def getArea(self):
        start, finish, duration = self.get('start'), self.get('finish'), self.get('duration')
        return (start + (finish-start)/2) *duration


class Sine(AtomSegment):
    default_name = 'sine'
    param_lbls = ['frequency', 'amplitude', 'phase', 'offset']
    def __init__(self, name=default_name,
                 freq_amp_phase=(.0,.0,.0,.0), 
                 duration=.0):
        # type: str, tuple[float,float,float,float], float
        if len(freq_amp_phase) != 4:
            raise ValueError('A sine has 4 parameters: (freq, ampli, phase, offset)')
        super(Sine, self).__init__(name, freq_amp_phase, duration, self.param_lbls)

    def getWave(self, sample_rate):
        freq = self.get('frequency')
        amp = self.get('amplitude')
        phase = self.get('phase')
        offset = self.get('offset')
        dur = self.getDuration()
        t = np.linspace(0, dur, int(sample_rate * dur))
        return amp * np.sin(2*np.pi*freq*t + phase) + offset

    def getArea(self):
        #raise NotImplementedError()
        return 0 # TODO: implement this
    
class GaussianWrap(AtomSegment):
    default_name = 'gaussian_'
    param_lbls = ['mu', 'sigma']
    atom_segment = None # the segment around which the gaussian is applied
    def __init__(self, name=default_name,
                 params=(.0,.0), 
                 atom_segment=None):
        # type: str, tuple[float,float], AtomSegment
        if len(params) != 2:
            raise ValueError('A gaussian wrap has 2 parameters: (mu, sigma)')
        if name == self.default_name:
            self.default_name = self.default_name + atom_segment.default_name
        self.atom_segment = atom_segment
        duration = atom_segment.getDuration()
        super(GaussianWrap, self).__init__(name, params, duration, self.param_lbls)

    def getWave(self, sample_rate):
        mu = self.get('mu')
        sigma = self.get('sigma')
        dur = self.getDuration()

        wave = self.atom_segment.getWave(sample_rate)
        t = np.linspace(-dur/2, dur/2, int(sample_rate * dur))
        gaussian = np.exp(-(t-mu)**2 / (2*sigma**2))
        return wave * gaussian

    def getArea(self):
        #raise NotImplementedError()
        return 0 # TODO: implement this

class Segment(object):
    ''' Represent a concatenation of AtomSegment.
    This is the main class to use, instanciate AtomSegment and Sequence from here:
    see the documentation for examples
    '''
    def __init__(self, name='segment'):
        self.name = name
        self.atoms = []
        self.atoms_names = []
        self.marks_dict = {} # {atom_name: (mark_start, mark_stop)}
    
    def _iter(self):
        return zip(self.atoms_names, self.atoms) #zip is not a generator
    
    def _atom_name_exists(self, name):
        # return true if an atom with the same name exists
        if name in [atom.name for atom in self.atoms] + ['']:
            return True
        return False

    def insert(self, *atomSegmentArgs):
        # insert one or several atom in the segment, making sure the name does not already exists
        for atomSegment in atomSegmentArgs:
            #if not isinstance(atomSegment, AtomSegment):
            #    raise TypeError()
            if self._atom_name_exists(atomSegment.name):
                raise NameError('An atom with this name already exists: {}'.format(atomSegment.name))
            self.atoms.append(atomSegment)
            self.atoms_names.append(atomSegment.name)
    
    def insertNew(self, atomType, name='', atomArgs=tuple(), duration=0.):
        # type: Type[AtomSegment], tuple, str
        # Create and insert an atom that does not exist yet
        # atomType is a children of the class AtomType
        # atomArgs is a tuple of argument that is sent to the constructor of AtomType
        if name=='':
            count = 0
            while self._atom_name_exists(name):
                name = atomType.default_name + '_' + str(count)
                count += 1
        atom = atomType(name, atomArgs, duration)
        self.atoms.append(atom)
        self.atoms_names.append(name)
    
    def insertStep(self, vals, durations, names=[]):        
        # type: list[float], list[float], list[str]
        # Abstraction to create and insert a list of constants
        if names == []:
            names = ['']*len(vals)
        if not(len(vals) == len(durations) == len(names)):
                raise ValueError('The lists must be the same size.')

        for val, duration, name in zip(vals, durations, names):
            self.insertNew(Constant, name, val, duration)

    def mark(self, label, duration=(0.,1.)):
        # type: str , tuple[float \in [0,1]]
        # Set a marker on the AtomSegment 'label' if it exists.
        # By default, mark the entire AtomSegment
        # Duration is to mark a part of the AtomSegment
        # TODO: mark multiple with lists
        if not self._atom_name_exists(label):
            raise NameError('Atom {} does not exist.'.format(label))
        if duration[0] < 0 or duration[1] > 1 or duration[0] > duration[1]:
            #raise ValueError('Duration must be a tuple (start,stop) with start > 0, stop < 1 and start < stop.')
            return
        self.marks_dict[label] = duration
    
    def getMarkDuration(self, name):
        return self.marks_dict.get(name, (0,0))

    def getWave(self, sample_rate, marker_low_high=(0,1), normalize=False):
        # Return the segment wave, marks and timesteps
        wave = np.empty(0)
        marker = np.empty(0, dtype=np.uint8)
        for atom_name, atom in self._iter():
            atom_wave = atom.getWave(sample_rate)
            wave = np.concatenate((wave, atom_wave))
            # handle marks
            if atom_name not in self.marks_dict.keys():
                atom_mark = atom.getMarkWave(sample_rate, (0,1), (marker_low_high[0],marker_low_high[0]))
            else:
                atom_mark = atom.getMarkWave(sample_rate, self.marks_dict.get(atom_name), marker_low_high)
            marker = np.concatenate((marker, atom_mark))
        # build timestep
        timestep = np.linspace(0, self.getDuration(), int(len(wave)))
        # handle normalize
        if normalize == True:
            wave = wave / max(abs(wave))
        elif not isinstance(normalize, bool):
            wave = wave / normalize
        return wave, marker, timestep

    def getDuration(self):
        return sum([atom.getDuration() for atom in self.atoms])
    
    def getAbsMax(self, sample_rate):
        return max([atom.getAbsMax(sample_rate) for atom in self.atoms])

    def getWaveIndexes(self, sample_rate):
        # return a dictionnary with the corresponding structure:
        # indexes = {'labelAtom1':(start_index, end_index), 'labelAtom2':(start_index, end_index), ...}
        # useful for highlighing atoms with drawPulse
        indexes = {}
        current_index = 0
        for atom_name, atom in self._iter():
            duration = atom.getDuration()
            indexes[atom_name] = (current_index, int(current_index+duration*sample_rate))
            current_index += int(duration*sample_rate)
        return indexes

    def _getAtomIndex(self, label):
        # Return the position corresponding to the given label if it exists in self.atom_names
        if label not in self.atoms_names:
            raise KeyError('The atom segment label must be a string among: {}'.format(self.atoms_names)) 
        index = self.atoms_names.index(label)
        return index
    
    def get(self, label):
        # return the corresponding atom. (label can also be a integer refering to the atom position)
        return self.atoms[self._getAtomIndex(label)]
    
    def clone(self, name):
        # Return a deepcopy of self with a new name
        copy = deepcopy(self)
        if name != '': copy.name = name
        return deepcopy(self)
    
    def constantToRamp(self, label, slope):
        # If the atom 'label' is a constant, convert it to a ramp:
        # start = value  and  stop = value + duration*slope
        # Made to be called internally when making a sequence
        atom = self.get(label)
        if not isinstance(atom, Constant):
            raise TypeError('Can only convert Constant to Ramp')
        value, duration = atom.get('value'), atom.get('duration')
        rmp = Ramp(label, (value, value+duration*slope), duration)
        self.atoms[self._getAtomIndex(label)] = rmp
    
    def rampToConstant(self, label):
        # If the atom 'label' is a ramp, convert it to a constant with value = start
        # Maybe not useful but at least constantToRamp is reversible
        atom = self.get(label)
        if not isinstance(atom, Ramp):
            return
        value, duration = atom.get('start'), atom.get('duration')
        cst = Constant(label, value, duration)
        self.atoms[self._getAtomIndex(label)] = cst

    def insertCompensation(self, value, name='_compensation'):
        # Compute the integral and append a compensation segment at value so the mean is zero.
        # Made to be called by the object itself when making a sequence
        # Best practice to not use this directly but use it trough the makeSequence argument: compensate=value.
        # Set compensate to 'last' for using the last value of the segment as the compensation value.
        if value=='last': # then use the last value
            last_atom = self.atoms[-1]
            value = last_atom.getWave(sample_rate=2/last_atom.getDuration())[-1]
        sum = 0
        for atom in self.atoms:
            sum += atom.getArea()
        duration = abs(sum/value)
        self.insertNew(Constant, name, value, duration)

    def makeSequence(self, repeat, constant_slope=[], compensate=0, wait_time=0, name=''):
        # A sequence is a concatenation of segments
        # This function make a simple concatenation X times.
        # For a more complex one (with varying parameters): use directly 'makeVaryingSequence'
        if name == '': name = 'sequence_fixed'
        seq = self.makeVaryingSequence(repeat, [], [], [],
                                       constant_slope=constant_slope,
                                       compensate=compensate,
                                       wait_time=wait_time,
                                       name=name)
        return seq

    def makeVaryingSequence(self, repeat,
                           name_to_change,
                           param_to_change,
                           values_iter,
                           constant_slope=[],
                           compensate=0,
                           wait_time=0,
                           name=''):
        # type: int, list[str], list[str], list[tuple[float]], float, float, float, str
        '''
        repeat: number of time to repeat sequence
        name_to_change: list of atom name to vary
        param_to_change: list of paramter to vary (same order as name_to_change)
        values_iter: list of tuple (start,stop) of the values to give to
            name.param (same order as name and param).
        constant_slope: a list of tuple: [(atom_name, slope_value), ..]. If the
            atom is a constant, it is converted to a ramp with the
            corresponding slope
        compensate: if != 0, add a Constant value at the end of each segment to
            make the mean equal to 0. Set compensate='last' if you want the
            value to be the same as the last value of the segment.
        wait_time: add a constant 0 at the end of every segment.
        '''
        # make sure everythings has the same length
        if not (len(name_to_change) == len(param_to_change) == len(values_iter)):
                raise ValueError('names, params and values must all have the same length.')
        
        # init sequence
        gen_kwargs = deepcopy(locals())
        gen_kwargs.pop('self')
        seq = Sequence('sequence_varying_'+str(repeat) if name=='' else name,
                       original_segment=self,
                       gen_kwargs=gen_kwargs)
        
        # gen list of values_iter inplace:
        for i, (start, stop) in enumerate(values_iter):
            values_iter[i] = np.linspace(start, stop, repeat)

        for i in range(repeat):
            new_seg = self.clone(self.name+'_'+str(i)) # clone self and give it the name: name_i
            ## varying part, change the wanted parameters
            for name, param, values in zip(name_to_change, param_to_change, values_iter):
                atom = new_seg.get(name)
                atom.set(param, values[i])
            ## add compensation if enabled
            if len(constant_slope) > 0 :
                for atom_name, slope in constant_slope:
                    new_seg.constantToRamp(atom_name, slope)
            if compensate != 0:
                new_seg.insertCompensation(compensate)
            if wait_time != 0:
                new_seg.insertNew(Constant, 'wait', 0, wait_time)
            ## segment done
            seq.insertSegment(new_seg)
        return seq

    def info(self):
        return [atom.info() for atom in self.atoms] + list(self.marks_dict.items())


class Sequence(object):
    ''' A concatenation of Segments '''
    def __init__(self, name, original_segment=None, gen_kwargs={}):
        self.name = name
        self.segments = []
        self.segments_names = []
        # memorize how this sequence was generated
        self.original_segment = original_segment
        self.gen_kwargs = gen_kwargs
    
    def _iter(self):
        return zip(self.segments_names, self.segments)

    def insertSegment(self, segment):
        # type: Segment
        self.segments.append(segment)
        self.segments_names.append(segment.name)
    
    def getDuration(self):
        return sum([segment.getDuration() for segment in self.segments])
    
    def getMaxSegmentDuration(self):
        return max([segment.getDuration() for segment in self.segments])
    
    def getAbsMax(self, sample_rate):
        # return the max absolute value of the wave
        return max([segment.getAbsMax(sample_rate) for segment in self.segments])
    
    def getNbSegment(self):
        return len(self.segments)
    
    def getWave(self, sample_rate, marker_low_high=(0,1), normalize=False):
        full_wave, full_marker = np.empty(0), np.empty(0)
        for seg in self.segments:
            wave, marker, _ = seg.getWave(sample_rate, marker_low_high)
            full_wave = np.concatenate((full_wave, wave))
            full_marker = np.concatenate((full_marker, marker))
        timestep = np.linspace(0, self.getDuration(), int(len(full_wave)))
        # handle normalize
        if normalize:
            full_wave = full_wave / max(abs(full_wave))
        return full_wave, full_marker, timestep
    
    def getWaveIndexes(self, sample_rate):
        # return a dictionnary with the corresponding structure:
        # indexes = {'labelAtom1':[(start_index1, end_index1), ..., (start_indexN, end_indexN)], ...}
        # useful for highlighing atoms with pulseDraw
        indexes = {}
        current_segment_end = 0
        for segment in self.segments:
            seg_indexes = segment.getWaveIndexes(sample_rate)
            # merge dictionnaries:
            for key, val in seg_indexes.items():
                indexes.setdefault(key,[]).append((val[0]+current_segment_end, val[1]+current_segment_end))
            current_segment_end += int(segment.getDuration()*sample_rate)
        return indexes


# to later implement in the awg class
def sendSequence(awg, seq, sample_rate, marker_low_high=(0,128), wfname='', force=False, ch=1):
    """ Force: wrtie even a wave with the same name is present """
    # but for now:
    awg_type = type(awg).__name__
    if awg_type not in ['tektronix_AWG']:
        raise TypeError('Awg not supported.')
    ###
    
    # Hardcoded way to get the appropriate functions for this awg_type
    awg_wf_list = awg.list_waveforms
    awg_wf_create = awg.waveform_create
    awg_wf_marker = awg.waveform_marker_data
    awg_wf_select = awg.channel_waveform

    if type(seq).__name__ != Sequence.__name__: # isintance(seq, Sequence) does not work for some reason
        raise TypeError('The given sequence is not a Sequence...')
    if wfname == '': wfname = seq.name
    
    wave, markers, _ = seq.getWave(sample_rate, normalize=True, marker_low_high=marker_low_high)
    ampl = seq.getAbsMax(sample_rate)

    # set waveform, sample_rate, ampl
    awg_wf_create(wave, wfname, sample_rate=sample_rate, amplitude=ampl, force=force)
    awg_wf_marker.set(markers, wfname=wfname)
    # 'select' waveform on channel ch
    awg_wf_list.get() # to update the list before setting (or else it doesn't find wfname.)
    awg_wf_select.set(wfname, ch=ch)

def pulseDraw(obj, sample_rate, y_label='', marker_low_high=(0,1), normalize=False,
              no_marks=False, vert_lines=False,
              highlight_atoms=[],
              superpose=False,
              fig_axes=(None, None, None),
              **plot_kwargs):
    # Can draw Segment and Sequence
    # highlight_atoms: of the form [('atomName1', 'color1'), ('atomName2','color2']
    #                  the color is optional: ['atomName1', 'atomName2'] also works
    # superpose: only for sequence: draw all windows on top of eachother with
    #                               different opacity
    if not isinstance(obj, (Segment, Sequence)):
        raise TypeError('This object can\'t be draw.')
    kwargs=locals()
    if None in fig_axes:
        # init graph
        fig, [ax1, ax2] = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    else:
        fig, ax1, ax2 = fig_axes
    fig.suptitle(obj.name)
    ax1.set_ylabel(y_label)
    ax1.grid(True)
    ax2.set_xlabel('time (s)')
    ax2.grid(True)

    # handle superpose
    if isinstance(obj, Sequence) and superpose:
        if normalize:
            kwargs['normalize'] = obj.getAbsMax(sample_rate)
        kwargs['fig_axes'] = (fig, ax1, ax2)
        plot_kwargs = kwargs.pop('plot_kwargs', {})
        nb_seg = len(obj.segments)
        for i, seg in enumerate(obj.segments):
            kwargs['obj'] = seg
            plot_kwargs['alpha'] = (i+1.)/nb_seg
            pulseDraw(**dict(kwargs, **plot_kwargs))
        return

    # get things and draw things
    wave, marker, timestep = obj.getWave(sample_rate, marker_low_high, 
                                         normalize=normalize)
    ax1.plot(timestep, wave, **plot_kwargs)
    if no_marks:
        fig.delaxes(ax2)
    else:
        plot_kwargs.pop('color', None)
        ax2.plot(timestep, marker, color='orange', **plot_kwargs)
    # draw extra stuff
    indexes = obj.getWaveIndexes(sample_rate)
    if len(highlight_atoms) > 0:
        _draw_helper_highlights(ax1, wave, timestep, indexes, highlight_atoms)
    if vert_lines:
        _draw_helper_vert_lines(ax1, ax2, wave, marker, timestep, indexes)


def _draw_helper_highlights(ax1, wave, timestep, indexes, highlight_atoms):
    # draw on top of the main plot for every atom name in highlight_atoms:
    # ['atomName1', ('atomName2', 'color2')]: if not tuple, convert to one
    highlight_atoms = [(val, None) if not isinstance(val, tuple) else val for val in highlight_atoms]
    for name, color in highlight_atoms:
        if name not in indexes.keys():
            continue
        starts_stops = indexes.get(name)
        if isinstance(starts_stops, tuple): # tuple or list of tuple depending of obj (Sequence or Segment)
            starts_stops = [starts_stops]
        for start, stop in starts_stops:
            ax1.plot(timestep[start:stop], wave[start:stop], color=color)

def _draw_helper_vert_lines(ax1, ax2, wave, marker, timestep, indexes):
    if len(marker) == 0:
        return
    for name, starts_stops in indexes.items():
        if isinstance(starts_stops, tuple): # tuple or list of tuple depending of obj (Sequence or Segment)
            starts_stops = [starts_stops]
        mark_min, mark_max = min(marker), max(marker)
        wave_min, wave_max = min(wave), max(wave)
        for start, stop in starts_stops:
            if stop >= len(wave):
                continue
            #ax1.text(xy_norm, name, fontsize=10, transform=ax1.transAxes)
            ax1.vlines(x=timestep[start], ymin=wave_min, ymax=wave_max, linestyles=':', alpha=0.2)
            ax2.vlines(x=timestep[start], ymin=mark_min, ymax=mark_max, linestyles=':', alpha=0.2)


def autoSetOscillo(self, osc, channel_wave, channel_trig, nb_segment, start_acq=True):
    osc.trigger_source.set(channel_trig)
    osc.channel
    osc.trigger_level.set(2)