# main_new2.py
# -*- coding: utf-8 -*-
# @Time    : 2019/12/05
# @Author  : cccc
# @File    : main_new2.py
from avg import avg
import time, uos, ujson, pyb
import array
import uasyncio as asyncio
from f1.test2 import *
from math import sqrt
import sys
import gc
from uio import StringIO
import utime
#import _thread
from machine import WDT
import asyn
import ubinascii
import os
import struct
from nvic import *
from uasyncio.synchro import Lock
import micropython
from f1.test3_globals import *
from f1.version import *
##############################
#############ISR##############
##############################
#
def pin_cb1(line):
    global charge_event
    charge_event.set()
    print("@@@ charge trigger @line=", line)
#
def pin_cb2(line):
    global full_event
    full_event.set()
    print("@@@ full trigger @line=", line)
#
def cb1(timer):
    global ch0_val
    global ch0
    global data_ch0
    irq_state = pyb.disable_irq() # Start of critical section
    ch0_val = avg(data_ch0, ch0.read())
    pyb.enable_irq(irq_state) # End of critical section
#
def cb2(timer):
    global ch1_val
    global ch1
    global data_ch1
    irq_state = pyb.disable_irq() # Start of critical section
    ch1_val = avg(data_ch1, ch1.read())
    pyb.enable_irq(irq_state) # End of critical section
#
def cb3(timer):
    global current_val
    global current
    global data_cur
    irq_state = pyb.disable_irq() # Start of critical section
    current_val = avg(data_cur, current.read())
    pyb.enable_irq(irq_state) # End of critical section
#
def cb4(timer):
    global vcc5_val
    global vcc5
    global data_vcc5
    irq_state = pyb.disable_irq() # Start of critical section
    vcc5_val = avg(data_vcc5, vcc5.read())
    pyb.enable_irq(irq_state) # End of critical section
#
def cb5(timer):
    global battery_val
    global battery
    global data_battery
    irq_state = pyb.disable_irq() # Start of critical section
    battery_val = avg(data_battery, battery.read())
    pyb.enable_irq(irq_state) # End of critical section
#
def cb_rec_event(timer):
    global record_event
    record_event.set()
#
def cb_wdt(timer):
    global wdt
    wdt.feed()
##############################
############库函数############
##############################
def init_from_settings():
    global data_set

    if not ('settings.json' in uos.listdir('/sd/')):
        print('* no settings.json find, and will init one here!!!')
        data_set = {'general': {'hw_ver': 'v1.1', 'lcd_sn': '0', 'sw_ver': 'v1.1', 'pcb_sn': '0', 'fw_ver': '0', 'rtc_cali': -20}, 'dev': {'type': 0, 'num': '000', 'current_offset': -0.07, 'ch0': {'K': 1, 'B': 0}, 'ch1': {'K': 1, 'B': 0}, 'start_current': 0.7}, 'firstrun': True, 'url': 'www.ccrobot-online.com.cn'}

        with open(parameter_filename, 'w', encoding='utf-8') as f_set:
            f_set.seek(0)
            f_set.write(ujson.dumps(data_set))
            f_set.flush()
        os.sync()

    if('settings.json' in uos.listdir('/sd/')):
        print('* settings.json find!!!')
        with open(parameter_filename, 'r', encoding='utf-8') as f_set:
            data_set = ujson.load(f_set)

        if (True == data_set['firstrun']):
            string = ubinascii.hexlify(machine.unique_id())
            data_set['general']['pcb_sn'] = string
            data_set['firstrun'] = False
            data_set['general']['fw_ver'] = str(firmware_ver)
            with open(parameter_filename, 'w', encoding='utf-8') as f_set:
                f_set.seek(0)
                f_set.write(ujson.dumps(data_set))
                f_set.flush()
            os.sync()

        #print(ujson.dumps(data_set))
        dnum = data_set['dev']['num']
        start_cur = data_set['dev']['start_current']
        offset_cur = data_set['dev']['current_offset']
        pcbsnn = data_set['general']['pcb_sn']
        rtc_cal = data_set['general']['rtc_cali']
    return dnum, start_cur, offset_cur, pcbsnn, rtc_cal
def init_lcd(dev):
    global lcd_tjc
    global lcd_about
    lcd_tjc.init(dev)
    lcd_about.init()
