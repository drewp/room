"""
listener to the POST messages sent by drv.py when a pin changes.
records interesting events to mongodb, sends further messages.

Will also serve activity stream.
"""
import sys, datetime, cyclone.web, simplejson
from twisted.python import log
from twisted.internet import reactor
from dateutil.tz import tzutc
from pymongo import Connection
sys.path.append("/my/site/magma")
from activitystream import ActivityStream

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.write("watchpins, writes to mongo db=house collection=sensor")

class PinChange(cyclone.web.RequestHandler):
    def post(self):
        msg = simplejson.loads(self.request.body)
        msg['t'] = datetime.datetime.now(tzutc())
        msg['name'] = {9: 'downstairsDoorOpen', 
                       10: 'downstairsDoorMotion',
                       }[msg['pin']]
        self.settings.mongo.insert(msg)

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
        ]
        settings = {
            'mongo' : Connection('bang', 27017, tz_aware=True)['house']['sensor']
            }
        cyclone.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    #log.startLogging(sys.stdout)
    reactor.listenTCP(9069, Application())
    reactor.run()
