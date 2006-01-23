#!/usr/local/bin/python2.3

from k8000 import *
import socket
import lights_server
import device
from light import k8000_dimmed, k8000_nd, Rainbow
from volume import Volume
from sys import stdout
import logging
import time
import SocketServer,thread,socket
from logsetup import commonlogsetup

from twisted.web import xmlrpc, server
from twisted.internet import reactor

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

digi = dict(
    pager0=1,
    pager1=2,
    pager2=3,
    pager3=4,
    offhook=5,
    dooropen=6,
    doorstrike=7,
    motion=8,
    screenpos=9,
    switches0=9, #unused
    switches1=10,
    switches2=11,
    switches3=12,
    deskhalo=13,
    screenmotorup=14,
    screenmotordown=15,
    projector=16,
    )
    
lights = [ 
           k8000_dimmed('drewdesk',8),
           k8000_dimmed('couchleft',7),
           k8000_dimmed('couchright',6),
           k8000_dimmed('dining',5),
           k8000_nd('deskhalo',digi['deskhalo']),
           k8000_nd('projector',digi['projector']),
#           Rainbow('rainbow1',0),
#           Rainbow('rainbow2',1)
           ]

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
        pagersw = (ReadIOchannel(digi['pager0']) +
                   ReadIOchannel(digi['pager1'])*2 +
                   ReadIOchannel(digi['pager2'])*4 +
                   ReadIOchannel(digi['pager3']) *8)
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
    
        oh = ReadIOchannel(digi['offhook'])
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
            now = time.time()
            if self.offtime and not self.talking and now - self.offtime>.1: 
                log.info('pick up')
                stdout.flush()
                if not self.loudvol: # maybe we have this from before the rings
                    self.loudvol = vol.getlevel()
                    vol.fade(.4,1)
                    tasks.append(vol)
                    
                tasks.append(vol)
                self.talking = 1
                
            if self.ringtime and now - self.ringtime>.1: # was ringing, now steady? ring must have stopped
                log.info('ring over')
                stdout.flush()
                self.ringtime = 0
            
        return 1
            

class task_wallswitches(Task):
    prevsw = 0
    downtime = 0
    def step(self):
        # note- chan 9 has been reused for screenmotor
        sw = (ReadIOchannel(digi['switches3']) * 8 +
              ReadIOchannel(digi['switches0']) * 4 + 
              ReadIOchannel(digi['switches1']) * 2 +
              ReadIOchannel(digi['switches2']))

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
        ConfigIOchannelAsOutput(digi['doorstrike'])

        class BarcodeHandler(SocketServer.StreamRequestHandler):
            def handle(self):
                barcode=self.rfile.readline().strip()
                log.info("got barcode %s" % barcode)
                import barcodekeys
                reload(barcodekeys)
                keys=barcodekeys.keys
                if barcode in keys:
                    log.info("door unlocks for %s" % keys[barcode])
                    SetIOchannel(digi['doorstrike'])
                    time.sleep(7)
                    ClearIOchannel(digi['doorstrike'])
                    

        self.server=SocketServer.TCPServer(('', socket.getservbyname('barcode',
                                                                     'tcp')),
                                           BarcodeHandler)

        thread.start_new_thread(self.server.serve_forever,())
        
    def step(self):
        d = ReadIOchannel(digi['dooropen'])
        if d != self.door:
            self.door = d
            log.info('door %s' % (('close','open')[self.door]))
            stdout.flush()

	m = not ReadIOchannel(digi['motion'])
	if m != self.motion: 
            self.motion = m
            log.info('motion %s' % (('no','yes')[self.motion]))
            stdout.flush()
        return 1


