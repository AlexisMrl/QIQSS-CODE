#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Python Interface for quantum calculus processing


###############################
# MAIN WINDOW
###############################

import os
import sys
import re
#import time
import traceback
#import logging
#import logging.handlers
try:
    # This for python 2.7
    from cStringIO import StringIO
except ImportError:
    # This for python 3
    from io import StringIO

import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)


import numpy as np
import sliderVert as SliderVert
import Trace_profils
import Diamond_simulation
import DD_extracter
import Cursors

import contextlib
#import re
#import os.path
#import sys, os, 
#import random

from PyQt5 import QtCore, QtWidgets, uic#, QtGui
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QFileSystemModel 
#from PyQt5.QtGui import  QPixmap, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt #,QObject, pyqtSignal


#******************************************************************
import matplotlib
matplotlib.use("Qt5Agg")
#******************************************************************

from matplotlib.backends.backend_qt5agg import(
 FigureCanvasQTAgg as FigureCanvas,
 NavigationToolbar2QT as NavigationToolbar)
 
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backend_bases import key_press_handler
from matplotlib import ticker
import matplotlib.lines as lines


#*******************
from pyHegel import util as pyHu
from scipy.ndimage import filters #for derivative and other filters

shell_interactive = False

# The original QMessageBox keeps using setFixedSize which prevents
# window resizing.
# This codes tries to remove the maximum limit to allow resizing.
class QMessageBox_Resizable(QMessageBox):
    def __init__(self, *args, **kwargs):
        super(QMessageBox_Resizable, self).__init__(*args, **kwargs)
        # This allows focusInEvent.
        self.setFocusPolicy(Qt.StrongFocus)
    def reset_max(self):
        self.setMaximumWidth(QtWidgets.QWIDGETSIZE_MAX)
        self.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)
    def enterEvent(self, event):
        # This is for mouse enter event.
        super(QMessageBox_Resizable, self).enterEvent(event)
        self.reset_max()
    def focusInEvent(self, event):
        super(QMessageBox_Resizable, self).focusInEvent(event)
        self.reset_max()
    def resizeEvent(self, event):
        # This gets called in many situations (like selecting detailed)
        super(QMessageBox_Resizable, self).resizeEvent(event)
        self.reset_max()
    def event(self, event):
        ret = super(QMessageBox_Resizable, self).event(event)
        if event.type() == QtCore.QEvent.LayoutRequest:
            # This is for when detailed is unchecked.
            self.reset_max()
        return ret

class save_file_dialog(QFileDialog):
    """
    Change path for own computer
    """
    def __init__(self, parent = None):
      super(save_file_dialog, self).__init__(parent)
      self.name = self.getSaveFileName(self, 'Save File','C:\Users\devj2901\Documents\Recherche\SimuBQ\projects\\', 'Dat files (*.dat)')

#specify the ui file to load
formclass, baseclass = uic.loadUiType('mainwindow.ui')

def get_exc_traceback(exc_type=None, exc_value=None, exc_traceback=None):
    """
        brief : Get exception informations and get exception traceback
        params : exception informations
        """
    if exc_type is None:
        exc_type, exc_value, exc_traceback = sys.exc_info()
    s = StringIO()
    # internally uses sys.
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=s)
    tb = s.getvalue()
    s.close()
    exc = traceback.format_exception_only(exc_type, exc_value)
    exc = ''.join(exc)
    return exc, tb

MiB = 1024*1024
main_logger = None
def config_excepthook():
    """
        brief : ???
    """
    global _except_hook_orig
    try:
        _except_hook_orig
    except NameError:
        _except_hook_orig = sys.excepthook
    sys.excepthook = handle_exception

def handle_exception(exc_type, value, traceback):
    """
        brief : handle a critical error exception and force exit of program
        """
    _except_hook_orig(exc_type, value, traceback)
    report_exception('Critical Error', exc_info=(exc_type, value, traceback), level=QMessageBox.Critical)
    if not shell_interactive:
        # To force exit
        sys.exit(1)

def report_exception(title='Error', parent=None, exc_info=None, level=QMessageBox.Warning):
    # either exc and tb are not None or exc_info is not None or all are.
    """
        brief : log the exception
        """
    if exc_info is None:
        exc_info = sys.exc_info()
    exc_type, value, traceback = exc_info
    exc, tb = get_exc_traceback(exc_type, value, traceback)
    #main_logger.error(title, exc_info=(exc_type, value, traceback))
    mbox = QMessageBox_Resizable(level, title, exc, detailedText=tb, sizeGripEnabled=True)
    mbox.exec_()

@contextlib.contextmanager
def exception_context_manager(title='Error', parent=None):
    cntxt = exception_context_manager_value()
    try:
        yield cntxt
    except Exception as e:
        cntxt.error = True
        cntxt.exception = e
        report_exception(title, parent)

