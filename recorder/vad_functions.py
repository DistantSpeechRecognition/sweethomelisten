#!/usr/bin/python

from numpy import *
import scipy
import scipy.io as sio
import numpy.testing
import scipy.special as sp

def vadsohn(*args):
    # function [vs,zo]=vadsohn(si,fsz,m,pp)
    # read input
    nargin = len(args)
    si = args[0]     # signal vector
    fsz = args[1]     # sample frequency
    m = args[2]     # mode

    if type(fsz) is dict:
        fs = fsz['fs']
        qq = fsz['qq']
        qp = fsz['qp']
        ze = fsz['ze']
        s = zeros(len(fsz['si'])+len(si))
        s[0:len(fsz['si'])] = fsz['si']
        s[len(fsz['si']):] = si.copy()
    else:
        fs = fsz
        s = si.copy()
        # default algorithm constants
        qq = {
            'of': 2,   # overlap factor = (fft length)/(frame increment)
            'pr': 0.7,    # Speech probability threshold
            'ts': 0.3,  # mean talkspurt length (100 ms)
            'tn': 0.05, # mean silence length (50 ms)
            'ti': 10e-3,   # desired frame increment (10 ms)
            'ri': 0,       # round ni to the nearest power of 2
            'ta': 0.396,    # Time const for smoothing SNR estimate = -tinc/log(0.98) from [2]
            'gx': 1000,     # maximum posterior SNR = 30dB
            'gz': 1e-4,     # minimum posterior SNR = -40dB
            'xn': 0        # minimum prior SNR = -Inf dB
        }
        if nargin>3:
            pp = args[3]
            qp = pp # save for estnoisem call
            for field in qq.keys():
                if field in pp.keys():
                    qq[field]=pp[field]
        else:
            qp = {}

    # derived algorithm constants
    if qq['ri']:
        ni = nextpow2(ti*fs*sqrt(0.5))**2
    else:
        ni = int(round(qq['ti']*fs))    # frame increment in samples

    tinc=float(ni)/fs          # true frame increment time
    a=exp(-tinc/qq['ta']) # SNR smoothing coefficient
    gmax=qq['gx']           # max posterior SNR = 30 dB
    kk=sqrt(2*pi)   # sqrt(8)*Gamma(1.5) - required constant
    xn=qq['xn']           # floor for prior SNR, xi
    gz=qq['gz']            # floor for posterior SNR
    a01=tinc/qq['tn']     # a01=P(silence->speech)
    a00=1-a01          # a00=P(silence->silence)
    a10=tinc/qq['ts']     # a10=P(speech->silence)
    a11=1-a10          # a11=P(speech->speech)
    b11=a11/a10
    b01=a01/a00
    b00=a01-a00*a11/a10
    b10=a11-a10*a01/a00
    prat=a10/a01       # P(silence)/P(speech)
    lprat=log(prat)

    no=int(round(qq['of']))                                   # integer overlap factor
    nf=ni*no           # fft length
    nd=int(floor(float(ni)*(no-1)/2)) # output delay relative to start of frame
    w=hamming(nf+1)   #w(end)=[]  # for now always use hamming window
    w=w[:-1]
    w=w/sqrt(sum(w[0:nf:ni]**2))      	# normalize to give overall gain of 1
    ns=len(s)
    y=enframe(s,w,ni)
    yf=rfft(y,nf,1)
    if not shape(yf)[0]:                                  # no data frames
        vs=[]
        nr=0
        nb=0
    else:
        yp=yf * conjugate(yf)             # power spectrum of input speech
        (nr,nf2) = shape(yp)              # number of frames
        nb=ni*nr

        if type(fsz) is dict:
            dp, ze = estnoisem(yp, ze)
            xu = fsz['xu']
            lggami = fsz['gg']
            nv = fsz['nv']
        else:
            dp, ze = estnoisem(yp,tinc,qp)     # estimate the noise using minimum statistics
            xu=1                              # dummy unsmoothed SNR from previous frame [2](53)++
            lggami=0                          # initial prob ratio
            nv=0
        gam = max_complex(min_complex(yp/dp,array([gmax])),array([gz]))       # gamma = posterior SNR [2](10)
        prsp=array(zeros((nr,1)),dtype=complex)                   # create space for prob ratio vector
        for i in range(0,nr):                          # loop for each frame
            gami=gam[i,:].copy()                  # gamma(i) = a posteriori SNR [2](10)
            xi=a*xu+(1-a)*max_complex(gami-1,array([xn]))   # xi = smoothed a priori SNR [2](53)
            xi1=1+xi
            v=0.5*xi*gami/xi1            # note that this is 0.5*vk in [2]
            lamk=2*v-log(xi1)              # log likelihood ratio [1](3)
            lami=numpy.sum(lamk[1:nf2])/(nf2-1)  # mean log LR omitting DC term [1](4)

            if lggami<0:                     # avoid overflow in calculating [1](11)
                lggami=lprat+lami+log(b11+b00/(a00+a10*exp(lggami)))
            else:
                lggami=lprat+lami+log(b01+b10/(a10+a00*exp(-lggami)))
            if lggami<0:
                gg=exp(lggami)
                prsp[i]=gg/(1+gg)
            else:
                prsp[i]=1/(1+exp(-lggami))

            gi=(0.277+2*v)/gami           # accurate to 0.02 dB for v>0.5
            mv=v<0.5
            if any(mv):                  # only calculate Bessel functions for v<0.5
                vmv=v[mv]
                gi[mv]=kk*sqrt(vmv)*((0.5+vmv)*sp.iv(0,vmv)+vmv*sp.iv(1,vmv))/(gami[mv]*exp(vmv)) # [2](7)

            xu=gami*gi**2                 # unsmoothed prior SNR % [2](53)

        # output
        nc=ns-nd-nb     # include tail if no output state desired
        vs=array(zeros((nd+nb+nc,1)))
        vs[nd+array(range(0,nb),dtype=int),0]=reshape(tile(prsp,(1,ni)),nb)
        vs[0:nd,0]=vs[nd,0]        # replicate start
        vs[nd+nb+1:,0]=vs[nd+nb,0] # replicate end
        vs=vs[:,0]>qq['pr']

    # Save current state
    zo = {}
    zo['si'] = s[nd+nb:].copy()
    zo['fs'] = fs
    zo['qq'] = qq
    zo['qp'] = qp
    zo['ze'] = ze
    zo['xu'] = xu
    zo['gg'] = lggami
    zo['nv'] = nv + nd + nb

    return vs, zo

