import sys

from matplotlib.pyplot import step
import Pulse
reload(Pulse)
from Pulse import *

########################
######load instrument###
########################

#  awg1= instruments.agilent_rf_33522A('TCPIP0::A-33522A-00526.mshome.net::inst0::INSTR')
#  dm = instruments.agilent_multi_34410A('USB0::0x2A8D::0x0101::MY57515472::INSTR')
#  rto= instruments.rs_rto_scope('tcpip::RTO2014-300206.mshome.net::inst0::instr')
# Be Careful that impedance is on High Z on the AWG


timelist=array([10e-3,10e-3,10e-3]) #time duration of each step
steplist=array([-0.5,0,0.5]) #voltage value of each step
ampl=(max(steplist)-min(steplist)) #Amplitude peak
sample_rate=1e4

#reglage des settings du dmm Par defaut sample_interval=20e-6 ; Checker si la slope du trigger= POS
# dmm_settings(dm,sum(timelist), Voltage_range=0.1, sample_interval=100e-6)  

pulse_seq = PulseReadout(awg1, steplist, timelist, 1,ampl,sample_rate,pulsefilename='TestPulsech2.arb',ch=1)
sweep(pulse_seq.devAmp,0,.1, 5, filename='test_%T.txt', out=rto.readval , async=True, close_after=True,beforewait=0.1)


###################################################
################Trace du graph ####################
####################################################  
gate=0 # Voltage de la grille pour centrage 

vd=readfile('test_*_rto_readval_*.txt')
for i in vd[2]:
    plot(i, '-o')
fig = plt.figure(figsize=[8,8])
ax = fig.add_subplot(111)
ax.axes.tick_params(labelsize=20)
im = ax.imshow(vd[2],
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
plt.tight_layout()
 

