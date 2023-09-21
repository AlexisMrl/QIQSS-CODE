import numpy as np
from pulse_v3 import *

class Generator(object):
    ''' Class that return a generated source code from a Sequence ONLY! '''
    def __init__(self):
        self.code = '' # final string
        self.seg_var_name = "mySegment"
        self.seq_var_name = "mySequence"

    def write(self, end_string):
        self.code = self.code + end_string + '\n'
        
    def writeEqual(self, right, left):
        self.write('{} = {}'.format(right, left))

    def writeSection(self, string):
        self.write('\n## {} ##'.format(string))
    
    def writeMethod(self, obj_name, method_name, *args):
        str_args = ''
        for arg in args:
            str_args += str(arg)
            str_args += ', '
        self.write('{}.{}({})'.format(obj_name, method_name, str_args))
    

    def genSegment(self, segment):
        self.writeSection('Generating segment')
        self.writeEqual(self.seg_var_name, "Segment('{}')".format(segment.name))
        # inserts
        self.write('# atoms')
        for name, atom in segment._iter():
            args = (type(atom).__name__, 
                    "'{}'".format(atom.name), 
                    atom.param_vals,
                    atom.duration)
            self.writeMethod(self.seg_var_name, 'insertNew', *args)
        # marks
        marks = [(name, start_stop) for name, start_stop in segment.marks_dict.items()]
        if marks == []:
            return
        self.write('# marks')
        for key, val in marks:
            self.writeMethod(self.seg_var_name, 'mark', "'{}'".format(key), val)
    
    def genSequence(self, sequence):
        self.writeSection('Generate sequence')
        make_varying = self.seg_var_name
        make_varying += '''.makeVaryingSequence({repeat},
        {name_to_change},
        {param_to_change},
        {values_iter},
        constant_slope={constant_slope},
        wait_time={wait_time},
        compensate={compensate},
        name='{name}')'''.format(**sequence.gen_kwargs)
        self.writeEqual(self.seq_var_name, make_varying)

    def genPulseDraw(self, sequence):
        self.writeSection('Drawing Pulse')
        kws = "{}, sample_rate, superpose=True, color='tab:blue'".format(self.seq_var_name)
        self.write('pulseDraw({})'.format(kws))

    def generate(self, sequence, sample_rate):
        self.code = ''
        dic = sequence.gen_kwargs
        dic['seg_name'] = sequence.original_segment.name

        self.writeSection('Code auto-generated from PulseBuilder GUI')
        self.write('%run -i pulse_v3.py')
        self.writeEqual('sample_rate', sample_rate)
        
        self.genSegment(sequence.original_segment)
        self.genSequence(sequence)
        self.genPulseDraw(sequence)

        self.writeSection('Reload and modify your sequence by running this:')
        self.write('#%run -i PulseBuilder')
        self.write("#pb.loadSeq({}, sample_rate)".format(self.seq_var_name))
        
        return self.code[1:]


    
        