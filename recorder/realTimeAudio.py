# This Python file uses the following encoding: utf-8
import ui_plot
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
from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt
from cvsp_recorder_on import *
from delay_and_sum_beamformer import *
from vera import *
import time
import threading
from collections import deque
import alsaaudio
from selenium import webdriver
import shutil

class RealTimeAudio(ui_plot.Ui_win_plot):
    def __init__(self, cvsp_recorder):
        ui_plot.Ui_win_plot.__init__(self)
        self.started_talking = False
        self.plotting_on = False
        #self.model_list = '../models/greek/greekdb_all_14/tiedlist'
        self.wav_file = ''
        # Framing parameters
        self.kws_frame_dur = 2.0	# window of keyword spotting search
        self.asr_frame_dur = 4.0 	# window where it expects to find a command
        self.kw_cmd_dist = 0.0		# offset between kws and asr
        self.threads_die_now = False
        self.new_command = True
        self.command = ''
        self.CR = cvsp_recorder		# the recorder class (cvsp_recorder_on.py)
        self.phonemap_file = "latin2gr.map"	# used in Greek version
        self.rec_output = ''

        self.timer = QtCore.QTimer()
        self.timer.start(1.0)
        self.c = None
        self.s_thread = None

        self.clear()
	#self.experiment_directory='wavs/fileforrec'
        #if not os.path.exists(self.experiment_directory):
        #    os.mkdir(self.experiment_directory)
	#self.kws_decoding_graph_dir = 'exp/tri2a/graph_nosp_tgpr_kws_with_cmds'
	#self.asr_decoding_graph_dir = 'exp/tri2a/graph_nosp_tgpr_asr'
	#self.decoding_dir = 'exp/tri2a/decode_nosp_tgpr_all'
        phonemap = codecs.open(self.phonemap_file, encoding='utf-8')
        self.phonedict = {}
        for ln in phonemap:
            ln = ln.rstrip('\r\n')
            ln_phones = ln.split()

            if len(ln_phones) == 2:
                self.phonedict[ln_phones[0]] = ln_phones[1]
            else:
                self.phonedict[ln_phones[0]] = 'null'
        phonemap.close()

    def latin2gr(self, str_in):
        # substitude final signma with S capital
        str_in = re.sub('s$', 'S', str_in)
        str_in = re.sub('s ', 'S ', str_in)

        str_out = []
        for ph in list(str_in):
            if ph == " ":
                str_out.extend(" ")
                continue
            if self.phonedict[ph] != 'null':
