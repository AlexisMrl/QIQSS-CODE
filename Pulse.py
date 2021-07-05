import pyHegel
import re
import glob
import sys
import os.path
import pylab
from pylab import*
from matplotlib.widgets import Slider, Button, RadioButtons
from pyHegel import*
from pyHegel.util import readfile
from pyHegel.commands import sweep
from io import StringIO


class PulseReadout(object):
    """
    this defines the pulse sequence send the AWG
    Parameter : 
    AWG instrument ; steplist of the waveform ; timelist of the waveform
    change index = index for the step that to sweep
    sample rate
    Change the steplist by steplist =  ***
    The set and get defines the value of the steplist at the change index
    Creating the pulse DOES NOT loads it automaticaly. you have to perform a set
    """

    def __init__(self, awg, steplist, timelist, change_index, ampl, sample_rate=100,pulsefilename='test.arb',ch=1,reshape=True):
        self.awg = awg
        self.steplist = steplist
        self.timelist = timelist
        self.change_index = change_index
        self.ampl = ampl
        self.sample_rate = sample_rate
        self.pulsefilename= pulsefilename
        self.ch=ch
        self.reshape=reshape
        self.devAmp = instruments.FunctionWrap(self.set_steplist, self.get_steplist, basedev=self.awg, min=-self.ampl, max=self.ampl)
        self.devtime = instruments.FunctionWrap(self.set_timelist, self.get_timelist, basedev=self.awg, min=0, max=sum(timelist))
        if len(steplist) != len(timelist):
            raise ValueError('number of step not the same size as the duration time list')
        if  min(timelist) < (1.0/sample_rate):
           raise ValueError('Sample rate too low for time resolution required')
        # pulse_readout(self.awg, self.steplist, self.timelist, self.sample_rate, self.ampl,self.pulsefilename,self.ch)
   
    @property
    def steplist(self):
        return self._steplist
    @steplist.setter
    def steplist(self, steplist):
        self._steplist = array(steplist).copy()
    def set_steplist(self, val):
        steplist = self._steplist
        steplist[self.change_index] = val
        self.ampl=(max(steplist)-min(steplist))
        pulse_readout(self.awg, steplist, self.timelist, self.sample_rate, self.ampl,self.pulsefilename,self.ch,self.reshape)
    def get_steplist(self):
        return self._steplist[self.change_index]

    @property
    def timelist(self):
        return self._timelist
    @timelist.setter
    def timelist(self,timelist):
        self._timelist = array(timelist).copy()
    def set_timelist(self,val):
        timelist = self._timelist
        timelist[self.change_index] = val
        pulse_readout(self.awg, self.steplist, timelist, self.sample_rate, self.ampl,self.pulsefilename,self.ch)
    def get_timelist(self):
        return self._timelist[self.change_index]

class PulseRabi(object):
    """
    this defines the Rabi pulse sequence send the AWG
    Parameter : 
    AWG instrument ; steplist of the waveform ; timelist of the waveform
    freq= modulation frequench
    sample rate
    ampl = amplitude
    phase
    start_time= delay before the modulation
    total_time= total time of the pulse sequence (for later puprose)
    The set and get defines the value of the plateau time of the rabi pulse
    Creating the pulse DOES NOT loads it automaticaly. you have to perform a set
    """

    def __init__(self, awg, freq=10e6,plateau_time=1e-6,sample_rate=250e6,ampl=0.5,phase=0,start_time=0,total_time=2e-6,pulsefilename='RabiTest.arb',steplist=None):
        self.awg = awg
        self.freq = freq
        self.plateau_time = plateau_time
        self.start_time= start_time
        self.total_time = total_time
        self.sample_rate = sample_rate
        self.ampl = ampl
        self.phase= phase
        self.pulsefilename= pulsefilename
        self.steplist=steplist
        self.dev= instruments.FunctionWrap(self.set_plateau_time, self.get_plateau_time, basedev=self.awg, min=0, max=self.total_time)
        if total_time < plateau_time:
            raise ValueError('plateau_time superior to total pulse time')
    @property
    def plateau_time(self):
        return self._plateau_time
    @plateau_time.setter
    def plateau_time(self,plateau_time):
        self._plateau_time = plateau_time
    def set_plateau_time(self,val):
        plateau_time = self._plateau_time
        plateau_time = val
        self.steplist=pulse_rabi(self.awg, self.freq, plateau_time, self.ampl,self.sample_rate, self.phase,self.start_time,
                    self.total_time, self.pulsefilename)
    def get_plateau_time(self):
        return self._plateau_time
    
    def set_total_time(self,val):
        self.total_time=val
        self.steplist=pulse_rabi(self.awg, self.freq, self.plateau_time, self.ampl,self.sample_rate, self.phase,self.start_time,
                self.total_time, self.pulsefilename)
    def get_total_time(self):
        return self.total_time

    def set_freq(self,val):
        self.freq=val
        self.steplist= pulse_rabi(self.awg, self.freq, self.plateau_time, self.ampl,self.sample_rate, self.phase,self.start_time,
                self.total_time, self.pulsefilename)
    def get_freq(self):
        return self.freq

    def set_phase(self,val):
        self.phase=val
        self.steplist=pulse_rabi(self.awg, self.freq, self.plateau_time, self.ampl,self.sample_rate, self.phase,self.start_time,
                self.total_time, self.pulsefilename)
    def get_phase(self):
        return self.phase              

