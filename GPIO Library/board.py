import lgpio
from gpio_device import GPIO_Device

class Board:
    _instance = None
    _initiated = False
    def __init__(self, chip):
        if not self._initiated:
            self._pins = []
            self._chip = chip
            self._handle = lgpio.gpiochip_open(chip)
            self._initiated = True
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super.__new__(cls, *args, **kwargs)
        return cls._instance

    def close(self):
        return lgpio.gpiochip_close(self._handle)
    
    def _add_pin(self, gpio_device : GPIO_Device):
        if not self._check_pin(gpio_device):
            self._pins.append(gpio_device)
            return True
        return False

    def _add_pin(self, pin_num : int):
        if not self._check_pin(pin_num):
            gpio_device = GPIO_Device(self._instance, pin_num)
            self._pins.append(gpio_device)
            return gpio_device
        return None
    
    def _remove_pin(self, gpio_device : GPIO_Device):
        for pin in self._pins:
            if pin.pin_num == gpio_device.pin_num:
                self._pins.remove(pin)
                return True
        return False
    
    def _remove_pin(self, pin_num : int):
        for pin in self._pins:
            if pin.pin_num == pin_num:
                self._pins.remove(pin)
                return True
        return False
    
    def _check_pin(self, pin_num : int):
        for pin in self._pins:
            if pin_num == pin.pin_num:
                return True
        return False
    
    def _check_pin(self, gpio_device : GPIO_Device):
        if gpio_device in self._pins:
            return True
        return False
