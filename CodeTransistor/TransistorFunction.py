# Author - Claude Rohrbacher <claude.rohrb@gmail.com> 2019
# This code is to be used for processing transistor data, extract ioff, ion ,vth and ss data at different temperature.
# Be aware that this code was written at the begining of my PhD thesis with pure chaotic energy.
# The comments are rare and the variable not well named.
# You've been warned

import re
import glob
import sys
import os.path
import pylab
from operator import truediv
from pylab import*
from matplotlib.widgets import Slider, Button, RadioButtons
from pyHegel import*
from pyHegel.util import readfile
from pyHegel import fitting as fit
from pyHegel import fit_functions as fitFCT
from pyHegel import derivative as der
from matplotlib.widgets import Slider, Button, RadioButtons
from statistics import stdev 
import GraphStyle
from GraphStyle import*
import pickle

class Mydata:
	"""
		Classe de donnees pour mieux naviguer les donnees de transistor
		Chaque courbe a comme variable de classe les differentes analyses de transistor pour faciliter
		le traitement des donnees.
		Cette classe a pour vocation a etre exporte via le module pickle.
	"""
	def __init__(self):
		self.value={}
		self.comment=[]
		self.instr=[]
		self.Vds=0
		self.T=0
		self.Ioff=0
		self.Ion=0
		self.Vthlin=0;
		self.vth_err = 0
		self.ss=0
		self.ssi=0 #current at which the ss is extracted
		self.offset=0 #if offset is present, usually not use
		self.Iofferror=0
		self.Vg=np.array([])
		self.I=np.array([])

	def toprint(self):
		return self.Vds, self.T

def loadmapDC(lst, Temp_name, Vg_I_index, trans_type, inverse_DS):
	"""
		Load les mesures de courant.
		create the Mydata Class and put all of them in a list
		The function return the list of Mydata
		assign Vds and Temperature value. 

		lst: list with all file name.
		Temp_name : Nom dans les commentaires ou est indique la temperature
		Vg_I_index : indices of the array to retrieve VG and IDS value

	"""
	# Definitions
	data = []  # List in which to store data
	n = len(lst)  # Number of files

	for i in range(n):  # For each file
		y = lst[i]  # y loads the file

		# If you inverted Source & Drain in a measurement, declare the file number with inverse_DS
		if i in inverse_DS:
			sign_intensity = -1  # If Source & Drain are inverted, then intensity is negative
		else:
			sign_intensity = 1

		# Extract data as an array from file
		file = readfile(y, getheaders=True)

		# Create a Mydata instance to store the data
		datatemp = Mydata()
		datatemp.comment = file[2]  # Comments from the file
		datatemp.instr = file[1]  # Name of the columns of the file
		datatemp.value = file[0]  # Data of the file

		# Extract Vg, I from file, such that Vg is always going from min to max value
		if trans_type=="n":
			datatemp.Vg = datatemp.value[Vg_I_index[0]][:]  # Vg_I_index[0] index of Vg column
			datatemp.I = sign_intensity * datatemp.value[Vg_I_index[1]][:]  # Vg_I_index[1] index of i_DS column
		elif trans_type=="p":
			datatemp.Vg = datatemp.value[Vg_I_index[0]][:][::-1]  # pfet measurements are performed from max to min value
			datatemp.I = sign_intensity * datatemp.value[Vg_I_index[1]][:][::-1]

		# except:
		# 	if trans_type=="n":
		# 		datatemp.Vg = datatemp.value[Vg_I_index[0]]
		# 		datatemp.I = sign_intensity * datatemp.value[Vg_I_index[1]]
		# 	elif trans_type=="p":
		# 		datatemp.Vg = datatemp.value[Vg_I_index[0]][::-1]
		# 		datatemp.I = sign_intensity * datatemp.value[Vg_I_index[1]][::-1]

		# Extract Temperature and Vd from the comments of the file
		for line in datatemp.comment:
			match = re.search("T =([^;]\S+)", line)
			match2 = re.search("Vd =([^;]\S+)",line)
			if match:
				datatemp.T = float(match.group((1))[2:-1])
			if match2:
				datatemp.Vds = float(match2.group((1)))
		data.append(datatemp)
	# tri selon les temperatures pour que les courbes soient belles,
	# et selon Vds pour que Vth-lin soit deja calcule quand on calcule Vth-sat

	# data.sort(key = lambda x: (x.T, x.Vds))

	return data


