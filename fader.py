from task import Task
from time import time

class Fader(Task):
    "mix-in for things with setlevel(); makes them tasks that change their level over time"
    starttime = 0
    endtime = 0
    startlev = 0
    endlev = 0
    def canfade(self):
        return 1
    def step(self):
        now = time()
        
        # fade is done?
        if now > self.endtime:
            if self.endtime != 0: # a fade ended naturally (not aborted)
                self.setlevel(self.endlev)
                self.endtime = 0
            return 0

        newlev = self.startlev +  \
                 (self.endlev-self.startlev)*     \
                 (now-self.starttime)/(self.endtime-self.starttime)

        self.setlevel(newlev)
        return 1

    def stopfade(self):
        self.endtime = 0
        return 0
    def isfading(self):
        return self.endtime != 0

    def fade(self,endlevel,seconds):
        now = time()
        self.starttime = now
        self.endtime = now+seconds
        self.startlev = self.getlevel()
        self.endlev = endlevel
        # insert self into global task list?

    def matchfade(self,other):
        self.starttime = other.starttime
        self.endtime = other.endtime
        self.startlev = self.getlevel()
        self.endlev = other.endlev
