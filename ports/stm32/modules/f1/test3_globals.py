#
# -*- coding: utf-8 -*-
import asyn
import array
import pyb
from uasyncio.synchro import Lock
from f1.test2 import *
from machine import WDT
from f1.test4_class import dev_file_display
from f1.test4_class import about_display
##############################
##########globals#############
##############################
t0_micros = 0
t0_millis = 0

check_enable_flag = True

ch0_val = 0
ch1_val = 0
current_val = 0
vcc5_val = 0
battery_val = 0
vref = 0

dev_number_event = asyn.Event()
dev_number_event_ak = asyn.Event()
dev_num = ''
start_current = 0
offset_current = 0
pcbsn = ''
rtc_ca = 0

record_event = asyn.Event()
rms_current = 0
record_flag = False
cycle_counter = 0
counter_rr = 0
cycle_lock = Lock()

full_event = asyn.Event()
charge_event = asyn.Event()
full_softint = None
#-----------------------------
error_filename = '/sd/error.log'
wdt_filename = '/sd/wdt.log'
power_filename = '/sd/power.log'
parameter_filename = '/sd/settings.json'
rec_filename = '/sd/rec.log'
##############################
##########大块数据############
##############################
data_ch0 = array.array('i', [0]*13) # Average over 10 samples
data_ch0[0] = len(data_ch0)
data_ch1 = array.array('i', [0]*13) # Average over 10 samples
data_ch1[0] = len(data_ch1)
data_cur = array.array('i', [0]*13) # Average over 10 samples
data_cur[0] = len(data_cur)
data_cur2 = array.array('f', [0]*50) # Average over 50 samples浮点数
data_vcc5 = array.array('i', [0]*13) # Average over 100 samples
data_vcc5[0] = len(data_vcc5)
data_battery = array.array('i', [0]*103) # Average over 100 samples
data_battery[0] = len(data_battery)
data_set = None
uart_bytes = bytearray(100)
##############################
###########硬件相关############
##############################
lcd_en = pyb.Pin('X18', pyb.Pin.OUT_PP) #LCD供电使能
lcd_en.low()
pyb.Pin.mapper(MyMapper)
ch0 = pyb.ADC(pyb.Pin('sensor0_adc'))
ch1 = pyb.ADC(pyb.Pin('sensor1_adc'))
current = pyb.ADC(pyb.Pin('current_adc'))
vcc5 = pyb.ADC(pyb.Pin('vcc5_adc'))
battery = pyb.ADC(pyb.Pin('battery_adc'))
uart = pyb.UART(2) #使用串口2连接串口屏
rtc = pyb.RTC()    #实时时间
adcall = pyb.ADCAll(12, 0x70000) # 12 bit resolution, internal channels
en0 = pyb.Pin('sensor0_en', pyb.Pin.OUT)
en1 = pyb.Pin('sensor1_en', pyb.Pin.OUT)
charge = pyb.Pin('charge_status', pyb.Pin.IN, pull=pyb.Pin.PULL_UP)  #40K PULL_UP
full = pyb.Pin('full_status', pyb.Pin.IN, pull=pyb.Pin.PULL_UP)    #40K PULL_UP
tim1 = pyb.Timer(1)
tim2 = pyb.Timer(2)
tim3 = pyb.Timer(3)
tim4 = pyb.Timer(4)
tim5 = pyb.Timer(5)
tim7 = pyb.Timer(7)
tim8 = pyb.Timer(8)
tim9 = pyb.Timer(9)
tim14 = pyb.Timer(14)
usb = pyb.USB_VCP()
sd = pyb.SDCard()
lcd_tjc = dev_file_display(uart) # 例化类
lcd_about = about_display(uart) # 例化类
#---------------------------------
# usb.setinterrupt(-1)
wdt = WDT(timeout=1000*32)  #1~32s之内的值可以取到
# wdt = None
