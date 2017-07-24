#packet sniffer in python
#for linux

import socket
from struct import *
from multiprocessing import Process, Lock, Pipe, Value
import random
import sched, time

ip_send_rtcp_on = '127.0.0.1'
port_send_rtcp_on = 5009
rtcp_sending_delay = 30 #in seconds

def giveRandom(givenRange=(0,5000)):
	return random.randint(givenRange[0],givenRange[1])

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

def sniff_rtp(conn):
	#create an INET RAW socket
	s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
	ip_header_length = 20
	udp_header_length = 8
	rtp_header_length = 12

	print 'Socket opened to sniff UDP packets'

	#receive a packet
	while True:
		packet, server = s.recvfrom(65536)
		ip_header = unpack('!BBHHHBBH4s4s',packet[0:ip_header_length])
		destination_address = socket.inet_ntoa(ip_header[9])
		source_port, destination_port, udp_packet_length, checksum = unpack('!HHHH', packet[ip_header_length:ip_header_length+udp_header_length])
		#print 'Source port: {}, Desination port: {}, Length: {}, Checksum: {}'.format(source_port, destination_port, udp_packet_length, checksum)

		rtp_packet_length = udp_packet_length-udp_header_length
		rtp_packet = packet[ip_header_length+udp_header_length:ip_header_length+udp_header_length+rtp_packet_length]
		#print len(rtp_packet)

		if destination_address == '192.168.2.66' and destination_port == 5004:
			rtp_header = rtp_packet[0:12]
			conn.send(parse_rtp_header(rtp_header))

def send_rtcp_packet(sc, sock, ssrc, frac_cum, extended, interval_gitter, last_sr, delay): 
    print "Doing stuff after 30 s..."
    vprc = 129
    rt = 201
    length = 64
    if delay.value == 0:
    	delay.value = 1
    else:
    	delay.value = 0
    rtcp_packet = pack('!BBHIIIIIII', vprc, rt, length, ssrc.value, ssrc.value, frac_cum.value, extended.value, interval_gitter.value, last_sr.value, delay.value)
    
    #send the socket to the relay
    sock.sendto(rtcp_packet, (ip_send_rtcp_on, port_send_rtcp_on))

    print unpack('!BBHIIIIIII', rtcp_packet)
    sc.enter(30, 1, send_rtcp_packet, (sc,sock,ssrc,frac_cum, extended, interval_gitter, last_sr, delay))
    




def processRTP(conn,ssrc, frac_cum, extended, interval_gitter, last_sr, delay):
	print 'Sending RTCP process opened'

	#initializing the data structure
	frac_cum.value = giveRandom()
	extended.value = giveRandom()
	interval_gitter.value = giveRandom()
	last_sr.value = giveRandom()
	delay.value = giveRandom(range(0,2))


	while True:
		rtp_header = conn.recv()
		ssrc.value = rtp_header['ssrc']
		#frac_cum.value = giveRandom()
		#extended.value = giveRandom()
		#interval_gitter.value = giveRandom()
		#last_sr.value = giveRandom()
		#delay.value = giveRandom(range(0,10))
		#print rtp_header['ssrc']


if __name__ == '__main__':
	jobs = []
	parent, child = Pipe()

	rtpSniffingProcess = Process(target = sniff_rtp, args=(child,))
	jobs.append(rtpSniffingProcess)

	lock = Lock()
	ssrc = Value('d', 0.0, lock=lock)
	frac_cum = Value('d', 0.0, lock=lock)
	extended = Value('d', 0.0, lock=lock)
	interval_gitter = Value('d', 0.0, lock=lock)
	last_sr = Value('d', 0.0, lock=lock)
	delay = Value('d', 0.0, lock=lock)

	rtpProcessingProcess = Process(target = processRTP, args=(parent,ssrc,frac_cum, extended, interval_gitter, last_sr, delay))
	jobs.append(rtpProcessingProcess)

	for job in jobs:
		job.start()

	#create the socket to send the RTCP Receiver reports to relay
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# schedule a function that gets the data structure as the arguments
	s = sched.scheduler(time.time, time.sleep)
	s.enter(30, 1, send_rtcp_packet, (s,sock, ssrc,frac_cum, extended, interval_gitter, last_sr, delay))
	s.run()