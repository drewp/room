#!/usr/local/bin/python2.3

from k8000 import *
import socket
import lights_server
import device
from light import *
from volume import Volume
from sys import stdout
import logging
import time
import SocketServer,thread,socket

from twisted.web import xmlrpc, server
from twisted.internet import reactor

def commonlogsetup(excludechannels=[]):
    """sets up logs how i usually like them, with a custom filter to
    exclude the given channel names. log level is DEBUG. return value
    is the top-level logger"""
    if isinstance(excludechannels,(str,unicode)):
        excludechannels=[excludechannels]
    class myfilter(logging.Filter):
        def filter(self,record,excludechannels=excludechannels):
            return record.name not in excludechannels
    log=logging.getLogger()
    log.setLevel(logging.DEBUG)

    for h in logging.StreamHandler(), logging.FileHandler("log"):
        h.setFormatter(logging.Formatter("%(created)s %(asctime)s %(levelname)-5s %(filename)s:%(lineno)d: %(message)s"))
        h.addFilter(myfilter())
        log.addHandler(h)
    return log

log=commonlogsetup()


# 3-swinging, 11-bc1 10-bc2, 2-lcr, 6-hall, 8-door = 3, 8, 10, 2, 6, 8


# use a switch number as index into switchloc to get a list of names of near lights
#             0  1  2        3            4  5  6        7  8                  9  10
switchloc = [ [],[],['hall'],['drewdesk'],[],[],['hall'],[],['table'],[],['BCR','swinging'],['BCR','swinging'] ]



log.info('initialized')
ConfigAllIOasInput()

global testmode
testmode=1

class pager_client:
    def __init__(self,x,y):
        self.coords = (x,y)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('dash', socket.getservbyname('pager','tcp') ))
            s.send('%i %i' % self.coords)
            s.close()
        except socket.error, num:
            #print 'pager_client: socket err %s' % num
            pass


lights = [ 
           k8000_dimmed('drewdesk',8),
           k8000_dimmed('couchleft',7),
           k8000_nd('deskhalo',13),
           k8000_nd('screenmotor0',14),
           k8000_nd('screenmotor1',15),
           Rainbow('rainbow1',0),
           Rainbow('rainbow2',1)]

def getlightbyname(name):
    for x in lights:
        if x.getname()==name:
            return x
    return None


#params = [["swinging",.3,.65,1],["hall",.35,.55,1],
#          ["LCL",.4,.7,1],["BCR",.35,.55,1],["table",.28,.65,1]]
#for p in params:
#    getlightbyname(p[0]).settcparams(p[1],p[2],p[3])

prev = 0
lev = 0

from task import Task

class task_pager(Task):
    def step(self):
        pagersw = ReadIOchannel(1) + ReadIOchannel(2)*2 + ReadIOchannel(3)*4 + ReadIOchannel(4) *8
        if pagersw:
            # send page number to the FVWM RealPager module
            pagersw = pagersw-1
            pager_client(pagersw % 4, int(pagersw/4)) # creating this does the send
        return 1

class task_phone(Task):
    # oh = on-hook
    prevoh = 1
    offtime = 0 # time since off-hook
    talking = 0 # phone off hook for talking (not ringing)?
    ringtime = 0 # time since last ring started, 0 if not ringing

    loudvol=0
    def offhook(self):
        return self.offtime!=0
    def step(self):
    
        oh = ReadIOchannel(5)
        log.debug("phone reads %s" % oh)

        if oh != self.prevoh:
            self.prevoh = oh
            if not oh: # on- to off-hook
                self.offtime = time.time()

            else: # off- to on-hook
                if time.time()-self.offtime < .1: # off-to-on too fast? must be a ring
                    if not self.ringtime:
                        log.info('start ring')
                        stdout.flush()
                        self.loudvol = vol.getlevel()
                        vol.fade(.02,1)
                        tasks.append(vol)
                    self.ringtime = time.time()
                else:
                    log.info('hangup, vol back to %f' % (self.loudvol))
                    stdout.flush()
                    vol.fade(self.loudvol,2)
                    
                    tasks.append(vol);
                    self.loudvol=0
                    self.talking = 0
                    
                self.offtime = 0                
        else:
            if self.offtime and not self.talking and time.time()-self.offtime>.1: 
                log.info('pick up')
                stdout.flush()
                if not self.loudvol: # maybe we have this from before the rings
                    self.loudvol = vol.getlevel()
                    vol.fade(.4,1)
                    tasks.append(vol)
                    
                tasks.append(vol)
                self.talking = 1
                
            if self.ringtime and time.time()-self.ringtime>.1: # was ringing, now steady? ring must have stopped
                log.info('ring over')
                stdout.flush()
                self.ringtime = 0
            
        return 1
            

