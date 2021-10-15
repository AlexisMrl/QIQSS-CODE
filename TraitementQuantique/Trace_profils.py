# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 14:02:48 2020

@author: devj2901
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 11:59:39 2020

@author: devj2901
"""

#import sys
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QCheckBox, QGridLayout, QLabel #, QApplication
from PyQt5.QtCore import Qt
import Cursors
#from PyQt5.QtGui import QPalette, QColor

#import start_qt_app

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=[width, height], dpi=None)
        self.ax1 = fig.add_subplot(121)
        self.ax2 = fig.add_subplot(122)
        super(MplCanvas, self).__init__(fig)

class Profils(QMainWindow):

    def __init__(self, ax_Sd, xHor, xVert, parent = None):
        super(Profils, self).__init__(parent)

        self.setWindowTitle(u"Profil de conductance")

        #Figure and ax of stability diagramm
        self.ax_Sd = ax_Sd

        self.xVert = xVert
        self.xHor = xHor
        self.yHor = self.empty_Array(np.size(self.xHor)-1)
        self.yVert = self.empty_Array(np.size(self.xVert)-1)

        #self.color = ['tab:blue','tab:orange','tab:green','tab:red','tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']
        self.color = ['royalblue','orange','forestgreen','red','darkviolet', 'peru', 'hotpink', 'lightslategray', 'olive', 'darkturquoise']

        #Cross when click stability diagramm
        self.cross = []

        #Create list of checkboxes
        self.check = []

        #Création de la fentre graphique
        self.sc = MplCanvas(self, width=15, height=10, dpi=100)

        ###########################################################
        #Label for cursors
        self.vertCurs_val_H = QLabel()
        self.horCurs_val_H = QLabel()
        self.vertCurs_val_V = QLabel()
        self.horCurs_val_V = QLabel()

        #Checkboxes for cursors
        self.check_vertCurs_H = QCheckBox('Vertical cursors') #horizontal slice
        self.check_horCurs_H = QCheckBox('Horizontal cursors')
        self.check_vertCurs_V = QCheckBox('Vertical cursors') #vertical slice
        self.check_horCurs_V = QCheckBox('Horizontal cursors')
        
        #Create the cursors
        Dx = xHor.max()-xHor.min()
        self.vertCursorH = Cursors.VerticalCursor(self.sc.ax1, self.vertCurs_val_H, self.check_vertCurs_H, xHor.min()+0.3*Dx, xHor.max()-0.3*Dx)
        Dx = xVert.max()-xVert.min()        
        self.vertCursorV = Cursors.VerticalCursor(self.sc.ax2, self.vertCurs_val_V, self.check_vertCurs_V, xVert.min()+0.3*Dx, xVert.max()-0.3*Dx)


        #Add elements for cursors
        self.layout3 = QGridLayout()
        #Horizontal slice
        self.layout3.addWidget(QLabel('Horizontal Slice'),0,0)
        self.layout3.addWidget(self.check_vertCurs_H,1,0)
        self.layout3.addWidget(self.check_horCurs_H,2,0)
        self.layout3.addWidget(self.vertCurs_val_H,1,1)
        self.layout3.addWidget(self.vertCurs_val_H,2,1)

        #Vertical slice
        self.layout3.addWidget(QLabel('Vertical Slice'),0,2)
        self.layout3.addWidget(self.check_vertCurs_V,1,2)
        self.layout3.addWidget(self.check_horCurs_V,2,2)
        self.layout3.addWidget(self.vertCurs_val_V,1,3)
        self.layout3.addWidget(self.vertCurs_val_V,2,3)
        #######################################################################

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.sc, self)

        #Layout
        self.layout1 = QGridLayout()
        self.layout2 = QVBoxLayout()

        #Add widget to layout
        self.layout1.addWidget(toolbar,2,0)
        self.layout1.addWidget(self.sc,1,0)
        self.layout1.addLayout(self.layout2,0,1,3,1)
        #self.layout1.addLayout(self.layout2,0,1,2,1)
        self.layout1.addLayout(self.layout3,0,0)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QWidget()
        widget.setLayout(self.layout1)
        self.setCentralWidget(widget)

        ##############################
        ##############################

        self.axis_Format()
        #self.show()

    def addDataArray(self, coordCross, sliceHor, sliceVert, lc):
        """
        Add data to graph when click in stability diagramm
        """
        if np.size(self.yVert[0,:])<len(self.color):
            ind = np.size(self.yVert[0,:])

            #Add cross to stability diagramm
            temp_cross, = self.ax_Sd.plot(coordCross[0], coordCross[1], marker = '+', markersize = 20, visible = True, color = self.color[ind])
            self.cross += [temp_cross]

            #Add data to data matrix
            self.yVert = np.concatenate((self.yVert, sliceVert), axis = 1)
            self.yHor = np.concatenate((self.yHor, sliceHor), axis = 1)

            #Add checkbox for the new data curve
            text = 'y='+str("%.2e"%coordCross[1])+u'\n x='+str("%.2e"%coordCross[0])
            text += '\n ln='+str(lc[0])+' col='+str(lc[1])
            self.check = self.check + [QCheckBox(text)]
            self.check[-1].setStyleSheet('color:'+self.color[ind])

            self.check[-1].setChecked(True)
            self.check[-1].stateChanged.connect(self.state_Changed)
            self.layout2.addWidget(self.check[-1])

            #Plot datas
            self.plot_Slice(ind)
        else:
            print('Reached max number of curves')
        self.show()

    def state_Changed(self):
        """
        Reinitialize plot when click on one checkbox
        """
        self.sc.ax1.cla()
        self.sc.ax2.cla()
        self.axis_Format()
        for i in range(int(np.shape(self.yVert)[1])):
            if self.check[i].checkState() == Qt.Checked:
                self.plot_Slice(i)
        self.vertCursorH.reinitialize_Ax()
        self.vertCursorV.reinitialize_Ax()

    def plot_Slice(self, ind):
        """
        Plot the slice at the selected points
        """
        self.sc.ax2.plot(self.xVert, self.yVert[:,ind], color = self.color[ind])
        self.sc.ax1.plot(self.xHor, self.yHor[:,ind], color = self.color[ind])
        self.sc.draw()

    def axis_Format(self):
        """
        Set the right format for the graph
        """
        self.sc.ax1.set_title(u'Horizontal slice')
        self.sc.ax1.set_xlabel(u'x')
        #self.sc.ax1.set_ylabel(u'$G (\mu S)$')
        self.sc.ax1.set_ylabel(u'z')
        self.sc.ax1.ticklabel_format(scilimits = (-1,2))
        self.sc.ax1.ticklabel_format(useMathText=True)
        self.sc.ax1.grid()
        
        self.sc.ax2.set_title(u'Vertical slice')
        self.sc.ax2.set_xlabel(u'y')
        self.sc.ax2.ticklabel_format(scilimits = (-1,2))
        self.sc.ax2.ticklabel_format(useMathText=True)
        self.sc.ax2.grid()
        self.sc.draw()

    def empty_Array(self, length):
        """
        Create empty numpy array
        """
        a = np.array([[]])
        empty = a
        for i in range(length):
            empty = np.concatenate((empty,a))        
        return empty

    def closeEvent(self, event):
        """
        Reinitialize data, graphs, checkboxes and cross on stability diagramm
        """
        self.sc.ax1.cla()
        self.sc.ax2.cla()
        #Replacing data array by empty data array
        self.yHor = self.empty_Array(np.size(self.xHor)-1)
        self.yVert = self.empty_Array(np.size(self.xVert)-1)

        #Deleting all check boxes
        self.check = []
        for i in range(self.layout2.count()):
            self.layout2.itemAt(i).widget().close()

        #Deleting and erasing cross
        for i in range(len(self.cross)):
            self.cross[i].set_visible(False)
            self.cross[i].set_visible(False)
        self.cross = []
        self.ax_Sd.figure.canvas.draw()

        self.axis_Format()

        #Recreate the cursors
        Dx = self.xHor.max()-self.xHor.min()
        self.vertCursorH = Cursors.VerticalCursor(self.sc.ax1, self.vertCurs_val_H, self.check_vertCurs_H, self.xHor.min()+0.3*Dx, self.xHor.max()-0.3*Dx)
        Dx = self.xVert.max()-self.xVert.min()
        self.vertCursorV = Cursors.VerticalCursor(self.sc.ax2, self.vertCurs_val_V, self.check_vertCurs_V, self.xVert.min()+0.3*Dx, self.xVert.max()-0.3*Dx)
        
        self.sc.draw()

if __name__ == "__main__":
    #qApp = start_qt_app.prepare_qt()
    #shell_interactive = start_qt_app._interactive
    #myapp.desktop = qApp.desktop() # gives access to screen sizes
    fig, ax = plt.subplots()
    x = np.array([np.linspace(-5,5,100)]).T
    prof = Profils(fig, ax, x, x)
    prof.show()
    prof.addDataArray([1,1], np.exp(-x**2),np.cos(x)*np.exp(-x**2), [0,0])

    # this is to keep multiple myapp alive by keeping a ref to it
    # this is needed for %run -i and execfile invocations,
    #  %run does not need it (it keeps the exec environment in
    #  in the array __IP.shell._user_main_modules

    if not vars().has_key('awarr'): awarr=[]
    #awarr.append(myapp)
    """
    start_qt_app.start_qt_loop_if_needed()
    sys.exit(qApp.exec_()) #make an error when run
    """