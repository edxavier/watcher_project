#!/usr/bin/python
import logging, sys, os, shutil, platform
import time, threading, signal, sys
from helpers.web_helper import UrlibHttpHelper
from helpers.os_helper import OSHelper
from helpers.funtions_utils import get_ip_address, compare_files, get_logger_handler, get_pos
import ConfigParser

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

handler = get_logger_handler()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
web = UrlibHttpHelper(SERVER_IP, port=SERVER_PORT)
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
                        web.do_post(url="/file_change", data={'file': fname, 'ip': IP, 'pos': POS,
                                'node': HOSTNAME, 'hora': time.strftime("%a, %d-%m-%Y %H:%M ")})

                    """Si cambio el archivo definamos el tiempo y actulizamos la copia temporal"""
                    if not compare_files(fpath, "/tmp/" + fname):
                        shutil.copy(fpath, "/tmp/" + fname)
                        change_time = time.time()
                        web.do_post(url="/file_change", data={'file': fname, 'ip': IP, 'pos': POS,
                                'node': HOSTNAME, 'hora': time.strftime("%a, %d-%m-%Y %H:%M ")})





                    if change_time and (time.time() - change_time) > FILE_CHANGE_THRESHOLD:
                        """ -Resetear tiempo de ultimo cambio
                            - Remover copia temp, a su vez
                            - Notificar el cambio al servidor web
                            - Actualixar la copia monitorizada en managed_files"""
                        change_time = None
                        shutil.copy(fpath, mngfile)
                        os.remove("/tmp/" + fname)
                        print "ARCHIVO ACTUALIZADO en MON"

            except OSError, oe:
                logger.error("Problema con: " + oe.filename)
            time.sleep(2)
    else:
        logger.warning(fpath + " no es un archivo valido, terminado hilo...")
        return


def format_resources():
    data = {}
    lavg = sysHelper.get_cpu_load_avg()
    ram = sysHelper.get_ram_values()
    cpu = sysHelper.get_cpu_usage()


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
    dif = sysHelper.get_sync_state("10.160.80.205")
    if dif:
        data['sync_dif'] = dif
    else:
        data['sync_dif'] = "---"
    data['uptime_str'], data['uptime_seg'] = sysHelper.get_sys_uptime()
    data['part_usage'], data['partition'], = sysHelper.get_partition_usage()
    data['pos'] = POS
    data['node'] = HOSTNAME
    data['ip'] = IP
    return data

def send_presence():
    time.sleep(1)
    while 1:
        web.do_post(url="/presence", data={'ip': IP, 'id': DB_ID})
        time.sleep(PRESENCE_PERIOD)

def resources_real_time():
    while 1:
        data = format_resources()
        data['id'] = DB_ID
        web.do_post(data=data)
        time.sleep(RSCR_COLLECT_PERIOD)



def signal_handler(signal, frame):
    logger.info('Deteniendo ejecucion!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)



# Verificar si ya existe en la BD
#gres = json.loads(dweb.do_get(url="/api/network/nodes/?ip=" + IP))
gres = dweb.do_get(url="/api/network/nodes/?ip=" + IP)

if len(gres) <= 2:
    data = sysHelper.get_sys_info(ifname=IFACE)
    r = dweb.do_post(url="/api/network/nodes/", data=data)
    #DB_ID = int(json.loads(r.read())['id'])
    DB_ID = int(r.read().split(',')[0].split(':')[1])
else:
    #DB_ID = int(gres[0]["id"])
    DB_ID = int(gres.split(',')[0].split(':')[1])


p = threading.Thread(target=send_presence)
p.daemon = True
p.start()

r = threading.Thread(target=resources_real_time)
r.daemon = True
r.start()

#fc = threading.Thread(target=watch_file, args=("/home/edx/heroku",))
#fc.daemon = True
#fc.start()

from subprocess import Popen, PIPE



while True:
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
