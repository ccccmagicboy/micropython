#
# -*- coding: utf-8 -*-
from f1.test2 import *
import uos
import ujson

class about_display():
    uart = None
    data0 = None
    data1 = None
    def __init__(self, uart):
        self.uart = uart
    def init(self):
        if 'lcd.json' in uos.listdir('/sd') and 'settings.json' in uos.listdir('/sd'):
            with open('/sd/lcd.json', 'r', encoding='utf-8') as f1:
                self.data0 = ujson.load(f1)
                
            with open('/sd/settings.json', 'r', encoding='utf-8') as f2:
                self.data1 = ujson.load(f2)
            lcd_write(self.uart, 'about.t2.txt="fw_ver: v{}"'.format(self.data1['general']['fw_ver']))
            lcd_write(self.uart, 'about.t3.txt="rtc_cali: {:d}"'.format(self.data1['general']['rtc_cali']))
            lcd_write(self.uart, 'about.qr0.txt="pcbsn:{}"'.format(self.data1['general']['pcb_sn']))
            lcd_write(self.uart, 'about.qr1.txt="lcdsn:{}"'.format(self.data0['lcd']['sn']))
    def goto_about_page(self):
        lcd_write(self.uart, 'page about')            
        
class dev_file_display():
    index = 0 # 屏层次索引值
    files = [] # 文件list
    file_num = 0 # 文件数量
    dev_str = '' # 道叉号
    uart = None # 串口屏串口号
    multi = 0 # 整除数
    rest = 0 # 余数
    floor = 0 # 目录层次
    current_command_num = 0
    amp = 5
    start_cur = ''
    def __init__(self, uart):
        self.uart = uart
    def max_play(self):
        self.amp += 5
        if(30 == self.amp):
            self.amp = 25
        result = self.get_select_filename(self.current_command_num)            
        self.process_data(result, self.amp)
    def min_play(self):
        if not (5 == self.amp):
            self.amp -= 5
        result = self.get_select_filename(self.current_command_num)
        self.process_data(result, self.amp)
    def process_data(self, file, chart_max):
        last_tick = 0
        # check file exist first!
        if (file in uos.listdir('/sd/data/'+ self.dev_str)):
            print('{} file process!!!'.format(file))
            full_name = 'data/'+self.dev_str+'/'+file
            print(full_name)
            status0 = '{} is {} Bytes'.format(full_name, check_file_size2(file, self.dev_str))
            lcd_write(self.uart, 'recall_chart.console.txt="{}"'.format(status0))
            
            lcd_write(self.uart, 'recall_chart.t13.txt="{:d}"'.format(chart_max))            
            # 启动图表页
            lcd_write(self.uart, 'page recall_chart')            
            #pyb.delay(0)
            i = 0
            max_rms = 0
            maxl = 0
            maxr = 0
            
            try:
                with open('/sd/'+full_name, 'r', encoding='utf-8') as ff:
                    for line in reversed(list(ff)):
                        i += 1
                            
                        line=line.rstrip('\n')
                        line=line.rstrip('\r')
                        if (line.startswith('\u9053') or line.startswith('\u6587') or line.startswith('\u542f') or line.startswith('\u5e8f')):
                            if (line.startswith('\u542f')):
                                _, self.start_cur = line.split(u'：')
                                print(self.start_cur)                        
                            continue
                            
                            
                        useful_data = line.split(',')
                        #print(useful_data)
                        index = int(useful_data[0])
                        tick = int(useful_data[1])
                        current = float(useful_data[2])
                        ch0 = float(useful_data[3])
                        ch1 = float(useful_data[4])
                        
                        if (current >= max_rms):
                            max_rms = current
                        if (ch0 >= maxl):
                            maxl = ch0
                        if (ch1 >= maxr):
                            maxr = ch1
                        #print(tick, current, ch0, ch1)
                        qq = int(100/chart_max)
                        lcd_write(self.uart, 'add 14,2,{:d}'.format(int(current*qq)))
                        lcd_write(self.uart, 'add 14,0,{:d}'.format(int(ch0*qq)))
                        lcd_write(self.uart, 'add 14,1,{:d}'.format(int(ch1*qq)))
                        
                        if(1 == i):
                            last_tick = tick
            except MemoryError:
                lcd_write(self.uart, 'recall_chart.t4.txt="oops, file is too big!!!"')
            else:
                lcd_write(self.uart, 'recall_chart.t4.txt="time:{:d}ms, threshold:{:s}, max_rms:{:.2f}, max_L:{:.2f}, max_R:{:.2f}"'.format(last_tick, self.start_cur, max_rms, maxl, maxr))            
                    
    def run_command(self, command_num):
        self.current_command_num = command_num
        result = self.get_select_filename(self.current_command_num)
        print(result)
        if not ('' == result):
            if (result.startswith('T')):
                self.init(result)
            else:
                if(result.endswith('.csv')):
                    self.process_data(result, self.amp)
        else:
            if(self.floor == 0):
                self.init('', root=True)
            else:
                if(self.current_command_num == 0x03):
                    self.init('', root=True)
    def goto_recall_page(self):
        lcd_write(self.uart, 'page recall')
    def get_select_filename(self, check):
        if(0x03 == check):
            result = ''
        else:
            if(self.index == self.multi and check >= self.rest + 4):
                result = ''
            else:
                result = self.files[self.index*11 + check -4]
        return result
    def init(self, dev, root=False): #初始化页面
        del self.files[:]
        self.index = 0
        
        if(True==root):
            self.floor = 0
            self.dev_str = ''
            for file in uos.listdir('/sd/data'):
                #print('bingo')
                if (file.startswith('T')):
                    self.files.append(file)
        else:
            self.floor = 1
            self.dev_str = dev
            if not (self.dev_str in uos.listdir('/sd/data')):
                uos.mkdir('/sd/data/' + self.dev_str)
            for file in uos.listdir('/sd/data/' + self.dev_str):
                if (file.endswith('.csv')):
                    self.files.append(file)
        self.file_num = len(self.files)
        self.multi, self.rest = divmod(self.file_num,11)
        if(True==root):
            self.files.sort(reverse=False)
        else:
            self.files.sort(reverse=True)
        print(self.files, self.file_num, self.multi, self.rest)
        
        if(True==root):
            command = 'recall.b0.txt="[data]"'
        else:
            command = 'recall.b0.txt="[' + self.dev_str + ']"'
        print(command)
        lcd_write(self.uart, command)
        if (11 < self.file_num):
            for i in range(1, 12):
                command = 'recall.b' + str(i) + '.txt="' + self.files[i - 1] + '"'
                print(command)
                lcd_write(self.uart, command)
        else:
            for i in range(1, self.file_num+1):
                command = 'recall.b' + str(i) + '.txt="' + self.files[i - 1] + '"'
                print(command)
                lcd_write(self.uart, command)            
            for i in range(self.file_num+1, 12):
                command = 'recall.b' + str(i) + '.txt=""'
                print(command)
                lcd_write(self.uart, command)
    def file_up(self):  #上翻
        print('up')
        if(1<= self.multi):
            if(0 == self.index):
                print(self.index)
            else:
                self.index-=1
                print(self.index)
                for i in range(1, 12):
                    command = 'recall.b' + str(i) + '.txt="' + self.files[self.index*11 +i - 1] + '"'
                    print(command)
                    lcd_write(self.uart, command)
        else:
            for i in range(1, self.rest+1):
                command = 'recall.b' + str(i) + '.txt="' + self.files[i - 1] + '"'
                print(command)
                lcd_write(self.uart, command)            
            for i in range(self.rest+1, 12):
                command = 'recall.b' + str(i) + '.txt=""'
                print(command)
                lcd_write(self.uart, command)            
                
    def file_down(self): #下翻
        print('down')
        if(1<= self.multi):
            if not (0 == self.rest):
                if(self.index < self.multi):
                    self.index+=1
                print(self.index)
                if(self.index == self.multi):
                    for i in range(1, self.rest+1):
                        command = 'recall.b' + str(i) + '.txt="' + self.files[self.index*11 +i - 1] + '"'
                        print(command)
                        lcd_write(self.uart, command)            
                    for i in range(self.rest+1, 12):
                        command = 'recall.b' + str(i) + '.txt=""'
                        print(command)
                        lcd_write(self.uart, command)               
                else: 
                    for i in range(1, 12):
                            command = 'recall.b' + str(i) + '.txt="' + self.files[self.index*11 +i - 1] + '"'
                            print(command)
                            lcd_write(self.uart, command)            
            else:
                if(self.index < self.multi - 1):
                    self.index+=1
                print(self.index)
                for i in range(1, 12):
                        command = 'recall.b' + str(i) + '.txt="' + self.files[self.index*11 +i - 1] + '"'
                        print(command)
                        lcd_write(self.uart, command)                   
        else:
            for i in range(1, self.rest+1):
                command = 'recall.b' + str(i) + '.txt="' + self.files[i - 1] + '"'
                print(command)
                lcd_write(self.uart, command)            
            for i in range(self.rest+1, 12):
                command = 'recall.b' + str(i) + '.txt=""'
                print(command)
                lcd_write(self.uart, command)      