import STASIS_Control #Contains definition of Hardware and Initializes Hardware.
import pathlib
import scipy
import numpy as np
import configparser
from time import sleep
import os
from tkinter import *
from tkinter import scrolledtext
from tkinter import filedialog
from tkinter.messagebox import askyesno
import STASIS_PulseTool
import re
import STASIS_Calibration
import pickle
from PIL import Image, ImageTk

# This is my first attempt on writing python code. Please be patient with me.

### Define GUI ###

def start_main_GUI():
    global MAINWINDOW
    global text_box
    global StartButton
    MAINWINDOW = Tk()
    MAINWINDOW.title('STASIS Control')
    MAINWINDOW.config(width=800, height=600)
    MAINWINDOW.resizable(False,False)
    MAINWINDOW.protocol('WM_DELETE_WINDOW', on_closing)
    MAINWINDOW.iconbitmap(os.path.dirname(__file__) + r'\images\S_square_32x32.ico')
    init_Menu(MAINWINDOW)
    text_box = scrolledtext.ScrolledText(MAINWINDOW, width = 45, height =30)
    text_box.place(x=400,y=60)
    status_label = Label(MAINWINDOW, text='System Settings')
    status_label.place(x=600,y=40, anchor=CENTER)
    StartButton = Button(MAINWINDOW, text='Apply & Start', command = start_system_dialog)
    StartButton.place(relx=0.15, rely=0.85, anchor=CENTER, width=150, height=50)
    StopButton = Button(MAINWINDOW, text='STOP', command = stop_system, bg='red')
    StopButton.place(relx=0.35, rely=0.85, anchor=CENTER, width=150, height=50)

    #Options Checkbuttons here:
    LabelsCheckButtons = ['Continous Mode','Modulator Reset from Timing Control','External RF source']
    global OptionsCheckButtons
    OptionsCheckButtons = []
    global ValuesCheckButtons
    ValuesCheckButtons = [0,0,0]
    
    for a in range(3):
        ValuesCheckButtons[a] = IntVar()
        OptionsCheckButtons.append(Checkbutton(MAINWINDOW, variable=ValuesCheckButtons[a], text=LabelsCheckButtons[a]))
        OptionsCheckButtons[a].place(x=30, y=50+a*30)
        OptionsCheckButtons[a].config(command=lambda: clickOptionsButton(ValuesCheckButtons))

    #Inputs for Timing Control here:
    global TimingEntry
    TimingEntry = []
    TimingEntryInput = [0,0,0]
    TimingEntryLabel = []
    LabelsTimingEntryLabel = ['Clock Division', 'Tx Clock Cycles', 'Rx Clock Cycles']
    ApplyTimingsButton = Button(MAINWINDOW, text='Set Timings', command=lambda: validateTimingEntry(TimingEntryInput, TimingEntry))
    for a in range(3):
        TimingEntryInput[a]=StringVar()
        TimingEntry.append(Entry(MAINWINDOW, textvariable=TimingEntryInput[a]))
        TimingEntryLabel.append(Label(MAINWINDOW, text=LabelsTimingEntryLabel[a]))    
        TimingEntry[a].place(x=40, y=140+a*30, width=50)
        TimingEntryLabel[a].place(x=90, y=140+a*30)
    TimingEntry[0].insert(0,str(STASIS_Control.STASIS_System.TimingControl.clock_divider))
    TimingEntry[1].insert(0,str(STASIS_Control.STASIS_System.TimingControl.counter_Tx))
    TimingEntry[2].insert(0,str(STASIS_Control.STASIS_System.TimingControl.counter_Rx))
    ApplyTimingsButton.place(x=210, y=165)
    update_status_text()

    return MAINWINDOW

