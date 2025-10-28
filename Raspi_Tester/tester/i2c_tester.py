from base_tester import BaseTester
try:
    import lgpio
except ModuleNotFoundError:
    print("Make sure you are in a Linux env")

class I2CTester(BaseTester):
   raise NotImplementedError

            

