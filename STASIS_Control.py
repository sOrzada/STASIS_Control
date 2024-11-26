'''Classes for Hardware Modules of STASIS system are defined and initialized here.'''
import math
import numpy as np
import ft4222
from ft4222.SPI import Cpha, Cpol
from ft4222.SPIMaster import Mode, Clock, SlaveSelect
import os
import configparser
import csv

class STASIS_SystemObj:
    '''Here we combine all classes to have a single object for the STASIS System.'''
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


        if config['DEFAULT']['Modulator_Module'] == 'true':
            self.Modulator = ModulatorObj(config)

 
        try:
            if config['DEFAULT']['USB2SPI_Module'] == 'true':
                try:
                    self.SPI = USB2SPIObj(config)
                    print('FT4222 connected.')
                except:
                    print('<p>Error accessing FT4222! Make sure to connect to USB.</p>')
                    quit()
        except:
            pass
    def enable_system(self):
        self.SPI.send_bitstream(bytes([128,0,0,0]))
    def setup_system(self):
        self.TimingControl.trigger_off() #Trigger needs to be switched off before programming Modulators, because trigger is used to select adress.
        bytestream = self.TimingControl.return_byte_stream()
        self.TimingControl.trigger_on() #Trigger can be switched on again after programming Modulators.
        bytestream = bytestream + self.SignalSource.return_byte_stream() + self.Modulator.return_byte_stream() + self.TimingControl.return_byte_stream() + bytes([0,0,0,0])
        self.SPI.send_bitstream(bytestream)    
    def disable_system(self):
        self.SPI.send_bitstream(bytes([0,0,0,0]))

### Helper Classes ###
class PulseObj:
    '''This is a Pulse Object for saving/loading pulses to/from files.'''
    Amplitudes=[]
    Phases=[]
    States=[]

class ControlByteObj: #Contains the control bits. Select the state and add for complete control byte. I introduced this for better readability of code.
    '''This class contains some constants that make the code in this module more readable.'''
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

### Hardware Representation Classes ###
class USB2SPIObj: #Contains all data and methods for USB2SPI hardware.
    '''This class contains all methods to send bit streams through a FT4222 in SPI mode.'''
    def __init__(self,config):
        
        #Open device with default Name
        self.devA = ft4222.openByDescription('FT4222 A')
        
        #Configure Device for SPI (We allow different clock speeds according to config file)
        if config['SPI_config']['clock_divider'] == '8':
            print('SPI Clock devider: 8')
            self.devA.spiMaster_Init(Mode.SINGLE, Clock.DIV_8, Cpha.CLK_LEADING, Cpol.IDLE_LOW, SlaveSelect.SS0)
        elif config['SPI_config']['clock_divider'] == '4':
            self.devA.spiMaster_Init(Mode.SINGLE, Clock.DIV_4, Cpha.CLK_LEADING, Cpol.IDLE_LOW, SlaveSelect.SS0)
        else:
            self.devA.spiMaster_Init(Mode.SINGLE, Clock.DIV_16, Cpha.CLK_LEADING, Cpol.IDLE_LOW, SlaveSelect.SS0)
    
    def send_bitstream(self, bitstream): #Write bit stream. Input variable is actually a row of 4*N bytes.
        '''This method sends a bitstream via the SPI interface.\n
        The input variable "bitstream" is a list of 4*N bytes.\n
        The order is: \n
            Control byte\n
            Address byte\n
            Data byte 2 (with most significant of 16 bits)\n
            Data byte 1 (with least significant of 16 bits)\n'''
        #In the following, the data in bitstream is sliced. This is necessary, as to long streams are cut by the FT4222's driver without notice.
        max_num_bytes=400
        stream_length=len(bitstream)
        number_of_steps=int(np.ceil(stream_length/max_num_bytes))
        for a in range(number_of_steps):
            if (a+1)*max_num_bytes<stream_length:
                bitstream_send=bitstream[a*max_num_bytes:(a+1)*max_num_bytes]
            else:
                bitstream_send=bitstream[a*max_num_bytes:stream_length]
            self.devA.spiMaster_SingleWrite(bitstream_send, True)

class SignalSourceObj: #Contains all data and methods for Signal Source Board
    '''Contains all data and methods for Signal Source Board'''
    #Attributes
    address = 0 #Standard address for Signal Source
    source = 1
    
    #Methods:
    def __init__(self,config):
        self.address = int(config['DEFAULT']['signal_source_address'])
        pass
    def set_internal(self): #Internal RF signal source (128MHz)
        '''Set the signal source to internal RF Signal.'''
        self.source = 1
    def set_external(self): #External RF signal source fed via SMA
        '''Set the signal source to external RF Signal.'''
        self.source = 0
    def return_byte_stream(self): #Return a byte stream ready to be transmitted via SPI
        '''Returns a list of bytes which can be transferred via SPI, according to the current state of this Object.'''
        CB = ControlByteObj() #For improved readability I use the object CB to gerenate the control bits.
        data = bytes([CB.prog, 0 , 0, 0,
                      CB.prog + CB.chip(0), self.address, 0, self.source,
                      CB.prog + CB.we + CB.chip(0), self.address, 0, self.source,
                      CB.prog + CB.chip(0), self.address, 0, self.source,
                      CB.prog, 0 , 0, 0])
        return data

