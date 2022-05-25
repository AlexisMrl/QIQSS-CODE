# CodePulse
CodePulse pour qubit de spin
le fichier Pulse_V2.Py regroupe un ensemble de fonction pour appliquer des pulses.
Le type de Pulse dépend de la classe donné.
Pulse readout : Fixe des pulse carré de temps et d'amplitude donné
Pulse Rabi : Pulse a utilisé avec une source micro-onde : Génère des fonction porte avec modulation sinusoidale (possibilité de prendre en compte un IQ filter)


Exemple.py regroup diffferent usage example.
Le fichier codeLabber est un copy paste du code utiliser par Labber pour la même utilisation

> For now this code is design to operate with Tektronix awg 5008


## How to Use

### Load Device
```
awg = instruments.tektronix_AWG('TCPIP0::AWG5200-9841.mshome.net::inst0::INSTR')
rto = instruments.rs_rto_scope('USB0::0x0AAD::0x0197::1329.7002k14-300206::INSTR')
```

### Define a readout pulse
```
timelist=array([100e-6,100e-6,100e-6]) #time duration of each step
steplist=array([-0.05,0,0.05]) #voltage value of each step
sample_rate=320e6
pulse_seq = PulseReadout(awg, steplist, timelist, change_index=1, sample_rate=2.5e9,pulsefilename='test',ch=1,reshape=False,trig=True):
```
> All the variable entered here are the default of the PulseReadout class.
> An important parameter is change_index, it is the index of the steplist that will be affected by the sweep function.
> By default the second step value (read level) is selected

> A new timelist is generated modifying the last step to have a x64 number of sample on the awg (weird bug)

### previz your pulses
Send all pulses as a list, will plot them on a graph for vizualisation.
```
futil.plot_pulse_seq([pulse_seq])
```

### lauching a readout sequence
will sweep the read level.
If you want statistical data at 1 read level, just enter equal start and stop value
```
sweep(pulse_seq.devAmp,-0.050,.05, 5, filename='test_basic_%T.txt', out=rto.fetch, async=True, close_after=True,beforewait=0.1)
```

### single segmented pulse

This command is used to gain time, it send one big waveform containing all the different pulse (or iterations of the same pulse).
To acquire data, use oscilloscope (or later Alazartech) in segmented mode. On rs_rto scope be carefull to add 10us of extra time at the last steplist corresponding to the acquisition delay.
This command generate the new steplist, timelist, and marker to create the pulse sequence. take as parameter the timelist, the steplist, the start,stop and number of point to iterate.
```
s,t,m=Single_Pulse_frag(timelist,steplist,-0.05,0.05,100)
```

