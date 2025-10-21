import lgpio

class GPIO_Device:
    def __init__(self, board, pin, mode='input'):
        self._pin = pin
        self._board = board
        self._mode = mode
        self._claimed = False
        self._claim_pin()
    
    def _claim_pin(self):
        """Claim the GPIO pin for use"""
        handle = self._board._handle
        if self._mode == 'input':
            result = lgpio.gpio_claim_input(handle, self._pin)
        elif self._mode == 'output':
            result = lgpio.gpio_claim_output(handle, self._pin, 0)  # Default to low
        else:
            raise ValueError(f"Invalid mode: {self._mode}. Use 'input' or 'output'")
        
        if result < 0:
            raise RuntimeError(f"Failed to claim GPIO pin {self._pin} as {self._mode}: {result}")
        
        self._claimed = True
    
    def write(self, value):
        """Write a value to the GPIO pin (output mode only)"""
        if not self._claimed:
            raise RuntimeError("GPIO pin not claimed")
        if self._mode != 'output':
            raise RuntimeError("Cannot write to input pin")
        
        result = lgpio.gpio_write(self._board._handle, self._pin, value)
        if result < 0:
            raise RuntimeError(f"Failed to write to GPIO pin {self._pin}: {result}")
        return result
    
    def read(self):
        """Read the value from the GPIO pin"""
        if not self._claimed:
            raise RuntimeError("GPIO pin not claimed")
        
        result = lgpio.gpio_read(self._board._handle, self._pin)
        if result < 0:
            raise RuntimeError(f"Failed to read from GPIO pin {self._pin}: {result}")
        return result
    
    def release(self):
        """Release the GPIO pin"""
        if self._claimed:
            lgpio.gpio_free(self._board._handle, self._pin)
            self._claimed = False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.release()

    def get_pin(self):
        return self._pin
    
    def get_board(self):
        return self._board
    
    @property
    def pin_num(self):
        return self._pin
    
    