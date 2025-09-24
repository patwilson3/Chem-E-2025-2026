import lgpio
from i2c_device import I2C_Device

class ASD1115(I2C_Device):

    '''REGISTERS'''

    CONVERSION_REG = 0x00 #read results (16 bit)
    CONFIG_REG = 0x01 #wrie config word (16 bit)
    REG_LO_THRESH = 0x02 #(low threshold for comp)
    REG_HI_THRESH = 0x03 #(high threshold for comp)

    '''BIT POSITIONS (for shifts)'''

    OS_SHIFT   = 15  # Operational status / start conversion
    MUX_SHIFT  = 12  # Input multiplexer config
    PGA_SHIFT  = 9   # Programmable gain amplifier
    MODE_SHIFT = 8   # Mode (continuous/single-shot)
    DR_SHIFT   = 5   # Data rate
    COMP_MODE_SHIFT = 4
    COMP_POL_SHIFT  = 3
    COMP_LAT_SHIFT  = 2
    COMP_QUE_SHIFT  = 0

    '''FILED OPTIONS'''
    #OS bit 15
    OS_SINGLE   = 0x1 << OS_SHIFT   # Write 1 to start single conversion
    OS_BUSY     = 0x0 << OS_SHIFT   # Read: 0 = busy
    OS_READY    = 0x1 << OS_SHIFT   # Read: 1 = ready

    #MUX bits 14-12
    MUX_AIN0_AIN1 = 0x0 << MUX_SHIFT  # Differential P = AIN0, N = AIN1
    MUX_AIN0_AIN3 = 0x1 << MUX_SHIFT
    MUX_AIN1_AIN3 = 0x2 << MUX_SHIFT
    MUX_AIN2_AIN3 = 0x3 << MUX_SHIFT
    MUX_AIN0_GND  = 0x4 << MUX_SHIFT  # Single-ended AIN0
    MUX_AIN1_GND  = 0x5 << MUX_SHIFT
    MUX_AIN2_GND  = 0x6 << MUX_SHIFT
    MUX_AIN3_GND  = 0x7 << MUX_SHIFT

    #PGA bits 11-9 (GAIN, to avoid chipping, smaller the Gain, finer the resolution is, so for out input voltage we will aim for PGA 2-4)

    PGA_6_144V = 0x0 << PGA_SHIFT  # ±6.144 V
    PGA_4_096V = 0x1 << PGA_SHIFT  # ±4.096 V
    PGA_2_048V = 0x2 << PGA_SHIFT  # ±2.048 V (default)
    PGA_1_024V = 0x3 << PGA_SHIFT  # ±1.024 V
    PGA_0_512V = 0x4 << PGA_SHIFT  # ±0.512 V
    PGA_0_256V = 0x5 << PGA_SHIFT  # ±0.256 V

    #Mode bit 8

    MODE_CONTINUOUS = 0x0 << MODE_SHIFT
    MODE_SINGLE     = 0x1 << MODE_SHIFT

    #Data rate bits 7-5

    DR_8SPS   = 0x0 << DR_SHIFT
    DR_16SPS  = 0x1 << DR_SHIFT
    DR_32SPS  = 0x2 << DR_SHIFT
    DR_64SPS  = 0x3 << DR_SHIFT
    DR_128SPS = 0x4 << DR_SHIFT  # default
    DR_250SPS = 0x5 << DR_SHIFT
    DR_475SPS = 0x6 << DR_SHIFT
    DR_860SPS = 0x7 << DR_SHIFT

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
                OS_SINGLE | 
                MUX_AIN0_GND |
                PGA_4_096V | 
                MODE_SINGLE |
                DR_128SPS |
                COMP_QUE DISABLE
            )
        
        since we can only send 8 bits at a time we will send by MSB and LSB
        msb = (config >> 8) & 0xFF
        lsb = (config) & 0xFF
    
    '''

    def __init__(self, addr, i2c_bus):
        super().__init__(addr, i2c_bus)
        self._ADDRESSES['Device'] = addr


