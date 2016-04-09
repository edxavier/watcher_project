import datetime

__author__ = 'edx'
from snmp_requests import get_request, get_bulk_request
from helpers import get_num_entries, get_matrix_data, get_data_reordered
from dictionary import OIDS, DEVICE_STATUS
from web_methods import HttpHelper

UPTIME = '1.3.6.1.2.1.25.1.1.0'
UPTIME2 = '1.3.6.1.2.1.1.3.0'
DESC = '1.3.6.1.2.1.1.1.0'
SERVICES = '1.3.6.1.2.1.1.7.0'
SYS_NAME = '1.3.6.1.2.1.1.5.0'
PROCESSES = '1.3.6.1.2.1.25.1.6.0'
USERS = '1.3.6.1.2.1.25.1.5.0'
SYS_DATE = '1.3.6.1.2.1.25.1.2.0'

class System:

    def __init__(self, address="127.0.0.1", initialize=True):
        self.initialized = initialize
        self.address = address
        if initialize:
            result = get_bulk_request(max_result=7, start_oid="1.3.6.1.2.1.1.1", address=address)
            result2 = get_bulk_request(max_result=7, start_oid="1.3.6.1.2.1.25.1.1", address=address)
            self.upTime = int(result2[0])/100
            self.description = result[0]
            self.services = result[6]
            self.processes = result2[5]
            self.users = result2[4]
            self.sysName = result[4]
        else:
            self.upTime = None
            self.description = None
            self.services = None
            self.processes = None
            self.users = None
            self.sysName = None
        # self.sysDate = get_request(destino=address, mib_oid=SYS_DATE)

    def get_hostname(self):
        return get_request(destino=self.address, mib_oid=SYS_NAME)

    def get_uptime_agent(self):
        return get_request(destino=self.address, mib_oid=UPTIME)

    def get_uptime_sys(self):
        return get_request(destino=self.address, mib_oid=UPTIME2)

    def get_storages(self, session):
        result = get_bulk_request(max_result=600, address=self.address, start_oid="1.3.6.1.2.1.25.2.3.1")
        n = get_num_entries(result)
        table = get_matrix_data(result, 7, n)
        result = get_data_reordered(table)
        for maped in result:
            storage = {'index':maped[0], 'type': OIDS[maped[1]], 'description': maped[2]}
            #las unidades de almacenamiento se registran en bytes, y el size en numero de allocationsunits
            allocationsUnits = float(maped[3])
            size = float(maped[4])
            used = float(maped[5])
            # un MB tiene 1048576 bytes
            a_MB = 1048576
            storage['size'] = int((size * allocationsUnits) / a_MB)
            storage['used'] = int((used * allocationsUnits) / a_MB)
            storage['allocation_failures'] = int(maped[6])
            storage['direccion'] = self.address
            session.http_post("/gestion/storages/", storage)

    def get_devices(self, session):
        result = get_bulk_request(max_result=600, address=self.address, start_oid="1.3.6.1.2.1.25.3.2.1")
        n = get_num_entries(result)
        table = get_matrix_data(result, 6, n)
        result = get_data_reordered(table)
        for maped in result:
            device = {'index':maped[0], 'type': OIDS[maped[1]], 'description': maped[2]}
            #las unidades de almacenamiento se registran en bytes, y el size en numero de allocationsunits
            status = float(maped[4])
            errors = float(maped[5])
            device['status'] = DEVICE_STATUS[int(status)]
            device['errors'] = int(errors)
            device['direccion'] = self.address
            session.http_post("/gestion/devices/", device)
            #print(res.text)

    def get_memory(self, session):
        result = get_bulk_request(max_result=4, address=self.address, start_oid="1.3.6.1.4.1.2021.4.3")
        mems = {'total_swap': int(result[0]) / 1024, 'free_swap': int(result[1]) / 1024}
        tr = int(result[2]) / 1024
        fr = int(result[3]) / 1024
        mems['total_ram'] = tr
        mems['free_ram'] = fr
        mems['direccion'] = self.address
        percent_free = (fr * 100) / tr
        if percent_free < 10:
            mems['mem_alarm'] = True
            print(self.address + " RAM Alarm " + datetime.datetime.now().strftime("%d-%b-%y %H:%M"))
        else:
            mems['mem_alarm'] = False
        session.http_post("/gestion/memory/", mems)

    def get_load(self, session):
        result = get_bulk_request(max_result=18, address=self.address, start_oid="1.3.6.1.4.1.2021.10.1.3")
        loads = {'load1': result[0], 'load5': result[1], 'load15': result[2], 'threshold1': result[3],
                 'threshold5': result[4], 'threshold15': result[5], 'flag1': result[12], 'flag5': result[13],
                 'flag15': result[14], 'msg1': result[15], 'msg5': result[16], 'msg15': result[17],
                 'direccion': self.address}
        session.http_post("/gestion/load_avg/", loads)
        #print(loads)

    def get_disk(self, session):
        result = get_bulk_request(max_result=60, address=self.address, start_oid="1.3.6.1.4.1.2021.9.1.1")
        n = get_num_entries(result)
        table = get_matrix_data(result, 12, n)
        result = get_data_reordered(table)
        for map in result:
            size = int(map[5]) / 1024
            used = int(map[7]) / 1024
            disk = {'path': map[1], 'device': map[2], 'min_free': map[4], 'size': size, 'used': used,
                    'percent_used': map[8], 'flag': map[10], 'msg': map[11], 'direccion': self.address}
            session.http_post("/gestion/disk/", disk)

    def get_procs(self, session):
        result = get_bulk_request(max_result=500, address=self.address, start_oid="1.3.6.1.4.1.2021.2.1")
        n = get_num_entries(result)
        table = get_matrix_data(result, 9, n)
        result = get_data_reordered(table)
        if int(result[0][0]) > 0:
            for map in result:
                proc = {'index':map[0], 'name': map[1], 'min': map[2], 'max': map[3],
                        'count': map[4], 'flag': map[5], 'msg': map[6],'direccion': self.address}
                session.http_post("/gestion/process/", proc)


