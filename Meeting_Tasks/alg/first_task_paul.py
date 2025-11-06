import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

files = np.array(["recording1.csv", "recording2.csv", "recording3.csv"])
n = 25
a=1
for file in files:
    df = pd.read_csv(file)
    m=len(df['orp_mV'])
    df['Moving_average'] = np.zeros(m)
    df['Moving_stdev'] = np.zeros(m)
    for i in range(len(df['orp_mV'])):
        if m-i >= n:
            df['Moving_average'][i] = np.mean(df['orp_mV'][i:i+n])
            df['Moving_stdev'][i] = np.std(df['orp_mV'][i:i+n])
        else:
            df['Moving_average'][i] = np.mean(df['orp_mV'][i:-1])
            df['Moving_stdev'][i] = np.std(df['orp_mV'][i:-1])  

    plt.plot(df['timestamp_ms'], df['orp_mV'], color='deepskyblue', label='orp_mV')
    plt.plot(df['timestamp_ms'], df['Moving_average'], color='darkorange', label=f'sliding average, n={n}')
    plt.plot(df['timestamp_ms'], df['Moving_stdev'], color='darkgreen', label=f'sliding standard deviation, n={n}')
    plt.title(f"Data Analysis ORP for Dataset {a} ")
    plt.xlabel("time [ms]")
    plt.ylabel("Tension [mV]")
    plt.xlim(0,max(df['timestamp_ms']))
    plt.grid(True)
    plt.legend()
    plt.show()
    a+=1