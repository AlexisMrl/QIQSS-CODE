from .Shapes import *
from copy import deepcopy
import matplotlib.pyplot as plt
import numpy as np

class Segment(object):
    """ A segment is a part of a pulse.
    It is by default a constant 0 for a duration of 0.1s.
    Attributes waveform and envelope are objects that have a getWave(sample_rate, duration) and getArea(duration) method.
    Mark is a tuple (start, stop) that defines the part of the segment that is marked.
    """
    _id = 0
    name = 'segment'
    duration = 0.1
    offset = 0.
    mark = (0., 0.)
    waveform = None
    envelope = None
    sweep_dict = {}

    def __init__(self, duration=0, offset=0, waveform=None, envelope=None,
                mark=(0, 0), sweep_dict={}, name=None):
        self._id = Segment._id
        Segment._id += 1
        if name is None:
            self.name = 'segment_' + str(self._id)
        self.duration = duration
        self.offset = offset
        self.mark = mark
        self.waveform = waveform
        self.envelope = envelope
        self.sweep_dict = {key:val for key, val in sweep_dict.items()}

    def getWave(self, sample_rate, to_ramp_value=0.):
        """ Build and return the waveform of the segment defined as waveform * envelope + offset.
        """
        if self.duration == 0: return np.array([])
        if self.envelope is not None:
            envelope_wave = self.envelope.getWave(sample_rate, self.duration)
        else:
            envelope_wave = np.ones(int(self.duration*sample_rate))

        if self.waveform is not None:
            waveform_wave = self.waveform.getWave(sample_rate, self.duration)
        else:
            waveform_wave = np.zeros(int(self.duration*sample_rate))

        offset_wave = self.offset * np.ones(int(self.duration*sample_rate))

        return waveform_wave * envelope_wave + offset_wave
    
    def getArea(self):
        """ Returns the area of the segment.
        """
        duration = self.duration
        if self.envelope is None and self.waveform is None:
            return self.offset * duration
        if self.envelope is None:
            return self.waveform.getArea(duration) + self.offset * duration
        if self.waveform is None:
            return self.envelope.getArea(duration) + self.offset * duration
        return self.waveform.getArea(duration) * self.envelope.getArea(duration) + self.offset * duration
    
    def getMarks(self, sample_rate, val_low=0, val_high=1):
        marks = val_low * np.ones(int(self.duration*sample_rate))
        if self.mark[0] == self.mark[1]:
            return marks
        id_high_start = int(self.duration*sample_rate*self.mark[0])
        id_high_end = int(self.duration*sample_rate*self.mark[1])
        marks[id_high_start:id_high_end] = val_high
        return marks
    
    def __str__(self):
        # same as above but wrtie only if attribute is not None
        string = "Segment("
        if self.duration != 0:
            string += "duration=" + str(self.duration) + ", "
        if self.offset != 0:
            string += "offset=" + str(self.offset) + ", "
        if self.mark != (0., 0.):
            string += "mark=" + str(self.mark) + ", "
        if self.waveform is not None:
            string += "waveform=" + str(self.waveform) + ", "
        if self.envelope is not None:
            string += "envelope=" + str(self.envelope) + ", "
        if self.sweep_dict != {}:
            string += "sweep_dict=" + str(self.sweep_dict) + ", "
        string = string[:-2] + ")"
        return string


