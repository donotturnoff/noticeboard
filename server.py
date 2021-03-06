import socket
import threading
import datetime
import os
import os.path
import errno

def log(ip = '127.0.0.1', event = 'error', msg = ''): #Create more consistent logging style
	msg = str(datetime.datetime.now()) + '\t' + ip + '\t' + event.ljust(16) + '\t' + msg
	print(msg)
	f = open("log", 'a')
	f.write(msg + '\n')
	f.close()

success = "[+] "
error = "[-] "
prompt = "[$] "
info = "[*] "

def recv(sock): #Use HTTP-style status codes
	try:
		length = int(sock.recv(1024).decode())
		sock.send(b"ready")
		response = sock.recv(length).decode()
	except ValueError as msg:
		response = "error\r\nPeer closed connection unexpectedly. (" + str(msg) + ")"
	except Exception as msg:
		response = "error\r\n" + str(msg)
	response = response.split("\r\n") #Delimit with \r\n instead of \r\n
	#print(response)
	return response

def send(sock, message):
	try:
		sock.send(str(len(message)).encode())
		response = sock.recv(5).decode()
		if response == "ready":
			sock.send(message.encode())
			return "success"
		else:
			raise Exception(error + "Expected 'ready', got " + response)
	except Exception as msg:
		return "error\r\n" + str(msg)

port = 5000
directory = "./"
boardsDirectory = directory + "boards/"

splash = """
..............................................................................................................................................
..............................................................................................................................................
..............................................................................................................................................
..+=================+.........................................................................................................................
..|    ,+#####+,    | ....########...#######..##....##..#######..########.########.##.....##.########..##....##..#######..########.########...
..|   ##"     "##   |  ...##.....##.##.....##.###...##.##.....##....##.......##....##.....##.##.....##.###...##.##.....##.##.......##.........
..|  +#     .## #+  |  ...##.....##.##.....##.####..##.##.....##....##.......##....##.....##.##.....##.####..##.##.....##.##.......##.........
..|  #|  .###'  |#  |  ...##.....##.##.....##.##.##.##.##.....##....##.......##....##.....##.########..##.##.##.##.....##.######...######.....
..|  *# ##'     #*  |  ...##.....##.##.....##.##..####.##.....##....##.......##....##.....##.##...##...##..####.##.....##.##.......##.........
..|   ##.     ,##   |  ...##.....##.##.....##.##...###.##.....##....##.......##....##.....##.##....##..##...###.##.....##.##.......##.........
..|    `*#####*'    |  ...########...#######..##....##..#######.....##.......##.....#######..##.....##.##....##..#######..##.......##.........
..+=================+  .......................................................................................................................
....                   .......................................................................................................................      
..............................................................................................................................................
..............................................................................................................................................
"""

print(splash)

boards = {}

if os.path.exists(boardsDirectory):
	for board in os.listdir(boardsDirectory):
		if not os.path.isfile(boardsDirectory + board):
			try:
				infoFile = open(boardsDirectory + board + "/info")
				description = infoFile.read()
				boards[board] = description if description != "" else ""
				infoFile.close()
			except:
				boards[board] = ""

#boards = {'science': 'A board dedicated to the study of the universe', 'maths': 'A board all about the most fundamental of all sciences', 'tech': 'For everything tech-related'}

connections = []
clients = []
currentId = 0
postId = sum([len(files) for r, d, files in os.walk(boardsDirectory)])

class Client:
	'''A prototype client class'''

	def __init__(self, cid, ip):
		self.cid = cid
		self.ip = ip
		self.connected = datetime.datetime.now()
		self.timesDead = 0 #Check for dead clients
		self.board = ""
		self.thread = ""

