
# -*- coding: utf-8 -*-

########################## Copyrights and license ############################
#                                                                            #
# Copyright Claude Rohrbacher <claude.rohrb@gmail.com>                       #
# January 2022                                                               #
# This file is part of Code Pulse
#                                                                            #       
##############################################################################

from this import d
import numpy as np 
import matplotlib
from matplotlib import*
import matplotlib.pyplot as plt
import Pulse_V2
from Pulse_V2 import *

def Single_Pulse_frag(timelist,steplist,start,stop,npts,sample_rate=320e6):
    """ This function generate an array of readout pulse with different read level for segmentation
    measurement on the oscilloscope.
    start, stop and npt are the sweep parameters of the read level. 
    Return, new steplist, timelist, and necessary markers """

    sweep_value= np.linspace(start,stop,npts)
    steplist_copy=steplist
    new_steplist, new_timelist=np.array([]),np.array([])
    res,marker=[],[]
    t=sum(timelist)
    for i in sweep_value:
        steplist_copy[1]=i
        new_steplist=np.append(new_steplist,steplist_copy)
        new_timelist=np.append(new_timelist,timelist)
        marker= marker+int(t*sample_rate)/2*[1]+int(t*sample_rate)/2*[0]
    
    for a,t in zip(new_steplist, new_timelist):
        res.append(zeros(int(t*1e3), dtype=int)+float(a))

    res = np.concatenate(res)
    wavstr = np.array([i<<7 for i in marker], dtype=np.uint8)
    # plot(res)

    return new_steplist,new_timelist,wavstr


def reshape_time(timelist,steplist):
    """ Reshape the timelist to average the readout pulse at zero
    Only increase or decrease the time of the last step
     """
    mean=sum((x*y) for x,y in zip(timelist,steplist))
    if mean!=0:
        T=sum(timelist)
        timelist[-1]=(- (sum((x*y) for x,y in zip(timelist[:-1],steplist[:-1]))))
    return timelist    

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