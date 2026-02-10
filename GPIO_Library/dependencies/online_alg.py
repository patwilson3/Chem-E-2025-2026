import numpy as np
from collections import deque
from .ads1115 import *
import csv
from pathlib import Path
import time
from datetime import datetime
from .dashboard import Dashboard

DASH = Dashboard()

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
					stop_result = None
			else: #DO NOT USE
				hits = 0
	return stop_result, None
									
def columns_to_csv(path, *columns, headers=None):

	length = len(columns[0])
	if any(len(col) != length for col in columns):
		raise ValueError("All lists must have the same length")

	with open(path, "w", newline="") as f:
		writer = csv.writer(f)
		if headers:
			writer.writerow(headers)
		for row in zip(*columns):
			writer.writerow(row)


def std_deviation_rate_of_change_alg_two_online(
	window=10,
	rot_window=10,
	threshold=5,
	hit_threshold=10,
	ads1115=None,
	stopping_event=None,
	period_s: float = 0.2,
	max_time_s = 15,
	reset_event=None
	):

	stop_threshold = 15
	init = time.time()

	if ads1115 is None:
		raise ValueError("ads1115 instance is required")
	if stopping_event is None:
		raise ValueError("stopping_event is required")

	DASH.update_alg('RUNNING')

	std_arr = []
	time_arr = []
	rot_arr = []
	mvs_arr = []
	is_stop = []

	slope = SlidingSlopeLR(rot_window)
	std_c = SlidingSTD(window=window)

	hits = 0
	finished = False

	t0 = time.monotonic()
	next_t = t0  # next scheduled loop time
	t_elapsed_s = 0.0

	while t_elapsed_s < max_time_s and not reset_event.is_set():
		loop_start = time.monotonic()

		t_elapsed_s = loop_start - t0
		time_s = t_elapsed_s

		mvs = ads1115.get_adjusted_mvs()
		rot = slope.update(time_s, mvs)
		std = std_c.update(mvs)
		if std is not None and rot is not None:
			print(f"mvs: {float(mvs):.3f}, std: {float(std):.3f}, rot: {float(rot):.3f}, time_s: {float(time_s):.3f}")
			DASH.update_orp(mvs=mvs, std=std, rot=rot, time_s=time_s)
		
		std_arr.append(std)
		time_arr.append(time_s)
		rot_arr.append(rot)
		mvs_arr.append(mvs)


		# default: not a stop sample
		stop_flag = 0

		if std is not None and rot is not None and not finished:
			curr = rot - std
			if abs(curr) < threshold:
				hits += 1
				elaspsed_since_init = time.time() - init
				if hits >= hit_threshold and elaspsed_since_init > stop_threshold:
					finished = True
					stop_flag = 1
					stopping_event.set()
					print(f"\nAlg stopped at mvs: {mvs}, time: {time_s}\n")  # notify others if needed
					DASH.update_alg('STOP DETECTED')
			else:
				hits = 0

		is_stop.append(stop_flag)

		next_t += period_s
		now = time.monotonic()
		sleep_time = next_t - now
		if sleep_time > 0:
			time.sleep(sleep_time)

	# now all lists have the same length and is_stop marks the stop sample
	DASH.update_alg('SAVING DATA')
	stopping_event.set()
	try:
		path_destination = Path(str(Path.cwd()) + r'/alg_results')
		columns_to_csv(str(path_destination) + f'/run{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv', time_arr, mvs_arr, rot_arr, std_arr, is_stop, headers=['time', 'mvs', 'rot', 'std', 'stop'])
		
	except FileNotFoundError:
		path_destination = r'/home/electrical/chem_repo/Chem-E-2025-2026/GPIO_Library/dependencies/alg_results'
		columns_to_csv(str(path_destination) + f'/run{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv', time_arr, mvs_arr, rot_arr, std_arr, is_stop, headers=['time', 'mvs', 'rot', 'std', 'stop'])


# return all collected data


                                
