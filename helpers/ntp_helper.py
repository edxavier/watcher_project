import socket

import struct
import datetime


class Pysntp(object):

    def __init__(self, direccion="127.0.0.1"):
        self._direccion = direccion


    def get_time(self):
        TIME1970 = 2208988800L
        # Thanks to F.Lundh
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(2)
        data = '\x1b' + 47 * '\0'
        client.sendto(data, (self._direccion, 123))
        #client.sendto(data, ('10.160.80.205', 123))

        try:
            data, address = client.recvfrom(1024)
            if data:
                t = struct.unpack('!12I', data)[10]
                t -= TIME1970
                utc_dt = datetime.datetime.utcfromtimestamp(t)
                return utc_dt
            else:
                return None
        except socket.timeout:
            return None

