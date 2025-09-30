from base_tester import BaseTester
try:
    import gpiozero
except ModuleNotFoundError:
    print("Make sure you have gpiozero installed")

class GPIOTester(BaseTester):

    def __init__(self):
        #setup board here pass
        pass

    def run_test(self, addr: hex, tests: list):
        for test in tests:
            pass
    
