'''GUIs for calibration of STASIS System.'''
from tkinter import *

import scipy.interpolate
import STASIS_Control
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import math
import scipy
from PIL import Image, ImageTk
from time import sleep

U_0dBm = math.sqrt(0.05) #RMS voltage at 0 dBm on 50 Ohms.

class CalibrateZeroObj:
    '''This class is used to calibrate the modulators LO-feedthrough/zero offset.\n
    It contains a GUI which can be started by using the "openGUI()" method.'''
    def __init__(self) -> None:
        self.number_of_channels = STASIS_Control.STASIS_System.Modulator.number_of_channels
        self.active_channel = 1
        self.IQoffset = STASIS_Control.STASIS_System.Modulator.IQoffset

        #Initiate Amplitudes, Phases and States(for the purpose of this Calibration step, the letter is unimportant, but needs to be set anyway)
        self.amplitudes = list([0])*self.number_of_channels
        self.phases = [0]*self.number_of_channels
        self.states = [0]*self.number_of_channels
    
    def openGUI(self):
        '''Prepares and Opens the GUI or this Class Object.'''
        self.WindowMain = Toplevel()
        self.WindowMain.iconbitmap(os.path.dirname(__file__) + '\images\S_square_32x32.ico')
        self.WindowMain.title('Zero Point Calibration of Modulators')
        self.WindowMain.config(width=1200, height=550)
        self.WindowMain.protocol('WM_DELETE_WINDOW', lambda: self.saveClose())
        
        #Initialize Controls
        self.controlButtonsInit(x_center=150, y_center=250) #Initialize control buttons
        self.channelSelectInit(x_center=150,y_center=100) #Initialize Listbox for channel selection
        self.ButtonSaveClose = Button(self.WindowMain, width=10, height=2, text='Save & Close', command=self.saveClose)
        self.ButtonSaveClose.place(x=150, y=400, anchor='center')

        #Load explanatory image and show in GUI
        self.image_path=os.path.dirname(__file__) + '\Images\Zero_Point_Cal.jpg'
        self.ph=Image.open(self.image_path)
        self.ph_resize=self.ph.resize((450,300), resample=1)
        self.ph_image=ImageTk.PhotoImage(self.ph_resize)
        self.label_image = Label(self.WindowMain, image=self.ph_image)
        self.label_image.config(image=self.ph_image)
        self.label_image.place(x=950,y=250, anchor='center')

        #Initialize Figure for Offset indication
        self.figureOffset = Figure(figsize=(5,5), dpi=80)
        self.plotFigureOffset = self.figureOffset.add_subplot(111)
        self.canvasFigureOffset = FigureCanvasTkAgg(self.figureOffset, master=self.WindowMain)
        self.canvasFigureOffset.get_tk_widget().place(x=500, y=250, anchor='center')
        
        #Update to show user the current offset
        self.update()

    def mainloop(self):
        '''Calls the mainloop() method for the GUI window.'''
        self.WindowMain.mainloop()

    def changeIQ(self,I_change,Q_change):
        '''Changes the IQ offset for the active channel by the numbers specified in I_change and Q_change'''
        self.IQoffset[self.active_channel-1][0] = self.IQoffset[self.active_channel-1][0] + I_change
        self.IQoffset[self.active_channel-1][1] = self.IQoffset[self.active_channel-1][1] + Q_change
        
        self.update()

    def saveClose(self):
        '''Function for closing the calibration Window. Also calls the "write_IQ_offset" method of the Modulator-Object.'''
        
        STASIS_Control.STASIS_System.Modulator.IQoffset = self.IQoffset
        STASIS_Control.STASIS_System.Modulator.write_IQ_offset()
        self.WindowMain.destroy()
        pass

    def controlButtonsInit(self,x_center,y_center): #Initialize Control Panel for I/Q correction
        '''Initializes the control Buttons and places them as a group at the location specified in x_center and y_center'''
        
        #This frame is only for looks:
        self.frame_buttons = Frame(self.WindowMain, width=180, height=180, borderwidth=3, relief='ridge')
        
        #Buttons for up/down
        self.frame_buttons.place(x=x_center,y=y_center, anchor='center')
        self.Button_up1 = Button(self.WindowMain, width=3, height=1, text='+1', command=lambda: self.changeIQ(1,0))
        self.Button_up10 = Button(self.WindowMain, width=3, height=1, text='+10', command=lambda: self.changeIQ(10,0))
        self.Button_down1 = Button(self.WindowMain, width=3, height=1, text='-1', command=lambda: self.changeIQ(-1,0))
        self.Button_down10 = Button(self.WindowMain, width=3, height=1, text='-10', command=lambda: self.changeIQ(-10,0))
        self.Button_up1.place(x=x_center, y=y_center-30, anchor='center')
        self.Button_up10.place(x=x_center, y=y_center-60, anchor='center')
        self.Button_down1.place(x=x_center, y=y_center+30, anchor='center')
        self.Button_down10.place(x=x_center, y=y_center+60, anchor='center')

        #Buttons for left/right
        self.Button_right1 = Button(self.WindowMain, width=3, height=1, text='+1', command=lambda: self.changeIQ(0,1))
        self.Button_right10 = Button(self.WindowMain, width=3, height=1, text='+10', command=lambda: self.changeIQ(0,10))
        self.Button_left1 = Button(self.WindowMain, width=3, height=1, text='-1', command=lambda: self.changeIQ(0,-1))
        self.Button_left10 = Button(self.WindowMain, width=3, height=1, text='-10', command=lambda: self.changeIQ(0,-10))
        self.Button_right1.place(x=x_center+30, y=y_center, anchor='center')
        self.Button_right10.place(x=x_center+65, y=y_center, anchor='center')
        self.Button_left1.place(x=x_center-30, y=y_center, anchor='center')
        self.Button_left10.place(x=x_center-65, y=y_center, anchor='center')
    
    def channelSelectInit(self, x_center, y_center): #Initialize Buttons and Label for Channel selection
        '''Initializes the channel selection interface at the coordinates specified by x_center and y_center.'''
        Button_prev = Button(self.WindowMain, width=3,height=1, text='<', command=lambda: self.channelselect(-1))
        Button_next = Button(self.WindowMain, width=3,height=1, text='>', command=lambda: self.channelselect(+1))
        self.label_channel = Label(self.WindowMain, height=1, width=6, text='Ch ' + str(self.active_channel), relief='sunken', bg='white')
        Button_prev.place(x=x_center-50,y=y_center,anchor='center')
        self.label_channel.place(x=x_center,y=y_center, anchor='center')
        Button_next.place(x=x_center+50,y=y_center, anchor='center')
    
    def channelselect(self,a): #Select channel with buttons and stay within actual channel count
        '''Selects a channel and makes sure you stay within actual channel count.'''
        self.active_channel = self.active_channel + a
        if self.active_channel<1:
            self.active_channel=1
        elif self.active_channel>self.number_of_channels:
            self.active_channel=self.number_of_channels
        self.label_channel.config(text='Ch ' + str(self.active_channel))
        self.update()

    def plotFigure(self):
        '''Plots the figure for modulator offset from center.'''
        a=self.active_channel
        self.plotFigureOffset.clear()
        self.plotFigureOffset.scatter(0,0, marker='o')
        self.plotFigureOffset.scatter(self.IQoffset[a-1][1],self.IQoffset[a-1][0], marker='x')
        self.plotFigureOffset.axis([-128,128,-128,128])
        self.plotFigureOffset.set_xlabel('I offset')
        self.plotFigureOffset.set_ylabel('Q offset')
        self.plotFigureOffset.set_title('Channel ' + str(self.active_channel))
        self.figureOffset.tight_layout()
        self.canvasFigureOffset.draw()

    def update(self):
        '''Calls functions for updating the figure and setting the Modulators. (self.plotFigure() and self.set_Modulators)'''
        self.plotFigure()
        self.set_Modulators()
    
    def set_Modulators(self):
        '''Sets the modulators by transmitting through SPI-Interface. Uses the SPI-object from the STASIS System.'''
        CB=STASIS_Control.ControlByteObj 
        STASIS_Control.STASIS_System.Modulator.IQoffset = self.IQoffset
        STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state(self.amplitudes,self.phases,self.states)
        bitstream=STASIS_Control.STASIS_System.Modulator.return_byte_stream()
        start_adress = STASIS_Control.STASIS_System.Modulator.start_address
        bitstream_adress = bytes([0 , start_adress-1+self.active_channel,0,0]) #sending this word as final word lets the active channels LED light up and sets the system to "on" without transmitting
        bitstream_enable_mod = bytes([CB.clock,0,0,0])
        bitstream = bitstream +bitstream_enable_mod+ bitstream_adress
        try:
            STASIS_Control.STASIS_System.SPI.send_bitstream(bitstream)
            sleep(0.05)
            STASIS_Control.STASIS_System.SPI.send_bitstream(bitstream_enable_mod+bitstream_enable_mod+bitstream_adress)
            sleep(0.05)
        except:
            print('Error! Could not transmit via SPI.')
            sleep(0.05)

