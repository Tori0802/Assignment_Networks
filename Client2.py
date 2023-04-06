from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

# Extension libraries
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
    DESCRIBE = 4
    FORWARD = 5
    BACKWARD = 6



    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master                                    # Tk object to design GUI
        self.master.protocol("WM_DELETE_WINDOW",self.handler)   # Design button X on the title bar which behaviour is "handler" function
        self.createWidgets()                                    # Create GUI
        self.serverAddr = serveraddr                            # Server address
        self.serverPort = int(serverport)                       # Server port
        self.rtpPort = int(rtpport)                             # Rtp Port
        self.fileName = filename                                # Filename
        self.rtspSeq = 0                                        # Numbers of transitions in one session
        self.sessionId = 0                                      # Unique Identifier
        self.requestSent = -1                                   # Code Request
        self.teardownAcked = 0                                  # Flag Teardown
        self.connectToServer()                                  # Connect to server
        self.frameNbr = 0                                       # Number of packets

        # Statistic datas
            # Packet loss rate
        self.packetTotal = 0                                    # Total packets
        self.packetReceived = 0                                 # Total of received packets
        self.packetLost = 0                                     # Total of loss packets
        self.lastSeqNum = 0                                     # Last sequence number packet

            # Video data rate
        self.totalBytes = 0                                     # Total number of bytes sent
        self.timerStart = 0                                     # Timeline for getting started
        self.timerEnd = 0                                       # Timeline for getting ended
        self.timer = 0                                          # Video playing total time

            # Jitter time
        self.totalJitter = 0                                    # Total Jitter time
        self.arrivaltimeofPreviousPacket = 0                    # Arrival time of previous packet
        self.lastPacketSpacing = 0                              # Time difference between 2 packets

        # Check Setup
        self.isSetup = 0                                        # Flag check setup

        # More functional
        self.currTime = 0                                       # Current time
        self.totalTime = 0                                      # Total time (Idle)
        self.isForward = 0                                      # Flag forward
        self.isBackward = 0                                     # Flag backward



    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
    def createWidgets(self):
        """Build GUI."""

        # Create Teardown button
        self.teardown = Button(self.master, width=10, padx=3, pady=3, bg="#FC8585")
        self.teardown["text"] = "⬛"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=2, column=0, padx=2, pady=2)

        # Create Backward button
        self.backward = Button(self.master, width=15, padx=3, pady=3, bg="#00EBC1", fg="black")
        self.backward["text"] = "≪"
        self.backward["command"] = self.backwardMovie
        self.backward["state"] = "disabled"
        self.backward.grid(row=2, column=1, sticky=E, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3, bg="#40A34A")
        self.start["text"] = "▶"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=2, sticky=E + W, padx=2, pady=2)

        # Create Pause button
        # self.pause = Button(self.master, width=20, padx=3, pady=3, bg="#E8DD68", fg="black")
        # self.pause["text"] = "⏸"
        # self.pause["command"] = self.pauseMovie
        # self.pause.grid(row=2, column=2, sticky=E + W, padx=2, pady=2)

        # Create Forward button
        self.forward = Button(self.master, width=15, padx=3, pady=3, bg="#00EBC1", fg="black")
        self.forward["text"] = "≫"
        self.forward["command"] = self.forwardMovie
        self.forward["state"] = "disabled"
        self.forward.grid(row=2, column=3, sticky=W, padx=2, pady=2)

        # Create Describe button
        self.describe = Button(self.master, width=10, padx=3, pady=3, bg="#6492BD", fg="black")
        self.describe["text"] = "⭐"
        self.describe["command"] = self.describeMovie
        self.describe["state"] = "disabled"
        self.describe.grid(row=2, column=4, sticky=W, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=25, bg="#C7DAEB")
        self.label.grid(row=0, column=0, columnspan=5, sticky=W + E + N + S, padx=5, pady=5)

        # Create a label to display Remaining Time of the movie
        self.remainTimeBox = Label(self.master, width=20, text="Remaining time: 00:00", bg="#F5E4D5")
        self.remainTimeBox.grid(row=1, column=1, columnspan=1, padx=5, pady=5)

        # Create a label to display Total Time of the movie
        self.totalTimeBox = Label(self.master, width=20, text="Total time: 00:00", bg="#F5E4D5")
        self.totalTimeBox.grid(row=1, column=3, columnspan=1, padx=5, pady=5)



    def setupMovie(self):
        """Setup button handler."""
        # TODO
        # -------------
        # If state = INIT, send SETUP request to server
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

        # Reset statistic datas
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

        # Set flag Setup
        self.isSetup = 1



    def exitClient(self):
        """Teardown button handler."""
        # TODO
        # -----------
        # Display Play button
        self.start = Button(self.master, width=20, padx=3, pady=3, bg="#40A34A")
        self.start["text"] = "▶"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=2, sticky=E + W, padx=2, pady=2)

        # If state != INIT, implement following operations
        if self.state != self.INIT:
            # Send SETUP request to server
            self.sendRtspRequest(self.TEARDOWN)

            # Delete the cache image from video
            for i in os.listdir():
                if i.find(CACHE_FILE_NAME) == 0:
                    os.remove(i)
            time.sleep(1)

            # Reset GUI
            # Cannot press Forward, Backward and Describe buttons
            self.forward["state"] = "disabled"
            self.backward["state"] = "disabled"
            self.describe["state"] = "disabled"

            # Reset Time Boxes
            self.totalTimeBox.configure(text="Total time: 00:00")
            self.remainTimeBox.configure(text="Remaining time: 00:00")

            self.state = self.INIT
            self.rtspSeq = 0
            self.sessionId = 0
            self.requestSent = -1
            self.teardownAcked = 0
            self.connectToServer()
            self.label.pack_forget()
            self.label.image = ''

            # Reset current time video and flag Setup
            self.currTime = 0
            self.isSetup = 0



    def pauseMovie(self):
        """Pause button handler."""
        # TODO
        # -------------
        # Display Play button
        self.start = Button(self.master, width=20, padx=3, pady=3, bg="#40A34A")
        self.start["text"] = "▶"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=2, sticky=E + W, padx=2, pady=2)

        # If state = PLAYING, send an PAUSE request to server
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)



    def playMovie(self):
        """Play button handler."""
        # TODO
        # -------------
        # Display Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3, bg="#E8DD68", fg="black")
        self.pause["text"] = "⏸"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, sticky=E + W, padx=2, pady=2)

        # If as the first time press "Play" button in the session, we first need to setup movie
        if self.isSetup == 0:
            self.setupMovie()

        # If state == READY, the following operations will be implemented
        if self.state == self.READY:
            # Enable Forward, Backward and Describe buttons
            self.forward["state"] = "normal"
            self.backward["state"] = "normal"
            self.describe["state"] = "normal"

            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()

            # Initialize and clear an event object that is used to pause and resume the video playback in the client
            self.playEvent = threading.Event()
            self.playEvent.clear()

            # Send an PLAY request to server
            self.sendRtspRequest(self.PLAY)



    def describeMovie(self):
        """Describe button handler"""
        # TODO
        # -------------
        # Send DESCRIBE request to server
        self.sendRtspRequest(self.DESCRIBE)



    def forwardMovie(self):
        """Forward button handler."""
        # TODO
        # -------------
        # Send a FORWARD request to server and set flag forward
        self.sendRtspRequest(self.FORWARD)
        self.isForward = 1



    def backwardMovie(self):
        """Backward button handler."""
        # TODO
        # -------------
        # Send a BACKWARD request to server
        self.sendRtspRequest(self.BACKWARD)
        # Update frameNbr
        numberFrames = int(self.totalTime / 0.05 * 0.05) # Divide 50 miliseconds * 5%
        if self.frameNbr <= numberFrames:
            self.frameNbr = 0
        else:
            self.frameNbr -= numberFrames
        # Set flag backward
        self.isBackward = 1



    def listenRtp(self):
        """Listen for RTP packets."""
        # TODO
        # -----------
        while True:
            try:
                # Create "data" to read and decode received packet
                data = self.rtpSocket.recv(20480)       # Maximum buffer 20480 bits -> 20 bytes
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)              # Decode data

                    # Snapshot the time when RtpPacket has arrived
                    # Retrieve and update the sequence number of the current packet
                    arrivalTime = time.time()
                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    # Incremental number of bytes of latest packet
                    self.totalBytes += len(rtpPacket.getPayload())

                    # If currentSeqNum > previousSeqNum, writing the frame to the output file
                    # Retrieve the latest packet, decompress and display frame on the screen
                    if currFrameNbr > self.frameNbr:
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

                        # Update current time, configure total time and remaining time to display the GUI
                        self.currTime = int(currFrameNbr * 0.05)
                        self.totalTimeBox.configure(text="Total time: %02d:%02d" % (self.totalTime // 60, self.totalTime % 60))
                        self.remainTimeBox.configure(text="Remaining time: %02d:%02d" % ((self.totalTime - self.currTime) // 60, (self.totalTime - self.currTime) % 60))

                        # Statistic Update
                        self.packetTotal += 1
                        self.packetReceived += 1
                            # Set condition to find lost packet
                        if (self.lastSeqNum + 1 != currFrameNbr) and (not (self.isForward | self.isBackward)):
                            self.packetLost += currFrameNbr - self.lastSeqNum - 1

                        # Calculate Total Jitter
                        if self.lastSeqNum + 1 == currFrameNbr and currFrameNbr > 1:
                            currSpacing = arrivalTime - self.arrivaltimeofPreviousPacket
                            self.totalJitter += abs(currSpacing - self.lastPacketSpacing) / 16
                            self.arrivaltimeofPreviousPacket = arrivalTime
                            self.lastPacketSpacing = currSpacing

                        # Update variables to implement next packet
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
        # Create and open cache
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
        self.label.configure(image=photo, height=300)
        self.label.image = photo



    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        # TODO
        # -------------
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
        # DESCRIBE request
        elif requestCode == self.DESCRIBE and self.state != self.INIT:
            # Update RTSP sequence number
            self.rtspSeq = self.rtspSeq + 1
            # Write RTSP request to be sent
            request = "DESCRIBE %s RTSP/1.0 \nCSeq: %d \nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            # Keep track of the sent request
            self.requestSent = self.DESCRIBE

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
            self.rtspSeq = self.rtspSeq + 1
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

                        # Start timer if not already playing by snapshot
                        if self.timerStart == 0:
                            self.timerStart = time.time()
                            self.arrivaltimeofPreviousPacket = time.time()

                    # -------------
                    # PAUSE request
                    elif self.requestSent == self.PAUSE:
                        # Next state: READY
                        self.state = self.READY

                        # Set timer end when paused and playing previously
                        # Calculate data time
                        if self.timerStart > 0:
                            self.timerEnd = time.time()
                            self.timer += self.timerEnd - self.timerStart
                            self.timerStart = 0

                        # Signal the playback thread to exit by setting the playEvent object
                        self.playEvent.set()

                    # -------------
                    # TEARDOWN request
                    elif self.requestSent == self.TEARDOWN:
                        # Next state: INIT
                        self.state = self.INIT
                        # Set timer end when paused and playing previously
                        # Calculate data time
                        self.timerEnd = time.time()
                        self.timer += self.timerEnd - self.timerStart
                        # Set flag teardownAcked active
                        self.teardownAcked = 1

                    # -------------
                    # DESCRIBE request
                    elif self.requestSent == self.DESCRIBE:
                        # Display the information on the description window
                        self.displayDescription(cmds)

                    # -------------
                    # With FORWARD and BACKWARD request, we don't need to handle any tasks in this function



    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # TODO
        # -------------
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
            self.playMovie()
        except:
            # Show warning messagebox if unable to bind port
            tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)



    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # TODO
        # -------------
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
        # TODO
        # -------------
        # Calculate loss rate
        lossRate = ((self.packetLost) / (self.packetTotal)) * 100

        # Create a new window to display the statistics
        top1 = Toplevel()
        top1.title("Statistics")
        top1.geometry('300x200')

        # Create a listbox to display the description lines
        Lb = Listbox(top1, width=100, height=80)

        Lb.insert(1, " Statistics ")
        Lb.insert(2, " ")

        # Display statistic about loss packets
        Lb.insert(3, "Current Packets No.%d " % self.frameNbr)
        Lb.insert(4, "Total Streaming Packets: %d packets" % self.packetTotal)
        Lb.insert(5, "Total Packets Received: %d packets" % self.packetReceived)
        Lb.insert(6, "Total Packets Lost: %d packets" % self.packetLost)
        Lb.insert(7, "Packet Loss Rate: %d%%" % lossRate)
        Lb.insert(8, " ")

        # Display statistic about video data rate
        Lb.insert(9, "Play time: %.2f seconds" % self.timer)
        Lb.insert(10, "Bytes received: %d bytes" % self.totalBytes)
        Lb.insert(11, "Video Data Rate: %d bytes per second" % (self.totalBytes / self.timer))
        Lb.insert(12, " ")

        # Display statistic about Jitter time
        Lb.insert(13, "Total Jitter: %.3fms" % (self.totalJitter * 1000))
        Lb.insert(14, "Average Jitter: %.3fms" % ((self.totalJitter / self.packetReceived) * 1000))

        # Pack the listbox into the window
        Lb.pack()



    def displayDescription(self, lines):
        # Create a new window to display the video description
        top = Toplevel()
        top.title("Description window")
        top.geometry('300x180')

        # Create a listbox to display the description lines
        Lb2 = Listbox(top, width=50, height=30)

        # Insert the first two lines: "Describe:" and the name of the video file
        Lb2.insert(1, "Describe")
        Lb2.insert(2, "Name video: " + str(self.fileName))

        # Loop over the remaining lines of the description and insert them into the listbox
        for i in range(1, len(lines)):
            Lb2.insert(i+2, lines[i])

        # Insert the current time at the end of the description
        Lb2.insert(len(lines)+3, "Current time: " + "%02d:%02d" % (self.currTime // 60, self.currTime % 60))

        # Pack the listbox into the window
        Lb2.pack()