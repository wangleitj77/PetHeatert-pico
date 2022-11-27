import network
import socket
import time
import _thread
import urequests
import utime

from machine import Pin

class Pserver:
    def __init__(self, control, config):
        self.control = control
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


        
    def processReq(self):
        # Listen for connections
        while True:
            try:
                cl, addr = self.s.accept()
                print('client connected from', addr)
                request = cl.recv(1024)
                print(request)

                request = str(request)
                
                temps = self.control.getTemps()
                isHome = "Home" if self.control.isHome() else "Away"
                isHeating = "Yes" if self.control.isHeating() else "No"
                datetm = utime.localtime()
                dateStr = f"{datetm[0]}/{datetm[1]}/{datetm[2]} {datetm[3]}:{datetm[4]}:{datetm[5]}"
                tempStr = f"<br/><br/>Current Time: {dateStr}<br/><br/>Heating: {isHeating}<br/><br/>Current temptures: {temps}<br/><br>Home Statue: {isHome}<br/><br>Manual Control: {self.control.manualMode}<br/><br>Config: {self.config}"
                

                stateis = request
                response = self.html % tempStr

                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(response)
                cl.close()
                
                if request.find('stopme') >= 0:
                    print('find key word: stopme')
                    cl.close()
                    self.stopWifiServer()
                    break
                
            except OSError as e:
                print('connection closed due to exceptions')
                cl.close()
                self.stopWifiServer()
                
                
