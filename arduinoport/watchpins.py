"""
listener to the POST messages sent by drv.py when a pin changes.
records interesting events to mongodb, sends further messages.

Will also serve activity stream.
"""
import sys, os, datetime, cyclone.web, simplejson, time
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.error import ConnectError
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage
from dateutil.tz import tzutc
from pymongo import Connection
from rdflib import Namespace, Literal, Graph
from rdflib.parser import StringInputSource
sys.path.append("/my/site/magma")
from activitystream import ActivityStream
from stategraph import StateGraph
     
sys.path.append("/my/proj/homeauto/lib")
from cycloneerr import PrettyErrorHandler

DEV = Namespace("http://projects.bigasterisk.com/device/")
ROOM = Namespace("http://projects.bigasterisk.com/room/")

class Index(PrettyErrorHandler, cyclone.web.RequestHandler):
    def get(self):
        self.write("watchpins, writes to mongo db=house collection=sensor")

class PinChange(PrettyErrorHandler, cyclone.web.RequestHandler):
    def post(self):
        # there should be per-pin debounce settings so we don't log
        # all the noise of a transition change
        
        msg = simplejson.loads(self.request.body)
        msg['t'] = datetime.datetime.now(tzutc())
        msg['name'] = {9: 'downstairsDoorOpen', 
                       10: 'downstairsDoorMotion',
                       }[msg['pin']]
        self.settings.mongo.insert(msg)

        if msg['pin'] == 10 and msg['level'] == 1:
            self.settings.history['lastMotion'] = msg['t']

class InputChange(PrettyErrorHandler, cyclone.web.RequestHandler):
    def post(self):
        msg = simplejson.loads(self.request.body)
        msg['t'] = datetime.datetime.now(tzutc())
        self.settings.mongo.insert(msg)

        # trigger to entrancemusic? rdf graph change PSHB?

class GraphHandler(PrettyErrorHandler, cyclone.web.RequestHandler):
    """
    fetch the pins from drv right now (so we don't have stale data),
    and return an rdf graph describing what we know about the world
    """
    @inlineCallbacks
    def get(self):
        g = StateGraph(ctx=DEV['houseSensors'])

        frontDoorDefer = getPage("http://slash:9080/door") # head start?

        doorOpen = int((yield getPage("http://bang:9056/pin/d9")))
        g.add((DEV['theaterDoorOpen'], ROOM['state'],
               ROOM['open'] if doorOpen else ROOM['closed']))

        motion = int((yield getPage("http://bang:9056/pin/d10")))
        g.add((DEV['theaterDoorOutsideMotion'], ROOM['state'],
               ROOM['motion'] if motion else ROOM['noMotion']))

        now = datetime.datetime.now(tzutc())
        lastMotion = self.settings.history['lastMotion']
        g.add((DEV['theaterDoorOutsideMotionRecent'], ROOM['state'],
               ROOM['motion']
               if (now - lastMotion) < datetime.timedelta(seconds=10)
               else ROOM['noMotion']))

        t1 = time.time()
        try:
            for s in (yield self.getBedroomStatements()):
                g.add(s)
        except ConnectError, e:
            g.add((ROOM['bedroomStatementFetch'], ROOM['error'],
                   Literal("getBedroomStatements: %s" % e)))
            

        try:
            frontDoor = yield frontDoorDefer
            g.add((DEV['frontDoorOpen'], ROOM['state'],
               ROOM[frontDoor] if frontDoor in ['open', 'closed'] else
               ROOM['error']))
        except Exception, e:
            g.add((DEV['frontDoorOpen'], ROOM['error'], Literal(str(e))))

        self.set_header('Content-type', 'application/x-trig')
        self.write(g.asTrig())

    @inlineCallbacks
    def getBedroomStatements(self):
        trig = yield getPage("http://bang:9088/graph")
        stmts = set()
        for line in trig.splitlines():
            if "http://projects.bigasterisk.com/device/bedroomMotion" in line:
                g = Graph()
                g.parse(StringInputSource(line+"\n"), format="nt")
                for s in g:
                    stmts.add(s)
        returnValue(stmts)
        
class Activity(PrettyErrorHandler, cyclone.web.RequestHandler):
    def get(self):
        a = ActivityStream()
        self.settings.mongo.ensure_index('t')
        remaining = {'downstairsDoorMotion':10, 'downstairsDoorOpen':10,
                     'frontDoorMotion':10, 'frontDoor':50}
        recent = {}
        for row in reversed(list(self.settings.mongo.find(sort=[('t', -1)],
                                                     limit=5000))):
            try:
                r = remaining[row['name']]
                if r < 1:
                    continue
                remaining[row['name']] = r - 1
            except KeyError:
                pass
            
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
                    objectName="backyard motion",
                    objectIcon="/magma/static/backyardMotion.png")
            elif row['name'] == 'downstairsDoorOpen':
                kw = dict(actorUri="http://bigasterisk.com/foaf/someone",
                       actorName="someone",
                       verbUri="op",
                       verbEnglish="opens" if row['level'] else "closes",
                       objectUri="...",
                       objectName="downstairs door",
                       objectIcon="/magma/static/downstairsDoor.png")
            elif row['name'] == 'frontDoor':
                kw = dict(actorUri="http://bigasterisk.com/foaf/someone",
                       actorName="someone",
                       verbUri="op",
                       verbEnglish="opens" if row['state']=='open' else "closes",
                       objectUri="...",
                       objectName="front door",
                       objectIcon="/magma/static/frontDoor.png")
            elif row['name'] == 'frontDoorMotion':
                if row['state'] == False:
                    continue
                if 'frontDoorMotion' in recent:
                    pass#if row['t'
                kw = dict(
                    actorUri="http://...",
                    actorName="front door",
                    verbUri="...",
                    verbEnglish="sees",
                    objectUri="...",
                    objectName="front yard motion",
                    objectIcon="/magma/static/frontYardMotion.png")
                recent['frontDoorMotion'] = kw
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
            (r'/inputChange', InputChange),
            (r'/activity', Activity),
            (r'/graph', GraphHandler),
        ]
        settings = {
            'mongo' : Connection('bang', 27017,
                                 tz_aware=True)['house']['sensor'],
            'history' : {'lastMotion' : datetime.datetime.fromtimestamp(0, tzutc())},
            }
        cyclone.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    #log.startLogging(sys.stdout)
    reactor.listenTCP(9069, Application())
    reactor.run()
