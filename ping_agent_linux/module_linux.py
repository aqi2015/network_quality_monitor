# coding:utf8

import re, time, subprocess


def ping(sentIp,receivedIp):
	report = {'sysType':2,'key':123456789,'auth':987654321,'sentIp':sentIp,'receivedIp':receivedIp,}
	ping_result = []
	report['sent_date'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
	p = subprocess.Popen(r'ping -c 30 ' + receivedIp,
						stdin = subprocess.PIPE,
						stdout = subprocess.PIPE,
						stderr = subprocess.PIPE,
						shell = True)
	out = p.stdout.read().split('\n')
	report['received_date'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
	for i in range(-4,0):
		line = out[i]
		if re.search(r'transmitted',line):
#			report['sent_times'] = re.sub(r'transmitted.*','',line).split()[0]
			report['sent_times']     = re.sub(r'\D','',re.sub(r'.*,','',re.sub(r'transmitted.*','',line)))
			report['received_times'] = re.sub(r'\D','',re.sub(r'.*,','',re.sub(r'received.*','',line)))
			report['lost_per']       = re.sub(r'\D','',re.sub(r'.*,','',re.sub(r'loss.*','',line)))
			report['lost_times'] = int(report['sent_times']) * int(report['lost_per']) / 100
		elif re.search(r'rtt',line):
			line = re.sub(r' +.*','',re.sub(r'.*= +','',line)).split(r'/')
			report['minimum'] = re.sub(r'\..*','',line[0])
			report['average'] = re.sub(r'\..*','',line[1])
			report['maximum'] = re.sub(r'\..*','',line[2])
	if 'minimum' not in report:
			report['minimum'] = report['average'] = report['maximum'] = '1000'
	return report


def trace(receivedIp):
	p = subprocess.Popen(r'traceroute -n ' + receivedIp,
						stdin = subprocess.PIPE,
						stdout = subprocess.PIPE,
						stderr = subprocess.PIPE,
						shell = True)
	return p.stdout.read().decode('utf-8')