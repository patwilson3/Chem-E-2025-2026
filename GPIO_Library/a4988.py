import lgpio
import time
import traceback

class A4988:

    '''THIS IS USING SOFTWARE PWM'''

    MIN_FREQ = 10
    MAX_FREQ = 50000

    MS_MAP = {
        1: (0, 0, 0),
        2: (1, 0, 0),
        4: (0, 1, 0),
        8: (1, 1, 0),
        16: (1, 1, 1) 
    }

    def __init__(self, chip=0,
                 step_pin=None, dir_pin=None,
                 enable_pin=None, reset_pin=None, sleep_pin=None, 
                 ms1_pin=None, ms2_pin=None, ms3_pin=None, micro_step_length=None, init_dir=0):
        
        if None in (step_pin, dir_pin, enable_pin, reset_pin, sleep_pin, ms1_pin, ms2_pin, ms3_pin):
            raise ValueError("STEP, DIR, ENABLE, RESET, SLEEP are required")

        self.h = lgpio.gpiochip_open(chip)
        self.step = step_pin
        self.dir = dir_pin
        self.en  = enable_pin
        self.rst = reset_pin
        self.slp = sleep_pin
        self.ms1 = ms1_pin
        self.ms2 = ms2_pin
        self.ms3 = ms3_pin

        lgpio.gpio_claim_output(self.h, self.step, 0)
        lgpio.gpio_claim_output(self.h, self.dir, init_dir)
        lgpio.gpio_claim_output(self.h, self.en, 1)   # disabled
        lgpio.gpio_claim_output(self.h, self.rst, 1)  # normal
        lgpio.gpio_claim_output(self.h, self.slp, 0)
        lgpio.gpio_claim_output(self.h, self.ms1, 1)  # default MS setting set at (1, 1, 1)
        lgpio.gpio_claim_output(self.h, self.ms2, 1)  #
        lgpio.gpio_claim_output(self.h, self.ms3, 1)  #


        if not micro_step_length is None:
            self.set_micro_steps(step_length=micro_step_length)


    def enable(self):
        """ENABLE low: driver outputs active."""
        lgpio.gpio_write(self.h, self.en, 0)

    def disable(self):
        """ENABLE high: outputs disabled (motor unpowered or high-Z)."""
        lgpio.gpio_write(self.h, self.en, 1)

    def wake(self):
        """SLEEP high -> normal operation; wait for charge pump."""
        lgpio.gpio_write(self.h, self.slp, 1)
        time.sleep(self.WAKE_DELAY_S)

    def sleep(self):
        """SLEEP low -> low-power, outputs off."""
        lgpio.gpio_write(self.h, self.slp, 0)
    
    def set_micro_steps(self, step_length):
        '''input 1, 2, 4, 8, 16'''
        if step_length not in self.MS_MAP.keys():
            raise ValueError("step length invalid must be 1, 2, 4, 8, 16")
        
        ms1, ms2, ms3 = self.MS_MAP[step_length]
        try:
            lgpio.gpio_write(self.h, self.ms1, ms1)
            lgpio.gpio_write(self.h, self.ms2, ms2)
            lgpio.gpio_write(self.h, self.ms3, ms3)
        except Exception as e:
            print("the following exception occurred")
            traceback.print_exc()

    def reset(self):
        lgpio.gpio_write(self.h, self.rst, 0)
        time.sleep(1e-6)
        lgpio.gpio_write(self.h, self.rst, 1)

    def start_step(self, step_amount, pulse_width, period):
        freq = 1/period
        print(f"frequency: {freq} Hz")
        if pulse_width < 1e-6:
            raise ValueError("pulse width too short")
        
        for _ in range(step_amount):
            lgpio.gpio_write(self.h, self.step, 1)
            time.sleep(pulse_width)
            lgpio.gpio_write(self.h, self.step, 0)
            time.sleep(period - pulse_width)
        


    def set_dir(self, direction: int):
        lgpio.gpio_write(self.h, self.dir, direction)
        self.dir = direction


    def release(self):
        """Release all pins and close chip."""
        # Optional: set outputs to safe state first
        try:
            self.disable()
            self.sleep()
        except Exception:
            pass

        for pin in {
            self.step,
            self.dir,
            self.en,
            self.rst,
            self.slp,
            self.ms1,
            self.ms2,
            self.ms3,
        }:
            if pin is not None:
                try:
                    lgpio.gpio_free(self.h, pin)
                except Exception:
                    pass

        lgpio.gpiochip_close(self.h)


if __name__ == '__main__':

    
    STEP_PIN = 17
    DIR_PIN = 27
    ENABLE_PIN = 22
    RESET_PIN = 23
    SLEEP_PIN = 24
    MS1_PIN = 5
    MS2_PIN = 6
    MS3_PIN = 13

    driver = A4988(
        chip=0,
        step_pin=STEP_PIN,
        dir_pin=DIR_PIN,
        enable_pin=ENABLE_PIN,
        reset_pin=RESET_PIN,
        sleep_pin=SLEEP_PIN,
        ms1_pin=MS1_PIN,
        ms2_pin=MS2_PIN,
        ms3_pin=MS3_PIN,
        micro_step_length=16,
        init_dir=1,
    )

    period = 0.01
    pulse_width = 0.005

    try:
        driver.enable()
        driver.set_micro_steps(1)
        driver.start_step(step_amount=1, pulse_width=pulse_width, period=period)
        driver.set_dir(int(not driver.dir))
        driver.start_step(step_amount=1, pulse_width=pulse_width, period=period)
    except Exception as e:
        print(e)
        traceback.print_exc()
        driver.release()

        








 
