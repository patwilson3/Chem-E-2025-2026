import lgpio
from i2c_device import I2C_Device
from enum import Enum

'''
CONFIG REGISTER STRUCTURE (from docs), this is where we write our configuraitons

Bit[15] 

OS: Operational status/single-shot conversion start
This bit determines the operational status of the device.
This bit can only be written when in power-down mode.
For a write status:
0 : No effect
1 : Begin a single conversion (when in power-down mode)
For a read status:
0 : Device is currently performing a conversion
1 : Device is not currently performing a conversion

Bits[14:12]

MUX[2:0]: Input multiplexer configuration (ADS1115 only)
These bits configure the input multiplexer. They serve no function on the ADS1113/4.
000 : AINP = AIN0 and AINN = AIN1 (default) 100 : AINP = AIN0 and AINN = GND
001 : AINP = AIN0 and AINN = AIN3 101 : AINP = AIN1 and AINN = GND
010 : AINP = AIN1 and AINN = AIN3 110 : AINP = AIN2 and AINN = GND
011 : AINP = AIN2 and AINN = AIN3 111 : AINP = AIN3 and AINN = GND

Bits[11:9]

PGA[2:0]: Programmable gain amplifier configuration (ADS1114 and ADS1115 only)
These bits configure the programmable gain amplifier. They serve no function on the ADS1113.
000 : FS = ±6.144V(1) 100 : FS = ±0.512V
001 : FS = ±4.096V(1) 101 : FS = ±0.256V
010 : FS = ±2.048V (default) 110 : FS = ±0.256V
011 : FS = ±1.024V

Bit[8]

MODE: Device operating mode
This bit controls the current operational mode of the ADS1113/4/5.
0 : Continuous conversion mode
1 : Power-down single-shot mode (default)

Bits[7:5]

DR[2:0]: Data rate
These bits control the data rate setting.
000 : 8SPS 001 : 16SPS 010 : 32SPS 011 : 64SPS 100 : 128SPS (default)
101 : 250SPS
110 : 475SPS
111 : 860SPS

Bit[4]

COMP_MODE: Comparator mode (ADS1114 and ADS1115 only)
This bit controls the comparator mode of operation. It changes whether the comparator is implemented as a
traditional comparator (COMP_MODE = '0') or as a window comparator (COMP_MODE = '1'). It serves no
function on the ADS1113.
0 : Traditional comparator with hysteresis (default)
1 : Window comparator

Bit[3]

COMP_POL: Comparator polarity (ADS1114 and ADS1115 only)
This bit controls the polarity of the ALERT/RDY pin. When COMP_POL = '0' the comparator output is active
low. When COMP_POL='1' the ALERT/RDY pin is active high. It serves no function on the ADS1113.
0 : Active low (default)
1 : Active high

Bit [2]

COMP_LAT: Latching comparator (ADS1114 and ADS1115 only)
This bit controls whether the ALERT/RDY pin latches once asserted or clears once conversions are within the
margin of the upper and lower threshold values. When COMP_LAT = '0', the ALERT/RDY pin does not latch
when asserted. When COMP_LAT = '1', the asserted ALERT/RDY pin remains latched until conversion data
are read by the master or an appropriate SMBus alert response is sent by the master, the device responds with
its address, and it is the lowest address currently asserting the ALERT/RDY bus line. This bit serves no
function on the ADS1113.
0 : Non-latching comparator (default)
1 : Latching comparator

Bits[1:0]

COMP_QUE: Comparator queue and disable (ADS1114 and ADS1115 only)
These bits perform two functions. When set to '11', they disable the comparator function and put the
ALERT/RDY pin into a high state. When set to any other value, they control the number of successive
conversions exceeding the upper or lower thresholds required before asserting the ALERT/RDY pin. They
serve no function on the ADS1113.
00 : Assert after one conversion
01 : Assert after two conversions
10 : Assert after four conversions
11 : Disable comparator (default)
'''


class REGISTERS(Enum):
    CONVERSION_REG = 0x00 #read results (16 bit)
    CONFIG_REG = 0x01 #wrie config word (16 bit)
    REG_LO_THRESH = 0x02 #(low threshold for comp)
    REG_HI_THRESH = 0x03 #(high threshold for comp)

class SHIFTS(Enum):
    OS_SHIFT   = 15  # Operational status / start conversion
    MUX_SHIFT  = 12  # Input multiplexer config
    PGA_SHIFT  = 9   # Programmable gain amplifier
    MODE_SHIFT = 8   # Mode (continuous/single-shot)
    DR_SHIFT   = 5   # Data rate
    COMP_MODE_SHIFT = 4
    COMP_POL_SHIFT  = 3
    COMP_LAT_SHIFT  = 2
    COMP_QUE_SHIFT  = 0