##############################
#############协程#############
##############################
#
async def space_check_up_(threadName, delay_first, delay):
    global check_enable_flag
    global uart
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD disk used percent update!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        if (True==check_enable_flag):
            free = updateUI_disk_perc(uart)
            if (10 > free):
                print('disk almost full!!!')
        await asyncio.sleep_ms(delay)
#-----------------------------
#
async def date_up_(threadName, delay_first, delay):
    global rtc
    global uart
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD date update!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        updateUI_dateTime(rtc, uart)
        await asyncio.sleep_ms(delay)
#-----------------------------
#
async def cpu_temp_up_(threadName, delay_first, delay):
    global uart
    global adcall
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD CPU Temperature update!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        updateUI_cpu_t(adcall, uart)
        #print('ok')
        await asyncio.sleep_ms(delay)
#-----------------------------
#
async def chx_up_(threadName, delay_first, delay):
    global uart
    global ch0_val
    global ch1_val
    global vref
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD ch0/ch1 pressure update!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        updateUI_chx(ch0_val, ch1_val, uart, vref, False)# if True debug is ON!!!
        #print('ok')
        await asyncio.sleep_ms(delay)
#-----------------------------
#
async def current_rms_up_(threadName, delay_first, delay):
    global current
    global uart
    global vref
    global data_cur2
    global tim7
    global rms_current
    global record_flag
    global offset_current

    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD current RMS update!!!#{}ms@{}ms'.format(threadName, delay_first, delay))

    first_cycle = 0
    second_cycle = 0
    third_cycle = 0
    uni_cycle = 0
    counter = 0

    while True:
        rms_current = updateUI_cur2(adc=current, buf=data_cur2, uart=uart, vref=3300, timer=tim7, offset=offset_current)
#        print(1/0)
#
        #do some thing here
        #counter+=1
        #if(1 == counter%3):
        #    first_cycle = rms_current
        #if(2 == counter%3):
        #    second_cycle = rms_current
        #if(0 == counter%3):
        #    third_cycle = rms_current

        # if(first_cycle>start_current and second_cycle>start_current and third_cycle>start_current):
            # record_flag = True
        # if(first_cycle<start_current and second_cycle<start_current and third_cycle<start_current):
            # record_flag = False

        uni_cycle = rms_current
        if(uni_cycle>start_current):
            record_flag = True
        else:
            record_flag = False

        await asyncio.sleep_ms(delay)
#-----------------------------
#
async def battery_up_(threadName, delay_first, delay):
    global battery_val
    global uart
    global vref
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD 1 x 18650 voltage update!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        updateUI_batt(raw=battery_val, uart=uart, vref=3300)
#       print(1/0)
        await asyncio.sleep_ms(delay)
#-----------------------------
#
async def mcu_power_up_(threadName, delay_first, delay):
    global vcc5_val
    global uart
    global vref
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD CPU POWER voltage update!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        updateUI_mcu_po(raw=vcc5_val, uart=uart, vref=vref)
#        print(1/0)
        await asyncio.sleep_ms(delay)
#-----------------------------
#
async def gclean_(threadName, delay_first, delay):
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for micropython gc!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        gc.collect()
#       print(1/0)
        print('* mem free {}'.format(gc.mem_free()))
        print('* mem alloc {}'.format(gc.mem_alloc()))
        await asyncio.sleep_ms(delay)
#-----------------------------
#

