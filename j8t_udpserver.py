from __future__ import print_function

import socket

import json
import time
import sys

listen = ('127.0.0.1', 2242)





class Server(object):

    def from_message(self,content):
        try:
            return json.loads(content)
        except ValueError:
            return {}


    def to_message(self,typ, value='', params=None):
        # do not log these send messages types
        if typ not in ('TX.GET_TEXT',):
            self.log('Send: ',typ,value,params)
        if params is None:
            params = {}
        return json.dumps({'type': typ, 'value': value, 'params': params})

    
    def process(self, message):
        typ = message.get('type', '')
        value = message.get('value', '')
        params = message.get('params', {})
        #do not log these messages
        if typ not in ('PING','STATION.STATUS','RX.SPOT','TX.FRAME','TX.TEXT','RX.ACTIVITY','RX.DIRECTED','RX.DIRECTED.ME','RIG.PTT'):
            self.log('Rx from JS8Call: ', typ)
            if value:
                self.log('      value: ', value)
            if params:
                self.log ('      params: ', params)
                
        # PING - save values for reading by gui    
        if typ == 'PING':
            self.js8_name=params['NAME']
            self.js8_UTC=params['UTC']
            self.js8_version=params['VERSION']
            self.ping_timeout=0
            # first time through init things that need server to be connected
            if self.first is True:
                self.connected_callback(True)
                self.first=False

            return        

        # pass some other messages to gui
        elif typ in ('RX.ACTIVITY','RX.DIRECTED','RX.DIRECTED.ME','STATION.STATUS','RIG.PTT','RIG.FREQ','MODE.SPEED','TX.TEXT','STATION.GRID','STATION.CALLSIGN','CLOSE'):
            self.event_callback(typ,value,params)
            return
            
        elif typ == 'CLOSE':
            self.ping_timeout= 150 # make disconnection happen after 5 secs
            self.close()
            pass
            
        elif typ in('TX.FRAME','RX.SPOT'):
            return
            
        else:
            self.log('UNHANDLED MESSAGE ',typ)

    def init_params(self):
        # PING message
        self.js8_name=''
        self.js8_UTC=''
        self.js8_version=''


    def send(self, *args, **kwargs):
        params = kwargs.get('params', {})
        if '_ID' not in params:
            params['_ID'] = int(time.time()*1000)
            kwargs['params'] = params
        message = self.to_message(*args, **kwargs)
        # print('outgoing message:', message)
        self.sock.sendto(message.encode(), self.reply_to)



    def init(self,root,ip,port,connected_callback,event_callback,reply_callback,error_callback,log):
        self.root=root
        self.ip=ip
        self.port=port
        self.connected_callback=connected_callback
        self.event_callback=event_callback
        self.reply_callback=reply_callback
        self.error_callback=error_callback
        self.log=log
        self.init_params()
        self.log('Listening on:', self.ip,':',self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip,int(self.port)))
        self.sock.settimeout(0.1)
        self.listening=True
        self.first=True
        self.ping_timeout=0




    def listentk(self):
        if not self.listening:
            return
        self.ping_timeout+=1
        if self.ping_timeout >= 200:   #20 seconds at 100mS
            self.error_callback('Lost connection with JS8Call\nTrying to reconnect')
            self.log('Lost connection with JS8Call')
            self.connected_callback(False)
            self.ping_timeout=0
            self.first=True
        try:
            content,addr = self.sock.recvfrom(4096)
        except socket.timeout as e:
            err = e.args[0]
            # timeout so just loop
            if err == 'timed out':
                self.root.after(100,self.listentk)
            else:
                self.error_callback(e)
                self.root.after(100,self.listentk) 
        except socket.error as e:
            # Something else happened, handle error, exit, etc.
                self.error_callback(e)
                self.root.after(100,self.listentk) 
        else:
            if len(content) == 0:
                self.error_callback('Zero length content')
                self.root.after(100,self.listentk)
            else:
                # got a message do something :)
                #print('incoming message:', ':'.join(map(str, addr)))

                try:
                    message = json.loads(content)
                except ValueError:
                    message = {}
                    self.error_callback('json conversion failed')
                    self.root.after(100,self.listentk)

                if not message:
                    self.error_callback('not message')
                    self.root.after(100,self.listentk)
                    
                self.reply_to = addr
                    
                self.process(message)


                
                self.root.after(100,self.listentk)


    def close(self):
        self.listening = False
        self.sock.close()

