from nevow import athena, loaders

class Button(athena.LiveFragment):
    jsClass = u"SimpleWidget.Button"
    docFactory = loaders.xmlstr("""
<div xmlns:nevow="http://nevow.com/ns/nevow/0.1"
     nevow:render="liveFragment">
  <form onSubmit="return false;">
    <input type="submit" value="" onClick="SimpleWidget.Button.get(this).click()"/>
  </form>
</div>""")
    allowedMethods = ['onClick', 'getLabel']
    def __init__(self, label):
        athena.LiveFragment.__init__(self)
        self.label = label

    def getLabel(self):
        return unicode(self.label)
    
    def onClick(self):
        print "clicked %s" % self.label
