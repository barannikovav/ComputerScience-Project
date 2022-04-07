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
ENCODE = 'ascii'
SOCKET_TIMEOUT = 5.0

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

# Listening to server and sending nickname
def receive():
    while True:
        try:
            # If received message is "NICK" - send nickname
            message = client.recv(BUFSIZE).decode(ENCODE)

            if message == 'NICK':
                client.sendall(nickname.encode(ENCODE))
                answer_message = client.recv(BUFSIZE).decode(ENCODE)
                if answer_message == 'PASSWORD':
                    client.sendall(password.encode(ENCODE))
                    if client.recv(BUFSIZE).decode(ENCODE) == 'DENIED':
                        print("[Client]: Wrong password - access denied")
                        client.shutdown(socket.SHUT_RDWR)
                        client.close()
                        os._exit(1)
            else:
                print(message)
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

# Sending messages
def write():
    while True:
        # Reading messages
        try: 
            message = f'{nickname}: {input("")}'
            print(message)
            if nickname.startswith('/admin'):
                message = message[len('/admin '):]
                print(message)
            if message[len(nickname)+2:].startswith('/'):
                if message[len(nickname)+len(': '):].startswith('/exit'):
                    print("[Client]: Ending session...")
                    client.sendall('EXIT'.encode(ENCODE)) 
                    client.shutdown(socket.SHUT_RDWR)
                    client.close()
                    print("[Client]: Session ended, good bye!")
                    os._exit(1)
                elif message[len(nickname)+len(': '):].startswith('/kick'):
                    if nickname.startswith('/admin'):
                        print(message[len(nickname)+len(": /kick_"):])
                        client.send(f'KICK {message[len(nickname)+len(": /kick_"):]}'.encode(ENCODE))
                    else:
                        print("[Client]: Commands using denied: no admin rights")

                #if nickname.startswith('/admin'):
                    #if message[len(nickname)+len(': '):].startswith('/help'):
                 #   if message[len(nickname)+len(': '):].startswith('/kick'):
                    # 2 for : and whitespace and 6 for /KICK_
                  #      client.send(f'KICK {message[len(nickname)+len(": /kick_"): ]}'.encode(ENCODE))
                   # else:
                    #    print("[Client]: Commands using denied: no admin rights")
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
