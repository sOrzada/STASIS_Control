import numpy as np
from time import sleep
from tkinter import *
from tkinter import scrolledtext
import re
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import STASIS_Control

#Test Program

CB = STASIS_Control.ControlByteObj
data_reset=bytes([CB.reset,0,0,0])
data = bytes([CB.clock,0,0,0]) + bytes([0,0,0,0])
STASIS_Control.STASIS_System.SPI.send_bitstream(data_reset)
for a in range(1000):
    STASIS_Control.STASIS_System.SPI.send_bitstream(data)
    sleep(0.01)


