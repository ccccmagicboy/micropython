#
# -*- coding: utf-8 -*-
# @Time    : 2019/12/05
# @Author  : cccc
import pyb
from math import sqrt
from nvic import *
import uos
import gc
import micropython
#######################################################################
def lcd_write(uart, str):
    irq_state = pyb.disable_irq() # Start of critical section
    uart.write(str)
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    pyb.enable_irq(irq_state) # End of critical section
def updateUI_dateTime(rtc, uart):
    datetime = rtc.datetime()
    lcd_write(uart, 'test.date.txt=\"%02d%02d%02d\"' % (datetime[0], datetime[1], datetime[2]))
    lcd_write(uart, 'test.time.txt=\"%02d:%02d:%02d\"' % (datetime[4], datetime[5], datetime[6]))
def updateUI_cpu_t(adcall, uart):
    irq_state = pyb.disable_irq() # Start of critical section
    temper = adcall.read_core_temp()
    pyb.enable_irq(irq_state) # End of critical section
    lcd_write(uart, 'debug.mcu_temp.val={:0.0f}'.format(temper*100))
def init_uart(uart, bitrate=115200):
    uart.deinit()
    uart.init(bitrate, bits=8, parity=None, stop=1, timeout=0, read_buf_len=512) # init with given parameters
    uart.read() #clear rxbuf
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
    pyb.delay(300) #wait for sensor output first voltage
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
def init_rtc(rtc, wakeup_time, cb, cali):
    rtc.wakeup(wakeup_time, cb)
    rtc.calibration(cali)
    print('* rtc calibration: {}'.format(rtc.calibration()))
    print('* rtc datetime: {}'.format(rtc.datetime()))
#######################################################################
def init_timer(timer, freq, cb):
    timer.deinit()
    timer.init(freq=freq)
    timer.callback(cb)
    print('* {}'.format(timer))
    print('\n')
    dump_nvic()
    print('\n')
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
######################2019.12.12#################################################
def df(rootdir):
  s = uos.statvfs(rootdir)
  return ('{0} MB'.format((s[0]*s[3])/1048576))
def check_disk(rootdir):
    # print('here!!!')
    vfs_sd = uos.statvfs(rootdir)
    # print(vfs_sd)
    free_percent = round((vfs_sd[3]/vfs_sd[2])*100, 2)
    # print(rootdir + ': '+free_percent+'% is used!!')
    return free_percent
def lcd_display_error(uart):
    lcd_write(uart, 'page code_bug')
def updateUI_batt(raw, uart, vref):
    result = battery_postprocessing(raw, vref)
#    print(raw)
#    print(vref)
#    print(result)
    lcd_write(uart, 'debug.bv.val={:0.0f}'.format(result*100))
def updateUI_mcu_po(raw, uart, vref):
    result = vcc5_postprocessing(raw, vref)
#    print(raw)
#    print(vref)
#    print(result)
    lcd_write(uart, 'debug.mcu_power.val={:0.0f}'.format(result*100))
def updateUI_dev_num(num, uart):
    lcd_write(uart, 'test.devNum.val=' + num)
def init_gc():
    gc.enable()
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
    gc.collect()
    print('* mem free {}'.format(gc.mem_free()))
    print('* mem alloc {}'.format(gc.mem_alloc()))
def init_usb(usb):
    if(usb.isconnected()):
        print('* {} is connected'.format(usb))
        return True
    else:
        return False
def init_WDT(wdt_l):
    print('* WDT: {}'.format(wdt_l))

def updateUI_cur2(adc, buf, uart, vref, timer, offset):
    irq_state = pyb.disable_irq() # Start of critical section
    adc.read_timed(buf, timer)
    pyb.enable_irq(irq_state) # End of critical section

    #print(offset)

    for i in range(len(buf)):
        buf[i]=buf[i]*vref/4095
        buf[i]=buf[i]*10/625-26.4