def close_application(self):
    '''this function closes the application'''
    qApp.quit()

class MyMainWindow(baseclass, formclass):
    
    def __init__(self):
        baseclass.__init__(self)
        self.setupUi(self)
        self.fig_dict = {}
        
        self.plot_status = 0
        self.TreeView.setAnimated(False)
        self.TreeView.setIndentation(20)
        self.TreeView.setColumnWidth(0, 200)
        self.TreeView.setColumnWidth(1, 80)
        self.TreeView.setColumnWidth(2, 190)
        self.TreeView.setSortingEnabled(True)
        self.model = QFileSystemModel(self)
        self.directory=None
        self.setDirectory()

        # Unecessary since on_TreeView_doubleClicked is already auto connected
        #self.TreeView.doubleClicked.connect(self.on_TreeView_doubleClicked)
        
        self.Comments.setReadOnly(True)
        
        self.fig1 = Figure()
        self.addmpl(self.fig1)

        #connection part for the buttons
        self.cb_src1.currentIndexChanged[int].connect(self.setAxisNames)
        self.cb_src2.currentIndexChanged[int].connect(self.setAxisNames)
        self.set_display_2.currentIndexChanged[int].connect(self.UpdateData)
        self.plot_status_display.currentIndexChanged[int].connect(self.UpdateData)
        self.inverseCheck.stateChanged.connect(self.inverseAxis)
        
        self.btn_clear.clicked.connect(self.clear)
        self.export_data.clicked.connect(self.export_data_matrix)
        self.btn_sim.clicked.connect(self.simulate)
        self.btn_DD.clicked.connect(self.dd_extract)
        self.nb_sim = 0
        
        #Tools for derivative and filters
        self.cb_sigma.valueChanged.connect(self.UpdateData)
        self.ord_filt.valueChanged.connect(self.UpdateData)
        self.cut_freq.valueChanged.connect(self.UpdateData)        
        
        #to load specified directory
        self.actionOpen.triggered.connect(self.openDirectory) #actions bar

        #self.actionReload.triggered.connect(self.load_config) #actions bar
        #self.actionSave.triggered.connect(self.save_config) #actions bar
        #self.actionSave_as_new.triggered.connect(self.save_as_new) #actions bar
        #self.actionCopy_filename.triggered.connect(self.copy_file_name) #actions bar
        #self.actionPreferences.triggered.connect(self.preferences) #actions bar
        #self.actionExit.triggered.connect(self.exit) #actions bar
        

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_TreeView_doubleClicked(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())
        self.filePath = self.model.filePath(indexItem)
        if self.filePath[-3:]=='txt': self.readFile()
    
    def readFile(self):
        self.twoDims = True    
        self.data, self.titles,self.headers = pyHu.readfile(self.filePath,getheaders=True,multi_sweep='force')
            
        #If 1d data, do not use multi_sweep
        if np.shape(myapp.data)[1]==1 or len(np.shape(self.data))==2:
            self.twoDims = False
            self.data, self.titles,self.headers = pyHu.readfile(self.filePath,getheaders=True,multi_sweep=False)

        self.comments=[c[len('#comment:= '):-1]for c in self.headers if c.startswith('#comment:=') or c.startswith('#com ...:=')]
        self.setComments()
        self.displayDataButtons()
        self.displayDataPlot() #default data displayed
               
    def openDirectory(self):
        self.directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.setDirectory()
        
    def setDirectory(self):
        if (self.directory == None):
            self.model.setRootPath(QtCore.QDir.rootPath())
        else :
            self.model.setRootPath(self.directory)
        
        self.indexRoot = self.model.index(self.model.rootPath())
        self.TreeView.setModel(self.model)
        self.TreeView.setRootIndex(self.indexRoot)
        self.TreeView.hideColumn(2)#hide column which specify if it's a directory or file

    def setComments(self):
        self.Comments.clear()
        self.str ="\n".join(self.comments)
        self.Comments.setPlainText(self.str)
    
    def clear(self):
        self.fig1.clf()
        self.canvas.draw()

    def export_data_matrix(self):
        """
        Export data displayed in matrix shape for further ananlysis
        The (0,0) coordinates must be at the graph origin (origin = lower)
        """
        s = save_file_dialog()
        if len(s.name[0]) != 0:
            f = open(s.name[0],'w')
            for x in range(self.dataToDisplay.shape[1]):
                for y in range(self.dataToDisplay.shape[0]):
                    if y != 0:
                        f.write('\t')
                    f.write(str(self.dataToDisplay[y,x]))
                f.write('\n')
            f.close()
            
    def simulate(self):
        """
        Create a DiamondSimulation object for simulation
        """
        if self.nb_sim == 0:
            self.simulation = Diamond_simulation.DiamondSimulation()
        self.simulation.setData(self.dataToDisplay.T, self.xmin, self.xmax, self.ymin, self.ymax)
        self.nb_sim +=1
        self.simulation.show()

    def dd_extract(self):
        """
        Create a DiamondSimulation object for simulation
        """
        self.dd_extraction = DD_extracter.DDExtracter()
        self.dd_extraction.setData(self.dataToDisplay.T, self.xmin, self.xmax, self.ymin, self.ymax)
        self.dd_extraction.show()

    def displayDataButtons(self):
        self.cb_src1.blockSignals(True)
        self.cb_src2.blockSignals(True)
        self.set_display_2.blockSignals(True)
        self.plot_status_display.blockSignals(True)
                                        
        self.cb_src1.clear()
        self.cb_src2.clear()
        self.set_display_2.clear()
        self.plot_status_display.clear()
        
        """
        Add name of new instrument here:
        """
        instruments = ['lockin', 'lockin_2','Lockin', 'zurich', 'Zurich', 'zi']
        for h in instruments: self.add_Mag_Phase(h)
        
        #Setting x and y possible titles for axis
        for g in range(len(self.titles)):
            self.cb_src1.addItem(self.titles[g])
            self.cb_src2.addItem(self.titles[g])
        
        if self.twoDims:
            #Add the different data to display
            for t in self.titles: 
                if t != 'time': self.set_display_2.addItem(t)
            self.set_display_2.setEnabled(True)
            
            #Trace graph only when 2D data array
            self.fig1.canvas.mpl_connect('button_press_event', self.onclick)
            
            #Indices for x coordinates begin at xind
            self.xcoord_ind = self.findCoordIndices(0)
            #Indices for y coordinates begin just after those for x
            self.ycoord_ind = self.findCoordIndices(self.xcoord_ind[-1]+1)

            #set default values for selectors
            self.cb_src1.setCurrentIndex(self.xcoord_ind[0])
            self.cb_src2.setCurrentIndex(self.ycoord_ind[0])
            self.set_display_2.setCurrentIndex(self.ycoord_ind[-1]+1)
            self.plot_status_display.addItems(["Unchanged","Log (base 10)","df/dx","df/dy","2D smoothing", "x smoothing", "y smoothing","Gradient magnitude","Butterworth filter","Tchebychev filter"])
            
        else:
            self.set_display_2.setEnabled(False)
            i = 0
            while np.unique(self.data[i,:]).size == 1: i+=1
            self.cb_src1.setCurrentIndex(i)
            self.cb_src2.setCurrentIndex(i+1)
            self.plot_status_display.addItems(["Unchanged","Log (base 10)","df/dx", "data smoothing"])
        
        #renable signals
        self.cb_src1.blockSignals(False)
        self.cb_src2.blockSignals(False)
        self.set_display_2.blockSignals(False)
        self.plot_status_display.blockSignals(False)

        #need info from file to nb of sublimes
        #nb_subline_2 = self.settings.value("Plot_2/nb_sublime", 2, type=int)
        #self.cb_nb_subline_2.setValue(nb_subline_2)
        
    def add_Mag_Phase(self, instrument):
        """
        Add magnitude and phase to data array
        """
        #Indices for real/imaginary values
        indx = None
        indy = None
        
        #Copy data and titles
        copdata = self.data.copy()
        coptitles = self.titles
        for i in range(len(self.titles)):
            if self.chainExp(self.titles[i], instrument):
                if self.chainExp(self.titles[i], 'x'):
                    indx = i
                elif self.chainExp(self.titles[i], 'y'):
                    indy = i
                if indx is not None and indy is not None:
                    break

        #Insert magnitude (then phase) after x and y values if they exist
        if indx is not None and indy is not None:
            #Add mag to data
            self.data = np.insert(copdata, int(max(indx, indy))+1, np.sqrt(copdata[int(indx)]**2 + copdata[int(indy)]**2), axis=0)
            #Add titles for mag
            self.titles = coptitles[:int(max(indx, indy))+1] + ['Magnitude '+str(instrument)] + coptitles[int(max(indx, indy))+1:]
        
            copdata2 = self.data.copy()
            coptitles2 = self.titles
            temp = np.zeros_like(self.data[0])
            
            if self.twoDims:
                #calculate phase if x different from 0
                for i in range(np.size(self.data[indx][:,0])):
                    for j in range(np.size(self.data[indx][0,:])):
                        if copdata[indx][i,j] != 0:
                            temp[i,j] = np.arctan(copdata[indy][i,j]/copdata[indx][i,j])
                        else:
                            temp[i,j] = float('nan')
            else:
                for i in range(np.size(self.data[indx])):
                    if copdata[indx,i] != 0:
                        temp[i] = np.arctan(copdata[indy,i]/copdata[indx,i])
                    else:
                        temp[i] = float('nan')
            #Add phase to data
            self.data = np.insert(copdata2,max(indx, indy)+2, temp, axis=0)
            #Add title for phase
            self.titles = coptitles2[:max(indx, indy)+2] + ['Phase '+str(instrument)] + coptitles2[max(indx, indy)+2:]
    
    def findCoordIndices(self, ind):
        """
        Return indices of coordinates data
        """
        i = len(self.titles[ind])-1
        while self.titles[ind][i] != '.' and i >= 0:
            i+=-1
        coord_title = self.titles[ind][0:i]
        coord_ind = [ind]
        while self.chainExp(self.titles[ind+1], coord_title):
            ind+=1
            coord_ind += [ind]
        return coord_ind
        
    def chainExp(self, chain, exp):
        """
        Check if the expression exp (string or number) is present in chain
        """
        if len(chain) >= len(exp):
            for i in range(len(chain)-len(exp)+1):
                if chain[i:i+len(exp)] == exp:
                    return True
        return False

    def displayDataPlot(self):
        self.clear()
        gs = gridspec.GridSpec(1,34)
        self.fig1.subplots_adjust(left = 0.1, right=0.96, wspace = 0.5)
        self.ax1f1=self.fig1.add_subplot(gs[0,0:31])
        self.ax1f1.tick_params('both', which='both', direction='out')
        self.ax1f1.ticklabel_format(scilimits = (-2,3))
        self.ax1f1.ticklabel_format(useMathText=True)
        self.ax1f1.tick_params(axis='x', labelsize='large')
        self.ax1f1.tick_params(axis='y', labelsize='large')
        if self.twoDims:
            self.reshape2Ddata()  #Reshape the data if it contains 2D array
            zIndex = int(self.set_display_2.currentIndex())
            self.dataToDisplay = self.data[zIndex]
            self.c = self.ax1f1.imshow(self.dataToDisplay.T, origin="lower", aspect='auto', cmap='RdBu_r')
            # self.c = self.ax1f1.imshow(self.dataToDisplay.T, origin="lower", aspect='auto', cmap='RdBu_r')
            ################################################
            #Color bar
            fmt = ticker.ScalarFormatter(useMathText=True)
            fmt.set_powerlimits((0, 0))
            self.bar = self.fig1.colorbar(self.c, ax=self.ax1f1, format = fmt)
            self.bar.ax.yaxis.set_offset_position('left')
            self.bar.update_ticks()
            self.bar.draw_all()

            #####################################################
            #Initializing sliders
            self.plotSliderMin = self.fig1.add_subplot(gs[0,32])
            self.plotSliderMax = self.fig1.add_subplot(gs[0,33])
            self.sliderMin = SliderVert.VertSlider(self.plotSliderMin, 'Min', 0, 1, valinit=0)
            self.sliderMax = SliderVert.VertSlider(self.plotSliderMax, 'Max', 0, 1, valinit=1)
            self.sliderMin.on_changed(self.updateSliderMin)
            self.sliderMax.on_changed(self.updateSliderMax)
            
            self.nb_click = 0
            self.nb_sim = 0 #Temporaire

        else:
            xIndex = self.cb_src1.currentIndex()
            yIndex = self.cb_src2.currentIndex()
            self.datCurve = lines.Line2D(self.data[xIndex], self.data[yIndex])
            self.ax1f1.add_artist(self.datCurve)
            self.ax1f1.grid()
        
        ##########################################################
        #Initializinf resizable line
        y1 = self.ax1f1.get_ylim()[0]
        y2 = self.ax1f1.get_ylim()[1]
        x1 = self.ax1f1.get_xlim()[0]
        x2 = self.ax1f1.get_xlim()[1]
        self.resLine = Cursors.Resizable_line(self.ax1f1, self.lab_resLine, self.check_resLine,x1, y1, x2, y2)
        
        self.setAxisNames()
        
        ############################################################
        #Initializing cursors
        Dy = abs(self.ax1f1.get_ylim()[0]-self.ax1f1.get_ylim()[1])
        y1 = self.ax1f1.get_ylim()[0]+0.3*Dy
        y2 = self.ax1f1.get_ylim()[1]-0.3*Dy
        self.horCursor = Cursors.HorizontalCursor(self.ax1f1, self.horCurs_val, self.check_horCurs, y1=y1, y2=y2)

        Dx = abs(self.ax1f1.get_xlim()[0]-self.ax1f1.get_xlim()[1])
        x1 = self.ax1f1.get_xlim()[0]+0.3*Dx
        x2 = self.ax1f1.get_xlim()[1]-0.3*Dx
        self.vertCursor = Cursors.VerticalCursor(self.ax1f1, self.verCurs_val, self.check_vertCurs,x1=x1, x2=x2)
        
        #Lines for cross
        self.lineh = self.ax1f1.axhline(visible=False, markersize=5, color='red')
        self.linev = self.ax1f1.axvline(visible=False, markersize=5, color='red')
        self.fig1.canvas.mpl_connect('motion_notify_event', self.show_cross)
        self.setAxisIndexes()
        
    def findExtremum(self, data):
        """
        Find extremum of data and take nan values into account
        First line must contains at least one data that is not nan
        """
        dim = len(np.shape(data))
        inds = []
        for i in range(dim): inds.append(0)
        #Initialize value for max and min at value different from nan
        l = 0
        inds[-1]=l
        if np.isnan(data[tuple(inds)]):
            while np.isnan(data[tuple(inds)]):
                l+=1
                inds[-1] = l
        maxi = data[tuple(inds)]
        mini = data[tuple(inds)]

        #Find max and min
        if len(np.shape(data))==2:
            for i in range(np.size(data,0)):
                for j in range(np.size(data,1)):
                    if not np.isnan(data[i,j]):
                        if data[i,j]<mini: mini = data[i,j]
                        if data[i,j]>maxi: maxi = data[i,j]
        elif len(np.shape(data))==1:
            for i in range(np.size(data)):
                if not np.isnan(data[i]):
                    if data[i]<mini: mini = data[i]
                    if data[i]>maxi: maxi = data[i]
        
        return maxi, mini

    def reshape2Ddata(self):
        """
        Reshape the data array to be in the right form for the programm to plot
        """
        yind=self.ycoord_ind[0]
        cop = self.data.copy()
        if self.data[yind,0,0]>self.data[yind,0,1]:
            print('true2')
            self.data=cop[:,:,::-1]
            cop=self.data.copy()
        if self.data[0,0,0]>self.data[0,1,0]:
            self.data=cop[:,::-1,:]
            cop=self.data.copy()
        self.data[:,1::2,::-1] =cop[:,1::2,:]
        
    def mean_VertCursors(self):
        """
        Calculate mean of data between vertical cursors if one dim data
        """
        if not self.twoDims:
            x = int(self.cb_src1.currentIndex())
            y = int(self.cb_src2.currentIndex())
            dx = abs(self.data[x,0]-self.data[x,1])
            x1, x2 = self.vertCursor.getX()
            indx1 = np.argwhere(abs(self.data[x]-x1)<=dx)[0][0]
            indx2 = np.argwhere(abs(self.data[x]-x2)<=dx)[0][0]
            return np.mean(self.data[y, min((indx1,indx2)):max((indx1,indx2))])
            
    def updateSliderMin(self, value):
        min_update = (self.max_data-self.min_data)*value+self.min_data
        if min_update < self.bar.vmax:
            self.bar.set_clim(min_update, self.bar.vmax)
            self.bar.draw_all()
            self.canvas.draw()

    def updateSliderMax(self, value):
        max_update = (self.max_data-self.min_data)*value+self.min_data
        if max_update > self.bar.vmin:
            self.bar.set_clim(self.bar.vmin, max_update)
            self.bar.draw_all()
            self.canvas.draw()

    def setAxisNames(self):
        #names x and y and min and max for each axis
        xName = str(self.cb_src1.currentText())
        yName = str(self.cb_src2.currentText())
        self.ax1f1.set_xlabel(xName,fontsize='x-large')
        self.ax1f1.set_ylabel(yName,fontsize='x-large')
        self.setAxisIndexes()
        self.UpdateData()
    
    def setAxisIndexes(self):
        xIndex = self.cb_src1.currentIndex()
        yIndex = self.cb_src2.currentIndex()
        #update min and max
        xVariable = np.unique(self.data[xIndex])
        yVariable = np.unique(self.data[yIndex])
        
        self.xmax=xVariable.max()
        self.xmin=xVariable.min()
        self.ymax = yVariable.max()
        self.ymin = yVariable.min()
        #find min and max
        if np.isnan(self.xmin): 
            self.xmax, self.xmin = self.findExtremum(xVariable)
            self.xmax= self.xmin+(self.data[xIndex][1,0]-self.data[xIndex][0,0])*len(self.data[xIndex][:,0])
            if np.isnan(self.xmax):
                self.xmax, self.xmin = self.findExtremum(xVariable)
                self.xmin= self.xmax-(self.data[xIndex][-1,0]-self.data[xIndex][-2,0])*len(self.data[xIndex][:,0])
            # print(self.xmin)
            # print(self.xmax)
        if np.isnan(self.ymin):
            self.ymax, self.ymin = self.findExtremum(yVariable)
        
        #If 2D table, set min and max of axis
        if self.twoDims:
            if self.xmin!=self.xmax and self.ymin!=self.ymax: self.c.set_extent([self.xmin,self.xmax,self.ymin,self.ymax])
            if self.xmin==self.xmax and self.ymin!=self.ymax: self.c.set_extent([0,np.size(self.data[xIndex,:,0]),self.ymin,self.ymax]) #for 1d repeated data ty pically
            if self.xmin!=self.xmax and self.ymin==self.ymax: self.c.set_extent([self.xmin,self.xmax,0,np.size(self.data[xIndex,0,:])])
        else:
            if self.xmin!=self.xmax: self.ax1f1.set_xlim(self.xmin-self.xmax*0.05, self.xmax*1+0.05)
            else: print 'Change absciss'
        
        self.canvas.draw()
        
