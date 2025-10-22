import lgpio

class AD4988:
    def __init__(self, pins:dict):
        if not isinstance(pins, dict):
            raise TypeError("Pins must be a dictionary")
        self.MS1 = pins['MS1']
        self.MS2 = pins['MS2']
        self.MS3 = pins['MS3']
        self.RESET = pins['RESET']
        self.SLEEP = pins['SLEEP']
        self.STEP = pins['STEP']
        self.GND = pins['GND']
        self.DIR = pins['DIR']
        self.ENABLE = pins['ENABLE']

        
    








 
