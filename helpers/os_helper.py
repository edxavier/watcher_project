import logging
import subprocess
from datetime import timedelta
import datetime
from helpers.funtions_utils import clear_multiple_spaces, get_logger_handler, get_pos, get_ip_address
from helpers.ntp_helper import Pysntp
from subprocess import Popen, PIPE

class OSHelper(object):

    def __init__(self):
        handler = get_logger_handler()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(handler)

    def get_ram_values(self):
        """Retorna dvalores de memoria RAM"""
        try:
            s = Popen(['free', '-m'], stdout=PIPE).communicate()[0]
            line = s.split('\n')[1]
            line = clear_multiple_spaces(line)
            ram = line.split()
            total_ram = float(ram[1])
            used_ram = float(ram[2])
            free_ram = float(ram[3])
            used_ram_percent = (used_ram / total_ram) * 100

            s = Popen(['ps', '-eo', '%mem,comm', '--sort', '%mem'], stdout=PIPE).communicate()[0]
            top_proc = s.split('\n')[-2].rstrip('\n').rstrip('\r')
            proc_pmem = top_proc.split()[0]
            proc_name = top_proc.split()[1]
            return int(total_ram), int(used_ram), int(free_ram), used_ram_percent, proc_name, proc_pmem
        except Exception, e:
            self.logger.error("Error obteniendo RAM...")
            return 0, 0, 0, 0, 0, 0

    def get_sys_uptime(self):
        """Retorna el tiempo de ejecucuion del sistema operativo"""
        try:
            s = Popen(['cat', '/proc/uptime'], stdout=PIPE).communicate()[0]
            line = clear_multiple_spaces(s)
            uptime_seconds = float(str(line).split()[0])
            uptime_string = str(timedelta(seconds=uptime_seconds))
            return uptime_string.split('.')[0], uptime_seconds
        except Exception, e:
            self.logger.error("Error: obteniendo Uptime... " + e.message)
            return None

    def get_cpu_usage(self):
        """Retorna el procetanje de uso de la cpu"""
        try:
            s = Popen(['ps', '-eo', '%cpu,comm', '--sort', '%cpu'], stdout=PIPE).communicate()[0]
            pcpu = 0.0
            top_proc = s.split('\n')[-2].rstrip('\n').rstrip('\r')
            for line in s.split('\n'):
                try:
                    pcpu += float(line.split()[0])
                except Exception, e:
                    pass
                    #self.logger.error(e.message)

            proc_pcpu = top_proc.split()[0]
            proc_name = top_proc.split()[1]
            return {'pcpu': pcpu, 'proc_name': proc_name, 'proc_pcpu': proc_pcpu}
        except Exception, e:
            self.logger.error("Error: CPU usage... " + e.message)

    def get_cpu_load_avg(self):
        """Retorna numero de nucleos, procesos y load5, load15"""
        try:
            cores = Popen(['grep', '--count', '^processor', '/proc/cpuinfo'], stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
            loads = Popen(['cat', '/proc/loadavg'], stdout=PIPE).communicate()[0]
            load5 = loads.split(' ')[1]
            load15 = loads.split(' ')[2]
            procs = loads.split(' ')[3].split('/')[1]
            return {'cores': cores, 'procs': procs, 'load5': load5, 'load15': load15}
        except Exception, e:
            self.logger.error("Error: CPU load..." + e.message)


    def get_partition_usage(self, partition="/"):
        """Retorna uso de almacenamiento de particion"""
        try:
            usage = Popen(['df', '-m', partition], stdout=PIPE).communicate()[0].split('\n')
            if len(usage) == 3:
                usage = usage[1].split()[4].split('%')[0]
            else:
                usage = clear_multiple_spaces(usage[2]).split()[3].split('%')[0]
            return usage, partition
        except Exception, e:
            self.logger.error("Error: partition Usage... ")


    def get_sync_state(self, server="127.0.0.1"):
        """Retorna la diferiencia en segundo respecto a un servidor NTP"""
        try:
            date = Popen(['date', "+%Y-%m-%d %H:%M:%S %Z"], stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
            sntp = Pysntp(direccion=server)
            local = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S %Z')
            sntp_time = sntp.get_time()
            sec = None
            if sntp_time:
                dif = local - sntp_time
                sec = dif.total_seconds()
            return sec
        except Exception, e:
            self.logger.error("Error: Sync check... "+ e.message)
            return None


    def get_sys_info(self, ifname):
        data = Popen(['uname', '-snrmpio'], stdout=PIPE).communicate()[0].strip('\n').strip('\r').split()
        os_version = Popen(['uname', '-v'], stdout=PIPE).communicate()[0].strip('\n').strip('\r').split()[0]
        cpu_info = Popen(['grep', 'name', '/proc/cpuinfo'], stdout=PIPE).communicate()[0].split('\n')[0].split(':')[1].strip()
        ram = self.get_ram_values()
        cores = Popen(['grep', '--count', '^processor', '/proc/cpuinfo'], stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        try:
            ip = get_ip_address(ifname)
        except:
            ip = "127.0.0.1"
        position = get_pos()

        return {'os_version': os_version, 'kernel': data[0], 'hostname': data[1], 'k_release': data[2], 'processor': data[4], 'platform': data[5], 'os': data[6], 'pos': position, 'cpu_model': cpu_info, 'ip': ip, 'ram': ram[0], 'cores': cores}