def Ioff(data):
	""" Extraction Ioff et de Ion"""

	ioff900mV= np.empty((0,0), float)
	ioff50mV= np.empty((0,0), float)
	ion900mV= np.empty((0,0), float)
	ion50mV= np.empty((0,0), float)
	T1= np.empty((0,0), float)
	T2= np.empty((0,0), float)
	error50mV=np.empty((0,0), float)
	error900mV=np.empty((0,0), float)
	w=50
	for i in data:
		#calcul de ion

		index_of_maximum = np.argmax(data[0].Vg)
		i.Ion=average(i.I[index_of_maximum-2:index_of_maximum])
		#calcul de ioff
		if i.Vds==0.05:
			index_of_minimum = np.argmin(abs(i.Vg))
			try:
				i.Ioff=average(i.I[index_of_minimum-w:index_of_minimum+w])
				i.Iofferror=stdev(i.I[index_of_minimum-w:index_of_minimum+w])
			except:
				i.Ioff=average(i.I[index_of_minimum:index_of_minimum+w])
				i.Iofferror=stdev(i.I[index_of_minimum:index_of_minimum+w])
			ioff50mV=np.append(ioff50mV, i.Ioff)
			ion50mV=np.append(ion50mV,i.Ion)
			T1=np.append(T1,(i.T))
			error50mV=np.append(error50mV, i.Iofferror)

		if i.Vds==0.9:
			index_of_minimum = np.argmin(abs(i.Vg))
			try:
				i.Ioff=average(i.I[index_of_minimum-20:index_of_minimum+20])
				i.Iofferror=stdev(i.I[index_of_minimum-20:index_of_minimum+20])
			except:
				i.Ioff=average(i.I[index_of_minimum:index_of_minimum+20])
				i.Iofferror=stdev(i.I[index_of_minimum:index_of_minimum+20])

			error900mV=np.append(error900mV, i.Iofferror)
			ioff900mV=np.append(ioff900mV,i.Ioff)
			ion900mV=np.append(ion900mV,i.Ion)
			T2=np.append(T2,(i.T))

	res900mV = ion900mV/ioff900mV
	res50mV = ion50mV/ioff50mV
	errorRes50=error50mV*(res50mV/ioff50mV)
	errorRes900=error900mV*(res900mV/ioff900mV)
	plt.figure(4)
	plt.loglog(T1,ioff50mV,color='royalblue',marker='o',label= 'Vds=50mV')
	plt.errorbar(T1,ioff50mV,yerr=error50mV,capsize=4, elinewidth=1)
	plt.loglog(T2,ioff900mV,color='tab:orange',marker='o',label='Vds=900mV')
	plt.errorbar(T2,ioff900mV,yerr=error900mV, capsize=4, elinewidth=1)
	plt.legend()
	
	plt.figure(5)
	plt.loglog(T1,ion50mV,color='royalblue',marker='o',label= 'Vds=50mV')
	plt.loglog(T2,ion900mV,color='tab:orange',marker='o',label='Vds=900mV')
	plt.legend()

	
	plt.figure(6)
	plt.loglog(T1,res50mV,color='royalblue',marker='o',label= 'Vds=50mV')
	plt.errorbar(T1,res50mV, yerr=errorRes50, capsize=4, elinewidth=1)
	plt.loglog(T2,res900mV,color='tab:orange',marker='o',label='Vds=900mV')
	plt.errorbar(T2,res900mV,yerr=errorRes900,capsize=4, elinewidth=1)
	plt.legend()
	
	return data


