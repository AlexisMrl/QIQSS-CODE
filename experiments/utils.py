import time
import numpy as np
from matplotlib import pyplot as plt
from scipy import ndimage

from pyHegel import commands
from pyHegel import fitting, fit_functions
from pyHegel.types import dict_improved


#### INSTRUMENTS ####

#ats = instruments.ATSBoard(systemId=1, cardId=1)
#ats_conf = dict(sample_rate=10e5,
#                input_range=4000) # vertical resolution in mV
def configureATS(ats, input_range=4000, sample_rate=10e5):
    """ apply the default configuration
    """
    if not ats: pass
    ats.active_channels.set(['A','B']) # read on A and B
    ats.buffer_count.set(4) # usually 4
    ats.clock_type.set('INT')
    ats.trigger_delay.set(0) # waiting time after trigger
    ats.trigger_channel_1.set('ext') # channel A trigger on external channel
    ats.trigger_channel_2.set('ext') # channel B trigger on external channel
    ats.trigger_slope_1.set('ascend')
    ats.trigger_slope_2.set('ascend')
    ats.sample_rate.set(sample_rate)
    
    ats.input_range.set(input_range) # vertical resolution in mV [20, 40, 50, 80, 100, 125, 200, 250, 400, 500, 800, 1000, 2000, 2500, 4000, 5000, 8000, 1e4, 2e4, 1.6e4, 2e4, 4e4]
    ats.sample_rate.set(sample_rate)
    
    ats.ConfigureBoard() # apply changes

def getATSImage(ats, with_time=False):
    """ returns an array of shape (nbwindows, samples_per_record)
        ret = [[trace0], [trace1], ..., [tracen]]
    If with_time is True:
        return is [[trace0], [trace1], ..., [tracen]], [t0, t1, ..., tm]
        with t0, ..., tm the timestamp for ONE trace.
    """
    times, indexes, traces = ats.fetch_all.get() #2D array of size (nbwindows+1, samples_per_record)
    nb_windows = ats.nbwindows.get()
    ret = traces.reshape((nb_windows, -1)) # from [trace0, ..., tracen] to [[trace0], ..., [tracen]]
    if with_time:
        time = times[:len(ret[0])]
        time -= time[0]
        return ret, time
    return ret

#awg = instruments.tektronix.tektronix_AWG('USB0::0x0699::0x0503::B030793::0')
def sendSeqToAWG(awg, sequence, channel=1, awg_sr=32e4, wv_name='waveform', plot=False, run_after=True):
    """ Stop the awg then send the sequence (object from Pulse code) to the awg
    If run_after: it play the wave after sending it.
    """
    wv_name += '_' + str(channel)
    wave = sequence.getWaveNormalized(awg_sr)
    wave_max_val = max(abs(sequence.getWave(awg_sr)))
    marks = sequence.getMarks(AWG_SR, val_low=1, val_high=-1)
    
    awg.run(False)
    awg.waveform_create(wave, wv_name, sample_rate=AWG_SR, amplitude=2*wave_max_val*GAIN, force=True)
    awg.waveform_marker_data.set(marks, wfname=wv_name)
    awg.channel_waveform.set(awg_sr,ch=channel)
    awg.volt_ampl.set(2*wave_max_val*GAIN, ch=channel)
    
    awg.sample_rate.set(awg_sr)
    awg.current_wfname.set(wv_name)
    
    if run_after: awg.run(True)
    
    if plot:
        plt.figure()
        plt.plot(wave)
        plt.plot(marks)
        plt.title(wv_name)







#### SIGNAL FILTERING ####

def gaussianLineByLine(image, sigma=20, **kwargs): 
    return np.array([ndimage.gaussian_filter1d(line, sigma, **kwargs) for line in image])

def _doubleGaussian(x, sigma1, sigma2, mu1=0., mu2=0., A1=3.5, A2=3.5):
    """ use for fitting state repartition
    sigma: curvature =1:sharp, =15:very flatten
    mu: center
    A: height
    """
    g1 = fit_functions.gaussian(x, sigma1, mu1, A1)
    g2 = fit_functions.gaussian(x, sigma2, mu2, A2)
    return g1+g2

def estimateDigitThreshold(image, p0=[7, 10, 25, 62, 3.5, 3.5], bins=100, show_plot=True):
    # 1 prepare data
    samples = image.flatten()
    hist, bins = np.histogram(samples, bins=bins, density=True)
    x = np.linspace(0, len(hist)-1, len(hist))
    
    # 2 do the fit
    fit_result = fitting.fitcurve(_doubleGaussian, x, hist, p0)
    fit_curve = _doubleGaussian(x, *fit_result[0])
    
    # 3 find threshold index and value
    A1, A2 = fit_result[0][2], fit_result[0][3]
    threshold_ind = np.argmin(fit_curve[int(A1):int(A2)]) # find the min between the two peaks
    threshold_ind += int(A1) # "recenter" the treshold
    threshold_val = bins[threshold_ind]
    
    # 4 show print return
    if show_plot:
        plt.figure()
        plt.plot(hist)
        plt.plot(fit_curve)
        plt.axvline(x=threshold_ind, color='r', linestyle=':', label='threshold: '+str(threshold_val))
        plt.legend()
    print('Threshold found at x='+str(threshold_val))
    return threshold_val

