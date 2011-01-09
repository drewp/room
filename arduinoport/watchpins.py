"""
listener to the POST messages sent by drv.py when a pin changes.
records interesting events to mongodb, sends further messages.

Will also serve activity stream.
"""
import sys, os, datetime, cyclone.web, simplejson
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import getPage
from dateutil.tz import tzutc
from pymongo import Connection
from rdflib import Namespace
sys.path.append("/my/site/magma")
from activitystream import ActivityStream
from stategraph import StateGraph

DEV = Namespace("http://projects.bigasterisk.com/device/")
ROOM = Namespace("http://projects.bigasterisk.com/room/")

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.write("watchpins, writes to mongo db=house collection=sensor")

class PinChange(cyclone.web.RequestHandler):
    def post(self):
        # there should be per-pin debounce settings so we don't log
        # all the noise of a transition change
        
        msg = simplejson.loads(self.request.body)
        msg['t'] = datetime.datetime.now(tzutc())
        msg['name'] = {9: 'downstairsDoorOpen', 
                       10: 'downstairsDoorMotion',
                       }[msg['pin']]
        self.settings.mongo.insert(msg)

        # triggers go here: new motion means we need to consider a
        # door unlock; then keep polling after that to know when we
        # should lock it again (no motion for a while, or door open)
    
class GraphHandler(cyclone.web.RequestHandler):
    """
    fetch the pins from drv right now (so we don't have stale data),
    and return an rdf graph describing what we know about the world
    """
    @inlineCallbacks
    def get(self):
        g = StateGraph(ctx=DEV['theaterArduino'])

        doorOpen = int((yield getPage("http://bang:9056/pin/d9")))
        g.add((DEV['theaterDoorOpen'], ROOM['state'],
               ROOM['open'] if doorOpen else ROOM['closed']))

        motion = int((yield getPage("http://bang:9056/pin/d10")))
        g.add((DEV['theaterDoorOutsideMotion'], ROOM['state'],
               ROOM['motion'] if motion else ROOM['noMotion']))

        self.set_header('Content-type', 'application/x-trig')
        self.write(g.asTrig())
        
class Activity(cyclone.web.RequestHandler):
    def get(self):
        a = ActivityStream()
        self.settings.mongo.ensure_index('t')
        for row in self.settings.mongo.find(sort=[('t', -1)], limit=20):

            # lots todo
            if row['name'] == 'downstairsDoorMotion':
                if row['level'] == 0:
                    continue
                kw = dict(
                    actorUri="http://...",
                    actorName="downstairs door",
                    verbUri="...",
                    verbEnglish="sees",
                    objectUri="...",
                    objectName="backyard motion")
            elif row['name'] == 'downstairsDoorOpen':
                kw = dict(actorUri="http://bigasterisk.com/foaf/someone",
                       actorName="someone",
                       verbUri="op",
                       verbEnglish="opens" if row['level'] else "closes",
                       objectUri="...",
                       objectName="downstairs door",
                       objectIcon=None)
            else:
                raise NotImplementedError(row)
                    
            kw.update({'published' : row['t'],
                       'entryUriComponents' : ('sensor', row['board'])})
            a.addEntry(**kw)
            
        self.set_header("Content-type", "application/atom+xml")
        self.write(a.makeAtom())

class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Index),
            (r'/pinChange', PinChange),
            (r'/activity', Activity),
            (r'/graph', GraphHandler),
        ]
        settings = {
            'mongo' : Connection('bang', 27017,
                                 tz_aware=True)['house']['sensor']
            }
        cyclone.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    #log.startLogging(sys.stdout)
    reactor.listenTCP(9069, Application())
    reactor.run()