#                str_out.extend(self.phonedict[ph].encode("utf-8"))
                str_out.extend(self.phonedict[ph])

        return ''.join(str_out)

    def attach_curve(self):
        self.c = Qwt.QwtPlotCurve()
        self.c.attach(self.qwtPlot)
        self.qwtPlot.setAxisScale(self.qwtPlot.yLeft, -32767, 32767)

    def setup(self, platform, language, working_vera):
	self.platform = platform	#retrieve the platform (kaldi or htk) parameter (chosen in main)
	self.language = language	#retrieve language parameter (chosen in main)
        self.wav_dir = 'wavs'		#directory where wav files will be stored
        self.mfcc_dir = 'mfcc'		#directory where mfc files will be stored
        self.rec_dir = 'rec'		#directory where recognition results will be stored
	self.working_vera = working_vera	# retrieve whether vera will e used or not
        if not os.path.exists(self.mfcc_dir):
            os.mkdir(self.mfcc_dir)
        if not os.path.exists(self.rec_dir):
            os.mkdir(self.rec_dir)

	if self.platform=="kaldi":	#kaldi parameters (rate, models, directories, etc.)
	    self.models_rate = 16000
	    self.language = 'english'
	    self.bin_dir = '/home/antigoni/spitakimou/kaldi/egs/wsj/mys5'
	    self.kws_decoding_graph_dir = 'exp/tri2a/graph_nosp_tgpr_kws_with_cmds'
            self.asr_decoding_graph_dir = 'exp/tri2a/graph_nosp_tgpr_asr'
            self.decoding_dir = 'exp/tri2a/decode_nosp_tgpr_all'
	    self.experiment_directory='wavs/fileforrec'
	    if not os.path.exists(self.experiment_directory):
            	os.mkdir(self.experiment_directory)

	else:		#HTK parameters (bin dir, models and relevant files, language, etc.)
            self.bin_dir = '../bin/linux_x86_64/'
	    if self.language=='greek':
        	self.hcopy_cfg = '../configs/hcopy.cfg'
		self.models_rate = 16000
	        self.models = '../models/greek/CONT1_Train_h_s63_u11771_MFCC_DAZO_FLAT_HTK/R3/hmm15/models'
	        self.dictionary = '../dict/greek_dictionary.dic'
	        self.model_list = '../models/greek/CONT1_Train_h_s63_u11771_MFCC_DAZO_FLAT_HTK/R3/hmm15/hmmlist'
	        self.hvite_cfg = '../configs/HVite.config'
        	self.kws_wordnet = '../lm/dirha_demo_greek/demo_activation.wdnet'
        	self.asr_wordnet = '../lm/dirha_demo_greek/demo_commands_short.wdnet'
        	self.classes = '../models/greek/CONT1_Train_h_s63_u11771_MFCC_DAZO_FLAT_HTK_adaptation/classes_32'
        	self.xforms = '../models/greek/CONT1_Train_h_s63_u11771_MFCC_DAZO_FLAT_HTK_adaptation/xforms_office_ch20_32'
	    elif self.language=='english':
	        self.hvite_cfg = '../configs/HVite.config'
        	self.hcopy_cfg = '../configs/hcopy_english.cfg'
		self.models_rate = 16000
	        #self.models = '../models/english/wsj_all_10000_32/hmmdefs'
	        self.models = '../models/english/wsj_si84_2750_8/hmmdefs'
	        self.dictionary = '../dict/reduced_english_dic.dic'
	        self.model_list = '../models/english/wsj_si84_2750_8/tiedlist'
        	self.kws_wordnet = '../lm/demo_english/demo_activation.wdnet'
        	self.asr_wordnet = '../lm/demo_english/demo_commands_short.wdnet'
        
        self.btnA.clicked.connect(self.start_recording)
        self.btnB.clicked.connect(self.end_recording)

    def reply_english(self):	# controls what will be played back to the user in english (depends on recognition results)
        rout = self.rec_output
        if rout.find('FAN') != -1:
            if (rout.find('SWITCH ON') != -1) or (rout.find('TURN ON') != -1):
                self.textbox.setText(self.switched_on_fan_text)
		self.play_back('../prompts/i_will_switch_on_the_fan.wav','action')
		self.current_action = 1
            elif (rout.find('SWITCH OFF') != -1)  or (rout.find('TURN OFF') != -1):
                self.textbox.setText(self.switched_off_fan_text)
		self.play_back('../prompts/i_will_switch_off_the_fan.wav','action')
		self.current_action = 2
        elif rout.find('LIGHT') != -1 or rout.find('LIGHTS') != -1:
            if rout.find('TURN ON') != -1 or rout.find('SWITCH ON') != -1:
                self.textbox.setText(self.switched_on_lights_text)
		self.play_back('../prompts/i_will_turn_on_the_lights.wav','action')
		self.current_action = 5
            elif rout.find('TURN OFF') != -1 or rout.find('SWITCH OFF') != -1:
                self.textbox.setText(self.switched_off_lights_text)
		self.play_back('../prompts/i_will_turn_off_the_lights.wav','action')
		self.current_action = 6
            elif rout.find('RAISE') != -1:
                self.textbox.setText(self.raise_lights_text)
		self.play_back('../prompts/i_will_raise_up_the_lights.wav','action')
		self.current_action = 3
            elif rout.find('LOWER') != -1:
                self.textbox.setText(self.lower_lights_text)
		self.play_back('../prompts/i_will_lower_the_lights.wav','action')
		self.current_action = 4
	else:
            self.textbox.setText('')

    def reply(self):
	if self.language=='english':
	    self.reply_english()
	else:
	    self.reply_greek()
	

    def reply_greek(self):	# the same for Greek playback
        rout = self.rec_output
        if rout.find('anemisthra') != -1:
            if (rout.find('anoije') != -1) or (rout.find('anace') != -1) or (rout.find(' energopoihse ')!= -1):
                self.textbox.setText(self.switched_on_fan_text)
		self.play_back('../prompts/anoigei_o_anemisthras.wav','action')
		self.current_action = 1
            elif (rout.find('kleise') != -1)  or (rout.find('sbhse') != -1) or (rout.find('apenergopoihse')!= -1):
                self.textbox.setText(self.switched_off_fan_text)
		self.play_back('../prompts/kleinei_o_anemisthras.wav','action')
		self.current_action = 2
        elif rout.find('fwta') != -1 or rout.find('fws') != -1 or rout.find('fwtismo') != -1:
            if rout.find('anoije') != -1 or rout.find('anace') != -1:
                self.textbox.setText(self.switched_on_lights_text)
		self.play_back('../prompts/anaboun_ta_fwta.wav','action')
		self.current_action = 5
            elif rout.find('kleise') != -1 or rout.find('sbhse') != -1:
                self.textbox.setText(self.switched_off_lights_text)
		self.play_back('../prompts/sbhnoun_ta_fwta.wav','action')
		self.current_action = 6
            elif rout.find('dynamwse') != -1:
                self.textbox.setText(self.raise_lights_text)
		self.play_back('../prompts/tha_dynamwsoun_ta_fwta.wav','action')
		self.current_action = 3
            elif rout.find('xamhlwse') != -1:
                self.textbox.setText(self.lower_lights_text)
		self.play_back('../prompts/tha_xamhlwsoun_ta_fwta.wav','action')
		self.current_action = 4
	#elif rout.find('xairetise') != -1:
	    #self.play_back('../prompts_correct_niki/xairetismos.wav')
	    #self.textbox.setText(self.xairetismos_text)
	elif rout.find('radio'):
	    if rout.find('anoije') != -1 and rout.find('melodia') != -1:
		self.textbox.setText(self.switchon_radio_text)
		self.play_back('../prompts/anoigw_to_radiofwno.wav','action')
                self.current_action = 7
	    elif rout.find('anoije') != -1 and rout.find('peper') != -1:
		self.textbox.setText(self.switchon_radio_text)
		self.play_back('../prompts/anoigw_to_radiofwno.wav','action')
                self.current_action = 8
	    elif rout.find('anoije') != -1 and rout.find('trito') != -1:
		self.textbox.setText(self.switchon_radio_text)
		self.play_back('../prompts/anoigw_to_radiofwno.wav','action')
                self.current_action = 9
	    elif rout.find('kleise') != -1:
		self.textbox.setText(self.switchoff_radio_text)
		self.play_back('../prompts/kleinw_to_radiofwno.wav','action')
                self.current_action = 10
	else:
            self.textbox.setText('')


    def play_back(self, wav_file, pbtype='simple'):
	self.p_thread = PlaybackThread(self, wav_file, pbtype)
	self.connect(self.p_thread, QtCore.SIGNAL('run_asr'), self.a_thread.start_asr)
	self.connect(self.p_thread, QtCore.SIGNAL('do_action'), self.action_implementation)
 	self.p_thread.start()

    def prompt(self):	# prompt playback
        self.textbox.setText(self.prompt_text)
	if self.language=='greek':
	    self.play_back('../prompts/pws_mporw_na_voithisw.wav', 'prompt')
	else:
            self.play_back('../prompts/how_can_i_help_you.wav', 'prompt')

    def plot_fft(self):
        if self.CR.new_audio is False:
            return
        xs, ys = self.CR.fft(logScale=True)
        self.c.setData(xs, ys)
        self.qwtPlot.replot()
        self.CR.new_audio = False

    def plot_wave(self, frame_start, frame_end):
        #if CR.new_audio is False:
        #    return
        xs, ys, ymin, ymax = self.CR.wave(frame_start,frame_end)
        self.c.setData(xs, ys[:,0])
        #self.qwtPlot.setAxisScale(self.qwtPlot.yLeft, min(ymin, -1000), max(ymax, 1000))
        self.qwtPlot.replot()
        #CR.new_audio = False

    def clear(self):
	if False:
	    for d in [self.wav_dir, self.rec_dir, self.mfcc_dir]:
	        if os.path.exists(d):
	            for f in os.listdir(d):
               	        os.remove(os.path.join(d, f))

    def save_wave(self, start_buffer, end_buffer):	#saves the wave file. If multiple channels, then saves the beamformed signal
        if not os.path.exists(self.wav_dir):		#else it saves the first channel
            os.mkdir(self.wav_dir)
        wav_file_bname = os.path.join(self.wav_dir,'cvsp_recorder_{}_{}_{}'.format(time.strftime('%Y%m%d_%H%M%S'),start_buffer,end_buffer))
        self.wav_file = wav_file_bname + '.wav'
        xs, ys, ymin, ymax = self.CR.wave(start_buffer, end_buffer)
        N = self.CR.n_channels

        y_out = []
        F_s = self.CR.rate
        if N>5:
            d=0.04
            theta_source = degreesTOradians(90)
            c = 340
            N_fft = xs.shape[0]
            Ybeamf= delay_and_sum_beamf(ys, N, d, theta_source, c, N_fft, F_s)
            y_out = np.int16(Ybeamf)
        else:
            y_out = ys[:, 0]

        scipy.io.wavfile.write(self.wav_file,F_s,y_out)

	if self.CR.rate>self.models_rate:
	    subprocess.check_output(['sox', self.wav_file, '-r', '16000', wav_file_bname+'_16k.wav'])
	    self.wav_file = wav_file_bname + '_16k.wav';

	return self.wav_file

    def read_recognition_output(self, wav_file):
	if self.platform=='kaldi':
	    return self.read_recognition_output_kaldi(wav_file)
	else:
	    return self.read_recognition_output_htk(wav_file)

    def read_recognition_output_kaldi(self, wav_file):
	rec_file_path = os.path.join(self.bin_dir,self.decoding_dir,'log/decode.1.log')
	filename=wav_file.replace('.wav','')
	filename=filename.replace('wavs/','')
	
	bash_cmd='cat '+rec_file_path+' | grep -m 1 ^'+filename+' | awk \'{for(i=2;i<=NF;i++){printf \"%s \", $i}; printf \"\\n\"}\' > '+filename+'.rec'
	print bash_cmd
	os.system(bash_cmd)
	
	rec_file = filename+'.rec'
	
        #rec_file = wav_file.replace('.wav','.rec').replace(self.wav_dir, self.rec_dir)
        rec = open(rec_file, 'r')
        #words = []
        #for ln in rec:
        #    ln = ln.rstrip('\r\n')
        #    ln_info = ln.split(' ')
        #    if len(ln_info) > 0:
        #        words.append(ln_info[0])
	rec_output = rec.readline()
        #rec_output = " ".join(words)
        return rec_output

    def read_recognition_output_htk(self, wav_file):
        rec_file = wav_file.replace('.wav','.rec').replace(self.wav_dir, self.rec_dir)
        rec = open(rec_file, 'r')
        words = []
        for ln in rec:
            ln = ln.rstrip('\r\n')
            ln_info = ln.split(' ')
            if len(ln_info) > 0:
                words.append(ln_info[0])
	if self.language=='greek':
            rec_output = " ".join(words).decode('iso-8859-7')
	else:
	    rec_output = " ".join(words)
        return rec_output

    def print_recognition_output(self, rec_output):
	if self.language=='english':
	    self.print_recognition_output_english(rec_output)	
	else:
	    self.print_recognition_output_greek(rec_output)	

    def print_recognition_output_english(self, rec_output):
        print rec_output
        self.textbox.setText(rec_output)

    def print_recognition_output_greek(self, rec_output):
        print rec_output
        self.textbox.setText(self.latin2gr(rec_output))

    def recognize_wave(self, rec_type, wav_file):
	start_t = time.time()

	if self.platform=='kaldi':
	    self.recognize_wave_kaldi(rec_type, wav_file)
	else:
	    if self.language=='greek':
	    	self.recognize_wave_htk_greek(rec_type, wav_file)
	    else:
		self.recognize_wave_htk_english(rec_type,wav_file)
	end_t = time.time()
	print "duration: {} wav_file: {}".format(end_t-start_t, wav_file)

    def recognize_wave_kaldi(self,rec_type,wav_file): 	#kaldi recognition function, setup differently for kws and asr
        mfc_file = wav_file.replace('.wav','.mfc').replace(self.wav_dir, self.mfcc_dir)
        #wav_file_16k = wav_file.replace('.wav','_16k.wav')
	wav_file_16k = wav_file.replace('wavs/','')
	#subprocess.check_output([os.system('rm wav/fileforrec/*; echo ')])
	bash1="rm -r "+self.experiment_directory+"/*; filename=`basename "+ wav_file_16k + " .wav`; echo \"$filename wavs/"+wav_file_16k +" \" > "+self.experiment_directory+"/wav.scp; echo \"$filename $filename\" > " +self.experiment_directory+"/spk2utt; echo \"$filename $filename\" > "+self.experiment_directory+"/utt2spk"
	#print(bash1)
	os.system(bash1)
	#subprocess.check_output([os.system('rm wav/fileforrec/*')])
	#subprocess.check_output([os.system('rm wav/fileforrec/*')])
	bash_mfccs=os.path.join(self.bin_dir,'steps/make_mfcc.sh ')+self.experiment_directory+' make_mfcc/fileforrec mfcc'
        #os.system(os.path.join(self.bin_dir,'steps/make_mfcc.sh '), self.experiment_directory,' make_mfcc/fileforrec ', 'mfcc')
	os.system(bash_mfccs)
	bash_cmvn=os.path.join(self.bin_dir,'steps/compute_cmvn_stats.sh ')+self.experiment_directory+' make_mfcc/fileforrec mfcc'
	os.system(bash_cmvn)
	#subprocess.check_output([os.path.join(self.bin_dir,'steps/compute_cmvn_stats.sh'), data/$x exp/make_mfcc/$x $mfccdir])
	#subprocess.check_output([os.path.join(self.bin_dir,'HCopy'), '-C', self.hcopy_cfg, wav_file, mfc_file])
        #subprocess.check_output(['HDecode','-C',hdecode_cfg,'-t','150.0','-H',models,'-l',rec_dir,'-w',lm,
        #                         '-s','15.0','-p','-4.0','-o','TM',dictionary,model_list,mfc_file])
        if rec_type == 0:
	    bash_kws=os.path.join(self.bin_dir,'steps/decode_kws.sh ')+os.path.join(self.bin_dir, self.kws_decoding_graph_dir)+' '+self.experiment_directory+' '+os.path.join(self.bin_dir,self.decoding_dir)
	    #subprocess.check_output([os.path.join(self.bin_dir,'steps/decode.sh '),os.path.join(self.bin_dir, self.kws_decoding_graph_dir), self.experiment_directory,  os.path.join(self.bin_dir,self.decoding_dir)])
	    os.system(bash_kws)

            #subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '150.0',
            #                     '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.kws_wordnet, '-p',
            #                     '-10.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        elif rec_type == 1:
	    bash_asr=os.path.join(self.bin_dir,'steps/decode_asr.sh ')+os.path.join(self.bin_dir, self.asr_decoding_graph_dir)+' '+self.experiment_directory+' '+os.path.join(self.bin_dir,self.decoding_dir)
	    #subprocess.check_output([os.path.join(self.bin_dir,'steps/decode.sh '),os.path.join(self.bin_dir, self.asr_decoding_graph_dir), self.experiment_directory,  os.path.join(self.bin_dir,self.decoding_dir)])
	    os.system(bash_asr)
            #subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '100.0',
            #                     '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.asr_wordnet, '-p',
            #                     '0.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        else:
	    bash_kws=os.path.join(self.bin_dir,'steps/decode_kws.sh ')+os.path.join(self.bin_dir, self.kws_decoding_graph_dir)+' '+self.experiment_directory+' '+os.path.join(self.bin_dir,self.decoding_dir)
            #subprocess.check_output([os.path.join(self.bin_dir,'steps/decode.sh '),os.path.join(self.bin_dir, self.kws_decoding_graph_dir), self.experiment_directory,  os.path.join(self.bin_dir,self.decoding_dir)])
            os.system(bash_kws)
	    #subprocess.check_output([os.path.join(self.bin_dir,'steps/decode.sh '),os.path.join(self.bin_dir, self.kws_decoding_graph_dir), self.experiment_directory,  os.path.join(self.bin_dir,self.decoding_dir)])
            #subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '100.0',
            #                     '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.kws_wordnet, '-p',
            #                     '-20.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        #subprocess.check_output(['HVite','-C',hvite_cfg,'-l',rec_dir,'-H',models,'-w',wordnet,
        #    '-p','-100.0','-o','TM',dictionary,model_list,mfc_file])

        #self.read_recognition_output()


    def recognize_wave_htk_greek(self,rec_type,wav_file):	#HTK recognition function, setup with different parameters for kws and asr 
        mfc_file = wav_file.replace('.wav','.mfc').replace(self.wav_dir, self.mfcc_dir)
        wav_file_16k = wav_file.replace('.wav','_16k.wav')
        subprocess.check_output([os.path.join(self.bin_dir,'HCopy'), '-C', self.hcopy_cfg, wav_file, mfc_file])
        #subprocess.check_output(['HDecode','-C',hdecode_cfg,'-t','150.0','-H',models,'-l',rec_dir,'-w',lm,
        #                         '-s','15.0','-p','-4.0','-o','TM',dictionary,model_list,mfc_file])
        if rec_type == 0:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '150.0',
                                 '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.kws_wordnet, '-p',
                                 '-10.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        elif rec_type == 1:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '100.0',
                                 '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.asr_wordnet, '-p',
                                 '0.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        else:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir,'-k','-J', self.classes, '-t', '100.0',
                                 '-J', self.xforms,'mllr1','-h','''*.mfc''','-H',self.models,'-w', self.kws_wordnet, '-p',
                                 '-20.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        #subprocess.check_output(['HVite','-C',hvite_cfg,'-l',rec_dir,'-H',models,'-w',wordnet,
        #    '-p','-100.0','-o','TM',dictionary,model_list,mfc_file])

        #self.read_recognition_output()

    def recognize_wave_htk_english(self,rec_type,wav_file):	#the same for English
        mfc_file = wav_file.replace('.wav','.mfc').replace(self.wav_dir, self.mfcc_dir)
        wav_file_16k = wav_file.replace('.wav','_16k.wav')
        subprocess.check_output([os.path.join(self.bin_dir,'HCopy'), '-C', self.hcopy_cfg, wav_file, mfc_file])
        #subprocess.check_output(['HDecode','-C',hdecode_cfg,'-t','150.0','-H',models,'-l',rec_dir,'-w',lm,
        #                         '-s','15.0','-p','-4.0','-o','TM',dictionary,model_list,mfc_file])
        if rec_type == 0:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir, '-t', '50.0',
                                 '-H',self.models,'-w', self.kws_wordnet, '-p',
                                 '-5.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        elif rec_type == 1:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir, '-t', '100.0',
                                 '-H',self.models,'-w', self.asr_wordnet, '-p',
                                 '0.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        else:
            subprocess.check_output([os.path.join(self.bin_dir,'HVite'), '-C', self.hvite_cfg,'-l', self.rec_dir, '-t', '100.0',
                                 '-H',self.models,'-w', self.kws_wordnet, '-p',
                                 '-20.0', '-o','TM',self.dictionary, self.model_list, mfc_file])
        #subprocess.check_output(['HVite','-C',hvite_cfg,'-l',rec_dir,'-H',models,'-w',wordnet,
        #    '-p','-100.0','-o','TM',dictionary,model_list,mfc_file])

        #self.read_recognition_output()





    def action_implementation(self):	#defines what action follows when a command is recognized
	time.sleep(0.5)
	if self.current_action < 7:
	    if self.working_vera:
	        vera(self.current_action)
	    print "doing something with vera"
	elif self.current_action ==7:
	    #driver = webdriver.Firefox()
	    #driver.get("http://www.e-radio.gr/Melodia-FM-992-Athens-i83/live")
	    #os.system('killall firefox &')
	    os.system('firefox http://www.e-radio.gr/Melodia-FM-992-Athens-i83/live &')
	elif self.current_action ==8:
            #driver = webdriver.Firefox()
	    #os.system('killall firefox &')
            os.system('firefox http://live24.gr/radio/pepper &')
	elif self.current_action ==9:
            #driver = webdriver.Firefox()
            #os.system('killall firefox &')
            os.system('firefox http://live24.gr/radio/generic.jsp?sid=1419 &')
	elif self.current_action ==10:
	    os.system('killall firefox &')
        rout = self.rec_output

    def action_recognition(self):
        rout = self.rec_output
        if rout.find('anemisthra') != -1:
            if (rout.find('anoije') != -1) or (rout.find('anace') != -1) or (rout.find(' energopoihse ')!= -1):
                vera(1)
            elif (rout.find('kleise') != -1)  or (rout.find('sbhse') != -1) or (rout.find('apenergopoihse')!= -1):
                vera(2)
        elif rout.find('fwta') != -1 or rout.find('fws') != -1 or rout.find('fwtismo') != -1:
            if rout.find('anoije') != -1 or rout.find('anace') != -1:
                vera(5)
            elif rout.find('kleise') != -1 or rout.find('sbhse') != -1:
                vera(6)
            elif rout.find('dynamwse') != -1:
                vera(3)
            elif rout.find('xamhlwse') != -1:
                vera(4)
	else:
            self.textbox.setText('')


    def play_wave_alsa(self,playwavefile):	#playback main function
	
	card = 'default'
	fplay = open(playwavefile,'rb')
	
	out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, device = card)
	out.setchannels(1)
	out.setrate(44100)
	out.setformat(alsaaudio.PCM_FORMAT_S16_LE)

	out.setperiodsize(160)
	
	data = fplay.read(320)
	while data:
		out.write(data)
		data = fplay.read(320)
	#bash_command='aplay ../prompts_correct_niki/'+playwavefile+' &'
        #os.system(bash_command)

    def play_wave(self):
        CHUNK = 1024
        if not os.path.exists(self.wav_file):
            return
        wf = wave.open('xairetismos.wav', 'rb')
        p = pyaudio.PyAudio()
        # open stream (2)
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(), output=True)

        data = wf.readframes(CHUNK)

        # play stream (3)
        while data != '':
            stream.write(data)
            data = wf.readframes(CHUNK)

        # stop stream (4)
        stream.stop_stream()
        stream.close()
        wf.close()
        # close PyAudio (5)
        p.terminate()

    def start_recording(self):
        if not self.started_talking:
            self.CR.continuous_start_alsa()
            self.started_talking = True
	    self.textbox.setText('')
        #t = threading.Thread(target=start_kws)
        #t.start()
            self.s_thread = SpeechThread(self)
	    self.a_thread = AsrThread(self)
            self.connect(self.s_thread, QtCore.SIGNAL("plotWave"), self.plot_wave)
            self.connect(self.s_thread, QtCore.SIGNAL("printOutput"), self.print_recognition_output)
            self.connect(self.s_thread, QtCore.SIGNAL('action'), self.action_recognition)
	    self.connect(self.s_thread, QtCore.SIGNAL('recognize'), self.a_thread.push_file)
            self.connect(self.a_thread, QtCore.SIGNAL('prompt'), self.prompt)
            self.connect(self.a_thread, QtCore.SIGNAL('reply'), self.reply)
            self.connect(self.a_thread, QtCore.SIGNAL('asr_on'), self.s_thread.pause_pushing)
            self.connect(self.a_thread, QtCore.SIGNAL('asr_off'), self.s_thread.resume_pushing)
            self.s_thread.start()
	    self.a_thread.start()
            self.threads_die_now = False
        #start_kws()
    
    def stop_recording(self):
        self.CR.continuous_end()
        self.started_talking = False
        self.threads_die_now = True

    def end_recording(self):
        if app.mouseButtons() == QtCore.Qt.NoButton:
            self.CR.continuous_end()
            self.started_talking = False
            self.threads_die_now = True

