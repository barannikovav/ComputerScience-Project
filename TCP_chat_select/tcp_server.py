import socket
import select
import traceback
import sys
import time
from collections import deque

# Connection Data
host = '0.0.0.0'
BUFSIZE = 2048
ENCODE = 'utf-8'
TCP_KEEPALIVE_TIMEOUT = 300
QUEUELEN = 10


# Lists for program work

connection_list = []
nicknames = []
permissions  = []
addresses = []
message_queue = deque([])

#-----------------------------------------------------------------------------

# Send message to all users of chat
def broadcast(message, user=None):
    add_to_queue(message)
    for sock in connection_list:
        if sock != server_socket and sock != user:
            try:
                sock.sendall(message.encode(ENCODE))
            except Exception as e:
                if e.errno == 57:
                    pass
                else:
                    sock.shutdown(SHUT_RDWR)
                    sock.close()
                    remove_client(sock)

#-----------------------------------------------------------------------------

def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = connection_list[name_index]
        connection_list.remove(client_to_kick)
        client_to_kick.send('<KICKED>'.encode(ENCODE))
        time.sleep(0.5)
        client_to_kick.close()
        del nicknames[name_index]
        del permissions[name_index]
        del addresses[name_index]
        broadcast(f'[Server]: {name} was kicked from server!')
    else:
        print("[System]: Trying to kick unknown user")

#-----------------------------------------------------------------------------

def disconnect_client(user):
    if user in connection_list:
        index = connection_list.index(user)
        connection_list.remove(user)
        nickname = nicknames[index]
        del nicknames[index]
        del permissions[index]
        del addresses[index]
        try:
            user.shutdown(socket.SHUT_RDWR)
            user.close()
        except Exception as e:
            if e.errno == 57:
                pass
            else:
                traceback.print_exc()
        
        broadcast(f"[Server]: [{nickname}] left the Chat!")
    else:
        print("[System]: Trying to disconnect unknown user")

#-----------------------------------------------------------------------------

def remove_client(client):
    if client in connection_list:
        index = connection_list.index(client)
        connection_list.remove(client)
        del nicknames[index]
        del permissions[index]
        del addresses[index]
    else:
        print("[System]: Trying to remove unknown user")

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

def request_processing(command, client, right_password):
    command = command.decode(ENCODE)
    if client in connection_list:
        if command.startswith('<NICK_'):
            index = connection_list.index(client)
            nicknames[index] = command[6:-1]

            # Print and broadcast nickname
            print(f"[System]: New user connected:[{command[6:-1]}]\n")
            broadcast(f"[Server]: [{command[6:-1]}] joined!")
            time.sleep(0.5)
            client.send("[Server]: Successfully connected to server!\n".encode(ENCODE))
            time.sleep(0.5)

            send_msg_history(client)
     
        elif command == '<EXIT>':
            disconnect_client(client)
        elif command.startswith('<PERMS_'):
            if right_password  != command[7:-1]:
                client.sendall("[Client]: Wrong password - access denied\n".encode(ENCODE))
            else:
                index = connection_list.index(client)
                permissions[index] = True
                client.sendall("[Client]: Admin perms obtained\n".encode(ENCODE))
        elif command.startswith('<KICK'):
            index = connection_list.index(client)
            if permissions[index] == True:
                kick_user(command[6:-1])
            else:
                client.sendall("[Client]: Command using denied: no admin rights\n".encode(ENCODE))

        elif command == '<USERLIST>':
            if not nicknames:
                client.sendall("[Server]: Sorry, userlist is empty!\n")
            else:
                message = ''
                for num, nickname in enumerate(nicknames, start = 0):
                    message = message + f"{num+1}: [{nickname}] {addresses[num]}\n"
                client.sendall(message.encode(ENCODE))
        else:
            client.sendall("[Client]: Unknown request\n")
    else:
        print("[System]: Unable to process request from unknown user")
        client.sendall("[Client]: Sorry, we can't identify your client! Unable to process request from unknown user\n".encode(ENCODE))
    


#-----------------------------------------------------------------------------


if __name__ == "__main__":

    # Setting up server
    host = str(input("Input server IP adress: "))
    port = int(input("Input server port: "))

    # AF_INET - internet socket, SOCK_STREAM - connection-based protocol for TCP, 
    # IPPROTO_TCP - choosing TCP
    print ("[System]: Creating the server socket")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Check and turn on TCP Keepalive
    x = server_socket.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
    if (x == 0):
        print ("[System]: Socket Keepalive off, turning on")
        x = server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        print ('[System]: setsockopt ' + str(x))
        # Overrides value (in seconds) for keepalive
        server_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPALIVE, TCP_KEEPALIVE_TIMEOUT)
    else:
        print ("[System]: Socket Keepalive already on")

    try:
        # Assigning IP and port num to socket
        server_socket.bind((host, port))
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

    #server_socket.setblocking(False)

    connection_list.append(server_socket)
    nicknames.append("Server")
    permissions.append(True)
    addresses.append( (host, port) )

    print ("[System]: Socket setup worked!")

    password = input('[System]: Input password for administrator permissions: ')

    try:
        while True:
            # Get the list of sockets that are ready to be read
            read_sockets, write_sockets, error_sockets = select.select(connection_list,[],[])

            # Process if we got data
            for sock in read_sockets:
                # New connection
                if sock == server_socket:
                    # Processing new client
                    client, address = server_socket.accept()
                    print(f"[System]: New connection with {str(address)} requested...")
                    client.sendall("<NICK>".encode(ENCODE))
                    connection_list.append(client)
                    nicknames.append("None")
                    permissions.append(False)
                    addresses.append(address)
                    print(connection_list)

                # Incoming message from a client
                else:
                    # Data received -> processing
                    print("Data received")
                    try:
                        message = client.recv(BUFSIZE)
                        if message:
                            if message.startswith(b'<'):
                                request_processing(message, client, password)
                            else:
                                if client in connection_list:
                                    index = connection_list.index(client)
                                    nickname = nicknames[index]
                                    message = f"[{nickname}]: {message.decode(ENCODE)}"
                                    broadcast(message, client)
                    except:
                        traceback.print_exc()
                        disconnect_client(client)
                        continue
    except KeyboardInterrupt:
        server_socket.shutdown(socket.SHUT_RDWR)
        server_socket.close()
        print("[System]: Shut down")

