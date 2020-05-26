# f1_0.py
# -*- coding: utf-8 -*-
# @Time    : 2019/12/05
# @Author  : cccc
import pyb
from math import sqrt
#######################################################################
def lcd_write(uart, str):
    uart.write(str)
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    uart.writechar(0xFF)

def updateUI_dateTime(rtc, uart):
    datetime = rtc.datetime()
    lcd_write(uart, 'test.date.txt=\"%02d%02d%02d\"' % (datetime[0], datetime[1], datetime[2]))
    lcd_write(uart, 'test.time.txt=\"%02d:%02d:%02d\"' % (datetime[4], datetime[5], datetime[6]))

def updateUI_cpu_t(adcall, uart):
    irq_state = pyb.disable_irq() # Start of critical section
    temper = adcall.read_core_temp()
    pyb.enable_irq(irq_state) # End of critical section
    lcd_write(uart, 'debug.mcu_temp.val={:0.0f}'.format(temper*100))

def init_uart(uart):
    #初始化屏的串口
    bitrate = 115200
    uart.deinit()
    uart.init(bitrate, bits=8, parity=None, stop=1, timeout=0, read_buf_len=4096) # init with given parameters
    print('* lcd uart is: {}'.format(uart))
#######################################################################
def MyMapper(pin_name):
    if pin_name == "sensor0_en":
        return pyb.Pin.cpu.A6
    if pin_name == "sensor1_en":
        return pyb.Pin.cpu.A7
    if pin_name == "sensor0_adc":
        return pyb.Pin.cpu.C4
    if pin_name == "sensor1_adc":
        return pyb.Pin.cpu.C5
    if pin_name == "current_adc":
        return pyb.Pin.cpu.C0
    if pin_name == "vcc5_adc":
        return pyb.Pin.cpu.B0
    if pin_name == "battery_adc":
        return pyb.Pin.cpu.B1
    if pin_name == "charge_status":
        return pyb.Pin.cpu.C3
    if pin_name == "full_status":
        return pyb.Pin.cpu.C2
def chx_postprocessing(val, vref):
    val2=(val*vref)/4095
    val2=val2*3/2
    val2=0.00625*val2 - 3.125
    return round(val2,2)
def current_postprocessing(val, vref):
    val2=(val*vref)/4095
    val2=val2*10/625-26.4
    return round(val2,2)
def battery_postprocessing(val, vref):
    val2=(val*vref)/4095
    val2=val2*5/4
    return round(val2,2)
def vcc5_postprocessing(val, vref):
    val2=(val*vref)/4095
    val2=val2*3/2
    return round(val2,2)
def init_sensor_enable(en0, en1):
    en0.high()
    en1.high()
    print('* sensor0 enable: {} is {}'.format(en0, en0.value()))
    print('* sensor1 enable: {} is {}'.format(en1, en1.value()))
def init_mcu_adc(ch0, ch1, current, vcc5, battery, adcall):
    vref = round(adcall.read_vref(), 2)*1000
    print('* ch0 is {} MPa@{}'.format(chx_postprocessing(ch0.read(), vref), ch0))
    print('* ch1 is {} MPa@{}'.format(chx_postprocessing(ch1.read(), vref), ch1))
    print('* current is {} A@{}'.format(current_postprocessing(current.read(), vref), current))
    print('* vcc5 is {} mV@{}'.format(vcc5_postprocessing(vcc5.read(), vref), vcc5))
    print('* battery is {} mV@{}'.format(battery_postprocessing(battery.read(), vref), battery))
    print('* mcu core is {} V'.format(adcall.read_core_vref()))
    print('* mcu adc vref is {} V'.format(adcall.read_vref()))
    print('* mcu rtc vbat is {} V'.format(adcall.read_core_vbat()))
    print('* mcu core temperature is {} C'.format(adcall.read_core_temp()))
    print('* vcc33 is {} mV'.format(vref))
    return vref
def init_battery(charge, full):
    print('* charge pin: {} is {}'.format(charge, charge.value()))
    print('* full pin: {} is {}'.format(full, full.value()))
    #define callback
def init_rtc(rtc):
    #rtc.calibration(-10)
    print('* rtc calibration: {}'.format(rtc.calibration()))
    print('* rtc datetime: {}'.format(rtc.datetime()))
#######################################################################
def init_timer(timer, freq, cb):
    timer.deinit()
    timer.init(freq=freq)
    timer.callback(cb)
    print('* {}'.format(timer))
def updateUI_chx(value0, value1, uart, vref, debug):

    ch0_val2=chx_postprocessing(value0, vref)
    ch1_val2=chx_postprocessing(value1, vref)

    if(True != debug):
        if(0>ch0_val2):
            ch0_val2 = 0
        if(0>ch1_val2):
            ch1_val2 = 0

#    print(ch0_val2)
#    print('test.ch0.val={:0.0f}'.format(ch0_val2*100))
    lcd_write(uart, 'test.ch0.val={:0.0f}'.format(ch0_val2*100))
    #lcd_write(uart, 'test.ch0.val=rand'.format(ch0_val2*100))

#    print(ch1_val2)
#    print('test.ch1.val={:0.0f}'.format(ch1_val2*100))
    lcd_write(uart, 'test.ch1.val={:0.0f}'.format(ch1_val2*100))
######################2019.12.07########################################
def amplitude(buf):
    buflen = len(buf)
    return sqrt(sum(x**2 for x in buf)/buflen)

def updateUI_cur(adc, buf, uart, vref, timer):
    irq_state = pyb.disable_irq() # Start of critical section
    adc.read_timed(buf, timer)
    pyb.enable_irq(irq_state) # End of critical section

    for i in range(len(buf)):
        buf[i]=buf[i]*vref/4095
        buf[i]=buf[i]*10/625-26.4

#    print(buf)
#    sys.exit(0)

    result=amplitude(buf)

#    print(result)
#    sys.exit(0)
#    print(round(result,2))
    lcd_write(uart, 'debug.n0.val={:0.0f}'.format(round(result,2)*100))
#######################################################################
#######################################################################
#######################################################################
#######################################################################
#######################################################################
#######################################################################
#######################################################################
