
########################## Copyrights and license ############################
#                                                                            #
# Copyright Claude Rohrbacher <claude.rohrb@gmail.com>   					 #
#                                                                            #
# This file is part of  QIQSS-CODE							 		         #
#                                                                            #
##############################################################################

from IPython.display import clear_output
import matplotlib.pyplot as plt
import ipywidgets as widgets
from ipywidgets import Button, HBox, VBox, interactive, FloatLogSlider, Layout,IntSlider,interactive_output,interact
import util
import numpy as np
import fitting as fit
import gen_poly as poly
import fit_functions as fitFCT
import derivative as der
import pickle
import scipy

from GraphStyle import graphPy3

class Device:
	"""
		Classe de donnees pour mieux naviguer les donnees de transistor
		Un Device correspond a toutes les donnees prises sur un meme device.
		est compose d'un seul attribut : la list de dictionnaire des donnees traite.
	"""
	def __init__(self):
		self.list_data=[]
		self.dibl = []
		self.T_lin = 0
		self.T_sat = 0
		self.ss_sat = 0
		self.ss_lin = 0
		self.Vth_lin = 0
		self.vth_sat = 0
		self.ss_sat_err = 0
		self.ss_lin_err = 0
		
	def generate_list(self):
		# temperature list
		self.T_lin = [d['Temp'] for d in self.list_data if d['curve_type'] == 'lin']
		self.T_sat = [d['Temp'] for d in self.list_data if d['curve_type'] == 'sat']
		#ion and ioff 
		self.ioff_lin = [d['Ioff'] for d in self.list_data if d['curve_type'] == 'lin']
		self.ioff_err = [d['Ioff_err'] for d in self.list_data if d['curve_type'] == 'lin']
		self.ioff_sat_err = [d['Ioff_err'] for d in self.list_data if d['curve_type'] == 'sat']
		self.ioff_sat = [d['Ioff'] for d in self.list_data if d['curve_type'] == 'sat']
		self.ion_lin = [d['Ion'] for d in self.list_data if d['curve_type'] == 'lin']
		self.ion_sat = [d['Ion'] for d in self.list_data if d['curve_type'] == 'sat']
		# Vth
		self.Vth_lin = [d['Vth'] for d in self.list_data if d['curve_type'] == 'lin']
		self.Vth_error = [d['Vth_err'] for d in self.list_data if d['curve_type'] == 'lin']
		self.Vth_sat =[d['Vth'] for d in self.list_data if d['curve_type'] == 'sat']
		# SS
		self.ss_lin =[d['ss'] for d in self.list_data if d['curve_type'] == 'lin']
		self.ss_sat =[d['ss'] for d in self.list_data if d['curve_type'] == 'sat']
		self.ss_sat_err = [d['ss_err'] for d in self.list_data if d['curve_type'] == 'sat']
		self.ss_lin_err = [d['ss_err'] for d in self.list_data if d['curve_type'] == 'lin']

	def dibl_calc(self, val=None):
		'''
		calculate the dibl (in mV/V)
		'''
		# Vth
		vth_lin =np.array([d['Vth']*1e3 for d in self.list_data if d['curve_type'] == 'lin'])
		vth_sat =np.array([d['Vth']*1e3 for d in self.list_data if d['curve_type'] == 'sat'])
		# Vds
		vds_lin = [d['Vds'] for d in self.list_data if d['curve_type'] == 'lin'][0]
		try:
			vds_sat = [d['Vds'] for d in self.list_data if d['curve_type'] == 'sat'][0]
			self.dibl= -(vth_sat-vth_lin)/(vds_sat-vds_lin)
		except:
			vds_sat = 0
			print('Carefull no curve at sat found')
			self.dibl= None

	def draw_ss_current(self,fig_check):
		'''
		Plot ss(I)
		send a figure as argument
		made to plot the full fig_check figure with vth 
		'''
		#on cree les axes
		ax1 = fig_check.add_subplot(2,2,3)
		ax2 = fig_check.add_subplot(2,2,4)
		# Colorbar from cool to warm
		T_lin = [d['Temp'] for d in self.list_data if d['curve_type'] == 'lin']
		colorbar = plt.colormaps['plasma'].resampled(len(T_lin))
		c1 = 0
		for index, i in enumerate(self.list_data):
			
			if i['curve_type'] == 'lin':
				ax1.semilogx(i['ss_current'][0],i['ss_current'][1],'o',markersize=2,color=colorbar(index))
			if i['curve_type'] == 'sat':
				ax2.semilogx(i['ss_current'][0],i['ss_current'][1],'o',markersize=2,color=colorbar(c1))
				c1 +=1
		current_lin = [d['ssi'] for d in self.list_data if d['curve_type'] == 'lin'][0]
		try:
			current_sat = [d['ssi'] for d in self.list_data if d['curve_type'] == 'sat'][0]
		except :
			current_sat = None

		# On trace la ligne de selection de courant
		ax1.plot([current_lin]*2,[0,100],'--')
		ax2.plot([current_sat]*2,[0,100],'--')	

		graphPy3(fig_check,ax1,name=None,
	   				xlabel='I (A)', ylabel=r'SS (mV/decade)',
					title='Linear regime',
					ylim=[0,250],
					figsize=[8,8])
		graphPy3(fig_check,ax2,name=None, 
	   				xlabel='I (A)', ylabel=r'SS (mV/decade)',
					ylim=[0,250],
					title='Saturation regime',
		 			figsize=[8,8])
		
		plt.tight_layout

	def draw_results(self,savepath,name='',save = False):
		'''
		Plot on one figure all the results and save them
		'''
		# Colorbar from cool to warm
		c1 =0
		fig = plt.figure()
		ax1 = fig.add_subplot (4,2,1) # IdVg lin
		ax2 = fig.add_subplot (4,2,2) # IdVg sat
		ax3 = fig.add_subplot (4,2,3) # SS  with T
		ax4 = fig.add_subplot (4,2,4) # Vth with T
		ax5 = fig.add_subplot (4,2,5) # ioff with T
		ax6 = fig.add_subplot (4,2,6) # ion with T
		ax7 = fig.add_subplot (4,2,7) # DIBL
		size=[8,18]
		#generate value
		self.generate_list()
		#temperature legends
		colorbar = plt.colormaps['plasma'].resampled(len(self.T_lin))
		str_temp_lin = [str(d['Temp']) + ' K' for d in self.list_data if d['curve_type'] == 'lin'] 
		str_temp_sat = [str(d['Temp']) + ' K' for d in self.list_data if d['curve_type'] == 'sat'] 

		# string of vds value
		str_vds_lin = r'$V_{DS}$ = ' + [str(int(d['Vds']*1e3)) for d in self.list_data if d['curve_type'] == 'lin'][0] + ' mV'
		try:
			str_vds_sat = r'$V_{DS}$ = ' +[str(int(d['Vds']*1e3)) for d in self.list_data if d['curve_type'] == 'sat'][0] + ' mV'
		except:
			str_vds_sat = None

		#Temperature tick
		T_tick = [1,4,10,77,300]
		T_tick_label = ['1','4','10','77','300']

	# ON TRACE ID-VG
		for index, i in enumerate(self.list_data):
			if i['curve_type'] == 'lin':
				ax1.semilogy(i['Vg'],i['I'],'o', markersize = 2,color = colorbar(index))

			if i['curve_type'] == 'sat':
				ax2.semilogy(i['Vg'],i['I'],'o', markersize = 2,color = colorbar(c1))
				c1 +=1

		ax3.errorbar(self.T_lin,self.ss_lin,yerr=self.ss_lin_err,marker='o', label = str_vds_lin,elinewidth=1)
		ax3.errorbar(self.T_sat,self.ss_sat,yerr=self.ss_sat_err,marker='o', label = str_vds_sat,elinewidth=1)
		ax3.set_xscale('log')
		ax3.legend()

		# ax4.semilogx(self.T_lin,Vth_lin,'-o', label = str_vds_lin)
		ax4.errorbar(self.T_lin,self.Vth_lin,yerr=self.Vth_error,marker='o',capsize=4, elinewidth=1, label = str_vds_lin)
		ax4.semilogx(self.T_sat,self.Vth_sat,'-o', label = str_vds_sat)
		ax4.legend()

		ax5.loglog(self.T_lin,self.ion_lin, '-o',label = str_vds_lin)
		ax5.loglog(self.T_sat,self.ion_sat, '-o',label = str_vds_sat)
		ax5.legend()
		try:
			ax6.errorbar(self.T_lin,self.ioff_lin, yerr=self.ioff_err,marker='o',capsize=4, elinewidth=1, label = str_vds_lin)
			ax6.errorbar(self.T_sat,self.ioff_sat, yerr=self.ioff_sat_err,marker='o',capsize=4, elinewidth=1, label = str_vds_lin)	
			
			ax6.legend()
		except:
			print('no ioff')

		try:	
			ax7.semilogx(self.T_lin,self.dibl,'-o')
		except:
			print ('no dibl')

		graphPy3(fig,ax1,name=None, 
					xlabel='Vg (V)', ylabel=r'I (A)',
					title=str_vds_lin, 
					figsize=size,
					legend = str_temp_lin,col=1, fontsize=10)

		graphPy3(fig,ax2,name=None, 
					xlabel='Vg (V)', ylabel=r'I (A)',
					title=str_vds_sat,
					figsize=size,
					legend = str_temp_sat, col =1, fontsize=10)
		# in case no sat data
		try: max(ss_sat)
		except : ss_sat=[np.max(self.ss_lin)]
		graphPy3(fig,ax3,name=None, 
					xlabel='T (K)', ylabel=r'SS (mv/decade)',
					title='Subthreshold swing',
					xtick=T_tick, xticklabel= T_tick_label,
					ylim=[0,max(ss_sat)+10],
					figsize=size)
		graphPy3(fig,ax4,name=None, 
					xlabel='T (K)', ylabel=r'$V_{TH}$ (V)',
					title='Threshold voltage',
					xtick=T_tick, xticklabel= T_tick_label,
					figsize=size)
		graphPy3(fig,ax5,name=None, 
					xlabel='T (K)', ylabel=r'$I_{ON}$ (A)',
					title=r'$I_{ON}$',
					xtick=T_tick, xticklabel= T_tick_label,
					figsize=size)
		graphPy3(fig,ax7,name=None, 
					xlabel='T (K)', ylabel=r'DIBL (mV/V)',
					title=r'DIBL',
					xtick=T_tick, xticklabel= T_tick_label,
					figsize=size)		
		# this graph saves everything
		graphPy3(fig,ax6,path = savepath,name=name, 
					xlabel='T (K)', ylabel=r'$I_{OFF}$ (A)',
					title=r'$I_{OFF}$',
					xtick=T_tick, xticklabel= T_tick_label,
					figsize=size, save=save, format = 'svg')
		
		plt.tight_layout()
		return fig



