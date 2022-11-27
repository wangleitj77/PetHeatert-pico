from machine import Pin
import utime

class UltraS:
    def __init__(self, trigger, echo, homeDist = 30):
        self.trigger = Pin(trigger, Pin.OUT)
        self.echo = Pin(echo, Pin.IN)
        self.homeDist = homeDist
        
    def getDistance(self):
       self.trigger.low()
       utime.sleep_us(2)
       self.trigger.high()
       utime.sleep_us(5)
       self.trigger.low()
       signaloff = 0
       signalon = 0
       while self.echo.value() == 0:
           signaloff = utime.ticks_us()
       while self.echo.value() == 1:
           signalon = utime.ticks_us()
       timepassed = signalon - signaloff
       distance = (timepassed * 0.0343) / 2
       print("The distance from object is ",distance,"cm")
       
       return distance

    def setHomeDistance(self,homeDist):
        self.homeDist = homeDist
        
    def isHome(self):
        return self.homeDist > self.getDistance()
    