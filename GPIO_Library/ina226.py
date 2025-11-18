import lgpio
from i2c_device import I2C_Device
from enum import Enum


class REGISTERS(Enum):
    CONFIG         = 0x00  # Configuration register
    SHUNT_VOLTAGE  = 0x01  # Shunt voltage (Vshunt)
    BUS_VOLTAGE    = 0x02  # Bus voltage (Vbus)
    POWER          = 0x03  # Power
    CURRENT        = 0x04  # Current
    CALIBRATION    = 0x05  # Calibration
    MASK_ENABLE    = 0x06  # Alert mask/enable
    ALERT_LIMIT    = 0x07  # Alert limit
    MANUFACTURER_ID = 0xFE
    DIE_ID          = 0xFF


class SHIFTS(Enum):
    RST_SHIFT    = 15   # Reset bit
    AVG_SHIFT    = 9    # Averaging mode bits 11:9
    VBUSCT_SHIFT = 6    # Bus voltage conversion time bits 8:6
    VSHCT_SHIFT  = 3    # Shunt voltage conversion time bits 5:3
    MODE_SHIFT   = 0    # Operating mode bits 2:0


class FIELD_OPTIONS(Enum):
    """
    Bitfield helpers for the INA226 configuration register.
    Values here are already shifted into place so you can OR them.
    """

    # RST (bit 15)
    RST_SYSTEM_RESET = 0x1 << SHIFTS.RST_SHIFT.value  # write 1 to reset (self-clearing)

    # AVG[2:0] bits 11:9 (number of averaged samples)
    AVG_1    = 0x0 << SHIFTS.AVG_SHIFT.value
    AVG_4    = 0x1 << SHIFTS.AVG_SHIFT.value
    AVG_16   = 0x2 << SHIFTS.AVG_SHIFT.value
    AVG_64   = 0x3 << SHIFTS.AVG_SHIFT.value
    AVG_128  = 0x4 << SHIFTS.AVG_SHIFT.value
    AVG_256  = 0x5 << SHIFTS.AVG_SHIFT.value
    AVG_512  = 0x6 << SHIFTS.AVG_SHIFT.value
    AVG_1024 = 0x7 << SHIFTS.AVG_SHIFT.value

    # VBUSCT[2:0] bits 8:6 (bus voltage conversion time)
    # From Table 7-4 (140 µs → 8.244 ms)
    VBUSCT_140US   = 0x0 << SHIFTS.VBUSCT_SHIFT.value
    VBUSCT_204US   = 0x1 << SHIFTS.VBUSCT_SHIFT.value
    VBUSCT_332US   = 0x2 << SHIFTS.VBUSCT_SHIFT.value
    VBUSCT_588US   = 0x3 << SHIFTS.VBUSCT_SHIFT.value
    VBUSCT_1_1MS   = 0x4 << SHIFTS.VBUSCT_SHIFT.value
    VBUSCT_2_116MS = 0x5 << SHIFTS.VBUSCT_SHIFT.value
    VBUSCT_4_156MS = 0x6 << SHIFTS.VBUSCT_SHIFT.value
    VBUSCT_8_244MS = 0x7 << SHIFTS.VBUSCT_SHIFT.value

    # VSHCT[2:0] bits 5:3 (shunt voltage conversion time)
    # Same options as VBUSCT (Table 7-5)
    VSHCT_140US   = 0x0 << SHIFTS.VSHCT_SHIFT.value
    VSHCT_204US   = 0x1 << SHIFTS.VSHCT_SHIFT.value
    VSHCT_332US   = 0x2 << SHIFTS.VSHCT_SHIFT.value
    VSHCT_588US   = 0x3 << SHIFTS.VSHCT_SHIFT.value
    VSHCT_1_1MS   = 0x4 << SHIFTS.VSHCT_SHIFT.value
    VSHCT_2_116MS = 0x5 << SHIFTS.VSHCT_SHIFT.value
    VSHCT_4_156MS = 0x6 << SHIFTS.VSHCT_SHIFT.value
    VSHCT_8_244MS = 0x7 << SHIFTS.VSHCT_SHIFT.value

    # MODE[2:0] bits 2:0 (operating modes, Table 7-6)
    MODE_POWER_DOWN_0        = 0x0 << SHIFTS.MODE_SHIFT.value  # 000
    MODE_SHUNT_TRIG          = 0x1 << SHIFTS.MODE_SHIFT.value  # 001
    MODE_BUS_TRIG            = 0x2 << SHIFTS.MODE_SHIFT.value  # 010
    MODE_SHUNT_BUS_TRIG      = 0x3 << SHIFTS.MODE_SHIFT.value  # 011
    MODE_POWER_DOWN_1        = 0x4 << SHIFTS.MODE_SHIFT.value  # 100
    MODE_SHUNT_CONT          = 0x5 << SHIFTS.MODE_SHIFT.value  # 101
    MODE_BUS_CONT            = 0x6 << SHIFTS.MODE_SHIFT.value  # 110
    MODE_SHUNT_BUS_CONT      = 0x7 << SHIFTS.MODE_SHIFT.value  # 111 (default)


