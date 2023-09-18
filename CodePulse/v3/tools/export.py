import numpy as np
from pulse_v3 import *

class Exporter(object):
    def __init__(self, location, filename, filetype):
        self.string = ''
    def __add__(self, end_string):
        if end_string is not str:
            raise NotImplementedError()
        self.string = self.string + end_string + '\n'
    def __radd__(self, beg_string):
        self.string = beg_string + '\n' + self.string
        
    def exportWaveToNpy(self, file, wave, mark):
        np.save(file, np.array([wave, mark]))
    
    def exportWaveToTxt(self, file, wave, mark):
        np.savetxt(file, np.array([wave, mark]))

    def genSequence(self, **kwargs):
        pass
    def genSegment(self, segment):
        pass
    def genAtom(self, atom):
        pass

    def exportCodeToPy(self, segment):
        raise NotImplementedError()
    
        