# main_new3.py
# -*- coding: utf-8 -*-
# @Time    : 2019/12/18
# @Author  : cccc
# @File    : main_new3.py

from f1.test2 import init_sd
from f1.test2 import init_uart
import pyb
import uos
import utime
import ujson
import os
import uos

def init_uart2(uart, bitrate):
    uart.deinit()
    uart.init(bitrate, bits=8, parity=None, stop=1, timeout=2000, read_buf_len=4096)

def check_file_size(filename):
    if(filename in uos.listdir('/sd/')):
        size = uos.stat('/sd/'+filename)[6]
    else:
        size = 0
    return size

def rest_lcd_for_down(uart):
    uart.write('rest')
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    pyb.delay(800)
    uart.write('page usb_thr')
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    pyb.delay(900)
    print(uart.read())

def connect_to_lcd(uart):
    uart.write('connect')
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    pyb.delay(500)

    x=str(uart.read())
    print(x)
    y = x.split(' ')
    print('aaa{}bbb'.format(y[0]))
    if ("b'comok" == y[0]):
        z = y[1].split(',')
        print('----------------------------------------')
        print('lcd model number is {}'.format(z[2]))
        print('lcd fw version is {}'.format(z[3]))
        print('lcd serial number is {}'.format(z[5]))
        print('----------------------------------------')
        return z[2], z[3], z[5]
    else:
        return None, None, None

def write_tft_to_lcd(uart, size, bitrate):
    uart.write('whmi-wri {},{},0'.format(size, bitrate))
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    uart.writechar(0xFF)
    pyb.delay(2000)
    if(b'\x05' == uart.read(1)):
        print('bingo!!!')
    else:
        print('bad!!!')
        #pyb.hard_reset()

    multi=int(size/4096)
    rest=size%4096
    print('{}, {}'.format(multi, rest))

    uart.deinit()
    uart.init(bitrate, bits=8, parity=None, stop=1, timeout=2000, read_buf_len=4096) # init with given parameters

    file = open('/sd/YEYA.tft', 'rb')

    for i in range(0, multi):
        uart.write(file.read(4096))
        y=uart.read(1)
        print(y)
        print(i)
        if(b'\x05' != y):
            print('bad!!!')
            pyb.hard_reset()

    uart.write(file.read(rest))
    y=uart.read(1)
    print(y)
    if(b'\x05' != y):
        print('bad!!!')
        pyb.hard_reset()
    print('happy!!!!finished!!! now reset!!!')
    pyb.delay(2000)

def write_lcd_json(file, type, fw_ver, sn, size):
    data_set = {'lcd': {'type': '', 'fw_ver': '', 'sn': '', 'file': '', 'size': 0, 'time': 0}, }
    
    data_set['lcd']['file'] = file
    data_set['lcd']['type'] = type
    data_set['lcd']['fw_ver'] = fw_ver
    data_set['lcd']['sn'] = sn
    data_set['lcd']['size'] = size
    data_set['lcd']['time'] = utime.time()+946684800
    
    json_name = '/sd/lcd.json'
    
    #del old file
    if (0 < check_file_size(json_name)):
        uos.remove(json_name)
    
    with open(json_name, 'w', encoding='utf-8') as f_set:
        f_set.seek(0)
        f_set.write(ujson.dumps(data_set))
        f_set.flush()
    os.sync()
    
def main():
    uart_lcd = pyb.UART(2)
    sd = pyb.SDCard()
    lcd_type = ''
    lcd_fw_ver = ''
    lcd_sn = ''
    tft_file = 'YEYA.tft'

    init_sd(sd)
    tft_size = check_file_size(tft_file)
    print('{} size is {} Bytes'.format(tft_file, tft_size))

    if not (0 == tft_size):
        init_uart2(uart_lcd, 115200)
        rest_lcd_for_down(uart_lcd)
        lcd_type, lcd_fw_ver, lcd_sn =connect_to_lcd(uart_lcd)
        if (None == lcd_type == lcd_fw_ver == lcd_sn):
            init_uart2(uart_lcd, 9600)
            rest_lcd_for_down(uart_lcd)
            lcd_type, lcd_fw_ver, lcd_sn =connect_to_lcd(uart_lcd)
        if ('TJC4024T032_011R' == lcd_type):
            write_tft_to_lcd(uart_lcd, tft_size, 460800)
            write_lcd_json(tft_file, lcd_type, lcd_fw_ver, lcd_sn, tft_size)
            
    if 'SKIPSD' in uos.listdir('/flash'):
        print('SKIPSD file finded in flash!')
        #cp boot.py
        if not 'boot.py' in uos.listdir('/sd'):
            with open('/flash/boot.py', 'r', encoding='utf-8') as fffs:
                with open('/sd/boot.py', 'w', encoding='utf-8') as fffd:
                    for line in list(fffs):
                        fffd.write(line)
        #cp main.py
        if not 'main.py' in uos.listdir('/sd'):
            with open('/flash/main.py', 'r', encoding='utf-8') as fffs2:
                with open('/sd/main.py', 'w', encoding='utf-8') as fffd2:
                    for line in list(fffs2):
                        fffd2.write(line)    
        #cp pybcdc.inf
        if not 'pybcdc.inf' in uos.listdir('/sd'):
            with open('/flash/pybcdc.inf', 'r', encoding='utf-8') as fffs3:
                with open('/sd/pybcdc.inf', 'w', encoding='utf-8') as fffd3:
                    for line in list(fffs3):
                        fffd3.write(line)     
        #del SKIPSD
        uos.remove('/flash/SKIPSD')
        #reboot to sd
        pyb.hard_reset()
        
    import f1.main_new2
    f1.main_new2.main()

print('{} is load'.format(__name__))
if __name__ == '__main__':
    main()

if __name__ == 'builtins':
    main()

if __name__ == 'cccc':
    main()

