import numpy as np
from collections import deque
from pathlib import path
from ads1115 import *


class SlidingSlopeLR:
    #using ordinary least squares (OLS)
    def __init__(self, window):
        self.window = window
        self.time_deq = deque(maxlen=window)
        self.mv_deq = deque(maxlen=window)

    def update(self, t, v):
        self.time_deq.append(t)
        self.mv_deq.append(v)

        if len(self.time_deq) < self.window:
            return None

        t_arr = np.fromiter(self.time_deq, dtype=float)
        v_arr = np.fromiter(self.mv_deq, dtype=float)

        t_mean = t_arr.mean()
        v_mean = v_arr.mean()

        numerator = np.sum((t_arr - t_mean) * (v_arr - v_mean))
        denominator = np.sum((t_arr - t_mean)**2)

        return numerator / denominator if denominator != 0 else 0.0
    

class SlidingSTD:
    def __init__(self, window):
        self.window = window
        self.value_deq = deque(maxlen=window)
    
    def update(self, v):
        self.value_deq.append(v)

        if len(self.value_deq) != self.window:
            return None
        
        std = np.std(self.value_deq)

        return std
    



def std_deviation_rate_of_change_alg_two_offline(window=10, rot_window=10, threshold=5, hit_threshold=10, data=None):
    '''
    best alg out of the three:
    uses: OLS, ordinary least squares as an estimator for the slope, combined with standard deviation
    
    '''
    std_arr = []
    time_arr = []
    rot_arr = []
    mvs_arr = []
    stop_result = {}

    slope = SlidingSlopeLR(rot_window)
    std_c = SlidingSTD(window=window)
    arr = deque(maxlen=window)
    hits = 0
    for time, mvs in data:
        arr.append(mvs)
        rot = slope.update(time, mvs)
        std = std_c.update(mvs)
        std_arr.append(std), time_arr.append(time), rot_arr.append(rot), mvs_arr.append(mvs)
        if std is not None and rot is not None:
            curr = rot - std
            if abs(curr) < threshold:
                hits += 1
                if hits == hit_threshold:
                    stop_result = pd.DataFrame({
                                                    "mvs": [mvs], 
                                                    "ols_rot" : [rot], 
                                                    "std" : [std], 
                                                    "time" : [time]
                                                })
            else:
                hits = 0
    return stop_result, pd.DataFrame({
                                "time" : time_arr,
                                "mvs": mvs_arr, 
                                "ols_rot" : rot_arr, 
                                "std" : std_arr
                                    })
                                    
def init_ads1115():
	os_bit=FIELD_OPTIONS.OS_SINGLE
    mux_bit=FIELD_OPTIONS.MUX_AIN1_GND 
    pga_bit=FIELD_OPTIONS.PGA_4_096V
    mode_bit=FIELD_OPTIONS.MODE_CONTINUOUS
    sps_bit=FIELD_OPTIONS.DR_128SPS
    comp_bit=FIELD_OPTIONS.COMP_QUE_DISABLE

    config = (os_bit.value | mux_bit.value | pga_bit.value | mode_bit.value | sps_bit.value | comp_bit.value)
    #this means, os bit on continuos mode, using AIN0 and GND, GAIN set at 2.048v, Continous mode, data rate set at 128 (def), disable comp bit (continuous read)

	ads1115 = ADS1115(addr=0x48, i2c_bus=1)
	ads1115.set_config(config)
	ads1115.set_pga_bit(pga_bit)
	print(f"writing configuration")
	ads1115.write_configuration()
	
	return ads1115
                                    
def std_deviation_rate_of_change_alg_two_online(window=10, rot_window=10, threshold=5, hit_threshold=10, ads1115=None)

		

	    std_arr = []
		time_arr = []
		rot_arr = []
		mvs_arr = []
		stop_result = {}

		slope = SlidingSlopeLR(rot_window)
		std_c = SlidingSTD(window=window)
		arr = deque(maxlen=window)
		hits = 0
		finished = False
		while not :
			arr.append(mvs)
			rot = slope.update(time, mvs)
			std = std_c.update(mvs)
			std_arr.append(std), time_arr.append(time), rot_arr.append(rot), mvs_arr.append(mvs)
			if std is not None and rot is not None:
				curr = rot - std
				if abs(curr) < threshold:
					hits += 1
					if hits == hit_threshold:
						stop_result = pd.DataFrame({
														"mvs": [mvs], 
														"ols_rot" : [rot], 
														"std" : [std], 
														"time" : [time]
													})
				else:
					hits = 0
		return stop_result, pd.DataFrame({
									"time" : time_arr,
									"mvs": mvs_arr, 
									"ols_rot" : rot_arr, 
									"std" : std_arr
										})
                                    
