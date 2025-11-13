from collections import deque
import pandas as pd
import numpy as np
import math
#Author: Allen Virlan
THRESHOLD = 0.3

def determine_stop(values, threshold):
    for i in values:#for std values (Personal hypothesis)
        if isinstance(i, float) and not pd.isna(i):
            if compare_floats(i, 0.0, threshold):
                print("Stop")
    #for i in range(len(mean_values)): #for mean values(personal hypothesis)
        #if isinstance(mean_values[i], float):
            #if compare_floats(mean_values[i], orp_values[i]):
                #print("Stop the car")

def compare_floats(float1, float2,tolerance):
    if abs(float1 - float2) < tolerance:
        return True
    return False

orp_values = []
mean_values = []
std_values = []

data_stream = [] #represents the data stream we will collect live from ORP probe

for i in data_stream:
    orp_values.append(i)
    s = pd.Series(orp_values)
    mean_value = s.rolling(window=30).mean().iloc[-1]
    std_value = s.rolling(window=30).std().iloc[-1]

    mean_values.append(mean_value)
    std_values.append(std_value)

    determine_stop(std_values, THRESHOLD)
    #determine_stop(mean_values, THRESHOLD)