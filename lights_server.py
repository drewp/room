import socket
import asyncore
import string
import asynchat
import logging
from light import *

log=logging.getLogger("lights_server")
log.setLevel(logging.INFO)

# copy from main program to operate on our local copy of lights
def getlightbyname(name):
    for x in lights:
        if x.getname()==name:
            return x
    return None

lights = []

class lights_server(asyncore.dispatcher):
    
    def __init__(self,lightlist): 
        global lights
        lights = lightlist
        self.port = socket.getservbyname('lights','tcp')
        asyncore.dispatcher.__init__ (self)
        self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('', self.port))
        self.listen(1)

    def dopoll(self,seconds):
        # if asyncore.socket_map
        asyncore.poll(seconds)

    def handle_accept (self):
        conn, addr = self.accept()
        log.debug('incoming connection from %s:%d' % (addr[0], addr[1]))
        lights_chan (conn, addr)
          
class lights_chan (asynchat.async_chat): # handles one connection to the server
    def __init__ (self, conn, addr):
        asynchat.async_chat.__init__ (self, conn)
        self.set_terminator ('\n')
        self.in_buffer = ''

    def handle_connect (self):
        self.send('\377\375\"')

    def collect_incoming_data (self, data):
        self.in_buffer = self.in_buffer + data

    def found_terminator (self):
        log.debug('got input '+self.in_buffer)
        words = string.split(self.in_buffer)
        self.in_buffer = ''

        if len(words)<1:
            return
        lightname = string.strip(words[0])
        l = getlightbyname(lightname)
        if not isinstance(l,light):
            log.warning("%s is not a light" % l)
            return
        
        if len(words)>1:
            level = string.atof(words[1])
            log.debug('will set %s to %f' % (lightname,level))
            l.setlevel(level)
        else:
            self.push(("%s %s" % (lightname,l.getlevel()))+self.terminator)


    def handle_close (self):
        self.close()

