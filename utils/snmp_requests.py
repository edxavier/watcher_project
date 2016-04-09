__author__ = 'edx'

from pysnmp.entity.rfc3413.oneliner import cmdgen

def get_request(destino='127.0.0.1', comunidad='public', puerto=161, mib_oid='1.3.6.1.2.1.1.1.0'):
    try:
        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData(comunidad),
            cmdgen.UdpTransportTarget((destino, puerto), timeout=1.5, retries=1),
            mib_oid
        )

        # Check for errors and print out results
        if not errorIndication and not errorStatus:
            return varBinds[0][1].prettyPrint()
        elif errorIndication:
            return None
        else:
            return None
    except Exception, e:
        print("Error on get request: "+e.message)
        return None


def get_bulk_request(max_result=0, start_oid="", address="127.0.0.1"):
    try:
        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.bulkCmd(
            cmdgen.CommunityData('public'),
            cmdgen.UdpTransportTarget((address, 161)),
            0, max_result,
            #'1.3.6.1.2.1.1.1'
            start_oid
        )

        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print('%s at %s' % (
                    errorStatus.prettyPrint(),
                    errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                    )
                )
            else:
                res = []
                for varBindTableRow in varBindTable:
                    for name, val in varBindTableRow:
                        res.append(val.prettyPrint())
                        #print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
                return res
    except Exception, e:
        print("Error on bulk request: " + e.message)
        return None

"""
oid = '1.3.6.1.2.1.2.2.1.2.2'
value = get_request(mib_oid=oid, destino='10.160.80.22', )
if value:
    print(value)
else:
    print("error")

"""

#get_bulk_request()