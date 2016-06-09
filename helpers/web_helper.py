import logging

from helpers.funtions_utils import get_logger_handler

__author__ = 'edx'
#import requests
import urllib, urllib2

"""class HttpHelper(object):
    def __init__(self, server_addr="127.0.0.1", server_port=443, url="/"):
        self.addr = server_addr
        self.port = server_port
        self.url = url
        #Crear un objeto que preserve la sesion
        self.cli = requests.session()
        super(HttpHelper, self).__init__()

    def http_login(self, user="", password=""):
        self.cli.get('http://' + self.addr + ':'+str(self.port) + '/login/', verify=False)
        login_data = dict(username=user, password=password, csrfmiddlewaretoken=self.cli.cookies['csrftoken'])
        try:
            r = self.cli.post('http://' + self.addr + ':' + str(self.port) + '/login/', data=login_data, verify=False)
            if r.status_code == 200:
                return True
            else:
                return False
        except Exception, e:
            print(e.message)
            print("ERROR")


    def http_logout(self,):
        r = self.cli.get('http://'+self.addr+':'+str(self.port)+'/logout/',  verify=False)
        if r.status_code == 200:
            return True
        else:
            return False

    def http_get(self, url="/"):
        self.url = url
        res = self.cli.get('http://'+self.addr+':'+str(self.port)+self.url,  verify=False)
        return res

    def http_post(self, url="/", data=None):
        self.url = url
        res = self.cli.post('http://' + self.addr + ':' + str(self.port) + self.url, data, verify=False)
        return res

"""
"""
r = requests.get('http://127.0.0.1:8000/login', auth=('edx', 'edx'))
print r.status_code
print r.headers['content-type']
print r.encoding

r = requests.get('http://127.0.0.1:8000/api/gestion/hosts/')
print r.status_code
print r.headers['content-type']
print r.encoding
print(r.json())
exit()
"""


class UrlibHttpHelper(object):
    def __init__(self, addr="127.0.0.1", port=80):
        self.wadrr = addr
        self.wport = port
        handler = get_logger_handler()
        #logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(handler)

    def do_post(self, url="/", data=None):
        try:
            straddr = self.wadrr
            strPort = str(self.wport)
            wurl = 'http://' + straddr + ':' + strPort + url
            data_dic = urllib.urlencode(data)
            u = urllib.urlopen(wurl, data_dic)
            return u
        except Exception, e:
            self.logger.error("No se pudo relizar el post para la url: " + url)
            return None

    def do_get(self, url="/"):
        try:
            straddr = self.wadrr
            strPort = str(self.wport)
            wurl = 'http://' + straddr + ':' + strPort + url
            u = urllib.urlopen(wurl)
            return u.read()
        except Exception, e:
            self.logger.error("No se pudo relizar el get para la url: " + url)
            return None

    def do_put(self, url="/", data=None):
        try:
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            straddr = self.wadrr
            strPort = str(self.wport)
            wurl = 'http://' + straddr + ':' + strPort + url
            data_dic = urllib.urlencode(data)
            request = urllib2.Request(wurl, data=data_dic)
            #request.add_header('Content-Type', 'application/json')
            request.get_method = lambda: 'PUT'
            url = opener.open(request)
            return url
        except Exception, e:
            self.logger.error("No se pudo relizar el PUT para la url: " + url)
            return None
