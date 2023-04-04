class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError

		self.frameNum = 0
		self.isNext = 0
		self.totalFrame = 0

		print('frame = 0')

	def get_total_time_video(self):
		self.totalFrame = 0
		# Get total of frames
		while True:
			# Read first 5 bytes
			data = self.file.read(5)
			if data:
				# Read the current frame
				data = self.file.read(int(data))
				self.totalFrame += 1
			else:
				self.file.seek(0)
				break
		return self.totalFrame * 0.05	 # 50 miliseconds

	def setIsNext(self):
		self.isNext = 1

	def nextFrame(self):
		"""Get next frame."""
		# Handle forward signal
		if self.isNext == 1:
			# Forward 0.05% total video
			forwardFrames = int(self.totalFrame * 0.05)
			remainFrames = int(self.totalFrame - self.frameNum)
			# If video has only remainFrames, forwardFrames = remainFrames
			if forwardFrames > remainFrames:
				forwardFrames = remainFrames
			self.isNext = 0
		# If not, only forward 1 frames normally
		else:
			forwardFrames = 1

		if forwardFrames:
			for i in range(forwardFrames):
				# Get the framelength from the first 5 bits
				data = self.file.read(5)
				if data:
					framelength = int(data)

					# Read the current frame
					data = self.file.read(framelength)
					self.frameNum += 1
			return data


	def prevFrame(self):
		"""Get next frame."""
		prevFrames = int(self.totalFrame * 0.05)
		data = self.file.seek(0)
		if self.frameNum <= prevFrames:
			self.frameNum = 0
			if data:
				framelength = int(data)
				# Read the current frame
				data = self.file.read(framelength)
				self.frameNum += 1
		else:
			fFrames = self.frameNum - prevFrames
			self.frameNum = 0
			for i in range(fFrames):
				data = self.nextFrame()
		return data

	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	