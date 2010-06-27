#!/usr/bin/python
from carbondata import CarbonClient
import restkit, jsonlib, logging, time
from logsetup import commonlogsetup

log = commonlogsetup(filename=None)
log.setLevel(logging.INFO)

carbon = CarbonClient(serverHost='bang')

while True:
    now = time.time()
    nextRead = now + 120
    try:
        shiftweb = restkit.Resource("http://plus:9014/")
        temp = jsonlib.load(shiftweb.get("temperature").body)['temp']
        carbon.send('system.house.temp.ariroom', temp, now)
    except restkit.RequestError, e:
        log.warn(e)
    time.sleep(max(0, nextRead - time.time()))
