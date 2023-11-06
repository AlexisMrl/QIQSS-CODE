
class Exporter(object):
    def __init__(self):
        self.string = ''

    def export(self, sequence, sample_rate,
               swp_compensate=0., swp_count=1):
        self.string = ''
        self.string += '%cd "C:/Codes/QIQSS-CODE/CodePulse/v4"\n'
        self.string += "%run -i src/Model.py\n"
        self.writeSection('Code generated from PulseBuilder')
        self.writeEquality('SR', str(sample_rate))

        self.writeSegments(sequence.segments)
        self.writePulse(sequence.segments)

        self.writeSwp(swp_count, swp_compensate)

        self.writePlot()
        self.writeNewLine
        self.writeReload()
    
    def writeEquality(self, left, right):
        self.string += str(left) + ' = ' + str(right) + '\n'
    
    def writeSection(self, string):
        self.string += '## ' + string + ' ##\n'
    
    def writeComment(self, string):
        self.string += '#' + string + '\n'
    
    def writeNewLine(self):
        self.string += '\n'

    def writeSegments(self, segments):
        for segment in segments:
            self.writeEquality(segment.name, str(segment))
    
    def writePulse(self, segments):
        names = [segment.name for segment in segments]
        names = ', '.join(names)
        self.writeEquality('pulse', 'Pulse(*[' + str(names) + '])')
    
    def writeSwp(self, swp_count, swp_compensate):
        self.writeEquality('nb_rep', swp_count)
        self.writeEquality('compensate', swp_compensate)
        self.writeEquality('sequence',
                           'pulse.genSequence(nb_rep=nb_rep, compensate=compensate)')
    
    def writePlot(self):
        self.writeComment(' To plot:')
        self.writeComment('plotPulse(pulse, SR)')
        self.writeComment('plotPulse(sequence, SR, superpose=False)')
    def writeReload(self):
        self.writeComment(' To reload:')
        self.writeComment('%run -i pulsebuilder.py')
        self.writeComment('pb.loadPulse(pulse, nb_rep=nb_rep, compensate=compensate)')

    
    

