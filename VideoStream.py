class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError

		self.frameNum = 0			# Total sent frames
		self.totalFrame = 0			# Total frames in video

		print('frame = 0')

	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5)  # Get the framelength from the first 5 bits
		if data:
			framelength = int(data)

			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data

	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum

	# Extend functions in EXTEND part

	def get_total_time_video(self):
		"""Get total time (idle)"""
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


	def forwardFrame(self):
		"""Handle Forward frames"""
		# Idle - Forward 5% total video
		forwardFrames = int(self.totalFrame * 0.05)
		remainFrames = int(self.totalFrame - self.frameNum)

		# If video has only remainFrames, forwardFrames = remainFrames
		if forwardFrames >= remainFrames:
			forwardFrames = remainFrames

		# Implement forward frames (same as the implementation of nextFrame function)
		if forwardFrames:
			for i in range(forwardFrames + 1):
				# Get next forwardFrames
				data = self.nextFrame()
			return data


	def backwardFrame(self):
		"""Handle Backward frames"""
		# Idle - Backward 5% total video
		backwardFrames = int(self.totalFrame * 0.05)

		# Reset read data to first position
		data = self.file.seek(0)

		# If video has only transmitted frameNum frames (< backwardFrames), start read Frame No.1
		if self.frameNum <= backwardFrames:
			self.frameNum = 0
			data = self.nextFrame()

		# Else, start read Frame number tempFrame (= frameNum - backwardFrames)
		else:
			tempFrame = self.frameNum - backwardFrames
			self.frameNum = 0
			for i in range(tempFrame):
				data = self.nextFrame()
		return data


	
	