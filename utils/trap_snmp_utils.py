__author__ = 'edx'
import urllib

WEB_SERVER = 'http://127.0.0.1:8000'

OIDS = {
    '1.3.6.1.2.1.1.3.0': 'sysUpTime',
    '1.3.6.1.6.3.1.1.4.1.0': 'snmpTrapOID',
    '1.3.6.1.6.3.1.1.4.3.0': 'snmpTrapEnterprise',
    '1.3.6.1.6.3.1.1.5.1': 'coldStart',
    '1.3.6.1.6.3.1.1.5.2': 'warmStart',
    '1.3.6.1.6.3.1.1.5.3': 'linkDown',
    '1.3.6.1.6.3.1.1.5.4': 'linkUp',
    '1.3.6.1.4.1.8072.3.2.10': 'linux',
    '1.3.6.1.4.1.8072.3.2.13': 'win',
    '1.3.6.1.4.1.8072.3.2.255': 'desconocido',
    '1.3.6.1.4.1.8072.4.0.1': 'nsNotifyStart',
    '1.3.6.1.4.1.8072.4.0.2': 'nsNotifyShutdown',
    '1.3.6.1.4.1.8072.4.0.3': 'nsNotifyRestart',
    '1.3.6.1.2.1.88.2.1.1.0': 'mteHotTrigger',
    '1.3.6.1.2.1.88.2.1.2.0': 'mteHotTargetName',
    '1.3.6.1.2.1.88.2.1.3.0': 'mteHotContextName',
    '1.3.6.1.2.1.88.2.1.4.0': 'mteHotOID',
    '1.3.6.1.2.1.88.2.1.5.0': 'mteHotValue',
    '1.3.6.1.2.1.88.2.1.6.0': 'mteFailedReason',
    '1.3.6.1.2.1.88.2.0.1': 'mteTriggerFired'
}

OPER_STATUS = {
    1: 'up',
    2: 'down',
    3: 'testing',
    4: 'unknown',
    5: 'dormant',
    6: 'notPresent',
    7: 'lowerLayerDown'
}


DESIRED_TRAPS = [
    "nsNotifyShutdown", "nsNotifyStart", "nsNotifyRestart", "coldStart",
    "warmStart", "linkDown", "linkUp", "mteTriggerFired"
]

def aceptable_value(val):
    return val in DESIRED_TRAPS

def get_OID_Name(oid):
    try:
        val = OIDS[oid]
    except:
        val = oid
    return val



def http_post(data_dict= {}, url=""):

    try:
        data = urllib.urlencode(data_dict)
        u = urllib.urlopen(WEB_SERVER+url, data)
        res = u.read()
        print("Result %s: %s" % (u.getcode(), res))
    except Exception, e:
        print(e.message)
        print("Error enviando datos al servidor")

def http_get(url=""):

    try:
        u = urllib.urlopen(WEB_SERVER+url)
        return u.read()
    except Exception, e:
        print(e.message)
        print("Error enviando datos al servidor")