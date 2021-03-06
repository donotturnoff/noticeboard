import socket
import time
import datetime
import os
import math
import threading

success = "[+] "
failure = "[-] "
prompt = "[$] "
info = "[*] "

def recv(sock):
	try:
		length = int(sock.recv(1024).decode())
		sock.send(b"ready")
		response = sock.recv(length).decode()
	except ValueError as e:
		response = "error\r\nPeer closed connection unexpectedly. (" + str(e) + ")"
	except Exception as e:
		response = "error\r\n" + str(e)
	response = response.split("\r\n")
	#print(response)
	return response

def send(sock, message):
	try:
		sock.send(str(len(message)).encode())
		response = sock.recv(5).decode()
		if response == "ready":
			sock.send(message.encode())
			return "success".split("\r\n")
		else:
			raise Exception(failure + "Expected 'ready', got \'" + response + "\'")
	except Exception as e:
		return ("error\r\n" + str(e)).split("\r\n")

lock = threading.Lock()

#Define host and port
host = ""
port = 5000

boardName = ""
threadName = "" #Use thread path instead

timesDead = 0

#Determine OS
if os.name == 'nt': clear = 'cls'
elif os.name == 'posix': clear = 'clear'
else: clear = ""

aliases = {'no': ['no', 'n', 'nope', 'nein', 'non', 'nop'], "yes": ["yes", "yep", "yeah", "ye", "y", "ja", "oui", "si"], 'help': ['help', 'hlp', 'hlep', 'hllp', 'helo'], 'connect': ['connect', 'conn', 'connct', 'connet'], 'disconnect': ['disconnect', 'disconn', 'dscnct', 'disconnet', 'disconnct'], 'quit': ['quit', 'exit', 'bye', 'close', 'leave', 'qit', 'clse', 'xit', 'exti', "q"], 'boards': ['boards', 'bords', 'bosrds', "borads", "baords"], "board": ["board", "borad", "baord"], "threads": ["threads", "thrads", "treads"], "new": ["new", "open", "op", "nwe"], "thread": ["thread", "theard", "thred"], "refresh": ["refresh", "reload", "posts", "rfresh", "rld", "rfrsh", "refrsh"], "reply": ["reply", "respond", "rply", "rrply", "post"], "clear": ["clear", "cls", "claer", "cler", "clar"], "status": ["status", "state", "stats"]}

#Help screen information
helpInfo = info + 'Noticeboard is a simple, anonymous forum client which can connect to servers via the \'Forum\' protocol.\n' + info + 'For any command, type help [command] to view more detailed help.'
basicHelp = {'help': 'Displays this help screen', 'quit': 'Exit the program', 'connect': 'Connect to a forum', 'disconnect': 'Quit the current forum', 'boards': 'View list of boards on current server', 'board': 'View a board specified in the argument', 'threads': 'Show all threads on the current board', 'thread': 'Select a thread specified in the argument', 'reply': 'Reply to the current thread', "new": "Create a new thread on the current board"}
detailedHelp = {'help': "With no arguments, displays a basic help screen detailing the program's use and the basic function of each command."}

def localSplash(clearScreen):
	if clearScreen:	clear
	localSplash = """
	d8b   db  .d88b.  d888888b d888888b  .o88b. d88888b d8888b.  .d88b.   .d8b.  d8888b. d8888b. 
	888o  88 .8P  Y8. `~~88~~'   `88'   d8P  Y8 88'     88  `8D .8P  Y8. d8' `8b 88  `8D 88  `8D 
	88V8o 88 88    88    88       88    8P      88ooooo 88oooY' 88    88 88ooo88 88oobY' 88   88 
	88 V8o88 88    88    88       88    8b      88~~~~~ 88~~~b. 88    88 88~~~88 88`8b   88   88 
	88  V888 `8b  d8'    88      .88.   Y8b  d8 88.     88   8D `8b  d8' 88   88 88 `88. 88  .8D 
	VP   V8P  `Y88P'     YP    Y888888P  `Y88P' Y88888P Y8888P'  `Y88P'  YP   YP 88   YD Y8888D'                                                                                             
	"""
	print(localSplash)
	print(info + 'Welcome to Noticeboard, a simple text-based forum client')
	print(info + 'For a list of commands, type help')

def showHelp(command = ""):
	if command == "": 
		for key, value in basicHelp.items(): print(key.ljust(32) + value)
	else: print(command + ": " + detailedHelp[command])
	
def end(s):
	try:
		send(s, "end")
		response = recv(s)
		if response[0] == "204 No Content": s.close()
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not correctly end transmission.")
		print(info + "(Error: " + str(e) + ")")
		
def clearScreen(): os.system(clear)