def enframe(*args):

    # ENFRAME split signal up into (overlapping) frames: one per row. [F,T]=(X,WIN,INC)
    #
    # Usage:  (1) f=enframe(x,n)     # split into frames of len n
    #
    #         (2) win=hamming(4*n,'periodic')
    #             f=enframe(x,win,n)     # use a 75# overlapped Hamming window of len 4*n
    #
    #  Inputs:   x    input signal
    #          win    window or window len in samples
    #          inc    frame increment in samples
    #            m    mode input:
    #                  'z'  zero pad to fill up final frame
    #                  'r'  reflect last few samples for final frame
    #                  'A'  calculate window times as the centre of mass
    #                  'E'  calculate window times as the centre of energy
    #
    # Outputs:   f    enframed data - one frame per row
    #            t    fractional time in samples at the centre of each frame
    #            w    window function used
    #
    # By default, the number of frames will be rounded down to the nearest
    # integer and the last few samples of x() will be ignored unless its len
    # is lw more than a multiple of inc. If the 'z' or 'r' options are given,
    # the number of frame will instead be rounded up and no samples will be ignored.
    #
    # Example of frame-based processing:
    #          INC=20       						# set frame increment in samples
    #          NW=INC*2     						# oversample by a factor of 2 (4 is also often used)
    #          S=cos((0:NW*7)*6*pi/NW)				# example input signal
    #          W=sqrt(hamming(NW),'periodic'))  	# sqrt hamming window of period NW
    #          F=enframe(S,W,INC)               	# split into frames
    #          ... process frames ...
    #          X=overlapadd(F,W,INC)               # reconstitute the time waveform (omit "X=" to plot waveform)

    # Bugs/Suggestions:
    #  (1) Possible additional mode options:
    #        'u'  modify window for first and last few frames to ensure WOLA
    #        'a'  normalize window to give a mean of unity after overlaps
    #        'e'  normalize window to give an energy of unity after overlaps
    #        'wm' use Hamming window
    #        'wn' use Hanning window
    #        'x'  include all frames that include any of the x samples

    #	   Copyright (C) Mike Brookes 1997-2012
    #      Version: $Id: enframe.m 1710 2012-03-27 06:49:59Z dmb $
    #
    #   VOICEBOX is a MATLAB toolbox for speech processing.
    #   Home page: http://www.ee.ic.ac.uk/hp/staff/dmb/voicebox/voicebox.html
    #
    #################################################################################
    #   This program is free software you can redistribute it and/or modify
    #   it under the terms of the GNU General Public License as published by
    #   the Free Software Foundation either version 2 of the License, or
    #   (at your option) any later version.
    #
    #   This program is distributed in the hope that it will be useful,
    #   but WITHOUT ANY WARRANTY without even the implied warranty of
    #   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #   GNU General Public License for more details.
    #
    #   You can obtain a copy of the GNU General Public License from
    #   http://www.gnu.org/copyleft/gpl.html or by writing to
    #   Free Software Foundation, Inc.,675 Mass Ave, Cambridge, MA 02139, USA.
    #################################################################################

    # get inputs
    nargin = len(args)
    x = args[0]

    nx = len(x)

    if nargin < 2:
        win = nx
    else:
        win = args[1]

    if nargin < 4:
        m = ''

    if type(win) is int:
        nwin = 1
        lw = win
        w = ones((1, lw))
    else:
        lw = len(win)
        nwin = lw
        w = win

    if (nargin < 3):
        inc = lw
    else:
        inc = args[2]

    nli = nx - lw + inc
    nf = int(round((nli) / inc))
    na = nli - inc * nf
    f = zeros((nf, lw))
    indf = inc * arange(nf)
    inds = arange(0,lw)
    i = tile(indf,(lw,1)) + tile(inds,(nf,1)).T
    f = x[i]

