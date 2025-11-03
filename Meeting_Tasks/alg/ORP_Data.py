import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

for i in range(1,4):
    data_frame = pd.read_csv("recording" + str(i) + ".csv") #Which csv file is being read
    plt.xlabel('time(ms)')
    plt.ylabel('Oxidation-Reduction potential(mV)')
    #Printing mean and std without a rolling window
    print("Standard deviation of ORP without rolling window:" , data_frame['orp_mV'].std())
    print("Mean of ORP without rolling window", data_frame['orp_mV'].mean())
    #calculating mean and std with rolling window of 30 and stripping it of NaN results
    rolling_std = data_frame['std_rolling'] = data_frame['orp_mV'].rolling(window=30).std()
    rolling_std_valid = rolling_std.dropna()
    rolling_avg = data_frame['avg_rolling'] = data_frame['orp_mV'].rolling(window=30).mean()
    rolling_avg_valid = rolling_avg.dropna()
    data_frame['std_rolling'] = rolling_std_valid
    data_frame['avg_rolling'] = rolling_avg_valid
    #printing all results in neat table without NaN
    print("Standard deviation rolling (30)")
    #print(data_frame[['orp_mV', 'std_rolling']].head(100))
    print(data_frame[['timestamp_ms', 'orp_mV', 'std_rolling']])
    print("Mean rolling (30)")
    print(data_frame[['timestamp_ms' ,'orp_mV', 'avg_rolling']])
    print(data_frame.shape)
    print(data_frame.describe())
    #print(rolling_avg_valid.tolist())
    #plottin valus of orp against time and std against time
    plt.title('ORP vs Time with Stadard deviation(rolling 30) and Average rolling (30)')
    plt.plot(data_frame['timestamp_ms'], data_frame['orp_mV'], label='ORP')
    plt.plot(data_frame['timestamp_ms'], data_frame['std_rolling'], label='Rolling Std')
    plt.plot(data_frame['timestamp_ms'], data_frame['avg_rolling'], label='Rolling Average')
    plt.legend(loc='upper right')
    #print(data_frame[['orp_mV', 'std_rolling']].head(35))
    #print(data_frame['std_rolling'].dropna().iloc[0])
    plt.show()