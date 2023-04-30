#!/usr/bin/env python3

import socket
import sys 

#handles 404 fnf error, sends response with appropriate web-page
def fnfErrorHandler(tcpSocket):
		with open("404.html", "rb") as requestedFile:
			buffer = requestedFile.read();

		tcpResponse = b"HTTP/1.1 404 Not Found \r\nContent-Type: text/html \r\n\r\n" + buffer;
		tcpSocket.send(tcpResponse);
		tcpSocket.close();

#handles a client request
def handleRequest(tcpSocket):
	print("Received Request")
	requestPacket, address = tcpSocket.recvfrom(256);
	
	#gets the method (GET, POST etc.) and requested file path
	requestPacket = requestPacket.split(b"\r\n");
	requestPacket = requestPacket[0].split(b" ");
	method = requestPacket[0];
	path = requestPacket[1][1:];

	#reads the requested file, if file isn't found, calls fnf handler
	try:
		with open(path, "rb") as requestedFile:
			buffer = requestedFile.read();
	except (FileNotFoundError):
		print("Requested file not found:", path);
		fnfErrorHandler(tcpSocket);
		return;

	#sends a packet with the file and the 200 status message 
	tcpResponse = b"HTTP/1.1 200 OK \r\nContent-Type: text/html \r\n\r\n" + buffer;
	tcpSocket.send(tcpResponse);

	tcpSocket.close();

def startServer(serverAddress, serverPort):
	print("Starting Server...")
	openSocket = socket.create_server((serverAddress, serverPort));
	
	#waits for a client request, if one is recieved handleRequest function is called  
	try:
		while True:
			openRequest = openSocket.accept();
			handleRequest(openRequest[0]);
	except:
		openSocket.close;

#sets the port to the one specified within arguments, otherwise to the default of 8000
def init():
	port = 8000;
	if (len(sys.argv) > 1):
		port = int(sys.argv[1]);
	
	try:
		startServer("", port)
	except:
		print("Something went wrong");


init();
