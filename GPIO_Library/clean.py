import lgpio

h = lgpio.gpiochip_open(0)
for i in range(4, 28, 1):
	try:
		lgpio.gpio_claim_output(h, i)
		lgpio.gpio_write(h, i, 0)
		lgpio.gpio_free(h, i)
	except Exception as e:
		continue

lgpio.gpiochip_close(h)
