import socket
import threading
import traceback
import time
import sys
import os

# Connection Data
HOST = '127.0.0.1'
PORT = 65432
BUFSIZE = 1024
ENCODE = 'utf-8'
SOCKET_TIMEOUT = 5.0

thread_stop = False

# Input nickname
nickname = input("[Client]: Input your nickname here: ")
if nickname.startswith('/admin'):
    password = input("[Client]: Enter password for admin: ")

#---------------------------------------------------------------------------------------------

# Connecting to server

# AF_INET - internet socket, SOCK_STREAM - connection-based protocol for TCP, 
# IPPROTO_TCP - choosing TCP
# 5-second timeout to detect errors
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
except:
    print("Error creating socket!")
    traceback.print_exc()
    sys.exit(1)
# Check and turn on TCP Keepalive
try:
    x = client.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
    if (x == 0):
        x = client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Overrides value (in seconds) for keepalive
        client.setsockopt(socket.SOL_TCP, socket.TCP_KEEPALIVE, 300)
except:
    print("Error processing TCP Keepalive!")
    traceback.print_exc()
    sys.exit(1)   

try: 
    client.connect((HOST, PORT))
except:
    print ("Socket connect failed!")
    traceback.print_exc()
    sys.exit(1)

print ("[Client]: Socket connect worked!")

#---------------------------------------------------------------------------------------------

def commands_processing(command, client):
    if command == '/exit':
        print("[Client]: Ending session...")
        client.sendall('<EXIT>'.encode(ENCODE))
        client.shutdown(socket.SHUT_RDWR)
        client.close()
        print("[Client]: Session ended, good bye!")
        os._exit(1)
    elif command == '/admin':
        client.sendall(('<PERMS_'+input("Input password: ")+'>').encode(ENCODE))
    elif command.startswith('/kick'):
        print(command[6:])
        client.sendall(f'<KICK_{command[6:]}>'.encode(ENCODE))
    elif command == '/userlist':
        client.sendall('<USERLIST>'.encode(ENCODE))
    else:
        print("[Client]: Unknown command")



#---------------------------------------------------------------------------------------------

# Listening to server and sending nickname
def receive():
    while True:
        try:
            # If received message is "NICK" - send nickname
            message = client.recv(BUFSIZE).decode(ENCODE)
            if message == '':
                raise RuntimeError
        except socket.error:
            print("Socket error occured!")
            traceback.print_exc()
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            os._exit(1)
        except:
            print("Non-socket error occured!")
            traceback.print_exc()
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            os._exit(1)

        if message == 'NICK':
            client.sendall(nickname.encode(ENCODE))
        elif message == '<KICKED>':
            print('[System]: You were kicked from chat!')
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            print("[Client]: Session ended, good bye!")
            os._exit(1)
        else:
            print(message)
        

# Sending messages
def write():
    while True:
        # Reading messages
        try:
            message = input('')
            if message.startswith('/'):
                commands_processing(message, client)
            else: 
                client.sendall(message.encode(ENCODE))
        except socket.error:
            print("Socket error occured!")
            traceback.print_exc()
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            os._exit(1)
        except:
            print("Non-socket error occured!")
            traceback.print_exc()
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            os._exit(1)


# Starting threads
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
