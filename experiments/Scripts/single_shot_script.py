# %%
import sys
sys.path.append('C:\Codes\QIQSS-CODE\experiments')
from Pulses.Builder import *

from pyHegel.commands import *

# %% INSTRUMENTS
awg = instruments.tektronix.tektronix_AWG('USB0::0x0699::0x0503::B030793::0')
ats = instruments.ATSBoard(systemId=1, cardId=1)

# %% VARIABLES
path = "./logs" # path where to save the data
AWG_SR = 32e4

# %% 1) SPIN-TAIL MAPS

read_list = np.linspace(0.792, 0.798, 151)

# pulse shaping
load = Segment(duration=0.001, waveform=Ramp(val_start=0.00, val_end=0.00), offset=0.000, mark=(0.8, 1.0))
read = Segment(duration=0.0003, waveform=Ramp(val_start=0.00, val_end=-0.00038), offset=-0.002)
empty = Segment(duration=0.0002, waveform=Ramp(val_start=0.000, val_end=-0.00138), offset=-0.004)
pulse = Pulse(load, read, empty)
pulse.addCompensationZeroMean(0.02)
#plotPulse(pulse, AWG_SR)
sendSeqToAwg(awg, pulse)

# ats
configATS(ats)
ats.acquisition_length_sec.set(0.0007)
ats.nbwindows.set(1)


final_map = []

awg.run(True)
for i, read_lvl in enumerate(read_list):
    P1.set(read_lvl)
    print('i:{}, P1={}'.format(i, level))
    
    image, time = getATSImage(with_time=True) # [[trace0], [trace1], ..., [traceNWindow]], [t0, t1, ..., t_SR*AcquisitionLength]    

    image = gaussianLineByLine(image, sigma=20)
    #threshold = 42
    threshold = estimateDigitThreshold(image, show_plot=True)
    image = digitize(image, threshold)
    trace = averageLines(image)
    final_map.append(trace)
awg.run(False)

final_map = np.array(final_map)
filename = saveNpz(path, "pulse_P1_sweep", final_map, x_axis=time, y_axis=read_list, metadata={'pulse':str(pulse), 'ats':ats})

npzdict = loadNpz(filename)
plotNpzDict(npzdict)


# %% 2) SPIN READOUT

# pulse shaping
load = Segment(duration=0.0002, waveform=Ramp(val_start=0.00, val_end=0.00015), offset=0.002)
read = Segment(duration=0.0003, waveform=Ramp(val_start=0.00, val_end=-0.000), offset=-0.000, mark=(0.0, 1.0))
empty = Segment(duration=0.0002, waveform=Ramp(val_start=0.000, val_end=-0.0015), offset=-0.002)
pulse = Pulse(load, read, empty)
pulse.addCompensationZeroMean(-0.01)
#plotPulse(pulse, AWG_SR)
sendSeqToAwg(awg, pulse)

# ats
configATS(ats)
ats.acquisition_length_sec.set(0.0003)
ats.nbwindows.set(500)

threshold = 46

awg.run(True)
data_all, time = getATSImage(ats, with_time=True) # [[trace0], [trace1], ..., [traceNWindow]], [t0, t1, ..., t_SR*AcquisitionLength]
awg.run(False)

data_filt = gaussianLineByLine(data_all, sigma=20)
data_digit = digitize(data_filt, threshold)

plt.plot(averageLines(data_all))
plt.plot(averageLines(data_digit))

filename = saveNpz(path, "readout_digit", data_digit, x_axis=time, metadata={'pulse':str(pulse), 'ats':ats})

npzdict = loadNpz(filename)
plotNpzDict(npzdict)

events_all = countEvents(data_digit, time)
events_spins = countEvents(data_digit, time, one_blip_only=True)
print(events_spins)




# %% 3) T1

len_list = np.linspace(0.00001, 0.001, 400)
twait_list = [] # dynamically constructed in the for loop

# pulse shaping
load = Segment(duration=0.1, waveform=Ramp(val_start=0.00, val_end=0.00), offset=0.000)
read = Segment(duration=0.0003, waveform=Ramp(val_start=0.00, val_end=-0.0004), offset=-0.002, mark=(0., 0.2))
empty = Segment(duration=0.001, waveform=Ramp(val_start=0.000, val_end=-0.00138), offset=-0.004)
pulse = Pulse(load, read, empty)
pulse.addCompensationZeroMean(0.2)
sendSeqToAWG(pulse)

# ats
configATS(ats)
ats.acquisition_length_sec.set(0.0003)
ats.nbwindows.set(500)

threshold = 46
maps=[]
spin=[]

for i, load_time in enumerate(len_list)):
    print('i:{}, load_time={}'.format(i, load_time))
    
    load = Segment(duration=load_time, waveform=Ramp(val_start=0.00, val_end=0.00), offset=0.000)
    read = Segment(duration=0.0003, waveform=Ramp(val_start=0.00, val_end=-0.0004), offset=-0.002, mark=(0., 0.2))
    empty = Segment(duration=0.0002, waveform=Ramp(val_start=0.000, val_end=-0.00138), offset=-0.004)
    pulse = Pulse(load, read, empty)
    pulse.addCompensationZeroMean(0.02)
    
    twait_time = load_time + pulse.segments[-1].duration # load_time + compenstation_time
    twait_list.append(twait_time)
    
    sendSeqToAWG(pulse, run_after=True)
    
    data_all, time = getATSImage(ats, with_time=True) # [[trace0], [trace1], ..., [traceNWindow]], [t0, t1, ..., t_SR*AcquisitionLength]

    data_filt = gaussianLineByLine(data_all, sigma=20)
    data_digit = digitize(data_filt, threshold)

    
    maps.append(data_digit)

    events = countEvents(data_digit, time, one_blip_only=True)
    spin.append(events)

filename = saveNpz(path, "t1_data", maps, metadata={'pulse':str(pulse), 'ats':ats, 'twait_list':twait_list})
filename = saveNpz(path, "spin", spin, metadata={'pulse':str(pulse), 'ats':ats, 'twait_list':twait_list})


    
