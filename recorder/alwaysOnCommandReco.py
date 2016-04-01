# This Python file uses the following encoding: utf-8
import numpy as np
import sys
import os
import re
import os.path
import time
import wave
import subprocess
import codecs
import scipy.io.wavfile
from cvsp_recorder_on import *
#from delay_and_sum_beamformer import *
import time
import threading
from collections import deque
from vad_functions import *

class AlwaysOnCommandReco():
    def __init__(self, recorder):
        self.started_talking = False
        self.wav_dir = 'wavs'
        self.mfcc_dir = 'mfcc'
        self.rec_dir = 'rec'
        self.bin_dir = '../bin/linux_x86_64'
        self.hcopy_cfg = '../configs/hcopy_voxforge.cfg'
        self.models = '../models/german/voxforge_german/hmmdefs'
        self.models_rate = 16000
        self.dictionary = '../dict/mobot_cmds_words.dict'
        self.model_list = '../models/german/voxforge_german/tiedlist'
        self.wav_file = ''
        # Vite params
        self.hvite_cfg = '../configs/HVite.config'
        self.asr_wordnet = '../lm/mobot_demo_german/mobot_commands.wdnet'
        self.classes = '../models/german/mobot_demo_global_mllr_adaptation_loo_2_adapt/classes_32'
        self.xforms = '../models/german/mobot_demo_global_mllr_adaptation_loo_2_adapt/xforms'
        # Framing parameters
        self.asr_frame_dur = 2.5
        self.asr_frame_shift_time = 0.6
        self.vad_frame_time = 0.5
        self.threads_die_now = False
        self.CR = recorder
        self.max_recent_rec_results = 3
        self.recent_rec_results = deque(self.max_recent_rec_results*' ', self.max_recent_rec_results)
        self.rec_output = ''
        self.file_queue = deque()
        self.times_queue = deque()
        self.rec_output_changed = False
        self.read_output = threading.Event()
        self.read_output.set()
	self.use_beamforming = True
	
	# Increase robustness by requesting two continuous segments to give the same result
	# Makes sense when no vad is applied
        self.increased_robustness = True

	# Apply voice activity detection
	self.use_vad = False

        self.s_thread = None

        self.clear()

    def clear(self):
        if False:
            for d in [self.wav_dir, self.rec_dir, self.mfcc_dir]:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        os.remove(os.path.join(d, f))

    def save_wave(self, start_buffer, end_buffer):
        if not os.path.exists(self.wav_dir):
            os.mkdir(self.wav_dir)
        wav_file_bname = os.path.join(self.wav_dir,'cvsp_recorder_{}_{}_{}'.format(time.strftime('%Y%m%d_%H%M%S'),start_buffer,end_buffer))
        self.wav_file = wav_file_bname + '.wav'
	if self.CR.n_channels>1 and self.use_beamforming:
	    xs, ys, ymin, ymax = self.CR.wave(start_buffer, end_buffer, beamforming=True)
	    y_out = ys
	else:
	    xs, ys, ymin, ymax = self.CR.wave(start_buffer, end_buffer)
	    if self.CR.n_channels>1:
	        y_out = ys[:, 0]
	    else:
	    	y_out = ys
	
        scipy.io.wavfile.write(self.wav_file,self.CR.rate,y_out)
	if self.CR.rate>self.models_rate:
	    subprocess.check_output(['sox', self.wav_file, '-r', str(self.models_rate), wav_file_bname+'_16k.wav'])
	    self.wav_file = wav_file_bname + '_16k.wav';

        return self.wav_file

    def set_rec_output(self, rec_output):
	if not self.increased_robustness:
	    self.rec_output = rec_output
	    print rec_output
	else:
  	    if self.recent_rec_results[-1]==rec_output:
		self.rec_output = rec_output
		self.file_queue = deque()
		self.times_queue = deque()
		self.recent_rec_results = deque(self.max_recent_rec_results*' ', self.max_recent_rec_results)
            	print rec_output
	    else:
	        self.recent_rec_results.append(rec_output)

    def get_rec_output(self):
        #self.read_output.set()
        return self.rec_output

    def empty_rec_output(self):
        self.rec_output = ''

    def read_recognition_output(self, wav_file):
        rec_file = wav_file.replace('.wav','.rec').replace(self.wav_dir, self.rec_dir)
        rec = open(rec_file, 'r')
        words = []
        for ln in rec:
            ln = ln.rstrip('\r\n')
            ln_info = ln.split(' ')
            if len(ln_info) > 0:
                words.append(ln_info[0])

        rec_output = " ".join(words).decode('iso-8859-7')
        return rec_output

    def print_recognition_output(self, rec_output):
        print rec_output
        self.textbox.setText(self.latin2gr(rec_output))

    def recognize_wave(self,rec_type,wav_file):
        if not os.path.exists(self.mfcc_dir):
            os.mkdir(self.mfcc_dir)
        if not os.path.exists(self.rec_dir):
            os.mkdir(self.rec_dir)
        mfc_file = wav_file.replace('.wav','.mfc').replace(self.wav_dir, self.mfcc_dir)
        subprocess.check_output([os.path.join(self.bin_dir,'HCopy'), '-C', self.hcopy_cfg, wav_file, mfc_file])

        if rec_type == 0:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '200.0',
                                 '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.kws_wordnet, '-p',
                                 '0.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        elif rec_type == 1:
            output = subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-T', '1', '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '200.0',
                                 '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.asr_wordnet, '-p',
                                 '0.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        else:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '300.0',
                                 '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.kws_wordnet, '-p',
                                 '0.0', '-o','TM',self.dictionary, self.model_list, mfc_file])

	rout = ''
        if output.find('No tokens survived')<0:
	    rout = self.read_recognition_output(wav_file)
	
	return rout

    def start_recording(self):
        if not self.started_talking:
            self.CR.continuous_start_alsa()
            self.started_talking = True
	if self.use_vad:
	    self.v_thread = VadThread(self)
       	    self.v_thread.start()
	else:
	    self.s_thread = SpeechThread(self)
       	    self.s_thread.start()

        self.a_thread = AsrThread(self)
        self.a_thread.start()
        self.threads_die_now = False

    def end_recording(self):
        self.CR.continuous_end()
        self.started_talking = False
        self.threads_die_now = True

    def push_file(self,wav_file,end_frame):
        with threading.Lock():
            self.file_queue.append(wav_file)
            self.times_queue.append(end_frame)

