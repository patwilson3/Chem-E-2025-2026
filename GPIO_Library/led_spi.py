import lgpio, atexit, time
from control import event

class LED_Spi:
    """
    WS2812 over SPI using lgpio.
    Uses a 1-byte-per-bit encoding at ~6.4 MHz SPI.
    """
    def __init__(self, num_leds=60, spi_bus=0, spi_cs=0, spi_hz=6_400_000):
        self.num_leds = num_leds
        self.spi_h = lgpio.spi_open(spi_bus, spi_cs, spi_hz)  # /dev/spidev0.0
        atexit.register(self.close)

        # Encoding bytes for 0/1 at ~6.4 MHz:
        # tune if colors flicker: try (0xC0, 0xF8) or (0x88, 0xEE)
        self.bit0 = 0xC0
        self.bit1 = 0xF8

    def _encode24(self, r, g, b):
        # WS2812 expects GRB
        out = bytearray()
        for c in (g, r, b):
            for i in range(8):
                out.append(self.bit1 if (c >> (7 - i)) & 1 else self.bit0)
        return out

    def _xfer(self, data: bytes):
        lgpio.spi_write(self.spi_h, data)

    def fill(self, r, g, b):
        frame = bytearray()
        enc = self._encode24(r, g, b)
        frame.extend(enc * self.num_leds)
        self._xfer(frame)

    def show_white_75(self):
        self.fill(191, 191, 191)

    def clear(self):
        # Send “all zeros” frame to latch off
        # 24 encoded bytes per LED for 1-bit/byte encoding
        self._xfer(bytes(self.num_leds * 24))

    def close(self):
        try:
            self.clear()      # turn LEDs off
        finally:
            lgpio.spi_close(self.spi_h)
            
            
def call_leds():
    strip = LED_Spi(num_leds=60)
    strip.show_white_75()
    while not event.is_set():
        pass
    strip.clear()  # optional; close() also clears
    strip.close()

# Example
if __name__ == "__main__":
    strip = LED_Spi(num_leds=60)
    strip.show_white_75()
    time.sleep(5)
    strip.clear()  # optional; close() also clears
    strip.close()
