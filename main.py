#!/usr/bin/env /home/uemura/Apps/anaconda3_2021Aprl/bin/python
import sys, os, string, io, glob, re, yaml, math, time, shutil, natsort
import numpy as np
import pandas as pd

import silx
from silx.gui import qt
app = qt.QApplication([])
import time
import silx.gui.colors as silxcolors
from silx.gui.plot import PlotWindow, Plot1D, Plot2D, PlotWidget,items
import silx.gui.colors as silxcolors
import silx.io as silxIO
import tifffile as tif
from scipy.interpolate import interp1d

from mw import Ui_MainWindow

def msg(txt):
    _msg = qt.QMessageBox()
    _msg.setIcon(qt.QMessageBox.Warning)
    _msg.setText(txt)
    _msg.setStandardButtons(qt.QMessageBox.Ok)
    return _msg

default_cmap = silxcolors.Colormap(name='jet')

class Ui(qt.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        self.u = Ui_MainWindow()
        self.u.setupUi(self)

        self.raw_plot = Plot1D()
        layout = qt.QVBoxLayout()
        self.u.widget.setLayout(layout)
        layout.addWidget(self.raw_plot)

        self.conv_plot = Plot1D()
        layout = qt.QVBoxLayout()
        self.u.widget_2.setLayout(layout)
        layout.addWidget(self.conv_plot)

        self.hist = Plot1D()
        layout = qt.QVBoxLayout()
        self.u.widget_3.setLayout(layout)
        layout.addWidget(self.hist)
        self.hist.setGraphTitle("Number of shots")
        self.hist.setGraphYLabel("# shots")


        def selectDir():
            if os.path.isdir(self.u.textBrowser.toPlainText()):
                dat_dir = self.u.textBrowser.toPlainText()
            else:
                dat_dir = os.environ['HOME']
            self.u.listWidget.clear()
            FO_dialog = qt.QFileDialog(self)
            f = FO_dialog.getExistingDirectory(self, "Select a directory", dat_dir,)
            if f and os.path.isdir(f):
                self.u.textBrowser.clear()
                self.u.textBrowser.append(f)
                print (os.listdir(f))
                # dirs = [x for x in os.listdir(f) if os.path.isdir(dat_dir+'/'+x)]
                dirs = [x for x in os.listdir(f) if re.match(r'r\d+',x)]
                self.u.listWidget.clear()
                if dirs:
                    self.u.listWidget.addItems(natsort.natsorted(dirs))
                else:
                    msg("Please select a directory which includes tiff files ;_;").exec_()
            else:
                msg("!! You did not select a directory :(").exec_()

        def reloadDir():
            _dir = self.u.textBrowser.toPlainText()
            if _dir and os.path.isdir(_dir):
                self.u.textBrowser.clear()
                self.u.textBrowser.append(_dir)
                dirs = [x for x in os.listdir(_dir) if re.match(r'r\d+',x)]
                self.u.listWidget.clear()
                if dirs:
                    self.u.listWidget.addItems(natsort.natsorted(dirs))
                else:
                    msg("Please select a directory which includes tiff files ;_;").exec_()
            else:
                msg("!! You did not select a directory :(").exec_()


        def load_data():
            self.u.comboBox.clear()
            if self.u.listWidget.selectedItems():
                items = [x.text() for x in self.u.listWidget.selectedItems()]
                self.u.comboBox.addItems(items)

                self.u.listWidget_2.clear()
                self.u.listWidget_2.addItems(items)
                for j in range(self.u.listWidget_2.count()):
                    self.u.listWidget_2.item(j).setSelected(True)

        def unselectFiles():
            if self.u.listWidget.selectedItems():
                for x in self.u.listWidget.selectedItems():
                    x.setSelected(False)

        def plot_single_run(rnum):
            if rnum:
                datdir = self.u.textBrowser.toPlainText()+'/'+rnum
                ext = ('escan'*(self.u.radioButton.isChecked())+'mscan'*(self.u.radioButton_2.isChecked()))+'_mpccd'*(self.u.rB_MPCCD.isChecked())
                file = f'{rnum}_{ext}.csv'
                if not os.path.isfile(datdir+'/'+file):
                    msg(f"!! <i><font color='red'>{ext}</font> </i> files are not found. You do not select the scan type properly... :(").exec_()
                    return
                try:
                    df = pd.read_csv(datdir+'/'+file,delim_whitespace=True)
                    if self.u.radioButton_2.isChecked():
                        self.raw_plot.addCurve(df['#motor'],df['xas_on'],color='red',linewidth=1.5,symbol='.',legend='On')
                        self.raw_plot.addCurve(df['#motor'], df['xas_off'],color='blue',linewidth=1.5,symbol='.',legend='Off')
                        self.raw_plot.addCurve(df['#motor'],df['xas_on']-df['xas_off'],yaxis='right',color='green',linewidth=1.5,symbol='.',legend='diff')
                        self.raw_plot.setGraphXLabel('Motor /pls')
                        self.raw_plot.setGraphYLabel('XAS')
                        self.raw_plot.setGraphYLabel('$\Delta$XAS',axis='right')
                        self.raw_plot.setGraphTitle(f'{rnum}')
                        median = np.median(np.diff(df['#motor'].values))
                        # if median.size > 1:
                        #     x = np.append(df['#motor'].values,df['#motor'].values[-1]+median[0])
                        # else:
                        #     x = np.append(df['#motor'].values, df['#motor'].values[-1] + median)
                        self.hist.addCurve(df['#motor'].values,df['num_shots_on'].values,symbol='o',legend='On')
                        self.hist.addCurve(df['#motor'].values, df['num_shots_off'].values,symbol='o', legend='Off')
                        self.hist.setGraphXLabel("Motor /pls")
                    elif self.u.radioButton.isChecked():
                        self.raw_plot.addCurve(df['Energy'], df['xas_on'], color='red',linewidth=1.5,symbol='.', legend='On')
                        self.raw_plot.addCurve(df['Energy'], df['xas_off'], color='blue',linewidth=1.5,symbol='.', legend='Off')
                        self.raw_plot.addCurve(df['Energy'], df['xas_on'] - df['xas_off'], yaxis='right', color='green',linewidth=1.5,symbol='.',legend='diff')
                        self.raw_plot.setGraphXLabel('Energy /eV')
                        self.raw_plot.setGraphYLabel('XAS')
                        self.raw_plot.setGraphYLabel('$\Delta$XAS', axis='right')
                        self.raw_plot.setGraphTitle(f'{rnum}')

                        # median = np.median(np.diff(df['Energy'].values))
                        # if median.size > 1:
                        #     x = np.append(df['Energy'].values, df['Energy'].values[-1] + median[0])
                        # else:
                        #     x = np.append(df['Energy'].values, df['Energy'].values[-1] + median)
                        self.hist.addCurve(df['Energy'].values, df['num_shots_on'].values,symbol='o',legend='On')
                        self.hist.addCurve(df['Energy'].values, df['num_shots_off'].values,symbol='o', legend='Off')
                        self.hist.setGraphXLabel("Energy /eV")

                except Exception as e:
                    msg(f"!! {str(e)}").exec_()

        def merge():
            if self.u.comboBox.currentText():
                rnum = self.u.comboBox.currentText()
                datdir = self.u.textBrowser.toPlainText() + '/' + rnum
                ext = ('escan'*(self.u.radioButton.isChecked())+'mscan'*(self.u.radioButton_2.isChecked()))+'_mpccd'*(self.u.rB_MPCCD.isChecked())
                items = [x.text() for x in self.u.listWidget_2.selectedItems()]
                xas_on, xas_off = [], []
                df_model = pd.read_csv(datdir+'/'+f'{rnum}_{ext}.csv',delim_whitespace=True)

                if self.u.radioButton.isChecked():
                    x = df_model['Energy'].values
                    for _f in items:
                        try:
                            _datdir = self.u.textBrowser.toPlainText()
                            df = pd.read_csv(f'{_datdir}/{_f}/{_f}_{ext}.csv',delim_whitespace=True)
                            func = interp1d(df['Energy'].values,df['xas_on'].values,bounds_error=False)
                            xas_on.append(func(x))
                            func = interp1d(df['Energy'].values, df['xas_off'].values, bounds_error=False)
                            xas_off.append(func(x))
                        except Exception as e:
                            print (f"Error for '_f': str{e}")
                    try:
                        xas_on = np.array(xas_on)
                        xas_off = np.array(xas_off)
                        self.conv_plot.addCurve(x, np.nanmean(xas_on,axis=0), color='red',linewidth=1.5,symbol='.',legend='On')
                        self.conv_plot.addCurve(x, np.nanmean(xas_off, axis=0),color='blue',linewidth=1.5,symbol='.',legend='Off')
                        self.conv_plot.addCurve(x, np.nanmean(xas_on,axis=0)-np.nanmean(xas_off, axis=0), color='green',yaxis='right',linewidth=1.5,symbol='.',legend='diff')
                        self.conv_plot.setGraphXLabel('Energy /eV')
                        self.conv_plot.setGraphYLabel('XAS')
                        self.conv_plot.setGraphYLabel('$\Delta$XAS', axis='right')
                    except Exception as e:
                        msg("!! {str(e)}").exec_()

                elif self.u.radioButton_2.isChecked():
                    x = df_model['#motor'].values
                    for _f in items:
                        try:
                            _datdir = self.u.textBrowser.toPlainText()
                            df = pd.read_csv(f'{_datdir}/{_f}/{_f}_{ext}.csv',delim_whitespace=True)
                            func = interp1d(df['#motor'].values,df['xas_on'].values,bounds_error=False)
                            xas_on.append(func(x))
                            func = interp1d(df['#motor'].values, df['xas_off'].values, bounds_error=False)
                            xas_off.append(func(x))
                        except Exception as e:
                            print (f"Error for '_f': str{e}")

                    try:
                        xas_on = np.array(xas_on)
                        xas_off = np.array(xas_off)
                        self.conv_plot.addCurve(x, np.nanmean(xas_on, axis=0), color='red',linewidth=1.5,symbol='.', legend='On')
                        self.conv_plot.addCurve(x, np.nanmean(xas_off, axis=0), color='blue',linewidth=1.5,symbol='.',legend='Off')
                        self.conv_plot.addCurve(x, np.nanmean(xas_on, axis=0) - np.nanmean(xas_off, axis=0), color='green',yaxis='right',linewidth=1.5,symbol='.',legend='diff')
                        self.conv_plot.setGraphXLabel('Motor /pls')
                        self.conv_plot.setGraphYLabel('XAS')
                        self.conv_plot.setGraphYLabel('$\Delta$XAS',axis='right')
                    except Exception as e:
                        msg(f"!! {str(e)}").exec_()

        def savedata():
            if os.path.isdir(self.u.textBrowser.toPlainText()):
                FO_dialog = qt.QFileDialog(self)
                f = FO_dialog.getSaveFileName(self, "Set the output file name", self.u.textBrowser.toPlainText(), )
                if f[0]:
                    try:
                        x,On,_,_ = self.conv_plot.getCurve('On').getData()
                        x, Off, _, _ = self.conv_plot.getCurve('Off').getData()
                        x, diff, _, _ = self.conv_plot.getCurve('diff').getData()
                        label = '#Energy/eV'*(self.u.radioButton.isChecked()) + '#Motor/pls'*(self.u.radioButton_2.isChecked())
                        pd.DataFrame({
                            label: x,
                            'On': On,
                            'Off': Off,
                            'diff': diff
                        }).to_csv(f[0],index=False,sep=' ')
                    except Exception as e:
                        msg(f"!! {str(e)}").exec_()

        self.u.pushButton.clicked.connect(selectDir)
        self.u.pushButton_2.clicked.connect(load_data)
        self.u.comboBox.currentTextChanged.connect(plot_single_run)
        self.u.pushButton_3.clicked.connect(merge)
        self.u.pushButton_4.clicked.connect(reloadDir)
        self.u.pushButton_5.clicked.connect(savedata)
        self.u.pushButton_6.clicked.connect(unselectFiles)
        self.show()

if __name__ == '__main__':
    mw = Ui()
    app.exec_()