def init_Menu(MainWindow): #Initialize the menu bar of main window.
    MenuBar=Menu(MainWindow)
    MainWindow.config(menu=MenuBar)
    
    FileMenu = Menu(MenuBar, tearoff = 0)
    MenuBar.add_cascade(label='File', menu=FileMenu)
    FileMenu.add_command(label= 'Load System State...', command=openFile)
    FileMenu.add_command(label= 'Save System State...', command=saveFile)
    FileMenu.add_separator()
    FileMenu.add_command(label = 'Quit', command = quit)
    
    ModulatorSettingsMenu = Menu(MenuBar, tearoff = 0)
    MenuBar.add_cascade(label='Modulators', menu=ModulatorSettingsMenu)
    ModulatorSettingsMenu.add_command(label = 'Set Shim', command = setShim)
    ModulatorSettingsMenu.add_command(label = 'Pulse Tool', command = pulseTool)
    ModulatorSettingsMenu.add_separator()
    ModulatorSettingsMenu.add_command(label= 'Load Pulse...', command=loadPulse)
    ModulatorSettingsMenu.add_command(label= 'Save Pulse...', command=savePulse)
    ModulatorSettingsMenu.add_separator()
    ModulatorSettingsMenu.add_command(label = 'Load External Pulse...', command = externalPulse)

    CalibrationMenu = Menu(MenuBar, tearoff = 0)
    MenuBar.add_cascade(label='Calibration', menu=CalibrationMenu)
    CalibrationMenu.add_command(label = 'Zero Offset Calibration', command = calibrateSystemZero)
    CalibrationMenu.add_command(label = 'Linearity Calibration', command = calibrateSystemLin1D)
    CalibrationMenu.add_command(label = 'Power Level Calibration', command = calibratePowerLevel)

    HelpMenu = Menu(MenuBar, tearoff = 0)
    MenuBar.add_cascade(label='Help', menu=HelpMenu)
    HelpMenu.add_command(label = 'Help', command = callHelp)
    HelpMenu.add_command(label = 'About', command = aboutInfo)

def on_closing():
    MAINWINDOW.destroy()
    stop_system()
    quit()

def clickOptionsButton(Values):
    if Values[0].get()==1:
        STASIS_Control.STASIS_System.TimingControl.set_continous_mode()
    else:
        STASIS_Control.STASIS_System.TimingControl.set_alternating_mode()

    STASIS_Control.STASIS_System.TimingControl.mod_res_sel=Values[1].get()

    if Values[2].get()==1:
        STASIS_Control.STASIS_System.SignalSource.set_external()
    else:
        STASIS_Control.STASIS_System.SignalSource.set_internal()
    
    update_status_text()

def openFile(): #ToDo: Check functionality of SPI-Object!
    f_name=filedialog.askopenfile(mode='rb', filetypes=(('System State','*.sav'),), defaultextension=(('System State','*.sav'),))
    STASIS_Control.STASIS_System = pickle.load(f_name)
    update_status_text()

def saveFile(): # ToDo: Check functionality of SPI-Object!
    f_name=filedialog.asksaveasfile(mode='wb', filetypes=(('System State','*.sav'),), defaultextension=(('System State','*.sav'),))
    pickle.dump(STASIS_Control.STASIS_System, f_name, pickle.HIGHEST_PROTOCOL)

def loadPulse():
    '''Loads a pulse (Amplitude, Phase, State) and applies this to modulators (this includes a normalization from calibration)'''
    f_name=filedialog.askopenfile(mode='rb', filetypes=(('STASIS Pulse File','*.pls'),), defaultextension=(('STASIS Pulse File','*.pls'),))
    pulse = pickle.load(f_name)
    STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state(pulse.Amplitudes,pulse.Phases,pulse.States)
    update_status_text()

def savePulse():
    '''Saves the current pulse (Amplitude, Phase, State)'''
    pulse=STASIS_Control.PulseObj()
    pulse.Amplitudes = STASIS_Control.STASIS_System.Modulator.amplitudes
    pulse.Phases = STASIS_Control.STASIS_System.Modulator.phases
    pulse.States = STASIS_Control.STASIS_System.Modulator.Amp_state

    f_name=filedialog.asksaveasfile(mode='wb', filetypes=(('STASIS Pulse File','*.pls'),), defaultextension=(('STASIS Pulse File','*.pls'),))
    pickle.dump(pulse, f_name, pickle.HIGHEST_PROTOCOL)
    pass

