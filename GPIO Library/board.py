import lgpio
from gpio_device import GPIO_Device

class Board:
    _instance = None
    _initiated = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, chip):
        if not Board._initiated:
            self._pins = []
            self._chip = chip
            self._handle = lgpio.gpiochip_open(chip)
            if self._handle < 0:
                raise RuntimeError(f"Failed to open GPIO chip {chip}: {self._handle}")
            Board._initiated = True

    def close(self):
        """Close the GPIO chip and release all resources"""
        # Release all GPIO pins first
        for pin in self._pins[:]:  # Copy list to avoid modification during iteration
            pin.release()
        self._pins.clear()
        
        # Close the GPIO chip
        result = lgpio.gpiochip_close(self._handle)
        if result < 0:
            raise RuntimeError(f"Failed to close GPIO chip: {result}")
        
        # Reset singleton state
        Board._instance = None
        Board._initiated = False
        return result
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.close()
    
    def _add_pin_device(self, gpio_device : GPIO_Device):
        if not self._check_pin_device(gpio_device):
            self._pins.append(gpio_device)
            return True
        return False

    def _add_pin(self, pin_num : int):
        if not self._check_pin(pin_num):
            gpio_device = GPIO_Device(self._instance, pin_num)
            self._pins.append(gpio_device)
            return gpio_device
        return None
    
    def _remove_pin_device(self, gpio_device : GPIO_Device):
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
    
    def _check_pin_device(self, gpio_device : GPIO_Device):
        if gpio_device in self._pins:
            return True
        return False
