from PyQt5.QtWidgets import *
from PyQt5 import QtCore, uic
formclass, baseclass = uic.loadUiType('src/ui/pulse_builder.ui')

from pyHegel.gui import ScientificSpinBox

from Model import Segment, Pulse, plotPulse
from Shapes import Ramp, Sine, Gaussian, GaussianFlatTop
from Export import Exporter


class PbWindow(baseclass, formclass):
    def __init__(self):
        baseclass.__init__(self)
        # setup
        self.setupUi(self)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.exporter = Exporter()

        # app options
        self.shape_cls = [('NoneType',None), ('Ramp',Ramp), ('Sine',Sine), ('Gaussian',Gaussian), ('GaussianFlatTop',GaussianFlatTop)]
        self.show_plot = self.en_plots.isChecked()
        self.superpose = self.en_superpose.isChecked()
        self.highlight = self.en_highlight.isChecked()
        self.sweep_count = self.sb_sweep_count.value()
        self.compensate = self.sb_compensate.value()
        self.sample_rate = self.sb_sample_rate.value()
        self.loading = False

        # sequence
        self.sequence = Pulse()
        self.swp_sequence = Pulse()

        # setter
        self.en_plots.toggled.connect(lambda b: self.setShowPlot(b))
        self.en_superpose.toggled.connect(lambda b: self.setSuperpose(b))
        self.en_highlight.toggled.connect(lambda b: self.setHighlight(b))
        self.sb_sweep_count.valueChanged.connect(lambda val: self.setSweepCount(val))
        self.sb_compensate.valueChanged.connect(lambda val: self.setCompensate(val))
        self.sb_sample_rate.valueChanged.connect(lambda val: self.setSampleRate(val))

        # ui slots
        self.bt_add_segment.clicked.connect(lambda _: self.addSegment())
        self.bt_rm_segment.clicked.connect(lambda _: self.removeSegment())
        self.tree.itemSelectionChanged.connect(lambda: self.drawPlots())
        self.action_export.triggered.connect(lambda _: self.showWindowExport())

        
    # ====
    
    # ====  view part  ====  #
    def triggerUpdatePlots(func):
        def wrapper(self, *args, **kwargs):
            gen_swp_sequence_flag = kwargs.pop('gen_swp_sequence', True)
            # ---
            result = func(self, *args, **kwargs)
            # ---
            if gen_swp_sequence_flag:
                self.genSwpSequence()
            self.drawPlots(swp_sequence=gen_swp_sequence_flag)
            self.duration_label.setText(str(self.swp_sequence.duration))
            self.nbpts_label.setText(str(self.swp_sequence.duration*self.sample_rate))
            return result
        return wrapper
    
    @triggerUpdatePlots
    def treeRemoveSegment(self, i_seg):
        # remove the segment at index i_seg
        self.tree.takeTopLevelItem(i_seg)
    
    def _treeAddLine(self, parent, label):
        item = QTreeWidgetItem(parent)
        item.setText(0, label)
        return item
    def _treeAddSpinbox(self, value, column, parent):
        widget = ScientificSpinBox.PyScientificSpinBox()
        widget.setValue(value)
        self.tree.setItemWidget(parent, column, widget)
        return widget
    def _treeAddCombobox(self, values, column, parent):
        widget = QComboBox()
        widget.addItems(values)
        self.tree.setItemWidget(parent, column, widget)
        return widget
    def _treeAddCheckbox(self, value, column, parent):
        widget = QCheckBox()
        widget.setChecked(value)
        self.tree.setItemWidget(parent, column, widget)
        return widget

    def _treeAddSweep(self, parent, i_seg, param_lbl):
            cb = self._treeAddCheckbox(False, 2, parent)
            sb_start = self._treeAddSpinbox(0, 3, parent)
            sb_stop = self._treeAddSpinbox(0, 4, parent)
            sb_start.setEnabled(False); sb_stop.setEnabled(False)
            cb.toggled.connect(lambda boo: sb_start.setEnabled(boo))
            cb.toggled.connect(lambda boo: sb_stop.setEnabled(boo))
            cb.toggled.connect(lambda boo, i_seg=i_seg, param_lbl=param_lbl: self.setSweep(boo, i_seg, param_lbl, (sb_start.value(), sb_stop.value())))
            sb_start.valueChanged.connect(lambda val, i_seg=i_seg, param_lbl=param_lbl: self.setSweep(cb.isChecked(), i_seg, param_lbl, (val, sb_stop.value())))
            sb_stop.valueChanged.connect(lambda val, i_seg=i_seg, param_lbl=param_lbl: self.setSweep(cb.isChecked(), i_seg, param_lbl, (sb_start.value(), val)))
            return cb, sb_start, sb_stop
    
    def treeAddSegment(self, seg):
        # add a segment at the end of the tree
        i_seg = len(self.sequence.segments)-1
        # - name
        seg_item = QTreeWidgetItem(self.tree)
        seg_item.setText(0, seg.name)
        # - duration    
        seg_item_duration = self._treeAddLine(seg_item, 'Duration')
        duration_spinbox = self._treeAddSpinbox(seg.duration, 1, seg_item_duration)
        duration_spinbox.valueChanged.connect(lambda val, i=i_seg: self.setDuration(i, val))
        duration_spinbox.setMinimum(0)
        _, sb_start, sb_stop = self._treeAddSweep(seg_item_duration, i_seg, 'duration')
        sb_start.setMinimum(0); sb_stop.setMinimum(0)
        # - offset
        seg_item_offset = self._treeAddLine(seg_item, 'Offset')
        offset_spinbox = self._treeAddSpinbox(seg.offset, 1, seg_item_offset)
        offset_spinbox.valueChanged.connect(lambda val, i=i_seg: self.setOffset(i, val))
        self._treeAddSweep(seg_item_offset, i_seg, 'offset')
        # - waveform combobox
        seg_item_waveform = self._treeAddLine(seg_item, 'Waveform')
        waveform_combobox = self._treeAddCombobox([shape[0] for shape in self.shape_cls], 1, seg_item_waveform)
        waveform_shape_cls = seg.waveform.__class__.__name__
        waveform_combobox.setCurrentText(waveform_shape_cls)
        waveform_combobox.currentTextChanged.connect(lambda shape, i_seg=i_seg: self.setWaveform(i_seg, shape))
        self.treeUpdateWaveform(i_seg)
        # - envelope combobox
        seg_item_envelope = self._treeAddLine(seg_item, 'Envelope')
        envelope_combobox = self._treeAddCombobox([shape[0] for shape in self.shape_cls], 1, seg_item_envelope)
        envelope_shape_name = seg.envelope.__class__.__name__
        envelope_combobox.setCurrentText(envelope_shape_name)
        envelope_combobox.currentTextChanged.connect(lambda shape, i_seg=i_seg: self.setEnvelope(i_seg, shape))
        self.treeUpdateEnvelope(i_seg)
        # - mark
        seg_item_mark = self._treeAddLine(seg_item, 'Marks')
        beg_mark = self._treeAddLine(seg_item_mark, 'start')
        beg_mark_spinbox = self._treeAddSpinbox(seg.mark[0], 1, beg_mark)
        beg_mark_spinbox.setRange(0, 1); beg_mark_spinbox.setSingleStep(0.01)
        beg_mark_spinbox.valueChanged.connect(lambda val, i=i_seg: self.setMark(i, 'start', val))
        #self._treeAddSweep(beg_mark, i_seg, ('mark','start'))
        end_mark = self._treeAddLine(seg_item_mark, 'finish')
        end_mark_spinbox = self._treeAddSpinbox(seg.mark[1], 1, end_mark)
        end_mark_spinbox.setRange(0, 1); end_mark_spinbox.setSingleStep(0.01)
        end_mark_spinbox.valueChanged.connect(lambda val, i=i_seg: self.setMark(i, 'finish', val))
        #self._treeAddSweep(end_mark, i_seg, ('mark','finish'))
    
    def _treeUpdateShape(self, i_seg, shape_type):
        # update the shape parameters sub-items and the sweep values
        shape_id = ['waveform', 'envelope'].index(shape_type) + 2
        seg_item = self.tree.topLevelItem(i_seg)
        shape_item = seg_item.child(shape_id)
        shape_combobox = self.tree.itemWidget(shape_item, 1)
        shape_name = shape_combobox.currentText()
        shape_item.takeChildren()
        if shape_name != 'NoneType':
            shape_param = getattr(self.sequence.segments[i_seg], shape_type).parameters
            for param, val in shape_param.items():
                param_item = self._treeAddLine(shape_item, param)
                param_spinbox = self._treeAddSpinbox(val, 1, param_item)
                param_spinbox.valueChanged.connect(lambda val, i=i_seg, p=param: self.setShapeParam(i, shape_type, p, val))
                self._treeAddSweep(param_item, i_seg, (shape_type,param))

    def treeUpdateWaveform(self, i_seg):
        self._treeUpdateShape(i_seg, 'waveform')
    
    def treeUpdateEnvelope(self, i_seg):
        self._treeUpdateShape(i_seg, 'envelope')
    
    def treeGetSelectedSegment(self):
        # return the selected segment
        selected_items = self.tree.selectedItems()
        if len(selected_items) == 0:
            return None
        selected_item = selected_items[0]
        while selected_item.parent() is not None:
            selected_item = selected_item.parent()
        return self.tree.indexOfTopLevelItem(selected_item)
 

    def drawPlots(self, swp_sequence=False):
        if self.loading:
            return
        seq_list = [(self.sequence, self.plot_segment)]
        if swp_sequence:
            seq_list.append((self.swp_sequence, self.plot_sequence))
        for seq, plot in seq_list:
            plot.ax1.clear()
            plot.ax2.clear()
            if not self.show_plot:
                plot.canvas.draw()
                return

            selected_segment = self.treeGetSelectedSegment()
            highlight = [] if selected_segment is None else [selected_segment]
            highlight = highlight if self.highlight else []

            plotPulse(seq,
                      self.sample_rate,
                      superpose=self.superpose,
                      highlight=highlight,
                      fig_axes=(plot.fig, plot.ax1, plot.ax2))
            plot.canvas.draw()


    #  ====  controller part  ====  #
    @triggerUpdatePlots
    def setShowPlot(self, val):
        self.show_plot = val

    @triggerUpdatePlots
    def setSuperpose(self, val):
        self.superpose = val
    
    @triggerUpdatePlots
    def setHighlight(self, val):
        self.highlight = val

    @triggerUpdatePlots
    def addSegment(self, seg=None):
        # add a segment to the sequence
        if seg == None:
            seg = Segment(duration=0.1, waveform=Sine(10,2,0))
        self.sequence.addSegment(seg)
        self.treeAddSegment(seg)
    
    @triggerUpdatePlots
    def removeSegment(self):
        # remove the selected segment from the sequence
        i_seg = self.treeGetSelectedSegment()
        if i_seg is None:
            return
        self.sequence.removeSegment(i_seg)
        self.treeRemoveSegment(i_seg)

    @triggerUpdatePlots
    def setDuration(self, i_seg, val):
        self.sequence.segments[i_seg].duration = float(val)
        self.sequence.duration = sum([seg.duration for seg in self.sequence.segments])

    @triggerUpdatePlots
    def setOffset(self, i_seg, val):
        self.sequence.segments[i_seg].offset = float(val)
    
    @triggerUpdatePlots
    def setMark(self, i_seg, mark, val):
        if mark == 'start':
            self.sequence.segments[i_seg].mark = (float(val), self.sequence.segments[i_seg].mark[1])
        elif mark == 'finish':
            self.sequence.segments[i_seg].mark = (self.sequence.segments[i_seg].mark[0], float(val))

    def _setShapeHelper(self, shape_name):
        if shape_name == 'NoneType':
            return None
        else:
            shape_cls = [shape_cls[1] for shape_cls in self.shape_cls if shape_cls[0] == shape_name][0]
            param = shape_cls.parameters
            return shape_cls(**param)

    @triggerUpdatePlots
    def setWaveform(self, i_seg, shape):
        self.sequence.segments[i_seg].waveform = self._setShapeHelper(shape)
        self.sequence.segments[i_seg].sweep_dict['waveform'] = {}
        self.treeUpdateWaveform(i_seg)
    
    @triggerUpdatePlots
    def setEnvelope(self, i_seg, shape):
        self.sequence.segments[i_seg].envelope = self._setShapeHelper(shape)
        self.sequence.segments[i_seg].sweep_dict['envelope'] = {}
        self.treeUpdateEnvelope(i_seg)

    @triggerUpdatePlots
    def setShapeParam(self, i_seg, wv_or_env, param, val):
        if wv_or_env == 'waveform':
            self.sequence.segments[i_seg].waveform.parameters[param] = val
        elif wv_or_env == 'envelope':
            self.sequence.segments[i_seg].envelope.parameters[param] = val

    # -- swp sequence related -- #
    def genSwpSequence(self):
        self.swp_sequence = self.sequence.genSequence(
            nb_rep=self.sweep_count,
            compensate=self.compensate)

    @triggerUpdatePlots
    def setSweepCount(self, val):
        self.sweep_count = val

    @triggerUpdatePlots
    def setCompensate(self, val):
        self.compensate = val

    @triggerUpdatePlots
    def setSampleRate(self, val):
        self.sample_rate = val

    @triggerUpdatePlots
    def setSweep(self, boo, i_seg, param, val):
        seg = self.sequence.segments[i_seg]
        if boo:
            if isinstance(param, tuple):
                if param[0] not in seg.sweep_dict:
                    seg.sweep_dict[param[0]] = {}
                seg.sweep_dict[param[0]][param[1]] = val
            else:
                seg.sweep_dict[param] = val
        else:
            if isinstance(param, tuple):
                seg.sweep_dict[param[0]].pop(param[1], None)
            else:
                seg.sweep_dict.pop(param, None)
    


    # ====  export and load part  ====  #
    def showWindowExport(self):
        self.export_window = QMainWindow()
        self.export_window.setWindowTitle('Export')
        self.export_window.setGeometry(200, 200, 400, 300)

        w_central_widget = QWidget(self)
        w_text_edit = QTextEdit(self.export_window)
        w_copy_button = QPushButton('Copy to clipboard')
        w_layout = QVBoxLayout(w_central_widget)
        w_layout.addWidget(w_text_edit)
        w_layout.addWidget(w_copy_button)

        self.exporter.export(self.sequence,
                             self.sample_rate,
                             swp_count=self.sweep_count,
                             swp_compensate=self.compensate)
        w_text_edit.setPlainText(self.exporter.string)

        clipboard = QApplication.clipboard()
        w_copy_button.clicked.connect(lambda: clipboard.setText(w_text_edit.toPlainText()))

        self.export_window.setCentralWidget(w_central_widget)
        self.export_window.show()
    
    def loadPulse(self, pulse, nb_rep=None, compensate=None, sample_rate=None):
        self.sequence = Pulse()
        self.tree.clear()
        self.loading = True
        for seg in pulse.segments:
            self.addSegment(seg)

        # manually set ui values
        if nb_rep is not None:
            self.sb_sweep_count.setValue(nb_rep)
        if compensate is not None:
            self.sb_compensate.setValue(compensate)
        if sample_rate is not None:
            self.sb_sample_rate.setValue(sample_rate)

        self.loading = False
        self.genSwpSequence()
        self.drawPlots(swp_sequence=True)
    
        
        
