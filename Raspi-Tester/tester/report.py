import datetime
'''
Report dict:

{1: [Module, source, type]}

#source means pin or address

'''


class Report:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, path=''):
        if self._instance is not None:
            self.successes = {}
            self.fails = {}
            self.counter = 0
            self.result_path = path

    def get_instance(self):
        return self._instance

    def append_success(self, module, source, test_type):
        self.counter += 1
        self.successes[self.counter] = [module, source, test_type]

    def append_fail(self, module, source, test_type, error):
        self.counter += 1
        self.fails[self.counter] = [module, source, test_type, error]

    def sort_test_result(self, result:dict):
        if result['result'] == 'Pass':
            self.append_success(module=result["module"], source=result["source"], test_type=result["test"])
        else:
            self.append_fail(module=result["module"], source=result["source"], test_type=result["test"], error=result["result"])

    def create_report(self):
        date = datetime.datetime.now()
        try:
            with open(self.result_path + f'{date}.txt', 'x') as f:
                f.write("=" * 10 + " PASS " + "=" * 10 + '\n')
                for test_number, test_results in self.successes.items():
                    module = test_results[0]
                    source = test_results[1]
                    test_type = test_results[2]
                    f.write(f"Test Number: {test_number}, Module: {module}, Source: {source}, TestType: {test_type}\n")

                f.write("=" * 10 + " FAIL " + "=" * 10 + '\n')
                for test_number, test_results in self.fails.items():
                    module = test_results[0]
                    source = test_results[1]
                    test_type = test_results[2]
                    error = test_results[3]
                    f.write(f"Test Number: {test_number}, Module: {module}, Source: {source}, TestType: {test_type}, Error: {error}\n")
                
                f.close()

        except OSError as e:
            print("OS buggin or File probably already exists")

        except Exception as e:
            print(f"the following exception occured while making the report: {e}")
            f.close()
        
        finally:
            self.reset_attributes()

    def reset_attributes(self):
        self.successes = {}
        self.fails = {}
        self.counter = 0


if __name__ == '__main__':
    report = Report(r"/Users/patrickwilson/Desktop/ChemE/Raspi-Tester/tester/tests/")
    report.append_success("I2C", 0x40, "read")
    report.append_success("GPIO", 12, "pull up")
    report.append_fail("I2C", 0x37, "write", "conn error")
    report.append_fail("GPIO", 22, "button", "did not receive button press")
    report.create_report()