#if nargin>3 && (any(m=='z') || any(m=='r')) && na>0
#    if any(m=='r')
#        ix=1+mod(nx-na:nx-na+lw-1,2*nx)
#        f(nf+1,:)=x(ix+(ix>nx).*(2*nx+1-2*ix))
#    else:
#        f(nf+1,1:na)=x(1+nx-na:nx)

#    nf=size(f,1)

    if (nwin > 1):  # if we have a non-unity window
        w = tile(w,(nf,1))
        f = f * w.T

#if nargout>1
#    if any(m=='E')
#        t0=sum((1:lw).*w.^2)/sum(w.^2)
#    else:if any(m=='E')
#        t0=sum((1:lw).*w)/sum(w)
#    else:
#        t0=(1+lw)/2

#    t=t0+inc*(0:(nf-1)).'
    return f.T

#def hamming(n):
  # SYM_WINDOW   Symmetric generalized cosine window.
  # SYM_WINDOW Returns an exactly symmetric N point generalized cosine 
  # window by evaluating the first half and then flipping the same samples
  # over the other half.

#  if not n%2:
#    # Even length window
#    half = n/2
#    x = arange(0,half,dtype=float) / (n-1)
#    w = 0.54 - 0.46*cos(2*pi*x)
#    w = hstack((w,w[::-1]))
#  else:
#    # Odd length window
#    half = (n+1)/2
#    x = arange(0,half,dtype=float) / (n-1)
#    w = 0.54 - 0.46*cos(2*pi*x)
#    w = hstack((w,w[len(w)-1:0:-1]))

#  return w

