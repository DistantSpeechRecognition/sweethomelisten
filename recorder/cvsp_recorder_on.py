import matplotlib
matplotlib.use('TkAgg') # <-- THIS MAKES IT FAST!
import numpy
import pyaudio
import threading
import pylab
import time
import sys
import alsaaudio
from delay_and_sum_beamformer import *


class CvspRecorder:
    """Simple, cross-platform class to record from the microphone."""

    def __init__(self):
        """minimal garb is executed when class is loaded."""
	#self.input_device_index = 1
        self.buffersize = 2**9
        self.sec_to_record = .1
        self.threads_die_now = False
        self.new_audio = False
	self.n_channels = 8
	self.max_recording_time = 60
	self.rate = 16000
	self.buffersize = 160
        self.current_buffer = 0
        self.record_start_buffer = 0
        self.record_stop_buffer = 0
        self.frame_start = 0
        self.recording = False
        self.input_device_index = 0
        self.max_n_buffers = int(self.rate * self.max_recording_time / self.buffersize)
        self.max_nsamples = self.max_n_buffers * self.buffersize

	# Switch to either file or microphone streaming
	self.read_from_mics = 1
	self.audio_raw_file = 'test_tum.raw'

    def setup(self):
        """initialize sound card."""
        self.p = pyaudio.PyAudio()

        # Find the appropriate device: choose default input device if no multichannel input card is available
        n_devices = self.p.get_device_count()
        for dc in range(0, n_devices):
            dev_info = self.p.get_device_info_by_index(dc)
            n_channels = dev_info['maxInputChannels']
            if n_channels>self.n_channels and n_channels<9:
                self.input_device_index = dc
                self.n_channels = n_channels
                self.rate = int(dev_info['defaultSampleRate'])
	

        print self.n_channels, self.input_device_index, self.rate
        self.max_n_buffers = int(self.rate * self.max_recording_time / self.buffersize)
        self.max_nsamples = self.max_n_buffers * self.buffersize
        self.chunks_to_record = int(self.max_nsamples/self.buffersize)
        self.audio = numpy.zeros((self.max_nsamples,self.n_channels), dtype=numpy.int16)

    def setup_alsa(self):
	self.card = "hw:CARD=Mod"
	#self.card = "default"
	self.inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, self.card)
	self.inp.setchannels(self.n_channels)
	self.inp.setrate(self.rate)
	self.inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	self.inp.setperiodsize(self.buffersize)
	
    def close(self):
        """cleanly back out and release sound card."""
        if hasattr(self, 'in_stream'):
            self.in_stream.close()
        if hasattr(self, 'p'):
            self.p.terminate()

    ### RECORDING AUDIO ###
    def get_audio(self):
        """get a single buffer size worth of audio."""
        audio_string = self.in_stream.read(self.buffersize)
        return numpy.fromstring(audio_string, dtype=numpy.int16)

    def is_recording(self):
        return self.recording

    def pause(self):
        self.do_record = False
        self.in_stream.stop_stream()
        print self.do_record

    def restart(self):
        self.do_record = True
        self.in_stream.start_stream()
        print self.do_record

    def get_current_buffer(self):
	lock = threading.Lock()
        with lock:
	    cb = self.current_buffer
        return cb

    def get_current_start(self):
	return self.current_start

    def do_talk(self):
        self.record_start_buffer = self.current_buffer
        #print self.record_start_buffer
        return self.current_buffer

    def stop_talking(self):
        self.record_stop_buffer = self.current_buffer
        self.audio = numpy.zeros([self.max_nsamples,self.n_channels],dtype=numpy.int16)
        #self.audio = numpy.zeros([self.max_nsamples,6],dtype=numpy.int16)
        self.current_buffer = 0
        return self.record_stop_buffer

    def record_alsa(self):
	print "Started recording..."
	while True:
	    if self.threads_die_now:
		break
	    while True:
	    	if self.threads_die_now:
		    break
	    	time.sleep(0.001)
		l, data = self.inp.read()
		if l>0:
		    frame = numpy.fromstring(data, dtype=numpy.int16)
		    if self.current_start+l>self.max_nsamples:
		 	self.current_start = 0
        		#self.audio = numpy.zeros((self.max_nsamples,self.n_channels), dtype=numpy.int16)
		    self.audio[self.current_start:self.current_start+l,:] = frame.reshape(l, self.n_channels)
		    self.current_start = self.current_start + l
		    #self.current_buffer += 1
		    #print self.current_buffer
		    time.sleep(.001)
		
    def record(self):
	self.in_stream = self.p.open(format=pyaudio.paInt16,channels=self.n_channels,rate=self.rate,input=True,input_device_index=self.input_device_index,frames_per_buffer=self.buffersize)

        """record secToRecord seconds of audio."""
        while True:
            if self.threads_die_now:
                break
            while True:
                if self.threads_die_now:
                    break
		try:
		    r = self.get_audio()
                    	#r = self.get_audio(in_stream)
                    j = self.current_buffer % self.max_n_buffers

                    self.audio[j*self.buffersize:(j+1)*self.buffersize,:] = r.reshape(self.buffersize,self.n_channels)
		    self.current_buffer += 1
		    print self.current_buffer, self.max_n_buffers, j
		except:
		    print "Unexpected error:", sys.exc_info()[0]
		    print "Finishing"
		    self.n_errors += 1
	    	    self.in_stream.stop_stream()
		    self.in_stream.close()
		    if self.n_errors < 500:
			self.record()
		    else:
		    	self.p.terminate()   
			raise
                #print "Recorder:", self.current_buffer, j
                #            s = r.reshape(self.buffersize,self.n_channels)
                # #selected_channels = s[:,16:22]
                #        self.audio[j*self.buffersize:(j+1)*self.buffersize,0:6] = selected_channels.copy()
                #self.audio[(j+self.max_n_buffers)*self.buffersize:(j+1+self.max_n_buffers)*self.buffersize,:] = \
                #    self.audio[j*self.buffersize:(j+1)*self.buffersize,:].copy()
                while not self.do_record:
                    time.sleep(0.1)
                    print in_stream.is_stopped()

        self.p.close(self.in_stream)


    def read_from_raw_file(self):
	print "Started reading from raw..."
	fraw = open(self.audio_raw_file,'rb')
        while True:
            if self.threads_die_now:
		fraw.close()
                break
	    sleep_time = float(self.buffersize)/(1.5*self.rate)
            time.sleep(sleep_time)
            data = fraw.read(self.buffersize*self.n_channels)
	    
	    if len(data)>0:
	        frame = numpy.fromstring(data, dtype=numpy.int16)
	        l = frame.shape[0]/self.n_channels
                if self.current_start+l>self.max_nsamples:
         	    self.current_start = 0
		    self.audio[self.current_start:self.current_start+l,:] = frame.reshape(l, self.n_channels)
                    self.current_start = self.current_start + l
		else:
		    self.audio[self.current_start:self.current_start+l,:] = frame.reshape(l, self.n_channels)
		    self.current_start = self.current_start + l


    def continuous_start_alsa(self):
        """CALL THIS to start running forever."""
        self.recording = True
        #self.audio = numpy.empty([2*self.max_nsamples,6],dtype=numpy.int16)
	if self.read_from_mics ==1:
            self.t = threading.Thread(target=self.record_alsa)
	else:
	    self.t = threading.Thread(target=self.read_from_raw_file)
	self.current_buffer = 0
	self.current_start = 0
        self.do_record = True
        self.threads_die_now = False
	self.n_errors = 0
        self.audio = numpy.zeros((self.max_nsamples,self.n_channels), dtype=numpy.int16)
        self.t.start()

    def continuous_start(self):
        """CALL THIS to start running forever."""
        self.recording = True
        #self.audio = numpy.empty([2*self.max_nsamples,6],dtype=numpy.int16)
        self.t = threading.Thread(target=self.record)
	self.current_buffer = 0
        self.do_record = True
        self.threads_die_now = False
	self.n_errors = 0
        self.audio = numpy.zeros((self.max_nsamples,self.n_channels), dtype=numpy.int16)
        self.t.start()

    def continuous_end(self):
        """shut down continuous recording."""
        self.recording = False
        self.frame_start = 0
        self.frame_end = 0
        self.threads_die_now = True
        #self.current_buffer = 0


    ### MATH ###

    def downsample(self,data,mult):
        """Given 1D data, return the binned average."""
        overhang=len(data)%mult
        if overhang: data=data[:-overhang]
        data=numpy.reshape(data,(len(data)/mult,mult))
        data=numpy.average(data,1)
        return data


    def fft(self,data=None,trimBy=10,logScale=False,divBy=100):
        if data==None:
            data=self.audio.flatten()
        left,right=numpy.split(numpy.abs(numpy.fft.fft(data)),2)
        ys=numpy.add(left,right[::-1])
        if logScale:
            ys=numpy.multiply(20,numpy.log10(ys))
        xs=numpy.arange(self.BUFFERSIZE/2, dtype=float)
        if trimBy:
            i=int((self.BUFFERSIZE/2)/trimBy)
            ys=ys[:i]
            xs=xs[:i]*self.RATE/self.BUFFERSIZE
        if divBy:
            ys=ys/float(divBy)
        return xs,ys

    def wave(self,start_buffer,end_buffer, beamforming=False):
        #print "Frame buffers: ", start_buffer, end_buffer
        #print "bufs1: {} {}".format(start_buffer, end_buffer)
	#with threading.Lock():
	if start_buffer >= self.max_n_buffers-1:
            start_buffer %= self.max_n_buffers
        if end_buffer >= self.max_n_buffers-1:
            end_buffer %= self.max_n_buffers
        #print "bufs2: {} {}".format(start_buffer, end_buffer)
        #print "Audio MAtrix Indices: ",(start_buffer+1)*self.buffersize, (end_buffer+1)*self.buffersize
        if end_buffer > start_buffer:
            #with threading.Lock():
            ys = self.audio[(start_buffer+1)*self.buffersize:(end_buffer+1)*self.buffersize, :].copy()
        #ys = numpy.random.randint(-300, 300, size=(90000,8))
        else:
	    ys = numpy.concatenate((self.audio[(start_buffer+1)*self.buffersize:self.max_nsamples, :],self.audio[0:(end_buffer+1)*self.buffersize, :])).copy()

        xs = numpy.arange(ys.shape[0],dtype=float)
        xs = xs[:] / self.rate
        ys_min = -1000
        ys_max = 1000
        if ys.shape[0] > 0:
            ys_min = numpy.amin(ys)
            ys_max = numpy.amax(ys)

        if beamforming:
            d=0.04
            theta_source = degreesTOradians(90)
            c = 340
            N_fft = xs.shape[0]
            Ybeamf= delay_and_sum_beamf(ys, self.n_channels, d, theta_source, c, N_fft, self.rate)
            ys = np.int16(Ybeamf)

        return xs, ys, ys_min, ys_max


    ### VISUALIZATION ###


    def wave_old(self,start_buffer=0):
        if start_buffer==0:
            current_buffer = self.current_buffer
            if self.current_buffer >= self.max_n_buffers-1:
                current_buffer %= self.max_n_buffers
                ys = self.audio[(current_buffer+1)*self.buffersize:(current_buffer+1+self.max_n_buffers)*self.buffersize,:].copy()
                xs = numpy.arange(ys.shape[0],dtype=float)
		#xs = numpy.arange(len(ys),dtype=float)
            else:
                ys = self.audio[0:current_buffer*self.buffersize,:].copy()
                current_sample = self.current_buffer*self.buffersize
                xs = numpy.arange(current_sample,dtype=float)
        else:
            current_buffer = self.current_buffer
            if current_buffer-start_buffer >= self.max_n_buffers:
                current_buffer %= self.max_n_buffers
                ys = self.audio[(current_buffer+1)*self.buffersize:(current_buffer+1+self.max_n_buffers)*self.buffersize,:].copy()
                #xs = numpy.arange(len(ys),dtype=float)
		xs = numpy.arange(ys.shape[0],dtype=float)
            else:
                if self.current_buffer >= self.max_n_buffers-1:
                    n_buffers = self.current_buffer - start_buffer
                    current_buffer %= self.max_n_buffers
                    current_end_buffer = current_buffer+1+self.max_n_buffers
                    ys = self.audio[(current_end_buffer - n_buffers - 1)*self.buffersize:current_end_buffer*self.buffersize,:].copy()
                    #xs = numpy.arange(len(ys),dtype=float)
		    xs = numpy.arange(ys.shape[0],dtype=float)
                else:
                    ys = self.audio[start_buffer*self.buffersize:self.current_buffer*self.buffersize,:].copy()
                    #xs = numpy.arange(len(ys),dtype=float)
		    xs = numpy.arange(ys.shape[0],dtype=float)

        xs = xs[:] / self.rate
        ys_min = -1000
        ys_max = 1000
        if ys.shape[0] > 0:
            ys_min = numpy.amin(ys)
            ys_max = numpy.amax(ys)
        return xs, ys, ys_min, ys_max


    ### VISUALIZATION ###

    def plotAudio(self):
        """open a matplotlib popup window showing audio data."""
        pylab.plot(self.audio.flatten())
        pylab.show()

