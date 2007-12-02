from fcntl import ioctl
import os, struct

IOPWRITE = 2
class SolarisParport(object):
    """alternate implementation of an ieee1294.Port

    where you might use this elsewhere:
        import ieee1284
        ports = ieee1284.find_ports()
        port = ports['0x3bc']
        port.open()
        
    ..this version seems to work on solaris x86:
        port = SolarisParport(port=0x3bc)
        port.open()
    
    """
    def __init__(self, file='/devices/pseudo/iop@0:iop', port=0x3bc):
        self.file, self.port = file, port

    def open(self):
        self.fd = os.open(self.file, os.O_RDWR)
        return "capabilities return value not implemented"

    def write_data(self, value):
        ioctl(self.fd, IOPWRITE, self._iopbuf_struct(self.port, value))
        
    def _iopbuf_struct(self, port, port_value):
        return struct.pack('IB', port, port_value)

# see also http://www.captain.at/programming/solaris/ for the structs,
# IOP constants


# not working yet
class Usbprn(object):
    """a solaris parallel port on usb"""
    def __init__(self, file="/dev/printers/0"):
        self.file = file

    def open(self):
        print "opening - sun hangs here"
        self.fd = os.open(self.file, os.O_RDWR)
        print "opened"
        return "capabilities return value not implemented"

    def write_data(self, value):
        print "writing"
        os.write(self.fd, chr(value))
        print "wrote"

class LinuxUsbParallel(object):
    def __init__(self, file="/dev/usblp1"):
        self.file = file

    def open(self):
         self.fd = os.open(self.file, os.O_RDWR)

    def write_data(self, value):
        print "writing"
        os.write(self.fd, chr(value))
        print "wrote"

class LinuxParallel(object):
    def __init__(self, port=0):
        self.portNum = port

    def open(self):
        import parallel
        self.port = parallel.Parallel(port=self.portNum)
        self.device = self.port.device

    def write_data(self, value):
        self.port.setData(value)
        
        

if __name__ == '__main__':
    p = LinuxUsbParallel()
    p.open()
    import time
    while 1:
        print "hi"
        p.write_data(255)
        time.sleep(1)
        print "lo"
        p.write_data(0)
        time.sleep(1)
        
