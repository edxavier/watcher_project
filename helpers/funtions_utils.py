import filecmp
import logging
#import hashlib
import os
import socket
import fcntl
import struct
import subprocess
from subprocess import Popen, PIPE


def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])
    except:
        return "127.0.0.1"

def clear_multiple_spaces(text=""):
        return ' '.join(text.split())

def get_logger_handler():
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_file = os.path.join(BASE_DIR, 'logs.txt')
    handler = logging.FileHandler(logs_file)
    handler.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # add the handlers to the logger
    return handler

"""
def create_checksum(path):

    Reads in file. Creates checksum of file line by line.
    Returns complete checksum total for file.
    fp = open(path)
    checksum = hashlib.md5()
    while True:
        buffer = fp.read(8192)
        if not buffer:break
        checksum.update(buffer)
    checksum = checksum.digest()
    return checksum
"""

def compare_files(path1, path2):
    return filecmp.cmp(path1, path2)

def get_pos():
    try:
        #position = subprocess.check_output(['cat', '/root/pos']).strip('\n').strip('\r')
        position = Popen(['cat', '/root/pos'], stdout=PIPE).communicate()[0].strip('\n')
    except:
        position = "----"
    return position