def externalPulse():
    '''Enables loading of external pulses from Python or Matlab\n
    The file must contain a matlab array called 'pulse' or numpy array\n
    The size must be [number of channels, number of samples, 3]\n
    The last dimension contains: Amplitudes in V, Phase in degree, amplifier state (0 for low power, 1 for high power)'''
    f_name=filedialog.askopenfile(mode='rb', filetypes=([('Matlab file','*.mat'),('Numpy file','.npy')]), defaultextension=(('Matlab file','*.mat'),))
    extension=pathlib.Path(f_name.name).suffix
    
    match extension:
        case '.mat':
            mat_contents=scipy.io.loadmat(f_name)
            loaded_pulse=mat_contents['pulse']
        case '.npy':
            loaded_pulse=np.load(f_name)

    size_pulse_array=loaded_pulse.shape #Dimensions should be as follows: [Nch, Nsamples, 3], where dimension 3 is 1) Amplitude in V, 2) Phase in degree, 3) Amplifier state
    Amplitudes=[0]*size_pulse_array[0]
    Phases=[0]*size_pulse_array[0]
    States=[0]*size_pulse_array[0]
    for a in range(size_pulse_array[0]):
        Amplitudes[a]=[]
        Phases[a]=[]
        States[a]=[]
        for b in range(size_pulse_array[1]):
            Amplitudes[a].append(float(loaded_pulse[a,b,0]))
            Phases[a].append(float(loaded_pulse[a,b,1]))
            States[a].append(int(loaded_pulse[a,b,2]))
    STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state(Amplitudes,Phases,States)
    update_status_text()
                
    

def validateTimingEntry(TimingEntryInput, TimingEntry):
    '''Checks Timings for Validity (max 2^16, only numbers) and applies settings'''
    try:
        value = int(TimingEntryInput[0].get())
        if value <= pow(2,16)-1:
            STASIS_Control.STASIS_System.TimingControl.clock_divider=value
        else:
            STASIS_Control.STASIS_System.TimingControl.clock_divider=pow(2,16)-1
    except:
        pass
    try:
        value = int(TimingEntryInput[1].get())
        if value <= pow(2,16)-1:
            STASIS_Control.STASIS_System.TimingControl.counter_Tx=value
        else:
            STASIS_Control.STASIS_System.TimingControl.counter_Tx=pow(2,16)-1
    except:
        pass
    try:
        value = int(TimingEntryInput[2].get())
        if value <= pow(2,16)-1:
            STASIS_Control.STASIS_System.TimingControl.counter_Rx=value
        else:
            STASIS_Control.STASIS_System.TimingControl.counter_Rx=pow(2,16)-1
    except:
        pass
    for a in range(3):
        TimingEntry[a].delete(0,END)
    TimingEntry[0].insert(0,str(STASIS_Control.STASIS_System.TimingControl.clock_divider))
    TimingEntry[1].insert(0,str(STASIS_Control.STASIS_System.TimingControl.counter_Tx))
    TimingEntry[2].insert(0,str(STASIS_Control.STASIS_System.TimingControl.counter_Rx))
    update_status_text()

def start_system_dialog():
    if askyesno('Start System?', 'This will switch on the system and transmit power. Are you sure?'):
        start_system()
    else:
        pass

def start_system():
    STASIS_Control.STASIS_System.setup_system()
    STASIS_Control.STASIS_System.enable_system()

def stop_system():
    STASIS_Control.STASIS_System.disable_system()

