import time
from time import mktime
import logging
import subprocess
from datetime import timedelta
import datetime
from helpers.funtions_utils import clear_multiple_spaces, get_logger_handler, get_pos, get_ip_address
from helpers.ntp_helper import Pysntp
from subprocess import Popen, PIPE
import os

class OSHelper(object):

    def __init__(self):
        handler = get_logger_handler()
        #logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

            #s = Popen(['ps', '-eo', '%mem,comm', '--sort', '%mem'], stdout=PIPE).communicate()[0]
            s2 = Popen('ps -eo %mem,comm | sort -k 1 -r', stdin=PIPE, shell=True, stdout=PIPE).communicate()[0]
            """ el comando anterior produce una salida similar a esta:
                %MEM COMMAND
                 1.3 chrome
                 1.3 atom
                 1.7 deepin-terminal
            """
            outputs = s2.split('\n')
            proc_pmem = 0.0
            proc_name = ""
            #Recorrer el resultado desde el segundo resultado hasta el penultimo,
            #ya que el primero son nombres de columnas y el ultimo es vacio
            for output in outputs[1:-1]:
                tpr = float(output.rstrip('\n').rstrip('\r').split()[0])
                if (tpr > proc_pmem):
                    proc_pmem = tpr
                    proc_name = output.rstrip('\n').rstrip('\r').split()[1]

            #top_proc = s.split('\n')[-2].rstrip('\n').rstrip('\r')
            #proc_pmem = top_proc.split()[0]
            #proc_name = top_proc.split()[1]
            return int(total_ram), int(used_ram), int(free_ram), used_ram_percent, proc_name, proc_pmem
        except Exception, e:
            self.logger.error("Error obteniendo RAM...", exc_info=True)
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
            self.logger.error("Error: obteniendo Uptime... ")
            return None

    def get_cpu_usage(self):
        """Retorna el procetanje de uso de la cpu"""
        try:
            cores = Popen(['grep', '--count', '^processor', '/proc/cpuinfo'], stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
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
            pcpu = float(pcpu/float(cores))
            #divido el total entre todas las cpu para calcular el uso global
            #el % de el proceso corresponde al uso de un cpu no global
            return {'pcpu': pcpu, 'proc_name': proc_name, 'proc_pcpu': proc_pcpu}
        except Exception, e:
            self.logger.error("Error: CPU usage... ")

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
            self.logger.error("Error: CPU load...")


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


    def get_sync_state(self, server="10.160.80.205"):
        """Retorna la diferiencia en segundo respecto a un servidor NTP"""
        try:
            date = Popen(['date', "+%Y-%m-%d %H:%M:%S %Z"], stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
	    sntp = Pysntp(direccion=server)
	#local = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S %Z')
            local = datetime.datetime(*time.strptime(date, '%Y-%m-%d %H:%M:%S %Z')[:6])
            sntp_time = sntp.get_time()

            sec = None
            if sntp_time:
                dif = mktime(local.timetuple()) - mktime(sntp_time.timetuple())
                sec = dif
            return sec
        except Exception, e:
            self.logger.error("Error: Sync check... ")
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

    def get_hp_health(self):

        try:
            fans = Popen(['hpasmcli', '-s','show fan'], stdout=PIPE).communicate()[0].replace('\n','<br>')
            fans = ' '.join(fans.split()).replace(' ',' | ')
            temperature = Popen(['hplog', '-t'], stdout=PIPE).communicate()[0].replace('\n','<br>')
            temperature = ' '.join(temperature.split()).replace('Normal','| <strong>Normal</strong> |')
            temperature = temperature.replace('Basic Sensor','| Basic Sensor |')
            power_suply = Popen(['hpasmcli', '-s','show powersupply'], stdout=PIPE).communicate()[0].replace('\n','<br>')
            dimms = Popen(['hpasmcli', '-s','show dimm'], stdout=PIPE).communicate()[0].replace('\n','<br>')
            server_desc = Popen(['hpasmcli', '-s','show server'], stdout=PIPE).communicate()[0].replace('\n','<br>')
            #raid = Popen('/root/hp.sh', stdout=PIPE).communicate()[0].replace('\n','<br>')
            raid = Popen(['hpacucli', 'controller','slot=0','ld','all','show', 'detail'], stdout=PIPE).communicate()[0].replace('\n','<br>')
            raid += Popen(['hpacucli', 'controller','slot=0','pd','all','show', 'detail'], stdout=PIPE).communicate()[0].replace('\n','<br>')
            #raid =  Popen(' hpacucli ctrl slot=0 pd all show detail', stdin=PIPE, shel l=False, stdout=PIPE).communicate()[0].replace('\n','<br>')
            #print raid
            #temperature = Popen('hpasmcli -s "show temp" ', stdin=PIPE, shell=False, stdout=PIPE).communicate()[0]
            #power_suply = Popen('hpasmcli -s "show powersuply" ', stdin=PIPE, shell=False, stdout=PIPE).communicate()[0]
            #print fans
            return fans, temperature, power_suply, dimms, server_desc, raid
        except:
            #self.logger.warning("hp_health error...")
            return "No disponible", "No disponible", "No disponible","No disponible","No disponible","No disponible"

    def hp_health_values(self):
        #print "VALUES hp_health"
        #temp_ambient = Popen("hplog -t | grep Ambient | awk '{print $7}'", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')[:-1]
        temp_total = Popen("hplog -t | tail -n +2 | head -n -1 | wc -l", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        temp_normal = Popen("hplog -t | tail -n +2 | head -n -1 | grep -c Normal", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        if int(temp_total) > int(temp_normal):
            temp_stat = "WRN"
        else:
            temp_stat = "OK"

        fans_total = Popen("hplog -f | tail -n +2 | head -n -1 | wc -l", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        fans_normal = Popen("hplog -f | tail -n +2 | head -n -1 | grep -c Normal", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')

        if int(fans_total) > int(fans_normal):
            fans_stat = "F"
        else:
            fans_stat = "OK"

        pwr_total = Popen("hplog -p | tail -n +2 | head -n -1 | wc -l", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        pwr_normal = Popen("hplog -p | tail -n +2 | head -n -1 | grep -c Normal", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        if int(pwr_total) > int(pwr_normal):
            pwr_stat = "F"
        else:
            pwr_stat = "OK"

        dimm_total = Popen("hpasmcli -s 'show dimm' | grep -c Status", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        dimm_normal = Popen("hpasmcli -s 'show dimm' | grep Status | grep -c Ok", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        if int(dimm_total) > int(dimm_normal):
            dimm_stat = "F"
        else:
            dimm_stat = "OK"

        proc_total = Popen("hpasmcli -s 'show server' | grep -c Status", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        proc_normal = Popen("hpasmcli -s 'show server' | grep Status | grep -c Ok", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        if int(proc_total) > int(proc_normal):
            proc_stat = "F"
        else:
            proc_stat = "OK"

        ld_total = Popen("hpacucli ctrl slot=0 ld all show | grep -c logical", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        ld_normal = Popen("hpacucli ctrl slot=0 ld all show | grep -c OK", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        if int(ld_total) > int(ld_normal):
            ld_stat = "F"
        else:
            ld_stat = "OK"

        pd_total = Popen("hpacucli ctrl slot=0 pd all show | grep -c physical", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        pd_normal = Popen("hpacucli ctrl slot=0 pd all show | grep -c OK", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        if int(pd_total) > int(pd_normal):
            pd_stat = "F"
        else:
            pd_stat = "OK"

        return temp_stat,fans_stat,pwr_stat,dimm_stat,proc_stat,ld_stat,pd_stat
