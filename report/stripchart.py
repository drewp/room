from __future__ import division
import time
from nevow import tags as T, rend, loaders
from datetime import date, datetime, time as datetime_time, timedelta

class Events(object):
    """collection of timeseries events"""
    def __init__(self, events):
        """takes list of (start, end, {label:...}) tuples.
        Times are unix seconds.

        Use end=None for one-shot events
        """
        self.tuples = events
        times = [s for s,e,d in self.tuples] + [e for s,e,d in self.tuples
                                                if e is not None]
        self.minTime = min(times) if times else 0
        self.maxTime = max(times) if times else 1

    def __iter__(self):
        return iter(self.tuples)


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


class Chart(rend.Page):
    addSlash = True
    docFactory = loaders.stan(T.html[
        T.head[
        T.link(rel="stylesheet", href="../www/hours.css", type='text/css')
        ],
        T.body[T.directive("timeline"),
               T.directive("table")]
        ])

    def render_timeline(self, ctx, data):
        events = self.getData(ctx)

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
            dt = dxTime(100)
            assert dt > 0
            t += dt

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
                         style=style)[evDict.get('state', evDict.get('marker'))]
        
        for ev in events:
            x1 = xPx(ev[0])
            if ev[1] is not None:
                x2 = xPx(ev[1])
            else:
                x2 = x1 + 30
            pts.append(backgroundRect(ev[2], x1, x2))
            pts.append(labelDiv(ev[2], x1, x2, row))
            row = (row + 1) % 3

        upperHalf = T.div(style="position: relative; overflow: hidden; width: %spx; height: 50px" % widthPx)[pts]

        return T.div[
            self.title,
            T.div(class_="timeline-outer")[upperHalf, lowerHalf]]
    
    def render_table(self, ctx, data):
        events = self.getData(ctx)

        rows = {} # (mintime,maxtime) : bands
        startHour = 7
        for r in dayRanges(date.fromtimestamp(events.minTime),
                           date.fromtimestamp(events.maxTime),
                           startHour=startHour):
            rows[r] = []

        for ev in events.tuples:
            for r in rows:
                i = intersect((ev[0], ev[1]), (r[0], r[1]))
                if i is not None:
                    rows[r].append((i[0], i[1], ev[2]))
            
        def clearPixel(w=1,h=1):
            return T.img(src="../www/clear.png", width=w, height=h)

        def makeTick(startSec, endSec, state, style='', class_=''):
            widthSec = (endSec - startSec)
            color = dict(Off='#555', On='#ffa', Suspend='#775',
                         Standby='#dca').get(state)
            if color is not None:
                color = 'background: %s; ' % color
            else:
                color = ''
                     
            return T.div(class_="abs %s" % class_,
                     style="%s left: %.2f%%; width: %.2f%%; %s" % (
                color,
                100 * startSec / 86400,
                100 * widthSec / 86400,
                style))[state]

        trs = []
        for row, bands in sorted(rows.items()):
            ticks = []

            for (startSec, endSec, state) in sorted(bands):
                if endSec is not None:
                    ticks.append(makeTick(startSec - row[0], endSec - row[0],
                                          state['state']))
                else:
                    ticks.append(makeTick(startSec - row[0],
                                          startSec - row[0] + 3600,
                                          state=state['marker']))

            for hr in range(24):
                ticks.append(makeTick(3600 * hr, 3600 * hr + 3200,
                                      str((hr + startHour) % 24),
                                      class_='hour'))
                
            d = date.fromtimestamp(row[0])
            rowColor = "#e8e8e8"
            if d.weekday() in (5,6):
                rowColor = "#e8cccc"
            trs.append(T.tr[
                T.td(style="background: %s;" % rowColor)[
                  T.div(class_="dayLabel")["%s %s" %
                                           (d.strftime("%A")[:2], str(d))]],
                T.td(width="100%", style="background: %s;" % rowColor)[
                  T.div(class_="tdContents")[ticks]],
                ])
        
        return T.table(width="100%")[trs]

def dayRanges(d1, d2, periodHours=24, startHour=0):
    """
    list of (start,end) in unix seconds that covers N-hour periods
    aligned to startHour in your local time zone

    >>> from pprint import pprint
    >>> rgs = dayRanges(date(2008,1,5), date(2008,1,7), startHour=7)
    >>> pprint([[str(datetime.fromtimestamp(x)) for x in r] for r in rgs])
    [['2008-01-05 07:00:00', '2008-01-06 06:59:59'],
     ['2008-01-06 07:00:00', '2008-01-07 06:59:59'],
     ['2008-01-07 07:00:00', '2008-01-08 06:59:59']]
    """
    ret = []
    t1 = datetime.combine(d1, datetime_time(startHour, 0, 0))
    while t1 < datetime.combine(d2, datetime_time(23,59,59)):
        t2 = t1 + timedelta(hours=periodHours) - timedelta.resolution
        ret.append((time.mktime(t1.timetuple()),
                    time.mktime(t2.timetuple())))
        t1 = t1 + timedelta(hours=periodHours)
    return ret

def intersect(range1, range2):
    """return None, or a new (start,end) range for the intersection
    clipped to range2. doesn't return start==end (maybe unless range2
    was like that)

    supports endTime=None on range1, for one-shot events

    >>> intersect((1, 5), (10, 20))
    >>> intersect((1, 10), (10, 20))
    >>> intersect((1, 15), (10, 20))
    (10, 15)
    >>> intersect((10, 15), (10, 20))
    (10, 15)
    >>> intersect((12, 18), (10, 20))
    (12, 18)
    >>> intersect((5, 25), (10, 20))
    (10, 20)
    >>> intersect((12, 20), (10, 20))
    (12, 20)
    >>> intersect((15, 25), (10, 20))
    (15, 20)
    >>> intersect((20, 25), (10, 20))
    >>> intersect((21, 25), (10, 20))

    >>> intersect((1, None), (10, 20))
    >>> intersect((12, None), (10, 20))
    (12, None)
    >>> intersect((10, None), (10, 20))
    (10, None)
    >>> intersect((20, None), (10, 20))
    (20, None)
    >>> intersect((22, None), (10, 20))
    
    """
    oneshot = False
    x1,x2 = range1
    if x2 is None:
        x2 = x1
        oneshot = True
    y1,y2 = range2
    if x1 >= y1 and x2 <= y2:
        ret = (x1, x2)
    elif y1 < x2 <= y2:
        ret = (y1, x2)
    elif y1 <= x1 < y2:
        ret = (x1, y2)
    elif x1 <= y1 and x2 >= y2:
        ret = (y1, y2)
    else:
        return None
    if oneshot:
        return ret[0], None
    return ret

if __name__ == '__main__':
    import doctest
    doctest.testmod()
