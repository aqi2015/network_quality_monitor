#!/usr/bin/python
# coding:utf8

import sys,os,socket,subprocess,re,json,time,urllib,urllib2,threading,copy

from module_linux import *

reload(sys)
sys.setdefaultencoding('utf8')

def monitor_ip(action_info):
	try:
		for sentIp,receivedIp_list in action_info.items():
			with open('local_wan_ip.conf', 'w') as f:
				f.write(sentIp)
				
			with open('receivedIp.conf', 'w') as f:
				for receivedIp in receivedIp_list:
					f.write(receivedIp+'\n')
	except Exception as e:
		print Exception,":",e


def change_mail_rule(action_info):
	for m_rule in action_info:
		mail_rule[m_rule['dport_ip']] = {int(k):int(v) for k,v in m_rule['dict_rule'].items()}
	with open('mail_rule.json', 'w') as f:
		json.dump(mail_rule, f)
	print mail_rule
	
	
def ping_once(action_info):
	sentIp,receivedIp = action_info
	report = ping(sentIp,receivedIp)
#	send_info = '已发送 = %s, 已接收 = %s，丢失 = %s (%s%% 丢失)，\n最短 = %sms，最长 = %sms，平均 = %sms' % (report['sent_times'], report['received_times'], report['lost_times'], report['lost_per'], report['minimum'], report['maximum'], report['average'])
#	send_info = 'sent_times = %s, received_times = %s，lost_times = %s (%s%% lost_per)，\nminimum = %sms，maximum = %sms，average = %sms' % (report['sent_times'], report['received_times'], report['lost_times'], report['lost_per'], report['minimum'], report['maximum'], report['average'])
	send_info = str(report['sent_times']) + '-' + str(report['received_times']) + '-' + str(report['lost_times']) + '-' + str(report['lost_per']) + '-' + str(report['minimum']) + '-' + str(report['maximum']) + '-' + str(report['average'])

	return json.dumps(send_info)


def trace_once(action_info):
	sentIp,receivedIp = action_info
	report = trace(receivedIp)
	return json.dumps(report)


def listen_wait(sock, action):
	connection,address = sock.accept()    
	try:    
		connection.settimeout(50)  
		#获得一个连接，然后开始循环处理这个连接发送的信息  
		''''' 
		如果server要同时处理多个连接，则下面的语句块应该用多线程来处理， 
		否则server就始终在下面这个while语句块里被第一个连接所占用， 
		无法去扫描其他新连接了，但多线程会影响代码结构，所以记得在连接数大于1时 
		下面的语句要改为多线程即可。 
		'''  
		while True:
			send_info = None
			try:
				get_info = json.loads(connection.recv(8092).encode('utf-8'))
				action_name = get_info['action_to_client']
				action_info = get_info[action_name]
				send_info = action[action_name](action_info)
				if send_info:
					connection.sendall(send_info)
			except Exception as e:
				print Exception,":",e
			break  #退出连接监听循环  
	except socket.timeout:  #如果建立连接后，该连接在设定的时间内无数据发来，则time out  
		print 'time out'  
	
	print "closing one connection" #当一个连接监听循环退出后，连接可以关掉  
	connection.close()
			
	
def listen_client(port):
	dict_listen_id = {}
	action = {'monitor_ip':monitor_ip, 'mail_rule':change_mail_rule, 'ping':ping_once, 'trace':trace_once}
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
#	sock.bind(('localhost', 9001))  #配置soket，绑定IP地址和端口号  
	sock.bind(('0.0.0.0', port))  #配置soket，绑定IP地址和端口号  
	sock.listen(50) #设置最大允许连接数，各连接和server的通信遵循FIFO原则
	print "Server is listenting port " + str(port) +", with max connection 50" 
	for id in range(10):
		dict_listen_id[id] = thread(listen_wait,(sock, action))
	while True:  #循环轮询socket状态，等待访问  			
		for id in dict_listen_id:
			if not dict_listen_id[id].isAlive():
				dict_listen_id[id] = thread(listen_wait,(sock, action))
				dict_listen_id[id].start()
		time.sleep(1)


def send_to_server(send_info):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(('180.153.117.120', 9002))
		sock.send(json.dumps(send_info))
	except Exception as e:
		print Exception,":",e	
		
