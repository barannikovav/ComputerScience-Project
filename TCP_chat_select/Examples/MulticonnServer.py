# MulticonnServer.py

import sys
import socket
import selectors
import types


def main():
    # instantiate a selector
    sel = selectors.DefaultSelector()

    # define host, port, and number of connections
    host = '127.0.0.1'
    port = 65432
    num_conns = 2

    # instantiate a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind and listen
    sock.bind((host, port))
    sock.listen()
    print('listening on', (host, port))
    # set non-blocking
    sock.setblocking(False)
    # register the socket with the selector
    sel.register(sock, selectors.EVENT_READ, data=None)

    try:
        # while True:
        # ToDo: figure out why have to multiply x2 here ??
        for i in range(num_conns * 2):
            # execution waits here until ??
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(sel, key.fileobj)
                else:
                    service_connection(sel, key, mask)
                # end if
            # end for
        # end for
    except KeyboardInterrupt:
        print('caught keyboard interrupt, exiting')
    finally:
        sel.close()
    # end try
# end function

def accept_wrapper(sel, sock):
    conn, addr = sock.accept()  # Should be ready to read

    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
# end function

def service_connection(sel, key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print("closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print("echoing", repr(data.outb), "to", data.addr)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]
        # end if
    # end if
# end function

if __name__ == '__main__':
    main()
