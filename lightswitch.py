#!/usr/local/bin/python2.3
from twisted.internet import protocol
from twisted.protocols import basic
from twisted.internet import reactor, tksupport, defer
from twisted.web.xmlrpc import Proxy
from optparse import OptionParser
import logging,sys,socket
import Tkinter as tk

log=logging.getLogger()

def lightCall(method,*args):
    proxy = Proxy("http://dot:%s" % socket.getservbyname("lights","tcp"))
    return proxy.callRemote(method,*args)

class Slider(tk.Frame):
    def __init__(self,master,lightname):
        tk.Frame.__init__(self,master)
        self.lightname = lightname
        tk.Label(self, text=lightname, font="6x13").pack(side='top')

        self.e=tk.Scale(self, orient='vertical', showvalue=0,
                        from_=1, to=0, res=1.0/64,
                        width=40, sliderlength=40, length=400,
                        state="disabled", command=self.scalechanged)
        self.e.pack(padx=5,pady=5,expand=1,fill='both')

        self.serverLev = None
        self.pendingLevel = None
        self.waitingForServer = False
        
        self.getLightLoop()

    def serverLevel(self,lev):
        self.e.config(state="normal")
        self.e.set(lev)
        self.serverLev = lev

        self.waitingForServer = False

        if self.pendingLevel is not None:
            lightCall("setLight",self.lightname,
                      self.pendingLevel).addCallback(self.serverLevel)
            self.pendingLevel = None
            self.waitingForServer = True
        
    def scalechanged(self,lev):
        lev = float(lev)
        if lev == self.serverLev:
            return
        if self.e.cget('state') == 'disabled':
            return

        if not self.waitingForServer:
            lightCall("setLight",self.lightname,
                      lev).addCallback(self.serverLevel)
            self.waitingForServer = True
            self.pendingLevel = None
        else:
            self.pendingLevel = lev

    def getLightLoop(self):
        lightCall("getLight",self.lightname).addCallback(self.serverLevel)
        self.waitingForServer = True
        reactor.callLater(1,self.getLightLoop)
        

class Screen(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bd=2, relief='raised')
        tk.Label(self, text="Screen control:").pack(side='left')
        for n in "down up stop set_top set_bottom nudge_up nudge_down".split():
            b = tk.Button(self, text=n,
                          command=lambda n=n: lightCall("screen.%s" % n))
            b.pack(side='left')
            

parser = OptionParser()
options,args = parser.parse_args()

root=tk.Tk()


Screen(root).pack(side='top')
sliders = tk.Frame()
sliders.pack(side='top')

def setupSliders(lightnames):
    for lightname in lightnames:
        e = Slider(sliders,lightname)
        e.pack(side='left')

lightCall("listLights").addCallback(setupSliders)

tksupport.install(root)
root.protocol('WM_DELETE_WINDOW', reactor.stop)

reactor.run()
