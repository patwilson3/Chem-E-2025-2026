import time
import ina226_move as ina226
from pathlib import Path
import csv


def call_ina_226(address, max_expected_amps, shunt_ohms, bus_volts_max, shunt_volts_max, event):
	m_amps = []
	volts = []
	while not event.is_set():
		ammeter = ina226.INA226(address=address, max_expected_amps=max_expected_amps, shunt_ohms=shunt_ohms)
		ammeter._calibrate(bus_volts_max=bus_volts_max, shunt_volts_max=shunt_volts_max, max_expected_amps=max_expected_amps)
		m_amp = ammeter.current()
		volt = ammeter.voltage()
		m_amps.append(m_amp)
		volts.append(volt)
		print(f"\n{volt:.4f} volts", f"{m_amp:.4f} mA\n")
		time.sleep(2)
	path = str(Path.cwd()) + r'/battery_results'
	columns_to_csv(path + f'/run{time.monotonic()}.csv', m_amps, volts, headers=['m_amps', 'volts'])
	
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

ina226_add = 0x40

if __name__ == '__main__':
	#7.09ma, 3.297v
	try:
		ammeter = ina226.INA226(address=ina226_add, max_expected_amps=0.4, shunt_ohms=0.0945)
		ammeter._calibrate(bus_volts_max=18, shunt_volts_max=0.05, max_expected_amps=0.4)
		while (True):
			print(f"Voltage: {ammeter.voltage():.4f}, Current: {ammeter.current():.4f} mA, Shuntvoltage: {ammeter.shunt_voltage():.4f}, SupplyVoltage: {ammeter.supply_voltage()}")
			time.sleep(0.2)
		
	except KeyboardInterrupt as e:
		print("closing")
	
		
		

