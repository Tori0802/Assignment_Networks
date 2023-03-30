import sys
from time import time
HEADER_SIZE = 12

class RtpPacket:	
	header = bytearray(HEADER_SIZE)
	
	def __init__(self):
		pass
		
	def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
		"""Encode the RTP packet with header fields and payload."""
		timestamp = int(time())
		header = bytearray(HEADER_SIZE)
		#--------------
		# TO COMPLETE
		#--------------

		# Fill the header bytearray with RTP header fields
		# header[0]
		header[0] = header[0] | ((version & 0x03) << 6)		# Set version
		header[0] = header[0] | ((padding & 0x01) << 5)		# Set padding
		header[0] = header[0] | ((extension & 0x01) << 4)	# Set extension
		header[0] = header[0] | (cc & 0x0F)					# Set number of contributing sources

		# header[1]
		header[1] = header[0] | ((marker & 0x01) << 6)		# Set marker
		header[1] = header[0] | (pt & 0x7F)					# Set payload type field

		# header[2] and header[3]
		header[2] = (seqnum >> 8) & 0xFF					# Set first 8 bits of sequence number
		header[3] = seqnum & 0xFF							# Set last 8 bits of sequence number

		# header[4] - header[7]
		header[4] = (timestamp >> 24) & 0xFF				# Set first 8 bits of timestamp
		header[5] = (timestamp >> 16) & 0xFF				# Set next 8 bits of timestamp
		header[6] = (timestamp >> 8) & 0xFF					# Set next 8 bits of timestamp
		header[7] = timestamp & 0xFF						# Set last 8 bits of timestamp

		# header[8] - header[11]
		header[8] = (ssrc >> 24) & 0xFF						# Set first 8 bits of SSRC
		header[9] = (ssrc >> 16) & 0xFF						# Set next 8 bits of SSRC
		header[10] = (ssrc >> 8) & 0xFF						# Set next 8 bits of SSRC
		header[11] = ssrc & 0xFF							# Set last 8 bits of SSRC

		self.header = header

		# Get the payload from the argument
		# self.payload = ...
		self.payload = payload
		
	def decode(self, byteStream):
		"""Decode the RTP packet."""
		self.header = bytearray(byteStream[:HEADER_SIZE])
		self.payload = byteStream[HEADER_SIZE:]
	
	def version(self):
		"""Return RTP version."""
		return int(self.header[0] >> 6)
	
	def seqNum(self):
		"""Return sequence (frame) number."""
		seqNum = self.header[2] << 8 | self.header[3]
		return int(seqNum)
	
	def timestamp(self):
		"""Return timestamp."""
		timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
		return int(timestamp)
	
	def payloadType(self):
		"""Return payload type."""
		pt = self.header[1] & 127
		return int(pt)
	
	def getPayload(self):
		"""Return payload."""
		return self.payload
		
	def getPacket(self):
		"""Return RTP packet."""
		return self.header + self.payload