def vth(data, w, c1, trans_type):
	
	"""
		Calcul le threshold  

	"""

	# Initialisations
	vth50 = np.empty((0,0), float)  # array([array([])])
	T1 = np.empty((0,0), float)
	vth900 = np.empty((0,0), float)
	T2 = np.empty((0,0), float)
	current_vthlin = None

	for index, i in enumerate(data):
		# Compute the derivative of the I(Vg) curve
		ioffset = i.I - i.offset
		derivative = der.Dfilter(i.Vg, ioffset, 10)

		if i.Vds == 0.05:
			# Figure 7:
			# Plot the derivative in -- line
			plt.figure(7)
			plot(derivative[0],derivative[1],'--',color=c1(int(index/2)))

			#TEST LINEAR FIT ON THE NORMAL CURVE
			# Find the maximum of the absolute of the slope
			if trans_type=="n":
				rep = np.argmax(derivative[1])  # If nfet, the slope is positive
			if trans_type=="p":
				rep = np.argmin(derivative[1])  # If pfet, the slope is negative

			# Fit I(Vg) with a linear curve over a sub-section of the Vg range
			x = i.Vg[rep-w:rep+w]  # Vg range over which to fit
			p0=[-0.00091647 , 0.00113323]  # fit parameter
			(b, a), _, (db, da), _ = fit.fitcurve(fitFCT.linear, x, ioffset[rep-w:rep+w], p0)  # linear fit
			y = a * x + b  # obtained linear fit over Vg range

			# calcul de l'erreur d_vth = 1/a * db + b/a^2 * da
			i.vth_err = 1/a * db + b / (a**2) * da

			# Figure 8:
			# Plot I(Vg) in -- and its linear fit y(x) in - on the same curve
			plt.figure(8)
			plot(i.Vg, ioffset,'--',color=c1(int(index/2)))
			plot(x,y,'-',color=c1(int(index/2)))
			if trans_type=="n":
				plot([min(x), max(x)], [min(y), max(y)], 'o', color=c1(int(index/2)))  # Put o markers for beginning and end of fit
			if trans_type=="p":
				plot([max(x), min(x)], [min(y), max(y)], 'o', color=c1(int(index/2)))  # Put o markers for beginning and end of fit

			plot(i.Vg[rep], ioffset[rep], 'o', color=c1(int(index/2)))  # Put o marker for maximum of the absolute slope

			# Figure 9:
			# Plot Vthreshold (vth) function of the temperature for Vds = 50mV
			plt.figure(9)
			T1 = np.append(T1, i.T)  # Temperature associated with the measurement
			i.Vthlin = (i.Ioff - b) / a  # Vg at which linear fit equals Ioff
			vth50 = np.append(vth50, i.Vthlin)
			plt.semilogx(T1, vth50, '-o', color="tab:blue")  # Plot Vth function of Temperature
			plt.errorbar(i.T, i.Vthlin, yerr=i.vth_err, capsize=4, elinewidth=1, color="tab:blue")  # With errorbars

			# extract index of the closest voltage to vth
			i_vthlin = np.argmin(np.abs(i.Vg - i.Vthlin))
			# current, current's derivative and fit error associated to this voltage
			current_vthlin = i.I[i_vthlin] # pour calculer Vth900
			dcurrent_vthlin = np.average(derivative[1][i_vthlin - 5 : i_vthlin + 5])
			linerr = i.vth_err

		if i.Vds == 0.9:

			"""
			Value of Vg for which Id is equal to the current at the threshold voltage extracted in linear regime 
			"""

			# Figure 9:
			# Plot vth function of the temperature for Vds = 900mV
			plt.figure(9)

			# extract index of the closest voltage to vth
			try:
				i_vthlin = np.argmin(abs(i.I-current_vthlin))
			except:
				raise ValueError("lst should be sorted by (Vds, T) growing")
			# current, voltage's derivative and fit error associated to this voltage
			i.Vthlin = i.Vg[i_vthlin]
			dv_vthlin = 1 / np.average(derivative[1][i_vthlin - 5 : i_vthlin + 5])
			i.vth_err = dv_vthlin * dcurrent_vthlin * linerr
			# add vth and temperature
			vth900 = np.append(vth900, i.Vthlin)
			T2 = np.append(T2, i.T)

			plt.semilogx(T2,vth900,'-o', color="tab:orange")
			plt.errorbar(i.T,i.Vthlin, yerr=i.vth_err, capsize=4, elinewidth=1, color="tab:orange")
	return data	


