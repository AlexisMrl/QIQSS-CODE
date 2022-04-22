reset_pyHegel()
from Pulse_V2 import *

awg = instruments.tektronix_AWG('TCPIP0::AWG5200-9841.mshome.net::inst0::INSTR')
rto = instruments.rs_rto_scope('USB0::0x0AAD::0x0197::1329.7002k14-300206::INSTR')


steplist = array([0, 0.03, 0.1])
timelist = array([100e-6, 100e-6, 100e-6])
sample_rate = 1e7
wfname = "temp"

pulse_seq = PulseReadout(awg, steplist, timelist, 1,sample_rate,pulsefilename='TestPulsech2.arb',ch=1,reshape=False)
sweep(pulse_seq.devAmp,0,.1, 5, filename='test_%T.txt', out=rto.fetch, async=True, close_after=True,beforewait=0.1)

# pulse_readout(awg, steplist, timelist, sample_rate, wfname, 1)
# print awg.ask("*OPC?")
# awg.run()
# set awg.output_en, 1