def rfft(x,n,d):
    #function y=rfft(x,n,d)
    #RFFT     Calculate the DFT of real data Y=(X,N,D)
    # Data is truncated/padded to length N if specified.
    #   N even:	(N+2)/2 points are returned with
    # 			the first and last being real
    #   N odd:	(N+1)/2 points are returned with the
    # 			first being real
    # In all cases fix(1+N/2) points are returned
    # D is the dimension along which to do the DFT



    #      Copyright (C) Mike Brookes 1998
    #      Version: $Id: rfft.m 713 2011-10-16 14:45:43Z dmb $
    #
    #   VOICEBOX is a MATLAB toolbox for speech processing.
    #   Home page: http://www.ee.ic.ac.uk/hp/staff/dmb/voicebox/voicebox.html
    #
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #   This program is free software; you can redistribute it and/or modify
    #   it under the terms of the GNU General Public License as published by
    #   the Free Software Foundation; either version 2 of the License, or
    #   (at your option) any later version.
    #
    #   This program is distributed in the hope that it will be useful,
    #   but WITHOUT ANY WARRANTY; without even the implied warranty of
    #   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #   GNU General Public License for more details.
    #
    #   You can obtain a copy of the GNU General Public License from
    #   http://www.gnu.org/copyleft/gpl.html or by writing to
    #   Free Software Foundation, Inc.,675 Mass Ave, Cambridge, MA 02139, USA.
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    s = array(shape(x))
    if prod(s)==1:
        y=x
    else:
        y = fft.fft(x,n,d)
        y = y.reshape(prod(s[0:d]),n,prod(s[d+1:]))
        s[d]= 1+int(n/2)
        y=y[:,0:s[d],:]
        y = y.reshape(s)

    return y

