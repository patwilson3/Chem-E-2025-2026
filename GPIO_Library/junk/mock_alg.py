from control import event

def call_alg(sleep_time):
	print('alg starting')
	time.sleep(sleep_time)
	event.set()