class task_screenmotor(Task):
    def __init__(self):
        self.oldsens = False
        self.pos = 0
        self.state = "stopped"

        self.top = 0
        self.bottom = 142
        
        self.output = dict([(n[len("screenmotor"):], k8000_nd(n, digi[n]))
                            for n in 'screenmotorup', 'screenmotordown'])

        self.stop()

        reactor.addSystemEventTrigger("before", "shutdown", self.stop)
        
    def step(self):
        sens = not ReadIOchannel(digi['screenpos'])

        if sens != self.oldsens:
            if self.output['up'].getlevel():
                self.pos -= 1
            if self.output['down'].getlevel():
                self.pos += 1

            if self.state == "nudge":
                self.stop()
            
            log.info("screenmotor position %s" % self.pos)
            self.oldsens = sens

        if self.state == "moving":
            if self.stop_test(self.pos):
                self.stop()

        return 1

    def _getFunction(self, functionPath):
        """from xmlrpc.XMLRPC interface"""

        if not functionPath.startswith("_") and functionPath != "step":
            try:
                return getattr(self, functionPath)
            except AttributeError:
                pass
        raise xmlrpc.NoSuchFunction(8001,
                                    "function %s not found" % functionPath)
    
    def down(self, _up=False):
        extent, name = self.bottom, "bottom"
        if _up:
            extent, name = self.top, "top"
            
        if extent is None:
            raise xmlrpc.Fault(8002, "%s is not set- nudge to the %s and call "
                               "set_%s() before calling this method" %
                               (name, name, name))
        
        if _up:
            self.output['up'].setlevel(1)
            self.stop_test = lambda pos: pos <= self.top
        else:
            self.output['down'].setlevel(1)
            self.stop_test = lambda pos: pos >= self.bottom

        self.state = "moving"
        
        return "ok"

    def up(self):
        return self.down(_up=True)
    
    def stop(self):
        self.output['up'].setlevel(0)
        self.output['down'].setlevel(0)
        self.state = "stopped"
        return "ok"
        
    def set_top(self):
        # should move bottom so top is always zero
        self.top = self.pos
        return "ok"
    
    def set_bottom(self):
        self.bottom = self.pos
        return "ok"
    
    def nudge_up(self, _dir="up"):
        self.output[_dir].setlevel(1)
        self.state = "nudge"
        self.lastpos = self.pos
        return 'ok'
    
    def nudge_down(self):
        return self.nudge_up(_dir="down")
        

class ambient_light(Task):
    def __init__(self):
        self.last_levs = []
        self.window_size = 4
        self.last_shown = 0
        self.recent_reports = [] #times
    def step(self):
        x = ReadADchannel(3)
        now = time.time()
        self.recent_reports = [t for t in self.recent_reports if now-t<10]

        self.last_levs = self.last_levs[:self.window_size-1] + [x]
        avg = int(sum(self.last_levs) / len(self.last_levs))
        if avg != self.last_shown:
            delta = abs(avg - self.last_shown)
            if delta > 2 and len(self.recent_reports) < 3:
                log.info("ambient light at %s" % avg)
                self.recent_reports.append(now)
                self.last_shown = avg
        return 1
            

vol = Volume()

tasks = []

phonetask = task_phone()
tasks.append(phonetask)
#tasks.append(task_door())
tasks.append(task_pager())
#tasks.append(task_vol_slider())
screenmotor = task_screenmotor()
tasks.append(screenmotor)
tasks.append(ambient_light())

class LightsServer(xmlrpc.XMLRPC):
    def xmlrpc_getLight(self,lightname):
        l = getlightbyname(lightname)
        if l is None:
           raise ValueError("light %r not found" % lightname)
        return float(l.getlevel())
    
    def xmlrpc_setLight(self,lightname,level):
        level = float(level)
        l = getlightbyname(lightname)
        l.setlevel(level)
        return level
    def xmlrpc_listLights(self):
        return [l.getname() for l in lights]

xmlrpcserv = LightsServer()
reactor.listenTCP(socket.getservbyname('lights','tcp'),
                  server.Site(xmlrpcserv))

xmlrpcserv.putSubHandler("screen",screenmotor)
        

debug=0
if debug:
  log.setLevel(logging.DEBUG)
else:
  log.setLevel(logging.INFO)

def backgroundtasks():
    for x in tasks:
        if debug:
            t1 = time.time()
            repeat = x.step()
            stepTime = time.time() - t1
            print "%s step takes %.1fms" % (x.__class__, stepTime * 1000)
        else:
            repeat = x.step()
        if not repeat:
            tasks.remove(x)
    reactor.callLater(.005+.2*debug, backgroundtasks)

backgroundtasks()

reactor.run()
