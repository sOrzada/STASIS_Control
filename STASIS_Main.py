import STASIS_Control #Contains definition of Hardware and Initializes Hardware.
import ft4222 #Library for SPI device
import math
import numpy as np
import configparser
from time import sleep
import os
from tkinter import *
from tkinter import scrolledtext
from tkinter.messagebox import askyesno
import STASIS_PulseTool
import re

### Define GUI ###


def start_main_GUI():
    global MAINWINDOW
    global text_box
    MAINWINDOW = Tk()
    MAINWINDOW.title('STASIS Control')
    MAINWINDOW.config(width=800, height=600)
    MAINWINDOW.resizable(False,False)
    MAINWINDOW.protocol('WM_DELETE_WINDOW', on_closing)
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
    OptionsCheckButtons = []
    ValuesCheckButtons = [0,0,0]
    
    for a in range(3):
        ValuesCheckButtons[a] = IntVar()
        OptionsCheckButtons.append(Checkbutton(MAINWINDOW, variable=ValuesCheckButtons[a], text=LabelsCheckButtons[a]))
        OptionsCheckButtons[a].place(x=30, y=50+a*30)
        OptionsCheckButtons[a].config(command=lambda: clickOptionsButton(ValuesCheckButtons))

    #Inputs for Timing Control here:
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
    #FileMenu.add_command(label = 'Quit', command = MAINWINDOW.destroy)
    FileMenu.add_command(label = 'Quit', command = quit)
    ModulatorSettingsMenu = Menu(MenuBar, tearoff = 0)
    MenuBar.add_cascade(label='Modulators', menu=ModulatorSettingsMenu)
    ModulatorSettingsMenu.add_command(label = 'Set Shim', command = setShim)
    ModulatorSettingsMenu.add_command(label = 'Load Pulse', command = loadPulse)
    ModulatorSettingsMenu.add_command(label = 'Pulse Tool', command = pulseTool)

    CalibrationMenu = Menu(MenuBar, tearoff = 0)
    MenuBar.add_cascade(label='Calibration', menu=CalibrationMenu)
    CalibrationMenu.add_command(label = 'Calibrate System', command = calibrateSystem)

    HelpMenu = Menu(MenuBar, tearoff = 0)
    MenuBar.add_cascade(label='Help', menu=HelpMenu)
    HelpMenu.add_command(label = 'Help', command = callHelp)
    HelpMenu.add_command(label = 'About', command = aboutInfo)

def on_closing():
    MAINWINDOW.destroy()
    stop_system()
    quit()

def clickOptionsButton(Values):
    STASIS_Control.STASIS_System.TimingControl.con_mode=Values[0].get()
    STASIS_Control.STASIS_System.TimingControl.mod_res_sel=Values[1].get()
    STASIS_Control.STASIS_System.SignalSource.source=1-Values[2].get()
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
    shim_set_text = scrolledtext.ScrolledText(setShimWindow, width = 40, height =10)
    shim_set_text.place(x=50,y=10)
    shim_string=str('')
    setShim_Button = Button(setShimWindow, text='Apply', command = lambda: setShim_Button_Press(shim_set_text.get("1.0",END), amp_state_select,setShimWindow))
    setShim_Button.place(x=490,y=140, anchor=CENTER, width=100)
    Amp_State_Radiobuttons = []
    amp_state_select=0
    Amp_State_Radiobuttons.append(Radiobutton(setShimWindow,variable=amp_state_select, value=0, text='Low Power'))
    Amp_State_Radiobuttons.append(Radiobutton(setShimWindow,variable=amp_state_select, value=1, text='High Power'))
    Amp_State_Radiobuttons[0].place(x=400,y=40)
    Amp_State_Radiobuttons[1].place(x=400,y=70)
    for a in range(STASIS_Control.STASIS_System.Modulator.number_of_channels):
        shim_string = shim_string + str(STASIS_Control.STASIS_System.Modulator.amplitudes[a][0]) + ', ' + str(STASIS_Control.STASIS_System.Modulator.phases[a][0])
        if a < STASIS_Control.STASIS_System.Modulator.number_of_channels-1:
            shim_string = shim_string + '\n'
    
    shim_set_text.insert(INSERT,shim_string)

