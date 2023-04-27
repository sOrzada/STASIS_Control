# This script provides control over the STASIS hardware
import ft4222 #Library for SPI device
import math
import numpy as np
import configparser
from ft4222.SPI import Cpha, Cpol
from ft4222.SPIMaster import Mode, Clock, SlaveSelect
from ft4222.GPIO import Port, Dir
from time import sleep

##### Define Classes for different hardware modules #####
class ControlByteObj: #Contains the control bits. Select the state and add for complete control byte. I introduced this for better readability of code.
    chip0=0 #Important: Use only one chip at a time!
    chip1=1
    chip2=2
    chip3=3
    prog=4 #Set System to programming mode
    reset=8 #Reset Modulator Counters
    clock=16 #Trigger Modulator Counters
    we=32 #Write to Latch/SRAM
    #64 (7th bit) is reserved for future use
    enable=128 #Enable system. This enables the Unblank Signal for the Amplifiers. If this is not set, no signal can come from the amplifiers
    def __init__(self):
        pass
    def chip(self,c): #Another option to define chip. 0-3
        return int(c)

class SignalSourceObj: #Contains all data and methods for Signal Source Board
    #Attributes
    address = 0 #Standard address for Signal Source
    source = 0
    #Methods:
    def __init__(self):
        self.address = int(config['DEFAULT']['signal_source_address'])
        pass
    def set_internal(self): #Internal RF signal source (128MHz)
        self.source = 1
    def set_external(self): #External RF signal source fed via SMA
        self.source = 0
    def return_byte_stream(self): #Return a byte stream ready to be transmitted via SPI
        CB = ControlByteObj() #For improve readability use the object CB to gerenate the control bits.
        data = bytes([CB.prog, 0 , 0, 0,
                      CB.prog + CB.chip(0), self.address, 0, self.source,
                      CB.prog + CB.we + CB.chip(0), self.address, 0, self.source,
                      CB.prog + CB.chip(0), self.address, 0, self.source,
                      CB.prog, 0 , 0, 0])
        return data

class TimingControlObj: #Contains all data and methods for Timing Control
    #Attributes
    con_mode = 1 #Continous Mode or intermittant mode (Tx/Rx)
    mod_res_sel = 0 #Select whether to reset modulators via Tx/Rx (1) or their own counters (0)
    ubl_enable = 1 #Enable unblank
    clock_divider = 100 #Clock Divider for 10 MHz clock.
    counter_Rx = 9500 #Rx will last this many clock cycles
    counter_Tx = 500 #Tx will last this many clock cycles
    def __init__(self):
        self.address = int(config['DEFAULT']['timing_control_address']) #Physical Address for TimingControl
    def set_continous_mode(self):
        self.con_mode = 1
    def set_alternating_mode(self):
        self.con_mode = 0
    def switch_off(self):
        self.ubl_enable = 0
    def switch_on(self):
        self.ubl_enable = 1
    def return_byte_stream(self):
        CB = ControlByteObj() #For improve readability use the object CB to gerenate the control bits.
        byte_stream = [CB.prog, 0, 0, 0] #Initiate by setting system into write mode.
        for a in range(4): #Timing Control contains 4 registers.
            match a:
                case 0: #State Register
                    data1 = self.con_mode + 2* self.mod_res_sel + 4* self.ubl_enable #First three bits
                    data2 = 0 #Not used
                case 1: #Register for Clock Devider
                    data1=self.clock_divider%256
                    data2=math.floor(self.clock_divider/256)
                case 2: #Register for Rx Counter
                    data1=self.counter_Rx%256
                    data2=math.floor(self.counter_Rx/256)
                case 3: #Register for Tx Counter
                    data1=self.counter_Tx%256
                    data2=math.floor(self.counter_Tx/256)
            byte_stream_add = [CB.prog + CB.chip(a), self.address, data2, data1,
                               CB.prog + CB.we + CB.chip(a), self.address, data2, data1,
                               CB.prog + CB.chip(a), self.address, data2, data1]
            byte_stream = byte_stream + byte_stream_add
        byte_stream=byte_stream + [CB.prog, 0, 0, 0]
        data = bytes(byte_stream)
        return data
    def return_timings(self): #Calculate and return timings
        clock_f=10e6/self.clock_divider
        t_Rx=self.counter_Rx/clock_f
        t_Tx=self.counter_Tx/clock_f
        duty_cycle = t_Tx/(t_Rx+t_Tx)*100
        print('Clock Frequency: ' + str(clock_f/1000) + 'kHz')
        print('Transmit Time: ' + str(t_Tx*1000) + 'ms')
        print('*Receive* Time: ' + str(t_Rx*1000) + 'ms')
        print('Duty Cycle: ' + str(duty_cycle) + '%')

