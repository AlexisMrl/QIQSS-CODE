from Shapes import *
from copy import deepcopy
import matplotlib.pyplot as plt
from src.Model import *

class Segment(object):
    _id = 0
    name = 'segment'
    duration = 0.
    offset = 0.
    mark = (0., 0.)
    waveform = None
    envelope = None
    sweep_dict = {}
    to_ramp = False

    def __init__(self, duration=0, offset=0, waveform=None, envelope=None,
                mark=(0, 0), sweep_dict={}, to_ramp=False):
        self._id = Segment._id
        Segment._id += 1
        self.name = 'segment_' + str(self._id)
        self.duration = duration
        self.offset = offset
        self.mark = mark
        self.waveform = waveform
        self.envelope = envelope
        self.sweep_dict = {key:val for key, val in sweep_dict.items()}
        self.to_ramp = to_ramp

    def getWave(self, sample_rate, to_ramp_value=0.):
        if self.duration == 0: return np.array([])
        envelope_wave = self.envelope.getWave(sample_rate, self.duration) \
            if self.envelope else [1]*int(self.duration*sample_rate)
        waveform_wave = self.waveform.getWave(sample_rate, self.duration) \
            if self.waveform else [1]*int(self.duration*sample_rate)
        offset_wave = self.offset * np.ones(int(self.duration*sample_rate))
        if self.to_ramp:
            offset_wave *= np.linspace(self.offset, self.offset+to_ramp_value*self.duration, len(offset_wave))
        if self.envelope is None and self.waveform is None:
            return offset_wave * np.ones(int(self.duration*sample_rate))
        return waveform_wave * envelope_wave + offset_wave
    
    def getArea(self):
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
        string = "Segment(" \
                + "duration=" + str(self.duration) + ", " \
                + "offset=" + str(self.offset) + ", " \
                + "mark=" + str(self.mark) + ", " \
                + "waveform=" + str(self.waveform) + ", " \
                + "envelope=" + str(self.envelope) + ", " \
                + "sweep_dict=" + str(self.sweep_dict) + ") "
        return string


class Pulse(object):
    # A pulse is a concatenation of Segments

    def __init__(self, *segments):
        self.segments = []
        self.duration = 0.
        self.addSegment(*segments)
        # a sweep pulse is also a pulse so:
        self.nb_rep = 1 # to keep track of the number of repetitions
        self.sub_pulse_seg_count = 0 # to keep track of the number of segments in a sub pulse
        self.compensate = 0. # to keep track of the compensation value
    
    def addSegment(self, *segments):
        for segment in segments:
            self.segments.append(segment)
            self.duration += segment.duration
    
    def removeSegment(self, i_segment):
        self.duration -= self.segments[i_segment].duration
        self.segments.pop(i_segment)
    
    def getWave(self, sample_rate, to_ramp_value=0.):
        wave = np.array([])
        for segment in self.segments:
            wave = np.concatenate((wave, segment.getWave(sample_rate, to_ramp_value=to_ramp_value)))
        return wave
    
    def getWaveNormalized(self, sample_rate, to_ramp_value=0.,
                          norm_low=-1,
                          norm_high=1):
        wave = self.getWave(sample_rate, to_ramp_value=to_ramp_value)
        wave_min, wave_max = min(wave), max(wave)
        wave = (wave - wave_min) / (wave_max - wave_min)
        return wave
    
    def getMarks(self, sample_rate, val_low=-1, val_high=0):
        marks = np.array([])
        for segment in self.segments:
            marks = np.concatenate((marks, segment.getMarks(sample_rate, val_low, val_high)))
        return marks
    
    def getTimestep(self, sample_rate):
        return np.linspace(0., self.duration, len(self.getWave(sample_rate)))
    
    def getIndexes(self, sample_rate):
        ret = []
        start = 0
        for seg in self.segments:
            end = start + len(seg.getWave(sample_rate))
            ret.append([start, end-1])
            start = end
        return ret
    
    def getSubPulse(self, i_sub_pulse):
        sub_pulse = Pulse()
        sub_pulse.segments = []
        segments = self.segments[i_sub_pulse*self.sub_pulse_seg_count:(i_sub_pulse+1)*self.sub_pulse_seg_count]
        sub_pulse.addSegment(*segments)
        return sub_pulse
    
    def _genSequenceSweep(self, segments, nb_rep):
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
        # Generate another Pulse composed of a long sequence of segments
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
                pulse_area = sum([seg.getArea() for seg in new_segments])
                print pulse_area
                comp_duration = pulse_area/abs(compensate)
                comp_segment = Segment(duration=comp_duration, offset=compensate)
                new_segments.append(comp_segment)
            sequence.addSegment(*new_segments)
        return sequence

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
    