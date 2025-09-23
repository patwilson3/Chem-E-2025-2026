import lgpio

class Pin:
    def __init__(self, handle, pin_num):
        self.handle = handle
        self.pin_num = pin_num

    def _digital_in(self):
        pass
    def _digital_out(self):
        pass
    def _pwm_out(self):
        pass
    
    