class CalibrateLinearity1DObj:
    '''This class is used for calibrating for non-linearities of the Modulator/Amplifier system.'''
    def __init__(self) -> None:
        self.number_of_channels = STASIS_Control.STASIS_System.Modulator.number_of_channels
        self.active_channel = 1
        self.IQoffset = STASIS_Control.STASIS_System.Modulator.IQoffset #Load IQoffset from Modulators.
        self.Cal1D = STASIS_Control.STASIS_System.Modulator.Cal1D       #Load 1D Calibration from Modulators.
        self.dig_index = 0  #Always start with the first digital value (which is 0, so no danger to components or people)
        self.max_dig_value = STASIS_Control.STASIS_System.Modulator.number_of_1D_samples #Maximum number of 1D samples.

    def openGUI(self):
        '''Prepares and Opens the GUI or this Class Object.'''
        #Preparations for safety:
        self.active_channel = 1 #Always start with first channel when user activates GUI.
        self.dig_index = 0  #Always start with the first digital value (which is 0, so no danger to components or people)
        
        #Open Main Window
        self.WindowMain = Toplevel()
        self.WindowMain.iconbitmap(os.path.dirname(__file__) + '\images\S_square_32x32.ico')
        self.WindowMain.title('Linearity Calibration of Amplifiers')
        self.WindowMain.config(width=1300, height=550)
        self.WindowMain.protocol('WM_DELETE_WINDOW', lambda: self.saveClose())

        #Load explanatory image and show in GUI
        self.image_path=os.path.dirname(__file__) + '\Images\Cal_Lin1D.jpg'
        self.ph=Image.open(self.image_path)
        self.ph_resize=self.ph.resize((550,375), resample=1)
        self.ph_image=ImageTk.PhotoImage(self.ph_resize)
        self.label_image = Label(self.WindowMain, image=self.ph_image)
        self.label_image.config(image=self.ph_image)
        self.label_image.place(x=1000,y=250, anchor='center')

        #Save & Close Button
        self.ButtonSaveClose = Button(self.WindowMain, width=10, height=2, text='Save & Close', command=self.saveClose)
        self.ButtonSaveClose.place(x=150, y=400, anchor='center')
        
        #Channel Select
        self.channelSelectInit(x_center=150,y_center=100) #Initialize Listbox for channel selection
        
        #Radio Buttons for Amplifier Mode
        self.init_radiobuttons(x_start=80,y_start=130)

        #Digital Value Selector
        self.init_dig_value_select(x_center=150,y_center=210)

        #Initialize Entry Boxes
        self.init_entry_boxes(x_center=130, y_center=250)

        #Initialize Figure for linearity results
        self.Figurelin = Figure(figsize=(5,5), dpi=80)
        self.plotFigurelin = self.Figurelin.add_subplot(111) #Axes for Amplitude
        self.plotFigureAngle= self.plotFigurelin.twinx() #Axes for Phase
        self.canvasFigurelin = FigureCanvasTkAgg(self.Figurelin, master=self.WindowMain)
        self.canvasFigurelin.get_tk_widget().place(x=500, y=250, anchor='center')

        #Set Timings for Calibration: 1% Duty Cycle, 1ms pulses. This should be long enough for triggered measurements.
        STASIS_Control.STASIS_System.disable_system()
        STASIS_Control.STASIS_System.TimingControl.clock_divider=1000
        STASIS_Control.STASIS_System.TimingControl.counter_Tx=10
        STASIS_Control.STASIS_System.TimingControl.counter_Rx=990
        STASIS_Control.STASIS_System.TimingControl.set_alternating_mode()
        data=STASIS_Control.STASIS_System.TimingControl.return_byte_stream()
        try:
            STASIS_Control.STASIS_System.SPI.send_bitstream(data)
        except:
            print('Error: Could not transmit via SPI')
        #Set RF source to external
        STASIS_Control.STASIS_System.SignalSource.set_external()
        data=STASIS_Control.STASIS_System.SignalSource.return_byte_stream()
        try:
            STASIS_Control.STASIS_System.SPI.send_bitstream(data)
        except:
            print('Error: Could not transmit via SPI')
        #Set modulators to zero point transmission in low power mode
        STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state([0]*self.number_of_channels,[0]*self.number_of_channels,[0]*self.number_of_channels)
        self.set_Modulators()
        try:
            STASIS_Control.STASIS_System.enable_system() #Here the system is in a safe state and can be started.
        except:
            print('Error: Could not transmit via SPI!')

        #Update
        self.update()
    
    def init_radiobuttons(self, x_start, y_start):
        '''Initializes the radio buttons for selecting amplifier state.'''
        self.Amp_Mode=IntVar()
        R1= Radiobutton(self.WindowMain, text='Low Power Mode', variable=self.Amp_Mode, value=0, command=self.sel)
        R1.place(x=x_start,y=y_start,anchor=W)
        R2= Radiobutton(self.WindowMain, text='High Power Mode', variable=self.Amp_Mode, value=1, command=self.sel)
        R2.place(x=x_start,y=y_start+20,anchor=W)
    
    def init_dig_value_select(self, x_center, y_center): #Initialize Buttons and Label for Channel selection
        '''Initializes the channel selection interface at the coordinates specified by x_center and y_center.'''
        Caption1 = Label(self.WindowMain, height=1, width=20, text='Digital Value Selector')
        Caption1.place(x=x_center,y=y_center-30, anchor=CENTER)
        Button_prev = Button(self.WindowMain, width=3,height=1, text='<', command=lambda: self.dig_value_select(-1))
        Button_next = Button(self.WindowMain, width=3,height=1, text='>', command=lambda: self.dig_value_select(+1))
        self.label_dig_value = Label(self.WindowMain, height=1, width=6, text=str(0), relief='sunken', bg='white')
        Button_prev.place(x=x_center-50,y=y_center,anchor='center')
        self.label_dig_value.place(x=x_center,y=y_center, anchor='center')
        Button_next.place(x=x_center+50,y=y_center, anchor='center')

    def init_entry_boxes(self,x_center,y_center):
        '''Initializes the entry boxes for amplitude and phase inputs'''
        self.dB_value = StringVar()
        self.deg_value = StringVar()
        
        self.entry_db = Entry(self.WindowMain, width=12, textvariable=self.dB_value)
        self.entry_db.place(x=x_center,y=y_center-10, anchor=W)
        label_dB = Label(self.WindowMain, height=1, width=6, text='dB')
        label_dB.place(x=x_center-60,y=y_center-10, anchor=W)
        self.entry_degree = Entry(self.WindowMain, width=12, textvariable=self.deg_value)
        self.entry_degree.place(x=x_center,y=y_center+10, anchor=W)
        label_deg = Label(self.WindowMain, height=1, width=6, text='°')
        label_deg.place(x=x_center-60,y=y_center+10,anchor=W)
        Button_entry= Button(self.WindowMain, width=5,height=2, text='Apply', command=lambda: self.apply_entry())
        Button_entry.place(x=x_center+110, y=y_center, anchor=CENTER)

    def channelSelectInit(self, x_center, y_center): #Initialize Buttons and Label for Channel selection
        '''Initializes the channel selection interface at the coordinates specified by x_center and y_center.'''
        Button_prev = Button(self.WindowMain, width=3,height=1, text='<', command=lambda: self.channelselect(-1))
        Button_next = Button(self.WindowMain, width=3,height=1, text='>', command=lambda: self.channelselect(+1))
        self.label_channel = Label(self.WindowMain, height=1, width=6, text='Ch ' + str(self.active_channel), relief='sunken', bg='white')
        Button_prev.place(x=x_center-50,y=y_center,anchor='center')
        self.label_channel.place(x=x_center,y=y_center, anchor='center')
        Button_next.place(x=x_center+50,y=y_center, anchor='center')

    def apply_entry(self):
        '''Applies the entry from the entry boxes and writes them into the Cal1D variable.'''
        if self.dig_index>0: #Only allow changes for digital values other than 0
            voltage=pow(10,float(self.dB_value.get())/20)*U_0dBm
            angle=float(self.deg_value.get())
            self.Cal1D[self.active_channel-1,self.Amp_Mode.get(),self.dig_index,1]=voltage
            self.Cal1D[self.active_channel-1,self.Amp_Mode.get(),self.dig_index,2]=angle
            self.Cal1D[self.active_channel-1,self.Amp_Mode.get(),0,2]=self.Cal1D[self.active_channel-1,self.Amp_Mode.get(),1,2] #We need to make sure that there is no change in angle between 0V and the smallest measured voltage.
        self.update()


    def dig_value_select(self,a):
        '''Selects a digital value from a pre-defined set. These are the digital values added on top of the zero point calibration.'''
        self.dig_index=self.dig_index+a
        if self.dig_index<0:
            self.dig_index=0
        if self.dig_index>self.max_dig_value-1:
            self.dig_index=self.max_dig_value-1
        
        self.label_dig_value.config(text=str(int(self.Cal1D[self.active_channel-1,self.Amp_Mode.get(),self.dig_index,0])))
        self.update()

    def sel(self):
        
        self.update()

    def channelselect(self,a): #Select channel with buttons and stay within actual channel count
        '''Selects a channel and makes sure you stay within actual channel count.'''
        self.dig_value_select(-10000) #Reset to 0 output for safety. User might forget to plug cable!
        self.active_channel = self.active_channel + a
        if self.active_channel<1:
            self.active_channel=1
        elif self.active_channel>self.number_of_channels:
            self.active_channel=self.number_of_channels
        self.label_channel.config(text='Ch ' + str(self.active_channel))
        self.update()

    def plotFigure(self):
        '''Plots the figure for System linearity'''

        color_highlight='0'  #Color for highlighting current point of measurement
        color_amp = 'tab:blue' #Color for amplitude plot
        color_angle = 'tab:red' #Color for phase plot

        ch=self.active_channel-1
        mode=self.Amp_Mode.get()
        dig_index=self.dig_index
        self.plotFigurelin.clear()
        self.plotFigureAngle.clear()

        #For convenience of reader, change y axis of plot:
        if mode==0:
            U_max=100
        else:
            U_max=270
        
        if mode==0:
            x_ax_max=900
        else:
            x_ax_max=4500

        x=range(0,x_ax_max,20) #Range for possible digital values (<2^13-1)

        #Plot interpolated values of Amplitude
        xi=self.Cal1D[ch,mode,:,0]
        yi=self.Cal1D[ch,mode,:,1]
        y=scipy.interpolate.pchip_interpolate(xi,yi,x)
        self.plotFigurelin.plot(x,y,color=color_amp)
        #Plot interpolated values of Phase
        xi=self.Cal1D[ch,mode,:,0]
        yi=self.Cal1D[ch,mode,:,2]
        y=scipy.interpolate.pchip_interpolate(xi,yi,x)
        self.plotFigureAngle.plot(x,y,color=color_angle)

        self.plotFigurelin.scatter(self.Cal1D[ch,mode,:,0],self.Cal1D[ch,mode,:,1], color=color_amp, marker='x')
        self.plotFigurelin.scatter(self.Cal1D[ch,mode,dig_index,0],self.Cal1D[ch,mode,dig_index,1],color=color_highlight, marker='o')
        self.plotFigureAngle.scatter(self.Cal1D[ch,mode,:,0],self.Cal1D[ch,mode,:,2],color=color_angle,marker='*' )
        self.plotFigureAngle.scatter(self.Cal1D[ch,mode,dig_index,0],self.Cal1D[ch,mode,dig_index,2],color=color_highlight, marker='o')
        self.plotFigureAngle.set_ylim(-180,180)
        
        self.plotFigurelin.axis([0,x_ax_max*1.1,0,U_max])
        self.plotFigurelin.set_xlabel('Digital Value')
        self.plotFigurelin.set_ylabel('Output in V',color='tab:blue')
        self.plotFigureAngle.set_ylabel('Phase in °',color='tab:red')
        self.plotFigureAngle.yaxis.set_label_position('right')
        self.plotFigurelin.set_title('Channel ' + str(ch+1) + ', Mode: ' +str(mode))
        self.Figurelin.tight_layout()
        self.Figurelin.canvas.draw()

    def set_Modulators(self):
        '''Updates the modulators.'''
        CB=STASIS_Control.ControlByteObj 
        bitstream=STASIS_Control.STASIS_System.Modulator.return_byte_stream()
        start_adress = STASIS_Control.STASIS_System.Modulator.start_address
        bitstream_adress = bytes([CB.enable, start_adress-1+self.active_channel,0,0]) #sending this word as final word lets the active channels LED light up and sets the system transmit.
        bitstream_enable_mod = bytes([CB.clock,0,0,0])
        bitstream = bitstream +bitstream_enable_mod+ bitstream_adress
        try:
            STASIS_Control.STASIS_System.SPI.send_bitstream(bitstream)
            sleep(0.05)
            STASIS_Control.STASIS_System.SPI.send_bitstream(bitstream_enable_mod+bitstream_enable_mod+bitstream_adress)
            sleep(0.05)
        except:
            print('Error! Could not transmit via SPI.')
            sleep(0.005)
    
    def update(self):
        '''Calls functions for updating the figure and setting the Modulators. (self.plotFigure() and self.set_Modulators)'''
        I_values=[0]*self.number_of_channels
        Q_values=[0]*self.number_of_channels
        
        for a in range(self.number_of_channels): #Set all values for I and Q to calibrated zero, to make sure no transmit happens.
            I_values[a]=pow(2,13)-1 + self.IQoffset[a][0]
            Q_values[a]=pow(2,13)-1 + self.IQoffset[a][1]
        

        ch=self.active_channel-1
        mode=self.Amp_Mode.get()
        dig_index=self.dig_index
        self.plotFigurelin.clear()
        self.entry_degree.delete('0',END)
        self.entry_db.delete('0',END)

        I_values[ch]=int(I_values[ch]+self.Cal1D[ch,mode,dig_index,0]) #For measurement, add the current digital value to zero point.

        STASIS_Control.STASIS_System.Modulator.I_values=I_values
        STASIS_Control.STASIS_System.Modulator.Q_values=Q_values
        STASIS_Control.STASIS_System.Modulator.counter_max=[1]*self.number_of_channels
        STASIS_Control.STASIS_System.Modulator.Amp_state=[mode]*self.number_of_channels
        self.set_Modulators() #Set the Modulators to the values just provided.

        if dig_index==0:
            self.entry_db.insert('0','-inf')
            self.entry_degree.insert('0','n.a.')
            self.entry_db.config(state='readonly')
            self.entry_degree.config(state='readonly')
        else:
            self.entry_db.config(state='normal')
            self.entry_degree.config(state='normal')
            self.entry_degree.delete('0',END)
            self.entry_db.delete('0',END)

        current_dB = 20*math.log10((self.Cal1D[ch,mode,dig_index,1]+0.000001)/U_0dBm)
        current_deg = self.Cal1D[ch,mode,dig_index,2]

        
        self.entry_db.insert('0',str(current_dB))
        self.entry_degree.insert('0',str(current_deg))

        self.plotFigure()

    def saveClose(self):
        '''Function for closing the calibration Window. Also calls the "write_1D_Cal" method of the Modulator-Object and disables the system.'''
        try:
            STASIS_Control.STASIS_System.disable_system()
        except:
            print('Error! Could not transmit via SPI.')
        STASIS_Control.STASIS_System.Modulator.Cal1D=self.Cal1D #Write the new calibration data into the Modulator.
        STASIS_Control.STASIS_System.Modulator.write_1D_Cal()
        self.WindowMain.destroy()
            