async def lcd_receiver_(threadName, delay_first, lock):
    global uart
    global tim8
    global full_softint
    global vcc5_val
    global dev_num
    global dev_number_event
    global dev_number_event_ak
    global rtc
    global check_enable_flag
    global start_current
    global offset_current
    global cycle_counter
    global counter_rr
    global battery_val
    global lcd_en
    global lcd_tjc
    global lcd_about

    uart.read() #clear first
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for lcd uart receive!!!#{}ms'.format(threadName, delay_first))

    while True:
        await asyncio.sleep_ms(50)
        if(uart.any()):
            if(b'\xea'==uart.read(1)):
                await asyncio.sleep_ms(10)#about 20bytes for 115200 transfer
                uart.readinto(uart_bytes, 8)
                check0 = uart_bytes[0]
                check1 = uart_bytes[1]
                check5 = uart_bytes[5]
                check6 = uart_bytes[6]
                check7 = uart_bytes[7]
                print(check0, check1, check5, check6, check7)
                if(0xFF == check5 == check6 == check7):
                    if(0x10 == check0):#test page display
                        if (4000 > vcc5_val):
                            full_softint.swint()
                    if(0x11 == check0):#start record
                        init_timer(tim5, 10, cb=cb_rec_event)
                        #   vis n0,1
                        #   vis record,1
                        #   tm1.en=1
                        #   vis btnSet,0
                        #lcd_write(uart,'test.n0.val=0')
                        lcd_write(uart,'vis n0,1')
                        lcd_write(uart,'vis record,1')
                        lcd_write(uart,'tm1.en=1')
                        lcd_write(uart,'vis b2,0')
                        lcd_write(uart,'vis b3,1')
                        lcd_write(uart,'vis btnSet,0')
                        check_enable_flag = False
                    if(0x13 == check0):#end record
                        init_timer(tim5, 10, cb=None)
                        #   vis n0,0
                        #   vis record,0
                        #   tm1.en=0
                        #   vis btnSet,1
                        #
                        lcd_write(uart,'vis n0,0')
                        lcd_write(uart,'vis record,0')
                        lcd_write(uart,'tm1.en=0')
                        lcd_write(uart,'vis b2,1')
                        lcd_write(uart,'vis b3,0')
                        lcd_write(uart,'vis btnSet,1')
                        check_enable_flag = True
                        await lock.acquire()
                        print("Acquired {} in coro lcd_receiver_".format(lock))
                        cycle_counter = 0
                        counter_rr = 0
                        updateUI_cycle(uart, cycle_counter)
                        print(cycle_counter)
                        lock.release()
                    if(0x22 == check0):#update device number
                        #print('bingo!')
                        rr = struct.unpack('<HH', uart_bytes[1:5])
                        #print(rr)
                        dev_num = str(rr[0])
                        dev_number_event.set()
                        #check for ak event
                        await dev_number_event_ak
                        dev_number_event_ak.clear()
                        lcd_write(uart, 'page set')
                    if(0x23 == check0):#update set time page init value
                        update_set_time_page(rtc_l=rtc, uart_l=uart)
                    if(0x24 == check0):#get y:m:d
                        rr1 = struct.unpack('<HBB', uart_bytes[1:5])
                    if(0x25 == check0):#get h:m:s
                        rr2 = struct.unpack('<BBBB', uart_bytes[1:5])
                        print(rr1+(1,)+rr2)#1是weekday is 1-7 for Monday through Sunday. rr2的最后一个B为subseconds counts down from 255 to 0
                        rtc.datetime(rr1+(1,)+rr2)
                        lcd_write(uart, 'page set')
                    if(0x50 == check0):
                        #update_recall_page(uart_l=uart)
                        if(0x00 == check1):
                            init_lcd('T'+dev_num)
                            lcd_tjc.goto_recall_page()
                        elif(0x01 == check1):
                            lcd_tjc.file_up()
                        elif(0x02 == check1):
                            lcd_tjc.file_down()
                        elif(0x0F == check1):
                            lcd_tjc.goto_recall_page()
                        elif(0x10 == check1):
                            lcd_tjc.max_play()
                        elif(0x11 == check1):
                            lcd_tjc.min_play()
                        else:
                            lcd_tjc.run_command(check1)
                    if(0x51 == check0):
                        update_debug_page(uart_l=uart)
                    if(0x52 == check0):
                        if('error.log' in uos.listdir('/sd/')):
                            #print(uos.stat('/sd/error.log'))
                            size = uos.stat('/sd/error.log')[6]/1000
                            command = 'debug.console.txt="error.log is {:.1f}KB"'.format(size)
                            print(command)
                            lcd_write(uart, command)
                    if(0x53 == check0):
                        if('error.log' in uos.listdir('/sd/')):
                            try:
                                uos.remove('/sd/error.log')
                            except:
                                command('error.log delete error!!!')
                            command = 'debug.console.txt="error.log is deleted."'
                            print(command)
                            lcd_write(uart, command)
                    if(0x54 == check0):
                        if('wdt.log' in uos.listdir('/sd/')):
                            #print(uos.stat('/sd/wdt.log'))
                            size = uos.stat('/sd/wdt.log')[6]/1000
                            command = 'debug.console.txt="wdt.log is {:.1f}KB"'.format(size)
                            print(command)
                            lcd_write(uart, command)
                    if(0x55 == check0):
                        if('wdt.log' in uos.listdir('/sd/')):
                            try:
                                uos.remove('/sd/wdt.log')
                            except:
                                command('wdt.log delete error!!!')
                            command = 'debug.console.txt="wdt.log is deleted."'
                            print(command)
                            lcd_write(uart, command)
                    if(0x56 == check0):
                        command = 'debug.console.txt="disk is {:.2f}% free"'.format(check_disk('/sd/'))
                        print(command)
                        lcd_write(uart, command)
                    if(0x57 == check0):
                        command = 'debug.console.txt="C0 is {:.2f}A"'.format(start_current)
                        print(command)
                        lcd_write(uart, command)
                    if(0x58 == check0):
                        command = 'debug.console.txt="Offset is {:.2f}A"'.format(offset_current)
                        print(command)
                        lcd_write(uart, command)
                    if(0x59 == check0):#about page
                        lcd_about.goto_about_page()
                    if(0x5A == check0):#low power
                        enable_lcd(False, lcd_en)
                        #write power.log
                        with open(power_filename, 'a', encoding='utf-8') as pp_fi:
                            pp_fi.write('almost ran out of battery@{}@{:.2f}\n'.format(utime.time()+946684800, battery_postprocessing(battery_val, 3300)))
                        pyb.freq(30*1000000)
                    ###
