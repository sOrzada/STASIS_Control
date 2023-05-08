# Classes for Hardware Modules of STASIS system are defined and initialized here.
import math
import numpy as np
import ft4222
from ft4222.SPI import Cpha, Cpol
from ft4222.SPIMaster import Mode, Clock, SlaveSelect
import os
import configparser

class STASIS_SystemObj:
    def __init__(self,config):
        try:
            if config['DEFAULT']['Signal_Source_module'] == 'true':
                self.SignalSource = SignalSourceObj(config)
        except:
           pass

        try:
            if config['DEFAULT']['Timing_Control_module'] =='true':
                self.TimingControl = TimingControlObj(config)
        except:
            pass

        try:
            if config['DEFAULT']['Modulator_Module'] == 'true':
                self.Modulator = ModulatorObj(config)
        except:
            pass

        try:
            if config['DEFAULT']['USB2SPI_Module'] == 'true':
                try:
                    self.SPI = USB2SPIObj(config)
                except:
                    print('<p>Error accessing FT4222! Make sure to connect to USB.</p>')
                    quit()
        except:
            pass
    def enable_system(self):
        self.SPI.send_bitstream(bytes([128,0,0,0]))
    def setup_system(self):
        bytestream = self.TimingControl.return_byte_stream() + self.SignalSource.return_byte_stream() + self.Modulator.return_byte_stream()+ bytes([0,0,0,0])
        self.SPI.send_bitstream(bytestream)    
    def disable_system(self):
        self.SPI.send_bitstream(bytes([0,0,0,0]))



class ControlByteObj: #Contains the control bits. Select the state and add for complete control byte. I introduced this for better readability of code.
    '''ControlByteObj'''
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
        '''chip(c) simply returns c.'''
        return int(c)

class USB2SPIObj: #Contains all data and methods for USB2SPI hardware. 
    def __init__(self,config):
        #Open device with default Name
        self.devA = ft4222.openByDescription('FT4222 A')
        #Configure Device for SPI (We allow different clock speeds according to config file)
        if config['SPI_config']['clock_divider'] == '8':
            self.devA.spiMaster_Init(Mode.SINGLE, Clock.DIV_8, Cpha.CLK_LEADING, Cpol.IDLE_LOW, SlaveSelect.SS0)
        elif config['SPI_config']['clock_divider'] == '4':
            self.devA.spiMaster_Init(Mode.SINGLE, Clock.DIV_4, Cpha.CLK_LEADING, Cpol.IDLE_LOW, SlaveSelect.SS0)
        else:
            self.devA.spiMaster_Init(Mode.SINGLE, Clock.DIV_16, Cpha.CLK_LEADING, Cpol.IDLE_LOW, SlaveSelect.SS0)
    
    def send_bitstream(self, bitstream): #Write bit stream. Input variable is actually a row of 4*N bytes.
        self.devA.spiMaster_SingleWrite(bitstream, True)


class SignalSourceObj: #Contains all data and methods for Signal Source Board
    #Attributes
    address = 0 #Standard address for Signal Source
    source = 0
    #Methods:
    def __init__(self,config):
        self.address = int(config['DEFAULT']['signal_source_address'])
        pass
    def set_internal(self): #Internal RF signal source (128MHz)
        self.source = 1
    def set_external(self): #External RF signal source fed via SMA
        self.source = 0
    def return_byte_stream(self): #Return a byte stream ready to be transmitted via SPI
        CB = ControlByteObj() #For improved readability I use the object CB to gerenate the control bits.
        data = bytes([CB.prog, 0 , 0, 0,
                      CB.prog + CB.chip(0), self.address, 0, self.source,
                      CB.prog + CB.we + CB.chip(0), self.address, 0, self.source,
                      CB.prog + CB.chip(0), self.address, 0, self.source,
                      CB.prog, 0 , 0, 0])
        return data

class TimingControlObj: #Contains all data and methods for Timing Control
    #Attributes
    con_mode = 0 #Continous Mode or intermittant mode (Tx/Rx)
    mod_res_sel = 0 #Select whether to reset modulators via Tx/Rx (1) or their own counters (0)
    ubl_enable = 1 #Enable unblank
    clock_divider = 100 #Clock Divider for 10 MHz clock.
    counter_Rx = 255 #Rx will last this many clock cycles
    counter_Tx = 255 #Tx will last this many clock cycles
    def __init__(self,config):
        self.address = int(config['DEFAULT']['timing_control_address']) #Physical Address for TimingControl
    def set_continous_mode(self):
        self.con_mode = 1
    def set_alternating_mode(self):
        self.con_mode = 0
    def switch_off(self):
        self.ubl_enable = 0
    def switch_on(self):
        self.ubl_enable = 0
    def return_byte_stream(self):
        CB = ControlByteObj() #For improved readability use the object CB to gerenate the control bits.
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
    def __init__(self,config):
        self.number_of_channels = int(config['DEFAULT']['number_of_channels']) #Number of modulators in system.
        self.start_address = int(config['DEFAULT']['start_channel']) #address of first modulator, others are counted upwards from here.
        self.counter_max = [1] * self.number_of_channels #Maximum of value of counter in modulator. On this number, it switches back to 0
        self.I_values = [0] * self.number_of_channels #In phase value for Modulator
        self.Amp_state = [0] * self.number_of_channels #Amplifier state (high(1) and low(0) voltage)
        self.Q_values = [0] * self.number_of_channels #Quadrature value for Modulator
        self.amplitudes = [200] *self.number_of_channels #Amplitudes of all channels
        self.phases = [0] * self.number_of_channels #Phases of all channels
        for a in range(self.number_of_channels):
            self.I_values[a] = [pow(2,14)-1]*self.counter_max[a]
            self.Q_values[a] = [pow(2,13)-1]*self.counter_max[a]
            self.Amp_state[a] = [0]*self.counter_max[a]

    def set_amplitudes_phases_state(self,amplitudes_in,phases_in,state_in):
        self.amplitudes=amplitudes_in
        self.phases=phases_in
        self.I_values=[0]*self.number_of_channels
        self.Q_values=[0]*self.number_of_channels
        for a in range(self.number_of_channels):
            self.counter_max[a]=len(amplitudes_in[a])
            self.I_values[a]=[0]*self.counter_max[a]
            self.Q_values[a]=[0]*self.counter_max[a]
            self.Amp_state[a]=[0]*self.counter_max[a]
            for b in range(len(amplitudes_in[a])):
                self.I_values[a][b] = int(pow(2,13)-1 + amplitudes_in[a][b] * np.cos(phases_in[a][b])) #This is preliminary Code! Change later to account for amplitudes/calibration
                self.Q_values[a][b] = int(pow(2,13)-1 + amplitudes_in[a][b] * np.sin(phases_in[a][b])) #This is preliminary Code! Change later to account for amplitude/calibration
                self.Amp_state[a][b] = state_in[a][b]


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

config=configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/STASIS_config.ini')

### Instance Hardware Objects ##

STASIS_System = STASIS_SystemObj(config)
print('Initialized System')