import setup
from report import Report


'''Module: addr: action'''

class BaseTester:

    def __init__(self, module):
        self._report_instance = Report.get_instance()
        self.module = module
    def setup():
        pass
    
    def run_tests(self, test_data):
        self.setup()
        for addr, tests in test_data:
            test_result = self.run_test(addr, tests)
            self._report_instance.sort_test_result(test_result)
            self.print(test_result)
        
    def run_test(self, source, tests):
        raise NotImplementedError #subclasses will have method
    
    def teardown(self):
        pass

    def print(self, result:dict):
        if result.get("result") != "Pass":
            print(f"Module: {self.module}, Source: {result["source"]}, Test: {result["test"]}, Result: Fail, Error:{result['result']}\n")
        else:
            print(f"Module: {self.module}, Source: {result["source"]}, Test: {result["test"]}, Result: Pass\n")


        