#
async def feed_dog_(threadName, delay_first, delay):
    global wdt_filename
    global battery_val
    
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for watchdog event record!!!#{}ms@{}ms'.format(threadName, delay_first, delay))
    while True:
        wdt.feed()
#       print(1/0)
#       ###
        #size = uos.stat(wdt_filename)[6]/1024
        #print('wdt log file size is {:.2f}KB'.format(size))
        #save last wdt feed tick here!!!
        with open(wdt_filename, 'a', encoding='utf-8') as fi:
            str_temp = '{}@{:.2f}\n'.format(utime.time()+946684800, battery_postprocessing(battery_val, 3300))
            fi.write(str_temp)
        ###
        await asyncio.sleep_ms(delay)
#
async def update_dev_(threadName, delay_first, event, event_ak):
    global uart
    global dev_num
    global parameter_filename
    global data_set
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for LCD dev number update!!!#{}ms@{}'.format(threadName, delay_first, event))
    while True:
        await event
        # print('got event')
        #do some uart
        updateUI_dev_num(uart=uart, num=dev_num)
        #save to config
        data_set['dev']['num'] = dev_num
        with open(parameter_filename, 'w', encoding='utf-8') as f_set:
            f_set.seek(0)
            f_set.write(ujson.dumps(data_set))
            f_set.flush()
        os.sync()
        #make a dir under /sd/data/
        dir = '/sd/data/T' + dev_num

        selec = 'T'+dev_num
        if( selec in uos.listdir('/sd/data')):
            print('$$$ dir is already there!!!')
        else:
            uos.mkdir(dir)
            uos.sync()
            print('$$$ make a dir@{}'.format(dir))

        #print(uos.stat(dir))
        print('$$$ {}'.format(uos.listdir('/sd/data')))
        event.clear()
        event_ak.set()
#
async def dev_num_first_(threadName, delay_first, event):
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for first device number update!!!#{}ms@{}'.format(threadName, delay_first, event))
    event.set()
    # print('event was set')
#
async def rec_(threadName, delay_first, event, lock):
    global rms_current
    global record_flag
    global ch0_val
    global ch1_val
    global vref
    global cycle_counter
    global uart
    global dev_num
    global counter_rr
    global start_current
    global pcbsn

    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for save the record!!!#{}ms@-{}'.format(threadName, delay_first, event))

    counter_rr = 0

    while True:
        await event
        ###
        if (True == record_flag):
            await lock.acquire()
            counter_rr+=1
            lock.release()

            if(1==counter_rr):
                t1 = pyb.millis()
                await lock.acquire()
                print("Acquired {} in coro rec_".format(lock))
                cycle_counter+=1
                updateUI_cycle(uart, cycle_counter)
                print(cycle_counter)
                lock.release()
                #make a file
                filename = '/sd/data/T{}/'.format(dev_num)+'{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}_{}.csv'.format(utime.localtime()[0], utime.localtime()[1], utime.localtime()[2], utime.localtime()[3], utime.localtime()[4], utime.localtime()[5], cycle_counter)
                print(filename)
                with open (rec_filename, 'a', encoding='utf-8') as fff:
                    fff.write('{} is recording...\n'.format(filename))
                with open(filename, 'a', encoding='utf-8') as fff:
                    fff.write('道岔编号：'+dev_num+'\t集采设备：{}\n'.format(pcbsn.upper()))
                    fff.write('文件名：'+filename+'\n')
                    fff.write('启动电流（A安培）：{:.2f}A\n'.format(start_current))
                    fff.write('序号, 时刻（毫秒ms）, 电流（安培A）, 通道1（L红色）压力（兆帕MPa）, 通道2（R绿色）压力（兆帕MPa）\n')
            ch0_val2=chx_postprocessing(ch0_val, vref)
            ch1_val2=chx_postprocessing(ch1_val, vref)
            if(0>ch0_val2):
                ch0_val2 = 0
            if(0>ch1_val2):
                ch1_val2 = 0
            tick = pyb.elapsed_millis(t1)
            txt_str = '{},{},{:.2f},{:.2f},{:.2f}\n'.format(counter_rr, tick, rms_current, ch0_val2, ch1_val2)
            #print(txt_str)
            with open(filename, 'a', encoding='utf-8') as fff:
                fff.write(txt_str)
        else:
            counter_rr = 0

        event.clear()
    #
