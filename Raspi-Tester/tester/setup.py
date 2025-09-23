import json
import os

""" JSON format will be as follows 
{
    {
        Module : I2C,
        tests : {0x40: [write], 0x47 : [read, write], 0x80 : [write]}, #addresses to be tested
    },
    {
        Module: GPIO
        tests: {12 : [pullup, pulldown], 15 : [high, low], 19 : [freq]} #type of tests for GPIO to be determined
    }
    
}

program will parse the config.json and convert it into wanted test format:
    {Module type: {address/pin : [test_type]},}

So in the tester we can easily parse as such:

for module in test_dict:
    for address in module:
        for test in address:
            #do some test

"""

def setup():
    path_to_config = "config.json"
    config = get_config_as_json_obj(path_to_config)
    return parse_config_json_into_dict(config)

def get_config_as_json_obj(path_to_config) -> dict:

    try:
        with open(path_to_config, 'r') as config_file:
            config_data = json.load(config_file)
    except FileNotFoundError:
        print("config.json file was not found, make sure it exists")
    
    return config_data

def parse_config_json_into_dict(config_data) -> dict:

    test_format_dictionary = {}

    if not config_data:
        print("config_data is Null, please verify")
        return
    
    for module_list in config_data:
        test_format_dictionary[module_list['Module']] = module_list['tests']
    
    return test_format_dictionary

if __name__ == '__main__':

    #testing

    test_json = [
        {
            "Module": "I2C",
            "tests": {
                "0x40": ["write"],
                "0x47": ["read", "write"],
                "0x80": ["write"]
            }
        },
        {
            "Module": "GPIO",
            "tests": {
                "12": ["pullup", "pulldown"],
                "15": ["high", "low"],
                "19": ["freq"]
            }
        }
    ]

    with open("test.json", "w") as f:
        json.dump(test_json, f, indent=4)

    path_to_test = "./test.json"

    data = get_config_as_json_obj(path_to_test)

    print(data)

    res_test_dict = parse_config_json_into_dict(data)

    print(res_test_dict)

    os.remove("./test.json")

