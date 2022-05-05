# import sys

# from matplotlib.pyplot import step
# import Pulse_V2
# reload(Pulse)
# from Pulse import *

########################
######load instrument###
########################

# awg = instruments.tektronix_AWG('TCPIP0::AWG5200-9841.mshome.net::inst0::INSTR')
# rto = instruments.rs_rto_scope('USB0::0x0AAD::0x0197::1329.7002k14-300206::INSTR')
# Be Careful that impedance is on High Z on the AWG


timelist=array([100e-6,100e-6,100e-6]) #time duration of each step
steplist=array([-0.05,0,0.05]) #voltage value of each step
sample_rate=320e6
awg.waveform_delete('Test')
pulse_seq = PulseReadout(awg, steplist, timelist,sample_rate=sample_rate,pulsefilename='Test',ch=1,reshape=False)




def Single_Pulse_frag(timelist,steplist,start,stop,npts,sample_rate=320e6):
    """ This function generate an array of readout pulse with different read level for segmentation
    measurement on the oscilloscope
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

def test_run(awg,rto):
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
plt.tight_layout()
 
"""