from libs.tm1637 import TM1637
from libs.ultraS import UltraS
from ds18x20 import DS18X20
from onewire import OneWire
from machine import Pin
from machine import RTC
from utime import sleep
from utime import sleep_us

class Control:
    def __init__(self, config):
        
        self.clockPin  = Pin(config['LED']['ClockPin'])
        self.dioPin    = Pin(config['LED']['DioPin'])
        self.tempPin   = Pin(config['Tempture']['dsPin'])
        self.heatPin   = Pin(config['Heater']['HeatPin'],Pin.OUT)
        self.HomeBtnPin   = Pin(config['HomeAway']['ButtonPin'],Pin.IN,Pin.PULL_UP)
        self.HomeLedPin   = Pin(config['HomeAway']['LedPin'],Pin.OUT)
        #self.trigger   = config['UltraS']['TriggerPin']
        #self.echo      = config['UltraS']['EchoPin']
        self.setConfig(config)
        self.manualMode= False #manul mode by default
        #setup LED pins
        self.mydisplay = TM1637(self.clockPin, self.dioPin)
        
        #setup Timer pins
        
        #setup and init Tempture sensor 
        self.ow = OneWire(self.tempPin)
        self.temp = DS18X20(self.ow)
        self.roms = self.temp.scan()
        self.temp.convert_temp()
        self.degrees = []
        self.cnt = 0
        self.rtc = RTC()
        
        
        #setup Ultra sensor
        #self.ultras = UltraS(self.trigger, self.echo, self.homeDist)
    
    def setConfig(self, config):
        self.minTempP  = config['Heater']['minTempP'] # tempture on heat pat
        self.minTempA  = config['Heater']['minTempA'] # tempture on air
        #self.homeDist  = config['UltraS']['HomeDist'] # max distance of home statue
        self.startTime = config['Schedule']['Start']  # heating start time
        self.endTime   = config['Schedule']['End']    # heating end time
        self.IgnoreHome = config['HomeAway']['Ignore']    # False : heating only when home
        
    def run(self):
        while True:
            self.cnt = 0 if self.cnt > 9 else self.cnt
            self.refreshTempture()
            self.HomeLedPin.value(1 if self.isHome() else 0)

            if self.manualMode:
                #manualMode, do not control heater
                continue
            elif not((self.IgnoreHome=='True' or self.isHome()) and self.isTiming()): 
                #Not Home and in time then stop heating
                self.heatOff()
            else:
                #In range of time, control heater
                if len(self.degrees) >1 and (self.minTempP > self.degrees[0] or self.minTempA > self.degrees[1]):
                    self.heatOn()
                else:
                   #heating one more degree if it is heating now
                   #to avoid off too soon
                   if self.isHeating() and len(self.degrees) >1 and (self.minTempP+1 > self.degrees[0] or self.minTempA+1 > self.degrees[1]):
                        #not stop heating
                       self.heatOn()
                   else:
                       self.heatOff()
                    
            self.displayLED()
            self.cnt += 1
            sleep(1)
            

    #show 7-seg LED
    def displayLED(self):
        #print(f'count={self.cnt}')
        if self.cnt <= 3:
            self.displayCurrentTime()
        elif self.cnt <=6:
            self.displayAllTemps(0)
        elif self.cnt <=9:
            self.displayAllTemps(1)

        #self.displayHomeStatus()
        #sleep(1)
    def displayText(self, text):
        self.mydisplay.show(text)
        
    #refresh tempture
    def refreshTempture(self):
        self.temp.convert_temp()
        newdegrees = []
        for rom in self.roms:
            romTemp = self.temp.read_temp(rom)
            #print(romTemp, end=" ")
            newdegrees.append(romTemp)
        self.degrees = newdegrees
        return self.degrees
    
    #read tempture sensor
    def getTemps(self):
        return self.degrees
        
    #display all tempture sensor, CX
    def displayAllTemps(self, index):
        if len(self.degrees) >1:
            dgs = self.getTemps()
            d = [0,0]
            d[0] = '{:0>2}'.format(int(dgs[0]))
            d[1] = '{:0>2}'.format(int(dgs[1]))
            #self.mydisplay.scroll(f"P {d0} A {d1}")
            s = 'P' if index==0 else 'A'
            self.mydisplay.show(f"{s} {d[index]}")
            #print(f"show temp{dgs}, cnt={self.cnt}")

    
    #display Home or AWAY
    def displayHomeStatus(self):
        self.mydisplay.show("HOME" if self.isHome() else "AWAY")
        
    def displayCurrentTime(self):
        datetm = self.rtc.datetime()
        self.mydisplay.numbers(datetm[4],datetm[5])
        
    #check if it is home
    def isHome(self):
        return not self.HomeBtnPin.value()
    
    #check if heating
    def isHeating(self):
        return self.heatPin.value()
    
    #check if it is in the time range now
    def isTiming(self):
        startTime = self.startTime #format: 21:18->2118
        endTime = self.endTime
        datetm = self.rtc.datetime()
        nowTm = datetm[4]*100+datetm[5]
        #convert to today time
        if startTime > endTime: 
            #cross night
            return ( nowTm > startTime or nowTm < endTime)
        else:
            #same day
            return ( nowTm > startTime and nowTm < endTime)

    
    #Turn on Heat
    def heatOn(self):
        self.heatPin.value(1)
        
    #Turn of heat
    def heatOff(self):
        self.heatPin.value(0)
        
    #Force Heating
    def manualHeat(self, turnOn = True):
        self.heatPin.value( 1 if turnOn else 0)
        self.manualMode = True
    
    #Set Manual Mode
    def setMode(self, manual = False):
        self.manualMode = manual

    