import network
import socket
import time
import _thread
import urequests
import utime
import json

from machine import Pin

class Pserver:
    def __init__(self, config):
        self.config = config
        self.ssid = config['SERVER']['SSID']
        self.password = config['SERVER']['WIFIPWD']
        self.port = config['SERVER']['PORT']
        self.host = '0.0.0.0'
        self.html = """<!DOCTYPE html>
        <html>
            <head> <title>Pico W</title> </head>
            <body> <h1>Pico W test123</h1>
                <p>%s</p>
            </body>
        </html>
        """

    def __del__(self):
        self.stopWifiServer()
        
    def startWifiServer(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        max_wait = 20
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)

        if self.wlan.status() != 3:
            raise RuntimeError('network connection failed')
        else:
            print('connected')
            status = self.wlan.ifconfig()
            print( 'ip = ' + status[0] )

        addr = socket.getaddrinfo(self.host, self.port)[0][-1]

        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(addr)
        self.s.listen(1)

        print('listening on', addr)


    def stopWifiServer(self):
        print('Stop server')
        self.running = False
        
        self.s.close()
        #socket.socket(socket.AF_INET, 
        #          socket.SOCK_STREAM).connect( (self.host, self.port))
        
    def sendGetRequest(self, url):
        request = urequests.get(url)
        ret  = request.content
        request.close()
        return ret

        
    def processReq(self, control):
        self.control = control
        # Listen for connections
        while True:
            try:
                print('waiting for request')
                cl, addr = self.s.accept()
                print('client connected from', addr)
                request = cl.recv(1024)

                request = request.decode("utf-8")
                res = request.split()
                print(res)
                for para in res:
                    print(para)
                
                if len(res)<=2:
                    print('connection closed due to less request content')
                    cl.close()
                    continue
                
                respon = ""
                if res[1] == '/status':
                    respon = json.dumps(self.getStatus())
                elif res[1] == '/set':
                    respon = json.dumps(self.setValues(request))
                elif res[1] == '/cmd':
                    respon = json.dumps(self.Heating(request))
                else:
                    respon = "{'err':'No such service'}"
                
                

                #stateis = request
                #response = json.dumps(ret_status)

                cl.send('HTTP/1.0 200 OK\r\nContent-type:application/json \r\n\r\n')
                cl.send(respon)
                cl.close()
                
                if request.find('stopme') >= 0:
                    print('find key word: stopme')
                    cl.close()
                    self.stopWifiServer()
                    break
                
            except OSError as e:
                print('connection closed due to exceptions')
                cl.close()
                #self.stopWifiServer()
                
    def getStatus(self):
        print('getStatus')
        temps = self.control.getTemps()
        isHome = "Home" if self.control.isHome() else "Away"
        isHeating = "Yes" if self.control.isHeating() else "No"
        datetm = utime.localtime()
        dateStr = f"{datetm[0]}/{datetm[1]}/{datetm[2]} {datetm[3]}:{datetm[4]}:{datetm[5]}"
        
        ret_status = {'now' : dateStr,
                      'home' : isHome,
                      'heating' : isHeating,
                      'temptures' : temps,
                      'mode' : 'Manual' if self.control.manualMode else 'Auto',
                      'config' : self.config
                      }
        return ret_status
    
    def setValues(self, request):
        print(f'SetValues:{request}')
        res = request.split('\r\n\r\n')
        if len(res)<=1:
            err = {'error':'Set Value Content Not Found'}
            return err
        
        try:
            params = json.loads(res[1])
            print(f'Get content:{params}')
            for pkey in params.keys():
                if pkey == 'mode':
                    self.control.setMode( True if params[pkey]=='Manual' else False )
                    continue
                for subkey in params[pkey].keys():
                    if pkey in self.config and subkey in self.config[pkey]:
                        print(f'found keys:{pkey}.{subkey}={params[pkey][subkey]}')
                        self.config[pkey][subkey] = params[pkey][subkey]
                        self.control.setConfig(self.config)
                        self.writeConfig(self.config)

            return self.getStatus()
        except Exception as e:
            err = {'error':e}
            return err
        
        
    def Heating(self,request):
        print(f'Heating:{request}')
        res = request.split('\r\n\r\n')
        if len(res)<=1:
            err = {'error':'Heating Content Not Found'}
            return err
        
        try:
            params = json.loads(res[1])
            print(f'Get Heating content:{params}')
            for pkey in params.keys():
                if pkey == 'Heating':
                    self.control.manualHeat( True if params[pkey]=='On' else False )
                    continue

            return self.getStatus()
        except Exception as e:
            err = {'error':e}
            return err
        
    def writeConfig(self, config):
        f = open('config.json', 'w')
        f.write(json.dumps(config))
        f.close()
