#!/usr/bin/python
import logging, sys, os, shutil, platform
import time, threading, signal, sys
from helpers.web_helper import UrlibHttpHelper
from helpers.os_helper import OSHelper
from helpers.funtions_utils import get_ip_address, compare_files, get_logger_handler, get_pos
import ConfigParser
from datetime import datetime


from helpers.funtions_utils import clear_multiple_spaces
#import json
__author__ = 'edx'
""" Send HTTP msg periodically """
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANAGED_FILES_DIR = os.path.join(BASE_DIR, 'managed_files')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.ini')
#leer archivo de configuracion
config = ConfigParser.ConfigParser()
config.readfp(open(CONFIG_FILE))



SERVER_IP = config.get('NODEJS_SERVER', 'ip')
SERVER_PORT = config.get('NODEJS_SERVER', 'port')

DSERVER_IP = config.get('NGINX_SERVER', 'ip')
DSERVER_PORT = config.get('NGINX_SERVER', 'port')

RSCR_COLLECT_PERIOD = int(config.get('WATCHER', 'rscr_updates_period'))
RSCR_HIST_PERIOD = int(config.get('WATCHER', 'rscr_hist_period'))
PRESENCE_PERIOD = int(config.get('WATCHER', 'presence_period'))
FILE_CHANGE_THRESHOLD = int(config.get('WATCHER', 'file_chg_threshold'))
IFACE = config.get('WATCHER', 'local_iface')
NTP_SERVER = config.get('WATCHER', 'ntp_server')
ISVR = config.get('WATCHER', 'is_server')
SECTOR = config.get('WATCHER', 'sector')

IS_SERVER = False

if(ISVR == "True" ):
    IS_SERVER = True

#print IS_SERVER

handler = get_logger_handler()
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

IP = get_ip_address(IFACE)
HOSTNAME = platform.node()
POS = get_pos()


DB_ID = 0

logger.info("Iniciando ejecucion!")
#verificar que exist el directorio
try:
    os.stat(MANAGED_FILES_DIR)
except:
    # crear el directorio
    os.mkdir(MANAGED_FILES_DIR)


#web = HttpHelper(server_port=SERVER_PORT)
#servidor nodejs
web = UrlibHttpHelper(SERVER_IP, port=SERVER_PORT)
#servidor django
dweb = UrlibHttpHelper(DSERVER_IP, DSERVER_PORT)

sysHelper = OSHelper()

def watch_file(fpath):
    """Vigilar cambios en el archivo"""
    # verificar que es un archivo valido
    if os.path.isfile(fpath):
        fname = os.path.basename(fpath)
        mngfile = os.path.join(MANAGED_FILES_DIR, fname)
        # verificar si ya existe copia para monitorizar cambios
        if not os.path.exists(mngfile):
            shutil.copy(fpath, mngfile)

        change_time = None
        while 1:
            try:
                # verificar si son diferentes
                if not compare_files(fpath, mngfile):
                    """Si cambio el archivo definamos el tiempo y hagamos una copia temporal
                        por si se detectan cambios seguidos"""
                    if not change_time:
                        shutil.copy(fpath, "/tmp/" + fname)
                        change_time = time.time()
                        #web.do_post(url="/file_change", data={'file': fpath, 'ip': IP, 'pos': POS,
                        #        'node': HOSTNAME, 'hora': time.strftime("%a, %d-%m-%Y %H:%M ")})

                    """Si cambio el archivo definamos el tiempo y actulizamos la copia temporal"""
                    if not compare_files(fpath, "/tmp/" + fname):
                        shutil.copy(fpath, "/tmp/" + fname)
                        change_time = time.time()
                        #web.do_post(url="/file_change", data={'file': fname, 'ip': IP, 'pos': POS,
                        #        'node': HOSTNAME, 'hora': time.strftime("%a, %d-%m-%Y %H:%M ")})


                    if change_time and (time.time() - change_time) > FILE_CHANGE_THRESHOLD:
                        """ -Resetear tiempo de ultimo cambio
                            - Remover copia temp, a su vez
                            - Notificar el cambio al servidor web
                            - Actualixar la copia monitorizada en managed_files"""
                        change_time = None
                        shutil.copy(fpath, mngfile)
                        os.remove("/tmp/" + fname)

                        web.do_post(url="/file_change", data={'file': fpath, 'ip': IP, 'pos': POS,
                                'node': HOSTNAME, 'hora': datetime.now()})

                        notification = "El archivo " + fpath + " fue modificado el "+ time.strftime("%d-%m-%Y a las %H:%M")+" hora del host"

                        dweb.do_post(url="/api/network/notification/", data={'description': notification, 'node': DB_ID})


            except OSError, oe:
                logger.error("Problema con: " + oe.filename, exc_info=True)
            except Exception, e:
                logger.error("Problema con archivo: ", exc_info=True)
            time.sleep(2)
    else:
        logger.warning(fpath + " no es un archivo valido, terminado hilo...")
        return
    logger.info('Deteniendo Thread [watch_file] finished...')