def ion_ioff(device):
	"Calcul le Ion et Ioff du device"

	for i in device.list_data:
			index_0 =np.argmin(np.abs(i['Vg']))
			index_1 =np.argmin(np.abs(i['Vg']-i['Vds']))
			i['Ioff'] = np.mean(i['I'][index_0-2:index_0+2])
			i['Ioff_err'] = np.std(i['I'][index_0-2:index_0+2])
			if i['Ioff'] < 0: 
				i['Ioff'] = i['Ioff_err']
			if i['Vds'] < 0.1:	
				i['Ion'] = i['I'][-1]
			else: i['Ion'] = i['I'][index_1]
def vth_calculator(device,fig=None):
	'''
	find the threshold voltage of the transistor. 
	method for lin : linear fit at max gm value
	method sat  : voltage for which current = I(Vth) in linear regim
	'''
	# Colorbar from cool to warm
	colorbar = plt.colormaps['plasma'].resampled(count_values_by_key(device.list_data,'Temp'))
	c1=0
	for index,i in enumerate(device.list_data):
		# discriminate between lin and sat
		# if load_data is correct data should already be sorted correctly to first calculate linar value
		
		if i['curve_type'] == 'lin' :
			gm = der.Dfilter(i['Vg'],i['I'],10)[1]*1e6 # transconductance in uS
			# Plot conductance
			ax1 = plt.subplot(2, 2, 1)
			ax1.plot(i['Vg'],gm,'o',markersize=1,color=colorbar(index))
			graphPy3(fig,name=None, xlabel='Vg (V)', ylabel=r'Gm ($\mu S$)', title='Transconductance linear regime',
					figsize=[8,8])
			
			#find the max of conductance
			gm_max_index = np.argmax(np.abs(gm))
			
			# fit I(Vg) with linear curve over small Vg range
			p0 = [-0.00091647 , 0.00113323]  # fit parameter
			(b, a), _, (db, da), _ = fit.fitcurve(fitFCT.linear, i['Vg'][gm_max_index-5:gm_max_index+5],
													i['I'][gm_max_index-5:gm_max_index+5], p0)  # linear fit
			
			# calculate the Vth, if Ioff exist  Vg at which linear fit equals Ioff\0 if not
			if i['Ioff'] > 0 : i['Vth'] = (i['Ioff'] - b) / a
			else: i['Vth'] = (0 - b) / a

			# plot of the fit to check if correct
			x = np.linspace(i['Vg'][gm_max_index]-0.2,i['Vg'][gm_max_index]+0.2)
			y = a * x + b 
			ax2 = plt.subplot(2, 2, 2)
			ax2.plot(i['Vg'], i['I'],'--',color=colorbar(index))
			ax2.plot(x, y,'-',color=colorbar(index))
			graphPy3(fig,name=None, xlabel='Vg (V)', ylabel=r'I (A)', title='Threshold fit',
		 			figsize=[8,8])
			# ax2.plot([min(x), max(x)],[min(y), max(y)],'o',color=colorbar(index))

			# calcul de l'erreur d_vth = 1/a * db + b/a^2 * da
			i['vth_err'] = 1/a * db + b / (a**2) * da		

		if i['curve_type'] == 'sat' :
						
			# get the corresponding lin curve
			try:
				lin = list(filter(lambda temp: temp['Temp'] == i['Temp'] and temp['curve_type'] == 'lin',device.list_data))[0]
			except:
				# if T slighlty different, correct the error and take the closest T
				print('Warning, not exactly equal temperature between lin and sat curve')
				lin = list(filter(lambda temp: temp['Temp'] < i['Temp']+2 and temp['Temp'] > i['Temp']-2 and temp['curve_type'] == 'lin',device.list_data))[0]

			# Find the value of current at vth (lin)
			if lin['Vth'] == 0:
				i['Vth'] = None
				print('No linear vth were found')
			else:
				if i['transistor_type'] == 'nmos':
					i_lin =  lin['I'][np.searchsorted(i['Vg'],lin['Vth'])]
					i['Vth'] = i['Vg'][np.argmin(np.abs(i['I']-i_lin))]
				if i['transistor_type'] == 'pmos':
					i_lin =  lin['I'][::-1][np.searchsorted(i['Vg'][::-1],lin['Vth'])]
					i['Vth'] = i['Vg'][np.argmin(np.abs(i['I']-i_lin))]
