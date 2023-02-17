import numpy as np 
import pyHegel
from pyHegel.util import readfile as readfile
import matplotlib
from matplotlib import*
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
import statistics as stats
from pyHegel import fitting as fit
from pyHegel import fit_functions as fitFCT
from pyHegel import derivative as der
import random
import scipy.signal as sig

def single_graph(data,amplitude):
	""""
	PLOT A SINGLE GRAPH WITHOUT TREATMENT
	"""
	fig = plt.figure(figsize=[8,8])
	ax = fig.add_subplot(111)
	ax.axes.tick_params(labelsize=20)
	im = ax.imshow(data[1],
	    extent=(0,max(data[0,0])*1e3,amplitude[0],amplitude[1]),
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
	return fig


def notch_filter(f0,signal, Q):
	"""
	IMPLEMENT A NOTCH FILTER
	"""

	time = signal[0]
	fs = 1/(time[1]-time[0])
	w0=(f0/(fs/2))
	b,a=sig.iirnotch(w0, Q)
	filtered_signal=sig.filtfilt(b,a,signal[1])
	return filtered_signal


def gaussian_mixture(x,sigma,mu1,mu2,A1,A2):
	f= (A1/np.sqrt(2*np.pi*sigma**2))*np.exp(- (x-mu1)**2/(2*sigma**2)) +(A2/np.sqrt(2*np.pi*sigma**2))*np.exp(-(x-mu2)**2/(2*sigma**2))
	return f

def counter(data,size,load_time,empty_time,binwidth=0.1e-9,filter_value=4):
	""" Compute and plot the histogram to choose threshold value 
	load_time et empty time enregistre
	binwidth : largeur de chaque bin de l'histomgramme
	filter_value : Valeur du filtre pour mooth les data, si none pas de filtrage
	
	"""
	data_copy=data.copy()
	data_notched=notch_filter(16e3,[data[0],data[1]],30)
	data_notched=notch_filter(8e3,[data[0],data_notched],10)
	data_notched=notch_filter(580,[data[0],data_notched],5)
	data_copy[1]=data_notched
	data_copy.shape=[2,-1,size]
	data.shape=[2,-1,size]

	resolution = data[0][0][2]-data[0][0][1]
	t=data[0][0][int(load_time/resolution):len(data[0][0])-int(empty_time/resolution)]-load_time

	#filtrage et on plot la difference des deux 
	plt.figure()
	rand=random.randrange(len(data[1]))
	plt.plot(t,data[1][rand][int(load_time/resolution):len(data[1][rand])-int(empty_time/resolution)])
	if filter_value is not None:
		data_copy[1] = der.filters.gaussian_filter1d(data_copy[1],filter_value)
		plt.plot(t,data_copy[1][rand][int(load_time/resolution):len(data_copy[1][rand])-int(empty_time/resolution)])

		
	# reshape les data en enleveant le empty et load time envoye
	# Et on concatene tout en un seul gros array pour traitement statistique

	newdata=[]
	for i in tqdm(data_copy[1]):
		newdata=np.append(newdata,i[int(load_time/resolution):len(i)-int(empty_time/resolution)])

	#trace l'histogramme
	dist=pd.DataFrame(newdata)
	fig, ax = plt.subplots()
	dist.plot.density(ax=ax)
	dist.plot.kde(ax=ax, legend=False)
	ax.set_ylabel('Probability')
	ax.grid(axis='y')
	ax.set_facecolor('#d8dcd6')
	plt.show()


	return newdata,data_copy

def tunnel_rate(data,load_time,empty_time,threshold):
	""" Calculate the tunnel rate """
	#on reshape les donnes
	resolution = data[0][0][2]-data[0][0][1]
	cutinit=int(load_time/resolution)
	cutend = len(data[0][0])-int(empty_time/resolution)
	t=data[0][0][cutinit:cutend]-load_time
	shape = [int(v) for v in data.shape]
	shapecut=[shape[1],cutend-cutinit]
	print shapecut
	print shape
	data_cut = np.zeros(shapecut)
	for i in range(shape[1]):
		data_cut[i]=data[1][i][cutinit:cutend]

	data_cut = der.filters.gaussian_filter1d(data_cut,4)

	#je digitalise les donn3es suivant un threshold
	data_filtered = np.digitize(data_cut,[threshold])
	fig = plt.figure(figsize=[10,4])
	ax= fig.add_subplot(111)
	ax2=ax.twinx()

	#display pour la forme
	ax.plot(t,data_cut[6],'o')
	ax2.plot(t,data_filtered[6],'r')
	# ax2.plot(t,data_filtered[56],'r')
	
	fig = plt.figure(figsize=[4,4])
	#on compte les evenements
	num_event_out=0  #e out of the dot
	in_time=np.array([]) #time spend in the dot

	for i in range(shapecut[0]):

		Event=False
		for j in range(shapecut[1]-1):
			if  (np.abs(data_filtered[i][j] - data_filtered[i][j+1])) == 1 and Event==False:
				num_event_out = num_event_out+1
				in_time = np.append(in_time,t[j])
				Event = True
	
	print('num_event_out', num_event_out)


	proba_in=np.ones(shapecut[1])

	for i in range(shapecut[1]):
		proba_in[i] = proba_in[i] - len(in_time[in_time <= t[i]])/float(num_event_out)
	 #on exclue volontairement les plateaux (on commence a fiter quand la probabilite descend)	
	
	
	lfit=len(proba_in[proba_in < 1.0])
	start_fit= len(proba_in) - lfit
	print ('start fit', start_fit)
	print ('proba in', len(proba_in))
	print ('lenght fit',(len(t[start_fit::])))
	params_in= fit.fitcurve(exp_decay, t[0:lfit], proba_in[start_fit::], p0=[10e-3]) 

	fig = plt.figure(figsize=[4,4])
	fit.fitplot(exp_decay, t[0:lfit], proba_in[start_fit::], p0=[10e-3])	
	#trace probabilite d'etre dans la boite 
	fig = plt.figure(figsize=[4,4])
	ax = fig.add_subplot(111)
	ax.set_title('Unloading event', fontsize=12)
	ax.plot(t[0:lfit],proba_in[start_fit::],'o',markersize=6)
	ax.plot(t[0:lfit], exp_decay(t[0:lfit], params_in[0]), label='Fitted function', lw=3)
	ax.tick_params(labelsize=12) 
	Tau_unload= (r'$\tau _{tun}$ = %.2f '%(1/params_in[0]) + u"\u00B1" + ' %.2f Hz' % (params_in[2]/(params_in[0]**2)))
	ax.text(0, 0, Tau_unload, fontsize=16)	
	ax.set_xlabel('Time(s)', fontsize=16)
	ax.set_ylabel(r'$P_{IN}$', fontsize=16)
	plt.tight_layout()
	# plt.show()

def exp_decay(x, a):
	return np.exp(-x/a)


def event_search(t,data):
	""" count the number of in and out event
	return the average number of event, average tunnel time
	and the std deviation """
	num_event_out=0.
	num_event_in=0.
	out_time=[]
	
	for i in range(data.shape[0]):

		first_in = False
		first_out = False

		in_Event = True
		event=np.diff(data[i], axis=-1)
		w1= np.where(event  == -1)
		w2= np.where(event  == 1)

		if data[i][0] == 0:
			num_event_out = num_event_out + len(w1[0])
			num_event_in = num_event_in + len(w2[0])
			if len(w1[0]) != 0: 
				out_time = out_time+ [t[w1[0][0]]]
		else:
			num_event_out = num_event_out + len(w2[0])
			num_event_in = num_event_in + len(w1[0])
			if len(w2[0]) != 0: out_time = out_time+[t[w2[0][0]]]

	num_event_out = num_event_out/int(data.shape[0])
	num_event_in = num_event_in/int(data.shape[0])
	out_time = np.array(out_time)
	try:
		out_time_std = stats.stdev(out_time)
	except:
		out_time_std=0

	param=[np.mean(out_time),out_time_std,num_event_out,num_event_in]
	return param

def spin_search(t,data):
	""" 
	Same as event_search but remove case where we have two event 
	"""

	total_event_out=0.
	total_event_in=0.
	count_exclusion = 0. 
	for i in range(data.shape[0]):

		trace_event_out = 0.
		trace_event_in = 0.

		event=np.diff(data[i], axis=-1)
		w1= np.where(event  == -1)
		w2= np.where(event  == 1)

		if data[i][0] == 0:
			trace_event_out = trace_event_out + len(w1[0])
			trace_event_in = trace_event_in + len(w2[0])
			
		else:
			trace_event_out = trace_event_out + len(w2[0])
			trace_event_in = trace_event_in + len(w1[0])
			
		if 	trace_event_out > 1: 
			count_exclusion +=1
		else : 
			total_event_out += trace_event_out
			total_event_in += trace_event_in

	total_event_out = total_event_out/(int(data.shape[0])-count_exclusion)
	total_event_in = total_event_in/(int(data.shape[0])-count_exclusion)
	
	return [total_event_out,count_exclusion,total_event_in]

def trace_graph(x,y,z,extent,length):
	""" 
	Function to plot the processed data from the average function, 
	x = Averaged.py file
	y = Digitize.py file
	z = tunnel.py file
	extent : the limit for the imshow plot first time and the voltage
	length : size of the given files (number of sweep)
	"""


	fig = plt.figure(figsize=[20,4])
	ax = fig.add_subplot(141)
	ax.axes.tick_params(labelsize=14)

	# trace averaged 
	im = ax.imshow(x,
		extent=extent,
		aspect="auto",
		origin="lower",
		cmap="jet")
	cbar = fig.colorbar(im)
	cbar.set_label(r"I nA)",fontsize=14)
	cbar.ax.tick_params(labelsize=14) 
	ax.set_xlabel('Time (ms)', fontsize=14)
	ax.set_ylabel('(mV)', fontsize=14)

	# trace digitize
	ax2 = fig.add_subplot(142)
	ax2.axes.tick_params(labelsize=14)
	im = ax2.imshow(y,
		extent=extent,
		aspect="auto",
		origin="lower",
		cmap="jet")
	cbar = fig.colorbar(im)
	cbar.set_label(r"I nA)",fontsize=14)
	cbar.ax.tick_params(labelsize=14) 
	ax2.set_xlabel('Time (ms)', fontsize=14)
	ax2.set_ylabel('(mV)', fontsize=14)

	#trace averaged event
	ax3 = fig.add_subplot(143)
	readV = np.linspace(extent[2],extent[3],length)
	line = [0.5]*length
	plt.plot(z[:,3],readV,'-o',label='num_event_in')
	plt.plot(z[:,2],readV,'-o',label='num_event_out')
	plt.plot(line,readV,'--')
	ax3.set_xlabel('Average number of event', fontsize=14)
	ax3.set_ylabel('Read level (mV)', fontsize=14)
	ax3.set_xlim([0,10])

	ax3.legend()

	ax4 = fig.add_subplot(144)
	ax4.errorbar(z[:,0],readV,xerr=z[:,1],label='moyenne temps out',fmt='o',ecolor='orange')
	ax4.set_xlabel('time', fontsize=14)
	ax4.set_ylabel('Read level (mV)', fontsize=14)
	ax4.set_xscale('log')
	ax4.set_xlim([1e-5,1e-2])
	ax4.legend()
	plt.tight_layout()
	return fig

def average_data(filename,length,size,threshold,load_time,empty_time,filter_value=5):
	""" 
	Does necessary data processing to analyse average single shot readout data 
	Specially crucial for detecting spin
	Take all the files 
	filename : name of one file (without npy extension, will take all the files if they are in the same folder)
	length : sweep size
	size : number of point of sample per shot
	threshold : Curren threshold to discriminate 0/1 state ()
	load_time,empty_time : takes into account both time to remove them from analysis
	filter_value : paramter faur gaussian filter
	"""

	x=np.empty([length,size])
	digit=np.empty([length,size])
	results=np.empty([length,4])

	for i in tqdm(range(length)):
		file_number='{}'.format(i)
		file= filename+'{}.npy'.format(file_number)
		data=readfile(file)
		data_copy=data.copy()
		data_notched=notch_filter(16e3,[data[0],data[1]],30)
		data_notched=notch_filter(8e3,[data[0],data_notched],10)
		data_notched=notch_filter(580,[data[0],data_notched],10)
		data_copy[1]=data_notched
		data_copy.shape=[2,-1,size]
		data.shape=[2,-1,size]
		# x[i]=np.mean(data[1],axis=0)

	
		if filter_value is not None:
			# FILTERING
			data_filtered = der.filters.gaussian_filter1d(data_copy[1],filter_value,axis=1)
		else : 
			data_filtered = data[1].copy()
		x[i]=np.mean(data_filtered,axis=0)

		# digitize
		digit_array = np.digitize(data_filtered,[threshold])
		digit[i]=np.mean(digit_array,axis=0)

		sa=int(size/np.max(data[0][0]))
		results[i]=event_search(data[0][0],digit_array[:,int(sa*load_time):len(data[0][0])-int(sa*empty_time)])

	

	np.save(filename+'AVERAGED.npy',x)
	np.save(filename+'DIGITIZE.npy',digit)
	np.save(filename+'tunnel.npy',results)
	# np.save(filename+'extent.npy',extent)

def spin_up_prob(filename, time_sweep,size,threshold,filter_value=4,cut=None):


	length = len(time_sweep)
	p_spin_up = np.empty([length])
	delta = np.empty([length])
	n_exclusion = np.empty([length])
	for i in tqdm(range(length)):
		file_number='{}'.format(i)
		file= filename+'{}.npy'.format(file_number)
		data=readfile(file)
		data.shape=[2,-1,size]
		if cut is not None:
			data=data[:,:,0:800]
		data_filtered = der.filters.gaussian_filter1d(data[1],filter_value,axis=1)
		digit_array = np.digitize(data_filtered,[threshold])
		spin_up, exclusion, in_event= spin_search(data[0][0],digit_array)
		n_exclusion[i] = exclusion
		p_spin_up[i] = spin_up
		

	plt.plot(time_sweep,p_spin_up,'o')
	return p_spin_up,n_exclusion