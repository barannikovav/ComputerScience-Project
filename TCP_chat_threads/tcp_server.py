import socket
import threading
import traceback
import sys
import os

#-----------------------------------------------------------------------------

# Connection Data
HOST = '127.0.0.1'
PORT = 65432
BUFSIZE = 2048
ENCODE = 'ascii'
PASSWORD = 'admin_1'
TCP_KEEPALIVE_TIMEOUT = 300
MSGLEN = 4096

#-----------------------------------------------------------------------------

# Setting up server

# AF_INET - internet socket, SOCK_STREAM - connection-based protocol for TCP, 
# IPPROTO_TCP - choosing TCP
# 5-second timeout to detect errors
print ("[System]: Creating the server socket")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
#server_socket.settimeout(SOCKET_TIMEOUT)

# Check and turn on TCP Keepalive
x = server_socket.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
if (x == 0):
    print ("[System]: Socket Keepalive off, turning on")
    x = server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    print ('[System]: setsockopt ' + str(x))
    # Overrides value (in seconds) for keepalive
    server_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPALIVE, 300)
else:
    print ("[System]: Socket Keepalive already on")

try:
    # Assigning IP and port num to socket
    server_socket.bind((HOST, PORT))
except socket.error:
    print ("[System]: Socket bind failed!")
    traceback.print_exc()
    sys.exit(1)

try:
    # Putting server into listening mode
    server_socket.listen(10)
except socket.error:
    print ("[System]: Socket listen failed!")
    traceback.print_exc()
    sys.exit(1)

server_socket.setblocking(True)

print ("[System]: Socket setup worked!")

#-----------------------------------------------------------------------------

# Lists for clients and nicknames
clients = []
nicknames = []

#-----------------------------------------------------------------------------

def mysend(socket, msg):
    totalsent = 0
    while totalsent < len(msg):
        print("send_mysend")
        sent = socket.send(msg[totalsent:])
        if sent == 0:
            raise RuntimeError("[System]: Socket connection broken")
        totalsent = totalsent + sent

#-----------------------------------------------------------------------------

def myreceive(socket):
    parts = []
    bytes_recorded = 0
    while bytes_recd < MSGLEN:
        part = socket.recv(min(MSGLEN - bytes_recorded, BUFSIZE)) 
        if part == b'':
            raise RuntimeError("[System]: Socket connection broken")
        parts.append(part)
        bytes_recorded = bytes_recorded + len(part)
    return b''.join(parts)

#-----------------------------------------------------------------------------

# Kicking user
def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('[System]: You were kicked from chat!', encode(ENCODE))
        client_to_kick.shutdown(socket.SHUT_RDWR)
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f'[Server]: {name} was kicked from server!'.encode(ENCODE))

#-----------------------------------------------------------------------------

# Send message to all users of chat
def broadcast(message):
    for client in clients:
        try:
            client.sendall(message)
        except socket.error:
            print("Socket.sendall error occured")
            traceback.print_exc()
            sys.exit(1)

#-----------------------------------------------------------------------------

# Handling msg from client
def handle(client):
    while True:
        try:
            # Trying to get msg and broadcast it
            message =b''

            try:
                message = client.recv(BUFSIZE)
            except:
                traceback.print_exc()

            if message == b'':
                raise RuntimeError("Socket connection broken")

            if  message.decode(ENCODE).startswith('KICK'):
                if nicknames[clients.index(client)].startswith('/admin'):
                    name_to_kick = msg.decode(ENCODE)[5:]
                    kick_user(name_to_kick)
                else:
                    client.send("Command using denied: no admin rights".encode(ENCODE))
            elif message.decode(ENCODE).startswith('EXIT'):
                if client in clients:
                    try:
                        client.send("test_msg".encode(ENCODE))
                    except socket.error:
                        client.shutdown(socket.SHUT_RDWR)
                        client.close()
                    index = clients.index(client)
                    clients.remove(client)
                    nickname = nicknames[index]
                    broadcast(f"[Server]: {nickname} left the Chat!".encode(ENCODE))
                    nicknames.remove(nickname)
                    break
            else:
                broadcast(message)

        except:
            print("Handle_exception")
            traceback.print_exc()
            # In case of error removing and closing clients
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.shutdown(socket.SHUT_RDWR)
                client.close()
                nickname = nicknames[index]
                broadcast(f"[Server]: {nickname} left the Chat!".encode(ENCODE))
                nicknames.remove(nickname)
                break
            sys.exit(1)

#-----------------------------------------------------------------------------

# Main function that will receive or listen
def receive(right_password="admin_1"):
    while True:
        # Accept connection
        client, address = server_socket.accept()
        print(f"[System]: New connection with {str(address)}")

        # Processing new client
        client.sendall("NICK".encode(ENCODE))
        nickname = client.recv(BUFSIZE).decode(ENCODE)

        if  nickname.startswith('/admin'):
            client.send('PASSWORD'.encode(ENCODE))
            password = client.recv(BUFSIZE).decode(ENCODE)
            if password  != right_password:
                client.sendall('DENIED'.encode(ENCODE))
                client.shutdown(socket.SHUT_RDWR)
                client.close()
                continue

        nicknames.append(nickname)
        clients.append(client)

        # Print and broadcast nickname
        print(f"[System]: New user connected:[{nickname}]")
        broadcast(f"[Server]: {nickname} joined!".encode(ENCODE))
        client.send("[System]: Successfully connected to server!".encode(ENCODE))

        # Starting new thread for handling client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

#-----------------------------------------------------------------------------

receive(input('[System]: Input password for administrator permissions: '))
