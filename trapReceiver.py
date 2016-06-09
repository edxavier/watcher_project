#!/usr/bin/python
import json
import logging
import os

from helpers.funtions_utils import get_logger_handler

__author__ = 'edx'
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from utils.trap_snmp_utils import get_OID_Name, OPER_STATUS, http_post
from utils.snmp_requests import get_request
from utils.web_methods import HttpHelper
#from config import CONFIG
import ConfigParser
from helpers.web_helper import UrlibHttpHelper
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.ini')
#leer archivo de configuracion
config = ConfigParser.ConfigParser()
config.readfp(open(CONFIG_FILE))

SERVER_IP = config.get('NODEJS_SERVER', 'ip')
SERVER_PORT = config.get('NODEJS_SERVER', 'port')

DSERVER_IP = config.get('NGINX_SERVER', 'ip')
DSERVER_PORT = config.get('NGINX_SERVER', 'port')

DB_ID = 0
#servidor django
dweb = UrlibHttpHelper(DSERVER_IP, DSERVER_PORT)

handler = get_logger_handler()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)


def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        if msgVer in api.protoModules:
            pMod = api.protoModules[msgVer]
        else:
            print('Unsupported SNMP version %s' % msgVer)
            return
        reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message(),)
        #print('Notification message from %s:%s ' % (transportAddress[0], transportAddress[1]))
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        if reqPDU.isSameTypeWith(pMod.TrapPDU()):
            if msgVer == api.protoVersion1:
                print('Enterprise: %s' % (
                    pMod.apiTrapPDU.getEnterprise(reqPDU).prettyPrint()
                    )
                )
                print('Agent Address: %s' % (
                    pMod.apiTrapPDU.getAgentAddr(reqPDU).prettyPrint()
                    )
                )
                print('Generic Trap: %s' % (
                    pMod.apiTrapPDU.getGenericTrap(reqPDU).prettyPrint()
                    )
                )
                print('Specific Trap: %s' % (
                    pMod.apiTrapPDU.getSpecificTrap(reqPDU).prettyPrint()
                    )
                )
                print('Uptime: %s' % (
                    pMod.apiTrapPDU.getTimeStamp(reqPDU).prettyPrint()
                    )
                )
                varBinds = pMod.apiTrapPDU.getVarBindList(reqPDU)
            else:
                varBinds = pMod.apiPDU.getVarBindList(reqPDU)
            notify_msg = {}
            #los varbinds vienen el tuplas de tuplas ((val1, val2),(val1, val2))
            cli = HttpHelper(server_addr=SERVER_IP, server_port=int(SERVER_PORT))
            uptime = int(varBinds[0][1].getComponent(True).prettyPrint()) / 100
            notify_type = get_OID_Name(varBinds[1][1].getComponent(True).prettyPrint())
            notify_msg['direccion'] = transportAddress[0]
            # Verificar si ya existe en la BD
            gres = json.loads(dweb.do_get(url="/api/network/nodes/?ip=" + transportAddress[0]))
            print gres[0]["pos"]
            #gres = dweb.do_get(url="/api/network/nodes/?ip=" + transportAddress[0])
            if len(gres)>0:
                DB_ID = gres[0]["id"]
            #else:
                # DB_ID = int(gres[0]["id"])
                #DB_ID = int(gres.split(',')[0].split(':')[1])
            #notify_msg['uptime'] = uptime
            #notify_msg['tipo'] = notify_type
            if notify_type == "nsNotifyShutdown":
                print("NOTIFICAR DE APAGADO")
                #http_post(notify_msg, "/gestion/boot_event/agregar/")
                notification = transportAddress[0] + " ("+ gres[0]["pos"]+") se ha apago el " + time.strftime(
                    "%d-%m-%Y a las %H:%M")
                notification2 = transportAddress[0] + " (" + gres[0]["pos"] + ") se esta apagando"

                dweb.do_post(url="/api/network/notification/", data={'description': notification, 'node': DB_ID})
                cli.http_post(url="/shutdown", data={'description': notification2, 'node': DB_ID})

                #print (notify_msg)
            elif notify_type == "coldStart":
                print("NOTIFICAR DE ARRANQUE")
                #http_post(notify_msg, "/gestion/boot_event/agregar/")
                notification = transportAddress[0] + " (" + gres[0]["pos"] + ") se encedio el " + time.strftime(
                    "%d-%m-%Y a las %H:%M")
                notification2 = transportAddress[0] + " (" + gres[0]["pos"] + ") esta iniciando"

                dweb.do_post(url="/api/network/notification/", data={'description': notification, 'node': DB_ID})
                cli.http_post(url="/startup", data={'description': notification2, 'node': DB_ID})
                #print (notify_msg)
            elif notify_type == "linkUp":
                #6 varBinds pos 3,4,5 = interfaceIndex, adminStatus, operstatus
                #print("NOTIFICAR DE INTERFACE UP")
                if_desc = '1.3.6.1.2.1.2.2.1.2.'+varBinds[2][1].getComponent(True).prettyPrint()
                #admin_stat = '1.3.6.1.2.1.2.2.1.7.'+varBinds[2][1].getComponent(True).prettyPrint()
                #oper_stat = '1.3.6.1.2.1.2.2.1.8.'+varBinds[2][1].getComponent(True).prettyPrint()
                iface = get_request(destino=transportAddress[0], mib_oid=if_desc)
                oper = varBinds[3][1].getComponent(True).prettyPrint()
                admin = varBinds[4][1].getComponent(True).prettyPrint()
                notify_msg['nombre'] = iface
                notify_msg['estado_operacional'] = OPER_STATUS[int(oper)]
                notify_msg['estado_administrativo'] = OPER_STATUS[int(admin)]
                #http_post(notify_msg, "/gestion/interface_event/agregar/")
                cli.http_post(url="/linkup", data=notify_msg)
                #print(notify_msg)
                #target = open('error.log', 'w')
                #target.write(res.text)
                #target.close()
            elif notify_type == "linkDown":
                #6 varBinds pos 3,4,5 = interfaceIndex, adminStatus, operstatus
                print("NOTIFICAR DE INTERFACE DOWN")
                if_desc = '1.3.6.1.2.1.2.2.1.2.'+varBinds[2][1].getComponent(True).prettyPrint()
                iface = get_request(destino=transportAddress[0], mib_oid=if_desc)
                oper = varBinds[3][1].getComponent(True).prettyPrint()
                admin = varBinds[4][1].getComponent(True).prettyPrint()
                notify_msg['nombre'] = iface
                notify_msg['estado_operacional'] = OPER_STATUS[int(oper)]
                notify_msg['estado_administrativo'] = OPER_STATUS[int(admin)]
                #http_post(notify_msg, "/gestion/interface_event/agregar/")
                #cli.http_post(url="/gestion/interface_event/agregar/", data=notify_msg)
                cli.http_post(url="/linkdown", data=notify_msg)
                #print(notify_msg)
            elif notify_type == "mteTriggerFired":
                pass
                """9 varBinds
                3 = The name of the trigger causing the notification.
                7 =The value of the object at mteTriggerValueID when a trigger fired.
                8 = The process name we're counting/checking on.
                9 = The reason for the failure
                """
                #print("NOTIFICAR De DISMAN")
                #notify_msg['tabla'] = varBinds[2][1].getComponent(True).prettyPrint()
                #notify_msg['warning'] = (varBinds[6][1].getComponent(True).prettyPrint())
                #notify_msg['item'] = (varBinds[7][1].getComponent(True).prettyPrint())
                #notify_msg['mensaje'] = (varBinds[8][1].getComponent(True).prettyPrint())
                #http_post(notify_msg, "/gestion/general_event/agregar/")
                #cli.http_post(url="/gestion/general_event/agregar/", data=notify_msg)
                #print(notify_msg)

            #print(notify_msg)

            """
            for oid, val in varBinds:
                print("----------------------------------")
                print get_OID_Name(oid.prettyPrint()) + ":"
                if get_OID_Name(oid.prettyPrint()) == "sysUpTime":
                    uptime = int(val.getComponent(True).prettyPrint()) / 100
                    print("Uptime:" + str(uptime))
                elif get_OID_Name(oid.prettyPrint()) == "snmpTrapOID":
                    valor = get_OID_Name(val.getComponent(True).prettyPrint())
                    #if aceptable_value(valor):
                    print get_OID_Name(val.getComponent(True).prettyPrint()) +":"
                    #else:
                        #print("No me interesa")
                elif get_OID_Name(oid.prettyPrint()) == "snmpTrapEnterprise":
                    print get_OID_Name(val.getComponent(True).prettyPrint())
                else:
                    print val.getComponent(True).prettyPrint()
            """

    return wholeMsg

transportDispatcher = AsynsockDispatcher()

transportDispatcher.registerRecvCbFun(cbFun)

# UDP/IPv4
transportDispatcher.registerTransport(
    udp.domainName, udp.UdpSocketTransport().openServerMode(('0.0.0.0', 162))
)

# UDP/IPv6
transportDispatcher.registerTransport(
    udp6.domainName, udp6.Udp6SocketTransport().openServerMode(('::1', 162))
)

transportDispatcher.jobStarted(1)

try:
    # Dispatcher will never finish as job#1 never reaches zero
    transportDispatcher.runDispatcher()
except:
    transportDispatcher.closeDispatcher()
    raise