class INA226(I2C_Device):
    """
    INA226 driver using lgpio and your I2C_Device abstraction.

    - Reads shunt voltage, bus voltage, current, and power.
    - Configuration is built via FIELD_OPTIONS enums OR-ed together.
    - Calibration can be computed from shunt resistance and max current.
    """

    # datasheet LSBs
    _SHUNT_LSB_V = 2.5e-6    # 2.5 µV / bit
    _BUS_LSB_V   = 1.25e-3   # 1.25 mV / bit

    def __init__(
        self,
        addr: int,
        i2c_bus: int,
        config_word: int | None = None,
        avg_bits: FIELD_OPTIONS = FIELD_OPTIONS.AVG_1,
        vbusct_bits: FIELD_OPTIONS = FIELD_OPTIONS.VBUSCT_1_1MS,
        vshct_bits: FIELD_OPTIONS = FIELD_OPTIONS.VSHCT_1_1MS,
        mode_bits: FIELD_OPTIONS = FIELD_OPTIONS.MODE_SHUNT_BUS_CONT,
        shunt_resistance_ohm: float | None = None,
        max_expected_current_a: float | None = None,
        current_lsb_a: float | None = None,
    ):
        """
        If config_word is None, it is built from avg_bits, vbusct_bits,
        vshct_bits, and mode_bits.

        If shunt_resistance_ohm and either max_expected_current_a or
        current_lsb_a are given, the Calibration register is programmed and
        current/power scaling is set up.
        """
        super().__init__(addr, i2c_bus)

        # Build configuration word if not explicitly provided
        if config_word is None:
            config_word = (
                avg_bits.value
                | vbusct_bits.value
                | vshct_bits.value
                | mode_bits.value
            )

        self._config = config_word

        # Calibration related fields
        self._r_shunt = shunt_resistance_ohm
        self._current_lsb = None
        self._power_lsb = None  # W/bit

        # Program configuration
        self.write_configuration()

        # Optional: program calibration if enough info is provided
        if shunt_resistance_ohm is not None:
            self.configure_calibration(
                shunt_resistance_ohm=shunt_resistance_ohm,
                max_expected_current_a=max_expected_current_a,
                current_lsb_a=current_lsb_a,
            )

    # ---------- Low-level I2C helpers ----------

    def _write_register_16(self, register: REGISTERS, value: int) -> None:
        handle = super().get_handle()
        msb = (value >> 8) & 0xFF
        lsb = value & 0xFF
        buf = bytes([register.value, msb, lsb])

        res = lgpio.i2c_write_device(handle, buf)
        if isinstance(res, (list, tuple)):
            status = res[0]
        else:
            status = res
        if status < 0:
            raise IOError(f"I2C write error {status} while writing {register.name}")

    def _read_register_16(self, register: REGISTERS) -> int:
        handle = super().get_handle()

        # Set pointer
        res = lgpio.i2c_write_device(handle, bytes([register.value]))
        if isinstance(res, (list, tuple)):
            status = res[0]
        else:
            status = res
        if status < 0:
            raise IOError(f"I2C write error {status} while setting pointer {register.name}")

        count, buf = lgpio.i2c_read_device(handle, 2)
        if count < 0 or count != 2:
            raise IOError(f"I2C read error {count} while reading {register.name}")
        return (buf[0] << 8) | buf[1]

    # ---------- Configuration / calibration ----------

    def write_configuration(self, config: int | None = None) -> None:
        """
        Write CONFIG register (00h). If config is None, uses self._config.
        """
        if config is None:
            config = self._config
        else:
            self._config = config

        self._write_register_16(REGISTERS.CONFIG, config)

    def get_config(self) -> int:
        return self._config

    def configure_calibration(
        self,
        shunt_resistance_ohm: float,
        max_expected_current_a: float | None = None,
        current_lsb_a: float | None = None,
    ) -> None:
        """
        Program the Calibration register and set current/power LSBs.

        You can either:
        - Provide max_expected_current_a → we compute a "nice" Current_LSB
        - Provide current_lsb_a directly (in A/bit)

        Calibration math (datasheet):
            Current_LSB ≈ I_max / 2^15
            CAL = 0.00512 / (Current_LSB * RSHUNT)
        """
        if shunt_resistance_ohm <= 0:
            raise ValueError("shunt_resistance_ohm must be > 0")

        self._r_shunt = shunt_resistance_ohm

        if current_lsb_a is None:
            if max_expected_current_a is None or max_expected_current_a <= 0:
                raise ValueError(
                    "Provide either current_lsb_a or max_expected_current_a > 0"
                )

            # Smallest LSB that still covers max current
            raw_lsb = max_expected_current_a / (1 << 15)

            # Round up to a "nice" number (e.g., 1 mA, 2 mA, etc.)
            # For your use-case, 1 mA granularity is usually fine.
            current_lsb_a = max(raw_lsb, 1e-3)
        self._current_lsb = current_lsb_a
        self._power_lsb = 25.0 * self._current_lsb  # W/bit

        cal_float = 0.00512 / (self._current_lsb * self._r_shunt)
        cal_reg = int(cal_float)
        if cal_reg <= 0 or cal_reg > 0xFFFF:
            raise ValueError(
                f"Computed calibration value out of range: {cal_reg} (0x{cal_reg:04X})"
            )

        self._write_register_16(REGISTERS.CALIBRATION, cal_reg)

    # ---------- Raw register reads (signed/unsigned) ----------

    @staticmethod
    def _to_signed_16(value: int) -> int:
        if value & 0x8000:
            value -= 1 << 16
        return value

    # ---------- High-level measurement helpers ----------

    def read_shunt_voltage_raw(self) -> int:
        """
        Raw shunt voltage register (two's complement).
        LSB = 2.5 µV.
        """
        raw = self._read_register_16(REGISTERS.SHUNT_VOLTAGE)
        return self._to_signed_16(raw)

    def read_shunt_voltage(self) -> float:
        """
        Shunt voltage in volts.
        """
        raw = self.read_shunt_voltage_raw()
        return raw * self._SHUNT_LSB_V

    def read_bus_voltage_raw(self) -> int:
        """
        Raw bus voltage register.
        LSB = 1.25 mV; D15 is always 0.
        """
        raw = self._read_register_16(REGISTERS.BUS_VOLTAGE)
        return raw & 0x7FFF  # MSB is always 0 for bus voltage

    def read_bus_voltage(self) -> float:
        """
        Bus voltage in volts.
        """
        raw = self.read_bus_voltage_raw()
        return raw * self._BUS_LSB_V

    def read_current_raw(self) -> int:
        """
        Raw current register (two's complement).
        Only valid if calibration has been programmed.
        """
        raw = self._read_register_16(REGISTERS.CURRENT)
        return self._to_signed_16(raw)

    def read_current(self) -> float:
        """
        Current in amperes.
        Requires calibration (current_lsb_a set via configure_calibration).
        """
        if self._current_lsb is None:
            raise RuntimeError("Current LSB is not configured (calibration not set).")
        raw = self.read_current_raw()
        return raw * self._current_lsb

    def read_power_raw(self) -> int:
        """
        Raw power register.
        Only valid if calibration has been programmed.
        """
        return self._read_register_16(REGISTERS.POWER)

    def read_power(self) -> float:
        """
        Power in watts.
        Requires calibration (power_lsb configured from current_lsb).
        """
        if self._power_lsb is None:
            raise RuntimeError("Power LSB is not configured (calibration not set).")
        raw = self.read_power_raw()
        return raw * self._power_lsb

    # Convenience read: all main quantities at once
    def read_all(self) -> tuple[float, float, float | None, float | None]:
        """
        Returns (bus_voltage_V, shunt_voltage_V, current_A or None, power_W or None)
        """
        vbus = self.read_bus_voltage()
        vshunt = self.read_shunt_voltage()
        current = power = None
        if self._current_lsb is not None:
            current = self.read_current()
        if self._power_lsb is not None:
            power = self.read_power()
        return vbus, vshunt, current, power


