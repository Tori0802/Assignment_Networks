import sys
from tkinter import Tk
from Client import Client
from Client2 import Client2

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
		fileName = sys.argv[4]	
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	

	# Because we have two type of clients to implement 2 mode: Normal and Extend
	# Choose option (Normal or Extend) before create a new client
	print('Options:')
	print('Normal (type 1) or Extend (type 2)')
	while True:
		INPUT = int(input('Your choice: '))
		if(INPUT == 1):
			root = Tk()
			app = Client(root, serverAddr, serverPort, rtpPort, fileName)
			break
		elif(INPUT == 2):
			root = Tk()
			app = Client2(root, serverAddr, serverPort, rtpPort, fileName)
			break
		else:
			print('Please choose option again!')

	# Create a new client
	print('Starting the client...')
	app.master.title("Friday Client")
	root.mainloop()
	