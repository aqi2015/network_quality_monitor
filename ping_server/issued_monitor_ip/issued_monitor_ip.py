#!/usr/bin/env python
# coding:utf8


import re,sys,socket,json

file = None
receivedIp_list = []


def send_to_client(client_ip, send_info):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((client_ip, 9001))
	sock.send(json.dumps(send_info))


try:
	file = sys.argv[1]
except:
	pass

if file:
	if not re.match(r'(\d{1,3}\.){3}\d{1,3}$', file):
		print '参数错误 文件名必须以 ip 命名 ！'
		exit()
	try:
		with open(file, 'r') as f:
			p = r'(\t* *\t*)*\n*'
			for ip in f:
				ip = re.sub(p, '', ip)
				if not ip or re.search('^#', ip):
					continue
				receivedIp_list.append(ip)
		send_info = {'action_to_client':'monitor_ip', 'monitor_ip':{file:receivedIp_list}}
		send_to_client(file, send_info)
	except IOError,e:
		print '%s 不存在 !' % file