class PlaybackThread(QtCore.QThread):
    def __init__(self, rt_audio, wav_file, pbtype):
        QtCore.QThread.__init__(self)
        self.rt = rt_audio
	self.wav_file = wav_file
	self.pbtype = pbtype
	print wav_file

    def run(self):
	print self.wav_file
	if self.wav_file:
	    self.rt.play_wave_alsa(self.wav_file)
	    if self.pbtype=='prompt':
		print "sending signal to asr"
	    	self.emit(QtCore.SIGNAL('run_asr'), int(self.rt.CR.get_current_start()/self.rt.CR.buffersize))
	    elif self.pbtype=='action':
		print "sending signal to action implementation"
	    	self.emit(QtCore.SIGNAL('do_action'))
		


class SpeechThread(QtCore.QThread):
    def __init__(self, rt_audio):
        QtCore.QThread.__init__(self)
        self.rt = rt_audio
	self.asr_on = False
    
    def pause_pushing(self):
	self.asr_on = True

    def resume_pushing(self):
	self.asr_on = False
    
    def save_and_plot(self):
        window_length = int(self.rt.kws_frame_dur * self.rt.CR.rate / self.rt.CR.buffersize)
        self.rt.CR.frame_start = 0
        self.rt.CR.frame_end = self.rt.CR.frame_start + window_length - 1

        while True:
            time.sleep(0.2)
            if self.rt.threads_die_now:
                break
            curr_start = self.rt.CR.get_current_start()
	    if curr_start < 1000:
		continue
            curr_frame = int(curr_start / self.rt.CR.buffersize)
	    print curr_frame

	    if not self.asr_on:
		wav_file = self.rt.save_wave(self.rt.CR.frame_start, min(self.rt.CR.frame_end, curr_frame))
	    	#print "wav_file in save_and_plot: {}".format(wav_file)
	    	print "wav0: {}".format(wav_file)
	    	self.emit(QtCore.SIGNAL('recognize'), wav_file, min(self.rt.CR.frame_end, curr_frame))
            
	    if curr_frame>self.rt.CR.frame_end:
		if curr_frame - self.rt.CR.frame_end < int(0.2*window_length):
	            self.rt.CR.frame_start += int(window_length*0.5)
		else:
		    self.rt.CR.frame_start = curr_frame - int(window_length*0.1)
                self.rt.CR.frame_end = self.rt.CR.frame_start + window_length - 1
	    elif self.rt.CR.frame_end > curr_frame + window_length:
		self.rt.CR.frame_start = curr_frame
                self.rt.CR.frame_end = self.rt.CR.frame_start + window_length - 1
            self.emit(QtCore.SIGNAL('plotWave'), self.rt.CR.frame_start, min(self.rt.CR.frame_end, curr_frame))

    def run(self):
        self.save_and_plot()

