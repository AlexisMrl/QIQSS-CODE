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
		self.Vthlin=0
		self.vth_err = 0
		self.ss=0
		self.ssi=0
		self.offset=0
		self.Iofferror=0
		self.Vg=np.array([])
		self.I=np.array([])

def loadmapDC(lst,Temp_name):
	"""
		Load les mesures de courant.
		create the Mydata Class and put all of them in a list
		The function return the list of Mydata
		assign Vds and Temperature value. 

		lst: list with all file name.
		Temp_name : Nom dans les commentaires ou est indique la temperature
		Vg_I_index : indices of the array to retrieve VG and IDS value

	"""
	data=[]
	for y in lst:
		file=readfile(y, getheaders=True)
		datatemp=Mydata()
		datatemp.comment=file[2]
		datatemp.instr=file[1]
		datatemp.value=np.delete(file[0], 0, 1)
		datatemp.Vg=datatemp.value[0]
		datatemp.I=datatemp.value[1]
		datatemp.Vds= .05 if "50mV" in y else .9
		datatemp.T=int(re.search(r'mV.*K', y).group(0)[3:-1])
		data.append(datatemp)
	# tri selon les temperatures pour que les courbes soient belles,
	# et selon Vds pour que Vth-lin soit deja calcule qund on calcule Vth-sat
	data.sort(key = lambda x: (x.T, x.Vds))
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


def vth(data, w,T):
	
	"""
		Calcul le threshold  

	"""

	plt.figure(7)	
	plt.figure(8)
	c1 = cm.get_cmap('coolwarm', T)
	vth50= np.empty((0,0), float)
	T1= np.empty((0,0), float)
	vth900= np.empty((0,0), float)
	T2= np.empty((0,0), float)
	current_vthlin=None;
	for index, i in enumerate(data):

		if i.Vds==0.05:

			plt.figure(7)
			derivative=der.Dfilter(i.Vg,i.I-(i.offset),10)
			plot(derivative[0],derivative[1],'--',color=c1(int(index/2)))
			#TEST LINEAR FIT ON THE NORMAL CURVE
			plt.figure(7)
			rep=np.argmax(derivative[1])
			p0=[-0.00091647 , 0.00113323]
			ioffset=i.I-(i.offset)
			(b, a), _, (db, da), _ = fit.fitcurve(fitFCT.linear,i.Vg[rep-w:rep+w],ioffset[rep-w:rep+w],p0)

			x=i.Vg[rep-w:rep+w]
			y = a * x + b
			# calcul de l'erreur d_vth = 1/a * db + b/a^2 * da
			i.vth_err = 1/a * db + b / (a**2) * da
			
			plt.figure(8)
			plot(i.Vg, ioffset,'--',color=c1(int(index/2)))
	
			plot(x,y,'-',color=c1(int(index/2)))
			plot([min(x), max(x)],[min(y), max(y)],'o',color=c1(int(index/2)))
			plot(i.Vg[rep],ioffset[rep], 'o',color=c1(int(index/2)))
			T1=np.append(T1,i.T)
			i.Vthlin=(i.Ioff-b)/a
			vth50=np.append(vth50,i.Vthlin)
			plt.figure(9)
			plt.semilogx(T1,vth50,'-o', color="tab:blue")
			plt.errorbar(i.T,i.Vthlin, yerr=i.vth_err, capsize=4, elinewidth=1, color="tab:blue")
			
			i_vthlin = np.argmin(np.abs(i.Vg - i.Vthlin)) # indice
			current_vthlin = i.I[i_vthlin] # pour calculer Vth900
			dcurrent_vthlin = np.average(derivative[1][i_vthlin - 5 : i_vthlin + 5])
			linerr = i.vth_err

		if i.Vds==0.9:

			"""
			Value of Vg for which Id is equal to the current at the threshold voltage extracted in linear regime 
			"""
			i_vthlin = np.argmin(abs(i.I-current_vthlin))
			i.Vthlin=i.Vg[i_vthlin]
			derivative=der.Dfilter(i.Vg,i.I-(i.offset),10)
			dv_vthlin = 1 / np.average(derivative[1][i_vthlin - 5 : i_vthlin + 5])
			i.vth_err = dv_vthlin * dcurrent_vthlin * linerr
			
			vth900=np.append(vth900,i.Vthlin)
			T2=np.append(T2,i.T)
			plt.figure(9)
			plt.semilogx(T2,vth900,'-o', color="tab:orange")
			plt.errorbar(i.T,i.Vthlin, yerr=i.vth_err, capsize=4, elinewidth=1, color="tab:orange")

	return data	