class Pulse(object):
    """ A pulse is a concatenation of Segments
    """

    def __init__(self, *segments):
        self.segments = []
        self.duration = 0.
        self.addSegment(*segments)
        # a sequence is a repetition of pulses.
        self.nb_rep = 1 # for a sequence: the number of repetitions
        self.sub_pulse_seg_count = 0 # for a sequence: the number of segments in the original pulse
        self.compensate = 0. # for a sequence: the compensation value
    
    def __str__(self):
        ret = "Pulse("
        for seg in self.segments:
            ret += str(seg) + ', '
        ret = ret[:-2] + ')'
        return ret

    
    def addSegment(self, *segments):
        for segment in segments:
            self.segments.append(segment)
            self.duration += segment.duration
    
    def removeSegment(self, i_segment):
        self.duration -= self.segments[i_segment].duration
        self.segments.pop(i_segment)
    
    def getWave(self, sample_rate):
        wave = np.array([])
        for segment in self.segments:
            wave = np.concatenate((wave, segment.getWave(sample_rate)))
        return wave
    
    def getWaveNormalized(self, sample_rate, get_min_max=False):
        wave = self.getWave(sample_rate)
        wave_min, wave_max = min(wave), max(wave)
        wave = (wave - wave_min) / (wave_max - wave_min)
        if get_min_max:
            return wave, wave_min, wave_max
        return wave
    
    def getMarks(self, sample_rate, val_low=-1, val_high=1):
        marks = np.array([])
        for segment in self.segments:
            marks = np.concatenate((marks, segment.getMarks(sample_rate, val_low, val_high)))
        return marks

    def getArea(self):
        return sum([seg.getArea() for seg in self.segments])
    
    def getTimestep(self, sample_rate):
        return np.linspace(0., self.duration, len(self.getWave(sample_rate)))
    
    def getIndexes(self, sample_rate):
        """ Returns the indexes of the segments in the wave.
        """
        ret = []
        start = 0
        for seg in self.segments:
            end = start + len(seg.getWave(sample_rate))
            ret.append([start, end-1])
            start = end
        return ret
    
    def getSubPulse(self, i_sub_pulse):
        """ Returns a Pulse composed of the i_sub_pulse-th segment.
        """
        sub_pulse = Pulse()
        sub_pulse.segments = []
        segments = self.segments[i_sub_pulse*self.sub_pulse_seg_count:(i_sub_pulse+1)*self.sub_pulse_seg_count]
        sub_pulse.addSegment(*segments)
        return sub_pulse
    
    
    def addCompensationZeroMean(pulse1, value, add=True):
        comp_time = abs(pulse1.getArea()/value)
        segment = Segment(duration=comp_time, offset=value)
        if add:
            pulse1.addSegment(segment)
        else:
            return segment
    
    def _genSequenceSweep(self, segments, nb_rep):
        """ Generate a dictionary of sweep values for each segment.
        """
        sweep_vals = {}
        for seg_i, seg in enumerate(segments):
            seg_sweep = {}
            for key, val in seg.sweep_dict.items():
                if key == 'mark':
                    # no mark sweep for now
                    pass
                elif key == 'waveform' or key == 'envelope':
                    for param_key, param_val in val.items():
                        seg_sweep[key] = {param_key : np.linspace(param_val[0], param_val[1], nb_rep)}
                else:
                    seg_sweep[key] = np.linspace(val[0], val[1], nb_rep)
            sweep_vals[seg_i] = seg_sweep
        return sweep_vals
    
    def _setSequenceSweep(self, segments, iteration, sweep_vals):
        for i_seg, sweep_val in sweep_vals.items():
            seg = segments[i_seg]
            for key, val in sweep_val.items():
                if key == 'mark':
                    seg.mark = (val['start'][iteration], val['stop'][iteration])
                elif key == 'waveform':
                    for param_key, param_val in val.items():
                        seg.waveform.parameters[param_key] = param_val[iteration]
                elif key == 'envelope':
                    for param_key, param_val in val.items():
                        seg.envelope.parameters[param_key] = param_val[iteration]
                elif key == 'duration':
                    seg.duration = val[iteration]
                elif key == 'offset':
                    seg.offset = val[iteration]

    def genSequence(self, nb_rep=1, compensate=0.):
        """ Generate another Pulse composed of a long sequence of segments
        """
        sequence = Pulse()
        sequence.segments = []
        sequence.compensate = compensate
        sequence.nb_rep = nb_rep
        sequence.sub_pulse_seg_count = len(self.segments)
        if compensate != 0.: sequence.sub_pulse_seg_count += 1
        sweep_vals = self._genSequenceSweep(self.segments, nb_rep)
        original_segments = deepcopy(self.segments)
        for rep in range(nb_rep):
            new_segments = deepcopy(original_segments)
            self._setSequenceSweep(new_segments, rep, sweep_vals)
            if compensate != 0.:
                comp_segment = self.compensate(compensate, add=False)
                new_segments.append(comp_segment)
            sequence.addSegment(*new_segments)
        return sequence


