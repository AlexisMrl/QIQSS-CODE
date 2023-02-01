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

def gaussian_mixture(x,sigma,mu1,mu2,A1,A2):
	f= (A1/np.sqrt(2*np.pi*sigma**2))*np.exp(- (x-mu1)**2/(2*sigma**2)) +(A2/np.sqrt(2*np.pi*sigma**2))*np.exp(-(x-mu2)**2/(2*sigma**2))
	return f

def counter(data,load_time,read_time,binwidth=0.1e-9,filter_value=4):
	""" Compute and plot the histogram to choose threshold value """
	print('HEY')
	resolution = data[0][0][2]-data[0][0][1]
	t=data[0][0][int(load_time/resolution):len(data[0][0])-int(read_time/resolution)]-load_time
	newdata=[]
	for i in tqdm(data[1]):
		newdata=np.append(newdata,i[int(load_time/resolution):len(i)-int(read_time/resolution)])
	newdata = der.filters.gaussian_filter1d(newdata,filter_value)
	dist=pd.DataFrame(newdata)
	fig, ax = plt.subplots()
	dist.plot.hist(density=True,  bins=np.arange(min(newdata), max(newdata) + binwidth, binwidth),ax=ax)
	dist.plot.kde(ax=ax, legend=False)
	ax.set_ylabel('Probability')
	ax.grid(axis='y')
	ax.set_facecolor('#d8dcd6')
	

	x=np.arange(min(newdata), max(newdata), binwidth)
	n=plt.hist(newdata, density=True, color='black',bins=binwidth,stacked=True)[0]

	plt.figure()
	param=fit.fitplot(gaussian_mixture, x, n, p0=[0.2e-9,-2.6e-9,-1.7e-9,5000,40000])
	D=np.abs((param[0][1]-param[0][2])/np.sqrt(param[0][0]**2))
	print('D = {}'.format(D))


def tunnel_rate(data,load_time,read_time,threshold):
	""" Calculate the tunnel rate """
	#on reshape les donnes
	resolution = data[0][0][2]-data[0][0][1]
	cutinit=int(load_time/resolution)
	cutend = len(data[0][0])-int(read_time/resolution)
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


def spin_search(t,data):
	""" count the number of in and out event
	return the average number of event, average tunnel time
	and the std deviation """
	num_event_out=0.
	num_event_in=0.
	out_time=[]
	in_time=[]

	for i in range(data.shape[0]):
		out_Event=False
		in_Event=False
		for j in range(data.shape[1]-1):
			if  (data[i][j] - data[i][j+1]) == 1 and out_Event == False:
				num_event_out = num_event_out+1
				out_time = np.append(out_time,t[j])
				out_Event = True
			elif (data[i][j] - data[i][j+1]) == 1 : 
				num_event_out = num_event_out+1

			if (data[i][j] - data[i][j+1]) == -1 and in_Event==False:
				num_event_in = num_event_in+1
				in_time = np.append(in_time,t[j])
				in_Event = True
			elif (data[i][j] - data[i][j+1]) == -1:
				num_event_in = num_event_in+1
			
	num_event_out = num_event_out/int(data.shape[0])
	num_event_in = num_event_in/int(data.shape[0])
	try:
		out_time_std=stats.stdev(out_time)
	except:
		out_time_std=0
	try:
		in_time_std=stats.stdev(in_time)
	except:
		in_time_std=0


	param=[np.mean(out_time),out_time_std,np.mean(in_time),in_time_std,num_event_out,num_event_in]
	return param
	

def trace_graph(x,y,z,extent,length):

	fig = plt.figure(figsize=[20,4])
	ax = fig.add_subplot(141)
	ax.axes.tick_params(labelsize=14)

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
	plt.show()
	plt.tight_layout()


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
	plt.show()
	plt.tight_layout()

	ax3 = fig.add_subplot(143)
	readV=np.linspace(extent[2],extent[3],length)
	plt.plot(z[:,5],readV,'-o',label='num_event_in')
	plt.plot(z[:,4],readV,'-o',label='num_event_out')
	ax3.set_xlabel('Average number of event', fontsize=14)
	ax3.set_ylabel('Read level (mV)', fontsize=14)
	ax3.set_xlim([0,5])
	ax3.legend()

	ax4 = fig.add_subplot(144)
	ax4.errorbar(z[:,0],readV,xerr=z[:,1],label='moyenne temps out',fmt='o',ecolor='orange')
	ax4.set_xlabel('time', fontsize=14)
	ax4.set_ylabel('Read level (mV)', fontsize=14)
	ax4.set_xscale('log')
	ax4.set_xlim([1e-5,1e-2])
	ax4.legend()

	return fig

def average_data(filename,length,size,threshold,load_time,read_time,filter_value=5):
	x=np.empty([length,size])
	digit=np.empty([length,size])
	results=np.empty([length,6])
	SA=int(size/13e-3)

	for i in tqdm(range(length)):
		file_number='{}'.format(i)
		file= filename+'{}.npy'.format(file_number)
		data=readfile(file)
		data.shape=[2,-1,size]
		x[i]=np.mean(data[1],axis=0)

		data_filtered = der.filters.gaussian_filter1d(data[1],filter_value,axis=1)
		digit_array = np.digitize(data_filtered,[threshold])
		digit[i]=np.mean(digit_array,axis=0)

		sa=int(size/np.max(data[0][0]))
		results[i]=spin_search(data[0][0],digit_array[:,int(sa*load_time):len(data[0][0])-int(sa*read_time)])

	np.save(filename+'AVERAGED.npy',x)
	np.save(filename+'DIGITIZE.npy',digit)
	np.save(filename+'tunnel.npy',results)