def connection(c, ip):
	global currentId
	global postId
	global clients
	while True:
		try:
			request = recv(c)
			if request[0] == 'connect':
				cid = currentId
				currentId += 1
				clients.append(Client(cid, ip))
				send(c, "204 No Content\r\n" + str(cid))
				log(ip, 'connect', 'New client assigned cid ' + str(cid))

			elif request[0] == 'disconnect':
				cid = int(request[1])
				disconnected = False

				for client in clients:
					if client.cid == cid and client.ip == ip:
						clients.remove(client)
						disconnected = True
						break

				if disconnected:
					send(c, "204 No Content")
					log(ip, "disconnect", "Client with cid " + str(cid) + " disconnected")
				else:
					send(c, "500 Internal Server Error")
					log(ip)

			elif request[0] == "end":
				send(c, "204 No Content")
				c.close()
				break

			elif request[0] == 'splash':
				send(c, "200 OK\r\n" + splash)
				log(ip, 'splash', 'Splash screen sent')
				
			elif request[0] == "boards":
				boardList = ""
				if os.path.exists(boardsDirectory):
					for name, description in sorted(boards.items()):
						amountOfThreads = 0
						for thread in os.listdir(boardsDirectory + name):
							if not os.path.isfile(boardsDirectory + name + "/" + thread): amountOfThreads += 1
						boardList += "\r\n" + name + "," + str(amountOfThreads) + "," + description
					boardList = boardList.rstrip("\r\n")
					if boardList == "":
						send(c, "204 No Content")
						log(ip, "info", "'boards' directory does not exist")						
					else: 
						send(c, "200 OK" + boardList)
						log(ip, "boards", "Board list sent")
				else:
					send(c, "204 No Content")
					log(ip, "info", "'boards' directory does not exist")
				
			elif request[0] == "board":
				cid = int(request[1])
				boardExists = False
				for name in boards:
					if name == request[2]: boardExists = True
				if boardExists:
					for client in clients:
						if client.cid == cid and client.ip == ip:
							client.board = request[2]
							send(c, "204 No Content")
							log(ip, "board", "Client with cid " + str(cid) + " is on board " + client.board)
							break
				else:
					send(c, "404 Not Found")
					log(ip)
					
			elif request[0] == "threads":
				cid = int(request[1])
				for client in clients:
					if client.cid == cid and client.ip == ip:
						board = client.board
						break
				if os.path.exists(boardsDirectory + board) and board != "":
					"""for thread in os.listdir(boardsDirectory + board): #Sort into modified date order
						amountOfPosts = 0
						if not os.path.isfile(boardsDirectory + board + "/" + thread):
							for post in os.listdir(boardsDirectory + board + "/" + thread): 
								if os.path.isfile(boardsDirectory + board + "/" + thread + "/" + post): amountOfPosts += 1
							if os.path.exists(boardsDirectory + board + "/" + thread + "/op"):
								opFile = open(boardsDirectory + board + "/" + thread + "/op")
								op = opFile.read()
								opFile.close()
							else: op = ""
							threadList += "\r\n" + thread + "," + str(amountOfPosts) + "," + op
					if threadList == "":
						send(c, "204 No Content")
						log(ip, "threads", "Thread list sent")					
					else: 
						send(c, "200 OK" + threadList)
						log(ip, "threads", "Thread list sent")"""
						
					threads = []
					if not os.path.isfile(boardsDirectory + board):
						for thread in os.listdir(boardsDirectory + board): #Sort into modified date order
							amountOfPosts = 0
							if not os.path.isfile(boardsDirectory + board + "/" + thread):
								for post in os.listdir(boardsDirectory + board + "/" + thread): 
									if os.path.isfile(boardsDirectory + board + "/" + thread + "/" + post): amountOfPosts += 1
								if os.path.exists(boardsDirectory + board + "/" + thread + "/op"):
									opFile = open(boardsDirectory + board + "/" + thread + "/op")
									opFileContents = opFile.read().split("\n")
									title = opFileContents[0]
									op = " " .join(opFileContents[3:])
									opFile.close()
								else: op = ""
								postTime = ""
								threads.append({"title": title, "posts": str(amountOfPosts), "datetime": postTime, "op": op, "id": thread})
					if threads == []: send(c, "204 No Content")
					else:
						send(c, "100 Continue") #Find more suitable code
						for thread in threads:
							response = recv(c)
							if response[0] == "next": send(c, thread["id"] + "\r\n" + thread["title"] + "\r\n" + thread["posts"] + "\r\n" + thread["datetime"] + "\r\n" + thread["op"])
							else: break
						recv(c)
						send(c, "200 OK")
				else:
					send(c, "404 Not Found")
					log(ip)
				
			elif request[0] == "new":
				cid = int(request[1])
				for client in clients:
					if client.cid == cid and client.ip == ip:
						board = client.board
						break
				thread = request[2]
				content = "\r\n".join(request[3:])
				if os.path.exists(boardsDirectory + board) and board != "":
					if not os.path.exists(boardsDirectory + board + "/" + str(postId)):
						try:
							now = datetime.datetime.now()
							os.makedirs(boardsDirectory + board + "/" + str(postId))
							replyFile = open(boardsDirectory + board + "/" + str(postId) + "/op", "w")
							replyFile.write(thread + "\n" + str(postId) + "\n" + str(now) + "\n" + content)
							replyFile.close()
							send(c, "201 Created\r\n" + board + "/" + str(postId))
							postId += 1
						except OSError as msg: #Catch exceptions such as directory exists already or full disk
							if msg.errno == errno.EEXIST: send(c, "409 Conflict")
							else:
								send(c, "500 Internal Server Error")
								raise
					else: send(c, "409 Conflict\r\n" + board + "/" + thread)
				else: send(c, "404 Not Found")	
				
			elif request[0] == "thread":
				cid = int(request[1])
				threadExists = False
				threadPath = "\r\n".join(request[2:])
				threads = []
				if os.path.exists(boardsDirectory + threadPath) and (boardsDirectory + threadPath).rstrip(" ").rstrip("/") != boardsDirectory:
					for client in clients:
						if client.cid == cid and client.ip == ip:
							client.thread = threadPath
							send(c, "204 No Content")
							log(ip, "thread", "Client with cid " + str(cid) + " is on thread " + client.thread)
							break
				else:
					send(c, "404 Not Found")
					log(ip, "nonexistent", "Thread '" + threadPath + "' does not exist")
			
			elif request[0] == "refresh":
				cid = int(request[1])
				for client in clients:
					if client.cid == cid and client.ip == ip:
						board = client.board
						threadPath = client.thread
						break
				if os.path.exists(boardsDirectory + threadPath) and board != "" and (boardsDirectory + threadPath).rstrip(" ").rstrip("/") != boardsDirectory:
					posts = []
					if not os.path.isfile(boardsDirectory + threadPath):
						for post in os.listdir(boardsDirectory + threadPath): #Sort into modified date order - perhaps use id at start of name?
							if os.path.isfile(boardsDirectory + threadPath + "/" + post):
								postFile = open(boardsDirectory + threadPath + "/" + post)
								data = postFile.read().split("\n")
								postFile.close()
								currentPostTitle = data[0]
								currentPostId = data[1]
								currentPostTime = data[2]
								currentPostContent = "\n".join(data[3:])
								posts.append({"title": currentPostTitle, "content": currentPostContent, "id": currentPostId, "datetime": currentPostTime})
					if posts == []: send(c, "204 No Content")
					else:
						send(c, "100 Continue") #Find more suitable code
						for post in posts:
							response = recv(c)
							if response[0] == "next": send(c, post["title"] + "\r\n" + post["id"] + "\r\n" + post["datetime"] + "\r\n" + post["content"])
							else: break
						recv(c)
						send(c, "200 OK")
				else: send(c, "404 Not Found")

			elif request[0] == "reply":
				cid = int(request[1])
				for client in clients:
					if client.cid == cid and client.ip == ip:
						board = client.board
						threadPath = client.thread
						break
				title = request[2]
				content = "\r\n".join(request[3:])
				if os.path.exists(boardsDirectory + threadPath) and board != "" and (boardsDirectory + threadPath).rstrip(" ").rstrip("/") != boardsDirectory:
					now = datetime.datetime.now()
					replyFile = open(boardsDirectory + threadPath + "/" + str(postId), "w")
					replyFile.write(title + "\n" + str(postId) + "\n" + str(now) + "\n" + content)
					replyFile.close()
					send(c, "201 Created\r\n" + threadPath + "/" + str(postId))
					postId += 1
				else: send(c, "404 Not Found")

			elif request[0] == 'error':
				raise Exception(request[1])

			else:
				send(c, "400 Bad Request\r\n" + "\\r\\n".join(request))

		except Exception as msg:
			log(ip = ip, msg = str(msg))
			send(c, '500 Internal Server Error\r\n' + str(msg)) #Don't send when client closes connection unexpectedly
			break

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", port))
s.listen(10)
log(event = "start", msg = "")

while True:
	c, addr = s.accept()
	connections.append(threading.Thread(target = connection, args = [c, addr[0]]))
	connections[-1].start()
