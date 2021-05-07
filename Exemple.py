import sys
sys.path.append('C:\Users\dphy-dupontferrielab\Claude\CodePulse')
import Pulse
reload(Pulse)
from Pulse import *

########################
######load instrument###
########################

# awg1= instruments.agilent_rf_33522A('TCPIP0::A-33522A-00526.local::inst0::INSTR')
# dm = instruments.agilent_multi_34410A('USB0::0x2A8D::0x0101::MY57515472::INSTR')
# Be Careful that impedance is on High Z on the AWG


timelist=array([50e-6,50e-6,50e-6]) #time duration of each step
steplist=array([0,1,0]) #voltage value of each step
ampl=(max(steplist)) #Amplitude peak
sample_rate=100e6

#reglage des settings du dmm Par defaut sample_interval=20e-6 ; Checker si la slope du trigger= POS
dmm_settings(dm,sum(timelist), Voltage_range=0.1, sample_interval=100e-6)  

pulse_seq = PulseReadout(awg1, steplist, timelist, 1, ampl,sample_rate,pulsefilename='TestPulse.arb')
sweep(pulse_seq.devtime,-.01,.01, 5, filename='test_%T.txt', out=dm.fetch_all , async=True, close_after=True)


###################################################
################Trace du graph ####################
####################################################  
gate=0 # Voltage de la grille pour centrage 

vd=readfile('test_*_dm_fetch_all_*.txt')
plot(vd.T, '-o')
fig = plt.figure(figsize=[8,8])
ax = fig.add_subplot(111)
ax.axes.tick_params(labelsize=20)
im = ax.imshow(vd,
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
 