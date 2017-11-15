#!/bin/env python
#
___author__ = 'Adam Grigolato'
__version__ = '0'
#IMPORTS
import socket
import sys
import os
import time
import datetime
import signal
#import PcapFile
import select
import Queue
#
servsock = "./socketin.sock"
clientsock = "./socketout.sock"
pcapfile = "traffic.pcap"


def sock(stype, sfile):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if stype == "server":
        try:
            os.unlink(sfile)
        except OSError:
            if os.path.exists(sfile):
                raise
        sock.bind(sfile)
        sock.listen(5)
        return sock
    elif stype == "client":
        try:
            sock.connect(sfile)
        except socket.error, msg:
            print msg
        return sock


def signal_handler(signal, frame):
    print "Bailing on Ctrl+C"
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    server = sock("server",servsock)
    client = sock("client",clientsock)
    pairs = {}
    inputs = [ server, client]
    outputs = [ ]
    message_queues = {}
    while inputs:
        readable, writable, exception = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is server:
                conn, caddr = s.accept()
                conn.setblocking(0)
                inputs.append(conn)
                pairs[conn] = client
                pairs[client] = conn
                message_queues[pairs[conn]] = Queue.Queue()
            else:
                if s == client:
                    message_queues[pairs[s]] = Queue.Queue()
                data = s.recv(65535)
                if data:
                    message_queues[pairs[s]].put(data)
                    if pairs[s] not in outputs:
                        outputs.append(pairs[s])
        
        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except Queue.Empty:
                outputs.remove(s)
            else:
                t = datetime.datetime.now()
                if s is pairs[client]:
                    print('<<'+str(t.hour)+'/'+str(t.minute)+'/'+str(t.second)+'/'+str(t.microsecond)+":"+str(next_msg))
                elif s is client:
                    print('>>'+str(t.hour)+'/'+str(t.minute)+'/'+str(t.second)+'/'+str(t.microsecond)+":"+str(next_msg))
                s.send(next_msg)
        for s in exception:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]
