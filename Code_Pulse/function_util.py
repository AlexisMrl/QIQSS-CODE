
# -*- coding: utf-8 -*-

########################## Copyrights and license ############################
#                                                                            #
# Copyright Claude Rohrbacher <claude.rohrb@gmail.com>                       #
# January 2022                                                               #
# This file is part of Code Pulse
#                                                                            #       
##############################################################################

# from this import d
# import numpy as np 
# import matplotlib
# from matplotlib import*
# import matplotlib.pyplot as plt
# import Pulse_V2
# from Pulse_V2 import *

# from time import time
# from typing import Concatenate


def single_Pulse_frag(timelist,steplist,start,stop,npts,sample_rate,index=1,wait_time=0,rshape=False,ramp=[]):
    """ This function generate an array of readout pulse with different read level for segmentation
    measurement on the oscilloscope.
    start, stop and npt are the sweep parameters of the read level. 
    index : array index to sweep
    wait_time : wait_time before each pulse
    reshape : bias-tee reshape
    ramp= [] parameter of the ramp for bias-tee compensation see ramp function for more detail
    Return, new steplist, timelist, and necessary markers
    
     """

    sweep_value= np.linspace(start,stop,npts)
    steplist_copy=steplist.copy()
    new_steplist, new_timelist=np.array([]),np.array([])
    marker=[]
    for i in sweep_value:
        
        steplist_copy[index]=i
        if rshape:
            timelist_copy=reshape(timelist,steplist_copy)
        else:
            timelist_copy=timelist.copy()
        new_steplist=np.append(new_steplist,steplist_copy)
        new_timelist=np.append(new_timelist,timelist_copy)
        total_time=sum(timelist_copy)

        #Marker
        res=[]
        for j in (timelist_copy):
            res.append(zeros(int(j*sample_rate), dtype=int))
        res = np.concatenate(res)        
        marker_temp=int(len(res))*[0]
        marker_temp[0:int(len(res)/2)] = int(len(res)/2)*[1]
        marker= marker+marker_temp
        #Wait time
        if wait_time != 0:
            new_steplist=np.append(new_steplist,0)
            new_timelist=np.append(new_timelist,[wait_time])
            marker=marker+int(wait_time*sample_rate)*[0]

    
    wavstr = array([i<<7 for i in marker], dtype=np.uint8)

    N=round(64*ceil(sample_rate*sum(new_timelist)/64)-sample_rate*sum(new_timelist))
    new_timelist[-1]= new_timelist[-1]+N/sample_rate
    res=[]
    for a,j in zip(new_steplist, new_timelist):
        res.append(zeros(int(j*sample_rate), dtype=int)+float(a))
    res = np.concatenate(res)
    wavstr=wavstr[0:len(res)]

    return new_steplist,new_timelist,wavstr
    

def plot_pulse_seq(pulse_list):
    """
    PLot the full pulse sequence sent.
    pulse_list= full list of pulses
    """
    fig=plt.figure()
    ax=fig.add_subplot(111)
    for i in pulse_list:
        res=[]
        for a,t in zip(i.steplist, i.timelist):
            res.append(np.zeros(int(t*i.sample_rate), dtype=int)+float(a))
        res=np.concatenate(res)
        time=np.linspace(0,len(res)/pulse_list[0].sample_rate,len(res))*1e6
        ax.plot(time,res,'-o',label=i.type)
    ax.set_xlabel('time (us)')
    ax.set_ylabel('V')
    ax.legend() 


def comment_generator(lst, com=''):
    """
    Generate a comment to put as the headers of your file
    insert different list of pulses
    """
    comment_string =''
    for i in lst:
        comment_string=comment_string+i.type +': steplist = ' + str(i.steplist)+ '; timelist' + str(i.timelist) + '\n'
    comment_string=comment_string+com
    return comment_string


def reshape(timelist,steplist):
    """
    Average the pulse to 0 (only increase the total time)
    only increase the time of the last pulse 
    """
    timelist_copy=timelist.copy()
    mean=sum((x*y) for x,y in zip(timelist,steplist))
    if mean != 0:
        timelist_copy[-1]=np.abs(((sum((x*y) for x,y in zip(timelist[:-1],steplist[:-1]))))/steplist[-1])
    return timelist_copy    

def run_frag(awg,rto,timelist,steplist,param,sample_rate,index=1,wait_time=0.1,rshape=False):
    """
    This function create a pulse sequence and send it to the awg and run the measurement
    Awg = awg
    rto= oscilloscope
    for the other argument see single_Pulse_frag
    """
    awg.waveform_delete('Test') 
    s,t,m=single_Pulse_frag(timelist,steplist,param[0],param[1],param[2],sample_rate,index=index,wait_time=wait_time,rshape=rshape)
    pulse_seq = PulseReadout(awg, s, t,sample_rate=sample_rate,pulsefilename='Test',ch=1,gain=gain)
    awg.waveform_marker_data.set(m,wfname='Test')
    wait(1)
    awg.run()
    
    return s,t,m

def run_test(awg,rto,fn='_%T.txt'):
    rto._async_trig()
    wait(.1)
    awg.wait_for_trig()
    rto.wait_after_trig()
    rto._async_cleanup_after()
    x= get(rto.fetch,history='all',filename=fn,bin='.npy')
    return x


def bf(data):
    rto._async_trig()
    wait(.1)
    awg.wait_for_trig()
    rto.wait_after_trig()
    rto._async_cleanup_after()