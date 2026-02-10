"""
A4988 stepper driver control from Raspberry Pi (Python 3.11) using lgpio.

WIRING (typical):
- Pi GND  -> A4988 GND (logic) AND motor power GND (common ground)
- Pi STEP -> A4988 STEP
- Pi DIR  -> A4988 DIR
- Pi EN   -> A4988 ENABLE (optional; active-low)
- A4988 VMOT -> motor supply + (e.g., 8–35V), with electrolytic cap near driver
- A4988 1A/1B/2A/2B -> motor coils

NOTES:
- Set A4988 current limit (Vref) before running the motor.
- STEP pulse high time minimum is ~1µs; we use 5µs for safety.
- This software pulse generator is reliable for moderate step rates.
  If you need very high step rates, use DMA-based libraries (e.g., pigpio waves),
  or offload stepping to a microcontroller.
"""

from __future__ import annotations
import time
import lgpio


class A4988Stepper:
    def __init__(
        self,
        step_pin: int,
        dir_pin: int,
        enable_pin: int | None = None,
        chip: int = 0,
        step_high_us: int = 5,
    ):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.chip = chip
        self.step_high_s = max(step_high_us, 2) / 1_000_000.0  # seconds
        self.h: int | None = None

    def open(self) -> None:
        if self.h is not None:
            return
        self.h = lgpio.gpiochip_open(self.chip)

        # Claim pins once (avoid GPIO busy errors)
        lgpio.gpio_claim_output(self.h, self.step_pin, 0)
        lgpio.gpio_claim_output(self.h, self.dir_pin, 0)

        if self.enable_pin is not None:
            lgpio.gpio_claim_output(self.h, self.enable_pin, 1)  # disabled by default (EN high)

    def close(self) -> None:
        if self.h is None:
            return
        try:
            if self.enable_pin is not None:
                lgpio.gpio_write(self.h, self.enable_pin, 1)  # disable
                lgpio.gpio_free(self.h, self.enable_pin)
            lgpio.gpio_write(self.h, self.step_pin, 0)
            lgpio.gpio_free(self.h, self.step_pin)
            lgpio.gpio_free(self.h, self.dir_pin)
        finally:
            lgpio.gpiochip_close(self.h)
            self.h = None

    def enable(self) -> None:
        if self.h is None:
            self.open()
        if self.enable_pin is not None:
            lgpio.gpio_write(self.h, self.enable_pin, 0)  # active-low

    def disable(self) -> None:
        if self.h is None:
            return
        if self.enable_pin is not None:
            lgpio.gpio_write(self.h, self.enable_pin, 1)  # active-low

    def set_direction(self, clockwise: bool) -> None:
        if self.h is None:
            self.open()
        lgpio.gpio_write(self.h, self.dir_pin, 1 if clockwise else 0)

    def step(
        self,
        steps: int,
        step_rate_sps: float,
        clockwise: bool = True,
        accel_sps2: float = 0.0,
    ) -> None:
        """
        Move 'steps' steps at 'step_rate_sps' (steps/sec).
        Optional simple trapezoidal accel/decel when accel_sps2 > 0.

        accel_sps2 is acceleration in steps/sec^2.
        """
        if steps <= 0:
            return
        if step_rate_sps <= 0:
            raise ValueError("step_rate_sps must be > 0")

        if self.h is None:
            self.open()

        self.set_direction(clockwise)
        self.enable()

        # Timing parameters
        target_rate = float(step_rate_sps)
        accel = float(accel_sps2)

        # Helper to emit one step pulse
        def pulse_once():
            lgpio.gpio_write(self.h, self.step_pin, 1)
            time.sleep(self.step_high_s)
            lgpio.gpio_write(self.h, self.step_pin, 0)

        # No acceleration: constant step period
        if accel <= 0.0:
            period = 1.0 / target_rate
            # Ensure low time is not negative
            low_time = max(0.0, period - self.step_high_s)

            next_t = time.perf_counter()
            for _ in range(steps):
                # schedule-based loop reduces drift vs sleep(period)
                now = time.perf_counter()
                if now < next_t:
                    time.sleep(next_t - now)
                pulse_once()
                next_t += period
                if low_time > 0:
                    # We already slept to align the leading edge; keep pulses from being too wide
                    pass
            return

        # With acceleration: trapezoid profile (accelerate then decelerate)
        # Compute steps needed to ramp from 0 to target_rate at accel:
        # v^2 = 2*a*x  => x = v^2 / (2a)
        ramp_steps = int((target_rate * target_rate) / (2.0 * accel))
        ramp_steps = max(1, ramp_steps)

        # If the move is short, we do a triangular profile
        if 2 * ramp_steps > steps:
            ramp_steps = steps // 2

        cruise_steps = steps - 2 * ramp_steps

        # Accelerate
        curr_rate = 1.0  # start at 1 sps to avoid division by zero
        for i in range(ramp_steps):
            # v = sqrt(2*a*x)
            x = i + 1
            curr_rate = (2.0 * accel * x) ** 0.5
            curr_rate = min(curr_rate, target_rate)
            period = 1.0 / curr_rate
            low_time = max(0.0, period - self.step_high_s)
            pulse_once()
            if low_time > 0:
                time.sleep(low_time)

        # Cruise
        if cruise_steps > 0:
            period = 1.0 / target_rate
            low_time = max(0.0, period - self.step_high_s)
            for _ in range(cruise_steps):
                pulse_once()
                if low_time > 0:
                    time.sleep(low_time)

        # Decelerate (mirror accelerate)
        for i in range(ramp_steps, 0, -1):
            x = i
            curr_rate = (2.0 * accel * x) ** 0.5
            curr_rate = max(1.0, min(curr_rate, target_rate))
            period = 1.0 / curr_rate
            low_time = max(0.0, period - self.step_high_s)
            pulse_once()
            if low_time > 0:
                time.sleep(low_time)

    def __enter__(self) -> "A4988Stepper":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def demo():
    # Example pins (BCM numbering):
    STEP = 12
    DIR = 27
    EN = 26  # optional

    steps_per_rev = 200  # 1.8° motor, full-step
    microstep = 1        # set to 2/4/8/16 depending on MS1-3 wiring
    effective_steps = steps_per_rev * microstep

    with A4988Stepper(step_pin=STEP, dir_pin=DIR, enable_pin=EN) as m:
        # One revolution clockwise at 800 steps/sec, with accel 2000 steps/s^2
        m.step(effective_steps, step_rate_sps=800, clockwise=True, accel_sps2=2000)

        time.sleep(0.5)

        # Half revolution counterclockwise, constant speed
        m.step(effective_steps // 2, step_rate_sps=600, clockwise=False)


if __name__ == "__main__":
    demo()
