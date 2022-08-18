# import sys

import Pulse_V2
from Pulse_V2 import *
import function_util as futil

########################
######load instrument###
########################

# awg = instruments.tektronix_AWG('TCPIP0::AWG5200-9841.mshome.net::inst0::INSTR')
# rto = instruments.rs_rto_scope('USB0::0x0AAD::0x0197::1329.7002k14-300206::INSTR')
# Be Careful that impedance is on High Z on the AWG

# code line to delete a waveform in the awg
awg.waveform_delete('Test') 



#############################
###Create readout Pulse   ###
#############################
timelist=array([100e-6,100e-6,100e-6]) #time duration of each step
steplist=array([-0.05,0,0.05]) #voltage value of each step
sample_rate=320e6

pulse_seq = PulseReadout(awg, steplist, timelist,sample_rate=sample_rate,pulsefilename='Test',ch=1,reshape=False)

#############################
###    Plotting Pulses  ###
#############################
futil.plot_pulse_seq([pulse_seq])

# %time sweep(pulse_seq.devAmp,-0.050,.05, 5, filename='test_basic_%T.txt', out=rto.fetch, async=True, close_after=True,beforewait=0.1)


def test_run_frag(awg,rto):
    s,t,m=Single_Pulse_frag(timelist,steplist,-0.05,0.05,100)
    pulse_seq = PulseReadout(awg, s, t,sample_rate=320e6,pulsefilename='Test',ch=1,reshape=False)
    awg.waveform_marker_data.set(m,wfname='Test')
    awg.wait_for_trig()
    sleep(sum(t))
    get(rto.fetch, filename='test_segmentation_%T.txt')


# %time sweep(pulse_seq.devAmp,-0.050,.05, 5, filename='test_basic_%T.txt', out=rto.fetch, async=True, close_after=True,beforewait=0.1)
###################################################
################Trace du graph ####################
####################################################  
"""
gate=0 # Voltage de la grille pour centrage 

vd=readfile(r'C:\Projets\Composant\TestAWG_TEKTRO\20220210\test_gated_long_*_rto_fetch_*.txt')
for i in vd[1]:
    plot(vd[0,0],i, '-o')
fig = plt.figure(figsize=[8,8])
ax = fig.add_subplot(111)
ax.axes.tick_params(labelsize=20)
im = ax.imshow(vd[1],
    extent=(0,sum(timelist),gate+min(steplist),gate+max(steplist)),
    aspect="auto",
    origin="lower",
    cmap="RdBu_r")
cbar = fig.colorbar(im)
cbar.set_label(r"I nA",fontsize=20)
cbar.ax.tick_params(labelsize=20) 
ax.set_xlabel('Time (s)', fontsize=20)
ax.set_ylabel('(V)', fontsize=20)
plt.show()
"""