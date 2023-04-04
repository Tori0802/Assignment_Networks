from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

# Extension
import time
import datetime

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client2:
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
    FORWARD = 4
    BACKWARD = 5



    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master                                    # Tk object to design GUI
        self.master.protocol("WM_DELETE_WINDOW",self.handler)   # Design button X on the title bar which behaviour is "handler" function
        self.createWidgets()                                    # Create GUI
        self.serverAddr = serveraddr                            # Server address
        self.serverPort = int(serverport)                       # Server port
        self.rtpPort = int(rtpport)                             # Rtp Port
        self.fileName = filename                                # Filename
        self.rtspSeq = 0                                        # Numbers of transitions
        self.sessionId = 0                                      # Unique Identifier
        self.requestSent = -1                                   # Code Request
        self.teardownAcked = 0                                  # Flag Teardown
        self.connectToServer()                                  # Connect to server
        self.frameNbr = 0                                       # Number of packets

        # Statistic datas
        self.packetTotal = 0                                    # Total packets
        self.packetReceived = 0                                 # Total of received packets
        self.packetLost = 0                                     # Total of loss packets
        self.lastSeqNum = 0                                     # Last sequence number packet

        self.totalBytes = 0                                     # Total number of bytes sent
        self.timerStart = 0                                     # Timeline for getting started
        self.timerEnd = 0                                       # Timeline for getting ended
        self.timer = 0                                          # Video playing total time

        self.totalJitter = 0                                    # Total Jitter time
        self.arrivaltimeofPreviousPacket = 0                    # Arrival time of previous packet
        self.lastPacketSpacing = 0                              # Time difference between 2 packets

        # More functional
        self.currTime = 0                                       # Current time
        self.totalTime = 0                                      # Total time (Idle)
        self.isForward = 0                                      # Flag forward
        self.isBackward = 0                                     # Flag backward



    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3, bg="#6B37C4")
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=2, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3, bg="#40A34A")
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3, bg="#E8DD68")
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3, bg="#FC8585")
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=2, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19, bg="#85CBD9")
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

        # Create a label to display total time of the movie
        self.totalTimeBox = Label(self.master, width=16, text="Total time: 00:00", bg="#A5D2EB")
        self.totalTimeBox.grid(row=1, column=3, columnspan=1, padx=5, pady=5)

        # Create a label to display remaining time of the movie
        self.remainTimeBox = Label(self.master, width=16, text="Remaining time: 00:00", bg="#A5D2EB")
        self.remainTimeBox.grid(row=1, column=0, columnspan=1, padx=5, pady=5)

        # Create forward button
        self.forward = Button(self.master, width=15, padx=3, pady=3, bg="#00EBC1", fg="black")
        self.forward["text"] = "⫸⫸"
        self.forward["command"] = self.forwardMovie
        self.forward["state"] = "disabled"
        self.forward.grid(row=1, column=2, sticky=E + W, padx=2, pady=2)

        # Create backward button
        self.backward = Button(self.master, width=15, padx=3, pady=3, bg="#00EBC1", fg="black")
        self.backward["text"] = "⫷⫷"
        self.backward["command"] = self.backwardMovie
        self.backward["state"] = "disabled"
        self.backward.grid(row=1, column=1, sticky=E + W, padx=2, pady=2)



    def setupMovie(self):
        """Setup button handler."""
        # TODO
        # -------------
        # If state = INIT, send SETUP request to server
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)
        self.frameNbr = 0
        self.packetTotal = 0
        self.packetReceived = 0
        self.packetLost = 0
        self.lastSeqNum = 0

        self.totalBytes = 0
        self.timerStart = 0
        self.timerEnd = 0
        self.timer = 0

        self.totalJitter = 0
        self.arrivaltimeofPreviousPacket = 0
        self.lastPacketSpacing = 0

    def exitClient(self):
        """Teardown button handler."""
        # TODO
        # -----------
        # If state != INIT, implement following operations
        if self.state != self.INIT:
            self.sendRtspRequest(self.TEARDOWN)

            # Delete the cache image from video
            for i in os.listdir():
                if i.find(CACHE_FILE_NAME) == 0:
                    os.remove(i)
            time.sleep(0.5)

            # Reset GUI
            self.forward["state"] = "disabled"
            self.backward["state"] = "disabled"
            self.state = self.INIT
            self.rtspSeq = 0
            self.sessionId = 0
            self.requestSent = -1
            self.teardownAcked = 0
            self.connectToServer()
            self.label.pack_forget()
            self.label.image = ''
            self.currTime = 0
    def pauseMovie(self):
        """Pause button handler."""
        # TODO
        # -------------
        # If state = PLAYING, send an PAUSE request to server
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        # TODO
        # -------------
        # If state == READY, the following operations will be implemented

        if self.state == self.READY:

            self.forward["state"] = "normal"
            self.backward["state"] = "normal"

            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()

            # Clear the playEvent
            self.playEvent = threading.Event()
            self.playEvent.clear()

            # Send an PLAY request to server
            self.sendRtspRequest(self.PLAY)



    def forwardMovie(self):
        self.sendRtspRequest(self.FORWARD)
        self.isForward = 1



    def backwardMovie(self):
        self.sendRtspRequest(self.BACKWARD)
        if self.frameNbr <= 50:
            self.frameNbr = 0
        else:
            self.frameNbr -= 50

        self.isBackward = 1



    def listenRtp(self):
        """Listen for RTP packets."""
        # TODO
        # -----------
        while True:
            try:
                # Create "data" to read and decode received packet
                data = self.rtpSocket.recv(20480)  # Maximum buffer 20480 bits -> 20 bytes
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)  # Decode data

                    # Make the packet receive has the class type of packet
                    arrivalTime = time.time()
                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    # Add number of bytes of latest packet
                    self.totalBytes += len(rtpPacket.getPayload())

                    # Discard the late packet and update frame
                    if currFrameNbr > self.frameNbr:
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

                        # Update current Time
                        self.currTime = int(currFrameNbr * 0.05)
                        self.totalTimeBox.configure(text="Total time: %02d:%02d" % (self.totalTime // 60, self.totalTime % 60))
                        self.remainTimeBox.configure(text="Remaining time: %02d:%02d" % ((self.totalTime - self.currTime) // 60, (self.totalTime - self.currTime) % 60))

                        # Statistic Update
                        self.packetTotal += 1
                        self.packetReceived += 1
                        if (self.lastSeqNum + 1 != currFrameNbr) and (not (self.isForward | self.isBackward)):
                            self.packetLost += currFrameNbr - self.lastSeqNum - 1

                        # Calculate Total Jitter
                        if self.lastSeqNum + 1 == currFrameNbr and currFrameNbr > 1:
                            currSpacing = arrivalTime - self.arrivaltimeofPreviousPacket
                            self.totalJitter += abs(currSpacing - self.lastPacketSpacing) / 16
                            self.arrivaltimeofPreviousPacket = arrivalTime
                            self.lastPacketSpacing = currSpacing

                        self.arrivaltimeofPreviousPacket = arrivalTime
                        self.lastSeqNum = currFrameNbr
            # Exception
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    self.displayStatistics()
                    break

                # Upon receiving ACK for TEARDOWN request, close the RTP socket
                if self.teardownAcked == 1:
                    self.displayStatistics()
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break



    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        # TODO
        # ------------
        cache = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cache, "wb")
        file.write(data)
        file.close()

        return cache

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        # TODO
        # ------------
        # Open image file
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        # Configure and update to the GUI
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        # TODO
        # -------------
        # Create and connect rtspSocket
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        # If connection failed, show message box
        except:
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------
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
        # FORWARD request
        elif requestCode == self.FORWARD:
            # Update RTSP sequence number
            self.rtspSeq = self.rtspSeq + 1
            # Write RTSP request to be sent
            request = "FORWARD %s RTSP/1.0 \nCSeq: %d \nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            # Keep track of the sent request
            self.requestSent = self.FORWARD

        # -------------
        # BACKWARD request
        elif requestCode == self.BACKWARD:
            # Update RTSP sequence number
            if self.rtspSeq <= 25:
                self.rtspSeq = 0
            else:
                self.rtspSeq -= 25
            # Write RTSP request to be sent
            request = "BACKWARD %s RTSP/1.0 \nCSeq: %d \nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            # Keep track of the sent request
            self.requestSent = self.BACKWARD

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
        # TODO
        # -------------
        while True:
            reply = self.rtspSocket.recv(1024)  # 1024 bytes

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
        # TODO
        # -------------

        # Decode returned syntax from server
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
                        # Update Total time
                        self.totalTime = float(cmds[3].split(' ')[1])
                        # Next state: READY
                        self.state = self.READY
                        # Open RTP port
                        self.openRtpPort()

                    # -------------
                    # PLAY request
                    elif self.requestSent == self.PLAY:
                        # Next state: PLAYING
                        self.state = self.PLAYING

                        # Start timer if not already playing
                        if self.timerStart == 0:
                            self.timerStart = time.time()
                            self.arrivaltimeofPreviousPacket = time.time()

                    # -------------
                    # PAUSE request
                    elif self.requestSent == self.PAUSE:
                        # Next state: READY
                        self.state = self.READY

                        # Set timer end when paused and playing previously
                        if self.timerStart > 0:
                            self.timerEnd = time.time()
                            self.timer += self.timerEnd - self.timerStart
                            self.timerStart = 0

                        # Exit play thread exits
                        # A new thread is created on resume
                        self.playEvent.set()

                    # -------------
                    # TEARDOWN request
                    elif self.requestSent == self.TEARDOWN:
                        # Next state: INIT
                        self.state = self.INIT
                        # Set timer end when paused and playing previously
                        self.timerEnd = time.time()
                        self.timer += self.timerEnd - self.timerStart
                        # Set flag teardownAcked active
                        self.teardownAcked = 1



    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
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
            tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # TODO
        if (self.state == self.PLAYING):
            self.pauseMovie()
        # Message box
        if tkinter.messagebox.askokcancel("Quit", "Are you sure?"):
            # Exit client and socket
            if self.state != self.INIT:
                self.sendRtspRequest(self.TEARDOWN)
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
            # Close the Gui window
            self.master.destroy()
            sys.exit(0)

    def displayStatistics(self):
        """Displays observed statistics"""
        lossRate = ((self.packetLost) / (self.packetTotal)) * 100
        top1 = Toplevel()
        top1.title("Statistics")
        top1.geometry('300x200')
        Lb = Listbox(top1, width=100, height=80)
        Lb.insert(1, " Statistics ")
        Lb.insert(2, " ")
        Lb.insert(3, "Current Packets No.%d " % self.frameNbr)
        Lb.insert(4, "Total Streaming Packets: %d packets" % self.packetTotal)
        Lb.insert(5, "Total Packets Received: %d packets" % self.packetReceived)
        Lb.insert(6, "Total Packets Lost: %d packets" % self.packetLost)
        Lb.insert(7, "Packet Loss Rate: %d%%" % lossRate)
        Lb.insert(8, " ")
        Lb.insert(9, "Play time: %.2f seconds" % self.timer)
        Lb.insert(10, "Bytes received: %d bytes" % self.totalBytes)
        Lb.insert(11, "Video Data Rate: %d bytes per second" % (self.totalBytes / self.timer))
        Lb.insert(12, " ")
        Lb.insert(13, "Total Jitter: %.3fms" % (self.totalJitter * 1000))
        Lb.insert(14, "Average Jitter: %.3fms" % ((self.totalJitter / self.packetReceived) * 1000))
        Lb.pack()