if __name__ == "__main__":
    import time

    # Example usage:
    # - INA226 at address 0x40 (depends on A0/A1 wiring)
    # - I2C bus 1
    # - 0.01 Ω shunt, expect up to ~5 A
    addr = 0x40
    bus = 1
    r_shunt = 0.01
    i_max = 5.0

    try:
        ina = INA226(
            addr=addr,
            i2c_bus=bus,
            avg_bits=FIELD_OPTIONS.AVG_16,
            vbusct_bits=FIELD_OPTIONS.VBUSCT_1_1MS,
            vshct_bits=FIELD_OPTIONS.VSHCT_1_1MS,
            mode_bits=FIELD_OPTIONS.MODE_SHUNT_BUS_CONT,
            shunt_resistance_ohm=r_shunt,
            max_expected_current_a=i_max,
        )

        print("INA226 configured; starting reads...")
        start_time = time.time()
        res_arr = []

        while True:
            t = time.time() - start_time
            try:
                vbus, vshunt, current, power = ina.read_all()

                t_str = f"{t:.3f}"
                vbus_str = f"{vbus:.5f}"
                vshunt_str = f"{vshunt:.6f}"
                curr_str = "N/A" if current is None else f"{current:.5f}"
                pwr_str = "N/A" if power is None else f"{power:.5f}"

                print(
                    f"t={t_str}s  Vbus={vbus_str} V  "
                    f"Vshunt={vshunt_str} V  I={curr_str} A  P={pwr_str} W"
                )

                res_arr.append(
                    [t_str, vbus_str, vshunt_str, curr_str, pwr_str]
                )
                time.sleep(0.5)
            except Exception as e:
                print(f"Error while reading data at t={t:.3f}s: {e}")
                res_arr.append([f"{t:.3f}", "read error"])

    except KeyboardInterrupt:
        print("closing bus")
        try:
            ina.close()
        except Exception:
            pass

        ts = int(time.time())
        filename = f"ina226_results_{ts}.txt"
        with open(filename, "a") as f:
            for row in res_arr:
                f.write(
                    f"time: {row[0]}, "
                    f"Vbus: {row[1]}, Vshunt: {row[2]}, "
                    f"I: {row[3]}, P: {row[4]}\n"
                )
