
import time
import ina226



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
	
		
		

