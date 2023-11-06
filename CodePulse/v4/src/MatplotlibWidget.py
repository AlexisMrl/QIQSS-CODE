from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

    
class MatplotlibWidget(QWidget):
    
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.fig, [self.ax1, self.ax2] = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 1]})
        
        self.canvas = FigureCanvas(self.fig)
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(NavigationToolbar2QT(self.canvas, self))
        vertical_layout.addWidget(self.canvas)
        
        self.setLayout(vertical_layout)