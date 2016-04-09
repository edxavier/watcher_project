import time
from .web_methods import HttpHelper
import paramiko

__author__ = 'edx'

def get_num_entries(data):
    total = 0
    for i in data:
        try:
            int(i)
            total += 1
        except:
            break
    return total

def get_matrix_data(data, cols, total):
    res_tupled=[]
    for i in range(0,cols):#dividir el resultado por cada coluna de la tabla
                ini = i * total
                fin = ini + total
                res_tupled.append(data[ini:fin])
    return res_tupled

def get_data_reordered(table):
    cols = len(table[0])
    rows = len(table)
    #print("COLUMS: %d ROWS: %d" % (cols,rows))
    data_array = []
    for c in range(0,cols):
        maped = []
        for r in range(0,rows):
            try:
                maped.append(table[r][c])
            except:
                maped.append(0)
        data_array.append(maped)
    return data_array

def clear_multiple_spaces(text=""):
    return ' '.join(text.split())

def get_pos(host='127.0.0.1'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host)
    # Send the command (non-blocking)
    stdin, stdout, stderr = ssh.exec_command("cat /root/pos")

    # Wait for the command to terminate
    values = []
    for i, line in enumerate(stdout):
        if i <= 3:
            line = line.rstrip()
            line = line.rstrip('\n').rstrip('\r').strip()
            line = clear_multiple_spaces(line)
            values.append(line)
    if len(values) > 0:
        return values[0]
    else:
        return "----"

