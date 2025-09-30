from gpio_tester import GPIOTester
from i2c_tester import I2CTester

class TestFactory():
    
    def get_test(module):
        if module == 'I2C':
            return I2CTester()
        elif module == 'GPIO':
            return GPIOTester()
        else:
            raise NotImplementedError("A tester for this module was not implemented")