def estnoisem(*args):

    #function [x,zo,xs]=estnoisem(yf,tz,pp)
    #ESTNOISEM - estimate noise spectrum using minimum statistics
    # Inputs:
    #   yf      input power spectra (one row per frame)
    #   tz      frame increment in seconds
    #           Alternatively, the input state from a previous call (see below)
    #   pp      algorithm parameters [optional]
    #
    # Outputs:
    #   x       estimated noise power spectra (one row per frame)
    #   zo      output state
    #   xs      estimated std error of x (one row per frame)
    #           xs seems often to be an underestimate by a factor of 2 or 3
    #
    # The algorithm parameters are defined in reference [1] from which equation
    # numbers are given in parentheses. They are as follows:
    #
    #        pp.taca      % (11): smoothing time constant for alpha_c [0.0449 seconds]
    #        pp.tamax     % (3): max smoothing time constant [0.392 seconds]
    #        pp.taminh    % (3): min smoothing time constant (upper limit) [0.0133 seconds]
    #        pp.tpfall    % (12): time constant for P to fall [0.064 seconds]
    #        pp.tbmax     % (20): max smoothing time constant [0.0717 seconds]
    #        pp.qeqmin    % (23): minimum value of Qeq [2]
    #        pp.qeqmax    % max value of Qeq per frame [14]
    #        pp.av        % (23)+13 lines: fudge factor for bc calculation  [2.12]
    #        pp.td        % time to take minimum over [1.536 seconds]
    #        pp.nu        % number of subwindows to use [3]
    #        pp.qith      % Q-inverse thresholds to select maximum noise slope [0.03 0.05 0.06 Inf ]
    #        pp.nsmdb     % corresponding noise slope thresholds in dB/second   [47 31.4 15.7 4.1]
    #
    # Example use:      y=enframe(s,w,ni);                  % divide speech signal s(n) into
    #                                                       % overlapping frames using window w(n)
    #                   yf=rfft(y,nf,2);                    % take fourier transform
    #                   dp=estnoisem(yf.*conj(yf),tinc);    % estimate the noise
    #
    # If convenient, you can call estnoisem in chunks of arbitrary size. Thus the following are equivalent:
    #
    #                   (a) dp=estnoisem(yp(1:300),tinc);
    #
    #                   (b) [dp(1:100),z]=estnoisem(yp(1:100),tinc);
    #                       [dp(101:200),z]=estnoisem(yp(101:200),z);
    #                       [dp(201:300),z]=estnoisem(yp(201:300),z);


    # This is intended to be a precise implementation of [1] with Table III
    # replaced by the updated table 5 from [2]. The only deliberate algorithm
    # change is the introduction of a minimum value for 1/Qeq in equation (23).
    # This change only affects the first few frames and improves the
    # convergence of the algorithm. A minor improveemnt was reported in [3] but
    # this has not yet been included.
    #
    # Refs:
    #    [1] Rainer Martin.
    #        Noise power spectral density estimation based on optimal smoothing and minimum statistics.
    #        IEEE Trans. Speech and Audio Processing, 9(5):504-512, July 2001.
    #    [2] Rainer Martin.
    #        Bias compensation methods for minimum statistics noise power spectral density estimation
    #        Signal Processing, 2006, 86, 1215-1229
    #    [3] Dirk Mauler and Rainer Martin
    #        Noise power spectral density estimation on highly correlated data
    #        Proc IWAENC, 2006

    #	   Copyright (C) Mike Brookes 2008
    #      Version: $Id: estnoisem.m 713 2011-10-16 14:45:43Z dmb $
    #
    #   VOICEBOX is a MATLAB toolbox for speech processing.
    #   Home page: http://www.ee.ic.ac.uk/hp/staff/dmb/voicebox/voicebox.html

    # read inputs
    nargin = len(args)
    yf = args[0]
    tz = args[1]

    (nr,nrf)=shape(yf)          # number of frames and freq bins
    x=array(zeros((nr,nrf)),dtype=complex)           # initialize output arrays
    xs=array(zeros((nr,nrf)),dtype=complex)           # will hold std error in the future

    if type(tz) is dict:
        nrcum = tz['nrcum']
        p = tz['p']
        ac = tz['ac']
        sn2 = tz['sn2']
        pb = tz['pb']
        pb2 = tz['pb2']
        pminu = tz['pminu']
        actmin = tz['actmin']
        actminsub = tz['actminsub']
        subwc = tz['subwc']
        actbuf = tz['actbuf']
        ibuf = tz['ibuf']
        lminflag = tz['lminflag']
        tinc = tz['tinc']
        qq = tz['qq']
    else:
        tinc = tz          # second argument is frame increment
        nrcum=0            # no frames so far

        # default algorithm constants
        qq = {
            'taca': 0.0449,    # smoothing time constant for alpha_c = -tinc/log(0.7) in equ (11)
            'tamax': 0.392,    # max smoothing time constant in (3) = -tinc/log(0.96)
            'taminh': 0.0133,    # min smoothing time constant (upper limit) in (3) = -tinc/log(0.3)
            'tpfall': 0.064,   # time constant for P to fall (12)
            'tbmax': 0.0717,   # max smoothing time constant in (20) = -tinc/log(0.8)
            'qeqmin': 2.0,       # minimum value of Qeq (23)
            'qeqmax': 14.0,      # max value of Qeq per frame
            'av': 2.12,             # fudge factor for bc calculation (23 + 13 lines)
            'td': 1.536,       # time to take minimum over
            'nu': 8.0,          # number of subwindows
            'qith': array([0.03, 0.05, 0.06, Inf],dtype=float), # noise slope thresholds in dB/s
            'nsmdb': array([47, 31.4, 15.7, 4.1],dtype=float)
        }

        if nargin >=3:
            pp = args[2]
            for field in qq.keys():
                if field in pp.keys():
                    qq[field]=pp[field]

    # unpack parameter structure

    taca=qq['taca']    # smoothing time constant for alpha_c = -tinc/log(0.7) in equ (11)
    tamax=qq['tamax']    # max smoothing time constant in (3) = -tinc/log(0.96)
    taminh=qq['taminh']    # min smoothing time constant (upper limit) in (3) = -tinc/log(0.3)
    tpfall=qq['tpfall']   # time constant for P to fall (12)
    tbmax=qq['tbmax']   # max smoothing time constant in (20) = -tinc/log(0.8)
    qeqmin=qq['qeqmin']       # minimum value of Qeq (23)
    qeqmax=qq['qeqmax']      # max value of Qeq per frame
    av=qq['av']             # fudge factor for bc calculation (23 + 13 lines)
    td=qq['td']       # time to take minimum over
    nu=qq['nu']           # number of subwindows
    qith=qq['qith'] # noise slope thresholds in dB/s
    nsmdb=qq['nsmdb']   # maximum permitted +ve noise slope in dB/s

    # derived algorithm constants
    aca=exp(-tinc/taca) # smoothing constant for alpha_c in equ (11) = 0.7
    acmax=aca          # min value of alpha_c = 0.7 in equ (11) also = 0.7
    amax=exp(-tinc/tamax) # max smoothing constant in (3) = 0.96
    aminh=exp(-tinc/taminh) # min smoothing constant (upper limit) in (3) = 0.3
    bmax=exp(-tinc/tbmax) # max smoothing constant in (20) = 0.8
    snrexp = -tinc/tpfall
    nv=round(td/(tinc*nu))    # length of each subwindow in frames
    if nv<4:        # algorithm doesn't work for miniscule frames
        nv=4
        nu=round(td/(tinc*nv))
    nd=nu*nv           # length of total window in frames
    (md,hd,dd) = mhvals(nd) # calculate the constants M(D) and H(D) from Table III
    (mv,hv,dv) = mhvals(nv) # calculate the constants M(D) and H(D) from Table III
    nsms=array([10])**(nsmdb*nv*tinc/10)  # [8 4 2 1.2] in paper
    qeqimax=1/qeqmin  # maximum value of Qeq inverse (23)
    qeqimin=1/qeqmax # minumum value of Qeq per frame inverse

    if len(yf)==0:   # provide dummy initialization
        ac=1               # correction factor (9)
        subwc=nv                   # force a buffer switch on first loop
        ibuf=0
        p=x          # smoothed power spectrum
        sn2=p              # estimated noise power
        pb=p               # smoothed noisy speech power (20)
        pb2=pb**2
        pminu=p
        actmin= array(ones(nrf) * Inf,dtype=complex)   # Running minimum estimate
        actminsub= array(ones(nrf) * Inf,dtype=complex)        # sub-window minimum estimate
        actbuf=array(ones(nrf) * Inf,dtype=complex)  # buffer to store subwindow minima
        lminflag=zeros(nrf)      # flag to remember local minimum
    else:
        if nrcum==0:      # initialize values for first frame
            p=yf[0,:].copy()         # smoothed power spectrum
            ac=1               # correction factor (9)
            sn2=p.copy()              # estimated noise power
            pb=p.copy()               # smoothed noisy speech power (20)
            pb2=pb**2
            pminu=p.copy()
            actmin=array(ones(nrf) * Inf,dtype=complex)   # Running minimum estimate
            actminsub=array(ones(nrf) * Inf,dtype=complex)          # sub-window minimum estimate
            subwc=nv                   # force a buffer switch on first loop
            actbuf=array(ones((nu,nrf)) * Inf,dtype=complex)  # buffer to store subwindow minima
            ibuf=0
            lminflag=zeros(nrf)      # flag to remember local minimum

        # loop for each frame

        for t in range(0,nr):                       # we use t instead of lambda in the paper
            yft=yf[t,:].copy()                      # noise speech power spectrum
            acb=(1+(sum(p) / sum(yft)-1)**2)**(-1)    # alpha_c-bar(t)  (9)
            ac=aca*ac+(1-aca)*max_complex(array([acb],dtype=complex),array([acmax],dtype=complex))    # alpha_c(t)  (10)
            ah=amax*ac*(1+(p/sn2-1)**2)**(-1)       # alpha_hat: smoothing factor per frequency (11)
            snr=sum(p)/sum(sn2)
            ah=max_complex(ah,min_complex(array([aminh],dtype=complex),array([snr**snrexp],dtype=complex)))                            # lower limit for alpha_hat (12)

            p=ah*p+(1-ah)*yft            # smoothed noisy speech power (3)
