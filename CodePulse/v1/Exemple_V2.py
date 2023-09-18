# import sys
# import pyHegel.instruments
# import Pulse_V2
# from Pulse_V2 import *
# import function_util as util_f

########################
######load instrument and start console ###
########################
%cd D:\QIQSS-CODE\Code_Pulse
%run -i function_util.py
%run -i Pulse_V2.py
awg = instruments.tektronix_AWG('TCPIP0::AWG5200-XXXX.mshome.net::inst0::INSTR')
rto = instruments.rs_rto_scope('USB0::0x0AAD::0x0197::1329.7002k14-300206::INSTR')
gain = 1/0.028184 # prise en compte des atténuators
# Be Careful that impedance is on High Z on the AWG

# code line to delete and create a waveform in the awg
sample_rate=320e3
timelist=array([5e-3,5e-3]) #time duration of each step
steplist=array([0.005,-0.005])
awg.waveform_delete('Test') 
pulse_seq = PulseReadout(awg, steplist, timelist,sample_rate=sample_rate,pulsefilename='Test',ch=1,gain=gain)
comment= comment_generator([pulse_seq],'Filter : 30 kHz \n Amp : 1e8 \n VB2 = 3 V \n VD1 = 0.732 V \n B = 0T')

#############################
###Create readout Pulse   ###
#############################
timelist=array([2.5e-3, 5e-3, 2.5e-3, 1e-3]) #time duration of each step
steplist=array([0.004,0.002,0,-0.02]) #voltage value of each step
sample_rate=320e3
awg.waveform_delete('Test') 
pulse_seq = PulseReadout(awg, steplist, timelist,sample_rate=sample_rate,pulsefilename='Test',ch=1,gain=gain)
comment= comment_generator([pulse_seq],'Filter : 10 kHz \n Amp : 1e8 \n VB2 = 0.5 mV \n VD1 = 0.8225 V \n B = 0T')

#############################
###    Plotting Pulses  ###
#############################
util_f.plot_pulse_seq([pulse_seq])


#############################
###    running measurement ###
#############################

run_test(awg,rto,fn=filename+'_{}.npy'.format(index))


# %time sweep(pulse_seq.devAmp,-0.050,.05, 5, filename='test_basic_%T.txt', out=rto.fetch, async=True, close_after=True,beforewait=0.1)
###################################################
################Trace du graph ####################
####################################################  
"""
vd=None
gate=0 # Voltage de la grille pour centrage 
vd=readfile(r'C:\Projets\IMEC TD\QBB24_3_4\2022-07-11\readout\QBB24_34_single_shot_read_B_0T_10kHz_20220711-162301\QBB24_34_single_shot_read_B_0T_10kHz_compare_20220711-162401_rto_fetch_*.txt')
fig = plt.figure(figsize=[8,8])
# for i in vd[1]:
#     plot(vd[0,0],i, '-o')
fig = plt.figure(figsize=[8,8])
ax = fig.add_subplot(111)
ax.axes.tick_params(labelsize=20)
im = ax.imshow(x[1],
    extent=(0,13.5,-8,8),
    aspect="auto",
    origin="lower",
    cmap="RdBu_r")
cbar = fig.colorbar(im)
cbar.set_label(r"I A",fontsize=20)
cbar.ax.tick_params(labelsize=20) 
ax.set_xlabel('Time (ms)', fontsize=20)
ax.set_ylabel('read voltage (mV)', fontsize=20)
plt.tight_layout()
plt.show()
"""

########
#Different code a copy paste pour lancer des sequence
######


#####################################################  
# For pulse to sweep read voltage, single shot no averaging
####################################################  
timelist=array([2e-3, 10e-3, 2e-3, 1e-3]) #time duration of each step
steplist=array([0.008,0.004,0,-0.05]) #voltage value of each step
sample_rate=32e3
timestr = time.strftime("%Y%m%d-%H%M%S")
awg.waveform_delete('Test')
filename='{}_QBB06_24_3_3_single_shot_long'.format(timestr)
comment="""Filter : 10 kHz \n Amp : 1e8 \n VB2 = 2.4V \n VD1= 776mV \n B = 0T \n
total time : {} \n steplist : {}\n  sample= {} """.format(timelist,steplist,get(rto.acquire_npoints))
text_file = open(r"C:\Projets\{}_comment_{}.txt".format(filename,timestr), "w")
# n = text_file.write(comment)
text_file.close()
s,t,m=run_frag(awg,rto,timelist,steplist,[0.0,0.008,100],sample_rate=sample_rate,index=1,wait_time=0.0025,rshape=True)
run_test(awg,rto,filename+'.npy')





#####################################################  
# LINE CODE TO TAKE SERIES OF SINGLE SHOT READOUT WITH VARIOUS 
# READ VOLTAGE FOR AVERAGING PURPOSE
#####################################################  
timelist=array([2e-3, 10e-3, 2e-3, 1e-3]) #time duration of each step
steplist=array([0.008,0.004,0,-0.05]) 
timestr = time.strftime("%Y%m%d-%H%M%S")
sweep_value= np.linspace(0.000,0.008,101)
sample_rate=32e3
average=100
filename='{}_QBB06_24_3_3_long_no_slope'.format(timestr)
for index,i in enumerate(sweep_value):
    s,t,m=run_frag(awg,rto,timelist,steplist,[i,i,average],sample_rate=sample_rate,index=1,wait_time=0.002,rshape=True)
    run_test(filename+'_{}.npy'.format(index))
    

comment="""Filter : 10 kHz \n Amp : 1e8 \n VB2 = 2.4V \n VD1= 770.5mV \n B = 0T  \n sweep = {} {} {} \n
total time : {} \n steplist : {}\n  sample= {} """.format(np.min(sweep_value),np.max(sweep_value),len(sweep_value),timelist,steplist,get(rto.acquire_npoints))
text_file = open(r"C:\Projets\IMEC TD\Die_8_QBB06_24_3_3\2022-10-27\average_0T_2\{}_comment_{}.txt".format(timestr,filename), "w")
n = text_file.write(comment)
text_file.close()


#####################################################  
# Use to generate slope at the read level for bias tee compensation
# ####################################################



timelist=array([2.5e-3, 5e-3,2.5e-3]) #time duration of each step
steplist=array([0.00,-0.0025,-0.005])
slope = 0.01 #in V/s
index = 1

def ramp(steplist,timelist,slope,index):
    timestep = int(timelist[index]*sample_rate)
    insert_step = np.linspace(steplist[index],slope*timelist[index]+steplist[index],timestep)
    insert_time = [1/sample_rate for i in range(timestep)] 
    new_steplist = steplist.copy()
    new_timelist = steplist.copy()
    new_steplist = np.delete(new_steplist, index)
    new_timelist = np.delete(new_timelist, index)
    new_steplist= np.insert(new_steplist,index,insert_step)
    new_timelist= np.insert(new_steplist,index,insert_time)
    return new_steplist,new_timelist
#####################################################  

# x= run_test('QBB24_34_single_shot_read_B_0T_VD3_693_5mV_10kHz_%T.npy')

# sweep(loop, 0,100,100, out=(rto.fetch, dict(history='all', bin='.npy')), exec_before=bf,filename='QBB24_34_single_shot_read_B_0T_10kHz_%T.npy',extra_conf=comment)