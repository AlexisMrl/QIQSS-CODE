
import Thot
from Thot import Device
import re 
import os
import numpy as np
from IPython.display import clear_output
import util
import sys
sys.path.append('C:\Program Files\Labber\Script')
try:
	import Labber
except:
	print('no Labber detected')
	
def create_dict():
	data_dictionnary = {
			'RawData' : np.array([]),
			'comment' : [],
			'Vg' : [],
			'I' : [],
			'Data_headers': [],
			'Vds' :  0,
			'Temp' : 0,
			'Ioff' : 0,
			'Ioff_err':0 ,
			'Ion' : 0,
			'Vth' : 0,
			'Vth_err' : 0,
			'ss' : 0,
			'ss_err':0,
			'ssi' : 0,
			'dibl' : 0,
			'ss_current' : [[],[]],
			'curve_type' : 'lin',
			'transistor_type' : 'nmos'
			}
	return data_dictionnary

def load_data_claude(folder,temp_name='Temperature'):

	"""
		Load Id-Vg measurements.
		create the data dictionnary and put all of them in a list
		The function return the list of Mydata (see MyData class for method)
		assign Vds and Temperature value. 
		IMPORTANT
		Everytime you have new way of taking and saving data you should create a new loadData function.
		Make sure to have an output with same format as this one

		folder: folder with all the data.
	"""
	#cherche toutes les donnees de transistor dans le fichier pour traitement
	file_list=[f for f in os.listdir(folder) if os.path.isfile(folder+f)]
	file_list=[folder+s  for s in file_list]
	device = Device()  # list of dictionnary that regroup all data from a device
	for i in range(len(file_list)):  # For each file

		datatemp = create_dict()  #Create the data dictionnary 
		file = util.readfile(file_list[i], getheaders=True) # extract data

		#On initialise le dictionnaire
		datatemp['comment'] = file[2]
		datatemp['RawData'] = file[0]
		datatemp['Data_headers'] = file[1]
		datatemp['Vds'] = file[0][0][0][0]

		# on trouve vg et I
		# print(file[0][4][0])
		datatemp['Vg'] = file[0][2][0]
		datatemp['I'] = file[0][4][0]
	
		# search in comment  Temperature
		for line in datatemp['comment']:
			match = re.search("Temperature:([^;]\S+)", line)
			if match:
				datatemp['Temp'] = float(match.group((1)))
		# tell if lin or sat
		if datatemp['Vds'] < 0.1: datatemp['curve_type'] = 'lin' 
		else: datatemp['curve_type'] = 'sat'

		device.list_data.append(datatemp)

	# sorting data for all Vds lin first
	device.list_data = sorted(device.list_data, key=lambda d: (d['Vds'],d['Temp'])) 
	clear_output()
	return device



def load_labber(folder,Vds_name=''):

	"""
		Load Id-Vg measurements for Labber data taken in michel's lab
		create the data dictionnary and put all of them in a list
		The function return the list of Mydata (see MyData class for method)
		assign Vds and Temperature value. 
		IMPORTANT
		Everytime you have new way of taking and saving data you should create a new loadData function.
		Make sure to have an output with same format as this one

		folder: folder with all the data.
	"""
	#cherche toutes les donnees de transistor dans le fichier pour traitement
	file_list=[f for f in os.listdir(folder) if os.path.isfile(folder+f)]
	file_list=[folder+s  for s in file_list]
	device = Device()  # list of dictionnary that regroup all data from a device
	for i in range(len(file_list)):  # For each file

		datatemp = create_dict()  #Create the data dictionnary 
		file =Labber.LogFile(file_list[i]) # extract data

		#On initialise le dictionnaire

		datatemp['RawData'] =  file.getEntry(0)
		try:
			datatemp['Vds'] = file.getData(Vds_name)[0,0]
		except:
			datatemp['Vds'] = file.getData(Vds_name+' 70nm')[0,0]
		# on trouve vg et I
	
		(datatemp['Vg'],datatemp['I']) = file.getTraceXY()
		print(file)
		# Temperature
		try:
			datatemp['Temp'] = file.getChannelValuesAsDict()['Lakeshore - Setpoint 1']
			if datatemp['Temp'] == 275: datatemp['Temp'] = 294
			if datatemp['Temp'] == 240: datatemp['Temp'] = 250
		except:
			datatemp['Temp'] = int(file.getData('Lakeshore 33x - Temperature C')[0,0])
		# tell if lin or sat
		if datatemp['Vds'] < 0.1: datatemp['curve_type'] = 'lin' 
		else: datatemp['curve_type'] = 'sat'

		device.list_data.append(datatemp)

	# sorting data for all Vds lin first
	device.list_data = sorted(device.list_data, key=lambda d: (d['Vds'],d['Temp']))
	clear_output()
	return device

