# coding:utf8

import re, time, subprocess


def ping(sentIp,receivedIp):
	report = {'sysType':1,'key':123456789,'auth':987654321,'sentIp':sentIp,'receivedIp':receivedIp,}
	ping_result = []
	list_model = ['sent_times','received_times','lost_times','lost_per','minimum','maximum','average']
	report['sent_date'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
	p = subprocess.Popen(r'ping -n 30 ' + receivedIp,
						stdin = subprocess.PIPE,
						stdout = subprocess.PIPE,
						stderr = subprocess.PIPE,
						shell = True)
	out = p.stdout.read().split('\n')
	report['received_date'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
	for i in range(-4,0):
		line = out[i]
		if re.search(r"=\D.*=\D.*=\D",line):
			ping_result.extend(line.split())
	for n in range(0,len(ping_result)):
		if ping_result[n] == '=':
			report[list_model.pop(0)] = re.sub(r'\D','',ping_result[n + 1])
		elif re.search('%',ping_result[n]):
			report[list_model.pop(0)] = re.sub(r'\D','',ping_result[n])
	if list_model:
		for i in list_model:
			report[i] = '1000'
	return report
	

def trace(receivedIp):
	p = subprocess.Popen(r'tracert -d ' + receivedIp,
						stdin = subprocess.PIPE,
						stdout = subprocess.PIPE,
						stderr = subprocess.PIPE,
						shell = True)
	return p.stdout.read().decode('gbk')