def create(amp, sample_rate, data,fil):
    """
    this creates the string to send to the awg for loading the waveform
    Takes in parameters : amplitude, sample_rate and data= array of int16 value
    """
    res = """Channel Count:1
    Sample Rate:%s
    High Level:%s
    Low Level:%s
    Data Type:"short"
    Filter:"%s"
    Data Points:%i
    Data:
 """%(sample_rate, min(data/32767 * amp)+amp,  min(data/32767 * amp),fil,len(data))
    s = StringIO()
    np.savetxt(s, data, fmt='%i')
    res += s.getvalue()
    return res.replace('\n', '\r\n')

def pulse_readout(awg1, steplist, timelist, sample_rate, ampl,filename,ch,reshape=False):
    """
    This function takes  the steplist convert it in a 16bytes values of correct length
    regarding to time list. write the file and send it to awg then load the waveform
    Parameters :
    awg1= instrument
    steplist= array of step voltage value
    timelist = array of time duration of each step
    sample_rate
    ampl= amplitude
    """
    if reshape:
        timelist = reshape_time(self.timelist,steplist)
        print('Change timelist : {}', timelist)
    
    total_time = sum(timelist)
    res = []
    ampl=max(steplist)
    print(ampl)
    for a,t in zip(steplist, timelist):
        res.append(zeros(int(t*sample_rate), dtype=int)+int(a*32767/ampl))
    res = np.concatenate(res)
    
    res = where(res < -32767, -32767, res)
    res = where(res>32767, 32767, res)
    pulsedata = create(ampl, sample_rate, res,fil='off')
    FILE=r'int:\%s'%(filename)
    awg1.send_file(FILE, src_data=pulsedata, overwrite=True)
    awg1.arb_load_file(FILE, clear=True,ch=ch)
    awg1.set_offset=0

def pulse_rabi(awg1,freq,plateau_time,ampl,sample_rate,phase,start_time,total_time,filename,IQ=True,phaseDiff=90):
    """
    This generate the right timelist and steplist for a rabi pulse
    implying you use a ssb mixer
    """
    if start_time !=0:
        start_time = start_time + plateau_time/2

    timelist, vI = np.zeros(int(sample_rate*total_time)),np.zeros(int(sample_rate*total_time))
    vQ=np.zeros(int(sample_rate*total_time))
    phaseDiff = phaseDiff*np.pi/180



    index = np.arange(max(np.round((start_time-plateau_time/2)*sample_rate), 0),
                    min(np.round((start_time+plateau_time)*sample_rate), sample_rate*total_time))
    index=np.int0(index)
    pulse_time = index/sample_rate
    pulse_value = (pulse_time >= (start_time-plateau_time)) & (pulse_time < (start_time+plateau_time))
    pulse_value = ampl * pulse_value
    freq = 2*np.pi*freq
    vI_ssbm = pulse_value * (np.cos(freq*pulse_time - phase))
    vQ_ssbm =-pulse_value * (np.sin(freq*pulse_time - phase + phaseDiff))
    timelist=np.linspace(0,total_time,int(sample_rate*total_time))
    vI[index] += vI_ssbm
    vQ[index] += vQ_ssbm
    plot(timelist*1e6,vI,'-o')
    plot(timelist*1e6,vQ,'-o')
    plt.show()
    
    #creat and send the data set to awg 
    dataI=[]
    dataQ=[]
    for i,q in zip (vI,vQ):
        dataI.append(int(i*32767/ampl))
        dataQ.append(int(q*32767/ampl))
    dataI = where(dataI < -32767, -32767, dataI)
    dataI = where(dataI>32767, 32767, dataI)
    dataQ = where(dataQ < -32767, -32767, dataQ)
    dataQ = where(dataQ>32767, 32767, dataQ)
    pulsedata = create(ampl, sample_rate, dataI,fil='normal',ch=1)
    FILE=r'int:\%s'%(filename)
    awg1.send_file(FILE, src_data=pulsedata, overwrite=True)
    awg1.arb_load_file(FILE, clear=True)

    #Envoie la waveform dephase au ch=2
    if IQ:
        pulsedata = create(ampl, sample_rate, data,fil='normal',ch=2)
        FILE=r'int:\%s'%(filename)
        awg1.send_file(FILE, src_data=pulsedata, overwrite=True)
        awg1.arb_load_file(FILE, clear=True)

    return steplist




