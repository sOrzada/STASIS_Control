'''GUI for calculating different types of pulses.'''
import numpy as np
from time import sleep
from tkinter import *
from tkinter import scrolledtext
import re
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import STASIS_Control

class PulseToolObj:
    '''This class contains all data and methods for a simple pulse tool for the STASIS System.\n
    The pulse tool enables the user to specify time varying pulses.'''
    def __init__(self):
        '''Initialize Pulse Tool Object'''
        
        self.amplitudes = []
        self.phases = []
        self.states = []
        ### Here, the pulse names are defined for the list of pulses the user can choose from.
        self.pulse_names=('Sinc Pulse', 'Rect with frequency shift', 'Noise')
        
    def openGUI(self):
        '''Opens the GUI for the pulse tool.'''
        ### Initialize values for use in this Tool ###
        self.clock = 10e6/STASIS_Control.STASIS_System.TimingControl.clock_divider
        self.clock_divider = STASIS_Control.STASIS_System.TimingControl.clock_divider
        self.Tx_samples = STASIS_Control.STASIS_System.TimingControl.counter_Tx
        self.number_of_channels = STASIS_Control.STASIS_System.Modulator.number_of_channels
        self.info_text='Clock frequency: ' + str(self.clock/1e3) + ' kHz\n'\
                        + '(Clock Divider: ' + str(self.clock_divider) + ')\n'\
                        + 'Tx Samples: ' + str(self.Tx_samples)+ '\n'\
                        + 'Number of Channels: ' + str(self.number_of_channels)
        
        #Define Window for GUI and set make this the only active window.
        self.WindowMain=Toplevel()
        self.WindowMain.config(width=1200, height=700)
        self.WindowMain.protocol('WM_DELETE_WINDOW', lambda: self.on_closing())
        self.WindowMain.title('STASIS - Simple Pulse Tool')
        self.WindowMain.iconbitmap(os.path.dirname(__file__) + r'\images\S_square_32x32.ico')
        self.WindowMain.grab_set()
        
        #General Info Box
        self.text_box_info = scrolledtext.ScrolledText(self.WindowMain, width = 45, height =8)
        self.text_box_info.place(x=20,y=20)
        self.text_box_info.insert(1.0, self.info_text)
        self.text_box_info.config(state='disabled')
        
        #Text box for user interaction. This Textbox is parsed to extract user inputs.
        self.text_box_input = scrolledtext.ScrolledText(self.WindowMain, width = 45, height =30)
        self.text_box_input.place(x=20,y=180)
        
        #Listbox for choosing the type of pulse to be used.
        self.pulses = Variable(self.WindowMain, value=self.pulse_names)
        self.pulse_list_box = Listbox(self.WindowMain, listvariable=self.pulses, height=5, width=30, selectmode=EXTENDED)
        self.pulse_list_box.place(x=450, y = 30)
        self.pulse_list_box.config(exportselection=False)        
        self.pulse_list_box.bind('<<ListboxSelect>>',self.listboxSelect)
        self.pulse_list_box.selection_set(0) #Make a standard selection when opening window.
        self.listboxSelect(self.pulse_list_box.event_generate('<<ListboxSelect>>')) #Pretend the user has clicked the standard selection.

        #Button to calculate pulse from user selctions and inputs.
        self.Button_Calculate_Pulse = Button(self.WindowMain, text='Calculate -->', command = self.Button_Calculate_Pulse_Press)
        self.Button_Calculate_Pulse.place(x=540,y=320, anchor=CENTER, width=150, height=50)

        #Button for applying the calculated pulse to the STASIS System Object (will not yet be transmitted to hardware)
        self.Button_Apply_Close = Button(self.WindowMain, text = 'Apply & Close', command = self.Button_Apply_Close_Press)
        self.Button_Apply_Close.place(x=540, y = 620, anchor=CENTER, width = 150, height = 50)

        #A Frame for the good looks.
        self.frame_right = Frame(self.WindowMain, borderwidth=3, relief='raised')
        self.frame_right.place(x=690, y=5, width=505, height=680)

        #Two figures, one for time domain of pulse, one for frequency domain.
        self.figure_time_domain = Figure(figsize=(6,4), dpi=80)
        self.figure_multipurpose = Figure(figsize=(6,4), dpi=80)
        self.plot_figure_time_domain = self.figure_time_domain.add_subplot(111)
        self.plot_figure_multipurpose = self.figure_multipurpose.add_subplot(111)

    def on_closing(self):
        '''Function that is called when the Pulse Tool GUI is closed.'''
        self.WindowMain.grab_release()
        self.WindowMain.destroy()
    
    def mainloop(self):
        '''Mainloop for stand-alone purposes.'''
        self.WindowMain.mainloop()
    
    def listboxSelect(self,event):
        '''When an item from the Listbox is selected, this method is called.'''
        selected = self.pulse_list_box.curselection()
        selected_Pulse = selected[0]
        match selected_Pulse:
            case 0:
                self.sinc_pulse_setup()
            case 1:
                self.rect_freq_shift_setup()
            case 2:
                self.noise_pulse_setup()
        self.Button_Calculate_Pulse_Press() #Run once to show standard

    def sinc_pulse_setup(self):
        '''Setup for sinc pulse. Specifies standard values and sets up the text box.'''
        self.bandwidth = 1000
        self.freq_shift = 1000
        amp_state_temp = 0
        amplitude_temp = 10
        phase_increment = 360/self.number_of_channels
        self.text_input = 'Sinc Pulse with Hamming window. Parameters:\n'\
                        + 'Bandwidth (Hz): ' + str(self.bandwidth) + '\n'\
                        + 'Frequency Shift (Hz): ' + str(self.freq_shift) + '\n\n'\
                        + 'Ch\tmaxAmpl\tPh.(°)\tState\n'
        for a in range(self.number_of_channels):
            self.text_input = self.text_input + str(a+1) + '\t' + str(amplitude_temp) + '\t' + str(phase_increment*a)+ '\t' + str(amp_state_temp)+ '\n'
        self.text_box_input.delete('1.0',END)
        self.text_box_input.insert('1.0',self.text_input)
        
    def noise_pulse_setup(self):
        '''Setup for noise pulse. Specifies standard values and sets up the text box.'''
        self.max_amplitude=10
        self.min_amplitude=0
        self.number_of_noise_samples= self.Tx_samples
        amp_state_temp = 0
        self.text_input = 'Noise Pulse Parameters:\n' \
                        + 'Maximum Amplitude: ' + str(self.max_amplitude) + '\n'\
                        + 'Minimum Amplitude: ' + str(self.min_amplitude) + '\n'\
                        + 'Number of noise samples: ' + str(self.number_of_noise_samples) + '\n'\
                        + 'Amplifier State: ' + str(amp_state_temp)
        self.text_box_input.delete('1.0', END)
        self.text_box_input.insert('1.0',self.text_input)
   
    def rect_freq_shift_setup(self):
        '''Setup for rect pulse. Specifies standard values and sets up the text box.'''
        self.freq_shift = 1000 #in Hz
        amplitude_temp = 10
        amp_state_temp = 0
        phase_increment = 360/self.number_of_channels #in Degrees
        self.text_input = 'Rect with frequency shift, Parameters:\n'\
                        + 'Frequency Shift (Hz): ' + str(self.freq_shift) + '\n\n'\
                        + 'Ch\tAmpl.\tPh.(°)\tState\n'
        for a in range(self.number_of_channels):
            self.text_input = self.text_input + str(a+1) + '\t' + str(amplitude_temp) + '\t' + str(phase_increment*a)+ '\t' + str(amp_state_temp)+ '\n'
        self.text_box_input.delete('1.0',END)
        self.text_box_input.insert('1.0',self.text_input)

    def Button_Calculate_Pulse_Press(self):
        '''Call the calculations for the selected pulse.'''
        selected = self.pulse_list_box.curselection()
        try:
            match selected[0]:
                case 0:
                    self.sinc_pulse_calculation()
                case 1:
                    self.rect_freq_shift_calculation()
                case 2:
                    self.noise_pulse_calculation()
        except:
            pass


    def noise_pulse_calculation(self):
        '''Calculate the noise pulse with the paramters provided by the user. Parameters are parsed from the text in the editable text box.'''
        numbers = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", self.text_box_input.get('1.0',END))
        max_amplitude = float(numbers[0])
        min_amplitude = float(numbers[1])
        number_of_samples = int(numbers[2])
        amplifier_state = int(numbers[3])
        self.amplitudes = [0.0]*self.number_of_channels
        self.phases = [0.0]*self.number_of_channels
        self.states = [0]*self.number_of_channels
        for channel in range(self.number_of_channels):
            self.amplitudes[channel]=[]
            self.phases[channel]=[]
            self.states[channel]=[]
            for sample_no in range(number_of_samples):
                self.amplitudes[channel].append(random.uniform(min_amplitude,max_amplitude))
                self.phases[channel].append(random.uniform(0,360))
                self.states[channel].append(amplifier_state)
        self.plot_figures(self.amplitudes[0],self.phases[0])
        
        
    def plot_figures(self, amplitudes, phases):
        '''Plots the time and frequency domain representations of the pulse (channel 1) into the respective figures.'''
        number_of_samples = len(amplitudes)
        #Plot Amplitude of Channel 1
        self.plot_figure_time_domain.clear()
        self.plot_figure_time_domain.plot(amplitudes)
        self.plot_figure_time_domain.set_xlabel('Samples')
        self.plot_figure_time_domain.set_ylabel('Amplitude')
        self.plot_figure_time_domain.set_title('Profile Channel 1')
        canvas = FigureCanvasTkAgg(self.figure_time_domain, master=self.WindowMain)
        canvas.draw()
        canvas.get_tk_widget().place(x=700, y=15)

        #Plot Spectrum of Channel 1
        x=np.linspace(-self.clock/2000,self.clock/2000,num=number_of_samples)
        y=A_phi2complex(amplitudes,phases)
        
        fft_y = (np.fft.fftshift(np.real(np.abs(np.fft.fft(y)))))
        
        self.plot_figure_multipurpose.clear()
        self.plot_figure_multipurpose.plot(x,fft_y)
        self.plot_figure_multipurpose.set_xlabel('Frequency in kHz')
        self.plot_figure_multipurpose.set_ylabel('Amplitude')
        self.plot_figure_multipurpose.set_title('FFT Channel 1')
        canvas = FigureCanvasTkAgg(self.figure_multipurpose, master=self.WindowMain)
        canvas.draw()
        canvas.get_tk_widget().place(x=700, y=350)

    def sinc_pulse_calculation(self):
        '''Calculate the sinc pulse with the paramters provided by the user. Parameters are parsed from the text in the editable text box.'''
        numbers = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", self.text_box_input.get('1.0',END))
        bandwidth = float(numbers[0])
        freq_shift = float(numbers[1])
        maxAmplitude = []
        phase = []
        state = []
        for channel in range(self.number_of_channels):
            maxAmplitude.append(float(numbers[2+channel*4+1]))
            phase.append(float(numbers[2+channel*4+2]))
            state.append(int(float(numbers[2+channel*4+3])))
        
        x=np.linspace(-0.5,0.5,num=self.Tx_samples)
        bw_factor = bandwidth/self.clock*self.Tx_samples
        shift_factor = freq_shift/self.clock*self.Tx_samples
        self.amplitudes=[0.0]*self.number_of_channels
        self.phases = [0.0]*self.number_of_channels
        self.states = [0]*self.number_of_channels
        
        for channel in range(self.number_of_channels):
            self.amplitudes[channel]=[]
            self.phases[channel]=[]
            self.states[channel]=[]
            for sample in range(self.Tx_samples):
                #y_temp = np.sinc(x[sample]*bw_factor)*np.cos(x[sample]*np.pi)*np.exp(1j*(x[sample]*2*np.pi*shift_factor + phase[channel]/180*np.pi))*maxAmplitude[channel] #Cosine Window
                y_temp = np.sinc(x[sample]*bw_factor)*(0.54-0.46*np.cos((x[sample]+0.5)*np.pi*2))*np.exp(1j*(x[sample]*2*np.pi*shift_factor + phase[channel]/180*np.pi))*maxAmplitude[channel] #Hamming Window
                
                self.amplitudes[channel].append(np.abs(y_temp))
                self.phases[channel].append(np.angle(y_temp)/np.pi*180)
                self.states[channel].append(state[channel])
        self.plot_figures(self.amplitudes[0],self.phases[0])

    def rect_freq_shift_calculation(self):
        '''Calculate the rect pulse with the paramters provided by the user. Parameters are parsed from the text in the editable text box.'''
        numbers = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", self.text_box_input.get('1.0',END))
        freq_shift = float(numbers[0])
        self.amplitudes=[0]*self.number_of_channels
        self.phases=[0]*self.number_of_channels
        self.states=[0]*self.number_of_channels
        shift_factor = freq_shift/self.clock*self.Tx_samples
        maxAmpltiude_in = []
        phases_in=[]
        states_in=[]
        for a in range(self.number_of_channels):
            maxAmpltiude_in.append(float(numbers[1 + a*4 + 1]))
            phases_in.append(float(numbers[1 + a*4 + 2]))
            states_in.append(int(numbers[1 + a*4 + 3]))
        
        x=np.linspace(-0.5,0.5,num=self.Tx_samples)
        for a in range(self.number_of_channels):
            self.amplitudes[a]=[]
            self.phases[a]=[]
            self.states[a]=[]
            for b in range(self.Tx_samples):
                y_temp = maxAmpltiude_in[a]*np.exp(1j*(x[b]*2*np.pi*shift_factor + phases_in[a]/180*np.pi))
                self.amplitudes[a].append(np.abs(y_temp))
                self.phases[a].append(np.angle(y_temp)/np.pi*180)
                self.states[a].append(states_in[a])
        self.plot_figures(self.amplitudes[0],self.phases[0])
    
    def Button_Apply_Close_Press(self):
        '''Applies pulse to STASIS_System object and closes the Pulse Tool GUI.'''
        if len(self.amplitudes)>0:
            STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state(self.amplitudes,self.phases,self.states)
            self.WindowMain.destroy()
        

def A_phi2complex(amplitudes,phases):
    '''Calculates complex numbers from Amplitude and Phase'''
    amplitudes=np.array(amplitudes)
    phases = np.array(phases)
    x=amplitudes*np.exp(1j*np.pi*phases/180)
    return x
