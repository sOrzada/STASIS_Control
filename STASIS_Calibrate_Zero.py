from tkinter import *
import STASIS_Control
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from PIL import Image, ImageTk
class CalibrateZeroObj:
    def __init__(self) -> None:
        self.number_of_channels = STASIS_Control.STASIS_System.Modulator.number_of_channels
        self.active_channel = 1
        self.IQoffset = STASIS_Control.STASIS_System.Modulator.IQoffset
        self.Window_calibrate_zero = Tk()
        self.ph=Image.open(os.path.dirname(__file__) + '\Images\Zero_Point_Cal.png')
        self.ph=self.ph.resize((450,300), resample=1)
        self.ph=ImageTk.PhotoImage(self.ph)
        
    
    def openGUI(self):
        
        self.Window_calibrate_zero.title('Zero Point Calibration of Modulators')
        self.Window_calibrate_zero.config(width=1200, height=550)
        self.Window_calibrate_zero.protocol('WM_DELETE_WINDOW', lambda: self.saveClose())
        self.controlButtonsInit(x_center=150, y_center=250) #Initialize control buttons
        self.channelSelectInit(x_center=150,y_center=100) #Initialize Listbox for channel selection
        
        self.figureOffset = Figure(figsize=(5,5), dpi=80)
        self.plotFigureOffset = self.figureOffset.add_subplot(111)
        self.canvasFigureOffset = FigureCanvasTkAgg(self.figureOffset, master=self.Window_calibrate_zero)
        self.canvasFigureOffset.get_tk_widget().place(x=500, y=250, anchor='center')
        self.plotFigure()
        
        #im=Image.open(os.path.dirname(__file__) + '\Images\Zero_Point_Cal.jpg')
        
        self.label_image = Label(self.Window_calibrate_zero)
        self.label_image.config(image=self.ph)
        self.label_image.place(x=950,y=250, anchor='center')
        #self.label_image.pack()
        


        self.ButtonSaveClose = Button(self.Window_calibrate_zero, width=10, height=2, text='Save & Close', command=self.saveClose)
        self.ButtonSaveClose.place(x=150, y=400, anchor='center')

    def mainloop(self):
        self.Window_calibrate_zero.mainloop()

    def changeIQ(self,I_change,Q_change):
        self.IQoffset[self.active_channel-1][0] = self.IQoffset[self.active_channel-1][0] + I_change
        self.IQoffset[self.active_channel-1][1] = self.IQoffset[self.active_channel-1][1] + Q_change
        
        self.plotFigure()

    def saveClose(self):
        
        
        STASIS_Control.STASIS_System.Modulator.number_of_channels = self.IQoffset
        STASIS_Control.STASIS_System.Modulator.write_IQ_offset()
        self.Window_calibrate_zero.destroy()
        pass

    def controlButtonsInit(self,x_center,y_center): #Initialize Control Panel for I/Q correction
        self.frame_buttons = Frame(self.Window_calibrate_zero, width=180, height=180, borderwidth=3, relief='ridge')
        self.frame_buttons.place(x=x_center,y=y_center, anchor='center')
        self.Button_up1 = Button(self.Window_calibrate_zero, width=3, height=1, text='+1', command=lambda: self.changeIQ(1,0))
        self.Button_up10 = Button(self.Window_calibrate_zero, width=3, height=1, text='+10', command=lambda: self.changeIQ(10,0))
        self.Button_down1 = Button(self.Window_calibrate_zero, width=3, height=1, text='-1', command=lambda: self.changeIQ(-1,0))
        self.Button_down10 = Button(self.Window_calibrate_zero, width=3, height=1, text='-10', command=lambda: self.changeIQ(-10,0))
        self.Button_up1.place(x=x_center, y=y_center-30, anchor='center')
        self.Button_up10.place(x=x_center, y=y_center-60, anchor='center')
        self.Button_down1.place(x=x_center, y=y_center+30, anchor='center')
        self.Button_down10.place(x=x_center, y=y_center+60, anchor='center')

        self.Button_right1 = Button(self.Window_calibrate_zero, width=3, height=1, text='+1', command=lambda: self.changeIQ(0,1))
        self.Button_right10 = Button(self.Window_calibrate_zero, width=3, height=1, text='+10', command=lambda: self.changeIQ(0,10))
        self.Button_left1 = Button(self.Window_calibrate_zero, width=3, height=1, text='-1', command=lambda: self.changeIQ(0,-1))
        self.Button_left10 = Button(self.Window_calibrate_zero, width=3, height=1, text='-10', command=lambda: self.changeIQ(0,-10))
        self.Button_right1.place(x=x_center+30, y=y_center, anchor='center')
        self.Button_right10.place(x=x_center+65, y=y_center, anchor='center')
        self.Button_left1.place(x=x_center-30, y=y_center, anchor='center')
        self.Button_left10.place(x=x_center-65, y=y_center, anchor='center')
    
    def channelSelectInit(self, x_center, y_center): #Initialize Buttons and Label for Channel selection
        Button_prev = Button(self.Window_calibrate_zero, width=3,height=1, text='<', command=lambda: self.channelselect(-1))
        Button_next = Button(self.Window_calibrate_zero, width=3,height=1, text='>', command=lambda: self.channelselect(+1))
        self.label_channel = Label(self.Window_calibrate_zero, height=1, width=6, text='Ch ' + str(self.active_channel), relief='sunken', bg='white')
        Button_prev.place(x=x_center-50,y=y_center,anchor='center')
        self.label_channel.place(x=x_center,y=y_center, anchor='center')
        Button_next.place(x=x_center+50,y=y_center, anchor='center')
    
    def channelselect(self,a): #Select channel with buttons and stay within actual channel count
        self.active_channel = self.active_channel + a
        if self.active_channel<1:
            self.active_channel=1
        elif self.active_channel>self.number_of_channels:
            self.active_channel=self.number_of_channels
        self.label_channel.config(text='Ch ' + str(self.active_channel))
        self.plotFigure()

    def plotFigure(self):
        a=self.active_channel
        self.plotFigureOffset.clear()
        self.plotFigureOffset.scatter(0,0, marker='o')
        self.plotFigureOffset.scatter(self.IQoffset[a-1][1],self.IQoffset[a-1][0], marker='x')
        self.plotFigureOffset.axis([-128,128,-128,128])
        self.plotFigureOffset.set_xlabel('I')
        self.plotFigureOffset.set_ylabel('Q')
        self.plotFigureOffset.set_title('Channel ' + str(self.active_channel))
        
        self.canvasFigureOffset.draw()
        

CalGUI = CalibrateZeroObj()
CalGUI.openGUI()
CalGUI.mainloop()