import time
from multiprocessing import Process, Lock, Pipe
from multiprocessing.sharedctypes import Value, Array
import pprint
import socket
import ctypes
from struct import *

from includes import config

#local
rtp_high_port = 5004
rtp_low_port = 5006
rtcp_receiver_port = 5009

#remote
rtp_receiver_ip = '192.168.2.66'
rtp_receiver_port = 5008



buffe_mutex = Lock()

def slice_bin_to_tuple(bin_string, indices):
            bin_string_tuple = [bin_string[s:e]for s,e in indices] # creating a list of all the values in binary string
            return tuple([int(e,2) for e in bin_string_tuple]) #converting all the values to int and putting them in the tuple

def parse_rtp_header(packet):
            vpxccm, payload, sequence_number, timestamp, ssrc = unpack('!BBHII', packet)
    
            #converting the first byte to different values
            vpxccm_bin = bin(vpxccm)[2:]
            indices = [(0,2), (2,3), (3,4), (4,7), (7,8)] #creating indices to splice the string at
            version, padding, ext_bit, cc, m = slice_bin_to_tuple(vpxccm_bin, indices)
    
            return {"version": version, "padding": padding, "ext_bit": ext_bit, "cc": cc, "m": m, "payload": payload, "sequence_number": sequence_number, "timestamp": timestamp, "ssrc": ssrc}

def changeToggle(toggle):
            while True:
                        time.sleep(20)
                        if toggle.value == 0:
                                    toggle.value = 1
                        else:
                                    toggle.value = 0
                        print("Toggle switched")

def sendTheBuffer(toggle, low_conn, high_conn, ip, port):
            sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            i = 0
            while True:
                        #time.sleep(0.5)
                        
                        if toggle.value == 0:
                                    packet = low_conn.recv()
                                    sock_server.sendto(packet, (ip, 5008))
                                    #print("Sending Low Resolution: %d"%len(packet))
                        else:
                                    packet=high_conn.recv()
                                    sock_server.sendto(packet, (ip, 5008))
                                    #print("Sending High Resolution: %d"%len(packet))
                        
                        i=i+1


def getBufferFromNetwork(conn, port, toggle, target_val, seq):
            try:
                        print('opening at port:%d'%port)
                        sock_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock_client.bind(('', port)) #change this to 5004 for RTP and 5005 for RTCP

                        seq_tuple = (-1,-1,-1)
                        #print('waiting to receive')
                        i = 0
                        pp = pprint.PrettyPrinter(indent = 4)
                        while True:
                                    if toggle.value == target_val:
                                                seq.value = seq.value+1
                                                packet, server = sock_client.recvfrom(4096)
                                                rtp_header = parse_rtp_header(packet[0:12])
                                                rtp_header_with_updated_sequence = pack('!BBHII', 128, rtp_header['payload'], seq.value, int(time.time()), rtp_header['ssrc'])
                                                rtp_data = packet[12:]
                                                print("Sequence: number: %d, Given: %d"%(rtp_header['sequence_number'],seq.value))
                                                conn.send(rtp_header_with_updated_sequence+rtp_data)
                                    i = i+1
            finally:
                        print('closing socket')
                        conn.close()
                        sock_client.close()
                        
            return

def receiveRTCP(port):
            try:
                        sock_rtcp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock_rtcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock_rtcp.bind(('', port)) 

                        
                        i = 0
                        pp = pprint.PrettyPrinter(indent = 4)
                        while True:
                                    print('Got rtcp')
                                    packet, server = sock_rtcp.recvfrom(4096)
                                    rtcp_receiver_report = unpack('!BBHIIIIIII', packet)
                                    if rtcp_receiver_report[9] < config['threshold']:
                                                toggle.value = 0
                                    else:
                                                toggle.value = 1
                                    print("Toggle updated:%d"%toggle.value)
                                    #print(rtcp_receiver_report)
                                    i = i+1
            finally:
                        print('closing socket')
                        conn.close()
                        sock_client.close()
                        
            return


if __name__ == '__main__':
            jobs = []
            mutex = Lock()     
            toggle = Value('i', 0, lock = mutex)
            seq = Value('i', 0)

            high_parent_conn, high_child_conn = Pipe()
            low_parent_conn, low_child_conn = Pipe()

            rtpBufferProcessLow = Process(target = getBufferFromNetwork, args = (low_child_conn,rtp_low_port, toggle, 0, seq))
            jobs.append(rtpBufferProcessLow)          

            rtpBufferProcessHigh = Process(target = getBufferFromNetwork, args = (high_child_conn,rtp_high_port, toggle, 1, seq))
            jobs.append(rtpBufferProcessHigh)

            sendBufferProcess = Process(target = sendTheBuffer, args = (toggle, low_parent_conn, high_parent_conn, rtp_receiver_ip,rtp_receiver_port))
            jobs.append(sendBufferProcess)

            receiveRTCPProcess = Process(target = receiveRTCP, args = (rtcp_receiver_port,))
            jobs.append(receiveRTCPProcess)

            #toggleProcess = Process(target = changeToggle, args = (toggle,))
            #jobs.append(toggleProcess)

            for job in jobs:
                        job.start()

