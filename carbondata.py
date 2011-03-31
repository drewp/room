"""
upload data to a carbon server (http://graphite.wikidot.com/carbon) from twisted

copied in netbars
"""
from __future__ import division
import time, math
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.internet import reactor, task

class CarbonFactory(ReconnectingClientFactory):
    protocol = Protocol

class CarbonClient(object):
    def __init__(self, serverHost="localhost", port=2003):
        self.carbonFactory = CarbonFactory()

        self.conn = reactor.connectTCP(serverHost, port, self.carbonFactory)
        
    def send(self, metricPath, value, timestamp="now"):
        # quietly fails if the connection isn't ready yet :(
        if timestamp == "now":
            timestamp = time.time()
        # carbon quietly ignores floating-point times
        self.conn.transport.write("%s %f %d\n" % (str(metricPath), # no unicode
                                                  value, timestamp))

if __name__ == '__main__':
    c = CarbonClient()

    def writeSin():
        now = time.time()
        print "sin", now
        c.send('system.demo.sensor2.sintwisted3', 50 + 50 * math.sin(now))

    task.LoopingCall(writeSin).start(2)

    reactor.run()