def ss_slider(device):
	'''
	find the subthreshold swing of the transistor. 
	first determine the range of fitting for both lin and sat curve
	then call to fit once button is called
	'''
	fig = plt.figure(figsize=[8,3]) # a commenter si qt 
	ax_lin = fig.add_subplot(1,2,1)
	ax_sat = fig.add_subplot(1,2,2)
	# fig=plt.figure(figsize=[8,3]) # comment if inline

	# fonction lorsque le bouton de selection est clique

	out = widgets.Output()
	def on_button_clicked(b):
		val = [w1.value,w2.value,w3.value,w4.value]
		ss_fit(device,val)


	# fonction pour tracer lorsque le slider bouge
	def draw_current_select(w1,w2,w3,w4):
		
		ax_lin.clear()
		ax_sat.clear()# a comment si inline
		
		#create colorbar depending of the number of temperature
		colorbar = plt.colormaps['plasma'].resampled(count_values_by_key(device.list_data,'Temp'))
		c1=0; #second index for sat curve colorbar	

		for index,i in enumerate(device.list_data):
			
			# We get the Vg index for each curve depending on the current range we want to look for
			
	
			# On trace les figures 
			if i['curve_type'] == 'lin':
				index_min = np.argmin(np.abs(i['I']-w1))
				index_max = np.argmin(np.abs(i['I']-w2))
				ax_lin.semilogy(i['Vg'][index_min:index_max],
								i['I'][index_min:index_max],
								'o', markersize = 2,
								color=colorbar(index))
			

			if i['curve_type'] == 'sat':
				index_min = np.argmin(np.abs(i['I']-w3))
				index_max = np.argmin(np.abs(i['I']-w4))
				ax_sat.semilogy(i['Vg'][index_min:index_max],
								i['I'][index_min:index_max],
								'o', markersize = 2,
								color=colorbar(c1))
				c1 += 1


		i_min =  min(min(device.list_data, key=lambda d:np.min(d['I']))['I'])
		i_max =  max(max(device.list_data, key=lambda d:np.max(d['I']))['I'])

		ax_lin.set_ylim(1e-14,1e-3)
		ax_sat.set_ylim(1e-14,1e-3)
		fig.canvas.draw()
		plt.tight_layout()

	# On cree les widget
	button = Button(description="Validate",
			 				layout=Layout(width='25%', height='25px'))
	
	# Widget for linear curve
	w1 = FloatLogSlider(description='Min',value=1e-14,min=-14, max=-3)
	w2 = FloatLogSlider(description='Max',value=1e-4,min=-14, max=-3)

	# Widget for saturation curve
	w3 = FloatLogSlider(description='Min',value=1e-14,min=-14, max=-3)
	w4 = FloatLogSlider(description='Max',value=1e-4,min=-14, max=-3)
	
	# Layout des widget
	widget=widgets.interactive(draw_current_select,w1=w1,w2=w2,w3=w3,w4=w4, display=False)
