import collections

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore


class AudioApp(object):
    ''' super class for audio application
    '''

    def __init__(self):
        self.circular_buffer = collections.deque()
    
    def plot(self):
        pass

    def update(self):
        ''' Method to update graphical plots
        '''
        pass


