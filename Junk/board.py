from pin import Pin
from bus import Bus
import lgpio

class Board:
    _instance = None
    _initialized = False
    _handle = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, chip=0):
        if not __class__._initialized:
            self.pins = dict()
            self.buses = dict()
            __class__._handle = lgpio.gpiochip_open(chip)
            __class__._initialized = True
            for i in range(1,41,1):
                self.pins[i] = False
            for i in range(1, 4, 1):
                self.buses[i] = False
    
    def handle(cls):
        return cls._handle

    def get_pin(self, pin_num, mode) -> Pin:
        if self.pins[pin_num]:
            print(f"Pin {pin_num} is already in use")
        else:
            pin = Pin(pin_num, mode)
            self.pins[pin_num] = pin
            return pin

    def free_pin(self, pin_num) -> None:
        if self.pins[pin_num]:
            pin = self.pins[pin_num]
            self.pins[pin_num] = None
            #lgpio code to clean up pin num
        else:
            print(f"Pin {pin_num} is not currently initialized, cannot remove an uninitialized pin")

    def get_bus(self, bus_num) -> Bus:
        if self.buses[bus_num]:
            print(f"Bus {bus_num} is occupied")
        else:
            return Bus(bus_num)

    def free_bus(self, bus_num) -> Bus:
        if self.buses[bus_num]:
            bus = self.buses[bus_num]
            self.buses[bus_num] = False
            #lgpio to free bus
        else:
            print(f"Bus {bus_num} is already free")

    def show_available_pins(self) -> None:
        for pin, pin_obj in self.pins.values():
            occupied = not pin_obj
            print(f"Pin {pin}, Occupied: {occupied}\n")

    def show_available_buses(self) -> None:
        for bus, bus_obj in self.buses.values():
            occupied = not bus_obj
            print(f"Bus {bus}, Occupied: {occupied}\n")

    
