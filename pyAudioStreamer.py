import pyaudio
import struct
import wave
import Queue

import numpy as np
import time

class PyAudioStreamer(object):
    ''' Interface between audio driver and DSP applications

    '''
    def __init__(self, CHUNK=44100, channels=2, sr=22050, INTERVAL=None):
        ''' Open a stream to pyaudio
        Args:
            channels    number of channels
            sr            sample rate
            isec        update interval
        '''
        self.CHUNK = CHUNK
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = channels
        self.RATE = sr
        
        # used in wave file streaming
        self.INTERVAL = INTERVAL # update interval in seconds

        self.pa = pyaudio.PyAudio()

        self.q_l = Queue.Queue() # concurrent Queue
        self.q_r = Queue.Queue() # concurrent Queue

        self.app_buffers = [] # list of buffers to populate
        self.stop = True

    def register(self, app_buffer):
        ''' Applications that need samples register their
            internal buffer
        '''
        self.app_buffers.append(app_buffer)

    def start(self, fn=None):
        ''' Start grabbing samples from system
        
        Args:
            fn:    If None, get from mic
                    If not None, get from the file
        '''
        
        if fn is None:
            self.stream = self.pa.open(format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK)
            
            self.stop = False
            while(self.stop is False):
                sample_bytes = self.stream.read(self.CHUNK)
                samples = struct.unpack('{}h'.format(self.CHANNELS*self.CHUNK), sample_bytes)
                samples = np.reshape(samples, (len(samples)/self.CHANNELS, self.CHANNELS))

                self.q_l.put(samples[:, 0])
                if self.CHANNELS == 2:
                    self.q_r.put(samples[:, 1])
    
                # populate app buffers
                for app_buffer in self.app_buffers:
                    app_buffer.extend((samples[:, 0], )) # add as a tuple block
    
            self.stream.stop_stream()
            self.stream.close()
            self.pa.terminate()
        else:
            wf = wave.open(fn, 'rb')
            self.RATE = wf.getframerate()
            self.CHANNELS = wf.getnchannels()
            self.CHUNK = int(self.INTERVAL * self.RATE)
            print "self.CHANNELS", self.CHANNELS
            print "self.CHUNK", self.CHUNK
            self.stop = False
            num_chunks = 0
            while(self.stop is False):
                sample_bytes = wf.readframes(self.CHUNK)
                print "len(sample_bytes)", len(sample_bytes)
                samples = struct.unpack('{}h'.format(self.CHANNELS*self.CHUNK), sample_bytes)
                samples = np.reshape(samples, (len(samples)/self.CHANNELS, self.CHANNELS))
                
                self.q_l.put(samples[:, 0])
                if self.CHANNELS == 2:
                    self.q_r.put(samples[:, 1])
    
                # populate app buffers
                for app_buffer in self.app_buffers:
                    app_buffer.extend((samples[:, 0], )) # add as a tuple block
                time.sleep(self.INTERVAL)
                num_chunks += 1
                print "num_chunks",num_chunks
    
    def stop(self):
        self.stop = True