def setShim(): #Manually set a simple shim by typing into a textbox.
    mainwindow_posx=MAINWINDOW.winfo_x()
    mainwindow_posy=MAINWINDOW.winfo_y()
    setShimWindow = Tk()
    setShimWindow.config(width=600, height=210)
    setShimWindow.geometry('%dx%d+%d+%d' % (600, 210, mainwindow_posx+50, mainwindow_posy+150))
    setShimWindow.title('Set simple shim')
    setShimWindow.iconbitmap(os.path.dirname(__file__) + r'\images\S_square_32x32.ico')
    shim_set_text = scrolledtext.ScrolledText(setShimWindow, width = 40, height =10)
    shim_set_text.place(x=50,y=10)
    shim_string=str('')
    
    Amp_State_Radiobuttons = []
    amp_state_select=IntVar()
    Amp_State_Radiobuttons.append(Radiobutton(setShimWindow,variable=amp_state_select, value=0, text='Low Power'))
    Amp_State_Radiobuttons.append(Radiobutton(setShimWindow,variable=amp_state_select, value=1, text='High Power'))
    Amp_State_Radiobuttons[0].place(x=400,y=40)
    Amp_State_Radiobuttons[1].place(x=400,y=70)
    setShim_Button = Button(setShimWindow, text='Apply', command =  lambda: setShim_Button_Press(shim_set_text.get("1.0",END), amp_state_select.get(),setShimWindow))
    setShim_Button.place(x=490,y=140, anchor=CENTER, width=100)
    for a in range(STASIS_Control.STASIS_System.Modulator.number_of_channels):
        shim_string = shim_string + str(STASIS_Control.STASIS_System.Modulator.amplitudes[a][0]) + ', ' + str(STASIS_Control.STASIS_System.Modulator.phases[a][0])
        if a < STASIS_Control.STASIS_System.Modulator.number_of_channels-1:
            shim_string = shim_string + '\n'
    
    shim_set_text.insert(INSERT,shim_string)

def setShim_Button_Press(text_in,amp_state_select,window):
    
    amplitudes = [0]*STASIS_Control.STASIS_System.Modulator.number_of_channels
    phases = [0]*STASIS_Control.STASIS_System.Modulator.number_of_channels
    amp_state = [(amp_state_select)]*STASIS_Control.STASIS_System.Modulator.number_of_channels
    numbers = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", text_in) #This line finds the numbers in text. Thanks: https://stackoverflow.com/questions/385558/extract-float-double-value
    b=0
    for a in range(STASIS_Control.STASIS_System.Modulator.number_of_channels):
        amplitudes[a]=[float(numbers[b]),float(numbers[b])]
        phases[a]=[float(numbers[b+1]),float(numbers[b+1])]
        amp_state[a]=[int(amp_state_select),int(amp_state_select)]
        b=b+2
    
    STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state(amplitudes,phases,amp_state)
    update_status_text()
    window.destroy()
    


def pulseTool():
    p.openGUI()
    p.WindowMain.wait_window(p.WindowMain)
    update_status_text()
    
def callHelp():
    pass

def aboutInfo():
    aboutWindow = Toplevel()
    aboutWindow.config(height=400,width=400)
    aboutWindow.resizable(False,False)
    aboutWindow.title('Info')
    aboutWindow.iconbitmap(os.path.dirname(__file__) + r'\images\S_square_32x32.ico')
    aboutLabel = Label(aboutWindow, text='\nSTASIS Control Software\nThis program was written by\nStephan Orzada\nat the German Cancer Center (DKFZ)\nStephan.Orzada@dkfz.de\n')
    aboutLabel.place(x=200,y=180, anchor=CENTER)
    okButton = Button(aboutWindow, text='OK', command = aboutWindow.destroy)
    okButton.place(relx=0.5, rely=0.85, anchor=CENTER, width=100)
    aboutLabel.config(width=40, height=15)

    #STASIS Logo:
    image_path_stasis=os.path.dirname(__file__) + r'\Images\csm_STASIS_logo_dadfd3b026.jpg'
    ph1=Image.open(image_path_stasis)
    ph1=ph1.resize((256,114), resample=1)
    ph1=ImageTk.PhotoImage(ph1)
    label_image1 = Label(aboutWindow, image=ph1)
    label_image1.place(x=200,y=70, anchor='center')
    
    #DKFZ Logo:
    image_path_stasis=os.path.dirname(__file__) + r'\Images\dkfz-logo2.png'
    ph2=Image.open(image_path_stasis)
    ph2=ph2.resize((181,54), resample=1)
    ph2=ImageTk.PhotoImage(ph2)
    label_image2 = Label(aboutWindow, image=ph2)
    label_image2.place(x=200,y=270, anchor='center')
    aboutWindow.grab_set()

    aboutWindow.mainloop()