# 	hbox = HBox([VBox([w1, w2]),VBox([w3, w4])])
	w4.close_all

	#bouton de selection
	v = button.on_click(on_button_clicked) 
	display(button)
	display(widget)

def ss_fit(device,val):
	
	'''
	Perform the fit at different current value 
	device : device class
	val : value extracted from the ss_slider function. otherwise can send value in this form
		[min_current_lin,max_current_lin,min_current_sat,max_current_sat]
		in ampere unit
	'''

	colorbar = plt.colormaps['plasma'].resampled(count_values_by_key(device.list_data,'Temp'))
	p0=[-14.22168096,  12.76228698]

	# fig = plt.figure() # comment if inline 
	fig = plt.figure() #comment if qt
	ax1 = fig.add_subplot(1,2,1)
	ax2 = fig.add_subplot(1,2,2)

	def draw_fit(fit_w,ss_i_lin,ss_i_sat):
		
		# When the slider is change replot the fit with new fit width
		ax1.clear()
		ax2.clear()	
		ylim_lin, ylim_sat = 0,0

		c1 = 0 # compteur for colorbar
		for index,i in enumerate(device.list_data):
			error = [] #error bar for ss
			i['ss_current'] = [[],[]]
			# I in log base 10 
			y=np.ma.log10(np.abs(i['I']))

			# We get the Vg index for each curve depending on the current range we want to look for
			# On trace les figures
			if i['curve_type'] == 'lin':

				# range of measurement taken from slider
				index_min = np.argmin(np.abs(i['I']-val[0]))
				index_max = np.argmin(np.abs(i['I']-val[1]))
				
				
				for j in range(index_min,index_max,1):
					# on fit 
					try:
						courbefit = fit.fitcurve(fitFCT.linear,
				    							i['Vg'][j-fit_w:j+fit_w],
												y[j-fit_w:j+fit_w],
												 p0)
					except:	
						courbefit = fit.fitcurve(fitFCT.linear,
				    							i['Vg'][j:j+2*fit_w],
												y[j:j+2*fit_w],
												 p0)
					
					# on initialise le courant et la valeur du fit dans ss current
					ss = 1/abs(courbefit[0][1])*1e3 # en mv/decade
					i['ss_current'][0].append(i['I'][j])
					i['ss_current'][1].append(ss)
					error.append(abs(ss*(courbefit[2][1]/courbefit[0][1])))

				# on fixe la valeur du ss en fonction du choix du courant
				arg = np.argmin(np.abs(np.asarray(i['ss_current'][0])-ss_i_lin))
				i['ss'] = i['ss_current'][1][arg]
				i['ss_err'] = error[arg] + np.std(i['ss_current'][1][arg-1:arg+1])
				i['ssi'] = ss_i_lin
				
				# on trace SS en fonction de I
				ax1.semilogx(i['ss_current'][0],i['ss_current'][1],
		 					'o',markersize=2,color=colorbar(index))

				if ylim_lin < max(i['ss_current'][1]): ylim_lin = max(i['ss_current'][1])
				if ylim_lin > 250 : ylim_lin =250 

			if i['curve_type'] == 'sat':
				
				# range of measurement taken from slider
				index_min = np.argmin(np.abs(i['I']-val[2]))
				index_max = np.argmin(np.abs(i['I']-val[3]))
				
				for j in range(index_min,index_max,1):
					# on fit
					# calm error on the fit
					try:
						courbefit = fit.fitcurve(fitFCT.linear,
				    							i['Vg'][j-fit_w:j+fit_w],
												y[j-fit_w:j+fit_w],
												 p0)
					except:	
						courbefit = fit.fitcurve(fitFCT.linear,
				    							i['Vg'][j:j+2*fit_w],
												y[j:j+2*fit_w],
												 p0)
					# on initialise le courant et la valeur du fit dans ss current
					ss = 1/abs(courbefit[0][1])*1e3 # en mv/decade
					i['ss_current'][0].append(i['I'][j])
					i['ss_current'][1].append(ss)
					error.append(abs(ss*(courbefit[2][1]/courbefit[0][1])))

				# on fixe la valeur du ss en fonction du choix du courant et on calcul l'incertitude
				arg = np.argmin(np.abs(np.asarray(i['ss_current'][0])-ss_i_sat))
				i['ss'] = i['ss_current'][1][arg]
				i['ss_err'] = error[arg] + np.std(i['ss_current'][1][arg-1:arg+1])
				i['ssi'] = ss_i_sat

				# on trace SS en fonction de I
				ax2.semilogx(i['ss_current'][0],i['ss_current'][1],
		 						'o',markersize = 2, color=colorbar(c1))
				
				if ylim_sat < max(i['ss_current'][1]): ylim_sat = max(i['ss_current'][1])
				if ylim_sat > 250 : ylim_sat =250 
				c1 += 1

		# on trace les ligne de selection
		ax1.plot([ss_i_lin]*2,[0,100],'--')
		ax2.plot([ss_i_sat]*2,[0,100],'--')

		graphPy3(fig,ax1,name=None,
	   				xlabel='I (A)', ylabel=r'SS (mV/decade)',
					title='Linear regime',
					ylim=[0,ylim_lin],
					figsize=[9,3],aspect = False)
		graphPy3(fig,ax2,name=None, 
	   				xlabel='I (A)', ylabel=r'SS (mV/decade)',
					ylim=[0,ylim_sat],
					title='Saturation regime',
		 			figsize=[9,3],aspect= False)
		plt.tight_layout()

	#slider for width			
	w1 = widgets.BoundedIntText(description='Fit Widdth',value=2,min=2, max=100)
	
	# slider pour selectionner le courant

	w2 = FloatLogSlider(description='Select Current (lin)',value=val[0],min=np.log10(val[0]), max=np.log10(val[1]))
	w3 = FloatLogSlider(description='Select Current (lin)',value=val[3],min=np.log10(val[2]), max=np.log10(val[3]))				
	widget = interactive(draw_fit,fit_w=w1,ss_i_lin=w2,ss_i_sat=w3)
	display(widget)

