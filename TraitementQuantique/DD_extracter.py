# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 10:31:31 2020

@author: devj2901
"""
from scipy.constants import e
import numpy as np
import Poly_interaction
from Poly_interaction import PolygonInteractor as triangle
#import matplotlib.pyplot as plt
import matplotlib.lines as lines
from matplotlib.figure import Figure
from matplotlib import ticker
from matplotlib.patches import Polygon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

#import sliderVert as SliderVert
import set

from PyQt5 import uic
#from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
#formclass, baseclass = uic.loadUiType('SimulationWindows\simulation_window.ui')
formclass, baseclass = uic.loadUiType('SimulationWindows\DD_simulation_window.ui')


class DDExtracter(baseclass, formclass):
    def __init__(self):
        baseclass.__init__(self)
        self.setupUi(self)

        #######################################################################
        #Sim part

        #Create a simulation window and add the central widget to the tab
        #We will create a list of the different simulation window correponding to the widget in the tab
        #this way, we can still access the property of the simulation window (we could not do that with the central widget only)
        #Remove the firts empty tab
        
        ############################
        #Create figure and axes for experimental datas
        self.figExp = Figure()
        self.addmpl(self.figExp)
        self.axExp=self.figExp.add_subplot(111)
        self.axExp.ticklabel_format(scilimits = (-2,2))
        self.axExp.ticklabel_format(useMathText=True)
        self.axExp.set_xlabel('$V_{G1}$'+' (V)', fontsize=12)
        self.axExp.set_ylabel('$V_{G2}$'+' (V)', fontsize=12)

        # self.figExp.canvas.mpl_connect('motion_notify_event', self.mouse_coord_exp)
        # self.figExp.canvas.mpl_connect('button_press_event', self.press_click)
        # self.figExp.canvas.mpl_connect('button_release_event', self.realease_click)
        # self.clicked = False

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
        self.check_fit.stateChanged.connect(self.fit_triangles)
        self.run_btn.clicked.connect(self.run_calculation)

        self.fit_triangle_1 = Polygon(np.column_stack([[1,1,1.5], [0,1,0]]), animated=True)
        self.axExp.add_patch(self.fit_triangle_1)


        self.triangle_1_interactor = triangle(self.axExp, self.fit_triangle_1)


        self.axExp.add_artist(self.fit_triangle_1)

        self.fit_triangle_1.set_visible(False)


        #Variables to know if there was a click near a line extremity
        #Each element of the lists correspond to the extremity of one line
        #True if click next to an extremity, false if not

        self.alpha_1 = 0.0
        self.alpha_2 =0.0
        self.Ec1=0.0
        self.Ec2=0.0
        self.Ecm=0.0
        self.Vg1=0.0
        self.Vg2 =0.0
        self.Vgm1 =0.0
        self.Vgm2=0.0
        self.Cm=0.0
        self.Vds=0.0
        

        self.xmin = 0
        self.xmax = 1
        self.ymin = 0
        self.ymax = 1
        #Size of the square centered on the fitline extreimities, if click inside, it is possible to move them
        self.dx = (self.xmax-self.xmin)/100
        self.dy = (self.ymax-self.ymin)/100

    def setData(self, data, xmin, xmax, ymin, ymax):


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

        self.fit_triangle_1.set_xy(np.column_stack([[xmin+self.dx*10, xmin+self.dx*30, xmin+self.dx*60],[ymin+self.dx*10, ymin+self.dy*30, ymin+self.dx*10]]))

        self.canvas.draw()

    def addmpl(self, fig):
        """
        Add canvas and toolbar to the experimental figure
        """
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)

        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,self.mplExp, coordinates =True)
        self.mplvl.addWidget(self.toolbar)

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

    def run_calculation(self):
        """
        Perform the calculation
        """
        #first  acquire data from textbox
        self.Vg1=self.Vgx.value()
        self.Vg2=self.Vgy.value()
        self.Vgm1=self.Vgmx.value()
        self.Vgm2=self.Vgmy.value()
        self.Vds=self.Vds_box.value()

        #acquire data from triangle
        deltaVg1 = np.abs(self.fit_triangle_1.get_xy()[0,0]-self.fit_triangle_1.get_xy()[2,0])*1e3
        deltaVg2 = np.abs(self.fit_triangle_1.get_xy()[0,1]-self.fit_triangle_1.get_xy()[1,1])*1e3

        #make calculation
        self.alpha_1 = self.Vds/deltaVg1
        self.alpha_2 = self.Vds/deltaVg2
        Cg1=np.abs(e)/self.Vg1
        Cg2=np.abs(e)/self.Vg2
        C1=Cg1/self.alpha_1
        C2=Cg2/self.alpha_2


        self.Cm = (self.Vgm1*Cg2)/(self.alpha_2*self.Vg1)
        self.Ecm=e/self.Cm * (1/(C1*C2/self.Cm**2-1))
        self.Ec1 = self.alpha_1*e/Cg1 * (1/(1-self.Cm**2/(Cg1*Cg2/(self.alpha_1*self.alpha_2))))
        self.Ec2 = self.alpha_2*e/Cg2 * (1/(1-self.Cm**2/(Cg1*Cg2/(self.alpha_1*self.alpha_2))))

        #update value
        print(self.Ec1)
        self.Ec1_display.setValue(self.Ec1)
        self.Ec2_display.setValue(self.Ec2)
        self.Ecm_display.setValue(self.Ecm)

        try:
            s = 'α1'+' = {a:.3f}'.format(a=self.alpha_1)
            self.lever_arm_1.setText(s)
            s = 'α2'+' = {a:.3f}'.format(a=self.alpha_2)
            self.lever_arm_2.setText(s)
            
        except:
            self.lever_arm_1.setText(str(a)+' = ')
            self.lever_arm_2.setText(str(a)+' = ')

    def fit_triangles(self):
    #function when you clic the fit triangle button. Make the triangle appear
        if self.check_fit.checkState() == Qt.Checked:
            self.fit_triangle_1.set_visible(True)
        else:
            self.fit_triangle_1.set_visible(False)
        self.canvas.draw()


if __name__ == "__main__":
    import start_qt_app
    qApp = start_qt_app.prepare_qt()
    shell_interactive = start_qt_app._interactive
    simu = DDExtracter()
    simu.desktop = qApp.desktop()
    f = 'C:\\Users\\devj2901\\Documents\\Recherche\\SimuBQ\\projects\\FichierClaude\\SET_VDS.dat'
    simu.setData(np.loadtxt(f), xmin = 3.75, xmax = 3.95, ymin = -0.002, ymax = 0.002)
    simu.show()