def connect(remote):
	global host
	global cid
	host = remote
	for i in range(6):
		try:
			s = socket.socket()
			s.connect((host, port))
			send(s, "connect")
			response = recv(s)
			if response[0] == "204 No Content":
				cid = response[1]
				try:
					send(s, "splash")
					response = recv(s)
					clearScreen()
					if response[0] == "200 OK":	
						serverSplash = "\r\n".join(response[1:])
						print(serverSplash)
					else: raise Exception("An unknown error occurred: " + response[0])
				except Exception as e:
					print(failure + "Could not retrieve splash screen.")
					print(info + "(Error: " + str(e) + ")")
				print(success + "Connected to " + host + " on port " + str(port) + ".")
				print(info + "Client id: " + cid)	
				end(s)			
				break
			else: raise Exception("An unknown error occurred: '" + response[0] + "'") #Show more detailed error messages at points like this

		except Exception as e:
			s.close()
			if i < 5:
				print(failure + "Could not connect. Trying again in 5 seconds...")
				print(info + "(Error: " + str(e) + ")")
				time.sleep(5)
			else:
				print(failure + "All 5 connection attempts failed.")
				host = ""
				break

def disconnect():
	global host
	global cid

	s = socket.socket()
	s.connect((host, port))

	try:
		send(s, "disconnect\r\n" + cid)
		response = recv(s)
		if response[0] == "204 No Content":
			clearScreen()
			print(success + "Disconnected from " + host + ".")
			localSplash(False)
			host = ""
			cid = 0
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not disconnect.")
		print(info + "(Error: " + str(e) + ")")
	finally: end(s)
		
def boards():	
	s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "boards")
		response = recv(s)
		if response[0] == "200 OK":
			print(info + "List of boards on " + host + ":")
			print("Board name".ljust(32) + "Amount of threads".ljust(32) + "Description")
			print("-" * (64 + len("Description")))
			for board in response[1:]:
				boardInfo = board.split(",")
				name = boardInfo[0]
				threads = boardInfo[1]
				description = ",".join(boardInfo[2:])
				if description == "": description = "[No description]"
				print(name.ljust(32) + threads.ljust(32) + description[:64].split("\n")[0] + (" [...]" if len(description) >= 64 else ""))
		elif response[0] == "204 No Content": print(info + "No boards available.")
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not retrieve board list.")
		print(info + "(Error: " + str(e) + ")")
	finally: end(s)
		
def board(boardNameParam):
	global boardName
	s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "board\r\n" + cid + "\r\n" + boardNameParam)
		response = recv(s)
		if response[0] == "204 No Content": print(success + "You are now on '" + boardNameParam + "'")
		elif response[0] == "404 Not Found": raise Exception("Board '" + boardNameParam + "' does not exist")
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
		threads()
	except Exception as e:
		boardName = ""
		print(failure + "Could not visit board.")
		print(info + "(Error: " + str(e) + ")")
	finally: end(s)

def threads():
	"""s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "threads\r\n" + cid)
		response = recv(s)
		if response[0] == "200 OK":
			print(info + "List of threads on board " + boardName + ":")
			print("Thread name".ljust(32) + "Amount of posts".ljust(32) + "Original post")
			print("-" * (64 + len("Original post")))
			for thread in response[1:]:
				threadInfo = thread.split(",")
				name = threadInfo[0]
				replies = threadInfo[1]
				op = threadInfo[2]
				if op == "": op = "[No OP]"
				print(name.ljust(32) + replies.ljust(32) + op[:64].split("\n")[0] + (" [...]" if len(op) >= 64 else ""))
		elif response[0] == "204 No Content": print(info + "No threads currently on board '" + boardName + "'. Create the first one with the command 'new'.")
		elif response[0] == "404 Not Found": raise Exception("Specified board doesn't exist")
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not retrieve thread list.")
		print(info + "(Error: " + str(e) + ")")
	finally: end(s)"""
	s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "threads\r\n" + cid)
		response = recv(s)
		if response[0] == "100 Continue":
			print(info + "List of threads on board " + boardName + ":")
			print("Thread ID".ljust(16) + "Thread name".ljust(32) + "Amount of posts".ljust(32) + "Original post")
			print("-" * (80 + len("Original post")))
			while response[0] != "200 OK":
				try:
					send(s, "next")
					response = recv(s)
					if response[0] != "200 OK":
						threadId = response[0]
						name = response[1]
						posts = response[2]
						op = "\r\n".join(response[3:]).lstrip("\r\n")
						if op == "": op = "[No OP]"
						print(threadId.ljust(16) + name.ljust(32) + posts.ljust(32) + op[:64] + (" [...]" if len(op) >= 64 else ""))
				except Exception as e:
					print(failure + "Could not view thread.")
					print(info + "(Error: " + str(e) + ")")
		elif response[0] == "204 No Content": print(info + "No threads currently on board '" + boardName + "'. Create the first one with the command 'new'.")
		elif response[0] == "404 Not Found": raise Exception("Specified board doesn't exist") #Show board name here
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not retrieve thread list.")
		print(info + "(Error: " + str(e) + ")")
	finally: end(s)
		