#    print(buf)
#    sys.exit(0)

    result=amplitude(buf) + offset
    
    if result < 0:
        result = 0

#    print(result)
#    sys.exit(0)
#    print(round(result,2))
    lcd_write(uart, 'debug.n0.val={:0.0f}'.format(round(result,2)*100))
    return round(result,2)
def init_extint(cb1, cb2):
    extint1 = pyb.ExtInt('charge_status', pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_UP, cb1)
    print('* extint1: {}'.format(extint1))
    extint2 = pyb.ExtInt('full_status', pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_UP, cb2)
    print('* extint2: {}'.format(extint2))
    print('\n')
    dump_nvic()
    print('\n')
    extint1.swint()
    extint2.swint()
    return extint2
def init_sd(sdcard):
    if (True == sdcard.present()):
        try:
            print('* try to mount /sd/')
            uos.mount(sdcard, '/sd')
        except:
            print('* already mount /sd/')
        print('* sd have {}'.format(check_disk('/sd/'))+'% free space ')
        print('* flash have {}'.format(check_disk('/flash/'))+'% free space')
        print('* sd size is '+df('/sd/'))
        print('* flash size is '+df('/flash/'))
def update_set_time_page(rtc_l, uart_l):
    dt = rtc_l.datetime()
    lcd_write(uart_l, 'set_time.year.val=' + str(dt[0]))
    lcd_write(uart_l, 'set_time.mon.val=' + str(dt[1]))
    lcd_write(uart_l, 'set_time.day.val=' + str(dt[2]))
    lcd_write(uart_l, 'set_time.hour.val=' + str(dt[4]))
    lcd_write(uart_l, 'set_time.min.val=' + str(dt[5]))
    lcd_write(uart_l, 'set_time.sec.val=' + str(dt[6]))
    lcd_write(uart_l, 'page set_time')
###############################2019.12.13##############################
def updateUI_disk_perc(uart):
    #print("disk {}% is used".format(100-check_disk('/sd/')))
    lcd_write(uart, 'set.sd.val={:0.0f}'.format(10*(100-check_disk('/sd/'))))
    free_space_perc = check_disk('/sd/')
    return free_space_perc

def del_useless_files():
    if('YEYA.tft' in uos.listdir('/sd/')):
        uos.remove('/sd/YEYA.tft')
        print('* find YEYA.tft, and had deleted it!!!')

def updateUI_cycle(uart, count):
    lcd_write(uart, 'test.n0.val={}'.format(count))

def update_debug_page(uart_l):
    command = 'debug.console.txt="touch above to probe!"'
    #print(command)
    lcd_write(uart_l, command)
    lcd_write(uart_l, 'page debug')

def update_recall_page(uart_l):
    lcd_write(uart_l, 'page recall')

def init_mcu(freq):
    pyb.freq(freq)
    #pyb.freq(168000000)
    #pyb.freq(30*1000000)
    print('* CPU: {0}|AHB: {1}|APB1: {2}|APB2: {3}'.format(pyb.freq()[0], pyb.freq()[1], pyb.freq()[2], pyb.freq()[3]))
#############################2019.12.17##################################
def init_data():
    if not 'data' in uos.listdir('/sd/'):
        print('no /sd/data folder find!!!')
        uos.mkdir('/sd/data')
    print('* data folder is {}'.format('data' in uos.listdir('/sd/')))
def init_mem():
    micropython.mem_info()
def check_fw():
    help('modules')
def enable_lcd(en, pinn):
    if en:
        pinn.high()#open lcd
    else:
        pinn.low()#close lcd
###########################2019.12.20#####################################
def check_file_size2(filename, dev):
    if(filename in uos.listdir('/sd/data/'+dev)):
        size = uos.stat('/sd/data/'+dev+'/'+filename)[6]
    else:
        size = 0
    return size
#######################################################################
#######################################################################
#######################################################################
