from twisted.internet import reactor
from twisted.spread import pb
from louie import dispatcher
import logging
log = logging.getLogger()

_root = None

class LocalSignal(pb.Referenceable):
    def remote_send(self, **kw):
        log.debug("received signal %r from hub", kw['signal'])
    
        # see below for the reason for this translation
        kw2 = {}
        for k,v in kw.items():
            if v == (None, "Anonymous"):
                v = dispatcher.Anonymous
            kw2[k] = v

        dispatcher.send(_remoteSignal=True, **kw)


_localSignal = LocalSignal()

def connect(host="slash", port=2012):
    global _root
    fact = pb.PBClientFactory()
    reactor.connectTCP(host, port, fact)
    _root = fact.getRootObject()
    def reg(r):
        r.callRemote("addClient", _localSignal)
        return r
    _root.addCallback(reg)

def listenAll(sender=None, **kw):
    #kw['sender'] = sender

    if kw.get('_remoteSignal', False):
        log.debug("not retransmitting remote signal")
        return
        
    log.debug("send away %r", kw)

    # this dumb Anonymous handling is because i can't figure out pb's
    # jelly stuff. What i want is to say that dispatcher.Anonymous can
    # be transmitted, and that the transmission is just the type name
    if sender is dispatcher.Anonymous:
        sender = (None, "Anonymous")
    kw2 = {'sender': sender}
    for k,v in kw.items():
        if v is dispatcher.Anonymous:
            v = (None, "Anonymous")
        kw2[k] = v
    
    def cr(r, kw):
        r.callRemote("send", _localSignal, **kw)
        return r
    _root.addCallback(cr, kw2)
dispatcher.connect(listenAll)




                
