import lgpio

class Pin:
    _TIMEOUT = 0
    _DEBOUNCE = 0
    _EDGE_TYPE = lgpio.BOTH_EDGES

    def __init__(self, handle, pin_num):
        self.handle = handle
        self.pin_num = pin_num

    def _digital_in(self):
        res = lgpio.gpio_read(self.handle, self.pin_num)
        if res < 0:
            raise SystemError(f"The following error occured when reading from gpio pin {self.pin_num}")
        return res
    
    def _digital_out(self, data):
        res = lgpio.gpio_write(self.handle, self.pin_num, data)
        if res < 0:
            raise SystemError(f"The following error occured when writing from gpio pin {self.pin_num}")
        return res
    
    def _toggle_expect_both_edges(self):
        self._EDGE_TYPE = lgpio.BOTH_EDGES

    def _toggle_expect_rising_edge(self):
        self._EDGE_TYPE = lgpio.RISING_EDGE
    
    def _toggle_expect_falling_edge(self):
        self._EDGE_TYPE = lgpio.FALLING_EDGE

    def _set_timeout(self, ms):
        self._TIMEOUT = ms

    def _set_debounce(self, ms):
        self._DEBOUNCE = ms
    
    def _reset_timeout(self, ms):
        self._TIMEOUT = 0
    
    def _reset_debounce(self, ms):
        self._DEBOUNCE = 0

    def _pwm_out(self):
        pass
        
    

    
    
    