class TimingControlObj: #Contains all data and methods for Timing Control
    '''Contains all data and methods for Timing Control Board'''
    
    ### Attributes ###
    con_mode = 0 #Continous Mode or intermittant mode (Tx/Rx)
    mod_res_sel = 0 #Select whether to reset modulators via Tx/Rx (1) or their own counters (0)
    ubl_enable = 1 #Enable unblank
    trig = 0 #Trigger from clock disabled/enabled
    clock_divider = 100 #Clock Divider for 10 MHz clock.
    counter_Rx = 255 #Rx will last this many clock cycles
    counter_Tx = 255 #Tx will last this many clock cycles
    
    ### Methods ###
    def __init__(self,config):
        self.address = int(config['DEFAULT']['timing_control_address']) #Physical Address for TimingControl
    
    def set_continous_mode(self):
        '''Set the variable for Continous Transmit Mode to enable.'''
        self.con_mode = 1
   
    def set_alternating_mode(self):
        '''Set the variable for Continous Transmit Mode to disable. System will be alternating between Tx and "Rx"'''
        self.con_mode = 0
    
    def switch_off(self):
        self.ubl_enable = 0
    
    def switch_on(self):
        self.ubl_enable = 1
    
    def trigger_on(self):
        self.trig = 1

    def trigger_off(self):
        self.trig = 0
    
    def return_byte_stream(self):
        '''Returns list of bytes to be transmitted via SPI interface. 
        The list of bytes provides the correct sequence to program the hardware to the settings in this object.'''
        CB = ControlByteObj() #For improved readability use the object CB to gerenate the control bits.
        byte_stream = [CB.prog, 0, 0, 0] #Initiate by setting system into write mode.
        for a in range(4): #Timing Control contains 4 registers.
            match a:
                case 0: #State Register
                    data1 = self.con_mode + 2* self.mod_res_sel + 4* self.ubl_enable + 8*self.trig #First four bits
                    data2 = 0 #Not used
                case 1: #Register for Clock Devider
                    data1=self.clock_divider%256
                    data2=math.floor(self.clock_divider/256)
                case 2: #Register for Tx Counter
                    data1=self.counter_Tx%256
                    data2=math.floor(self.counter_Tx/256)
                case 3: #Register for Rx Counter
                    data1=self.counter_Rx%256
                    data2=math.floor(self.counter_Rx/256)
            byte_stream_add = [CB.prog + CB.chip(a), self.address, data2, data1,
                               CB.prog + CB.we + CB.chip(a), self.address, data2, data1,
                               CB.prog + CB.chip(a), self.address, data2, data1]
            byte_stream = byte_stream + byte_stream_add
        byte_stream=byte_stream + [CB.prog, 0, 0, 0]
        data = bytes(byte_stream)
        return data
    
    def return_timings(self): #Calculate and return timings
        '''Calculates and prints timings Terminal'''
        clock_f=10e6/self.clock_divider
        t_Rx=self.counter_Rx/clock_f
        t_Tx=self.counter_Tx/clock_f
        duty_cycle = t_Tx/(t_Rx+t_Tx)*100
        print('Clock Frequency: ' + str(clock_f/1000) + 'kHz')
        print('Transmit Time: ' + str(t_Tx*1000) + 'ms')
        print('*Receive* Time: ' + str(t_Rx*1000) + 'ms')
        print('Duty Cycle: ' + str(duty_cycle) + '%')

