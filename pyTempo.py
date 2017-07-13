#!/usr/bin/python

import argparse


from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import thread

from AudioApp import AudioApp
from pyAudioStreamer import PyAudioStreamer

import librosa

class PyTempo(AudioApp):

    def __init__(self, pas):
        """ 
            Args:
                pas    reference to pyAudioStreamer; used for getting stream's sample rate, etc.
        """ 
        super(PyTempo, self).__init__()
        self.BUFFER_SIZE = 50 # number of buffered sample blocks to use for tempo estimation
                              # the actual number of samples used is self.BUFFER_SIZE * each element in self.circular_buffer
        self.TEMPO_ENV_SIZE = 500
        self.pas = pas
        self.onset_env = [] # Onset envelope, plotted
        self.tempo_env = [] # Time series of tempo values, plotted
        self.curve = None
        
        self.p={}
    
    def plot(self):
        """ Create a graphics window, and add a plot
        """
        self.win = pg.GraphicsWindow()
        self.win.setWindowTitle('Tempo Estimator')
        
        self.p['OnSet_Envelope'] = self.win.addPlot(title = 'OnSet Envelope', row=0, col=0)
        self.curve = {'OnSet_Envelope':self.p['OnSet_Envelope'].plot(pen='y')}
        self.p['OnSet_Envelope'].showGrid(x=True, y=True)
        
        self.p['Tempo'] = self.win.addPlot(title = 'Tempo', row=1, col=0)
        self.curve.update({'Tempo':self.p['Tempo'].plot(pen='y')})
        self.p['Tempo'].showGrid(x=True, y=True)
        
        self.text_tempo = pg.TextItem('test',color=(200, 200, 200))
        self.p['Tempo'].addItem(self.text_tempo)
    
    def update(self):
        """ Update the data for plot
        
        This function gets called every "--interval" seconds.
        
        """
        if self.curve is not None:
            if len(self.onset_env) > 0:
                self.curve['OnSet_Envelope'].setData(self.onset_env)
                self.curve['Tempo'].setData(self.tempo_env)
                self.text_tempo.setText('{}'.format(self.tempo_env[-1]))
                self.text_tempo.setPos(0, round(np.mean(self.tempo_env)))
#                 self.p['OnSet_Envelope'].enableAutoRange('y', False)
    
    def run(self):
        while(True):
            if(len(self.circular_buffer) > 0):
                samples_combined = np.array([])
                for samples in list(self.circular_buffer): # convert to list to avoid contention
                    samples_combined = np.concatenate((samples_combined, samples))
                
#                 print "len(samples_combined)", len(samples_combined)
                onset_env = librosa.onset.onset_strength(samples_combined, sr=self.pas.RATE)
                self.onset_env = onset_env
                tempo = librosa.beat.estimate_tempo(onset_env, sr=self.pas.RATE)
#                 print "tempo",tempo
                self.tempo_env.append(tempo)
#                 print "len(onset_env)",len(onset_env)
#                 print samples_combined
                #self.app_img[1::, : , :] = self.app_img[0:599, :, :]
                # insert new spectrum 
                #self.app_img[0, : ,0] = onset_env
                
                if(len(self.circular_buffer) >= self.BUFFER_SIZE):
                    self.circular_buffer.popleft()
                    
                if(len(self.tempo_env) >= self.TEMPO_ENV_SIZE):
                    self.tempo_env.pop(0)
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ifile', help='input wav/mp3 file', default=None)
    parser.add_argument('--interval', help='update interval in seconds', type=float, default=1.0)
    args = parser.parse_args()
    
    app = QtGui.QApplication([])
    
    # instantiate objects 
    pas = PyAudioStreamer(CHUNK=22050/2, channels=1, INTERVAL=args.interval)
    ps = PyTempo(pas)

    # register pySTFT's internal buffer with the audio streamer
    # so that the audio streamer enqueus samples to the pySTFT
    pas.register(ps.circular_buffer)
    thread.start_new_thread(pas.start, (args.ifile,))

    ps.plot()
    thread.start_new_thread(ps.run, ())

    timer = QtCore.QTimer()
    timer.timeout.connect(ps.update)
    timer.start(args.interval)


    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
