#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import random
import os
import hashlib
import time
import json

try:
    config = sys.argv[1]
except IndexError:
    sys.exit('Usage: python3 proxy_registrar.py config')


class XMLHandler(ContentHandler):

    def __init__(self):

        self.int_dic = {'server': ['name', 'ip', 'port'],
                           'database': ['path', 'passwdpath'],
                           'log': ['path']}
        self.init_list = []

    def startElement(self, name, attrs):
        dicc_stE ={}
        if name in self.int_dic:
            dicc_stE = {'Tag':name}
            for atribute in self.int_dic[name]:
                dicc_stE[atribute] = attrs.get(atribute, '')
            self.init_list.append(dicc_stE)

    def get_data(self):
        return self.init_list

parser = make_parser()
XMLH = XMLHandler()
parser.setContentHandler(XMLH)
parser.parse(open(config))
init_list = XMLH.get_data()
# Variables del xml
server_nombre = init_list[0]['name']
server_ip = init_list[0]['ip']
server_port = init_list[0]['port']
data_path = init_list[1]['path']
contraseña_path = init_list[1]['passwdpath']
log_file = init_list[2]['path']

def Log(log_file, tiempo, evento):
    fichero = open(log_file, 'a')
    tiempo = time.gmtime(time.time())
    fichero.write(time.strftime('%Y-%m-%d %H:%M:%S', tiempo))
    evento = evento.replace('\r\n', ' ')
    fichero.write(evento + '\r\n')
    fichero.close()


class RegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    dicc_client = {}  # Diccionario de clientes registrados
    nonce = [] #lista de numero aleatorio

    def register2json(self):
        
        json.dump(self.dicc_client, open('registered.json', 'w'))

    def json2registered(self):
        
        try:
            with open('registered.json') as client_file:
                self.dicc_client = json.load(client_file)
                self.file_exists = True
        except:
            self.file_exists = False

    def delete(self):
        
        deletList = []
        
        for client in self.dicc_client:
            self.expire = int(self.dicc_client[client][-1])
            now = time.time()
            if self.expire < now:
                deletList.append(client)
        for cliente in deletList:
            print('ELIMINADO ' + cliente)
            del self.dicc_client[cliente]
        self.register2json()

    def handle(self):
        
        self.json2registered()
        while 1:
            line = self.rfile.read().decode('utf-8')
            print('El cliente nos manda: ' + line)
            if not line:
                break
            line_selec = line.split()
            metodo = line_selec[0]

            evento = ' Received from ' + self.client_address[0] 
            evento += ':' + str(self.client_address[1]) + ': ' 
            evento +=  line
            tiempo = time.gmtime(time.time())
            Log(log_file, tiempo, evento)

            if metodo == 'REGISTER':

                if 'Digest' not in line_selec:
                    self.nonce.append(str(random.randint(0000, 9999)))
                    answer = 'SIP/2.0 401 Unauthorized\r\n'
                    answer += 'WWW Authenticate: Digest nonce='
                    answer += self.nonce[0] + '\r\n\r\n'
                    self.wfile.write(bytes(answer, 'utf-8'))

                    evento = ' Sent to ' + self.client_address[0] + ':'
                    evento += str(self.client_address[1]) + ': ' 
                    evento += answer
                    tiempo = time.gmtime(time.time())
                    Log(log_file, tiempo, evento)

                else:

                    self.user = line.split()[1].split(':')[1]
                    self.port = line.split()[1].split(':')[2]
                    hresponse = line.split()[-1].split('=')[1]
                    contraseña_file = open(contraseña_path, 'r')
                    contraseña_file1 = contraseña_file.readlines()
                    self.expires = line.split()[4]
                    for line in contraseña_file1:
                        line_selec = line.split()
                        word = line_selec[1].split('\r\n')
                        if line_selec[0] == self.user:
                            password = word[0].split('=')[1]
                    m = hashlib.sha1()
                    m.update(bytes(self.nonce[0], 'utf-8'))
                    m.update(bytes(password, 'utf-8'))
                    response_comparation = m.hexdigest()
                    if response_comparation == hresponse:
                        self.json2registered()
                        self.now = time.time()
                        self.expire_time = float(self.expires) +\
                            float(self.now)
                        self.cliente_lista = []
                        self.cliente_lista.append(self.client_address[0])  # IP
                        self.cliente_lista.append(self.port)  # Puerto
                        self.cliente_lista.append(self.now)
                        self.cliente_lista.append(self.expire_time)
                        self.dicc_client[self.user] = self.cliente_lista
                        self.delete()
                        self.cliente_lista = []
                        self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')

                        evento = ' Sent to ' + self.client_address[0] 
                        evento += ':' + str(self.port) + ': '
                        evento += 'SIP/2.0 200 OK\r\n\r\n'
                        tiempo = time.gmtime(time.time())
                        Log(log_file, tiempo, evento)

                    self.register2json()

            elif metodo == 'INVITE':

                self.json2registered()
                user = line.split()[1].split(':')[1]  # Al que mando el INVITE

                if user in self.dicc_client.keys():
                    self.json2registered()
                    IP_server = self.dicc_client[user][0]  # IP destino
                    PORT_server = self.dicc_client[user][1]  # Puerto destino                   
                    my_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_REUSEADDR, 1)
                    my_socket.connect((IP_server, int(PORT_server)))
                    my_socket.send(bytes(line, 'utf-8'))

                    evento = ' Sent to ' + IP_server + ':'
                    evento += PORT_server + ': ' + line
                    tiempo = time.gmtime(time.time())
                    Log(log_file, tiempo, evento)

                    data = my_socket.recv(int(server_port))
                    datos_recibidos = data.decode('utf-8')

                    evento = ' Received from ' + IP_server 
                    evento += ':' + PORT_server + ': ' + datos_recibidos
                    tiempo = time.gmtime(time.time())
                    Log(log_file, tiempo, evento)

                    print('Recibido -- ', data.decode('utf-8'))
                    self.wfile.write(bytes(datos_recibidos, 'utf-8'))

                else:

                    self.wfile.write(b'SIP/2.0 404 User Not Found\r\n\r\n')

                    evento = ' Sent to ' + self.client_address[0] + ':'
                    evento += str(self.client_address[1]) + ': ' + line
                    tiempo = time.gmtime(time.time())
                    Log(log_file, tiempo, evento)

            elif metodo == 'ACK':

                self.json2registered()
                user = line.split()[1].split(':')[1]  # Al que mando el ACK
                IP_server = self.dicc_client[user][0]  # IP destino
                PORT_server = self.dicc_client[user][1]  # Puerto destino
                my_socket = socket.socket(socket.AF_INET,
                                          socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET,
                                     socket.SO_REUSEADDR, 1)
                my_socket.connect((IP_server, int(PORT_server)))
                my_socket.send(bytes(line, 'utf-8'))

                evento = ' Sent to ' + IP_server + ': ' + PORT_server
                evento += ': ' + line
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

                data = my_socket.recv(int(server_port))
                datos_recibidos = data.decode('utf-8')

                evento = ' Received from ' + IP_server + ':'
                evento = PORT_server + ': ' + datos_recibidos
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

                print('Recibido -- ', data.decode('utf-8'))
                self.wfile.write(bytes(datos_recibidos, 'utf-8') + b'\r\n')

                evento = ' Sent to ' + self.client_address[0] + ':' 
                evento += str(self.client_address[1]) + ': ' + line
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

            elif metodo == 'BYE':
    
                self.json2registered()
                usuario = line.split()[1].split(':')[1]  # Al que mando el BYE
                IP_server = self.dicc_client[usuario][0]  # IP destino
                PORT_server = self.dicc_client[usuario][1]  # Puerto destino
                my_socket = socket.socket(socket.AF_INET,
                                          socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET,
                                     socket.SO_REUSEADDR, 1)
                my_socket.connect((IP_server, int(PORT_server)))
                my_socket.send(bytes(line, 'utf-8'))

                evento = ' Sent to ' + IP_server + ': ' + PORT_server
                evento += ': ' + line
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

                data = my_socket.recv(int(server_port))
                datos_recibidos = data.decode('utf-8')

                evento = ' Received from ' + IP_server + ':'
                evento += PORT_server + ': ' + datos_recibidos
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

                print('Recibido -- ', data.decode('utf-8'))
                self.wfile.write(bytes(datos_recibidos, 'utf-8'))

                evento = ' Sent to ' + self.client_address[0] + ':'
                evento += str(self.client_address[1]) + ': ' 
                evento += datos_recibidos
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

            elif metodo != 'REGISTER' or 'INVITE' or 'ACK' or 'BYE':

                answer = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(bytes(answer, 'utf-8'))

                evento = ' Sent to ' + self.client_address[0] + ':' 
                evento += str(self.client_address[1]) + ': ' + answer
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

            else:

                answer = 'SIP/2.0 400 Bad Request\r\n\r\n'
                self.wfile.write(bytes(answer, 'utf-8'))

                evento = ' Sent to ' + self.client_address[0] + ':' 
                evento += str(self.client_address[1]) + ': ' + answer
                tiempo = time.gmtime(time.time())
                Log(log_file, tiempo, evento)

# Creamos servidor de eco y escuchamos
evento = ' Starting...'
tiempo = time.gmtime(time.time())
Log(log_file, tiempo, evento)
try:
    serv = socketserver.UDPServer((server_ip, int(server_port)), RegisterHandler)
    print('Server BigBangServer listening at port ' + server_port + '...')
    serv.serve_forever()
except KeyboardInterrupt:
    evento = ' Finishing proxy_registrar.'
    tiempo = time.gmtime(time.time())
    Log(log_file, tiempo, evento)
sys.exit('\r\nFinished BigBangServer')