def digitize(image, threshold):
    """ return the image with values 0 for below TH and 1 for above TH
    """
    bool_image = image>threshold
    int_image = np.array(bool_image, dtype=int)
    return int_image

def averageLines(image):
    """ from [[trace1], ..., [tracen]] to [trace_mean].
        from 2d to 1d.
    example:
        arr = np.array([[1,1,1,1,1],[2,2,2,2,2],[3,3,3,3,3]])
        
        arr.mean(axis=0)
        Out[]: array([2., 2., 2., 2., 2.]) <-- GOOD
        
        arr.mean(axis=1)
        Out[]: array([1., 2., 3.])
    """
    image = np.array(image)
    return image.mean(axis=0)







#### SIGNAL ANALYSIS ####

def countAvgOutTime(data_digit, times):
    """ count the avg time of the first out event given a 2d array:
    data_digit = [[trace0], [trace1], .... ] with traces: list of 0/1
    trace_time: timestamp for one trace; same length as a trace.
    """
    out_time=[]
    
    for trace in data_digit: # trace by trace
        events = np.diff(trace)
        downs = np.where(events == -1)[0] # array of all the down events positions in the trace
        ups = np.where(events == 1)[0] # array of all the up events potisions in the trace
        nb_down = len(downs)
        nb_up = len(up)

        if trace[0] == 0:   # first point of the trace is 0 -> event_out==up and event_in==down
            event_out = ups
            event_in = downs
        elif trace[0] == 1: # first point of the trace is 1 -> event_out==down and event_in==up
            events_out = downs
            events_int= ups

        if len(events_out) > 0:
            out_time.append(times[events_out[0]])

    out_time_std = np.std(out_time)
    out_time_avg = np.mean(out_time)

    return out_time_avg, out_time_std

def countEvents(data_digit, times, one_blip_only=False):
    """ count the number of event in a given a 2d array:
        data_digit = [[trace0], [trace1], .... ] with traces: list of 0/1
    trace_time: timestamp for one trace; same length as a trace.
    return: of the form event_out_avg, event_in_avg, count_exclude
    """
    # 1 count events
    count_event_out = 0
    count_event_in = 0
    count_exclude = 0
    
    for trace in data_digit: # trace by trace
        events = np.diff(trace)
        downs = np.where(events == -1)[0] # array of all the down events positions in the trace
        ups = np.where(events == 1)[0] # array of all the up events potisions in the trace
        nb_down = len(downs)
        nb_up = len(up)

        if trace[0] == 0:   # first point of the trace is 0 -> event_out==up and event_in==down
            event_out = ups
            event_in = downs
        elif trace[0] == 1: # first point of the trace is 1 -> event_out==down and event_in==up
            events_out = downs
            events_int= ups
        
        if one_blip_only and len(events_out) > 1:
            count_exclude += 1
            continue # stop current for loop iteration; go to the next trace
        else:
            count_event_out += len(events_out)
            count_event_in += len(events_in)

    # 2 make stats
    event_out_avg = count_event_out/int(data.shape[0]-count_exclude)
    event_in_avg = count_event_in/int(data.shape[0]-count_exclude)

    return event_out_avg, event_in_avg, count_exclude


#### FILE SAVING/LOADING ####

def saveNpz(path, filename, array, x_axis=None, y_axis=None, metadata={}):
    """ Save array to an npz file.
    metadata is a dictionnary, it can have pyHegel instruments as values: the iprint will be saved.
    """
    if not path.endswith(('/', '\\')):
        path += '/'
    timestamp = time.strftime('%Y%m%d-%H%M%S-')
    fullname = path + timestamp + filename
    
    # formating metadata
    for key, val in metadata.items():
        if isinstance(val, instruments_base.BaseInstrument): # is pyHegel instrument
            metadata[key] = key.iprint()
    metadata['_filename'] = filename
    
    # saving zip
    np.savez(fullname, array=array, x_axis=x_axis, y_axis=y_axis, metadata=metadata)
    
    return fullname+'.npz'
    

def loadNpz(name):
    """ Returns a dictionnary build from the npzfile.
    if saveNpz was used, the return should be:
        {'array': array(),
         'x_axis': array() or None,
         'y_axis': array() or None,
         'metadata': {}}
    """
    if not name.endswith('.npz'):
        name += '.npz'
    npzfile = np.load(name, allow_pickle=True)
    ret =  {}
    for key in npzfile:
        obj = npzfile.get(key)
        try:
            python_obj = obj.item()
            ret[key] = python_obj
        except ValueError:
            ret[key] = obj
    return ret

def plotNpzDict(npzdict):
    """ npz dict of the form:
        {'array': array(),
         'x_axis': array() or None,
         'y_axis': array() or None,
         'metadata': {}}
    """
    array = npzdict.get('array')
    x_axis = npzdict.get('x_axis')
    y_axis = npzdict.get('y_axis')
    imshow(array)
    
def imshow(*arg, **kwargs):
    kwargs['interpolation'] = None
    kwargs['aspect'] = 'auto'
    plt.imshow(*args, **kwargs)
    