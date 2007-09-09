from fcntl import ioctl
import os, struct
import hubclient

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