# =============================================================================
#         if self.xmin==self.xmax:
#             self.c.set_extent([0,self.data[0].size/yVariable.size,self.ymin,self.ymax])
#             #self.ax1f1.set_xticklabels([xmin,xmin,xmin,xmin,xmin,xmin,xmin,xmin])
#         elif self.ymin == self.ymax:
#             self.c.set_extent([self.xmin,self.xmax,0,self.data[0].size/xVariable.size])
#             #self.ax1f1.set_yticklabels([ymin,ymin,ymin,ymin,ymin,ymin,ymin,ymin])
# =============================================================================
    
# =============================================================================
#         #No auto extant for 1D data
#         v = np.where(xVariable != xVariable[0,0])
#         if v[0].size == 0 and v[1].size == 0:
#             """
#             Axis indexes for 1D datas
#             """
#             s = str(xmin)
#             self.ax1f1.set_xticklabels([s,s,s,s,s,s,s,s,s])
# 
#             nb_yticks = 8
#             yticks = np.linspace(0, np.size(yVariable, 1), nb_yticks)
#             yaxis_dy = (ymax-ymin)/(nb_yticks-1)
#             yticks_label = ["{:.2e}".format(ymin)]
#             for i in range(1,nb_yticks):
#                 yticks_label += ["{:.2e}".format(ymin+i*yaxis_dy)]
#             self.ax1f1.set_yticks(yticks)
#             self.ax1f1.set_yticklabels(yticks_label)
# 
#         else:
#             self.c.set_extent([xmin,xmax,ymin,ymax])
# =============================================================================
    
    def inverseAxis(self,state):
        y = int(self.cb_src1.currentIndex())
        x = int(self.cb_src2.currentIndex())  
        self.cb_src1.setCurrentIndex(x)
        self.cb_src2.setCurrentIndex(y)    
        #self.UpdateData()
        self.setAxisNames()
        self.canvas.draw()
    
    def Data(self, inverseDeriv):
        text_plot = str(self.plot_status_display.currentText())
        xIndex = int(self.cb_src1.currentIndex())
        yIndex = int(self.cb_src2.currentIndex())
        datx=np.unique(self.data[xIndex])
        daty=np.unique(self.data[yIndex])
        
        if self.twoDims:
            zIndex = int(self.set_display_2.currentIndex())
            data = self.data[zIndex]
        else: data = self.data[yIndex]
        
        if text_plot == "Unchanged":
            self.cb_sigma.setEnabled(False)
            self.dataToDisplay = data
        
        elif text_plot == "Log (base 10)":
            self.cb_sigma.setEnabled(False)
            data_temp = np.abs(data)
            data_temp = np.where(data_temp == 0, np.nan, data_temp)
            self.dataToDisplay = np.log10(data_temp)
        
        ######################################################
        #Just for 2d data
        elif text_plot == "df/dx" and self.twoDims:
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            if inverseDeriv:
                self.dataToDisplay= self.Dfilter(datx, data, plot_sigma,axis=1)#derivative for x
            else:
                self.dataToDisplay= self.Dfilter(datx, data, plot_sigma,axis=0)#derivative for x

        elif text_plot == "df/dy":
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            if inverseDeriv:
                self.dataToDisplay=self.Dfilter(daty, data, plot_sigma,axis=0)
            else:
                self.dataToDisplay=self.Dfilter(daty, data, plot_sigma,axis=1)
        
        elif text_plot == "2D smoothing":
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            self.dataToDisplay = filters.gaussian_filter(data, plot_sigma, order = 0, mode = 'reflect')
        
        elif text_plot == "x smoothing":
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            try:
                self.dataToDisplay = filters.gaussian_filter1d(data, plot_sigma, axis=0, order = 0, mode = 'reflect')
            except: raise Exception("Error: sigma = 0")
            
        elif text_plot == "y smoothing":
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            try:
                self.dataToDisplay = filters.gaussian_filter1d(data, plot_sigma, axis=1, order = 0, mode = 'reflect')
            except: raise Exception("Error: sigma = 0")
            
        elif text_plot == "Butterworth filter":
            self.cb_sigma.setEnabled(False)
            data_nf = data
            n = int(self.ord_filt.value())
            D0 = float(self.cut_freq.value())
            if D0 != 0:
                w = np.floor(np.size(data_nf[0,:]))
                h = np.floor(np.size(data_nf[:,0]))
                B = np.sqrt(2) - 1
                x, y=np.meshgrid(np.arange(-w/2,w/2), np.arange(-h/2,h/2))
                D = np.sqrt(x**2 + y**2)
                butter = 1/(1 + B*((D/D0)**(2*n)))
            
                TF_data_nf = np.fft.fftshift(np.fft.fft2(np.double(data_nf)))
                TF_data = np.fft.ifftshift(TF_data_nf * butter)
                self.dataToDisplay = np.real(np.fft.ifft2(TF_data))
            else:
                print 'Error: Cut Frequency must be greater than 0'
 
        elif text_plot == "Tchebychev filter":
            self.cb_sigma.setEnabled(False)
            data_nf = data
            n = int(self.ord_filt.value())
            D0 = float(self.cut_freq.value())
            if D0 != 0:
                eps = 1
                w = np.floor(np.size(data_nf[0,:]))
                h = np.floor(np.size(data_nf[:,0]))
                a = np.zeros(n+1)
                a[n] = 1
                T = np.polynomial.chebyshev.Chebyshev(a)
                x, y=np.meshgrid(np.arange(-w/2,w/2), np.arange(-h/2,h/2))
                D = np.sqrt(x**2 + y**2)
                butter = 1/np.sqrt(1 + (eps*T(D/D0))**2)
            
                TF_data_nf = np.fft.fftshift(np.fft.fft2(np.double(data_nf)))
                TF_data = np.fft.ifftshift(TF_data_nf * butter)
                self.dataToDisplay = np.real(np.fft.ifft2(TF_data))
            else:
                print 'Error: Cut Frequency must be greater than 0'
                
        elif text_plot == "Gradient magnitude" and self.twoDims:
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            self.dataToDisplay = filters.gaussian_gradient_magnitude(data, plot_sigma, mode = 'reflect')
        
        ##############################################
        #Just for 1d data
        elif text_plot == "data smoothing":
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            try:
                self.dataToDisplay = filters.gaussian_filter1d(data, plot_sigma, axis=0, order = 0, mode = 'reflect')
            except: raise Exception("Error: sigma = 0 or data not appropriated")
            
        elif text_plot == "df/dx" and not self.twoDims:
            self.cb_sigma.setEnabled(True)
            plot_sigma = self.cb_sigma.value()
            try:
                self.dataToDisplay= self.Dfilter(datx, data, plot_sigma, axis=0)
            except: raise Exception("Error: sigma = 0")
            
        #Use findExtremum only when nan values are present in order to be faster
        if np.isnan(self.dataToDisplay.min()):
            self.max_data, self.min_data = self.findExtremum(self.dataToDisplay)
        else:
            self.max_data=self.dataToDisplay.max()
            self.min_data=self.dataToDisplay.min()
            
    
    def UpdateData(self):
        xIndex = [self.cb_src1.currentIndex()]
        yIndex = [self.cb_src2.currentIndex()]
        
        if self.twoDims:
            if self.chainExp(self.xcoord_ind, xIndex) and self.chainExp(self.ycoord_ind, yIndex):
                self.Data(False)
                self.c.set_data(self.dataToDisplay.T)
            elif self.chainExp(self.xcoord_ind, yIndex) and self.chainExp(self.ycoord_ind, xIndex):
                self.Data(True)
                self.c.set_data(self.dataToDisplay)
            else:
                self.Data(False)
                self.c.set_data(np.zeros_like(self.dataToDisplay))
            mn = self.min_data+(self.max_data-self.min_data)*self.sliderMin.val
            mx = self.min_data+(self.max_data-self.min_data)*self.sliderMax.val
            self.bar.set_clim(mn, mx)
            self.bar.draw_all()
        
        else:
            self.Data(False)
            self.datCurve.set_data(self.data[xIndex,:], self.dataToDisplay)
            self.ax1f1.set_ylim(self.min_data-abs(self.max_data)*0.05, self.max_data+abs(self.max_data)*0.05)
        
        Dy = abs(self.ax1f1.get_ylim()[0]-self.ax1f1.get_ylim()[1])
        Dx = abs(self.ax1f1.get_xlim()[0]-self.ax1f1.get_xlim()[1])
        y1 = self.ax1f1.get_ylim()[0]+0.3*Dy
        y2 = self.ax1f1.get_ylim()[1]-0.3*Dy
        x1 = self.ax1f1.get_xlim()[0]+0.3*Dx
        x2 = self.ax1f1.get_xlim()[1]-0.3*Dx
        self.resLine.setData([x1,x2], [y1,y2])
            
        self.canvas.draw()
     
    def addmpl(self, fig):
        '''
        Add matplot navigationTool bar and canvas to the figure
        '''
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,self.mplwindow, coordinates =True)
        self.mplvl.addWidget(self.toolbar)
        
        #handle key press
        self.key_press_handler_id = self.canvas.mpl_connect('key_press_event', self.key_press)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
    
    def key_press(self,event):
        key_press_handler(event, self.canvas, self.toolbar)
    
    #Derivative function
    def Dfilter(self, x, y, sigma, axis=-1, mode='reflect', cval=0.):
        """ gaussian filter of size sigma and order 1
          Data should be equally space for filter to make sense
          (sigma in units of dx)
          can use mode= 'nearest'. 'wrap', 'reflect', 'constant'
          cval is for 'constant'
        """
        dx = x[1]-x[0]
        try:
            yf = filters.gaussian_filter1d(y, sigma, axis=axis, mode=mode, cval=cval, order=1)
        except: raise Exception("Error: sigma must be greater than 0")

        return yf/dx
    
    def onclick(self, event):
        """
        this is an event to allow clicking on some point on the graph and obtaining somes slices on x and y of the 2D plot
        """
        
        x = int(self.cb_src1.currentIndex())
        y = int(self.cb_src2.currentIndex())
        
        #Trace graph only if left click into the axis and data in the right way and cursors (and resizable line) not visible
        if event.inaxes is self.ax1f1 and event.button == 1 \
        and not self.vertCursor.visible and not self.horCursor.visible \
        and not self.resLine.visible and self.fig1.canvas.toolbar._active is None \
        and self.chainExp(self.xcoord_ind, [x]):
            self.nb_click += 1
            
            #x and y position of the click
            self.xclick = event.xdata
            self.yclick = event.ydata

            indx = int(round(event.xdata))
            indy = int(round(event.ydata))
            if self.xmax!=self.xmin:
                for i in range(np.size(self.data[x],0)-1):
                    if self.data[x][i,0]<=self.xclick and self.data[x][i+1,0]>=self.xclick:
                        if np.abs(self.data[x][i,0]-self.xclick) < np.abs(self.data[x][i+1,0]-self.xclick):
                            indx = i
                        else:
                            indx = i+1
                            break
                coordx=self.data[x][indx,0]
            else: coordx=indx #for repeated line scan typically
            
            if self.ymax!=self.ymin:
                for i in range(np.size(self.data[y],1)-1):
                    if self.data[y][0,i]<=self.yclick and self.data[y][0,i+1]>=self.yclick:
                        if np.abs(self.data[y][0,i]-self.yclick) < np.abs(self.data[y][0,i+1]-self.yclick):
                            indy = i
                        else:
                            indy = i+1
                            break
                coordy=self.data[y][0,indy]
            else: coordy=indy #for repeated line scan typically
                
            coord = [coordx, coordy]
            yHor = np.array([self.dataToDisplay.T[indy,:]]).T
            yVert = np.array([self.dataToDisplay.T[:,indx]]).T

            if self.nb_click == 1:
                if self.xmin!=self.xmax: xHor = self.data[x][:,0]
                else: xHor=np.arange(0, self.data[0].size/np.unique(self.data[y]).size)
                if self.ymin!=self.ymax: xVert = self.data[y][0,:]
                else: xVert = np.arange(0, self.data[0].size/np.unique(self.data[x]).size)
                    
                self.profils = Trace_profils.Profils(self.ax1f1, xHor, xVert)
                self.profils.show()
            self.profils.addDataArray(coord, yHor, yVert, [indy, indx])
            
            #Force axis limit, otherwise, they are changed
            self.setAxisIndexes() 
            
            if not self.chainExp(self.xcoord_ind, [x]): print('No trace allowed in that configuration, inverse the axis')

    def show_cross(self, event):
        """
        Create a cross line at the position of the mouse if the cursors are not visible
        """
        if event.inaxes is self.ax1f1 and not self.horCursor.visible \
        and not self.vertCursor.visible and not self.resLine.visible:
            self.lineh.set_visible(False)
            self.linev.set_visible(False)
            self.lineh.set_ydata(event.ydata)
            self.linev.set_xdata(event.xdata)
            self.lineh.set_visible(True)
            self.linev.set_visible(True)
            #self.canvas.draw()
        else:
            self.lineh.set_visible(False)
            self.linev.set_visible(False)
            #self.canvas.draw()

if __name__ == "__main__":
    config_excepthook()
    import start_qt_app
    qApp = start_qt_app.prepare_qt()
    shell_interactive = start_qt_app._interactive

    myapp = MyMainWindow()
    myapp.desktop = qApp.desktop() # gives access to screen sizes
    
    # this is to keep multiple myapp alive by keeping a ref to it
    # this is needed for %run -i and execfile invocations,
    #  %run does not need it (it keeps the exec environment in
    #  in the array __IP.shell._user_main_modules
    if 'awarr' not in vars(): awarr=[]
    awarr.append(myapp)

    myapp.show()
    
    start_qt_app.start_qt_loop_if_needed(redirect_stderr=True)