def full_analysis(dev,savepath,name, save = False):

	def ss_button(b):
		# Bouton activié quand l'analyse du SS est terminé
		clear_output()
		fig_check=plt.figure()
		vth_calculator(dev,fig_check)
		dev.dibl_calc()
		#drawing check and result fig

		dev.draw_ss_current(fig_check)

		#on sauvegarde les figure
		graphPy3(fig_check,
					name= name +'Figure Check',
					figsize = [8,8],
					path = savepath,
					save = save)
		# Save Data if save is True
		dev.generate_list() # génere les list
		if save:
			with open(savepath +'\\' + name + ".pickle", 'wb') as DataSave:
				pickle.dump(dev, DataSave)

	ion_ioff(dev)
	ss_slider(dev)	
	
	# Le boutton indiquant que l'analyse du SS est terminé
	button = Button(description="SS finish",
			 				layout=Layout(width='25%', height='25px'))
	button.on_click(ss_button)
	display(button)


	# input("Press Enter to continue...")
###########################################
##########Various utilitary function#######
###########################################
###########################################

def count_values_by_key(lst, key):
	# Initialize an empty set to keep track of the different values found for the key
	values = set()
	
	# Iterate over each dictionary in the list
	for dct in lst:
		# Check if the input key is in the current dictionary
		if key in dct:
			# If the key is in the dictionary, add the value for that key to the set of values
			values.add(dct[key])
	
	# Return the length of the set of values, which represents the number of different values found for the key
	return len(values)