def new(threadName, content):
	s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "new\r\n" + cid + "\r\n" + threadName + "\r\n" + content)
		response = recv(s)
		threadPath = "\r\n".join(response[1:])
		if response[0] == "201 Created":
			print(success + "New thread successfully created at " + threadPath + ".")
			thread(threadPath)
		elif response[0] == "409 Conflict": raise Exception(failure + "Thread '" + threadPath + "' already exists.")
		elif response[0] == "404 Not Found": raise Exception(failure + "Board '" + boardName + "' does not exist")
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not create thread.")
		print(info + "(Error: " + str(e) + ")")	
	finally: end(s)
	
def thread(threadPath):
	global threadName
	s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "thread\r\n" + cid + "\r\n" + threadPath)
		response = recv(s)
		if response[0] == "204 No Content":
			print(success + "You are now on '" + threadPath + "'.")
			threadName = "/".join(threadPath.split("/")[1:])
			refresh()
		elif response[0] == "404 Not Found": raise Exception("Thread '" + threadPath + "' does not exist")
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		threadName = ""
		print(failure + "Could not view thread.")
		print(info + "(Error: " + str(e) + ")")
	finally: end(s)

def refresh():
	s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "refresh\r\n" + cid)
		response = recv(s)
		if response[0] == "100 Continue":
			while response[0] != "200 OK":
				try:
					send(s, "next")
					response = recv(s)
					if len(response) > 1:
						title = response[0]
						postId = response[1]
						datetime = response[2]
						content = "\r\n".join(response[3:]).rstrip("\n")
						print("+" + "-" * 130 + "+")
						print("| -- " + title + " --" + " " * (130 - len(title) - 7) + "|")
						print("|" + " " * 130 + "|")
						print("| ", end = "")
						stringLength = 0
						for char in content:
							if char == "\n":
								print(" " * (130 - stringLength - 1) + "|\n| ", end = "")
								stringLength = 0
								continue
							if stringLength == 128: 
								print(" |\n| " + char, end = "")
								stringLength = 1
							else:
								print(char, end = "")
								stringLength += 1
						print(" " * (130 - stringLength - 1) + "|\n+" + "-" * 130 + "+")
				except Exception as e:
					print(failure + "Could not view thread.")
					print(info + "(Error: " + str(e) + ")")
		elif response[0] == "204 No Content": print(info + "No posts on this thread.")
		elif response[0] == "404 Not Found": raise Exception("Thread does not exist") #Show thread name here
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not load posts.")
		print(info + "(Error: " + str(e) + ")")
	finally: end(s)
	
def reply(title, content):
	s = socket.socket()
	s.connect((host, port))
	try:
		send(s, "reply\r\n" + cid + "\r\n" + title + "\r\n" + content)
		response = recv(s)
		if response[0] == "201 Created":
			print(success + "Successfully replied to thread. Your post is at '" + "\r\n".join(response[1:]) + "'.")
			input(prompt + "Hit enter to refresh thread...")
			refresh()
		elif response[0] == "404 Not Found": raise Exception(failure + "Thread does not exist") #Show thread name here
		else: raise Exception("An unknown error occurred: '" + response[0] + "'")
	except Exception as e:
		print(failure + "Could not reply to thread")
		print(info + "(Error: " + str(e) + ")")	
	finally: end(s)
	
def status():
	print(info + "Remote host: " + host)
	print(info + "Board: " + board)
	print(info + "Thread: " + threadName)	
	print(info + "Client ID: " + cid)
	
def quit():
	try:
		if host != "":
			if input(prompt + "You are still connected to '" + host + "'. Are you sure you wish to quit? [Y/n] ").lower() in aliases["no"]: return
			else: disconnect()
		print(info + "Bye")
		exit() 
	except KeyboardInterrupt:
		disconnect()
		print(info + "Bye")
		exit() 
		
localSplash(True)

