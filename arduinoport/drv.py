"""
arduino example sketches, 'StandardFirmata'.

####easy_install http://github.com/lupeke/python-firmata/tarball/master

Now using http://code.google.com/p/pyduino, modified to run at 57600
baud like my arduino's code does. pyduino is better than the lupeke
one in that you can read your settings off the output pins
"""

import sys, web
from web.contrib.template import render_genshi
render = render_genshi('.', auto_reload=True)

sys.path.append("pyduino-read-only")
import pyduino 

def _num(name):
    if name.startswith('d'):
        return int(name[1:])
    raise ValueError(name)

class pin(object):
    def GET(self, name):
        web.header("Content-Type", "text/plain")
        arduino.iterate()
        return str(arduino.digital[_num(name)].read())

    def PUT(self, name):
        arduino.digital[_num(name)].write(int(web.data()))
        return ""

class pinMode(object):
    def GET(self, name):
        web.header("Content-Type", "text/plain")
        mode = arduino.digital[_num(name)].get_mode()
        return {pyduino.DIGITAL_INPUT : "input",
                pyduino.DIGITAL_OUTPUT : "output"}[mode]
    
    def PUT(self, name):
        mode = {
            "input" : pyduino.DIGITAL_INPUT,
            "output" : pyduino.DIGITAL_OUTPUT}[web.data().strip()]
        arduino.digital[_num(name)].set_mode(mode)
        return ""

class index(object):
    def GET(self):
        web.header("Content-Type", "application/xhtml+xml")
        return render.index()
    
urls = (r'/', "index",
        r'/pin/(.*)/mode', 'pinMode',
        r'/pin/(.*)', 'pin',
        # web refresh could benefit a lot from a json resource that
        # gives all the state
        )

arduino = pyduino.Arduino("/dev/ttyUSB0")

app = web.application(urls, globals())

def errorToUser():
    txt = str(sys.exc_info()[1])
    return web.webapi._InternalError(txt) 
app.internalerror = errorToUser

# ..cmdline opts to set pins to output at startup

if __name__ == '__main__':
    sys.argv.append("9056")
    app.run()
