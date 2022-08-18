# -*- coding: utf-8 -*-

########################## Copyrights and license ############################
#                                                                            #
# Copyright Claude Rohrbacher <claude.rohrb@gmail.com>                       #
# January 2022                                                               #
# This file is part of Code Pulse
#                                                                            #       
##############################################################################
import numpy as np

class PulseReadout(object):
    """
    this defines the pulse sequence send the AWG for readout pulses. This code is only designed to work
    with AWG TEKTRO 5008 (to be corrected)
    Parameter : 
    AWG instrument 
    ; steplist of the waveform ; timelist of the waveform
    change index = index for the step that to sweep
    sample rate = sample_rate is automatically corrected so that the total waveform is a  multiple of 64
    Change the steplist by steplist =  ***
    pulsefilneame = name of the arbitrary waveform in the AWG
    ch = output channel in the AWG
    trig = this pulse pulse generates the trigger. 
    devAmp = device a sweep pour modifier l'amplitude du pulse
    devTime = device a sweep pour modifier le temps du pulse
    """

    def __init__(self, awg, steplist, timelist, change_index=1, sample_rate=2.5e9,pulsefilename='test',ch=1,trig=True,gain=1):
        self.awg = awg
        self.steplist = steplist
        self.timelist = timelist
        self.change_index = change_index
        self.sample_rate = sample_rate
        self.pulsefilename= pulsefilename
        self.ch=ch
        self.trig=trig

        self.devAmp = instruments.FunctionWrap(self.set_steplist, self.get_steplist, basedev=self.awg)
        self.devtime = instruments.FunctionWrap(self.set_timelist, self.get_timelist, basedev=self.awg, min=0, max=sum(timelist))
        self.type= 'Readout Pulse'
        self.gain=gain

        if len(steplist) != len(timelist):
            raise ValueError('number of step not the same size as the duration time list')
        if  min(timelist) < (1.0/sample_rate):
           raise ValueError('Sample rate too low for time resolution required')     

         # New timelist for sample = *64
        N=round(64*ceil(self.sample_rate*sum(self.timelist)/64)-self.sample_rate*sum(self.timelist))
        self.timelist[-1]= self.timelist[-1]+N/sample_rate
        print('new timelist is {}'.format(self.timelist))

        # Initialise le sample rate, create waveform, load it to channel
        if self.awg is None:
            print('Carefull no awg is selected, set and get function won t  work')
        else:
            self.awg.sample_rate.set(self.sample_rate)
            pulse_readout(self.awg, self.steplist, self.timelist, self.sample_rate,self.pulsefilename,self.ch,self.gain)
            self.awg.list_waveforms.get()
            self.awg.channel_waveform.set(self.pulsefilename,ch=self.ch)

    @property
    def steplist(self):
        return self._steplist
    @steplist.setter
    def steplist(self, steplist):
        self._steplist = np.array(steplist).copy()
    def set_steplist(self, val):
        steplist = self._steplist
        steplist[self.change_index] = val
        pulse_readout(self.awg, steplist, self.timelist, self.sample_rate,self.pulsefilename,self.ch,self.gain)
        if self.trig==True:
            self.awg.wait_for_trig()

    def get_steplist(self):
        return self._steplist
    @property
    def timelist(self):
        return self._timelist
    @timelist.setter
    def timelist(self,timelist):
        self._timelist = np.array(timelist).copy()
    def set_timelist(self,val):
        timelist = self._timelist
        timelist[self.change_index] = val
        self.awg.run(enable=False)
        pulse_readout(self.awg, self.steplist, timelist, self.sample_rate,self.pulsefilename,self.ch,self.gain)
        self.awg.run(enable=True)
    def get_timelist(self):
        return self._timelist

class PulseRabi(object):
    """
    this defines the Rabi pulse sequence send the AWG
    Parameter : 
    AWG instrument ; steplist of the waveform ; timelist of the waveform
    pulse_shape : type of pulse send depending of mixer used : 'square' 'gaussian', 'ramp'
    freq= modulation frequency, irrelevent if ssb = false
    sample rate
    ampl = amplitude
    phase
    start_time= delay before the modulation
    total_time= total time of the pulse sequence (for later puprose)
    ssb= if ssb mixer is used
    The set and get defines the value of the plateau time of the rabi pulse
    Creating the pulse DOES NOT loads it automaticaly. you have to perform a set
    """

    def __init__(self, awg, pulse_shape='square',plateau_time=1e-6,sample_rate=250e6,ampl=0.5,phase=0,start_time=0,total_time=2e-6,ch=1,pulsefilename='RabiTest',ssb=False,freq=10e6):
        self.awg = awg
        self.pulse_shape=pulse_shape
        self.plateau_time = plateau_time
        self.start_time= start_time
        self.total_time = total_time
        self.sample_rate = sample_rate
        self.ampl = ampl
        self.phase= phase
        self.ch=ch
        self.pulsefilename= pulsefilename
        self.ssb= ssb
        self.freq = freq
        self.steplist=[]
        self.dev= instruments.FunctionWrap(self.set_plateau_time, self.get_plateau_time, basedev=self.awg, min=0, max=self.total_time)
        self.type= 'Rabi Pulse'
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


def pulse_readout(awg1, steplist, timelist, sample_rate,filename,ch,gain):
    """
    This function takes  the steplist normalize it and send the waveform to the awg
    then it resample the waveform to have correct time
    Parameters :
    awg1= instrument
    steplist= array of step voltage value
    timelist = array of time duration of each step
    sample_rate 
    resample : if True, send a fixed size waveform and resample after in AWG, used for timelist bigger than 10ms !
    """
    # Normalisation
    steplist=steplist*gain
    ampl=(max(abs(steplist)))
    steplist=(steplist/(ampl))
    res=[]


    for a,t in zip(steplist, timelist):
        res.append(zeros(int(t*sample_rate), dtype=int)+float(a))
    res = np.concatenate(res)
    awg1.volt_ampl.set(ampl, ch=ch)
    if filename in get(awg.list_waveforms):
        awg1.waveform_data.set(res, wfname=filename)
    else:
        awg1.waveform_create(res,filename,marker=(0,-1))


def pulse_rabi(awg1,freq,plateau_time,ampl,sample_rate,phase,start_time,total_time,filename,IQ=False,phaseDiff=90):
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

