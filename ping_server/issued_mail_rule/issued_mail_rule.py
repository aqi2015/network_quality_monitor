#!//usr/bin/python
# conding:utf8

import threading, time, socket, re, json, sys


def getRule(rule_file):
	dict_rule = {}
	try:
		with open(rule_file,'r') as f:
			for line in f:
				line = line.split()
				if not line or re.search(r'^ *#',line[0]):
					continue
				else:
					dict_rule[int(line[0])] = int(line[1])
	except:
		print 'please check ' + str(rule_file)
		exit()
	return dict_rule


def read_conf(file_conf):
	group_send_info = {}
	with open(file_conf, 'r') as f:
		for line in f:
			line = line.split()
			if not line or re.search(r'^ *#',line[0]):
				continue
			elif len(line) >= 3:
				dict_rule_info = {}
				dict_rule_info['dport_ip'] = line[1]
				dict_rule_info['dict_rule'] = getRule(line[2])
				group_send_info.setdefault(line[0], []).append(dict_rule_info)
	return group_send_info
				

def send_to_client(client_ip, send_info):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((client_ip, 9001))
		sock.send(json.dumps(send_info))
	except Exception,e:
		print Exception,":",e


				
def issued_mail_rule(group_send_info):	
	for ip, list_mail_rule in group_send_info.items():
		send_info = {'action_to_client':'mail_rule', 'mail_rule':list_mail_rule}
		send_to_client(ip, send_info)
	

if __name__ == '__main__':
	file_conf = sys.argv[1]
	group_send_info = read_conf(file_conf)
	issued_mail_rule(group_send_info)