def calibrateSystemZero():
    cal_zero.openGUI()
    #MAINWINDOW.withdraw()
    cal_zero.WindowMain.grab_set()
    cal_zero.WindowMain.wait_window(cal_zero.WindowMain)
    #MAINWINDOW.deiconify()
    update_status_text()

def calibrateSystemLin1D():
    cal_lin1D.openGUI()
    cal_lin1D.WindowMain.grab_set()
    cal_lin1D.WindowMain.wait_window(cal_lin1D.WindowMain)
    #MAINWINDOW.deiconify()
    update_status_text()

def calibratePowerLevel():
    cal_PowerLevel.openGUI()
    cal_PowerLevel.WindowMain.grab_set()
    cal_PowerLevel.WindowMain.wait_window(cal_PowerLevel.WindowMain)
    update_status_text()

def update_status_text():
    text_box.config(state=NORMAL)
    text_box.delete('1.0', END)
    #status_text = []

    clock_f=10e6/STASIS_Control.STASIS_System.TimingControl.clock_divider
    t_Rx=STASIS_Control.STASIS_System.TimingControl.counter_Rx/clock_f
    t_Tx=STASIS_Control.STASIS_System.TimingControl.counter_Tx/clock_f
    duty_cycle = t_Tx/(t_Rx+t_Tx)*100
    status_text= ' Clock Frequency: ' + str(clock_f/1000) + ' kHz\n'

    for a in range(3):
        TimingEntry[a].delete('0',END)

    TimingEntry[0].insert(0,str(STASIS_Control.STASIS_System.TimingControl.clock_divider))
    TimingEntry[1].insert(0,str(STASIS_Control.STASIS_System.TimingControl.counter_Tx))
    TimingEntry[2].insert(0,str(STASIS_Control.STASIS_System.TimingControl.counter_Rx))

    ValuesCheckButtons[0].set(STASIS_Control.STASIS_System.TimingControl.con_mode)
    ValuesCheckButtons[1].set(STASIS_Control.STASIS_System.TimingControl.mod_res_sel)
    ValuesCheckButtons[2].set(abs(STASIS_Control.STASIS_System.SignalSource.source-1))

    if STASIS_Control.STASIS_System.TimingControl.con_mode == 1:
        duty_cycle = 100
        status_text = status_text + ' Mode: Continous\n\n'
    else:
        status_text = status_text + ' Transmit Time  : ' + str(round(t_Tx*1000,4)) + ' ms\n'\
                                  + ' *Receive* Time : ' + str(round(t_Rx*1000,4)) + ' ms\n'\
                                  + ' Duty Cycle     : ' + str(round(duty_cycle,4)) + '%\n\n'
    if STASIS_Control.STASIS_System.TimingControl.mod_res_sel == 1:
        status_text = status_text + ' Modulator Reset from Timing Control active. If you see (!) not all samples in this channel are played out.\n\n'
    
    if STASIS_Control.STASIS_System.SignalSource.source == 0:
        status_text = status_text + ' External RF source.\n\n'
    else:
        status_text = status_text + ' Internal RF source.\n\n'

    status_text = status_text + ' Number of Channels: ' + str(STASIS_Control.STASIS_System.Modulator.number_of_channels) + '\n\n'\
                              + 'Channel\tsamples\tVrms,p\tP_RMS\n'
    show_decimals = 2
    RMS_total = 0
    for a in range(STASIS_Control.STASIS_System.Modulator.number_of_channels):
        
        RMS_value=0
        if STASIS_Control.STASIS_System.TimingControl.mod_res_sel == 1 and STASIS_Control.STASIS_System.Modulator.counter_max[a]>STASIS_Control.STASIS_System.TimingControl.counter_Tx:
            
            for samples in range(STASIS_Control.STASIS_System.TimingControl.counter_Tx):
                RMS_value = RMS_value + pow(STASIS_Control.STASIS_System.Modulator.amplitudes[a][samples],2)/50
            RMS_value = round(RMS_value/STASIS_Control.STASIS_System.TimingControl.counter_Tx * duty_cycle/100,show_decimals)
            status_text = status_text + str(a+1) +'\t' +str(STASIS_Control.STASIS_System.Modulator.counter_max[a]) + '\t' + str(round(np.max(STASIS_Control.STASIS_System.Modulator.amplitudes[a]),show_decimals)) + 'V\t'+ str(RMS_value) + 'W(!)\n'
        else:
            if STASIS_Control.STASIS_System.Modulator.counter_max[a] > 1:
                for samples in range(STASIS_Control.STASIS_System.Modulator.counter_max[a]):
                    RMS_value = RMS_value + pow(STASIS_Control.STASIS_System.Modulator.amplitudes[a][samples],2)/50
            else:
                RMS_value = pow(STASIS_Control.STASIS_System.Modulator.amplitudes[a],2)/50
            RMS_value = round(RMS_value/STASIS_Control.STASIS_System.Modulator.counter_max[a] * duty_cycle/100,show_decimals)
            RMS_total = RMS_total + RMS_value
            status_text = status_text + str(a+1) +'\t' + str(STASIS_Control.STASIS_System.Modulator.counter_max[a]) + '\t' + str(round(np.max(STASIS_Control.STASIS_System.Modulator.amplitudes[a]),show_decimals)) + 'V\t'+ str(RMS_value) + 'W\n'
    status_text = status_text + '\nTotal RMS Power: ' + str(round(RMS_total,show_decimals)) + ' W\n'   
    pulseInfo = check_pulse()
    if pulseInfo[0]:
        status_text = status_text + pulseInfo[1]
        StartButton.config(state='disabled')
    else:
        StartButton.config(state='normal')
    
    text_box.insert('1.0',status_text)
    text_box.config(state=DISABLED)