async def charge_(threadName, delay_first, event):
    global charge
    global uart
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for charge pin status monitor!!!#{}ms@{}'.format(threadName, delay_first, event))
    while True:
        await event
        #do some thing here
        #lcd_write(uart, 'page test')
        if  (0  ==  charge.value()):
            print('$$$ charging...@{}'.format(threadName))
        else:
            print('$$$ uncharged!!!@{}'.format(threadName))
        ###
        event.clear()
#
async def full_(threadName, delay_first, event):
    global full
    global uart
    global battery_val
    await asyncio.sleep_ms(delay_first)
    print('$$$ {} is for full pin status monitor!!!#{}ms@{}'.format(threadName, delay_first, event))
    while True:
        await event
        #do some thing here
        if  (0  ==  full.value()):
            #write power.log
            with open(power_filename, 'a', encoding='utf-8') as pp_fi:
                pp_fi.write('battery is full@{}@{:.2f}\n'.format(utime.time()+946684800, battery_postprocessing(battery_val, 3300)))
            #lcd_write(uart, 'page battery_full')
            lcd_write(uart, 'vis t6,1')
            print('$$$ already full!!!@{}'.format(threadName))
        else:
            print('$$$ unfull happened!!!@{}'.format(threadName))
        ###
        event.clear()
##############################

def initial():
    global t0_micros
    global t0_millis
    global uart
    global en0
    global en1
    global ch0
    global ch1
    global current
    global vcc5
    global battery
    global adcall
    global charge
    global full
    global rtc
    global tim1
    global tim2
    global tim3
    global tim4
    global tim5
    global tim7
    global tim8
    global tim9
    global tim14
    global vref
    global usb
    global dev_num
    global sd
    global full_softint
    global wdt
    global start_current
    global offset_current
    global pcbsn
    global rtc_ca

    print("Now init for pyb_f1 board\n")
    t0_micros = pyb.micros()
    t0_millis = pyb.millis()
    #init from settings
    dev_num, start_current, offset_current, pcbsn, rtc_ca = init_from_settings()    
    check_fw()
    #init_sd first
    init_sd(sd)
    #init mcu
    init_mcu(168000000)
    #init WDT
    init_WDT(wdt_l=wdt)
    #init rtc
    init_rtc(rtc, wakeup_time=10000, cb=None, cali=rtc_ca)#cali = -511~+512, 负值变慢，正值变快  0值快
    #init for lcd uart
    init_uart(uart, 115200)
    #init sensor pins
    init_sensor_enable(en0, en1)
    #init mcu adc
    vref = init_mcu_adc(ch0, ch1, current, vcc5, battery, adcall)
    #init battery
    init_battery(charge, full)
    #init 外部中断
    full_softint = init_extint(pin_cb1, pin_cb2)
    #init usb
    init_usb(usb)
    #init timer
    #默认优先级根据：micropython/stmhal/irq.h
    print('\n')
    dump_nvic()
    print('\n')
    init_timer(tim1, 1000, cb1)      #  14            avg for ch0
    init_timer(tim2, 1000, cb2)      #  14            avg for ch1
    init_timer(tim3, 1000, cb3)      #  14            avg for dc current
    init_timer(tim4, 10, cb4)        #  14            avg for vcc5
    init_timer(tim8, 800, cb5)       #  14            avg for battery
    init_timer(tim7, 5000, None)     #  14            calc for rms current
    init_timer(tim5, 10, None)       #  6             ticks for record
    #init_timer(tim9, 2, cb_wdt)     #  14            ticks for feed dog
    #init_timer(tim14, 1, cb1)       #  14            last timer
