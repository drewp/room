#!/usr/bin/python
from __future__ import division
from nevow import tags as T, flat, rend, loaders
from datetime import date, datetime

class Report(rend.Page):
    addSlash = True
    docFactory = loaders.stan(T.html[
        T.head[
        T.link(rel="stylesheet", href="../www/hours.css", type='text/css')
        ],
        T.body[T.directive("table")]
        ])
    def render_table(self, ctx, data):

        events = [] # [(start, end, {label:...}), ...]
        
        day = {} # date : times
        for line in open("log.dpms"):
            secs, state = line.strip().split()
            t = datetime.fromtimestamp(float(secs))
            d = t.date()
            dt = t.time()
            daySec = dt.hour * 3600 + dt.minute * 60 + dt.second
            day.setdefault(d, []).append((daySec, state))

        totals = {} # date : onsecs
        events = {} # date : [event]
        for d, states in sorted(day.items()):
            ticks = []
            total = 0
            startSec = None
            currentState = None
            for daySec, state in states:
                if currentState != None:
                    ticks.append((startSec, daySec, currentState))
                    total += (daySec - startSec)
                    
                currentState = state
                startSec = daySec
            if currentState:
                ticks.append((startSec, 86400, currentState))
                total += (86400 - startSec)
            events[d] = ticks
            totals[d] = total
            

        rows = []
        colWidth = 400

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
    