def check_pulse():
    '''This function checks whether the pulse and timings are within specified limits'''
    #Get limits defined in config file:
    maxAmpHigh = float(STASIS_Control.STASIS_System.config_data['Amplifiers']['max_amplitude_high'])
    maxAmpLow = float(STASIS_Control.STASIS_System.config_data['Amplifiers']['max_amplitude_low'])
    maxDutyHigh = float(STASIS_Control.STASIS_System.config_data['Amplifiers']['max_duty_high_percent'])
    maxDutyLow = float(STASIS_Control.STASIS_System.config_data['Amplifiers']['max_duty_low_percent'])
    maxPulseDurationHigh = float(STASIS_Control.STASIS_System.config_data['Amplifiers']['max_pulse_high_duration_ms'])
    maxRMSLow = float(STASIS_Control.STASIS_System.config_data['Amplifiers']['max_rms_power_low'])
    #Get Timings:
    samplesRx = STASIS_Control.STASIS_System.TimingControl.counter_Rx
    samplesTx = STASIS_Control.STASIS_System.TimingControl.counter_Tx
    clockDivider = STASIS_Control.STASIS_System.TimingControl.clock_divider
    conMode = STASIS_Control.STASIS_System.TimingControl.con_mode
    #Get number of channels:
    numberOfChannels = STASIS_Control.STASIS_System.Modulator.number_of_channels
    #Get pulse data:
    pulseAmp=STASIS_Control.STASIS_System.Modulator.amplitudes
    modeAmp=STASIS_Control.STASIS_System.Modulator.Amp_state

    #Output Text
    outText = '\n***WARNING***\n'
    #Error State
    ErrorState = FALSE

    pulseLength = clockDivider/10e6 * samplesTx * 1000 #Calculate Pulse Length in ms
    pulseDurationHigh=[0]*numberOfChannels

    #Duty Cycle Calculation:
    weightHigh = 100/maxDutyHigh
    weightLow = 100/maxDutyLow
    totalWeight = [0]*numberOfChannels #total dutycycle weight per channel
    samplesHigh = [0]*numberOfChannels
    samplesLow = [0]*numberOfChannels
    if conMode == 1:
        duty_cycle = 1
    else:
        duty_cycle = samplesTx/(samplesRx + samplesTx)

    peakAmpLow=0 #Highest amplitude in "low" mode
    peakAmpHigh=0 #Highest amplitude in "high" mode
    for a in range(numberOfChannels):
        
        if isinstance(pulseAmp[a],list):
            numberOfSamples=len(pulseAmp[a])

            for b in range(numberOfSamples):
                #Find max amplitude sorted by AmpMode:
                if modeAmp[a][b]==0:
                    totalWeight[a]=totalWeight[a]+(weightLow/numberOfSamples*duty_cycle)
                    samplesLow[a]=samplesLow[a]+1
                    if pulseAmp[a][b]>peakAmpLow:
                        peakAmpLow=pulseAmp[a][b]
                else:
                    totalWeight[a]=totalWeight[a]+(weightHigh/numberOfSamples*duty_cycle)
                    samplesHigh[a]=samplesHigh[a]+1
                    if pulseAmp[a][b]>peakAmpHigh:
                        peakAmpHigh=pulseAmp[a][b]
            pulseDurationHigh[a]=pulseLength*samplesHigh[a]/numberOfSamples
        else:
            numberOfSamples=1
            if modeAmp[a]==0:
                totalWeight[a]=weightLow*duty_cycle
                samplesLow[a]=1
                peakAmpLow=pulseAmp[a]
            else:
                totalWeight[a]=weightHigh*duty_cycle
                samplesHigh[a]=1
                peakAmpHigh=pulseAmp[a]
            pulseDurationHigh[a]=pulseLength*samplesHigh[a]/numberOfSamples
    
    

    if max(pulseDurationHigh) > maxPulseDurationHigh:
        ErrorState = TRUE
        outText = outText + 'Pulselength High Mode too long!\n'

    if max(totalWeight)>1.001: #Allow 0.1% Error for calculation, otherwise 20% in the config file might only be 19.999% or similar.
        ErrorState=TRUE
        outText = outText + 'Duty Cycle to high!\n'

    
    
    if peakAmpLow>maxAmpLow*1.001:
        outText = outText + 'Too high voltage in low power mode!\n'
        ErrorState=TRUE
    if peakAmpHigh>maxAmpHigh*1.001:
        outText = outText + 'Too high voltage in high power mode!\n'
        ErrorState=TRUE
    
    

    return [ErrorState, outText]



    



###### Start Programm ######

### Load Configuration file ###
#config=configparser.ConfigParser()
#config.read(os.path.dirname(__file__) + '/STASIS_config.ini')

### Instance Hardware Objects ##

#STASIS_Control.STASIS_System = STASIS_Control.STASIS_SystemObj(config)
amplitudes=[10]*8
phases=[45/180*np.pi]*8
amp_state=[0]*8
for channel in range(8):
   amplitudes[channel]=[20,20]
   phases[channel]=[0,45/180*np.pi]
   amp_state[channel]=[0,0]


STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state(amplitudes,phases,amp_state)

### Start GUI ###
p=STASIS_PulseTool.PulseToolObj()
cal_zero=STASIS_Calibration.CalibrateZeroObj()
cal_lin1D=STASIS_Calibration.CalibrateLinearity1DObj()
cal_PowerLevel=STASIS_Calibration.CalibratePowerLevelObj()
MAINWINDOW = start_main_GUI()





MAINWINDOW.mainloop()



