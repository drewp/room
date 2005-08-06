from k8000 import *
import device
from fader import *
import math
import logging
log=logging.getLogger("light")
testmode = 0



class transfercurve:
    "stores and evaluates a curve through (0,low), (.5,mid), (1,high)"
    def __init__(self):
        self.setparams(0,.5,1)
    def setparams(self, low, mid, high ):
        self.levlow = low
        self.levmid = mid
        self.levhigh = high

        # precompute variables for eval'ing curve
        self._a = self.levlow
        self._b = self.levhigh-self.levlow
        self._c = math.log((self.levmid-self._a)/self._b)/math.log(.5)
    def evallevel(self,x): # returns y in [low,high], with gamma = mid
        if x==0 or x==1:
            y=x
        else:
            y = 1.0*self._a + self._b * (x**self._c)
        # print " eval %f -> %f (%f,%f,%f)" % (x,y,self._a,self._b,self._c)
        return y
    

class light(device.device):
    "light has a level and a transfercurve for remapping levels for the light output"
    def __init__(self,name):
        self.level=0
        self.setname(name)
        self.tc = transfercurve()

    def settcparams(self,low,mid,high):
        self.tc.setparams(low,mid,high)
        
    def setlevel(self,newlevel):
        if self.level != newlevel:
            if newlevel<0:
                newlevel = 0
            if newlevel>1:
                newlevel = 1
            self.level = newlevel

            self.tclevel = self.tc.evallevel(newlevel)

            if testmode:
                log.debug('testmode: light changelevel to %f' % newlevel)
            else:
                self._changelevel()

    def getlevel(self):
        return self.level
    def canfade(self):
        return 0

class k8000_dimmed(light,Fader):
    def __init__(self,name,dacchannel):
        light.__init__(self,name)
        self.setdacchannel(dacchannel)
    def setdacchannel(self,chan):
        self.chan = chan
    def _changelevel(self):
        OutputDACchannel(self.chan,int(round(self.tclevel*64)))
        UpdateAllDAC() # terrible - should get called after a -round- of settings

class k8000_nd(light,Fader):
    def __init__(self,name,iochannel):
        light.__init__(self,name)
        self.setiochannel(iochannel)
    def setiochannel(self,chan):
        self.chan = chan
        ConfigIOchannelAsOutput(chan)
    def _changelevel(self):
        if self.level < .5:
            ClearIOchannel(self.chan)
        else:
            SetIOchannel(self.chan)
        UpdateIOchip(0) # ? specific to low IO's?

from rainbow import Rainbow


