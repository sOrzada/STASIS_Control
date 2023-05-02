from STASIS_Control import STASIS_SystemObj
import ft4222 #Library for SPI device
import math
import numpy as np
import configparser
from ft4222.SPI import Cpha, Cpol
from ft4222.SPIMaster import Mode, Clock, SlaveSelect
from ft4222.GPIO import Port, Dir
from time import sleep
import os
from tkinter import *
from tkinter import scrolledtext
import re

### Define GUI ###


def start_main_GUI():
    global MAINWINDOW
    global STATUS_TEXT_BOX
    MAINWINDOW = Tk()
    MAINWINDOW.title('STASIS Control')
    MAINWINDOW.config(width=800, height=600)
    MAINWINDOW.resizable(False,False)
    init_Menu(MAINWINDOW)
    STATUS_TEXT_BOX = scrolledtext.ScrolledText(MAINWINDOW, width = 45, height =30)
    STATUS_TEXT_BOX.place(x=400,y=60)
    status_label = Label(MAINWINDOW, text='System Settings')
    status_label.place(x=600,y=40, anchor=CENTER)
    okButton = Button(MAINWINDOW, text='Update', command = update_status_text)
    okButton.place(relx=0.5, rely=0.85, anchor=CENTER, width=100)
    OptionsCheckButtons = []
    OptionsCheckButtons.append(Checkbutton(MAINWINDOW, text='Continous Mode'))
    OptionsCheckButtons.append(Checkbutton(MAINWINDOW, text='Modulator Reset from Timing Control'))
    OptionsCheckButtons.append(Checkbutton(MAINWINDOW, text='External RF source'))
    OptionsCheckButtons[0].place(x = 30, y = 50)
    OptionsCheckButtons[1].place(x = 30, y = 80)
    OptionsCheckButtons[2].place(x = 30, y = 110)
    for a in range(3):
        OptionsCheckButtons[a].config(command=lambda: clickOptionsButton(OptionsCheckButtons))
    
    return MAINWINDOW

def init_Menu(MainWindow):
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

def clickOptionsButton(Button):
    pass

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
    for a in range(STASIS_System.Modulator.number_of_channels):
        shim_string = shim_string + str(STASIS_System.Modulator.amplitudes[a][0]) + ', ' + str(STASIS_System.Modulator.phases[a][0])
        if a < STASIS_System.Modulator.number_of_channels-1:
            shim_string = shim_string + '\n'
    
    shim_set_text.insert(INSERT,shim_string)

def setShim_Button_Press(text_in,amp_state_select,window):
    amplitudes = [0]*STASIS_System.Modulator.number_of_channels
    phases = [0]*STASIS_System.Modulator.number_of_channels
    amp_state = [int(amp_state_select)]*STASIS_System.Modulator.number_of_channels
    numbers = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", text_in) #This line finds the numbers in text. Thanks: https://stackoverflow.com/questions/385558/extract-float-double-value
    b=0
    for a in range(STASIS_System.Modulator.number_of_channels):
        amplitudes[a]=[float(numbers[b]),float(numbers[b])]
        phases[a]=[float(numbers[b+1]),float(numbers[b+1])]
        amp_state[a]=[int(amp_state_select),int(amp_state_select)]
        b=b+2
    
    STASIS_System.Modulator.set_amplitudes_phases_state(amplitudes,phases,amp_state)
    update_status_text()
    window.destroy()
    
        
        

def loadPulse():
    pass

def pulseTool():
    pass

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
    STATUS_TEXT_BOX.config(state=NORMAL)
    STATUS_TEXT_BOX.delete('1.0', END)
    #status_text = []

    clock_f=10e6/STASIS_System.TimingControl.clock_divider
    t_Rx=STASIS_System.TimingControl.counter_Rx/clock_f
    t_Tx=STASIS_System.TimingControl.counter_Tx/clock_f
    duty_cycle = t_Tx/(t_Rx+t_Tx)*100
    status_text= ' Clock Frequency: ' + str(clock_f/1000) + ' kHz\n'
               
    if STASIS_System.TimingControl.con_mode == 1:
        duty_cycle = 100
        status_text = status_text + ' Mode: Continous\n'
    else:
        status_text = status_text + ' Transmit Time  : ' + str(t_Tx*1000) + ' ms\n'\
                                  + ' *Receive* Time : ' + str(t_Rx*1000) + ' ms\n'\
                                  + ' Duty Cycle     : ' + str(duty_cycle) + '%\n\n'
    if STASIS_System.TimingControl.mod_res_sel == 1:
        status_text = status_text + ' Modulator Reset from Timing Control active. If you see (!) not all samples in this channel are played out.\n\n'
    
    if STASIS_System.SignalSource.source == 1:
        status_text = status_text + ' External RF source.\n\n'
    else:
        status_text = status_text + ' Internal RF source.\n\n'

    status_text = status_text + ' Number of Channels: ' + str(STASIS_System.Modulator.number_of_channels) + '\n\n'\
                              + ' Channel,\t#samples,\tpeak,\tRMS\n'
    
    for a in range(STASIS_System.Modulator.number_of_channels):
        
        if STASIS_System.TimingControl.mod_res_sel == 1 and STASIS_System.Modulator.counter_max[a]>STASIS_System.TimingControl.counter_Tx:
            RMS_value = sum(STASIS_System.Modulator.amplitudes[a][:STASIS_System.STASIS_System.TimingControl.counter_Tx-1])/(STASIS_System.TimingControl.counter_Tx-1)*duty_cycle/100
            status_text = status_text + ' ' + str(a+1) +',\t' +str(STASIS_System.Modulator.counter_max[a]-1) + '\t' + str(max(STASIS_System.Modulator.amplitudes[a])) + '\t'+ str(RMS_value) + ' (!)\n'
        else:
            RMS_value = sum(STASIS_System.Modulator.amplitudes[a][:STASIS_System.Modulator.counter_max[a]-1])/(STASIS_System.Modulator.counter_max[a]-1)*duty_cycle/100
            status_text = status_text + ' ' + str(a+1) +',\t' +str(STASIS_System.Modulator.counter_max[a]-1) + '\t' + str(max(STASIS_System.Modulator.amplitudes[a])) + '\t'+ str(RMS_value) + '\n'
        
        
    
    STATUS_TEXT_BOX.insert('1.0',status_text)
    STATUS_TEXT_BOX.config(state=DISABLED)





###### Start Programm ######

### Load Configuration file ###
config=configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/STASIS_config.ini')

### Instance Hardware Objects ##

STASIS_System = STASIS_SystemObj(config)
amplitudes=[10]*8
phases=[45/180*np.pi]*8
amp_state=[0]*8
for a in range(8):
    amplitudes[a]=[10,10]
    phases[a]=[0,45/180*np.pi]
    amp_state[a]=[1,1]


STASIS_System.Modulator.set_amplitudes_phases_state(amplitudes,phases,amp_state)

### Start GUI ###

MAINWINDOW = start_main_GUI()
MAINWINDOW.mainloop()



