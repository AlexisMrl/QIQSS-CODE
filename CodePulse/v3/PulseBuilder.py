#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import copy
from PyQt5 import QtCore, QtWidgets, uic

from tools.MatplotlibWidget import *

import pulse_v3 as model

formclass, baseclass = uic.loadUiType('ui/pulse_builder.ui')
class PBWindow(baseclass, formclass):
    def __init__(self):
        baseclass.__init__(self)
        self.setupUi(self)

        ## class variables
        self.segment = model.Segment('Segment')
        self.sequence = None
        self.sample_rate = 1000
        self.nb_cst, self.nb_rmp, self.nb_sine = 0, 0, 0 # for naming only
        self.selected_atom = None # keep the selected atom in the lit widget
        # for varying sequences:
        self.varying_dict = {} # {atomname: [[param], [values]]}
        
        
        ## initialization
        self.lw_atoms.installEventFilter(self)
        self.uiShowEditValuesRow(0, False)
        self.uiShowEditValuesRow(1, False)
        self.uiShowEditValuesRow(2, False)
        self.updatePlots(clear_first=False)

        ## Connections ##
        self.pb_constant.clicked.connect(self.addCst)
        self.pb_ramp.clicked.connect(self.addRmp)
        self.pb_sine.clicked.connect(self.addSine)
        self.lw_atoms.itemClicked.connect(self.selectAtom)
        self.gb_mark.toggled.connect(self.toggleMark)

        # update ui to Atom/Segment/Sequence
        self.sb_duration.valueChanged.connect(self.changeDuration)
        self.sb_value_1.valueChanged.connect(lambda val: self.changeParam(0, val))
        self.sb_value_2.valueChanged.connect(lambda val: self.changeParam(1, val))
        self.sb_value_3.valueChanged.connect(lambda val: self.changeParam(2, val))
        self.sb_mark_start.valueChanged.connect(lambda val: self.changeMark((val, None)))
        self.sb_mark_stop.valueChanged.connect(lambda val: self.changeMark((None, val)))
        self.sb_seq_repeat.valueChanged.connect(lambda: self.updatePlotSeq(True))
        self.sb_seq_wait.valueChanged.connect(lambda: self.updatePlotSeq(True))
        self.sb_seq_comp.valueChanged.connect(lambda: self.updatePlotSeq(True))
        
        #self.cb_vary_0.toggled.connect(lambda: self.setVarying(0, (0,0)))
        #self.cb_vary_1.toggled.connect(lambda: self.setVarying(1, (0,0)))
        #self.cb_vary_2.toggled.connect(lambda: self.setVarying(2, (0,0)))
        #self.cb_vary_3.toggled.connect(lambda: self.setVarying(3, (0,0)))
        self.vary_start_0.valueChanged.connect(lambda: self.updateVarying(0))
        self.vary_start_1.valueChanged.connect(lambda: self.updateVarying(1))
        self.vary_start_2.valueChanged.connect(lambda: self.updateVarying(2))
        self.vary_start_3.valueChanged.connect(lambda: self.updateVarying(3))
        self.vary_stop_0.valueChanged.connect(lambda: self.updateVarying(0))
        self.vary_stop_1.valueChanged.connect(lambda: self.updateVarying(1))
        self.vary_stop_2.valueChanged.connect(lambda: self.updateVarying(2))
        self.vary_stop_3.valueChanged.connect(lambda: self.updateVarying(3))
        
    ## Functions connected to ui events ## 
    def addCst(self):
        self.addAtom(model.Constant, 'const_'+str(self.nb_cst))
        self.nb_cst += 1
    def addRmp(self):
        self.addAtom(model.Ramp, 'ramp_'+str(self.nb_rmp))
        self.nb_rmp += 1
    def addSine(self):
        self.addAtom(model.Sine, 'sine_'+str(self.nb_sine))
        self.nb_sine += 1
    def addAtom(self, atomType, name):
        # add atom to the model (segment) AND to the interface
        atom = atomType(duration=1, name=name)
        self.segment.insert(atom)
        atom_item = QtWidgets.QListWidgetItem(atom.name)
        self.lw_atoms.addItem(atom_item)
        self.varying_dict[atom.name] = [['duration']+atom.param_lbls]
        self.varying_dict[atom.name].append([(0,0)]*(len(atom.param_lbls)+1))
        print self.varying_dict
        self.updatePlots()
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
        self.updatePlots()
    
    def toggleMark(self, new_state):
        # exec when toggling mark checkbox (!= changeMark)
        atom = self.selected_atom
        new_duration = (0,0)
        if new_state:
           new_duration = (0,1)
        self.sb_mark_start.setValue(new_duration[0])
        self.sb_mark_stop.setValue(new_duration[1])
        self.changeMark(new_duration)
        self.updatePlots()

    def updateVarying(self, row_id):
        # set varying for atom based to spinboxes values
        starts = [self.vary_start_0, self.vary_start_1, self.vary_start_2, self.vary_start_3]
        stops = [self.vary_stop_0, self.vary_stop_1, self.vary_stop_2, self.vary_stop_3]
        self.setVarying(row_id, (starts[row_id].value(), stops[row_id].value()))
        self.updatePlotSeq()

    ## Functions called by the ones above (i.e. not connected to events)
    def updateAtomUiEdit(self):
        # update the 'edit values' group box based on self.selected_atom
        atom = self.selected_atom
        atom_nb_param = self.getNbParam()
        self.gb_atom.setTitle('Edit ' + atom.name)
        spinboxes = [self.sb_value_1, self.sb_value_2, self.sb_value_3]
        labels = [self.lbl_value_1, self.lbl_value_2, self.lbl_value_3]
        for i, (label, spinbox) in enumerate(zip(labels, spinboxes)):
            if i >= atom_nb_param:
                self.uiShowEditValuesRow(i, False)
                continue
            self.uiShowEditValuesRow(i, True)
            label.setText(atom.param_lbls[i])
            spinbox.setValue(atom.param_vals[i])
        self.sb_duration.setValue(atom.get('duration'))
        # setting varying spinboxes
        starts = [self.vary_start_0, self.vary_start_1, self.vary_start_2, self.vary_start_3]
        stops = [self.vary_stop_0, self.vary_stop_1, self.vary_stop_2, self.vary_stop_3]
        for param_id, values in enumerate(self.varying_dict[atom.name][1]):
            starts[param_id].setValue(values[0])
            stops[param_id].setValue(values[1])

    def updateAtomUiMark(self):
        atom = self.selected_atom
        duration = (0,0)
        duration = self.segment.getMarkDuration(atom.name)
        self.sb_mark_start.setValue(duration[0])
        self.sb_mark_stop.setValue(duration[1])
        self.gb_mark.setChecked(duration != (0,0))

    def setVarying(self, param_id, start_stop):
        # set varying for atom to start_stop
        atom = self.selected_atom
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
    
    def uiShowEditValuesRow(self, row, boo):
        # show or hide a row in the group box Edit atom values
        spinboxes =  [self.sb_value_1, self.sb_value_2, self.sb_value_3]
        labels =     [self.lbl_value_1, self.lbl_value_2, self.lbl_value_3]
        starts =     [self.vary_start_1, self.vary_start_2, self.vary_start_3]
        stops =      [self.vary_stop_1, self.vary_stop_2, self.vary_stop_3]
        all_elements = [spinboxes, labels, starts, stops]
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
        # prepare kwargs for pulseDraw
        highlight_atoms = []
        atom = self.selected_atom
        if atom is not None:
            highlight_atoms = [(self.selected_atom.name, 'red')]
        vert_lines = self.action_show_v_lines.isChecked()

        model.pulseDraw(self.segment, self.sample_rate,
                        highlight_atoms=highlight_atoms,
                        vert_lines=True,
                        fig_axes=fig_axes)
        self.segment_plot.canvas.draw()
    
    def updatePlotSeq(self, clear_first=True):
        if clear_first:
            self.sequence_plot.ax1.clear()
            self.sequence_plot.ax2.clear()
        fig_axes = (self.sequence_plot.fig,
                    self.sequence_plot.ax1,
                    self.sequence_plot.ax2)
        # prepare kwargs for makeSequence
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
        
        # prepare kwargs for pulseDraw
        atom = self.selected_atom
        highlight_atoms = []
        if atom is not None:
            highlight_atoms = [(self.selected_atom.name, 'red')]
        vert_lines = self.action_show_v_lines.isChecked()

        model.pulseDraw(self.sequence, self.sample_rate,
                        highlight_atoms=highlight_atoms,
                        vert_lines=False,
                        fig_axes=fig_axes)
        self.sequence_plot.canvas.draw()

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


if __name__ == "__main__":
    #import tools.start_qt_app
    from tools import start_qt_app
    qApp = start_qt_app.prepare_qt()
    shell_interactive = start_qt_app._interactive

    myapp = PBWindow()
    myapp.desktop = qApp.desktop() # gives access to screen sizes
    
    # this is to keep multiple myapp alive by keeping a ref to it
    # this is needed for %run -i and execfile invocations,
    #  %run does not need it (it keeps the exec environment in
    #  in the array __IP.shell._user_main_modules
    if 'awarr' not in vars(): awarr=[]
    awarr.append(myapp)

    myapp.show()
    
    start_qt_app.start_qt_loop_if_needed(redirect_stderr=True)