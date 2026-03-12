import lgpio
import time

h = lgpio.gpiochip_open(0)
lgpio.gpio_write(h, 23, 0)
lgpio.gpio_free(h, 23)
time.sleep(10)
lgpio.gpiochip_close(h)
