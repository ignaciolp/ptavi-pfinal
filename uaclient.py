#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import hashlib
import os
import time

try:
    config = sys.argv[1]
    metodo = sys.argv[2]
    opcion = sys.argv[3]
except IndexError:
    sys.exit('Usage: python uaclient.py config method option')


class XMLHandler(ContentHandler):

    def __init__(self):

        self.int_dic = {'account': ['username', 'passwd'],
                        'uaserver': ['ip', 'puerto'],
                        'rtpaudio': ['puerto'],
                        'regproxy': ['ip', 'puerto'],
                        'log': ['path'],
                        'audio': ['path']}
        self.init_list = []

    def startElement(self, name, attrs):
        dicc_stE = {}
        if name in self.int_dic:
            dicc_stE = {'Tag': name}
            for atribute in self.int_dic[name]:
                dicc_stE[atribute] = attrs.get(atribute, "")
            self.init_list.append(dicc_stE)

    def get_data(self):
        return self.init_list


parser = make_parser()
XMLH = XMLHandler()
parser.setContentHandler(XMLH)
parser.parse(open(config))
init_list = XMLH.get_data()
# Variables del config xml
usuario_nombre = init_list[0]['username']
contraseña = init_list[0]['passwd']
server_ip = init_list[1]['ip']
server_port = init_list[1]['puerto']
rtpaudio_port = init_list[2]['puerto']
proxy_IP = init_list[3]['ip']
proxy_port = init_list[3]['puerto']
log_file = init_list[4]['path']
audio_file = init_list[5]['path']


def Log(log_file, tiempo, evento):
    fichero = open(log_file, 'a')
    tiempo = time.gmtime(time.time())
    fichero.write(time.strftime('%Y%m%d%H%M%S', tiempo))
    fichero.write(evento.replace('\r\n', ' ') + '\r\n')
    fichero.close()

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((proxy_IP, int(proxy_port)))

evento = ' Starting uaclient...'
tiempo = time.gmtime(time.time())
Log(log_file, tiempo, evento)

if metodo == 'REGISTER':

    petition = 'REGISTER sip:' + usuario_nombre + ':' + server_port
    petition += ' SIP/2.0\r\n' + 'Expires: ' + opcion + '\r\n'
    print('Enviando: ' + petition)
    my_socket.send(bytes(petition, 'utf-8') + b'\r\n')

    evento = ' Sent to ' + proxy_IP + ':'
    evento += proxy_port + ': ' + petition
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)

    data = my_socket.recv(int(proxy_port))

    evento = ' Received from ' + proxy_IP + ':'
    evento += proxy_port + ': ' + data.decode('utf-8')
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)

    print('Recibido -- ', data.decode('utf-8'))
    data_recibido = data.decode('utf-8').split()
    if data_recibido[1] == '401':
        nonce = data_recibido[-1].split('=')[1]
        m = hashlib.sha1()
        m.update(bytes(nonce, 'utf-8'))
        m.update(bytes(contraseña, 'utf-8'))
        response = m.hexdigest()
        petition += 'Authorization: Digest response=' + response
        print('Enviando: ' + petition)

        my_socket.send(bytes(petition, 'utf-8') + b'\r\n\r\n')
        evento = ' Sent to ' + proxy_IP + ':'
        evento += proxy_port + ': ' + petition
        tiempo = time.gmtime(time.time())
        Log(log_file, tiempo, evento)

        data = my_socket.recv(int(proxy_port))

        evento = ' Received from ' + proxy_IP + ':'
        evento += proxy_port + ': ' + data.decode('utf-8')
        tiempo = time.gmtime(time.time())
        Log(log_file, tiempo, evento)

        print('Recibido -- ', data.decode('utf-8'))

elif metodo == 'INVITE':

    petition = 'INVITE sip:' + opcion + ' SIP/2.0\r\n'
    petition += 'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n'
    petition += 'o=' + usuario_nombre + ' ' + server_ip
    petition += '\r\n' + 's=misesion\r\n'
    petition += 't=0\r\n' + 'm=audio ' + rtpaudio_port + ' RTP\r\n'
    print('Enviando: ' + petition)

    my_socket.send(bytes(petition, 'utf-8') + b'\r\n')

    evento = ' Sent to ' + proxy_IP + ':'
    evento += proxy_port + ': ' + petition
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)

    data = my_socket.recv(int(proxy_port))

    evento = ' Received from ' + proxy_IP + ':'
    evento += proxy_port + ': ' + data.decode('utf-8')
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)

    print('Recibido -- ', data.decode('utf-8'))
    selec = data.decode('utf-8').split()
    if selec[1] == '100' and selec[4] == '180' and selec[7] == '200':
        metodo == 'ACK'
        petition = 'ACK sip:' + opcion + ' SIP/2.0'
        ip_destino = selec[13]  # destino del RTP
        port_destino = selec[17]  # destino del RTP
        print('Enviando: ' + petition)

        my_socket.send(bytes(petition, 'utf-8') + b'\r\n\r\n')
        evento = ' Received from ' + proxy_IP + ':'
        evento += proxy_port + ': ' + data.decode('utf-8')
        tiempo = time.gmtime(time.time())
        Log(log_file, tiempo, evento)

        aEjecutar = './mp32rtp -i ' + ip_destino + ' -p ' + port_destino
        aEjecutar += ' < ' + audio_file
        print('Vamos a ejecutar', aEjecutar)
        os.system(aEjecutar)

        evento = ' Sending to ' + ip_destino + ':'
        evento += port_destino + ': ' + 'audio_file'
        tiempo = time.gmtime(time.time())
        Log(log_file, tiempo, evento)

        print('Finished transfer')
        data = my_socket.recv(int(port_destino))

        evento = ' Finished audio transfer to '
        evento += ip_destino + ':' + port_destino
        evento += ': ' + audio_file
        tiempo = time.gmtime(time.time())
        Log(log_file, tiempo, evento)

        print('Recibido -- ', data.decode('utf-8'))

elif metodo == 'BYE':
    petition = 'BYE sip:' + opcion + ' SIP/2.0'
    print('Enviando: ' + petition)

    my_socket.send(bytes(petition, 'utf-8') + b'\r\n\r\n')
    evento = ' Sent to ' + proxy_IP + ':'
    evento += proxy_port + ': ' + petition
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)

    data = my_socket.recv(int(proxy_port))

    evento = ' Received from ' + proxy_IP + ':'
    evento += proxy_port + ': ' + data.decode('utf-8')
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)

    print('Recibido -- ', data.decode('utf-8'))

evento = ' Finishing.'
tiempo = time.gmtime(time.time())
Log(log_file, tiempo, evento)
