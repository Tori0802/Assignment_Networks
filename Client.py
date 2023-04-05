from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

# Extension libraries
import time

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	# States
	INIT = 0
	READY = 1
	PLAYING = 2

	# State variable
	state = INIT

	# Code requests
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3



	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master										# Tk object to design GUI
		self.master.protocol("WM_DELETE_WINDOW", self.handler)		# Design button X on the title bar which behaviour is "handler" function
		self.createWidgets()										# Create GUI
		self.serverAddr = serveraddr								# Server address
		self.serverPort = int(serverport)							# Server port
		self.rtpPort = int(rtpport)									# Rtp Port
		self.fileName = filename									# Filename
		self.rtspSeq = 0											# Numbers of transitions in one session
		self.sessionId = 0											# Unique Identifier
		self.requestSent = -1										# Code Request
		self.teardownAcked = 0										# Flag Teardown
		self.connectToServer()										# Connect to server
		self.frameNbr = 0											# Number of packets



	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3,  bg="#6B37C4")
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3, bg="#40A34A")
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3, bg="#E8DD68")
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3, bg="#FC8585")
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=25, bg="#C7DAEB")
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 



	def setupMovie(self):
		"""Setup button handler."""
		# TODO
		# -------------
		# If state == INIT, send SETUP request to server
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)



	def exitClient(self):
		"""Teardown button handler."""
		#TODO
		#-----------
		# If state != INIT, implement following operations
		if self.state != self.INIT:
			# Send SETUP request to server
			self.sendRtspRequest(self.TEARDOWN)

			# Delete caches image from video
			for i in os.listdir():
				if i.find(CACHE_FILE_NAME) == 0:
					os.remove(i)
			time.sleep(1)

			# Reset GUI
			self.state = self.INIT
			self.rtspSeq = 0
			self.sessionId = 0
			self.requestSent = -1
			self.teardownAcked = 0
			self.connectToServer()
			self.frameNbr = 0
			self.label.pack_forget()
			self.label.image = ''



	def pauseMovie(self):
		"""Pause button handler."""
		# TODO
		# -------------
		# If state == PLAYING, send an PAUSE request to server
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)



	def playMovie(self):
		"""Play button handler."""
		# TODO
		# -------------
		# If state == READY, the following operations will be implemented
		if self.state == self.READY:

			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()

			# Initialize and clear an event object that is used to pause and resume the video playback in the client
			self.playEvent = threading.Event()
			self.playEvent.clear()

			# Send an PLAY request to server
			self.sendRtspRequest(self.PLAY)



	def listenRtp(self):
		"""Listen for RTP packets."""
		#TODO
		#-----------
		while True:
			try:
				# Create "data" to read and decode received packet
				data = self.rtpSocket.recv(20480)  							# Maximum buffer 20480 bits -> 20 bytes
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)  								# Decode data

					# Retrieve and update the sequence number of the current packet
					currFrameNbr = rtpPacket.seqNum()
					print("Current Seq Num: " + str(currFrameNbr))

					# If currentSeqNum > previousSeqNum, writing the frame to the output file
					# Retrieve the latest packet, decompress and display frame on the screen
					if currFrameNbr > self.frameNbr:
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

				# Exception
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet():
					break

				# Upon receiving ACK for TEARDOWN request, close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break



	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		#TODO
		#------------
		# Create and open cache
		cache = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cache, "wb")
		file.write(data)
		file.close()
		return cache



	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		#TODO
		#------------
		# Open image file
		photo = ImageTk.PhotoImage(Image.open(imageFile))

		# Configure and update to the GUI
		self.label.configure(image=photo, height=380)
		self.label.image = photo



	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		#TODO
		#-------------
		# Initialize a new TCP socket (self.rtspSocket)
		# Create and connect rtspSocket to the RTSP server address and port
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))

		# If connection failed, show message box to notify connection failed
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)



	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""
		#TODO
		#-------------
		# TO COMPLETE
		#-------------
		# SETUP request
		if requestCode == self.SETUP and self.state == self.INIT:
			# Create thread recvRtspReply
			threading.Thread(target=self.recvRtspReply).start()
			# Update RTSP sequence number
			self.rtspSeq += 1
			# Write RTSP request to be sent
			request = "SETUP %s RTSP/1.0 \nCSeq: %d \nTRANSPORT: RTP/UDP; client_port= %d" % (self.fileName, self.rtspSeq, self.rtpPort)
			# Keep track of the sent request
			self.requestSent = self.SETUP

		# -------------
		# PLAY request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number
			self.rtspSeq = self.rtspSeq + 1
			# Write RTSP request to be sent
			request = "PLAY %s RTSP/1.0 \nCSeq: %d \nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
			# Keep track of the sent request
			self.requestSent = self.PLAY

		# -------------
		# PAUSE request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number
			self.rtspSeq = self.rtspSeq + 1
			# Write RTSP request to be sent
			request = "PAUSE %s RTSP/1.0\nCSeq: %d \nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
			# Keep track of the sent request
			self.requestSent = self.PAUSE

		# -------------
		# TEARDOWN request
		elif requestCode == self.TEARDOWN and self.state != self.INIT:
			# Update RTSP sequence number
			self.rtspSeq = self.rtspSeq + 1
			# Write RTSP request to be sent
			request = "TEARDOWN %s RTSP/1.0 \nCSeq: %d \nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
			# Keep track of the sent request
			self.requestSent = self.TEARDOWN

		# -------------
		# Exception
		else:
			return

		# -------------
		# Send the RTSP request using rtspSocket
		self.rtspSocket.send(request.encode())
		print('\nData sent:\n' + request)



	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		#-------------
		while True:
			reply = self.rtspSocket.recv(1024) 	# 1024 bytes

			# RTSP socket keep adding and parse the new data
			if reply:
				self.parseRtspReply(reply.decode("utf-8"))

			# Close the RTSP socket if request is TEARDOWN
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break


	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		#-------------

		# Decode returned command from server
		cmds = data.split('\n')
		seqNum = int(cmds[1].split(' ')[1])

		# Process only if the server reply's sequence number == the request's sequence number
		if seqNum == self.rtspSeq:
			session = int(cmds[2].split(' ')[1])
			# Setup new RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(cmds[0].split(' ')[1]) == 200:
					# -------------
					# SETUP request
					if self.requestSent == self.SETUP:
						# Next state: READY
						self.state = self.READY
						# Open RTP port
						self.openRtpPort()

					# -------------
					# PLAY request
					elif self.requestSent == self.PLAY:
						# Next state: PLAYING
						self.state = self.PLAYING

					# -------------
					# PAUSE request
					elif self.requestSent == self.PAUSE:
						# Next state: READY
						self.state = self.READY
						# Signal the playback thread to exit by setting the playEvent object
						self.playEvent.set()

					# -------------
					# TEARDOWN request
					elif self.requestSent == self.TEARDOWN:
						# Next state: INIT
						self.state = self.INIT
						# Set flag teardownAcked active
						self.teardownAcked = 1



	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#TODO
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# Create a socket for IPv4 and use UDP protocol
		# socket.AF_INET - IPv4 ; socket.SOCK_DGRAM - UDP
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)

		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.rtpSocket.bind(('', self.rtpPort))
		except:
			# Show warning messagebox if unable to bind port
			tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)



	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		#-------------
		# First, pause video if video is playing
		if (self.state == self.PLAYING):
			self.pauseMovie()
		# Send a message box to check the Quit event
		if tkinter.messagebox.askokcancel("Quit", "Are you sure?"):
			# Exit client and socket
			if self.state != self.INIT:
				self.sendRtspRequest(self.TEARDOWN)
				self.rtpSocket.shutdown(socket.SHUT_RDWR)
				self.rtpSocket.close()
			# Close the Gui window
			self.master.destroy()
			sys.exit(0)