class FIELD_OPTIONS(Enum):
    '''FILED OPTIONS'''
    #OS bit 15
    OS_SINGLE   = 0x1 << SHIFTS.OS_SHIFT   # Write 1 to start single conversion
    OS_BUSY     = 0x0 << SHIFTS.OS_SHIFT   # Read: 0 = busy
    OS_READY    = 0x1 << SHIFTS.OS_SHIFT   # Read: 1 = ready

    #MUX bits 14-12
    MUX_AIN0_AIN1 = 0x0 << SHIFTS.MUX_SHIFT  # Differential P = AIN0, N = AIN1
    MUX_AIN0_AIN3 = 0x1 << SHIFTS.MUX_SHIFT
    MUX_AIN1_AIN3 = 0x2 << SHIFTS.MUX_SHIFT
    MUX_AIN2_AIN3 = 0x3 << SHIFTS.MUX_SHIFT
    MUX_AIN0_GND  = 0x4 << SHIFTS.MUX_SHIFT  # Single-ended AIN0
    MUX_AIN1_GND  = 0x5 << SHIFTS.MUX_SHIFT
    MUX_AIN2_GND  = 0x6 << SHIFTS.MUX_SHIFT
    MUX_AIN3_GND  = 0x7 << SHIFTS.MUX_SHIFT

    #PGA bits 11-9 (GAIN, to avoid chipping, smaller the Gain, finer the resolution is, so for out input voltage we will aim for PGA 2-4)

    PGA_6_144V = 0x0 << SHIFTS.PGA_SHIFT  # ±6.144 V
    PGA_4_096V = 0x1 << SHIFTS.PGA_SHIFT  # ±4.096 V
    PGA_2_048V = 0x2 << SHIFTS.PGA_SHIFT  # ±2.048 V (default)
    PGA_1_024V = 0x3 << SHIFTS.PGA_SHIFT  # ±1.024 V
    PGA_0_512V = 0x4 << SHIFTS.PGA_SHIFT  # ±0.512 V
    PGA_0_256V = 0x5 << SHIFTS.PGA_SHIFT  # ±0.256 V

    #Mode bit 8

    MODE_CONTINUOUS = 0x0 << SHIFTS.MODE_SHIFT
    MODE_SINGLE     = 0x1 << SHIFTS.MODE_SHIFT

    #Data rate bits 7-5

    DR_8SPS   = 0x0 << SHIFTS.DR_SHIFT
    DR_16SPS  = 0x1 << SHIFTS.DR_SHIFT
    DR_32SPS  = 0x2 << SHIFTS.DR_SHIFT
    DR_64SPS  = 0x3 << SHIFTS.DR_SHIFT
    DR_128SPS = 0x4 << SHIFTS.DR_SHIFT  # default
    DR_250SPS = 0x5 << SHIFTS.DR_SHIFT
    DR_475SPS = 0x6 << SHIFTS.DR_SHIFT
    DR_860SPS = 0x7 << SHIFTS.DR_SHIFT

    COMP_MODE_TRAD   = 0x0 << SHIFTS.COMP_MODE_SHIFT
    COMP_MODE_WINDOW = 0x1 << SHIFTS.COMP_MODE_SHIFT

    COMP_POL_ACTIVE_LOW  = 0x0 << SHIFTS.COMP_POL_SHIFT
    COMP_POL_ACTIVE_HIGH = 0x1 << SHIFTS.COMP_POL_SHIFT

    COMP_LAT_NONLATCH = 0x0 << SHIFTS.COMP_LAT_SHIFT
    COMP_LAT_LATCH    = 0x1 << SHIFTS.COMP_LAT_SHIFT

    COMP_QUE_1CONV = 0x0 << SHIFTS.COMP_QUE_SHIFT
    COMP_QUE_2CONV = 0x1 << SHIFTS.COMP_QUE_SHIFT
    COMP_QUE_4CONV = 0x2 << SHIFTS.COMP_QUE_SHIFT
    COMP_QUE_DISABLE = 0x3 << SHIFTS.COMP_QUE_SHIFT


class ASD1115(I2C_Device):    

    ''' example usag of using a config var:
        say you want:
        - single shot
        - channel AIN0 vs GND
        - Gain = +- 4.096v
        - 128 sps
        - comparator disabled

        we will build a word as follows

        config = 
            (
                FIELD_OPTIONS.OS_SINGLE | 
                FIELD_OPTIONS.MUX_AIN0_GND |
                FIELD_OPTIONS.PGA_4_096V | 
                FIELD_OPTIONS.MODE_SINGLE |
                FIELD_OPTIONS.DR_128SPS |
                FIELD_OPTIONS.COMP_QUE DISABLE
            )
        
        since we can only send 8 bits at a time we will send by MSB and LSB
        msb = (config >> 8) & 0xFF
        lsb = (config) & 0xFF

        what we will most likely be using

        config = 
            (
                FIELD_OPTIONS.BUSY | 
                FIELD_OPTIONS.MUX_AIN0_GND |
                FIELD_OPTIONS.PGA_2_048V | 
                FIELD_OPTIONS.MODE_CONTINUOUS |
                FIELD_OPTIONS.DR_128SPS |
                FIELD_OPTIONS.COMP_QUE DISABLE
            )
    
    '''

    def __init__(self, addr, i2c_bus, os_bit=FIELD_OPTIONS.BUSY, mux_bit=FIELD_OPTIONS.MUX_AIN0_GND, pga_bit=FIELD_OPTIONS.PGA_2_048V, mode_bit=FIELD_OPTIONS.MODE_CONTINUOUS, sps_bit=FIELD_OPTIONS.DR_128SPS, comp_bit=FIELD_OPTIONS.COMP_QUE_DISABLE):
        super().__init__(addr, i2c_bus)
        self._config = (os_bit | mux_bit | pga_bit | mode_bit | sps_bit | comp_bit)