def ss(data,param,w=40):
	'param is an array parameter'


	c1 = cm.get_cmap('coolwarm', 11)
	ss50= np.empty((0,0), float)
	ss900= np.empty((0,0), float)
	T= np.empty((0,0), float)

	for index, i in enumerate(data):

		ss50tem= np.empty((0,0), float)
		ssi50= np.empty((0,0), float)
		ss900tem= np.empty((0,0), float)
		ssi900= np.empty((0,0), float)	
		p0=[-14.22168096,  12.76228698]
		x=i.Vg
		y=(np.log10(abs(i.I-(i.offset))))
		

		if i.Vds==0.05:
			plt.figure(12)
			plot(x,y,'--',color=c1(int(index/2)))
			max=argmin(abs(y+param[0]))
			min=argmin(abs(y+param[1]))
			for rep in range(min,max,2):
				courbefit=fit.fitcurve(fitFCT.linear,x[rep-w:rep+w],y[rep-w:rep+w],p0)
				if courbefit[1]!=nan:
					z=x[rep-2*w:rep+2*w]*courbefit[0][1]+courbefit[0][0]
					plot(x[rep-2*w:rep+2*w],z,'-')
					ss50tem=np.append(ss50tem,1/courbefit[0][1]*1e3)
					ssi50=np.append(ssi50,i.I[rep])
			plt.figure(13)
			semilogx(ssi50,ss50tem,color=c1(int(index/2)))
			i.ssi=param[2]
			plt.axvline(x=i.ssi, ls='--')
			i.ss=ss50tem[argmin(abs(ssi50-i.ssi))]
			ss50=np.append(ss50,i.ss)
			T=np.append(T,i.T)

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
					ss900tem=np.append(ss900tem,1/courbefit[0][1]*1e3)
					ssi900=np.append(ssi900,i.I[rep])
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


def AnalyseComplet(lst,path,name,param,T=7,Temp_name='Temperature:',index=[2,4],wss=40,wvth=50,savepickle=False,savegraph=False):
    """ Call all function to calculate SS, Vth, Ioff, Ion 
        lst: list of filename data
        path=path to save figures and pickle
        name=name of pickle file
        T= number of expected temperature
        wss = width of fit for ss
        wvth: width of fit for Vth
        param : parameter for SS calculation : [minVds50,MaxVds50,ValueVds50,minVds900,minVds900,ValueVds900]"""
    data = loadmapDC(lst,Temp_name)
    # Offset= loadmapDC(Offset)
    c1 = cm.get_cmap('coolwarm', T)
    legend=[]
    
    for index, i in enumerate(data):
                    
        if i.Vds==0.05:
            legend = np.append(legend,[str(int(i.T))+'K'])
            plt.figure(1)
            plt.semilogy(i.Vg, i.I,color=c1(int(index/2)))
            
        if i.Vds==0.9:            
            plt.figure(2)
            plt.legend(loc="best")
            plt.semilogy(i.Vg, i.I,color=c1(int(index/2)))
            
    data=Ioff(data)
    data=vth(data,wvth,T)
    data=ss(data,param,wss)

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
    graph(figure(13),path,'SSlin'+name, 'Current (A)', '$SS $(mV/decade)', 'Linear regime $V_{DS}$ = 50 mV ',save=savegraph)
    graph(figure(15),path,'SSsat'+name, 'Current (A)', '$SS $(mV/decade)', 'Saturations regime $V_{DS}$ = 900 mV ',save=savegraph)
    graph(figure(16),path,'SS'+name, 'Temperature (K)', '$SS (mV/decade)$', '', ['$V_{DS}$ = 50 mV','$V_{DS}$ = 0.9 V'], xtick=Tick, xticklabel=Tticklabel,save=savegraph)
    graph(figure(13),path,'SSlin'+name, 'Current (A)', '$SS $(mV/decade)', 'Linear regime $V_{DS}$ = 50 mV ',save=savegraph)
    plt.show()

    if savepickle:
        with open(path +'\\' + name + ".pickle", 'wb') as DataSave:
               pickle.dump(data, DataSave)

    return data
