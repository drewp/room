#!/usr/bin/python
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
import restkit, jsonlib, logging, time, socket
from logsetup import commonlogsetup
from carbondata import CarbonClient

log = commonlogsetup(filename=None)
log.setLevel(logging.WARN)

carbon = CarbonClient(serverHost='bang')

def update():
    now = time.time()
    try:
        shiftweb = restkit.Resource("http://star:9014/", timeout=5)
        temp = jsonlib.read(shiftweb.get("temperature").body_string(), use_float=True)['temp']
        log.info("write temp %r" % temp)
        carbon.send('system.house.temp.ariroom', temp, now)
        log.debug("wrote to carbon")
    except (restkit.RequestError, socket.error), e:
        log.warn(e)
update()
LoopingCall(update).start(interval=120)
reactor.run()