#            mat_comp(p,'p')
            b=min_complex(ah**2,array([bmax],dtype=complex)) # smoothing constant for estimating periodogram variance (22 + 2 lines)
            pb=b*pb + (1-b)*p            # smoothed periodogram (20)
            pb2=b*pb2 + (1-b)*p**2     	 # smoothed periodogram squared (21)

            qeqi=max_complex(min_complex((pb2-pb**2)/(2*sn2**2),array([qeqimax],dtype=complex)),array([qeqimin/(t+1+nrcum)],dtype=complex))   # Qeq inverse (23)
            qiav=sum(qeqi)/nrf              # Average over all frequencies (23+12 lines) (ignore non-duplication of DC and nyquist terms)
            bc=1+av*sqrt(qiav)              # bias correction factor (23+11 lines)
            bmind=1+2*(nd-1)*(1-md)/(qeqi**(-1)-2*md)      # we use the simplified form (17) instead of (15)
            bminv=1+2*(nv-1)*(1-mv)/(qeqi**(-1)-2*mv)    # same expression but for sub windows
            kmod=(bc*p*bmind) < actmin      # Frequency mask for new minimum

            if any(kmod):
                actmin[kmod]=bc*p[kmod]*bmind[kmod]
                actminsub[kmod]=bc*p[kmod]*bminv[kmod]

            if subwc>1 and subwc<nv:              # middle of buffer - allow a local minimum
                lminflag= logical_or(lminflag,kmod)    	# potential local minimum frequency bins
                pminu=min_complex(actminsub,pminu)
                sn2=pminu.copy()
            else:
                if subwc>=nv:                   # end of buffer - do a buffer switch
                    ibuf=1+(ibuf%nu)     	# increment actbuf storage pointer
                    actbuf[ibuf-1,:]=actmin.copy()   	# save sub-window minimum
                    pminu=min_complex_mat(actbuf)
                    i=nonzero(array(qiav,dtype=complex)<qith)
                    nsm=nsms[i[0][0]]     	# noise slope max
                    lmin = logical_and(logical_and(logical_and(lminflag,logical_not(kmod)),actminsub<(nsm*pminu)),actminsub>pminu)
                    if any(lmin):
                        pminu[lmin]=actminsub[lmin]
                        actbuf[:,lmin]= ones((nu,1)) * pminu[lmin]
                    lminflag[:]=0
                    actmin[:]=Inf
                    subwc=0

            subwc=subwc+1
            x[t,:]=sn2.copy()
            #mat_comp(x,'x_%s' % (t+1))
            qisq=sqrt(qeqi)
            # empirical formula for standard error based on Fig 15 of [2]
            xs[t,:]=sn2*sqrt(0.266*(nd+100*qisq)*qisq/(1+0.005*nd+6/nd)/(0.5*qeqi**(-1)+nd-1))

    # Save the state
    zo = {}
    zo['nrcum'] = nrcum + nr
    zo['p'] = p 
    zo['ac'] = ac
    zo['sn2'] = sn2
    zo['pb'] = pb
    zo['pb2'] = pb2
    zo['pminu'] = pminu
    zo['actmin'] = actmin
    zo['actminsub'] = actminsub
    zo['subwc'] = subwc
    zo['actbuf'] = actbuf
    zo['ibuf'] = ibuf 
    zo['lminflag'] = lminflag
    zo['tinc'] = tinc
    zo['qq'] = qq
	
    return x, zo

