import numpy as np

class Shape(object):
    parameters = {}
    def getWave(self, sample_rate, duration):
        pass
    def getArea(self, duration):
        return 0
    def __str__(self):
        return self.__class__.__name__ + '(**' \
            + self.parameters.__str__() + ')'


class Ramp(Shape):
    parameters = {'val_start':0, 'val_end':1}
    def __init__(self, val_start, val_end):
        self.parameters = {'val_start':val_start, 'val_end':val_end}
    
    def getWave(self, sample_rate, duration):
        val_start = self.parameters['val_start']
        val_end = self.parameters['val_end']
        return np.linspace(val_start, val_end, int(duration*sample_rate))
    
    def getArea(self, duration):
        start = self.parameters['val_start']
        end = self.parameters['val_end']
        return (start+end)/2 * duration

class Sine(Shape):
    parameters = {'freq':1, 'amp':1, 'phase':0}
    def __init__(self, freq, amp, phase):
        self.parameters = {'freq':freq, 'amp':amp, 'phase': phase}

    def getWave(self, sample_rate, duration):
        amp = self.parameters['amp']
        freq = self.parameters['freq']
        phase = self.parameters['phase']
        t = np.linspace(0, duration, int(duration*sample_rate))
        return amp * np.sin(2*np.pi*freq*t + phase)

class Gaussian(Shape):
    parameters = {'amp':1, 'sigma':0.1, 'mu':0}
    def __init__(self, amp, sigma, mu):
        self.parameters = {'amp':amp, 'sigma':sigma, 'mu':mu}

    def getWave(self, sample_rate, duration):
        amp = self.parameters['amp']
        sigma = self.parameters['sigma']
        mu = self.parameters['mu']
        t = np.linspace(-duration/2., duration/2., int(duration*sample_rate))
        return amp * np.exp(-(t-mu)**2/(2*sigma**2))

class GaussianFlatTop(Shape):
    parameters = {'amp':1, 'sigma':0.1, 'mu':0, 'flat_perc':0.5}
    def __init__(self, amp, sigma, mu, flat_perc):
        self.parameters = {'amp':amp, 'sigma':sigma, 'mu':mu, 'flat_perc':flat_perc}
    
    def getWave(self, sample_rate, duration):
        amp = self.parameters['amp']
        sigma = self.parameters['sigma']
        mu = self.parameters['mu']
        flat_perc = self.parameters['flat_perc']

        # define timings
        gaussian_duration = duration*(1-flat_perc)
        gaussian_nbpts = int(gaussian_duration*sample_rate)
        flat_duration = duration*flat_perc
        flat_nbpts = int(flat_duration*sample_rate)

        # ensure total number of points is correct
        total_nbpts = gaussian_nbpts + flat_nbpts
        if total_nbpts != duration*sample_rate:
            flat_nbpts += int(duration*sample_rate) - total_nbpts

        # building parts
        flat = amp * np.ones(flat_nbpts)
        gaussian_t = np.linspace(-gaussian_duration/2., gaussian_duration/2.,
                                 int(gaussian_duration*sample_rate), endpoint=True)
        gaussian = amp * np.exp(-(gaussian_t-mu)**2/(2*sigma**2))

        # split gaussian in two parts at the maximum
        max_index = np.argmax(gaussian)
        raising = gaussian[:max_index]
        falling = gaussian[max_index:]

        return np.concatenate((raising, flat, falling))