def format_resources():
    data = {}
    lavg = sysHelper.get_cpu_load_avg()
    ram = sysHelper.get_ram_values()
    cpu = sysHelper.get_cpu_usage()
    if IS_SERVER:
        fans, temperature, power_suply, dimms, server_desc,raid = sysHelper.get_hp_health()
        data['fans'] = fans
        data['is_server'] = True
        data['temperature'] = temperature
        data['power_suply'] = power_suply
        data['dimms'] = dimms
        data['server_desc'] = server_desc
        data['raid'] = raid
        temp_stat,fans_stat,pwr_stat,dimm_stat,proc_stat,ld_stat,pd_stat = sysHelper.hp_health_values()
        data['temp_stat'] = temp_stat
        data['fans_stat'] = fans_stat
        data['pwr_stat'] = pwr_stat
        data['dimm_stat'] = dimm_stat
        data['proc_stat'] = proc_stat
        data['ld_stat'] = ld_stat
        data['pd_stat'] = pd_stat
    else:
        screen = Popen(['nvidia-smi', '-q'], stdout=PIPE).communicate()[0].replace('\n','<br>')
        data['screen'] = screen
        gpu_temp = Popen("nvidia-smi -q -d TEMPERATURE | grep Gpu | awk '{print $3}'", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        video_total = Popen("nvidia-smi -q -d MEMORY | grep Total | awk '{print $3}'", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        video_used = Popen("nvidia-smi -q -d MEMORY | grep Used | awk '{print $3}'", stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
        video_usage = (float(video_used)/float(video_total)) * 100.0
        data['gpu_temp'] = gpu_temp
        data['video_usage'] = video_usage
    dmi = Popen(['dmidecode', '-t', '0,1'], stdout=PIPE).communicate()[0].replace('\n','<br>')
    manufacturer = Popen("dmidecode -t 1 | grep Manufacturer | cut -d':' -f2",  stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
    node_model = Popen("dmidecode -t 1  | grep Name | cut -d':' -f2",  stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
    serial = Popen("dmidecode -t 1 | grep Serial | cut -d':' -f2",  stdin=PIPE, shell=True, stdout=PIPE).communicate()[0].rstrip('\n').rstrip('\r')
    data['dmi'] = dmi
    data['sector'] = SECTOR
    data['manufacturer'] = manufacturer
    data['node_model'] = node_model
    data['serial'] = serial
    data['cores'] = lavg['cores']
    data['procs'] = lavg['procs']
    data['load15'] = lavg['load15']
    data['load5'] = lavg['load5']
    data['ram_prc'] = ram[3]
    data['ram_top_proc'] = ram[4]
    data['ram_top_pmem'] = ram[5]
    data['cpu_pcpu'] = "%.2f" % cpu['pcpu']
    data['cpu_proc_name'] = cpu['proc_name']
    data['cpu_proc_pcpu'] = cpu['proc_pcpu']
    dif = sysHelper.get_sync_state(NTP_SERVER)

    if dif is not None:
        data['sync_dif'] = dif
    else:
        data['sync_dif'] = "---"
    data['uptime_str'], data['uptime_seg'] = sysHelper.get_sys_uptime()
    data['part_usage'], data['partition'], = sysHelper.get_partition_usage()
    data['pos'] = POS
    data['node'] = HOSTNAME
    data['ip'] = IP
    return data

def format_resources_for_node():
    data2 = {}
    lavg = sysHelper.get_cpu_load_avg()
    ram = sysHelper.get_ram_values()
    cpu = sysHelper.get_cpu_usage()
    data2['cores'] = lavg['cores']
    data2['procs'] = lavg['procs']
    data2['load15'] = lavg['load15']
    data2['load5'] = lavg['load5']
    data2['ram_prc'] = ram[3]
    data2['ram_top_proc'] = ram[4]
    data2['ram_top_pmem'] = ram[5]
    data2['cpu_pcpu'] = "%.2f" % cpu['pcpu']
    data2['cpu_proc_name'] = cpu['proc_name']
    data2['cpu_proc_pcpu'] = cpu['proc_pcpu']
    dif = sysHelper.get_sync_state(NTP_SERVER)
    if dif is not None:
        data2['sync_dif'] = dif
    else:
        data2['sync_dif'] = "---"
    data2['uptime_str'], data2['uptime_seg'] = sysHelper.get_sys_uptime()
    data2['pos'] = POS
    data2['node'] = HOSTNAME
    data2['ip'] = IP
    return data2

def send_presence(_IP, _ID):
    time.sleep(1)
    while 1:
        try:
            web.do_post(url="/presence", data={'ip': _IP, 'id': _ID})
            time.sleep(PRESENCE_PERIOD)
        except:
            pass
    logger.info('Thread [send_presence] finished...')

def resources_real_time(_ID):
    while 1:
        try:
            #start_t = time.time()
            data2 = format_resources_for_node()
            data2['id'] = _ID
            web.do_post(data=data2)
            #print time.time() - start_t
            time.sleep(RSCR_COLLECT_PERIOD)
        except:
            pass
    logger.info('Thread [resources_real_time] finished...')


def signal_handler(signal, frame):
    logger.info('Deteniendo ejecucion!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)



from subprocess import Popen, PIPE

def main():
    # Verificar si ya existe en la BD
    #gres = json.loads(dweb.do_get(url="/api/network/nodes/?ip=" + IP))
    gres = None
    while not gres:
        try:
            gres = dweb.do_get(url="/api/network/nodes/?ip=" + IP)
            if len(gres) <= 2:
                data = sysHelper.get_sys_info(ifname=IFACE)
                r = dweb.do_post(url="/api/network/nodes/", data=data)
                #DB_ID = int(json.loads(r.read())['id'])
                DB_ID = int(r.read().split(',')[0].split(':')[1])
            else:
                #DB_ID = int(gres[0]["id"])
                DB_ID = int(gres.split(',')[0].split(':')[1])
        except:
            logger.warning("No se pudo conectar al servidor web "+ DSERVER_IP +":"+ DSERVER_PORT + "... reintentando en 10 segundos.")
            time.sleep(10)
            #sys.exit()
    p = threading.Thread(target=send_presence, args=(IP, DB_ID))
    #p.daemon = True
    p.setDaemon(True)
    p.start()

    r = threading.Thread(target=resources_real_time, args=(DB_ID,))
    #r.daemon = True
    r.setDaemon(True)
    r.start()

    fc = threading.Thread(target=watch_file, args=("/etc/hosts",))
    #fc.daemon = True
    fc.setDaemon(True)
    fc.start()

    while True:
        try:
            start_time = time.time()
            # Ciclo para guardar historial de recursos
            data = format_resources()
            try:
                dweb.do_put(url="/api/network/nodes/" + str(DB_ID) + "/", data=data)
            except Exception, e:
                logger.error("No se envio actualizacion a nodo")
            data['node'] = DB_ID
            dweb.do_post(url="/api/network/performance_hist/", data=data)
            # print get_uptime()
            # web.http_post(data=data)

            #print("- %s seconds " % "{0:.3f} %".format((time.time() - start_time)))
            time.sleep(RSCR_HIST_PERIOD)
        except:
            pass
    print "FIN DE MAIN"

if __name__ == "__main__":
    main()
