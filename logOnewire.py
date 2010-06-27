#!/usr/bin/python
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
import restkit, jsonlib, logging, time
from logsetup import commonlogsetup
from carbondata import CarbonClient

log = commonlogsetup(filename=None)
log.setLevel(logging.DEBUG)

carbon = CarbonClient(serverHost='bang')

def update():
    now = time.time()
    try:
        shiftweb = restkit.Resource("http://plus:9014/", timeout=3)
        temp = jsonlib.read(shiftweb.get("temperature").body, use_float=True)['temp']
        log.info("write temp %r" % temp)
        carbon.send('system.house.temp.ariroom', temp, now)
        log.debug("wrote to carbon")
    except restkit.RequestError, e:
        log.warn(e)
update()
LoopingCall(update).start(interval=120)
reactor.run()