#################################
class rule_filter():

	def __init__(self, default_rule, receivedIp):
		self.receivedIp = receivedIp
		self.info = {'current_rule':copy.deepcopy(mail_rule.get(receivedIp,default_rule)),
					'alert100_times':2, 
					'sleep_times':0,
					'sleep5':None
					}
		
	def rule_filter(self, standard_rule, lost_per):
		receivedIp = self.receivedIp
		current_rule = self.info['current_rule']
		alert100_times = self.info['alert100_times']
		sleep_times = self.info['sleep_times']
		sleep5 = self.info['sleep5']
		tag = True
		dict_alert = {}
		send_info = None
		for k,v in current_rule.items():
			if lost_per >= k:
				tag = False				
				if sleep_times != 0:
					break					
				current_rule[k] -= 1			
				if current_rule[k] <= 0:
					if k == 100:
						alert100_times -= 1
						current_rule = standard_rule
					else:
						alert100_times = 2
					dict_alert[k] = standard_rule[k]
					current_rule[k] = standard_rule[k]
			if dict_alert:
				tuple_alert = sorted(dict_alert.items(), key=lambda x:x[0])[-1]
				percent = tuple_alert[0]
				times = tuple_alert[1]			
				mail_info = {'sentIp':sentIp, 'receivedIp':receivedIp, 'percent':percent, 'times':times}
				send_info = {'action_to_server':'alert_mail', 'alert_mail':mail_info,}
		if tag:
			current_rule = standard_rule
			alert100_times = 2			
		if alert100_times == 0 and sleep_times == 0:
			sleep5 = thread(sleep,(5,))
			sleep5.start()
			sleep_times = 5
			alert100_times = 2			
		if sleep_times != 0:
			if not tag:
				sleep_times = 5
			if not sleep5.isAlive():
				sleep5 = thread(sleep,(5,))
				sleep5.start()
				sleep_times -= 1		
		self.info['current_rule']   = current_rule
		self.info['alert100_times'] = alert100_times
		self.info['sleep_times']    = sleep_times
		self.info['sleep5']         = sleep5		
		return send_info
		
###################################
def post_to_server(post_url, post):
	headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1', 'Referer' : '******',}
	post = urllib.urlencode(post)
	try:
		urllib2.urlopen(urllib2.Request(post_url,post,headers))
	except Exception as e:
		print Exception,":",e


def func_trace(report,action = 'trace_file'):		#tracert
	sentIp = report['sentIp']
	receivedIp = report['receivedIp']
	trace_dir = report['received_date'].replace(' ','_',1)
	trace_date = report['received_date']
	out = trace(report['receivedIp'])
	trace_file = {'out':out, 'sentIp':sentIp, 'receivedIp':receivedIp, 'trace_dir':trace_dir, 'trace_date':trace_date}
	send_info = {'action_to_server':action, action:trace_file}
	send_to_server(send_info)
		

def sleep(s):
	time.sleep(s)

	
def func_ping(sentIp,receivedIp):
	default_rule = {100:2,}
	filter = rule_filter(copy.deepcopy(mail_rule.get(receivedIp,default_rule)), receivedIp)
	while True:
		global receivedIp_list				
		if receivedIp not in receivedIp_list:
			del(filter)
			if mail_rule.get(receivedIp):
				del(mail_rule[receivedIp])
			break			
		report = ping(sentIp,receivedIp)
		post_url = r'http://180.153.117.120/pingReceived.php'
		post_to_server(post_url, report)		
		mail_info = filter.rule_filter(copy.deepcopy(mail_rule.get(receivedIp,default_rule)), int(report['lost_per']))
		if mail_info:
			print report['received_date'],receivedIp,mail_info
			send_to_server(mail_info)
		if int(report['lost_per']) >= 10:
			t = thread(func_trace, (report, 'trace_file'))
			t.start()
			
		
def get_info_ip(conf_list):
	global receivedIp_list
	global receivedIp_sync_dict
	global sentIp
	get_receivedIp_list = []
	for f in conf_list:
		if not os.path.exists(f):
			file_new = open(f,'w')
			file_new.close()			
#	p = r'(\t* *\t*)*'
#	file_r = open('receivedIp.conf','r')
#	receivedIp_list = re.sub('\n+$', '', re.sub(p, '', file_r.read())).split('\n')
#	file_r.close()	
	with open('receivedIp.conf','r') as f:
		for ip in f:
			ip = ip.strip()
			if ip:
				get_receivedIp_list.append(ip)
	receivedIp_list = get_receivedIp_list
	file_r = open('local_wan_ip.conf','r')
	sentIp = file_r.readline()
	file_r.close()	
	for ip in receivedIp_sync_dict:
		if ip not in receivedIp_list:
			del(receivedIp_sync_dict[ip])
	time.sleep(5)


def get_mail_rule():
	try:
		with open('mail_rule.json', 'r') as f:
			rule = json.load(f)
			for k,v in rule.items():
				rule[k] = {int(x):int(y) for x,y in v.items()}
			return rule
	except:
		pass

		
class thread(threading.Thread):

	def __init__(self, func, args=None, name=None):
		threading.Thread.__init__(self)
		self.name = name
		self.func = func
		self.args = args
		
	def run(self):
		apply(self.func, self.args)	

		
if __name__ == "__main__":
	global receivedIp_list
	global receivedIp_sync_dict
	global sentIp
	global mail_rule
	
	mail_rule = get_mail_rule() or {}
	dict_listen_id = {}
	
	receivedIp_list = []
	receivedIp_sync_dict = {}
	conf_list = ('receivedIp.conf', 'local_wan_ip.conf',)
	info_ip = thread(get_info_ip,(conf_list,))	

	listen = thread(listen_client,(9001,))
	listen.start()
	
	while True:
		if not info_ip.isAlive():		
			info_ip = thread(get_info_ip,(conf_list,))
			info_ip.start()		
		time.sleep(1)
		
		for receivedIp in receivedIp_list:
			if receivedIp not in receivedIp_sync_dict and receivedIp != '':
				receivedIp_sync_dict[receivedIp] = thread(func_ping,(sentIp,receivedIp))
				receivedIp_sync_dict[receivedIp].start()