class AsrThread(QtCore.QThread):
    def __init__(self, rt_audio):
        QtCore.QThread.__init__(self)
	self.files = deque()
	self.times = deque()
	self.rt = rt_audio
	self.paused = False
	self.end_frame = 0
        self.asr_window_length = int(self.rt.asr_frame_dur * self.rt.CR.rate / self.rt.CR.buffersize)
        self.asr_offset = int(self.rt.kw_cmd_dist * self.rt.CR.rate / self.rt.CR.buffersize)

    def push_file(self, file_name, end_frame):
	if not self.paused and (end_frame>self.end_frame or end_frame<self.end_frame-1000):
	    print "In push file: {}".format(file_name)
	    self.files.append(file_name)
	    self.times.append(end_frame)

    def get_file(self):
	if self.files:
	    return self.files.popleft(), self.times.popleft()
	else:
	    return None, None

    def start_asr(self, end_frame):
    	wav_ready = False
	while True:
	    current_frame = int(self.rt.CR.get_current_start() / self.rt.CR.buffersize)
	    if current_frame < end_frame:
		window_start = end_frame + self.asr_offset - self.rt.CR.max_n_buffers
		if window_start<0:
		    window_start = end_frame + self.asr_offset
		    window_end = window_start + self.asr_window_length - self.rt.CR.max_n_buffers
		else:
		    window_end = window_start + self.asr_window_length
	    else:
                window_start = end_frame + self.asr_offset
                window_end = window_start + self.asr_window_length

	    if current_frame>window_end:
                wav_file = self.rt.save_wave(window_start, window_end)
	    	print "wav1: {}".format(wav_file)
                self.rt.recognize_wave(1, wav_file)
                self.rt.rec_output = self.rt.read_recognition_output(wav_file)
                #shutil.copyfile(wav_file, wav_file.replace('.wav','_{}.wav'.format(self.rt.rec_output)))
		
                self.emit(QtCore.SIGNAL('reply'))
		self.paused = False
                self.emit(QtCore.SIGNAL('asr_off'), self.rt.s_thread.resume_pushing)
                print "Recognition output: {}".format(self.rt.rec_output)
		self.end_frame = window_end
                break
	    time.sleep(0.02)

    def run(self):
	while True:
            if self.rt.threads_die_now:
                break
	    wav_file, end_frame = self.get_file()
	    if wav_file:
	    	print "wav2: {}".format(wav_file)
                self.rt.recognize_wave(0, wav_file)
                rec_output = self.rt.read_recognition_output(wav_file)
		if (rec_output.find("spitakimoy") != -1) or (rec_output.find("SWEET HOME") != -1):	#search for kws output
                    print "Found activation keyword ... starting ASR"					#if keyword found, it starts asr
		    self.paused = True
                    self.emit(QtCore.SIGNAL('asr_on'), self.rt.s_thread.pause_pushing)
		    self.files = deque()
		    print self.files
                    self.emit(QtCore.SIGNAL('prompt'), self.rt.prompt)
	    time.sleep(0.02)


if __name__ == "__main__":
    language = "english"
    platform = "HTK"
    vera_on = True
    app = QtGui.QApplication(sys.argv)

    win_plot = ui_plot.QtGui.QMainWindow()
    #uiplot = ui_plot.Ui_win_plot()
    #uiplot.setupUi(win_plot)
    CR = CvspRecorder()
    CR.setup_alsa()

    RT = RealTimeAudio(CR)
    RT.setupUi(win_plot, language)
    RT.attach_curve()
    RT.setup(platform, language, vera_on)

    #uiplot.btnC.clicked.connect(lambda: uiplot.timer.setInterval(10.0))
    #uiplot.btnD.clicked.connect(lambda: uiplot.timer.setInterval(1.0))

    ### DISPLAY WINDOWS
    win_plot.show()
    code = app.exec_()
    CR.close()
    sys.exit(code)

