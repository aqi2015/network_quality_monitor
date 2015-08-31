#!/usr/bin/env python
# coding:utf8

import json,sys,socket


send_info = sys.argv[1]
#send_info = json.dumps(send_info)
send_info = json.loads(send_info)
#send_info = {'action_to_client':'trace', 'trace':('192.168.202.136', '192.168.24.1')}

action_name = send_info['action_to_client']
host = send_info[action_name][0]
port = 9001

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #定义socket类型，网络通信，TCP
s.connect((host,port)) 	 #要连接的IP与端口

get_info = None
s.sendall(json.dumps(send_info))
while True:
	try:
		get_info = json.loads(s.recv(8092).encode('utf-8'))
		if get_info:
			break
	except:
		pass
print get_info
	