def mhvals(*args):

    # Values are taken from Table 5 in [2]
    #[2] R. Martin,"Bias compensation methods for minimum statistics noise power
    #               spectral density estimation", Signal Processing Vol 86, pp1215-1229, 2006.
    # approx: plot(d.^(-0.5),[m 1-d.^(-0.5)],'x-'), plot(d.^0.5,h,'x-')

    # read input
    nargin = len(args)

    dmh=array([
        [1,   0,       0],
        [2,   0.26,    0.15],
        [5,   0.48,    0.48],
        [8,   0.58,    0.78],
        [10,  0.61,    0.98],
        [15,  0.668,   1.55],
        [20,  0.705,   2],
        [30,  0.762,   2.3],
        [40,  0.8,     2.52],
        [60,  0.841,   3.1],
        [80,  0.865,   3.38],
        [120, 0.89,    4.15],
        [140, 0.9,     4.35],
        [160, 0.91,    4.25],
        [180, 0.92,    3.9],
        [220, 0.93,    4.1],
        [260, 0.935,   4.7],
        [300, 0.94,    5]
        ],dtype=float)

    if nargin>=1:
        d=args[0]
        i=nonzero(d<=dmh[:,0])
        if len(i)==0:
            i=shape(dmh)[0]-1
            j=i
        else:
            i=i[0][0]
            j=i-1
        if d==dmh[i,0]:
            m=dmh[i,1]
            h=dmh[i,2]
        else:
            qj=sqrt(dmh[i-1,0])    # interpolate using sqrt(d)
            qi=sqrt(dmh[i,0])
            q=sqrt(d)
            h=dmh[i,2]+(q-qi)*(dmh[j,2]-dmh[i,2])/(qj-qi)
            m=dmh[i,1]+(qi*qj/q-qj)*(dmh[j,1]-dmh[i,1])/(qi-qj)
    else:
        d=dmh[:,0].copy()
        m=dmh[:,1].copy()
        h=dmh[:,2].copy()

    return m,h,d