class ModulatorObj: #Contains all data and methods for Modulators
    def __init__(self):
        self.number_of_channels = int(config['DEFAULT']['number_of_channels']) #Number of modulators in system.
        self.start_address = int(config['DEFAULT']['start_channel']) #address of first modulator, others are counted upwards from here.
        self.counter_max = [10] * self.number_of_channels #Maximum of value of counter in modulator. On this number, it switches back to 0
        self.I_values = [0] * self.number_of_channels #In phase value for Modulator
        self.Amp_state = [0] * self.number_of_channels #Amplifier state (high(1) and low(0) voltage)
        self.Q_values = [0] * self.number_of_channels #Quadrature value for Modulator
        for a in range(self.number_of_channels):
            self.I_values[a] = [pow(2,14)-1]*self.counter_max[a]
            self.Q_values[a] = [pow(2,13)-1]*self.counter_max[a]
            self.Amp_state[a] = [0]*self.counter_max[a]

    def return_byte_stream(self):
        CB = ControlByteObj() #For improve readability use the object CB to gerenate the control bits.
        byte_stream = [CB.prog, 0 , 0, 0]*1000 #Make sure the switching to programming mode is finished.
        for a in range(self.number_of_channels):
            #Programm counter
            data1=self.counter_max[a]%256
            data2=math.floor(self.counter_max[a]/256)
            byte_stream_add = [CB.prog + CB.chip0, a + self.start_address, data2, data1,
                               CB.prog + CB.we + CB.chip0, a + self.start_address, data2, data1,
                               CB.prog + CB.chip0, a + self.start_address, data2, data1]
            byte_stream = byte_stream + byte_stream_add
            for c in range(1):
                byte_stream_add = [CB.prog, a + self.start_address, 0, 0,
                                   CB.prog + CB.reset, a + self.start_address, 0, 0, #Reset counters before starting to fill SRAM.
                                   CB.prog, a + self.start_address, 0, 0]
                byte_stream = byte_stream + byte_stream_add
                for b in range(self.counter_max[a]):
                    if c==0:
                        data1=self.I_values[a][b]%256
                        data2=math.floor(self.I_values[a][b]/256)+self.Amp_state[a][b]*64 #Switch 15th bit (7th in byte 2) akkording to amplifier state.
                        byte_stream_add = [CB.prog + CB.chip1, a + self.start_address, data2, data1,
                                           CB.prog + CB.chip1 + CB.we, a + self.start_address, data2, data1,
                                           CB.prog + CB.chip1 + CB.clock, a + self.start_address, data2, data1]
                        byte_stream = byte_stream + byte_stream_add
                    else:
                        data1=self.Q_values[a][b]%256
                        data2=math.floor(self.Q_values[a][b]/256) 
                        byte_stream_add = [CB.prog + CB.chip2, a + self.start_address, data2, data1,
                                           CB.prog + CB.chip2 + CB.we, a + self.start_address, data2, data1,
                                           CB.prog + CB.chip2 + CB.clock, a + self.start_address, data2, data1]
                        byte_stream = byte_stream + byte_stream_add
        byte_stream = byte_stream + [CB.prog, 0, 0, 0]
        data=bytes(byte_stream)    
        return data
    
###### Start Programm ######

### Load Configuration file ###
config=configparser.ConfigParser()
config.read('stasis_control-1\STASIS_config.ini')


print(str(ControlByteObj.chip0))
SignalSource = SignalSourceObj()
data_stream1 = SignalSource.return_byte_stream()
#print(data_stream)

TimingControl = TimingControlObj()
data_stream2 = TimingControl.return_byte_stream()
TimingControl.return_timings()
#print(data_stream)

Modulator = ModulatorObj()
data_out_mod=Modulator.return_byte_stream()


#quit()
# open 'device' with default description 'FT4222 A'
#devA = ft4222.openByDescription('FT4222 A')
# init spi master
#devA.spiMaster_Init(Mode.SINGLE, Clock.DIV_8, Cpha.CLK_LEADING, Cpol.IDLE_LOW, SlaveSelect.SS0)

enable_word=bytes([128,0,0,0])


#devA.spiMaster_SingleWrite(data_stream1+data_stream2+enable_word, True) #Write Data to SPI device.