#-----------------------------
    
    print('* current device number is {}'.format(dev_num))
    print('* start_current is {}'.format(start_current))
    print('* offset_current is {}'.format(offset_current))

    #delete *.tft@root
    del_useless_files()
    #init data folder
    init_data()
    #init gc
    init_gc()
    #check memory
    init_mem()

    init_bak = pyb.elapsed_millis(t0_millis)
    return init_bak
##############################

def main():
    global error_filename
    global uart
    global dev_number_event
    global dev_number_event_ak
    global record_event
    global charge_event
    global full_event
    global cycle_lock
    global battery_val
    global lcd_en
    global dev_num

    battery_check_value = 0
    
    init_result = initial()
    pyb.delay(100) # wait for battery_val ready and 稳定

    print("* init used total {}ms".format(init_result+100))
    battery_check_value = battery_postprocessing(battery_val, 3300)
    print("* prepare to start coros thread @{}".format(battery_check_value))
    
    if (3300 < battery_check_value):
        #write power.log
        with open(power_filename, 'a', encoding='utf-8') as pp_fi:
            pp_fi.write('poweron@{}@{:.2f}\n'.format(utime.time()+946684800, battery_check_value))
        
        if(init_result):
            print("\nWelcome to PYB_F1 board main thread\n")
            enable_lcd(True, lcd_en)
            pyb.delay(1000*2)#wait for lcd ready
            init_lcd('T'+dev_num)

            loop = asyncio.get_event_loop(runq_len=400, waitq_len=400)
            loop.create_task(date_up_("coro-0", 0, 1000,))#更新HMI日期及时间
            loop.create_task(cpu_temp_up_("coro-1", 100, 1000*10,))#更新HMI的CPU温度
            loop.create_task(chx_up_("coro-2", 50, 200,))#更新HMI上的ch0, ch1的压力值
            loop.create_task(current_rms_up_("coro-3", 150, 150,))#更新HMI上的电流RMS值
            loop.create_task(battery_up_("coro-4", 200, 1000*60,))#更新HMI上面的电池电压及电量显示
            loop.create_task(mcu_power_up_("coro-5", 250, 1000,))#更新HMI上面的MCU电压显示
            loop.create_task(gclean_("coro-6", 300, 1000*60,))#垃圾回收
            loop.create_task(lcd_receiver_("coro-7", 0, lock = cycle_lock))#接收串口命令
            loop.create_task(feed_dog_("coro-8", 0, 1000*25,))#喂狗25s
            loop.create_task(update_dev_("coro-9", 0, event=dev_number_event, event_ak=dev_number_event_ak))#更新设备号wait
            loop.create_task(dev_num_first_("coro-10", 600, event=dev_number_event,))#第一次设备号更新
            loop.create_task(rec_("coro-11", 0, event=record_event, lock = cycle_lock))#更新记录值的wait
            loop.create_task(charge_("coro-12", 0, event=charge_event,))#处理charge引脚事件
            loop.create_task(full_("coro-13", 1000*5, event=full_event,))#处理full引脚事件
            loop.create_task(space_check_up_("coro-14", 409, 1000*1,))#查检SD卡的空间占用情况

            try:
                loop.run_forever()
            except Exception as e:
                s=StringIO()
                sys.print_exception(e, s)
                print(s.getvalue())
                with open(error_filename, 'a', encoding='utf-8') as f:
                    str_temp = '{:04d}-{:02d}-{:02d}, {:02d}:{:02d}:{:02d}\n'.format(utime.localtime()[0], utime.localtime()[1], utime.localtime()[2], utime.localtime()[3], utime.localtime()[4], utime.localtime()[5])
                    f.write(str_temp)
                    f.write(s.getvalue())
                    f.write('---------------------------------------\n')
                    f.flush()
                uos.sync()
                lcd_display_error(uart=uart)
##############################
print('{} is load'.format(__name__))
if __name__ == '__main__':
    main()

if __name__ == 'builtins':
    main()

if __name__ == 'cccc':
    main()
