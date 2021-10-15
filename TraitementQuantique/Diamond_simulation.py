# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 10:31:31 2020

@author: devj2901
"""
from scipy.constants import e
import numpy as np

#import matplotlib.pyplot as plt
import matplotlib.lines as lines
from matplotlib.figure import Figure
from matplotlib import ticker
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

#import sliderVert as SliderVert
import set

from PyQt5 import uic
#from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt

formclass_simpart, baseclass_simpart = uic.loadUiType('SimulationWindows\wind_simPart.ui')
#formclass, baseclass = uic.loadUiType('SimulationWindows\simulation_window.ui')
formclass, baseclass = uic.loadUiType('SimulationWindows\simulation_window.ui')


class Simulation_widget(baseclass_simpart, formclass_simpart):
    def __init__(self):
        baseclass_simpart.__init__(self)
        self.setupUi(self)
        
        self.figSim = Figure()
        self.addmpl(self.figSim)
        self.axSim=self.figSim.add_subplot(111)
        self.axSim.set_xlabel('$V_{G}$'+' (mV)', fontsize=12)
        self.axSim.set_ylabel('$V_{DS}$'+' (mV)', fontsize=12)
        
        self.imSim = self.axSim.imshow(np.array([[np.nan]]), origin="lower", aspect='auto', cmap='RdBu_r')
        self.imSim.set_extent([0, 1, 0, 1])

        #Colorbar
        fmt = ticker.ScalarFormatter(useMathText=True)
        fmt.set_powerlimits((0, 0))
        self.barSim = self.figSim.colorbar(self.imSim, ax=self.axSim, format = fmt)
        self.barSim.ax.yaxis.set_offset_position('left')
        self.barSim.draw_all()

        #Associate button to function
        self.run_button.clicked.connect(self.run_Simulation)
        self.runned = False
        
        #Associate checkbox for dot to functions
        self.check_MD.stateChanged.connect(self.enable_MD)
        self.check_QD.stateChanged.connect(self.enable_QD)
        
        #Change Cs, Cd and Cs when spinbox values are changed
        self.Cg_sim.valueChanged.connect(self.set_Cg_sim)
        self.Cd_sim.valueChanged.connect(self.set_Cd_sim)
        self.Cs_sim.valueChanged.connect(self.set_Cs_sim)

        
        #Physical parameters
        self.Cs = None
        self.Cd = None
        self.Cg = None
        self.Gs = None
        self.Gd = None
        self.T = None
    
    def addmpl(self, fig):
        """
        Add canvas and toolbar to the experimental figure
        """
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,self.mpl, coordinates =True)
        self.mplvl.addWidget(self.toolbar)
        
    def derive(self, F, X):
        return np.diff(F)/abs(X[1]-X[0]), np.linspace(X[0], X[-1], len(X)-1)
    
    def plotSim(self, Vgmin, Vgmax, Vdmin, Vdmax, data, mode='Diff conductance'):
        """
        All potentials in mvolt
        """
        #Convert xmin and xmax in mV, y stays in V
        self.imSim.set_data(data)
        self.imSim.set_extent([Vgmin, Vgmax, Vdmin, Vdmax])
        self.barSim.set_clim([data.min(), data.max()])
        if mode == 'Diff conductance': 
            self.barSim.set_label('$G (\mu S)$', fontsize = 12)
        elif mode == 'Current':
            self.barSim.set_label('$I_{DS} (A)$', fontsize = 12)
        self.barSim.draw_all()
        self.canvas.draw()
    
    def setCapacitance(self, Cg, Cd, Cs):
        """
        Capacitance in aF
        """
        self.Cs_sim.setValue(Cs)
        self.Cd_sim.setValue(Cd)
        self.Cg_sim.setValue(Cg)
        
        self.Cg = Cg
        self.Cd = Cd
        self.Cs = Cs
        
    def set_Cg_sim(self, event):
        self.Cg = self.Cg_sim.value()
    def set_Cd_sim(self, event):
        self.Cd = self.Cd_sim.value()
    def set_Cs_sim(self, event):
        self.Cs = self.Cs_sim.value()
    
    def enable_MD(self):
        if self.check_MD.isChecked():
            self.spin_E_offset.setEnabled(True)
            self.spin_nb_e.setEnabled(True)
            self.check_ag.setEnabled(True)
            self.check_QD.setChecked(False)
        else:
            self.spin_E_offset.setEnabled(False)
            self.spin_nb_e.setEnabled(False)
            self.check_ag.setEnabled(False)
        
    def enable_QD(self):
        if self.check_QD.isChecked():
            self.line_levels.setEnabled(True)
            self.line_degeneracy.setEnabled(True)
            self.check_MD.setChecked(False)
        else:
            self.line_levels.setEnabled(False)
            self.line_degeneracy.setEnabled(False)
            
    def run_Simulation(self):
        """
        Cg, Cs, Cd in aF
        Gs, Gd in us
        T in K
        Vds, Vg in mV
        """

        self.Gs=self.Gs_sim.value()
        self.Gd=self.Gd_sim.value()
        self.T=self.T_sim.value()
        Vg_start = self.spin_Vg_start.value()
        Vg_end = self.spin_Vg_end.value()
        Vds_start = self.spin_Vds_start.value()
        Vds_end = self.spin_Vds_end.value()
        nb_Vg = self.spin_Vg_Pts.value()
        nb_Vds = self.spin_Vds_Pts.value()
        mode = self.box_mode.currentText()
        
        #Define the set
        myset = set.SET()
        # Quantum dots or mettallic dot
        if self.check_MD.isChecked():
            """
            If check_ag is checked, divide offset energy by lever arm
            Value divided by the lever arm is the offset observed on the absciss of stability diagramm 
            """
            if self.check_ag.isChecked():
                ag = self.Cg/(self.Cg+self.Cd+self.Cs)
                energy_offset = self.spin_E_offset.value()*ag
            else:
                energy_offset = self.spin_E_offset.value()
            myset.add_metallic_dot('dot', self.spin_nb_e.value(), 0, energy_offset)
        
        elif self.check_QD.isChecked():
            #If levels and degeneracy are not put, a message is displayed in the command
            if len(self.line_levels.text())!=0 and len(self.line_degeneracy.text())!=0:
                global levels
                global degeneracy
                l = self.line_levels.text()[0::2]
                d = self.line_degeneracy.text()[0::2]
                levels = []
                degeneracy = []
                for i in l: levels.append(float(i))
                for i in d: degeneracy.append(int(i))
            try:
                myset.add_quantum_dot('dot', levels, degeneracy)
            except: print 'Select levels and degeneracy'
         
        #Add components to the dot to form the structure
        myset.add_lead('source')
        myset.add_lead('drain')
        myset.add_gate('gate')
        myset.add_link('dl', 'dot', 'drain', self.Cd*1e-18, self.Gd*2/77.461)
        myset.add_link('dl', 'dot', 'source', self.Cs*1e-18, self.Gs*2/77.461)
        myset.add_link('dg', 'dot', 'gate', self.Cg*1e-18)
        myset.set_temperature(self.T)

        myset.pre_processing()

        #Calculate current for each volatge couple
        Vg = np.linspace(Vg_start, Vg_end, nb_Vg)
        Vd = np.linspace(Vds_start, Vds_end, nb_Vds)
        data_matrix = []
        for (i_vg, vg) in enumerate(Vg):
            I = []
            P = []
            V_dot = []
            for vd in Vd:
                myset.tunnel_rate([0, vd, vg])
                myset.solver() 
                I.append(myset.current('drain','dot'))
                #I.append(myset.current('source','dot'))
                P.append(myset.proba('dot'))
                #V_dot.append(myset.voltage('dot'))
            # convert lists to scipy arrays
            I = np.array(I)
            P = np.array(P)
            V_dot = np.array(V_dot)
            # compute the diffential conductance
            if mode == 'Current':
                Y = Vd
                F = I
            elif mode == 'Diff conductance':
                F, Y = self.derive(I, Vd)
                F *= 1e3
            data_matrix.append(F)
        data_matrix = np.array(data_matrix)
        self.data = np.transpose(data_matrix)
        self.plotSim(Vg.min(), Vg.max(), Y.min(), Y.max(), self.data, mode = mode)    
        
        self.runned = True


class DiamondSimulation(baseclass, formclass):
    def __init__(self):
        baseclass.__init__(self)
        self.setupUi(self)

        #######################################################################
        #Sim part

        #Create a simulation window and add the central widget to the tab
        #We will create a list of the different simulation window correponding to the widget in the tab
        #this way, we can still access the property of the simulation window (we could not do that with the central widget only)
        #Remove the firts empty tab
        self.sim_widg = [Simulation_widget()]
        self.simuTab.addTab(self.sim_widg[0].centralwidget, 'Simu1')
        self.simuTab.removeTab(0)

        #Connect tab to function that allow new ones to open and close       
        self.simuTab.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.simuTab.setTabsClosable(True)
        self.simuTab.tabCloseRequested.connect(self.close_current_tab)
        #######################################################################
        #######################################################################

        self.copy_dataToSim.clicked.connect(self.data_To_Sim)
        self.check_draw_fit.stateChanged.connect(self.draw_fit)

        ############################
        #Create figure and axes for experimental datas
        self.figExp = Figure()
        self.addmpl(self.figExp)
        self.axExp=self.figExp.add_subplot(111)
        self.axExp.ticklabel_format(scilimits = (-2,2))
        self.axExp.ticklabel_format(useMathText=True)
        self.axExp.set_xlabel('$V_{G}$'+' (V)', fontsize=12)
        self.axExp.set_ylabel('$V_{DS}$'+' (mV)', fontsize=12)

        self.figExp.canvas.mpl_connect('motion_notify_event', self.mouse_coord_exp)
        self.figExp.canvas.mpl_connect('button_press_event', self.press_click)
        self.figExp.canvas.mpl_connect('button_release_event', self.realease_click)
        self.clicked = False

        ##########################
        #Draw data
        self.im = self.axExp.imshow(np.array([[np.nan]]), origin="lower", aspect='auto', cmap='RdBu_r')
        self.im.set_extent([0, 1, 0, 1])

        fmt = ticker.ScalarFormatter(useMathText=True)
        fmt.set_powerlimits((0, 0))
        self.bar = self.figExp.colorbar(self.im, ax=self.axExp, format = fmt)
        self.bar.ax.yaxis.set_offset_position('left')
        self.bar.draw_all()

        ###########################
        #Lines for fit
        self.check_Cg.stateChanged.connect(self.fitCg)
        self.check_Cd.stateChanged.connect(self.fitCd)
        self.check_Cs.stateChanged.connect(self.fitCs)

        self.Cg_line = lines.Line2D([0.3, 0.7], [0.5, 0.5], color = 'tab:olive')
        self.Cd_line = lines.Line2D([0.3, 0.6], [0.3, 0.6], color = 'tab:olive')
        self.Cs_line = lines.Line2D([0.8, 0.9], [0.9, 0.8], color = 'tab:olive')

        self.axExp.add_artist(self.Cg_line)
        self.axExp.add_artist(self.Cd_line)
        self.axExp.add_artist(self.Cs_line)

        self.Cg_line.set_visible(False)
        self.Cd_line.set_visible(False)
        self.Cs_line.set_visible(False)

        #Variables to know if there was a click near a line extremity
        #Each element of the lists correspond to the extremity of one line
        #True if click next to an extremity, false if not
        self.Cg_line_ext = [False, False]
        self.Cd_line_ext = [False, False]
        self.Cs_line_ext = [False, False]

        self.Cgval = 0.0
        self.Cbgval = 0.0
        self.Cdval = 0.0
        self.Csval = 0.0
        self.ag_val = 0.0
        self.ad_val = 0.0

        self.xmin = 0
        self.xmax = 1
        self.ymin = 0
        self.ymax = 1
        #Size of the square centered on the fitline extreimities, if click inside, it is possible to move them
        self.dx = (self.xmax-self.xmin)/100
        self.dy = (self.ymax-self.ymin)/100

    def setData(self, data, xmin, xmax, ymin, ymax):
        #Convert xmin and xmax in mV, y stays in V
        ymin*=1e3
        ymax*=1e3

        self.dataExp = data
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.dx = (self.xmax-self.xmin)/100
        self.dy = (self.ymax-self.ymin)/100

        self.im.set_data(data)
        self.im.set_extent([xmin, xmax, ymin, ymax])

        maxi=data.max()
        mini=data.min()
        if np.isnan(mini): maxi, mini = self.findExtremum(data)
        self.bar.set_clim(vmin=mini, vmax=maxi)
        self.bar.draw_all()

        self.Cg_line.set_xdata([xmin+self.dx*30, xmax-self.dx*30])
        self.Cg_line.set_ydata([0, 0])
        self.Cd_line.set_xdata([xmin+self.dx*30, xmax-self.dx*30])
        self.Cd_line.set_ydata([ymax-self.dy*30, ymin+self.dy*30])
        self.Cs_line.set_xdata([xmin+self.dx*30, xmax-self.dx*30])
        self.Cs_line.set_ydata([ymin+self.dy*30, ymax-self.dy*30])

        self.canvas.draw()

    # when double clicked is pressed on tabs 
    def tab_open_doubleclick(self, i):
        """
        Add new simulation window to the list and and add its central widget to the tab
        Go to the last tab created    
        """
        self.sim_widg += [Simulation_widget()]
        self.simuTab.addTab(self.sim_widg[-1].centralwidget, 'Simu'+str(self.simuTab.count()+1))
        self.simuTab.setCurrentIndex(self.simuTab.count()-1)

    #Close table when clicking on close button
    def close_current_tab(self,i):
        if self.simuTab.count() > 1:
            self.simuTab.removeTab(i)
            del self.sim_widg[i]

    def addmpl(self, fig):
        """
        Add canvas and toolbar to the experimental figure
        """
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)

        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,self.mplExp, coordinates =True)
        self.mplvl.addWidget(self.toolbar)

    def data_To_Sim(self):
        """
        Copy experimental parameters to the open simulation tab
        """
        k = self.simuTab.currentIndex()
        self.sim_widg[k].setCapacitance(self.Cgval, self.Cdval, self.Csval)

    def press_click(self, event):
        if event.inaxes is self.axExp and event.button == 1:
            self.clicked = True
            #Check if the click was next to an extremity fitline
            self.extremity_fitlines(event.xdata, event.ydata) 

    def realease_click(self, event):
        if event.inaxes is self.axExp and event.button == 1:
            self.clicked = False

    def mouse_coord_exp(self, event):
        if event.inaxes is self.axExp and self.clicked:
            self.update_fitline(event.xdata, event.ydata)

    def update_fitline(self, x, y):
        """
        Update coordinates of the fitline if ckeckbox is checked
        Update the value of the correspondings checkboxes
        """
        if self.check_Cg.checkState() == Qt.Checked:
            if self.Cg_line_ext[0]:
                self.Cg_line.set_xdata([x, self.Cg_line.get_xdata()[1]])
            elif self.Cg_line_ext[1]:
                self.Cg_line.set_xdata([self.Cg_line.get_xdata()[0],x])

        if self.check_Cd.checkState() == Qt.Checked:
            if self.Cd_line_ext[0]:
                self.Cd_line.set_xdata([x, self.Cd_line.get_xdata()[1]])
                self.Cd_line.set_ydata([y, self.Cd_line.get_ydata()[1]])
            elif self.Cd_line_ext[1]:
                self.Cd_line.set_xdata([self.Cd_line.get_xdata()[0],x])
                self.Cd_line.set_ydata([self.Cd_line.get_ydata()[0],y])

        if self.check_Cs.checkState() == Qt.Checked:
            if self.Cs_line_ext[0]:
                self.Cs_line.set_xdata([x, self.Cs_line.get_xdata()[1]])
                self.Cs_line.set_ydata([y, self.Cs_line.get_ydata()[1]])
            elif self.Cs_line_ext[1]:
                self.Cs_line.set_xdata([self.Cs_line.get_xdata()[0],x])
                self.Cs_line.set_ydata([self.Cs_line.get_ydata()[0],y])

        
        try:
            self.Cgval = e/abs(self.Cg_line.get_xdata()[0]-self.Cg_line.get_xdata()[1])*self.num_diam_Cg.value()*1e18
            self.Cg_fit.setValue(self.Cgval)
            self.Cbgval = abs(self.bg_g_fit.value())*self.Cgval
            s = '{cbg:.3f}'.format(cbg=self.Cbgval)
            self.lab_Cbg.setText(s)
        except: raise Exception('Divison by zero')

        try:
            pente = abs(self.Cd_line.get_ydata()[0]-self.Cd_line.get_ydata()[1])/abs(self.Cd_line.get_xdata()[0]-self.Cd_line.get_xdata()[1])
            if pente != 0:
                self.Cdval = self.Cgval/pente*1e3 # multiply by 1e3 to have correct units
                self.Cd_fit.setValue(self.Cdval)
        except: raise Exception('Divison by zero')

        try:
            pente = abs(self.Cs_line.get_ydata()[0]-self.Cs_line.get_ydata()[1])/abs(self.Cs_line.get_xdata()[0]-self.Cs_line.get_xdata()[1])
            #Multply by 1e-3 to have correct units
            pente*=1e-3 
            if pente != 0:
                self.Csval = self.Cgval*(1/pente-1)-self.Cbgval
                self.Cs_fit.setValue(self.Csval)
        except: raise Exception('Divison by zero')

        self.ag_val=self.update_leverArm(self.lever_arm_g, self.Cgval, 'αg')
        self.ad_val=self.update_leverArm(self.lever_arm_d, self.Cdval, 'αd')

        self.canvas.draw()

    def update_leverArm(self, label, C, a):
        try:
            leverArm = C/(self.Cgval+self.Csval+self.Cdval)
            s = a+' = {a:.3f}'.format(a=leverArm)
            label.setText(s)
            return leverArm
        except:
            label.setText(str(a)+' = ')
            return

    def extremity_fitlines(self, x, y):
        """
        Check if the click is next to the extremity of a fitline
        """
        self.Cg_line_ext[0] = self.ext_fitline(self.Cg_line.get_xdata()[0], self.Cg_line.get_ydata()[0], x, y)
        self.Cg_line_ext[1] = self.ext_fitline(self.Cg_line.get_xdata()[1], self.Cg_line.get_ydata()[1], x, y)

        self.Cd_line_ext[0] = self.ext_fitline(self.Cd_line.get_xdata()[0], self.Cd_line.get_ydata()[0], x, y)
        self.Cd_line_ext[1] = self.ext_fitline(self.Cd_line.get_xdata()[1], self.Cd_line.get_ydata()[1], x, y)

        self.Cs_line_ext[0] = self.ext_fitline(self.Cs_line.get_xdata()[0], self.Cs_line.get_ydata()[0], x, y)
        self.Cs_line_ext[1] = self.ext_fitline(self.Cs_line.get_xdata()[1], self.Cs_line.get_ydata()[1], x, y)

    def ext_fitline(self, xl, yl, x, y):
        """
        Return True if click next to the extremity of a fitline
        """
        if abs(x-xl)<self.dx and abs(y-yl)<self.dy:
            return True
        else:
            return False

    def get_lineEquation(self, cap='Cd'):
        """
        pente en mV/V
        b en mV
        """
        if cap =='Cd':
            pente = (self.Cd_line.get_ydata()[0]-self.Cd_line.get_ydata()[1])/(self.Cd_line.get_xdata()[0]-self.Cd_line.get_xdata()[1])
            b = self.Cd_line.get_ydata()[0]-pente*self.Cd_line.get_xdata()[0]
        elif cap == 'Cs':
            pente = (self.Cs_line.get_ydata()[0]-self.Cs_line.get_ydata()[1])/(self.Cs_line.get_xdata()[0]-self.Cs_line.get_xdata()[1])
            b = self.Cs_line.get_ydata()[0]-pente*self.Cs_line.get_xdata()[0]
        return pente, b
    
    def set_cbar(self, mini=None, maxi=None):
        self.bar.set_clim(vmin=mini, vmax=maxi)
        self.bar.draw_all()
        self.canvas.draw()

    def findExtremum(self, data):
        """
        Find extremum of data and take nan values into account
        First line must contains at least one data that is not nan
        """
        #Initialize value for max and min at value different from nan
        l = 0
        if np.isnan(data[0,l]):
            while np.isnan(data[0,l]):
                l+=1
        maxi = data[0,l]
        mini = data[0,l]
        #Find max and min
        for i in range(np.size(data,0)):
            for j in range(np.size(data,1)):
                if not np.isnan(data[i,j]):
                    if data[i,j]<mini: mini = data[i,j]
                    if data[i,j]>maxi: maxi = data[i,j]
        return maxi, mini   

    def fitCg(self):
        if self.check_Cg.checkState() == Qt.Checked:
            self.Cg_line.set_visible(True)
        else:
            self.Cg_line.set_visible(False)
        self.canvas.draw()

    def fitCd(self):
        if self.check_Cd.checkState() == Qt.Checked:
            self.Cd_line.set_visible(True)
        else:
            self.Cd_line.set_visible(False)
        self.canvas.draw()

    def fitCs(self):
        if self.check_Cs.checkState() == Qt.Checked:
            self.Cs_line.set_visible(True)
        else:
            self.Cs_line.set_visible(False)
        self.canvas.draw()
        
    def draw_fit(self):
        if self.check_draw_fit.checkState() == Qt.Checked:
            DVg = abs(self.Cg_line.get_xdata()[0]-self.Cg_line.get_xdata()[1])/self.num_diam_Cg.value()
            
            #Positive slope
            pente1 = (self.Cs_line.get_ydata()[0]-self.Cs_line.get_ydata()[1])/(self.Cs_line.get_xdata()[0]-self.Cs_line.get_xdata()[1])
            #Negative slope
            pente2 = (self.Cd_line.get_ydata()[0]-self.Cd_line.get_ydata()[1])/(self.Cd_line.get_xdata()[0]-self.Cd_line.get_xdata()[1])
            
            #offset = self.Cg_line.get_xdata()[0]%DVg

            xnode = self.Cg_line.get_xdata()[0]
            self.linesp = []
            self.linesn = []
            while xnode <= self.xmax:
                self.linesp += [self.line(pente1, xnode)]
                self.linesn += [self.line(pente2, xnode)]
                self.axExp.add_artist(self.linesp[-1])
                self.axExp.add_artist(self.linesn[-1])
                xnode += DVg
            
            xnode = self.Cg_line.get_xdata()[0]
            while xnode >= self.xmin:
                self.linesp.insert(0, self.line(pente1, xnode))
                self.linesn.insert(0, self.line(pente2, xnode))
                self.axExp.add_artist(self.linesp[0])
                self.axExp.add_artist(self.linesn[0])
                xnode += -DVg
            self.canvas.draw()
            
        elif self.linesp is not None and self.linesn is not None:
            for i in range(len(self.linesp)):
                self.linesp[i].set_visible(False)
                self.linesn[i].set_visible(False)
            self.canvas.draw()

    def line(self, pente, x, y = 0):
        return lines.Line2D([x-(y-self.ymin)/pente, x+(self.ymax-y)/pente], [self.ymin, self.ymax], lw = 0.3, color = 'black')

if __name__ == "__main__":
    import start_qt_app
    qApp = start_qt_app.prepare_qt()
    shell_interactive = start_qt_app._interactive
    simu = DiamondSimulation()
    simu.desktop = qApp.desktop()
    f = 'C:\\Users\\devj2901\\Documents\\Recherche\\SimuBQ\\projects\\FichierClaude\\SET_VDS.dat'
    simu.setData(np.loadtxt(f), xmin = 3.75, xmax = 3.95, ymin = -0.002, ymax = 0.002)
    simu.show()