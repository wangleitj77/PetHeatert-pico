
import json
import _thread
from pserver import Pserver
from control import Control

g_startAt = "" #record the starting time from world time API
g_cn = False #Control center
g_ps = False #Pico Server
def startServer():
    global g_ps,g_cn
    g_ps = Pserver(g_cn, config)
    g_ps.startWifiServer()
    #syncTime()
    g_ps.processReq()

def startControl():
    syncTime()
    g_cn.run()

config = {}
#config = {'LED':{'ClockPin':16, 'DioPin':17},
#          'Tempture':{'dsPin':18},
#          'Heater':{'HeatPin':13, 'minTempP':21, 'minTempA':15},
#          'UltraS':{'TriggerPin':14,'EchoPin':15, 'HomeDist':30},
#          'HomePin':15
#          'Schedule':{'Start':18,'End':8}
#          }

def readConfig():
    f = open('config.json', 'r')
    config = json.loads(f.read())
    f.close()
    return config

def writeConfig(config):
    f = open('config.json', 'w')
    f.write(json.dumps(config))
    f.close()

#TODO sync world time
def syncTime():
    global g_ps,g_cn,g_startAt
    
    ret = g_ps.sendGetRequest('http://worldtimeapi.org/api/timezone/America/Los_Angeles')
    print(ret)
    jso = json.loads(ret)
    g_startAt = jso['datetime']
    print(f"Current time: {g_startAt}")

config = readConfig()
g_cn = Control(config)
_thread.start_new_thread(startControl, ())
startServer()
