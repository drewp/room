#!/usr/bin/python
from __future__ import division
import time
from stripchart import Events, Chart

def dpmsEvents():
    events = [] # [(start, end, {label:...}), ...]

    currentEvent = None
    # assumes log is in order
    for line in open("log.dpms"):
        secs, state = line.strip().split()

        if currentEvent is not None:
            events.append((currentEvent[0], float(secs), currentEvent[2]))

        currentEvent = (float(secs), None,
                        dict(state=state, cssClass="state-%s state" % state))

    if currentEvent is not None:
        events.append((currentEvent[0], time.time(), currentEvent[2]))
    return Events(events)

class DpmsChart(Chart):
    title = "DPMS power events"
    def getData(self, ctx):
        return dpmsEvents()
