

class device:
    name = "unnamed"
    def setname(self,name):
        self.name = name
    def getname(self):
        return self.name
    def nothing(self):
        print 'nothing'
    def powerdown(self):
        pass # go to the setting that uses no power, to be defined by child classes


