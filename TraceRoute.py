import socket
import sys
import time
import struct

ICMP_ECHO_REQUEST = 8 #ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0 #ICMP type code for echo reply messages

#return messages from the receiveOnePing function
ICMP_ERROR_PACKET_CORRUPTION = -1
ICMP_ERROR_TIMEOUT = -2
ICMP_ERROR_TIME_EXCEEDED = -3
ICMP_UNKNOWN_ERROR = -4
ICMP_SUCCESS = 0

STATUS = 0
TIME = 1
IP = 2

PORT = 80
ID = 89

def checksum(string): 
    csum = 0
    countTo = (len(string) // 2) * 2  
    count = 0

    while count < countTo:
        thisVal = string[count+1] * 256 + string[count]
        csum = csum + thisVal 
        csum = csum & 0xffffffff  
        count = count + 2
    
    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff 
    
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum 
    answer = answer & 0xffff 
    answer = answer >> 8 | (answer << 8 & 0xff00)

    answer = socket.htons(answer)

    return answer

#slighly modified function from provided datagram.py
def create_packet(seq):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, ID, seq)
    payload = ""

    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + bytes(payload, "utf-8"))
    
    #make up a new header with the actual value
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0,
        my_checksum, 89, seq)
    
    return header + bytes(payload, "utf-8")


#method to receive a ping, to be called after sendOnePing
def receiveOnePing(icmpSocket, sendTime, seq):
    #handles timeouts
    try:
        packet, address = icmpSocket.recvfrom(1024)
    except socket.timeout:
        return (ICMP_ERROR_TIMEOUT, ICMP_ERROR_TIMEOUT, None)
    
    #this is the RTT
    timer = time.time() - sendTime

    #unpacks the 20-28th bytes of the received packet
    type, icmp_code, packetChecksum, id, sequence = struct.unpack("bbHHh", packet[20:28])
    
    #checker is used to check for correct checksum 
    checker = packet[20:22] + b"\0\0"+ packet[24:]    
    ip = address[0]
    
    #ttl exceeded error check
    if (type == 11):
        return (ICMP_ERROR_TIME_EXCEEDED, timer*1000, ip)

    #packet corruption check
    if (seq != sequence or id != ID or packetChecksum != checksum(checker)):
        return (ICMP_ERROR_PACKET_CORRUPTION, 0, ip)
    
    #only returns ICMP_SUCCESS when TTL is not exceeded and no other error codes are found
    return (ICMP_SUCCESS, timer * 1000, ip)

#sends one packet to the destination address
def sendOnePing(icmpSocket, destinationAddress, seq):
    header = create_packet(seq)
    icmpSocket.sendto(header, (destinationAddress, 80))
    
    #returns time packet was sent, for RTT calculation    
    return time.time()

#calls receiveOnePing and sendOnePing functions three times
def doThreePings(openSocket, ip, seq):
    #adds results into an Array
    times = []
    destinationIp = ""

    for i in range(3):
        time = sendOnePing(openSocket, ip, seq)
        returnCode = receiveOnePing(openSocket, time, seq)
        times.append(getReturnCode(returnCode))
        
        #gets packet IP from the last packet received (could lead to issues if last packet corrupted)
        if returnCode[IP] != None:
            destinationIp = returnCode[IP]

    #turns the IP from the packet into a host-address
    try:       
        print(socket.gethostbyaddr(destinationIp)[0], " | ", end = "")
    except:
         print(destinationIp, " | ", end = "")
    return times

#transforms ICMP codes into Program-Constants
def getReturnCode(returnCode):
    status = returnCode[STATUS]

    if status == ICMP_ERROR_TIME_EXCEEDED:
        return returnCode[TIME]
    elif status == ICMP_SUCCESS or status == ICMP_ERROR_TIMEOUT or status == ICMP_ERROR_PACKET_CORRUPTION:
        return status
    
    return ICMP_UNKNOWN_ERROR

def traceRoute(host, timeout):    
    #creates the socket
    openSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)
    openSocket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 1)
    openSocket.settimeout(timeout)
    
    #tries to get the hostname from the ip
    try:
        ip = socket.gethostbyname(host)
    except:
        print("Error Resolving Hostname")
        return
    
    
    ttl = 1
    while 1:
        print(ttl, end = " ")
        times = doThreePings(openSocket, ip, ttl)
        timeAvg = 0
        counter = 0

        #formating and printing
        for x in times: 
            if x == ICMP_ERROR_TIMEOUT or x == ICMP_ERROR_PACKET_CORRUPTION:
                print("*      ", end = "")
            elif x == ICMP_SUCCESS:
                print("Connection Successful! ")
                return
            else:
                print(str(round(x, 2)), "  ", end = "")
                #for the time average calculation
                timeAvg += x
                counter+= 1 
             
        ttl+= 1

        if counter != 0:
            #prints the average time calculation if packet was returned
            timeAvg = timeAvg / counter
            print("| Avg: ", str(round(timeAvg, 2)), end = "")
        print()

        openSocket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)


def runTraceRoute():
    #tests for command line arguments, runs traceRoute
    if (len(sys.argv) > 2):
        try:
            timeout = int(sys.argv[2])
        except:
            print("Enter a valid number as a timeout")
            return
    else:
        timeout = 1

    try:
        traceRoute(sys.argv[1], timeout)
    except:
        print("Hostname expected as argument")
        return


runTraceRoute()
    