def compensateAndEqualizeTime(pulse1, pulse2, value):
    """ Add a compensation segment to each pulse and equalize their time with a 0 offset segment.
    """
    p1_comp_time = abs(pulse1.getArea()/value)
    p2_comp_time = abs(pulse2.getArea()/value)
    p1_comp = Segment(duration=p1_comp_time, offset=value)
    p2_comp = Segment(duration=p2_comp_time, offset=value)
    pulse1.addSegment(p1_comp)
    pulse2.addSegment(p2_comp)
    max_duration = max(pulse1.duration, pulse2.duration)
    if pulse1.duration < max_duration:
        p1_offset = Segment(duration=max_duration-pulse1.duration)
        pulse1.addSegment(p1_offset)
    elif pulse2.duration < max_duration:
        p2_offset = Segment(duration=max_duration-pulse2.duration)
        pulse2.addSegment(p2_offset)

def plotPulse(pulse, sample_rate, fig_axes=(None, None, None),
            highlight=[],
            superpose=False,
            plot_kwargs={}):
    if None in fig_axes:
        fig, [ax1, ax2] = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    else:
        fig, ax1, ax2 = fig_axes
    fig.suptitle('Pulse')
    ax1.grid(True); ax2.grid(True)
    ax2.set_xlabel('time (s)')

    wave = pulse.getWave(sample_rate)
    marks = pulse.getMarks(sample_rate)
    timestep = pulse.getTimestep(sample_rate)

    if superpose and pulse.sub_pulse_seg_count != 0:
        nb_sub_pulse = len(pulse.segments)//pulse.sub_pulse_seg_count
        for i_sub_pulse in range(nb_sub_pulse):
            alpha = 0.4 + 0.4*i_sub_pulse/nb_sub_pulse
            plotPulse(pulse.getSubPulse(i_sub_pulse), sample_rate, fig_axes=(fig, ax1, ax2),
                        highlight=[],
                        superpose=False,
                        plot_kwargs=dict(list(plot_kwargs.items())+[('alpha',alpha)]))
    else:
        ax1.plot(timestep, wave, color='tab:blue', **plot_kwargs)
        ax2.plot(timestep, marks, color='orange', **plot_kwargs)

    if len(highlight)>0:
        indexes = pulse.getIndexes(sample_rate)
        for i_seg in highlight:
            if i_seg >= len(indexes):
                continue
            # highlight the i_seg-th segment
            # with indexes = [[seg1_start, seg1_end], [seg2_start, seg2_end], ...
            start = indexes[i_seg][0]
            end = indexes[i_seg][1]
            ax1.axvspan(timestep[start], timestep[end], alpha=0.15, color='tab:blue')
            ax2.axvspan(timestep[start], timestep[end], alpha=0.15, color='orange')

def plot2ChannelPulse(pulse1, pulse2, sample_rate, name1='pulse1', name2='pulse2'):
    fig, [ax1, ax2, ax3] = plt.subplots(3, 1, sharex=True, gridspec_kw={'height_ratios': [2,2,1]})
    ax1.grid(True); ax2.grid(True); ax3.grid(True)
    ax1.set_title(name1)
    ax2.set_title(name2)
    ax3.set_xlabel('time (s)')

    wave1 = pulse1.getWave(sample_rate)
    wave2 = pulse2.getWave(sample_rate)
    marks1 = pulse1.getMarks(sample_rate)
    marks2 = pulse2.getMarks(sample_rate)
    timestep1 = pulse1.getTimestep(sample_rate)
    timestep2 = pulse2.getTimestep(sample_rate)
    
    ax1.plot(timestep1, wave1, color='tab:blue')
    ax2.plot(timestep2, wave2, color='tab:orange')
    ax3.plot(timestep1, marks1, color='tab:blue')
    ax3.plot(timestep2, marks2, color='tab:orange')
    
    fig.tight_layout()



    


# next step:
# x compensate
# x cst to ramp
# x plot
# x plot with highlight
# x plot with superpose
# x ui sweep
# - better draw pulse
# - generator

# - test python2/python3
    