
from socket import *
from light import *

rgbs = [[0,0,0],[0,0,0]]
def sendrgbs():
    print "send to colon"
    s = socket(AF_INET,SOCK_STREAM)
    s.connect(("colon",getservbyname("rainbow","tcp")))
    str = "%i %i %i %i %i %i lightcontrol\n" % (rgbs[0][0],rgbs[0][1],rgbs[0][2],rgbs[1][0],rgbs[1][1],rgbs[1][2])
    s.send(str)
    print "sent %s" % str
    
    s.close()
    

class Rainbow(light,Fader):
    
    def __init__(self,name,which): # use 0 1 to pick which rainbow to control
        light.__init__(self,name)
        self.which = which
        
    def _changelevel(self):
        print "rainbow changelevel to %f" % self.level
        rgbs[self.which] = [int(self.level*255),int(self.level*255),int(self.level*255)]
        sendrgbs()
        
        # connect to colon/rainbow, send command
        # but how do we represent the colors anyway?
        # hue and sat are specific to light_rainbow, value <= level
        pass
        
