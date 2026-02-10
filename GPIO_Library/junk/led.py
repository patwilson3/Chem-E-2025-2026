import board
import neopixel_spi as neopixel
import time
import traceback

class LED:
    def __init__(self, num_led):
        self.pixels = neopixel.NeoPixel_SPI(clock=board.SCLK, MOSI=board.MOSI, 
                                            n=num_led, pixel_order=neopixel.GRB, auto_write=True)

    def on(self):
        self.pixels.fill(191, 191, 191)
        self.pixels.show()

    def off(self):
        self.pixels.fill(0, 0, 0)
        self.pixels.show()


if __name__ == '__main__':

    try:
        led = LED(16)
        led.on()
        time.sleep(10)
        led.off()

    except Exception as e:
        traceback.print_exc()

    finally:
        led.off()