def setShim_Button_Press(text_in,amp_state_select,window):
    amplitudes = [0]*STASIS_Control.STASIS_System.Modulator.number_of_channels
    phases = [0]*STASIS_Control.STASIS_System.Modulator.number_of_channels
    amp_state = [int(amp_state_select)]*STASIS_Control.STASIS_System.Modulator.number_of_channels
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
    
        
        

def loadPulse():
    pass

def pulseTool():
    p.openGUI()
    MAINWINDOW.withdraw()
    p.pulseToolWindow.wait_window(p.pulseToolWindow)
    MAINWINDOW.deiconify()
    update_status_text()
    
def callHelp():
    pass

def aboutInfo():
    aboutWindow = Tk()
    aboutWindow.resizable(False,False)
    aboutWindow.title('Info')
    aboutLabel = Label(aboutWindow, text='\nSTASIS Control Software\nThis program was written by\nStephan Orzada\nat the German Cancer Center (DKFZ)\nStephan.Orzada@dkfz.de\n')
    aboutLabel.pack()
    okButton = Button(aboutWindow, text='OK', command = aboutWindow.destroy)
    okButton.place(relx=0.5, rely=0.85, anchor=CENTER, width=100)
    aboutLabel.config(width=40, height=15)
    aboutWindow.mainloop()

def calibrateSystem():
    pass

def update_status_text():
    text_box.config(state=NORMAL)
    text_box.delete('1.0', END)
    #status_text = []

    clock_f=10e6/STASIS_Control.STASIS_System.TimingControl.clock_divider
    t_Rx=STASIS_Control.STASIS_System.TimingControl.counter_Rx/clock_f
    t_Tx=STASIS_Control.STASIS_System.TimingControl.counter_Tx/clock_f
    duty_cycle = t_Tx/(t_Rx+t_Tx)*100
    status_text= ' Clock Frequency: ' + str(clock_f/1000) + ' kHz\n'
               
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
    for a in range(STASIS_Control.STASIS_System.Modulator.number_of_channels):
        
        RMS_value=0
        if STASIS_Control.STASIS_System.TimingControl.mod_res_sel == 1 and STASIS_Control.STASIS_System.Modulator.counter_max[a]>STASIS_Control.STASIS_System.TimingControl.counter_Tx:
            for samples in range(STASIS_Control.STASIS_System.TimingControl.counter_Tx):
                RMS_value = RMS_value + pow(STASIS_Control.STASIS_System.Modulator.amplitudes[a][samples],2)/50
            RMS_value = round(RMS_value/STASIS_Control.STASIS_System.TimingControl.counter_Tx * duty_cycle/100,show_decimals)
            status_text = status_text + str(a+1) +'\t' +str(STASIS_Control.STASIS_System.Modulator.counter_max[a]) + '\t' + str(round(max(STASIS_Control.STASIS_System.Modulator.amplitudes[a]),show_decimals)) + 'V\t'+ str(RMS_value) + 'W(!)\n'
        else:
            for samples in range(STASIS_Control.STASIS_System.Modulator.counter_max[a]):
                RMS_value = RMS_value + pow(STASIS_Control.STASIS_System.Modulator.amplitudes[a][samples],2)/50
            RMS_value = round(RMS_value/STASIS_Control.STASIS_System.Modulator.counter_max[a] * duty_cycle/100,show_decimals)
            status_text = status_text + str(a+1) +'\t' + str(STASIS_Control.STASIS_System.Modulator.counter_max[a]) + '\t' + str(round(max(STASIS_Control.STASIS_System.Modulator.amplitudes[a]),show_decimals)) + 'V\t'+ str(RMS_value) + 'W\n'
        
    
    text_box.insert('1.0',status_text)
    text_box.config(state=DISABLED)





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
   amplitudes[channel]=[10,10]
   phases[channel]=[0,45/180*np.pi]
   amp_state[channel]=[1,1]


STASIS_Control.STASIS_System.Modulator.set_amplitudes_phases_state(amplitudes,phases,amp_state)

### Start GUI ###

MAINWINDOW = start_main_GUI()
p=STASIS_PulseTool.PulseToolObj()
MAINWINDOW.mainloop()