def ss(data,param, w, c1, trans_type):
	'param is an array parameter'
	# SS = dVg/dlogIds
	ss_sign = 1
	if trans_type == "p":
		ss_sign = -1
		(minVds50, maxVds50, minVds900, maxVds900) = (param[0], param[1], param[3], param[4])
		param = [maxVds50, minVds50, param[2], maxVds900, minVds900, param[5]]

	ss50 = np.empty((0,0), float)
	ss900 = np.empty((0,0), float)
	T = np.empty((0,0), float)

	for index, i in enumerate(data):

		ss50tem= np.empty((0,0), float)
		ssi50= np.empty((0,0), float)
		ss900tem= np.empty((0,0), float)
		ssi900= np.empty((0,0), float)

		p0=[-14.22168096,  12.76228698]
		x=i.Vg  # Vg
		y=(np.log10(abs(i.I-(i.offset))))  #log(Ids)

		if i.Vds==0.05:
			# Figure 12 : log(Ids) function of Vg
			plt.figure(12)
			plot(x, y, '--', color=c1(int(index/2)))

			max = argmin(abs(y + param[0]))  #Vgmax Subthreshold regime #param en echelle log
			min = argmin(abs(y + param[1]))  #Vgmin Subthreshold regime #param en echelle log

			# For each point between min and max
			for rep in range(min, max, 2):
				# Make a model around rep
				courbefit = fit.fitcurve(fitFCT.linear, x[rep-w:rep+w], y[rep-w:rep+w], p0)
				if courbefit[1] != nan:
					# Make a linear regression
					z = x[rep-2*w:rep+2*w] * courbefit[0][1] + courbefit[0][0]
					# Figure 12 : Add the linear regressions to the curve
					plot(x[rep-2*w:rep+2*w],z,'-')
					# Model: log(Ids) = a*Vg+b, SS = dVg/dlog(Ids) = 1/a mV/dec
					ss50tem = np.append(ss50tem, ss_sign*1/courbefit[0][1]*1e3)  # V/dec
					ssi50 = np.append(ssi50,i.I[rep])  #Store current

			# Figure 13 : Plot ss function of the current
			plt.figure(13)
			semilogx(ssi50, ss50tem, color=c1(int(index/2))) #ss function of current
			i.ssi = param[2]  #central value for current
			plt.axvline(x=i.ssi, ls='--')  #show as vertical line
			# 
			i.ss = ss50tem[argmin(abs(ssi50-i.ssi))]
			ss50 = np.append(ss50,i.ss)
			T = np.append(T, i.T)

		if i.Vds==0.9:
			plt.figure(14)
			plot(x,y,'--',color=c1(int(index/2)))
			max=argmin(abs(y+param[3]))
			min=argmin(abs(y+param[4]))
			for rep in range(min,max,2):
				courbefit=fit.fitcurve(fitFCT.linear,x[rep-w:rep+w],y[rep-w:rep+w],p0)
				if courbefit[1]!=nan:
					z=x[rep-2*w:rep+2*w]*courbefit[0][1]+courbefit[0][0]
					plot(x[rep-2*w:rep+2*w],z,'-')
					ss900tem=np.append(ss900tem, ss_sign*1/courbefit[0][1]*1e3)
					ssi900=np.append(ssi900, i.I[rep])
			plt.figure(15)
			semilogx(ssi900,ss900tem,color=c1(int(index/2)))
			i.ssi=param[5]
			
			plt.axvline(x=i.ssi, ls='--')
			i.ss=ss900tem[argmin(abs(ssi900-i.ssi))]
			ss900=np.append(ss900,i.ss)
	
	plt.figure(16)
	semilogx(T,ss50,'-o')
	semilogx(T,ss900,'-o')
	return data


