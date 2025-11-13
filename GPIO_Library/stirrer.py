import lgpio
import time
import traceback

class Stirrer:
    def __init__(self, chip, pin):
        self.h = lgpio.gpiochip_open(chip)
        self.pin = pin
        
        lgpio.gpio_claim_output(self.h, pin)

    def spin(self, pwm_frequency, pwm_duty_cycle, pulse_offset=0, pulse_cycles=0):
        lgpio.tx_pwm(self.h, self.pin, pwm_frequency, pwm_duty_cycle, pulse_offset, pulse_cycles)

    def stop(self):
        lgpio.tx_pwm(self.h, self.pin, 0, 0)
        lgpio.gpio_write(self.h, self.pin, 0)

    def clear(self):
        lgpio.gpio_free(self.h, self.pin)


if __name__ == '__main__':
    try:
        stirrer = Stirrer(0, 12)
        stirrer.spin(35, 2000, 2, 0)
        time.sleep(10)
        stirrer.stop()
    except Exception as e:
        traceback.print_exc()

    finally:
        stirrer.clear()
    


