import socket
import select
import traceback
import time
import sys

# Connection Data
BUFSIZE = 1024
ENCODE = 'utf-8'
SOCKET_TIMEOUT = 2

#---------------------------------------------------------------------------------------------

def prompt() :
    sys.stdout.write('[You]: ')
    sys.stdout.flush()

#---------------------------------------------------------------------------------------------

def commands_processing(command, client_socket):
    if command == '/exit':
        print("[Client]: Ending session...")
        client_socket.sendall('<EXIT>'.encode(ENCODE))
        client_socket.close()
        print("[Client]: Session ended, good bye!")
        sys.exit(1)
    elif command == '/admin':
        client_socket.sendall(('<PERMS_'+input("Input password: ")+'>').encode(ENCODE))
    elif command.startswith('/kick'):
        client_socket.sendall(f'<KICK_{command[6:]}>'.encode(ENCODE))
    elif command == '/userlist':
        client_socket.sendall('<USERLIST>'.encode(ENCODE))
    else:
        print("[Client]: Unknown command")

#---------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Getting connection info
    host = str(input("Input server IP adress: "))
    port = int(input("Input server port: "))


    # Input nickname
    nickname = input("[Client]: Input your nickname here: ")

    # Connecting to server

    # AF_INET - internet socket, SOCK_STREAM - connection-based protocol for TCP, 
    # IPPROTO_TCP - choosing TCP
    # 5-second timeout to detect errors
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        client_socket.settimeout(SOCKET_TIMEOUT)
        #client_socket.setblocking(False)
    except:
        print("Error creating socket!")
        traceback.print_exc()
        sys.exit(1)
    # Check and turn on TCP Keepalive
    try:
        x = client_socket.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
        if (x == 0):
            x = client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Overrides value (in seconds) for keepalive
            client_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPALIVE, 300)
    except:
        print("Error processing TCP Keepalive!")
        traceback.print_exc()
        sys.exit(1)   

    # Connect to host
    try: 
        client_socket.connect((host, port))
    except Exception as e:
        if e.errno != 36:
            print ("Socket connect failed!")
            traceback.print_exc()
            sys.exit(1)

    print ("[Client]: Socket connect worked!")

    try:
        while True:
            socket_list = [sys.stdin, client_socket]

            # Get the list sockets that are readable
            read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])

            for sock in read_sockets:
                # Messages from remote server
                if sock == client_socket:
                    try:
                        message = client_socket.recv(BUFSIZE)
                    except Exception as e:
                        if e.errno == 54:
                            print("[System]: Disconnected from server")
                            print("[Client]: Session ended, good bye!")
                            sys.exit(1) 
                        else:
                            traceback.print_exc()
                    if not message:
                        print("[System]: Disconnected from server")
                        try:
                            client_socket.shutdown(socket.SHUT_RDWR)
                            client_socket.close()
                        except Exception as e:
                            if e.errno != 57:
                             traceback.print_exc()
                        print("[Client]: Session ended, good bye!")
                        sys.exit(1) 
                    else:
                        message = message.decode(ENCODE)
                        if message == '<NICK>':
                            client_socket.sendall((f"<NICK_{nickname}>").encode(ENCODE))
                        elif message == '<KICKED>':
                            print('[System]: You were kicked from chat!')
                            client_socket.shutdown(socket.SHUT_RDWR)
                            client_socket.close()
                            print("[Client]: Session ended, good bye!")
                            os._exit(1)
                        else:
                            print(message)
                else:
                    # User entered message
                    #msg = sys.stdin.readline()
                    msg = input("")
                    if msg.startswith('/'):
                        commands_processing(msg, client_socket)
                    else:
                        client_socket.sendall(msg.encode(ENCODE))
                        prompt()

    except KeyboardInterrupt:
        client_socket.shutdown(SHUT_RDWR)
        client_socket.close()
        print("[Client]: Shut down")







