#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import copy
from PyQt5 import QtCore, QtWidgets, QtGui, uic

from tools.MatplotlibWidget import *

from pyHegel.gui.ScientificSpinBox import PyScientificSpinBox

import pulse_v3 as model
import tools.Generator

SAMPLE_RATE = 1000

formclass, baseclass = uic.loadUiType('ui/pulse_builder.ui')
class PBWindow(baseclass, formclass):
    def __init__(self):
        baseclass.__init__(self)
        self.setupUi(self)

        ## class variables
        self.segment = model.Segment('Segment')
        self.sequence = None
        self.sample_rate = SAMPLE_RATE
        self.nb_cst, self.nb_rmp = 0, 0 # for naming only
        self.nb_sine, self.nb_gaussian_sine = 0, 0 # for naming only
        self.selected_atom = None # keep the selected atom in the lit widget
        # for varying sequences:
        self.varying_dict = {} # {atomname: [[param], [values]]}
        self.generator = tools.Generator.Generator()
        
        
        ## initialization
        self.lw_atoms.installEventFilter(self)
        self.updatePlots(clear_first=False)
        self.sb_sample_rate.setValue(self.sample_rate)

        ## Connections ## self.sb_sample_rate.valueChanged.connect(lambda val: self.setSampleRate(val))
        self.pb_constant.clicked.connect(lambda: self.addCst())
        self.pb_ramp.clicked.connect(lambda: self.addRmp())
        self.pb_sine.clicked.connect(lambda: self.addSine())
        self.pb_gaussian_sine.clicked.connect(lambda: self.addGaussianSine())
        self.lw_atoms.itemClicked.connect(self.selectAtom)
        self.lw_atoms.model().rowsMoved.connect(self.swapAtom)
        self.gb_mark.toggled.connect(self.toggleMark)

        # update ui to Atom/Segment/Sequence
        self.sb_mark_start.valueChanged.connect(lambda val: self.changeMark((val, None)))
        self.sb_mark_stop.valueChanged.connect(lambda val: self.changeMark((None, val)))
        self.sb_seq_repeat.valueChanged.connect(lambda: self.updatePlotSeq(True))
        self.sb_seq_wait.valueChanged.connect(lambda: self.updatePlotSeq(True))
        self.sb_seq_comp.valueChanged.connect(lambda: self.updatePlotSeq(True))
        
        self.sb_duration.valueChanged.connect(self.changeDuration)
        self.sb_value_1.valueChanged.connect(lambda val: self.changeParam(0, val))
        self.sb_value_2.valueChanged.connect(lambda val: self.changeParam(1, val))
        self.sb_value_3.valueChanged.connect(lambda val: self.changeParam(2, val))
        self.sb_value_4.valueChanged.connect(lambda val: self.changeParam(3, val))
        self.sb_value_5.valueChanged.connect(lambda val: self.changeParam(4, val))
        self.sb_value_6.valueChanged.connect(lambda val: self.changeParam(5, val))
        self.vary_start_0.valueChanged.connect(lambda: self.updateVarying(0))
        self.vary_start_1.valueChanged.connect(lambda: self.updateVarying(1))
        self.vary_start_2.valueChanged.connect(lambda: self.updateVarying(2))
        self.vary_start_3.valueChanged.connect(lambda: self.updateVarying(3))
        self.vary_start_4.valueChanged.connect(lambda: self.updateVarying(4))
        self.vary_start_5.valueChanged.connect(lambda: self.updateVarying(5))
        self.vary_start_6.valueChanged.connect(lambda: self.updateVarying(6))
        self.vary_stop_0.valueChanged.connect(lambda: self.updateVarying(0))
        self.vary_stop_1.valueChanged.connect(lambda: self.updateVarying(1))
        self.vary_stop_2.valueChanged.connect(lambda: self.updateVarying(2))
        self.vary_stop_3.valueChanged.connect(lambda: self.updateVarying(3))
        self.vary_stop_4.valueChanged.connect(lambda: self.updateVarying(4))
        self.vary_stop_5.valueChanged.connect(lambda: self.updateVarying(5))
        self.vary_stop_6.valueChanged.connect(lambda: self.updateVarying(6))

        ## Actions ##
        self.export_code.triggered.connect(self.exportCode)
        self.action_superpose.triggered.connect(self.updatePlotSeq)
        self.action_highlight.triggered.connect(self.updatePlots)
        

        ## objects
        self.edit_sbs=   [self.sb_duration, self.sb_value_1, self.sb_value_2, self.sb_value_3,
                          self.sb_value_4, self.sb_value_5, self.sb_value_6]
        self.edit_lbls=  [self.lbl_duration, self.lbl_value_1, self.lbl_value_2, self.lbl_value_3,
                          self.lbl_value_4, self.lbl_value_5, self.lbl_value_6]
        self.edit_starts=[self.vary_start_0, self.vary_start_1, self.vary_start_2, self.vary_start_3,
                          self.vary_start_4, self.vary_start_5, self.vary_start_6]
        self.edit_stops= [self.vary_stop_0, self.vary_stop_1, self.vary_stop_2, self.vary_stop_3,
                          self.vary_stop_4, self.vary_stop_5, self.vary_stop_6]
        self.max_param = len(self.edit_sbs)
        for row_id in range(1, self.max_param):
            self.uiShowEditValuesRow(row_id, False)
        
    ## Functions connected to ui events ## 
    def swapAtom(self):
        new_lbl_list = [self.lw_atoms.item(i).text() for i in range(self.lw_atoms.count())]
        new_atom_list = [self.segment.get(name) for name in new_lbl_list]
        self.segment.atoms_names = new_lbl_list
        self.segment.atoms = new_atom_list
        self.updatePlots()

    def setSampleRate(self, val):
        self.sample_rate = val
        self.updatePlots()

    def addCst(self, param_vals=.0, duration=1):
        self.addAtom(model.Constant, param_vals, duration, 'const_'+str(self.nb_cst))
        self.nb_cst += 1
    def addRmp(self, param_vals=(0,1), duration=1):
        self.addAtom(model.Ramp, param_vals, duration, 'ramp_'+str(self.nb_rmp))
        self.nb_rmp += 1
    def addSine(self, param_vals=(1,1,0,0), duration=1):
        self.addAtom(model.Sine, param_vals, duration, 'sine_'+str(self.nb_sine))
        self.nb_sine += 1
    def addGaussianSine(self, param_vals=(1,1,0,0,0.1,0), duration=1):
        self.addAtom(model.GaussianSine, param_vals, duration, 'gaussian_sine_'+str(self.nb_gaussian_sine))
        self.nb_gaussian_sine += 1
    def addAtom(self, atomType, atomArgs, duration, name):
        # add atom to the model (segment) AND to the interface
        atom = atomType(name, atomArgs, duration)
        self.segment.insert(atom)
        atom_item = QtWidgets.QListWidgetItem(atom.name)
        self.lw_atoms.addItem(atom_item)
        self.varying_dict[atom.name] = [['duration']+atom.param_lbls]
        self.varying_dict[atom.name].append([(0,0)]*(len(atom.param_lbls)+1))
        self.selectAtom(atom_item)
    
    def removeAtom(self, name):
        # not implemented in the model so the hard work is done here
        id = self.segment._getAtomIndex(name)
        self.segment.atoms.pop(id)
        self.segment.atoms_names.pop(id)
        self.varying_dict.pop(name)
        self.updatePlots()

    def renameAtom(self, old_name, new_name):
        # not implemented in the model so the hard work is done here
        atom = self.segment.get(old_name)
        id = self.segment._getAtomIndex(old_name)
        vary = self.varying_dict.pop(old_name)
        self.segment.atoms_names[id] = new_name
        atom.name = new_name
        self.varying_dict[new_name] = vary
        self.updateAtomUiEdit()
    
    def selectAtom(self, item):
        # exec when an atom from the list is selected
        # update the class variable self.selected_atom
        atom = self.segment.get(item.text())
        self.selected_atom = atom
        self.updateAtomUiEdit()
        self.updateAtomUiMark()
    
    def toggleMark(self, new_state):
        # exec when toggling mark checkbox (!= changeMark)
        atom = self.selected_atom
        new_duration = (0,0)
        if new_state:
           new_duration = (0,1)
        self.sb_mark_start.setValue(new_duration[0])
        self.sb_mark_stop.setValue(new_duration[1])

    def updateVarying(self, row_id):
        # set varying for atom based on spinboxes values
        start = self.edit_starts[row_id].value()
        stop = self.edit_stops[row_id].value()
        self.setVarying(row_id, (start, stop))
        self.updatePlotSeq()

    ## Functions called by the ones above (i.e. not connected to events)
    def updateAtomUiEdit(self):
        # update the 'edit values' group box based on self.selected_atom
        # show and hide appropriate spinboxes
        atom = self.selected_atom
        atom_nb_param = self.getNbParam()
        self.gb_atom.setTitle('Edit ' + atom.name)
        self.sb_duration.setValue(atom.get('duration'))
        for row_i in range(self.max_param):
            if row_i > atom_nb_param:
                self.uiShowEditValuesRow(row_i, False)
                continue
            # update 'varying' section:
            start, stop = self.varying_dict[atom.name][1][row_i]
            self.edit_starts[row_i].setValue(start)
            self.edit_stops[row_i].setValue(stop)
            if row_i == 0:
                continue
            # update value section:
            self.uiShowEditValuesRow(row_i, True)
            self.edit_lbls[row_i].setText(atom.param_lbls[row_i-1])
            self.edit_sbs[row_i].setValue(atom.param_vals[row_i-1])
        self.updatePlots()

    def updateAtomUiMark(self):
        atom = self.selected_atom
        duration = (0,0)
        duration = self.segment.getMarkDuration(atom.name)
        self.sb_mark_start.setValue(duration[0])
        self.sb_mark_stop.setValue(duration[1])
        self.gb_mark.setChecked(duration != (0,0))

    def setVarying(self, param_id, start_stop, atom=None):
        # set varying for atom to start_stop
        atom = self.selected_atom if atom == None else atom
        self.varying_dict[atom.name][1][param_id] = start_stop
    
    ### Functions acting on self.selected_atom: ###
    def changeDuration(self, value):
        self.selected_atom.set('duration', value)
        self.updatePlots()
    
    def changeParam(self, id, value):
        lbl = self.selected_atom.param_lbls[id]
        self.selected_atom.set(lbl, value)
        self.updatePlots()
    
    def changeMark(self, val):
        # change mark value of self.selected_atom
        atom = self.selected_atom
        duration = list(self.segment.getMarkDuration(atom.name))
        if val[0] == None:
            duration[1] = val[1]
        elif val[1] == None:
            duration[0] = val[0]
        elif None not in val:
            duration = val
        self.segment.mark(atom.name, tuple(duration))
        self.updatePlots()

    ### utility functions ###
    def getNbParam(self, atom=None):
        # return the number of parameters available
        if atom == None:
            atom = self.selected_atom
        return len(atom.param_lbls)

    def getVaryingList(self):
        name_to_change, param_to_change, values_to_change = [], [], []
        varying = copy.deepcopy(self.varying_dict)
        for name, (params, values) in varying.items():
            while (0,0) in values:
                id = values.index((0,0))
                values.pop(id)
                params.pop(id)
            if len(values) == 0:
                continue
            name_to_change += [name]*len(values)
            param_to_change += params
            values_to_change += values
        return name_to_change, param_to_change, values_to_change
    
    def genSequence(self):
        # generate self.sequence from self.segment
        repeat = self.sb_seq_repeat.value()
        compensate = self.sb_seq_comp.value()
        wait_time = self.sb_seq_wait.value()
        names_to_change, param_to_change, values_iter = self.getVaryingList()
        self.sequence = self.segment.makeVaryingSequence(repeat,
                                                         names_to_change,
                                                         param_to_change,
                                                         values_iter,
                                                         compensate=compensate,
                                                         wait_time=wait_time,
                                                         name='Sequence')
    
    ## helper for showing and hiding approriate spinboxes in gb_atom
    def uiShowEditValuesRow(self, row, boo):
        # show or hide a row in the group box Edit atom values
        all_elements = [self.edit_sbs, self.edit_lbls, self.edit_starts, self.edit_stops]
        for elem in all_elements:
            if boo: elem[row].show()
            else: elem[row].hide()

    def updatePlots(self, clear_first=True):
        self.updatePlotSeg(clear_first)
        self.updatePlotSeq(clear_first)
    
    def updatePlotSeg(self, clear_first=True):
        if clear_first:
            self.segment_plot.ax1.clear()
            self.segment_plot.ax2.clear()
        fig_axes = (self.segment_plot.fig,
                    self.segment_plot.ax1,
                    self.segment_plot.ax2)
        self.draw(self.segment, fig_axes)
        self.segment_plot.canvas.draw()
    
    def updatePlotSeq(self, clear_first=True):
        if clear_first:
            self.sequence_plot.ax1.clear()
            self.sequence_plot.ax2.clear()
        fig_axes = (self.sequence_plot.fig,
                    self.sequence_plot.ax1,
                    self.sequence_plot.ax2)
        self.genSequence()
        self.draw(self.sequence, fig_axes)
        self.sequence_plot.canvas.draw()
    
    def draw(self, obj, fig_axes):
        # prepare kwargs for pulseDraw
        atom = self.selected_atom
        plot_kwargs = {}
        highlight_atoms = []
        if atom is not None and self.action_highlight.isChecked():
            highlight_atoms = [(atom.name, 'hotpink')]
        vert_lines = False
        superpose = self.action_superpose.isChecked()
        color = 'tab:blue' if superpose else None
            
        model.pulseDraw(obj, self.sample_rate,
                        highlight_atoms=highlight_atoms,
                        vert_lines=vert_lines,
                        superpose=superpose,
                        fig_axes=fig_axes,
                        color=color)

    ## Event filter for the QListWidget ##
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.ContextMenu and source is self.lw_atoms:
            #print 'rightclick detected on' + self.
            menu = QtWidgets.QMenu()
            delete = menu.addAction('Delete')
            rename = menu.addAction('Rename')
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == delete:
                item = source.itemAt(event.pos())
                self.removeAtom(item.text())
                source.model().removeRow(source.currentRow())
            elif action == rename:
                item = source.itemAt(event.pos())
                old_name = item.text()
                new_name, validate = QtWidgets.QInputDialog.getText(self,
                                'New atom name', 'New name:', text=item.text())
                if validate and text != '':
                    item.setText(new_name)
                    self.renameAtom(old_name, new_name)
            return True
        return super(type(self), self).eventFilter(source, event)
    
    def loadSeg(self, segment, sample_rate = SAMPLE_RATE):
        # properly load a segment
        self.segment.name = segment.name
        for atom in segment.atoms:
            self.addAtom(type(atom), atom.param_vals, atom.duration, atom.name)
        self.segment.marks_dict = segment.marks_dict
        self.updateAtomUiMark()
        self.updatePlots()
    
    def loadSeq(self, sequence, sample_rate=SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.loadSeg(sequence.original_segment)
        gen_kwargs = sequence.gen_kwargs
        self.sb_seq_wait.setValue(gen_kwargs.get('wait_time', .0))
        self.sb_seq_repeat.setValue(gen_kwargs.get('repeat', .0))
        self.sb_seq_comp.setValue(gen_kwargs.get('compensate', .0))
        # fill 'varying'
        names = gen_kwargs.get('name_to_change')
        params = gen_kwargs.get('param_to_change')
        values = gen_kwargs.get('values_iter')
        for name, param, (start, stop) in zip(names, params, values):
            atom = self.segment.get(name)
            id = self.varying_dict[atom.name][0].index(param)
            self.setVarying(id, (start, stop), atom)
        self.updatePlots()

    def save(self):
        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        file = open(name,'w')
        text = self.textEdit.toPlainText()
        file.write(text)
        file.close()
        
    def exportCode(self):
        code = self.generator.generate(self.sequence, self.sample_rate)
        self.code_window = QMainWindow()
        self.code_window.setWindowTitle("Generated python code")
        self.code_window.setGeometry(200, 200, 400, 300)
        
        central_widget = QWidget(self)
        text_edit = QTextEdit(self.code_window)
        text_edit.setPlainText(code)

        copy_button = QPushButton("Copy to Clipboard")
        clipboard = QApplication.clipboard()
        copy_button.clicked.connect(lambda: clipboard.setText(text_edit.toPlainText()))
        #QMessageBox.information(self, "Copied", "Text copied to clipboard.")

        layout = QVBoxLayout(central_widget)
        layout.addWidget(text_edit)
        layout.addWidget(copy_button)
        self.code_window.setCentralWidget(central_widget)
        self.code_window.show()


if __name__ == "__main__":
    #import tools.start_qt_app
    from tools import start_qt_app
    qApp = start_qt_app.prepare_qt()
    shell_interactive = start_qt_app._interactive

    pb = PBWindow()
    pb.setWindowTitle('PulseBuilder');
    pb.desktop = qApp.desktop() # gives access to screen sizes
    
    # this is to keep multiple myapp alive by keeping a ref to it
    # this is needed for %run -i and execfile invocations,
    #  %run does not need it (it keeps the exec environment in
    #  in the array __IP.shell._user_main_modules
    if 'awarr' not in vars(): awarr=[]
    awarr.append(pb)

    pb.show()
    
    start_qt_app.start_qt_loop_if_needed(redirect_stderr=True)
                              

    #myapp.loadSeq(sequence, sample_rate)