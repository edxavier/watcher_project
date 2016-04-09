__author__ = 'edx'

DEVICE_STATUS = {
    0: 'unspecified',
    1: 'unknown',
    2: 'running',
    3: 'warning',
    4: 'testing',
    5: 'down',
}

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
    '1.3.6.1.2.1.88.2.0.1': 'mteTriggerFired',
    #storagesTypes
    '1.3.6.1.2.1.25.2.1.1': 'Otro',
    '1.3.6.1.2.1.25.2.1.2': 'Memoria RAM',
    '1.3.6.1.2.1.25.2.1.3': 'Memoria Virtual',
    '1.3.6.1.2.1.25.2.1.4': 'Disco Fijo',
    '1.3.6.1.2.1.25.2.1.5': 'Disco Removible',
    '1.3.6.1.2.1.25.2.1.6': 'Disco Flexible',
    '1.3.6.1.2.1.25.2.1.7': 'Disco Compacto',
    '1.3.6.1.2.1.25.2.1.8': 'Disco RAM',
    '1.3.6.1.2.1.25.2.1.9': 'Memoria Flash',
    '1.3.6.1.2.1.25.2.1.10': 'Disco de Red',
    #DeviceTypes
    '1.3.6.1.2.1.25.3.1.10': 'Video',
    '1.3.6.1.2.1.25.3.1.11': 'Audio',
    '1.3.6.1.2.1.25.3.1.12': 'Coprocesador',
    '1.3.6.1.2.1.25.3.1.13': 'Teclado',
    '1.3.6.1.2.1.25.3.1.14': 'Modem',
    '1.3.6.1.2.1.25.3.1.15': 'Puerto Paralelo',
    '1.3.6.1.2.1.25.3.1.16': 'Puntero',
    '1.3.6.1.2.1.25.3.1.17': 'Puerto Serie',
    '1.3.6.1.2.1.25.3.1.18': 'Cinta',
    '1.3.6.1.2.1.25.3.1.19': 'Reloj',
    '1.3.6.1.2.1.25.3.1.20': 'Memoria Volatil',
    '1.3.6.1.2.1.25.3.1.21': 'Memoria No Volatil',

    '1.3.6.1.2.1.25.3.1.6':'Disco de Almacenamiento',
    '1.3.6.1.2.1.25.3.1.5':'Impresora',
    '1.3.6.1.2.1.25.3.1.4':'Red',
        '1.3.6.1.2.1.25.3.1.3':'Procesador',
    '1.3.6.1.2.1.25.3.1.2':'Desconocido',
    '1.3.6.1.2.1.25.3.1.1':'Otro',

}
