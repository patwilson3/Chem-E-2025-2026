from ads1115 import *
import time
import os
import sys
import traceback

def main_orp(duration, title="default"):

    os_bit=FIELD_OPTIONS.OS_SINGLE
    mux_bit=FIELD_OPTIONS.MUX_AIN1_GND 
    pga_bit=FIELD_OPTIONS.PGA_4_096V
    mode_bit=FIELD_OPTIONS.MODE_CONTINUOUS
    sps_bit=FIELD_OPTIONS.DR_128SPS
    comp_bit=FIELD_OPTIONS.COMP_QUE_DISABLE

    config = (os_bit.value | mux_bit.value | pga_bit.value | mode_bit.value | sps_bit.value | comp_bit.value)
    #this means, os bit on continuos mode, using AIN0 and GND, GAIN set at 2.048v, Continous mode, data rate set at 128 (def), disable comp bit (continuous read)

    try:
        ads1115 = ADS1115(addr=0x48, i2c_bus=1)
        ads1115.set_config(config)
        ads1115.set_pga_bit(pga_bit)
        print(f"writing configuration")
        ads1115.write_configuration()
        start_time = time.time()
        res_arr = []
        while (time.time() - start_time) < duration:
            try:
                curr_time = time.time()
                data = ads1115.read_word_and_clean_data()
                amount_time = f'{(curr_time-start_time):.3f}'
                mv = data * 1000
                mv_adjusted = mv - 1483
                print(f"Reading {mv_adjusted:.5f} mvs, time: {amount_time}")
                res_arr.append([amount_time, mv_adjusted])
                time.sleep(0.2)
            except Exception as e:
                print(f"error while reading data at time {amount_time}")
                res_arr.append([amount_time, "read error"])

    except Exception as e:
        pass

    
    finally:
        output_dir = "./orp_data"
        os.makedirs(output_dir, exist_ok=True)
        print("closing bus")
        ads1115.close()
        filename = os.path.join(output_dir, f"{title}.txt")
        with open(filename, "a") as f:
            f.write(f"time(s),mvs\n")
            for t, v in res_arr:
                f.write(f'{float(t):.3f},{float(v):.5f}\n')


            f.close()

if __name__ == '__main__':
    duration = 60
    title = "default"
    if len(sys.argv) > 1:
        duration = int(sys.argv[-1])
    main_orp(duration, title)