def AnalyseComplet(lst,
				   path,
				   name,
				   param,
				   T=7,
				   Temp_name='Temperature:',
				   Vg_I=[2,4],
				   wss=40,
				   wvth=50,
				   savepickle=False,
				   savegraph=False,
				   trans_type="n",
				   inverse_DS=[]):
    """ Call all function to calculate SS, Vth, Ioff, Ion 
        lst: list of filename data
        path=path to save figures and pickle
        name=name of pickle file
        T= number of expected temperature
        wss = width of fit for ss
        wvth: width of fit for Vth
        param : parameter for SS calculation : [minVds50,MaxVds50,ValueVds50,minVds900,maxVds900,ValueVds900]"""

    # Load the data from files
    data = loadmapDC(lst, Temp_name, Vg_I, trans_type, inverse_DS)
    # Offset= loadmapDC(Offset)

    # Plot Graphs:
    # Generate colormap: one different color for each temperature
    c1 = cm.get_cmap('coolwarm', T)
    legend=[]

    for index, i in enumerate(data):
                    
        if i.Vds==0.05:
			# Figure 1 :
			# Plot I(Vg) for each temperature for Vds=50 mV
            legend = np.append(legend,[str(int(i.T))+'K'])
            plt.figure(1)
            plt.semilogy(i.Vg, i.I,color=c1(int(index/2)))  # ordinate in log scale
            
        if i.Vds==0.9:
			# Figure 2 :
			# Plot I(Vg) for each temperature for Vds=900 mV
            plt.figure(2)
            plt.legend(loc="best")
            plt.semilogy(i.Vg, i.I,color=c1(int(index/2))) # ordinate in log scale
    # Create figures 4, 5, 6
    data=Ioff(data)
	# Create figures 7, 8, 9
    data=vth(data, wvth, c1, trans_type)
    # Create figures 12, 14, 15, 16
    data=ss(data, param, wss, c1, trans_type)

    Tick=array([1,10,100,300])
    Tticklabel=['1', '10', '100','300']
    VgTick=array([-0.5,0,0.5,1,1.2])
    VgTickLabel=['-0.5','0','0.5','1','1.2']
    graph(figure(1),path,'I-V lin'+name, '$V_G$ (V)', '$I_{DS}$ (A)', '$V_{DS}$ = 0.05 V', legend,col=1,save=savegraph)
    graph(figure(2),path,'I-V sat'+name, '$V_G$ (V)', '$I_{DS}$ (A)', '$V_{DS}$ = 0.9 V', legend, col=1,save=savegraph)
    graph(figure(4),path,'IOFF'+name, 'Temperature (K)', '$I_{OFF}$ (A)', '', ['$V_{DS}$ = 50 mV','$V_{DS}$ = 900 mV'], xtick=Tick, xticklabel=Tticklabel,save=savegraph)
    graph(figure(5),path,'ION'+name, 'Temperature (K)', '$I_{ON}$ (A)', '', ['$V_{DS}$ = 50 mV','$V_{DS}$ = 900 mV'], xtick=Tick, xticklabel=Tticklabel,save=savegraph)
    graph(figure(6),path,'ION-IOFF'+name, 'Temperature (K)', '$ \\dfrac{I_{ON}}{I_{OFF}}$', '', ['$V_{DS}$ = 50 mV','$V_{DS}$ = 900 mV'], xtick=Tick, xticklabel=Tticklabel,save=savegraph)
    graph(figure(9),path,'NewVth'+name, 'Temperature (K)', '$V_{TH} (V)$', '', ['$V_{DS}$ = 50 mV','$V_{DS}$ = 900 mV'], xtick=Tick, xticklabel=Tticklabel,save=savegraph)
    # Plot figure 13
    graph(figure(13),path,'SSlin'+name, 'Current (A)', '$SS $(mV/decade)', 'Linear regime $V_{DS}$ = 50 mV ',save=savegraph)
    graph(figure(13),path,'SSlin'+name, 'Current (A)', '$SS $(mV/decade)', 'Linear regime $V_{DS}$ = 50 mV ',save=savegraph)
    graph(figure(15),path,'SSsat'+name, 'Current (A)', '$SS $(mV/decade)', 'Saturations regime $V_{DS}$ = 900 mV ',save=savegraph)
    graph(figure(16),path,'SS'+name, 'Temperature (K)', '$SS (mV/decade)$', '', ['$V_{DS}$ = 50 mV','$V_{DS}$ = 0.9 V'], xtick=Tick, xticklabel=Tticklabel,save=savegraph)

    plt.show()

	# Save Data if savepickle is True
    if savepickle:
        with open(path +'\\' + name + ".pickle", 'wb') as DataSave:
               pickle.dump(data, DataSave)

    return data