while True:
	try:
		command = input(prompt).split()
		if len(command) == 0: continue
		mainCommand = command[0].lower()
		args = len(command) - 1
		if mainCommand in aliases["help"]:
			if args == 0: helpCommand = ""
			elif args > 0: helpCommand = command[1]
			if args > 1: print(info + "'help' takes 0 or 1 arguments only. Using first argument only.")
			showHelp(helpCommand)

		elif mainCommand in aliases["quit"]: quit()

		elif mainCommand in aliases["connect"]:
			if args > 1: print(info + "'connect' takes 0 or 1 arguments only. Using first argument only.")
			if host != "":
				if input(prompt + "You are already connected. Are you sure you wish to disconnect from '" + host + "' and connect to another host instead? [Y/n] ").lower() not in aliases["no"]:	disconnect()
				else: continue				
			if args == 0:
				host = input(prompt + "Enter remote address to connect to: ")
				if host == "": host = "127.0.0.1"
			else: host = command[1]
			connect(host)

		elif mainCommand in aliases["disconnect"]:
			if args > 0: print(info + "'disconnect' takes 0 arguments. Ignoring all arguments.")
			if host != "": disconnect()
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")

		elif mainCommand in aliases["boards"]:
			if args > 0: print(info + "'boards' takes 0 arguments. Ignoring all arguments.")
			if host != "": boards()
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")
				
		elif mainCommand in aliases["board"]:
			if args > 1: print(info + "'board' takes 0 or 1 arguments only. using first argument only.")
			if host != "":
				if args == 0:
					while boardName == "":
						boards()
						boardName = input(prompt + "Enter a board to visit: ")
				else: boardName = command[1]
				board(boardName)
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")	
			
		elif mainCommand in aliases["threads"]:
			if args > 0: print(info + "'threads' takes 0 arguments. Ignoring all arguments.")
			if host != "":
				if boardName != "": threads()
				else: print(failure + "You are not on a board. Type 'boards' to see a list of boards on the current host, and type 'board' to visit a board.")
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")
			
		elif mainCommand in aliases["new"]:
			if host != "":
				if boardName != "":
					if args >= 1: newThreadName = command[1]
					if args == 0:
						newThreadName = ""
						while newThreadName == "": newThreadName = input(prompt + "Enter thread name: ")
						
					content = ""
					done = False
					print(prompt + "Enter OP content below. End with a single . (full stop/period) on a line on its own.")
					while not done:
						nextLine = input(prompt)
						if nextLine == ".": done = True
						else: content += nextLine + "\n"
						if done == True and content == "":
							if not input(prompt + "You have not entered any content for your OP. Would you like to continue with an empty first post? [y/N] ").lower() in aliases["yes"]: done = False
					
					newThreadName = newThreadName.replace("\r\n", " ") #Fix to allow for semicolons in titles
					new(newThreadName, content)
				else: print(failure + "You are not on a board. Type 'boards' to see a list of boards on the current host, and type 'board' to visit a board.")
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")
			
		elif mainCommand in aliases["thread"]:
			if host != "":
				if boardName != "":
					if args == 0:
						threadName = ""
						while threadName == "":
							threads()
							threadName = input(prompt + "Enter a thread ID to view that thread: ")
					else: threadName = " ".join(command[1:])
					threadPath = boardName + "/" + threadName
					thread(threadPath)
				else: print(failure + "You are not on a board. Type 'boards' to see a list of boards on the current host, and type 'board' to visit a board.")			
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")
			
		elif mainCommand in aliases["refresh"]:
			if args > 0: print(info + "'refresh' takes 0 arguments. Ignoring all arguments.")
			if host != "":
				if boardName != "":
					if threadName != "": refresh()
					else: print(failure + "You are not on a thread. Type 'threads' to see a list of threads on the current host, and type 'thread' to view a thread.")				
				else: print(failure + "You are not on a board. Type 'boards' to see a list of boards on the current host, and type 'board' to visit a board.")			
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")
			
		elif mainCommand in aliases["reply"]:
			if host != "":
				if boardName != "":
					if threadName != "":
						if args >= 1: title = command[1]
						if args == 0:
							title = ""
							title = input(prompt + "Enter reply title (or hit enter for blank): ")
					
						content = ""
						done = False
						print(prompt + "Enter reply content below. End with a single . (full stop/period) on a line on its own.")
						while not done:
							nextLine = input(prompt)
							if nextLine == ".": done = True
							else: content += nextLine + "\n"
							if done == True and content == "":
								print(info + "Please enter some content for your reply.")
								done = False
					
						title = title.replace("\r\n", " ") #Fix to allow for semicolons in titles
						reply(title, content)
					else: print(failure + "You are not on a thread. Type 'threads' to see a list of threads on the current board, and type 'thread' to visit a thread.")
				else: print(failure + "You are not on a board. Type 'boards' to see a list of boards on the current host, and type 'board' to visit a board.")
			else: print(failure + "You are not connected. Type 'connect' to connect to a server.")
			
		elif mainCommand in aliases["clear"]: clearScreen()
		
		elif mainCommand in aliases["status"]: status()
			
		else: print(failure + "Command not found. Type 'help' for a list of commands.")

	except KeyboardInterrupt: quit()