def myop(a,b,op):

    a = array(a)
    i = iscomplex(a)
    aa = a
    if any(i):
        aa[i]=absolute(aa[i])

    b = array(b)
    i = iscomplex(b)
    bb = b
    if any(i):
        bb[i]=absolute(bb[i])

    if op=='<':
        return aa<bb
    if op=='>':
        return aa>bb

def max_complex(a,b):
    # a,b are vectors

    if len(a)==1 and len(b)>1:
        a=tile(a,shape(b))
    if len(b)==1 and len(a)>1:
        b=tile(b,shape(a))

    i=logical_or(iscomplex(a),iscomplex(b))

    aa = a.copy()
    bb = b.copy()

    if any(i):
        aa[i]=absolute(aa[i])
        bb[i]=absolute(bb[i])
    if a.dtype == 'complex' or b.dtype== 'complex':
        cc = array(zeros(shape(a)),dtype=complex)
    else:
        cc = array(zeros(shape(a)),dtype=float)

    i=aa>bb
    cc[i]=a[i]
    cc[logical_not(i)] = b[logical_not(i)]

    return cc

def min_complex(a,b):
    # a,b are vectors

    if len(a)==1 and len(b)>1:
        a=tile(a,shape(b))
    if len(b)==1 and len(a)>1:
        b=tile(b,shape(a))

    i=logical_or(iscomplex(a),iscomplex(b))

    aa = a.copy()
    bb = b.copy()

    if any(i):
        aa[i]=absolute(aa[i])
        bb[i]=absolute(bb[i])

    if a.dtype == 'complex' or b.dtype== 'complex':
        cc = array(zeros(shape(a)),dtype=complex)
    else:
        cc = array(zeros(shape(a)),dtype=float)

    i=aa<bb
    cc[i]=a[i]
    cc[logical_not(i)] = b[logical_not(i)]

    return cc

def min_complex_mat(a):
    # minimum of each column
    s=shape(a)
    m = array(zeros(s[1]),dtype=complex)
    for i in range(0,s[1]):
        j = argmin(absolute(a[:,i]))
        m[i] = a[j,i]

    return m

def mat_comp(pyvar,mat_name):
    # read mat
    mat = sio.loadmat(mat_name + '.mat')[mat_name]
    # compare
    numpy.testing.assert_array_almost_equal(pyvar,mat)

def nextpow2(num):

    #Returns the next highest power of 2 from the given value.
    #Example
    #-------
    #>>>nextpow2(1000)
    #1024
    #>>nextpow2(1024)
    #2048

    npow = 2
    while npow <= num:
        npow = npow * 2
    return int(npow)

def bin2seg(A):
    #find start and end times of activity
    Ao= A
    ai= Ao > 0
    Ao[ai]= 1
    Ao= concatenate(([0],Ao,[0]))
    Adiff= numpy.diff(Ao)
    ent= array(nonzero(Adiff==-1))
    ent= ent-1
    start= array(nonzero(Adiff==1))

    return start,ent

def find_max_seg(A):

    #find start and end times of activity
    (start,ent) = bin2seg(A)

    #find maximum length segment
    maxlen = 0
    lstart= start.size
    for i in range(0,lstart):
        if (ent[0,i] - start[0,i] > maxlen):
            max_start = start[0,i]
            max_end = ent[0,i]

    return max_start,max_end

def intervals_delete(A,fs,td):

    fs = float(fs)

    #find start and end times of activity
    (start,ent) = bin2seg(A)

    #delete intervals with small duration (<td)
    lstart= start.size
    for i in range(0,lstart):
        if (ent[0,i] - start[0,i])/fs < td:
            A[start[0,i]:ent[0,i]+1]= 0

    output= A

    #find start and end times of activity
    (start,ent) = bin2seg(A)

    return start,ent,output

def intervals_unify(A,fs,td):

    fs = float(fs)

    #find start and end times of activity
    (start,ent) = bin2seg(A)

    #delete intervals with small duration (<td)
    lstart= start.size
    for i in range(0,lstart-1):
        if (A[start[0,i]] == A[start[0,i+1]]) and ((start[0,i+1]-ent[0,i]-1)/fs < td):
            A[ent[0,i]:start[0,i+1]+1]= A[start[0,i]]

    output= A

    #find start and end times of activity
    (start,ent) = bin2seg(A)

    return start,ent,output