def reshape_time(timelist,steplist):
    mean=sum((x*y) for x,y in zip(timelist,steplist))
    if mean <0 :
        i=argmax(steplist)
        steplist_copy=np.delete(steplist,i)
        timelist_copy=np.delete(timelist,i)
        timelist[i]=(- (sum((x*y) for x,y in zip(timelist_copy,steplist_copy)))/steplist[i])
    if mean >0 :
        i=argmin(steplist)
        steplist_copy=np.delete(steplist,i)
        timelist_copy=np.delete(timelist,i)
        timelist[i]=(- (sum((x*y) for x,y in zip(timelist_copy,steplist_copy)))/steplist[i])

    return timelist

########################################################
############ DMM MIS A LA BONNE CONFIGURATION #########
#######################################################

def dmm_settings(dm, meas_time, Voltage_range=0.1,sample_interval=20e-6):
    
    """
    Dmm settings for pulse sequence measurement
    dm= instrument
    meas_time = total time of pulse sequence
    Voltage_range = voltage range
    sample_interval = time between each sample (default at minimum
    """

    dm.range.set(Voltage_range)
    dm.aperture.set(2e-5)
    dm.voltdc_impedance_autoHigh.set(False)
    dm.zero.set(False)
    dm.trig_src.set('EXTernal')
    dm.trig_delay.set(2e-5)
    dm.sample_timer.set(sample_interval)
    dm.sample_count.set(meas_time/sample_interval)


##########################################################
################## Sequence de pulse################################
#########################################################

# def pulseseq(awg1,steplist, timelist, Sr, ampl, awg_file='temp'):
    
#     """
#     This creates the pulse sequence 
#     awg1 = instrument name
#     Steplist= array of value of each step in V
#     timelist= array of time duration of each step in volt
#     Sr= Sample rate of the AWG in Sa/s
#     Ampl= Amplitude of the awg in V 
#     awg_file = name of the file send to the awg = temp by default
#     """
    
#     if steplist.size != timelist.size:
#         raise ValueError('number of step not the same size as the duration time list')

#     total_time= sum(timelist)
#     sizeseq=total_time*Sr
#     seq=array([],dtype=int16)
#     for index, i in enumerate(steplist) : 
        
#         if i==0:
#             val=0
#         else:
#              val=int(round(32767*i/ampl))
#         seq=np.concatenate((seq, np.array([val]*(int(Sr*timelist[index])))))

#     createFile(awg_file,ampl,Sr,seq)
#     awg1.send_file('TEST.arb',local_src_file=awg_file,overwrite=True)
#     awg1.arb_load_file('INT:\TEST.arb',clear=True)

#     return seq



# def createFile(file,Amp, Sr, seq):
   
#     """
#     This creates the file that will be send to the AWG.
#     It contains information on SR, Amplitude, and the sequene
#     The file is overwritten every new waveform generated
#     """

#     open(file, 'w').close()
#     f = open(file,'a+')
#     f.write('Channel Count:1 \n')
#     f.write('Sample Rate:'+ str(Sr)+'\n')
#     f.write('High Level:'+ str(Amp/2)+'\n')
#     f.write('Low Level:'+ str(-Amp/2)+'\n')
#     f.write('Data Type:"short"\n')
#     f.write('Filter:"off"\n')
#     f.write('Data Points:10\n')
#     f.write('Data:\n')
#     for i in seq:
#         f.write(str(i)+'\n')

#     f.close()
#     return