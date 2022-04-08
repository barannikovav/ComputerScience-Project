import socket
import threading
import traceback
import sys
import os
import time
from collections import deque

#-----------------------------------------------------------------------------

# Connection Data
HOST = '127.0.0.1'
PORT = 65432
BUFSIZE = 2048
ENCODE = 'utf-8'
PASSWORD = 'admin_1'
TCP_KEEPALIVE_TIMEOUT = 300
MSGLEN = 4096
QUEUELEN = 10

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

# Lists for clients, nicknames, permissions and addresses
clients = []
nicknames = []
permissions  = []
addresses = []
message_queue = deque([])

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

def add_to_queue(message):
    if len(message_queue) > 9:
        message_queue.popleft()

    message_queue.append(message)

#-----------------------------------------------------------------------------

def send_msg_history(client):
    if len(message_queue) > 1:
        queue = message_queue
        queue.pop()
        for msg in queue:
            msg = msg + '\n'
            client.sendall(msg.encode(ENCODE))

#-----------------------------------------------------------------------------

def request_processing(command, client):
    command = command.decode(ENCODE)
    if command == '<EXIT>':
        if client in clients:
            try:
                time.sleep(0.5)
                client.send("test_msg".encode(ENCODE))
            except socket.error:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
            index = clients.index(client)
            clients.remove(client)
            nickname = nicknames[index]
            nicknames.remove(nickname)
            del permissions[index]
            del addresses[index]
            broadcast(f"[Server]: {nickname} left the Chat!".encode(ENCODE))
            return True
    elif command == '<PERMS>':
        client.send('<PASSWORD>'.encode(ENCODE))
        time.sleep(0.5)
        password = client.recv(BUFSIZE).decode(ENCODE)
        if password  != right_password:
            client.sendall("[Client]: Wrong password - access denied".encode(ENCODE))
        else:
            index = clients.index(client)
            permissions[index] = True
            client.sendall("[Client]: Admin perms obtained".encode(ENCODE))
    elif command.startswith('<KICK'):
        if client in clients:
            index = clients.index(client)
            if permissions[index] == True:
                print(command[6:len(command)-1])
                kick_user(command[6:len(command)-1])
            else:
                client.sendall("[Client]: Command using denied: no admin rights")

        else:
            client.sendall("[Client]: Request from unknown user".encode(ENCODE))
    elif command == '<USERLIST>':
        if not nicknames:
            client.sendall("[Server]: Sorry, userlist is empty!")
        else:
            message = ''
            for num, nickname in enumerate(nicknames, start = 0):
                #print(num)
                message = message + f"{num+1}: [{nickname}] {addresses[num]}\n"
            client.sendall(message.encode(ENCODE))
    else:
        client.sendall("[Client]: Unknown request")
    return False


#-----------------------------------------------------------------------------

# Kicking user
def kick_user(name):
    if name in clients:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('[System]: You were kicked from chat!', encode(ENCODE))
        client_to_kick.shutdown(socket.SHUT_RDWR)
        client_to_kick.close()
        nicknames.remove(name)
        del permissions[name_index]
        del addresses[index]
        broadcast(f'[Server]: {name} was kicked from server!')

#-----------------------------------------------------------------------------

# Send message to all users of chat
def broadcast(message, user=None):
    add_to_queue(message)
    for client in clients:
        if client == user:
            continue
        else:
            try:
                client.sendall(message.encode(ENCODE))
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

            if  message.startswith(b'<'):
                if request_processing(message, client): break
            else:
                if client in clients:
                    index = clients.index(client)
                    nickname = nicknames[index]
                    message = f"[{nickname}]: {message.decode(ENCODE)}"
                    broadcast(message, client)

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
                nicknames.remove(nickname)
                del permissions[index]
                del addresses[index]
                broadcast(f"[Server]: {nickname} left the Chat!")
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

        nicknames.append(nickname)
        clients.append(client)
        permissions.append(False)
        addresses.append(address)

        # Print and broadcast nickname
        print(f"[System]: New user connected:[{nickname}]")
        broadcast(f"[Server]: {nickname} joined!")
        time.sleep(0.5)
        client.send("[Server]: Successfully connected to server!".encode(ENCODE))
        time.sleep(0.5)
        send_msg_history(client)


        # Starting new thread for handling client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

#-----------------------------------------------------------------------------

receive(input('[System]: Input password for administrator permissions: '))
