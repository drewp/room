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
    for url, name in [("http://star:9014/", "ariroom"),
                      ("http://space:9080/", "frontDoor"),
                      ]:
        for tries in range(3):
            try:
                shiftweb = restkit.Resource(url, timeout=5)
                temp = jsonlib.read(shiftweb.get("temperature").body_string(), 
                                    use_float=True)['temp']
                log.info("write %s temp %r", name, temp)
                carbon.send('system.house.temp.%s' % name, temp, now)
                log.debug("wrote to carbon")
                break
            except Exception, e:
                log.warn(e)

LoopingCall(update).start(interval=120)
reactor.run()
