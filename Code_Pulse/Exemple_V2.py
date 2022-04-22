# import sys

# from matplotlib.pyplot import step
# import Pulse_V2
# reload(Pulse)
# from Pulse import *

########################
######load instrument###
########################

awg = instruments.tektronix_AWG('TCPIP0::AWG5200-9841.mshome.net::inst0::INSTR')
rto = instruments.rs_rto_scope('USB0::0x0AAD::0x0197::1329.7002k14-300206::INSTR')
# Be Careful that impedance is on High Z on the AWG


timelist=array([100e-6,100e-6,100e-6]) #time duration of each step
steplist=array([-0.5,0,0.5]) #voltage value of each step
sample_rate=10e6
awg.waveform_delete('Test')
pulse_seq = PulseReadout(awg, steplist, timelist, 1,sample_rate,pulsefilename='Test',ch=1,reshape=False)




# %time sweep(pulse_seq.devAmp,-0.50,.5, 5, filename='test_basic_%T.txt', out=rto.fetch, async=True, close_after=True,beforewait=0.1)
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
plt.tight_layout()
 
"""