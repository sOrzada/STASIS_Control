'''GUIs for calibration of STASIS System.'''
from tkinter import *
import STASIS_Control
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from PIL import Image, ImageTk
from time import sleep

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
        self.plotFigureOffset.set_xlabel('I')
        self.plotFigureOffset.set_ylabel('Q')
        self.plotFigureOffset.set_title('Channel ' + str(self.active_channel))
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
        self.dig_value = 0  #Always start with the first digital value (which is 0, so no danger to components or people)
        self.max_dig_value = STASIS_Control.STASIS_System.Modulator.number_of_1D_samples #Maximum number of 1D samples.
        #Initiate Amplitudes, Phases and States(for the purpose of this Calibration step, the letter is unimportant, but needs to be set anyway)
        self.amplitudes = list([0])*self.number_of_channels
        self.phases = [0]*self.number_of_channels
        self.states = [0]*self.number_of_channels

    def openGUI(self):
        '''Prepares and Opens the GUI or this Class Object.'''
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
        self.init_dig_value_select(x_center=150,y_center=180)

        #Initialize Figure for linearity results
        self.Figurelin = Figure(figsize=(5,5), dpi=80)
        self.plotFigurelin = self.Figurelin.add_subplot(111)
        self.canvasFigurelin = FigureCanvasTkAgg(self.Figurelin, master=self.WindowMain)
        self.canvasFigurelin.get_tk_widget().place(x=500, y=250, anchor='center')

        #Update
        self.update()

        #Set Timings for Calibration: 10% Duty Cycle, 1ms pulses
        STASIS_Control.STASIS_System.disable_system()
        STASIS_Control.STASIS_System.TimingControl.clock_divider=1000
        STASIS_Control.STASIS_System.TimingControl.counter_Tx=10
        STASIS_Control.STASIS_System.TimingControl.counter_Rx=90
        STASIS_Control.STASIS_System.TimingControl.set_alternating_mode()
        STASIS_Control.STASIS_System.SignalSource.set_external()

    def init_radiobuttons(self, x_start, y_start):
        self.Amp_Mode=IntVar()
        R1= Radiobutton(self.WindowMain, text='Low Power Mode', variable=self.Amp_Mode, value=0, command=self.sel)
        R1.place(x=x_start,y=y_start,anchor=W)
        R2= Radiobutton(self.WindowMain, text='High Power Mode', variable=self.Amp_Mode, value=1, command=self.sel)
        R2.place(x=x_start,y=y_start+20,anchor=W)
    
    def init_dig_value_select(self, x_center, y_center): #Initialize Buttons and Label for Channel selection
        '''Initializes the channel selection interface at the coordinates specified by x_center and y_center.'''
        Button_prev = Button(self.WindowMain, width=3,height=1, text='<', command=lambda: self.dig_value_select(-1))
        Button_next = Button(self.WindowMain, width=3,height=1, text='>', command=lambda: self.dig_value_select(+1))
        self.label_dig_value = Label(self.WindowMain, height=1, width=6, text=str(0), relief='sunken', bg='white')
        Button_prev.place(x=x_center-50,y=y_center,anchor='center')
        self.label_dig_value.place(x=x_center,y=y_center, anchor='center')
        Button_next.place(x=x_center+50,y=y_center, anchor='center')
    
    def dig_value_select(self,a):
        self.dig_value=self.dig_value+a
        if self.dig_value<0:
            self.dig_value=0
        if self.dig_value>self.max_dig_value-1:
            self.dig_value=self.max_dig_value-1
        
        self.label_dig_value.config(text=str(int(self.Cal1D[self.active_channel,self.Amp_Mode.get(),self.dig_value,0])))
        self.update()

    def sel(self):
        self.update()

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
        ch=self.active_channel
        mode=self.Amp_Mode.get()
        dig_value=self.dig_value
        self.plotFigurelin.clear()
        
        self.plotFigurelin.scatter(self.Cal1D[ch,mode,:,0],self.Cal1D[ch,mode,:,1], marker='x')
        self.plotFigurelin.scatter(self.Cal1D[ch,mode,dig_value,0],self.Cal1D[ch,mode,dig_value,1], marker='o')

        self.plotFigurelin.axis([0,pow(2,14)-1,0,270])
        self.plotFigurelin.set_xlabel('Digital Value')
        self.plotFigurelin.set_ylabel('Output in V')
        self.plotFigurelin.set_title('Channel ' + str(ch) + ', Mode: ' +str(mode))
        self.Figurelin.canvas.draw()
        
    
    def update(self):
        '''Calls functions for updating the figure and setting the Modulators. (self.plotFigure() and self.set_Modulators)'''
        self.plotFigure()
        
        #self.set_Modulators()

    def saveClose(self):
        '''Function for closing the calibration Window. Also calls the "write_IQ_offset" method of the Modulator-Object.'''
        
        #STASIS_Control.STASIS_System.Modulator.IQoffset = self.IQoffset
        #STASIS_Control.STASIS_System.Modulator.write_IQ_offset()
        self.WindowMain.destroy()
        pass    

#CalGUI = CalibrateZeroObj()
#CalGUI.openGUI()
#CalGUI.mainloop()