class ModulatorObj: #Contains all data and methods for Modulators
    '''Contains all data and methods for Modulator board. This also includes calibration data.'''
    
    def __init__(self,config):
        '''Initialize Modulator Object with standard values and values from config file.'''
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
        
        #Initialize Variables for I/Q offset
        self.IQoffset = [0]*self.number_of_channels
        for a in range(self.number_of_channels):
            self.IQoffset[a]=[0]*2
        self.f_name_CalZP=os.path.dirname(__file__) + '/' + config['Calibration']['Calibration_File_Zero_Point'] #Get file name for Zero Calibration from Config file.
        try:
            self.read_IQ_offset() #Read the Offset values from thr IQ-Offset file.
        except:
            print('Could not open IQ offset calibration file. Using no offset.')
    
    
    def read_IQ_offset(self):
        '''Reads the IQ offset from calibration file which is specified in the config file.'''
        with open(self.f_name_CalZP,'r') as f:
            reader = csv.reader(f, delimiter=',')
            a=0
            for row in reader:  #Read total file row by row. First value is I offset, second value is Q offset.
                self.IQoffset[a][0]=int(row[0])
                self.IQoffset[a][1]=int(row[1])
                a=a+1

    def write_IQ_offset(self):
        '''Saves the current IQ offset to the calibration file which is specified in the config file.'''
        with open(self.f_name_CalZP, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(self.IQoffset)
        
    def set_amplitudes_phases_state(self,amplitudes_in,phases_in,state_in):
        '''Sets the digital I and Q values to achieve the amplitudes and phases specified in the input variables.\n
        This includes normalizing according to the calibration.'''
        self.amplitudes=amplitudes_in
        self.phases=phases_in
        self.I_values=[0]*self.number_of_channels
        self.Q_values=[0]*self.number_of_channels
        for a in range(self.number_of_channels):
            if type(amplitudes_in[a]) is list: #Need to differentiate between cases with 1 and more elements.
                self.counter_max[a]=len(amplitudes_in[a])
                self.I_values[a]=[0]*self.counter_max[a]
                self.Q_values[a]=[0]*self.counter_max[a]
                self.Amp_state[a]=[0]*self.counter_max[a]
                for b in range(self.counter_max[a]):
                    cIQ=self.calcIQ(self.amplitudes[a][b],self.phases[a][b],a)
                    self.I_values[a][b]=int(np.real(cIQ))
                    self.Q_values[a][b]=int(np.imag(cIQ))
                    self.Amp_state[a][b]=state_in[a][b]
            else:
                self.counter_max[a]=1
                cIQ=self.calcIQ(self.amplitudes[a],self.phases[a],a)
                self.I_values[a]=int(np.real(cIQ))
                self.Q_values[a]=int(np.imag(cIQ))
                self.Amp_state[a]=state_in[a]

    def calcIQ(self,amp,ph,channel): #Calculate digital values including calibration
        '''This function translates a value for amplitude and phase into a complex I/Q value including normalization according to the calibration.\n
        "amp" is a single amplitude.\n
        "phase is a single phase.\n
        "channel" specifies for which channel this sample is. This is necessary to use the correct calibration values.'''
        IQ=(pow(2,13)-1 +self.IQoffset[channel][0])+ 1j*(pow(2,13)-1 +self.IQoffset[channel][1]) + amp*np.exp(1j*np.pi/180*ph) #Only includes offset correction. ToDo: include non-linearity! ToDo: include state!!
        return IQ
        
        

    def return_byte_stream(self):
        '''Returns a byte stream to be transmitted via SPI. This byte stream is suited to programm the modulators (hardware) to the state given in this object'''
        CB = ControlByteObj() #For improved readability use the object CB to gerenate the control bits.
        byte_stream = [CB.prog, 0 , 0, 0]*1000 #Make sure the switching to programming mode is finished.
        for a in range(self.number_of_channels): #Run through all channels
            data1=self.counter_max[a]%256
            data2=math.floor(self.counter_max[a]/256)
            byte_stream_add = [CB.prog + CB.chip0, a + self.start_address, data2, data1,
                               CB.prog + CB.we + CB.chip0, a + self.start_address, data2, data1,
                               CB.prog + CB.chip0, a + self.start_address, data2, data1]
            byte_stream = byte_stream + byte_stream_add
            for c in range(2): #Run through all SRAMs
                byte_stream_add = [CB.prog, a + self.start_address, 0, 0,
                                   CB.prog + CB.reset, a + self.start_address, 0, 0, #Reset counters before starting to fill SRAM.
                                   CB.prog, a + self.start_address, 0, 0]
                byte_stream = byte_stream + byte_stream_add
                for b in range(self.counter_max[a]): #Run through all samples
                    if c==0: #First SRAM Chip
                        if self.counter_max[a]>1:
                            data1=self.I_values[a][b]%256
                            data2=math.floor(self.I_values[a][b]/256)+self.Amp_state[a][b]*64 #Switch 15th bit (7th in byte 2) according to amplifier state.
                        else:
                            data1=self.I_values[a]%256
                            data2=math.floor(self.I_values[a]/256)+self.Amp_state[a]*64 #Switch 15th bit (7th in byte 2) according to amplifier state.
                    elif c==1: #Second SRAM Chip
                        if self.counter_max[a]>1:
                            data1=self.Q_values[a][b]%256
                            data2=math.floor(self.Q_values[a][b]/256)
                        else:
                            data1=self.Q_values[a]%256
                            data2=math.floor(self.Q_values[a]/256)

                    byte_stream_add = [CB.prog + CB.chip(c+1), a + self.start_address, data2, data1,
                                       CB.prog + CB.chip(c+1) + CB.we, a + self.start_address, data2, data1,
                                       CB.prog + CB.chip(c+1), a + self.start_address, data2, data1,
                                       CB.prog + CB.chip(c+1) + CB.clock, a + self.start_address, data2, data1]
                    byte_stream = byte_stream + byte_stream_add

        byte_stream = byte_stream + [CB.prog + CB.reset, 0, 0, 0] + [CB.prog, 0, 0, 0]
        data=bytes(byte_stream)    
        return data


### Load config file ###
config=configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/STASIS_config.ini')

### Instance Hardware Objects ###
STASIS_System = STASIS_SystemObj(config)
print('Initialized System')