class VadThread(threading.Thread):
    def __init__(self, rt_audio):
	threading.Thread.__init__(self)
	self.rt = rt_audio
	self.vad_start_frame = 0
	self.speech_start_frame = 0
	self.speech_end_frame = 0
	self.n_speech_frames = 0
	self.first_time = True

    def run_vad(self):
        while True:
            time.sleep(2*self.rt.vad_frame_time)
            if self.rt.threads_die_now:
                break
            curr_start = self.rt.CR.get_current_start()
	    
            curr_frame = int(curr_start / self.rt.CR.buffersize)

	    if curr_frame>100 and self.first_time:
		curr_frame = 100

	    xs, ys, ymin, ymax = self.rt.CR.wave(self.vad_start_frame, curr_frame, beamforming=True)


	    if self.first_time:
		
	        vout, zo = vadsohn(ys, self.rt.CR.rate, 'a')
		self.first_time = False
	    else:
		vout, zo = vadsohn(ys, zo, 'a')

	    if any(vout):
		if self.n_speech_frames==0:
		    self.speech_start_frame = self.vad_start_frame
		self.n_speech_frames += 1
		print self.n_speech_frames
		self.speech_end_frame = curr_frame
	    else:
		if self.n_speech_frames >= 3:
            	    wav_file = self.rt.save_wave(self.speech_start_frame, curr_frame)
                    self.rt.push_file(wav_file, curr_frame)
		self.n_speech_frames = 0

	    self.vad_start_frame = curr_frame + 1

    def run(self):
	self.run_vad()


class SpeechThread(threading.Thread):
    def __init__(self, rt_audio):
        threading.Thread.__init__(self)
        self.rt = rt_audio

    def save(self):
        window_length = int(self.rt.asr_frame_dur * self.rt.CR.rate / self.rt.CR.buffersize)
        self.rt.CR.frame_start = 0
        self.rt.CR.frame_end = self.rt.CR.frame_start + window_length - 1

        while True:
            time.sleep(self.rt.asr_frame_shift_time)
            if self.rt.threads_die_now:
                break
            #self.rt.read_output.wait(5)
            curr_start = self.rt.CR.get_current_start()

            #if curr_start < 0.01*self.rt.CR.rate:
            #    continue
            curr_frame = int(curr_start / self.rt.CR.buffersize)
	    f_start = curr_frame - window_length
  	    if f_start<0:
		if self.rt.CR.frame_start == 0:
		    continue
		else:
		    f_start += self.rt.CR.max_n_buffers
	    
	    self.rt.CR.frame_start = f_start
            wav_file = self.rt.save_wave(self.rt.CR.frame_start, curr_frame)
            self.rt.push_file(wav_file, curr_frame)
    def run(self):
        self.save()


class AsrThread(threading.Thread):
    def __init__(self, rt_audio):
        threading.Thread.__init__(self)
        self.rt = rt_audio
        self.paused = False

    def get_file(self):
        if self.rt.file_queue:
            return self.rt.file_queue.popleft(), self.rt.times_queue.popleft()
        else:
            return None, None

    def run(self):
        while True:
            if self.rt.threads_die_now:
                break
            wav_file, end_frame = self.get_file()
            if wav_file:
		print wav_file
                rec_output = self.rt.recognize_wave(1, wav_file)

            	self.rt.set_rec_output(rec_output)
            	with threading.Lock():
                    self.files = deque()
                    self.times = deque()
            time.sleep(0.04)


if __name__ == "__main__":
    CR = CvspRecorder()
    CR.setup_alsa()

    commandReco = AlwaysOnCommandReco(CR)
    commandReco.start_recording()

    counter = 0
    while counter < 10000000:
        time.sleep(0.2)
        output = commandReco.get_rec_output()
        #print "counter: {}, output: {}".format(counter, output)
        commandReco.empty_rec_output()
        counter += 1

    ### DISPLAY WINDOWS
    CR.close()
    sys.exit(code)