def load_data_ben(folder):

	"""
		Load Id-Vg measurements.
		create the data dictionnary and put all of them in a list
		The function return the list of Mydata (see MyData class for method)
		assign Vds and Temperature value. 
		IMPORTANT
		Everytime you have new way of taking and saving data you should create a new loadData function.
		Make sure to have an output with same format as this one

		folder: folder with all the data.
	"""
	#cherche toutes les donnees de transistor dans le fichier pour traitement
	file_list=[f for f in os.listdir(folder) if os.path.isfile(folder+f)]
	file_list=[folder+s  for s in file_list]
	device = Device()  # list of dictionnary that regroup all data from a device
	for i in range(len(file_list)):  # For each file

		datatemp = create_dict()  #Create the data dictionnary 
		file = util.readfile(file_list[i], getheaders=True) # extract data

		#On initialise le dictionnaire
		datatemp['comment'] = file[2]
		datatemp['RawData'] = file[0]
		datatemp['Data_headers'] = file[1]
		datatemp['Temp'] = round(file[0][3][0])
		if datatemp['Temp'] > 300: datatemp['Temp'] = 300
		# on trouve vg et I
		# print(file[0][4][0])
		datatemp['Vg'] = file[0][0]
		datatemp['I'] = file[0][1]
	
		# search in comment  Temperature
		for line in datatemp['comment']:
			match = re.search("Vds:([^;]\S+)", line)
			if match:
				datatemp['Vds'] = float(match.group((1)))

		# tell if lin or sat
		if datatemp['Vds'] < 0.2: datatemp['curve_type'] = 'lin' 
		else: datatemp['curve_type'] = 'sat'

		device.list_data.append(datatemp)

	# sorting data for all Vds lin first
	device.list_data = sorted(device.list_data, key=lambda d: (d['Vds'],d['Temp'])) 
	clear_output()
	return device

def load_data_antoine(folder):
	"""
	Load Id-Vg measurements.
	create the data dictionnary and put all of them in a list
	The function return the list of Mydata (see MyData class for method)
	assign Vds and Temperature value. 
	IMPORTANT
	Everytime you have new way of taking and saving data you should create a new loadData function.
	Make sure to have an output with same format as this one
	folder: folder with all the data.
	"""
	#cherche toutes les donnees de transistor dans le fichier pour traitement
	file_list=[f for f in os.listdir(folder) if os.path.isfile(folder+f)]
	file_list=[folder+s  for s in file_list]
	device = Device()  # list of dictionnary that regroup all data from a device
	for i in range(len(file_list)):  # For each file

		datatemp = create_dict()  #Create the data dictionnary 
		file = util.readfile(file_list[i], getheaders=True) # extract data

		#On initialise le dictionnaire
		datatemp['comment'] = file[2]
		datatemp['RawData'] = file[0]
		datatemp['Data_headers'] = file[1]
		datatemp['Vg'] = file[0][0]
		datatemp['I'] = file[0][1]
	
		# search in comment  Temperature amd vds
		# Extract Temperature and Vd from the comments of the file
		for line in datatemp['comment']:
			match = re.search("T =([^;]\S+)", line)
			match2 = re.search("Vd =([^;]\S+)",line)
			if match:
				datatemp['Temp'] = float(match.group((1))[2:-1])
				if round(datatemp['Temp']) == 4 : datatemp['Temp'] = round(datatemp['Temp'],1)
				else : datatemp['Temp'] = round(datatemp['Temp'])
			if match2:
				datatemp['Vds'] = float(match2.group((1)))

		# tell if lin or sat
		if datatemp['Vds'] < 0.2: datatemp['curve_type'] = 'lin' 
		else: datatemp['curve_type'] = 'sat'

		device.list_data.append(datatemp)

	# sorting data for all Vds lin first
	device.list_data = sorted(device.list_data, key=lambda d: (d['Vds'],d['Temp'])) 
	clear_output()
	return device

