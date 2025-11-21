import os
import sys
import time
from datetime import datetime
from picamera2 import Picamera2, Preview
from led_spi import LED_Spi


try:
	picam2 = Picamera2()
	picam2.start_preview(Preview.QT)
	picam2.start()
	strip = LED_Spi(num_leds=16)
	strip.clear()
	time.sleep(1000)
	
except Exception as e:
	pass
	
finally:
	picam2.stop_preview()
	picam2.close()
	strip.clear()
	strip.close()
    
    

