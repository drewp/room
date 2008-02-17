#!/usr/bin/python
from __future__ import division
import time
from nevow import tags as T, flat, rend, loaders
from datetime import date, datetime

class Events(object):
    """collection of timeseries events"""
    def __init__(self, events):
        """takes list of (start, end, {label:...}) tuples"""
        self.tuples = events
        self.minTime = min(s for s,e,d in self.tuples)
        self.maxTime = max(e for s,e,d in self.tuples)

    def __iter__(self):
        return iter(self.tuples)
    
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


def differentSuffix(s1, s2, key=lambda x: x):
    """return the minimum suffix of sequence s1 that's
    different from s2"""
    ret = []
    writing = False
    for e1, e2 in zip(s1, s2):
        if key(e1) != key(e2):
            writing = True
        if writing:
            ret.append(e1)
    return ret


class Report(rend.Page):
    addSlash = True
    docFactory = loaders.stan(T.html[
        T.head[
        T.link(rel="stylesheet", href="../www/hours.css", type='text/css')
        ],
        T.body[T.directive("timeline")]
        ])

    def render_timeline(self, ctx, data):
        events = dpmsEvents()

        widthPx = 5000
        def xPx(t):
            return (widthPx * (t - events.minTime) /
                    (events.maxTime - events.minTime))
        def dxTime(px):
            return px * (events.maxTime - events.minTime) / widthPx

        line = T.div(class_="timeline-line", style="width: %spx" % widthPx)

        times = []

        class TimeTicks(object):
            def __init__(self, output):
                self.prevLabel = [None] * 3
                self.output = output

            def addTickAtTime(self, t):
                dt = datetime.fromtimestamp(t)
                label = [T.span(class_="date")[dt.strftime("%Y-")],
                         (T.span(class_="date")[dt.strftime("%m-%d")], T.br),
                         dt.strftime("%H:%M")]
                visibleLabel = differentSuffix(label, self.prevLabel, key=str)
                self.output.append(
                    T.div(class_="abs timeline-timeLabel",
                          style=("left: %spx; top: 50px; height: 50px;" %
                                 xPx(t)))[visibleLabel])
                self.prevLabel = label
            
        ticks = TimeTicks(times)
        
        t = events.minTime
        prevLabel = [None] * 3
        while t <= events.maxTime:
            ticks.addTickAtTime(t)
            t += dxTime(100)

        lowerHalf = T.div[line, times]

        pts = []
        row = 0

        def backgroundRect(evDict, x1, x2):
            style = "left: %spx; width: %spx; top: 0; height: 50px" % (
                x1, x2 - x1)
            return T.div(class_="abs rect-%s" % evDict.get('cssClass', ''),
                         style=style)

        def labelDiv(evDict, x1, x2, row):
            style = ("left: %spx; width: %spx; top: %sem; "
                     "bottom: 50px; overflow: visible; border-left: 1px solid black" %
                     (x1, x2 - x1, row * 1.1))
            return T.div(class_="abs %s" % evDict.get('cssClass', ''),
                         style=style)[evDict['state']]
        
        for ev in events:
            x1 = xPx(ev[0])
            x2 = xPx(ev[1])
            pts.append(backgroundRect(ev[2], x1, x2))
            pts.append(labelDiv(ev[2], x1, x2, row))
            row = (row + 1) % 3

        upperHalf = T.div(style="position: relative; overflow: hidden; width: %spx; height: 50px" % widthPx)[pts]
        
        return T.div[
            "DPMS power events:",
            T.div(class_="timeline-outer")[upperHalf, lowerHalf]]

    
    def render_table(self, ctx, data):

        events = dpmsEvents()

        print events

            

        rows = []

        def clearPixel(w=1,h=1):
            return T.img(src="../www/clear.png", width=w, height=h)

        def makeTick(startSec, daySec, state, style='', class_=''):
            widthSec = (daySec - startSec)
            color = dict(Off='#555', On='#ffa', Suspend='#cc8',
                         Standby='green').get(state, 'white')
                     
            return T.div(class_="abs %s" % class_,
                         style="background: %s; left: %.2f%%; width: %.2f%%; %s" % (
                color,
                100 * startSec / 86400,
                100 * widthSec / 86400,
                style))[state]
        
        for d, events in sorted(events.items()):
            ticks = []

            for (startSec, endSec, state) in events:
                ticks.append(makeTick(startSec, endSec, state))

            for hr in range(24):
                ticks.append(makeTick(3600 * hr, 3600 * hr + 3200, str(hr),
                                      class_='hour'))

            rowColor = "#e8e8e8"
            if d.weekday() in (5,6):
                rowColor = "#e8cccc"
            rows.append(T.tr[
                T.td(style="background: %s;" % rowColor)[
                  T.div(class_="dayLabel")[d.strftime("%A")[:2], " ", str(d)]],
                T.td(width="100%", style="background: %s;" % rowColor)[
                  T.div(class_="tdContents")[ticks]],
                ])
        
        return T.table(width="100%")[rows]
    

