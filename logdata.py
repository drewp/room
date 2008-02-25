#!/usr/bin/python
"""
listen for some signals and log them in files
"""

import logging, time
from louie import dispatcher
from twisted.internet import reactor
import sys
import twisted.python.log
from nevow.appserver import NevowSite
from nevow import rend, loaders, json, static, tags as T, inevow
from xml.utils import iso8601
from email.utils import formatdate

import hubclient
from logsetup import commonlogsetup

log = commonlogsetup(filename=None)
log.setLevel(logging.INFO)

hubclient.connect()

history = []

def dataIn(**kw):
    now = time.time()
    if kw['signal'] == 'temps':
        print now, sorted(kw['temps'].items())

        typed = dict([(k.decode('ascii'), float(v))
                      for k,v in kw['temps'].items()])
        typed[u'time'] = iso8601.ctime(now).decode('ascii')
        history[:] = history[-500:] + [typed]

class Main(rend.Page):
    docFactory = loaders.xmlstr("<p>logdata server</p>")
    def child_temps(self, ctx):
        class Ret(rend.Page):
            def renderHTTP(self, ctx):
                sensors = set()
                for row in history[::10]: # hope we hit all the keys
                    sensors.update(row.keys())
                sensors.discard(u'time')
                sensors = sorted(sensors)
                return "(%s)" % json.serialize({u'sensors' : sensors,
                                                u'temps' : history})
        return Ret()
    
    def child_heater(self, ctx):
        """heater on/off events in timeplot/timeline event xml format:
        http://simile.mit.edu/wiki/How_to_Create_Event_Source_Files """
        class Ret(rend.Page):
            def renderHTTP(self, ctx):
                inevow.IRequest(ctx).setHeader("Content-Type", "text/xml")
                return rend.Page.renderHTTP(self, ctx)
            def render_events(self, ctx, data):
                current = None
                now = time.time()
                for line in open("log.parport"):
                    if 'heater on True' in line:
                        current = line
                    if 'heater on False' in line and current is not None:
                        convTime = lambda line: float(line.split()[0])

                        t1 = convTime(current)
                        t2 = convTime(line)
                        if t2 < now - float(ctx.arg('secs', 16 * 3600)):
                            continue
                        yield T.Tag('event')(start=formatdate(t1),
                                             end=formatdate(t2),
                                             isDuration='true',
                                             title='hi')[
                            'heater on for %.1f min' % ((t2 - t1) / 60)]

            docFactory = loaders.stan(T.Tag('data')[render_events])
        return Ret()

    def child_tempchart(self, ctx):
        return static.File("tempchart")
    def child_flot(self, ctx):
        return static.File("flot")
    def child_www(self, ctx):
        return static.File("www")
    def child_dpms(self, ctx):
        import report.dpms
        reload(report.dpms)
        return report.dpms.Report()
    
twisted.python.log.startLogging(sys.stdout)
reactor.listenTCP(8007 + (len(sys.argv) > 1), NevowSite(Main()))

dispatcher.connect(dataIn, 'temps')

reactor.run()
