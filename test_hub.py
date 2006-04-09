from twisted.internet import reactor
import hubclient
from louie import dispatcher
hubclient.connect("dash", 2012)
dispatcher.send("signal one")

dispatcher.send("timed test")

def listen():
    print "i got response"
dispatcher.connect(listen, "timed test response")

reactor.run()