def load_data_finfet(folder,t_type='n'):
	"""
	Load Id-Vg measurements.
	create the data dictionnary and put all of them in a list
	The function return the list of Mydata (see MyData class for method)
	assign Vds and Temperature value. 
	IMPORTANT
	Everytime you have new way of taking and saving data you should create a new loadData function.
	Make sure to have an output with same format as this one
	folder: folder with all the data.
	"""
	#cherche toutes les donnees de transistor dans le fichier pour traitement
	file_list=[f for f in os.listdir(folder) if os.path.isfile(folder+f)]
	file_list=[folder+s  for s in file_list]
	device = Device()  # list of dictionnary that regroup all data from a device
	for i in range(len(file_list)):  # For each file

		datatemp = create_dict()  #Create the data dictionnary 
		file = util.readfile(file_list[i], getheaders=True) # extract data

		#On initialise le dictionnaire
		datatemp['comment'] = file[2]
		datatemp['RawData'] = file[0]
		datatemp['Data_headers'] = file[1]
		if t_type == 'p':
			datatemp['Vg'] = file[0][0][::-1]
			datatemp['I'] = -file[0][1][::-1]
			datatemp['transistor_type'] = 'pmos'
		else: 
			datatemp['Vg'] = file[0][0]
			datatemp['I'] = file[0][1]
	
		# search in comment  Temperature amd vds
		# Extract Temperature and Vd from the comments of the file
		for line in datatemp['comment']:
			match = re.search("T =([^;]\S+)", line)
			match2 = re.search("Vd =([^;]\S+)",line)
			if match:
				datatemp['Temp'] = float(match.group((1))[2:-1])
				if round(datatemp['Temp']) == 4 : datatemp['Temp'] = round(datatemp['Temp'],1)
				else : datatemp['Temp'] = round(datatemp['Temp'])
			if match2:
				datatemp['Vds'] = float(match2.group((1)))

		# tell if lin or sat
		if abs(datatemp['Vds']) < 0.2: datatemp['curve_type'] = 'lin' 
		else: datatemp['curve_type'] = 'sat'

		device.list_data.append(datatemp)

	# sorting data for all Vds lin first
	device.list_data = sorted(device.list_data, key=lambda d: (abs(d['Vds']),d['Temp'])) 
	clear_output()
	return device


def load_data_gab(folder):
	"""
	Specificity : same as Antoine except i remove first point
	because of issue with SMU
	"""
	#cherche toutes les donnees de transistor dans le fichier pour traitement
	file_list=[f for f in os.listdir(folder) if os.path.isfile(folder+f)]
	file_list=[folder+s  for s in file_list]
	device = Device()  # list of dictionnary that regroup all data from a device
	for i in range(len(file_list)):  # For each file

		datatemp = create_dict()  #Create the data dictionnary 
		file = util.readfile(file_list[i], getheaders=True) # extract data

		#On initialise le dictionnaire
		datatemp['comment'] = file[2]
		datatemp['RawData'] = file[0]
		datatemp['Data_headers'] = file[1]
		datatemp['Vg'] = file[0][0][3:]
		datatemp['I'] = file[0][1][3:]
	
		# search in comment  Temperature amd vds
		# Extract Temperature and Vd from the comments of the file
		for line in datatemp['comment']:
			match = re.search("T =([^;]\S+)", line)
			match2 = re.search("Vd =([^;]\S+)",line)
			if match:
				datatemp['Temp'] = float(match.group((1))[2:-1])
				if round(datatemp['Temp']) == 4 : datatemp['Temp'] = round(datatemp['Temp'],1)
				else : datatemp['Temp'] = round(datatemp['Temp'])
			if match2:
				datatemp['Vds'] = float(match2.group((1)))

		# tell if lin or sat
		if datatemp['Vds'] < 0.2: datatemp['curve_type'] = 'lin' 
		else: datatemp['curve_type'] = 'sat'

		device.list_data.append(datatemp)

	# sorting data for all Vds lin first
	device.list_data = sorted(device.list_data, key=lambda d: (d['Vds'],d['Temp'])) 
	clear_output()
	return device

# def load_fata

def load_data_dominic(folder):

	"""
		Load Id-Vg measurements.
		create the data dictionnary and put all of them in a list
		The function return the list of Mydata (see MyData class for method)
		assign Vds and Temperature value. 
		IMPORTANT
		Everytime you have new way of taking and saving data you should create a new loadData function.
		Make sure to have an output with same format as this one

		folder: folder with all the data.
	"""
	#cherche toutes les donnees de transistor dans le fichier pour traitement
	file_list=[f for f in os.listdir(folder) if os.path.isfile(folder+f)]
	file_list=[folder+s  for s in file_list]
	device = Device()  # list of dictionnary that regroup all data from a device
	for i in range(len(file_list)):  # For each file

		datatemp = create_dict()  #Create the data dictionnary 
		file = util.readfile(file_list[i], getheaders=True) # extract data

		#On initialise le dictionnaire
		datatemp['comment'] = file[2]
		datatemp['RawData'] = file[0]
		datatemp['Data_headers'] = file[1]
		datatemp['Vg'] = file[0][0]
		datatemp['I'] = file[0][1]
	
		# search in comment  Temperature amd vds
		for line in datatemp['comment']:
			match = re.search("Vds:([^;]\S+)", line)
			if match:
				datatemp['Vds'] = float(match.group((1)))

		for line in datatemp['comment']:
			match = re.search("Temperature:([^;]\S+)", line)
			if match:
				datatemp['Temp'] = float(match.group((1)))

		# tell if lin or sat
		if datatemp['Vds'] < 0.2: datatemp['curve_type'] = 'lin' 
		else: datatemp['curve_type'] = 'sat'

		device.list_data.append(datatemp)

	# sorting data for all Vds lin first
	device.list_data = sorted(device.list_data, key=lambda d: (d['Vds'],d['Temp'])) 
	clear_output()
	return device