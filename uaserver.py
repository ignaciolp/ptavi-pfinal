#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os
import time

try:
    config = sys.argv[1]
except IndexError:
    sys.exit('Usage: python uaserver.py config')


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
        dicc_stE ={}
        if name in self.int_dic:
            dicc_stE = {'etiqueta':name}
            for atribute in self.int_dic[name]:
                dicc_stE[atribute] = attrs.get(atribute, "")
            self.init_list.append(dicc_stE)

    def get_data(self):
        return self.init_list

def Log(log_file, tiempo, evento):
    fichero = open(log_file, 'a')
    tiempo = time.gmtime(time.time())
    fichero.write(time.strftime('%Y%m%d%H%M%S', tiempo))
    fichero.write(evento.replace('\r\n', ' ') + '\r\n')
    fichero.close()


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


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    rtproxy_list = []

    def handle(self):
        while 1:
            # Leyendo lineas que envia el cliente
            line = self.rfile.read().decode('utf-8')
            print("El cliente nos manda " + line)
            line_selec = line.split()
            # cuando acaba sale
            if not line:
                break
            metodo = line_selec[0]
            
            evento = ' Received from ' + proxy_IP + ':' 
            evento += proxy_port + ': ' + line
            tiempo = time.gmtime(time.time())
            Log(log_file, tiempo, evento)

            if metodo == 'INVITE':

                petition = 'SIP/2.0 100 Trying\r\n\r\n'
                petition += 'SIP/2.0 180 Ring\r\n\r\n'
                petition += 'SIP/2.0 200 OK\r\n\r\n'
                petition += "Content-Type: application/sdp \r\n"
                petition += "v=0 \r\n" + "o=" + usuario_nombre + " "
                petition += server_ip + "\r\n" + "s=misesion \r\n" + "t=0 \r\n"
                petition += "m=audio " +rtpaudio_port + " RTP \r\n\r\n"

                evento = ' Sent to ' + proxy_IP + ':' 
                evento += proxy_port + ': ' + petition
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

                self.wfile.write(bytes(petition, 'utf-8'))
                self.rtp_user = line_selec[6].split('=')[1]
                self.rtproxy_list.append(self.rtp_user)
                self.rtp_ip = line_selec[7]
                self.rtproxy_list.append(self.rtp_ip)
                self.rtpaudio_port = line_selec[11]
                self.rtproxy_list.append(self.rtpaudio_port)

            elif metodo == 'ACK':
                print('me esta llegando ', line)
               
                aEjecutar = './mp32rtp -i ' + self.rtproxy_list[1] + ' -p '
                aEjecutar += self.rtproxy_list[2] + ' < ' + audio_file

                evento = ' Sending to ' + self.rtproxy_list[1] + ':' 
                evento += self.rtproxy_list[2] + ': ' + 'audio_file'
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)
               
                print('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)
                print('Finished transfer')

                evento = ' Finished audio transfer to ' + " "
                evento +=  self.rtproxy_list[1] + ':' + self.rtproxy_list[2] + ": "  
                evento +=  'audio_file'
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

            elif metodo == 'BYE':

                petition = 'SIP/2.0 200 OK\r\n\r\n'
                self.wfile.write(bytes(petition, 'utf-8'))

                evento = ' Sent to ' + proxy_IP + ':' 
                evento = proxy_port + ': ' + petition
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

            elif metodo != 'INVITE' or metodo != 'BYE' or metodo != 'ACK':
               
                petition = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(byes(petition, 'utf-8'))

                evento = ' Sent to ' + proxy_IP + ':' 
                evento = proxy_port + ': ' + petition
                tiempo = time.gmtime(time.time())
                mLog(log_file, tiempo, evento)

            else:
               
                petition = 'SIP/2.0 400 Bad Request'
                self.wfile.write(bytes(petition, 'utf-8'))

                evento = ' Sent to ' + proxy_IP + ':' 
                evento = proxy_port + ': ' + petition 
                tiempo = time.gmtime(time.time())         
                Log(log_file, tiempo, evento)

# Creamos servidor y escuchamos
# ST_LOG
evento = ' Starting uaserver...'
tiempo = time.gmtime(time.time())
Log(log_file, tiempo, evento)
# END_LOG
try:
    serv = socketserver.UDPServer((server_ip, int(server_port)), EchoHandler)
    print("Listening...")
    serv.serve_forever()
except KeyboardInterrupt:
    evento = ' Finishing uaserver.'
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)
    sys.exit('\r\nFinished uaserver')


