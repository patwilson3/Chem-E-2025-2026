"""
Raspberry Pi 5 + LS7366R (SPI) encoder reader + wheel speed + RPM

Matches your spidev_test settings:
- SPI mode 0
- 8 bits/word
- 500 kHz

LS7366R config:
- MDR0 = 0x03  (x4 quadrature, free-run)
- MDR1 = 0x00  (4-byte counter)

Your calibration:
- 3575.0855 counts per wheel revolution
- Wheel diameter: 70 mm

Output:
- count (signed 32-bit)
- speed (m/s and km/h)
- rpm (wheel RPM)

Behavior:
- Resets (clears) the counter every time the program starts.
"""

import math
import time
import spidev
from .dashboard import Dashboard

DASH = Dashboard()

# -------- LS7366R command bytes --------
CLR_CNTR = 0x20

RD_MDR0  = 0x48
WR_MDR0  = 0x88

RD_MDR1  = 0x50
WR_MDR1  = 0x90

RD_CNTR  = 0x60

# -------- Desired configuration --------
MDR0_VAL = 0x03  # x4 quadrature, free-run
MDR1_VAL = 0x00  # 4-byte counter

# -------- Your wheel calibration --------
COUNTS_PER_REV = 3575.0855          # counts per wheel revolution (your value)
WHEEL_DIAMETER_M = 0.070            # 70 mm
WHEEL_CIRC_M = math.pi * WHEEL_DIAMETER_M


def u32_to_i32(x: int) -> int:
    """Interpret unsigned 32-bit as signed 32-bit."""
    return x - 0x100000000 if x & 0x80000000 else x


class LS7366R:
    def __init__(self, bus=0, cs=0, max_hz=500_000):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, cs)
        self.spi.mode = 0
        self.spi.bits_per_word = 8
        self.spi.max_speed_hz = max_hz

    def close(self):
        self.spi.close()

    def write_reg(self, write_cmd: int, value: int):
        self.spi.xfer2([write_cmd, value & 0xFF])

    def read_reg(self, read_cmd: int) -> int:
        rx = self.spi.xfer2([read_cmd, 0x00])
        return rx[1]

    def clear_counter(self):
        self.spi.xfer2([CLR_CNTR])

    def read_counter_u32(self) -> int:
        rx = self.spi.xfer2([RD_CNTR, 0x00, 0x00, 0x00, 0x00])
        b1, b2, b3, b4 = rx[1], rx[2], rx[3], rx[4]
        return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4

    def init_device(self, clear_at_start=True, verify=True):
        self.write_reg(WR_MDR0, MDR0_VAL)
        self.write_reg(WR_MDR1, MDR1_VAL)

        if clear_at_start:
            self.clear_counter()

        if verify:
            mdr0 = self.read_reg(RD_MDR0)
            mdr1 = self.read_reg(RD_MDR1)
            print(f"MDR0 readback: 0x{mdr0:02X} (expected 0x{MDR0_VAL:02X})")
            print(f"MDR1 readback: 0x{mdr1:02X} (expected 0x{MDR1_VAL:02X})")
            
def speed_worker(event):
    enc = LS7366R(bus=0, cs=0, max_hz=500_000)  # change cs=1 if using /dev/spidev0.1
    try:
        # Clear count every run 
        enc.init_device(clear_at_start=True, verify=True)

        last_count = u32_to_i32(enc.read_counter_u32())
        last_t = time.monotonic()

        print("\ncount, speed_m_s, speed_km_h, rpm")
        dist = 0
        
        while not event.is_set():
            time.sleep(0.05)  # update rate (s)

            now_t = time.monotonic()
            now_count = u32_to_i32(enc.read_counter_u32())

            dt = now_t - last_t
            dc = now_count - last_count

            # counts -> revolutions during this interval
            rev = dc / COUNTS_PER_REV

            # distance traveled during this interval
            dist_m = rev * WHEEL_CIRC_M
            
            dist += dist_m

            # speed
            speed_m_s = dist_m / dt if dt > 0 else 0.0
            speed_km_h = speed_m_s * 3.6

            # rpm (wheel)
            rps = rev / dt if dt > 0 else 0.0
            rpm = rps * 60.0

            print(f"{now_count}, {speed_m_s:.4f}, {speed_km_h:.2f}, {rpm:.2f}")

            last_count = now_count
            last_t = now_t
            
            DASH.update_speed(round(dist, 4)*(-1/2), round(speed_m_s, 4)*(-1/2), round(rpm, 4)*(-1/2))

    finally:
        enc.close()



def main():
    enc = LS7366R(bus=0, cs=0, max_hz=500_000)  # change cs=1 if using /dev/spidev0.1
    try:
        # Clear count every run 
        enc.init_device(clear_at_start=True, verify=True)

        last_count = u32_to_i32(enc.read_counter_u32())
        last_t = time.monotonic()

        print("\ncount, speed_m_s, speed_km_h, rpm")
        dist = 0
        
        while True:
            time.sleep(0.05)  # update rate (s)

            now_t = time.monotonic()
            now_count = u32_to_i32(enc.read_counter_u32())

            dt = now_t - last_t
            dc = now_count - last_count

            # counts -> revolutions during this interval
            rev = dc / COUNTS_PER_REV

            # distance traveled during this interval
            dist_m = rev * WHEEL_CIRC_M
            
            dist += dist_m

            # speed
            speed_m_s = dist_m / dt if dt > 0 else 0.0
            speed_km_h = speed_m_s * 3.6

            # rpm (wheel)
            rps = rev / dt if dt > 0 else 0.0
            rpm = rps * 60.0

            print(f"{now_count}, {speed_m_s:.4f}, {speed_km_h:.2f}, {rpm:.2f}")

            last_count = now_count
            last_t = now_t
            
            DASH.update_speed(round(dist, 4), round(speed_m_s, 4), round(rpm, 4))

    finally:
        enc.close()


if __name__ == "__main__":
    main()
