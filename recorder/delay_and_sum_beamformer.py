import numpy as np
import scipy.io.wavfile


def tdoas(N, d, theta, c):
	ns = np.arange(0,N) - (N - 1) / 2
	T = - ns * d * np.cos(theta) / c
	return T


def degreesTOradians(angle_deg):
	rad_per_deg = np.pi / 180
	angle_rad = rad_per_deg * angle_deg
	return angle_rad

def dft_radian_frequencies(N_fft):
	k_upper = np.floor((N_fft - 1) / 2)
	k_lower = 1 + k_upper - N_fft
	omega =  np.arange(k_lower,k_upper+1).transpose() / N_fft * (2 * np.pi)
	omega = np.fft.ifftshift(omega)
	return omega


def DSB_weights_linear_arrays(N, d, theta_source, c, N_fft, F_s):
	T = tdoas(N, d, theta_source, c)
	T_samples = T * F_s

	# DFT radian frequencies in [-pi, pi)
	omega = dft_radian_frequencies(N_fft)
	W=np.zeros((N,N_fft))+1j*np.zeros((N,N_fft))
	# DS beamformer weights are phase shifts (equivalent to temporal shifts in
	#                   the time domain) that compensate for propagation delays
	for sensor_index in range(0,N):
    		W[sensor_index, :] = float(1) /float(N) * np.exp(- 1j * omega * T_samples[sensor_index])
	return W


def delay_and_sum_beamf(X, N, d, theta_source, c, N_fft, F_s):
	# Calculate DS beamformer weigths
	W = DSB_weights_linear_arrays(N, d, theta_source, c, N_fft, F_s)

	# DFT of input signals
	X_dft = np.fft.fft(X, N_fft, 0)
	Y_dft= np.zeros((N_fft,1))+1j*np.zeros((N_fft,1))
	# Apply DS beamformer weights and sum
	Y_dft = (np.sum(W.conj().transpose() * X_dft, 1))

	# DS beamformer output in the time domain
	y_zero_padded = np.fft.ifft(Y_dft, axis= 0)

	# Discard imaginary parts occuring due to finite numerical precision
	
    	y_zero_padded = np.real(y_zero_padded)
	#print(y_zero_padded)


	# Truncate DS beamformer output to original signal length
	signal_length = X.shape[0]
	if (N_fft > signal_length):
   		y = y_zero_padded[0 : signal_length-1].copy()
	else:
    		y = y_zero_padded.copy()
	return y
	