class task_wallswitches(Task):
    prevsw = 0
    downtime = 0
    def step(self):
        # note- chan 9 has been reused for screenmotor
        sw = ReadIOchannel(12) * 8 + ReadIOchannel(9) * 4 + \
             ReadIOchannel(10) * 2 + ReadIOchannel(11)

        action = "none"
        if sw:
            if not self.prevsw:
                action = "press"
                print "%f press switch #%i" % (time.time(),sw)
                self.prevsw = sw
                self.held = 0
                self.downtime = time.time()
            else:
                if time.time()-self.downtime > .2 and not self.held:
                    action = "hold"
                    print "hold"
                    self.held = 1
        else:
            if self.prevsw:
                action = "release"
                self.prevsw = sw


        def lightsbyswitch(sw):
            return map(lambda n: getlightbyname(n), switchloc[sw])

        if action == "press":
            primary = getlightbyname(switchloc[sw][0]) # one of the lights on this switch

            if not isinstance(primary,Fader): # primary is ND (treat all as ND)
                for l in lightsbyswitch(sw):
                    l.setlevel(round(1-primary.getlevel()))
            else:
                if primary.isfading(): # in a fade - abort
                    print "stop fade"
                    for l in lightsbyswitch(sw):
                        if isinstance(l,Fader):
                            l.stopfade()
                else: # start a fade
                    print "start fade"
                    for l in lightsbyswitch(sw):
                        if primary.getlevel() > .3:
                            l.fade(0,3) # bright? slow fadeoff
                        else:
                            l.fade(1,.3) # dim? fast fadeon
                        tasks.append(l)

        if action == "hold":
            primary = getlightbyname(switchloc[sw][0])

            if isinstance(primary,Fader):
                if primary.isfading():
                    print "match fade"
                    for l in lights:
                        if isinstance(l,Fader):
                            l.matchfade(primary)
                            tasks.append(l)
                else:
                    print "match level"
                    for l in lights:
                        l.setlevel(primary.getlevel())
                            
        return 1

class task_lights_server(Task):
    def __init__(self):
        self.ls = lights_server.lights_server(lights)
    def step(self):
        self.ls.dopoll(.02)
        return 1

class task_vol_slider(Task):
    avg = [0,0,0]
    i=0
    sum = 1

    def step(self):
        v = ReadADchannel(4)
        log.debug("volume reads %s" % v)
        self.sum = self.sum - self.avg[self.i] + v
        self.avg[self.i] = v
        self.i = (self.i + 1)%3
            
        setvol = 1.0*min(self.avg)/205
        
        if setvol > 1:
            setvol = 1
        if phonetask.offhook() == 0 and not vol.isfading():
            vol.setlevel(setvol)
#        print 'set to %f' % setvol

        return 1

class task_door(Task):
    door = 0 # 0=closed, 1=opened
    motion = 0 # 0=no, 1=yes
    def __init__(self):
        self.strikechan=7
        ConfigIOchannelAsOutput(self.strikechan) # chan 7 is output for door strike

        class BarcodeHandler(SocketServer.StreamRequestHandler):
            def handle(self):
                barcode=self.rfile.readline().strip()
                log.info("got barcode %s" % barcode)
                import barcodekeys
                reload(barcodekeys)
                keys=barcodekeys.keys
                if barcode in keys:
                    log.info("door unlocks for %s" % keys[barcode])
                    SetIOchannel(7)#self.strikechan)
                    time.sleep(7)
                    ClearIOchannel(7)#self.strikechan)
                    

        self.server=SocketServer.TCPServer( ('', socket.getservbyname('barcode','tcp')), BarcodeHandler)

        thread.start_new_thread(self.server.serve_forever,())
        
    def step(self):

#        SetIOchannel(self.strikechan)
#        ClearIOchannel(self.strikechan)
        
        d = ReadIOchannel(6)
        if d != self.door:
            self.door = d
            log.info('door %s' % (('close','open')[self.door]))
            stdout.flush()

	m = not ReadIOchannel(8)
	if m != self.motion: 
            self.motion = m
            log.info('motion %s' % (('no','yes')[self.motion]))
            stdout.flush()
        return 1


class task_screenmotor(Task):
    def __init__(self):
        self.oldsens = False
        self.pos = 0
    def step(self):
        sens = not ReadIOchannel(9)
        
        if sens != self.oldsens:
            if getlightbyname("screenmotor0").getlevel():
                self.pos += 1
            if getlightbyname("screenmotor1").getlevel():
                self.pos -= 1
            
            log.info("screenmotor position %s" % self.pos)
            self.oldsens = sens
            getlightbyname("drewdesk").setlevel(sens)
        return 1

vol = Volume()

#task_wallswitches()
#tasks = [ task_lights_server(), task_door() ]
tasks = []

phonetask = task_phone()
tasks.append(phonetask)
tasks.append(task_door())
tasks.append(task_pager())
tasks.append(task_vol_slider())
#tasks.append(task_lights_server())
tasks.append(task_screenmotor())

class LightsServer(xmlrpc.XMLRPC):
    def xmlrpc_getLight(self,lightname):
        l = getlightbyname(lightname)
        return float(l.getlevel())
    def xmlrpc_setLight(self,lightname,level):
        l = getlightbyname(lightname)
        l.setlevel(float(level))
        return "ok"
    def xmlrpc_listLights(self):
        return [l.getname() for l in lights]
reactor.listenTCP(socket.getservbyname('lights','tcp'),
                  server.Site(LightsServer()))
        

debug=0
if debug:
  log.setLevel(logging.DEBUG)
else:
  log.setLevel(logging.INFO)

def backgroundtasks():
    for x in tasks:
        if not x.step():
            tasks.remove(x)
    reactor.callLater(.005+.2*debug, backgroundtasks)


backgroundtasks()

reactor.run()
