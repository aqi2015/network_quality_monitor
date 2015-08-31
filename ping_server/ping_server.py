#!/usr/bin/env python
# coding:utf8

import sys, socket, subprocess, re, json, os, urllib, urllib2, smtplib, subprocess, threading, time


reload(sys)
sys.setdefaultencoding('utf8')

sender = 'SecManGroup@staff.9you.com\n'
receivers = 'SecManGroup@staff.9you.com\n'
to = 'To: SecManGroup@staff.9you.com\n'

def mail(message):
	try:
		smtpObj = smtplib.SMTP('localhost')
		smtpObj.sendmail(sender, receivers, message)         
#		print "Successfully sent email"
	except SMTPException:
		print "Error: unable to send email"
	


def alert_mail(info):
#	sendIp receivedIp percent times
	subject = 'Subject: ' + info['sentIp'] + ' to ' + info['receivedIp'] + '  连续 ' + str(info['times']) + ' 次 丢包率达到 ' + str(info['percent']) + '%\n' 
	subject = subject.decode('utf-8').encode('gbk')
	text = ''' '''.decode('utf-8').encode('gbk')
	message = to + subject + text
	mail(message)


def trace_file(info):
#	out = get_info[1]               #内容
#	sentIp = get_info[2]            #源ip
#	receivedIp = get_info[3]        #目标ip
#	file_name = get_info[4]         #文件å
#	trace_date = get_info[5]        #时间
	auth = {'key':123456789, 'auth':987654321} #'sentIp':sentIp, 'receivedIp':receivedIp, 'trace_date':trace_date, 'trace_dir':trace_dir,}
	out = info.pop('out')
	dir = os.path.join(r'/var/www/pingPro/trace',info['sentIp'],info['receivedIp'])
	if not os.path.isdir(dir):
		os.makedirs(dir)
	os.chdir(dir)
	file_w = open(info['trace_dir'],'w')
	file_w.write(out)
	file_w.close()

	info = {k.encode('utf8'):v.encode('utf8') for k,v in info.items()}
	info.update(auth)
	headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1', 'Referer' : '******',}
	post_url = r'http://127.0.0.1/traceAction.php'
	post = urllib.urlencode(info)
	response = urllib2.urlopen(urllib2.Request(post_url,post,headers))


def Ping(parameter):
#	p = subprocess.Popen(r'/bin/ping 192.168.24.1 -c 2',
	p = subprocess.Popen(r'/bin/ping ' + parameter,
							stdin = subprocess.PIPE,
							stdout = subprocess.PIPE,
							stderr = subprocess.PIPE,
							shell = True)
	out = p.stdout.read().split('\n')
	return (out.pop(-3) + '\n' + out.pop(-2))
 
def reply(ip):
	file_r = open('conf.txt','r')
	while True:
		line = file_r.readline().split()
		if not line:
			return('null')
			break
		if ip in line:
			return line[2]
			break
	

def multiple_listen(sock, action):
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
					try:
						get_info = json.loads(connection.recv(8092).encode('utf-8'))
					#	if isinstance(get_info,tuple):
						if isinstance(get_info,list):
#							get_info = json.loads(connection.recv(1024),encoding="GB2312")
#							get_info = connection.recv(1024)
#							print get_info
							if get_info[0] == '1':
								print get_info[1]
								source_ip = get_info[1]
								connection.send(reply(source_ip))   
							elif get_info[0] == '2':
								get = get_info[1]
								print get
							elif get_info[0] == '3':	#获取traceroute数据 0:标记  1:内容 2:源ip 3:目标ip 4:时间
								out = get_info[1]		#内容
								sentIp = get_info[2]		#源ip
								receivedIp = get_info[3]	#目标ip
								file_name = get_info[4]		#文件名
								trace_date = get_info[5]	#时间
								dir = os.path.join(r'/var/www/pingPro/trace',sentIp,receivedIp)
								if not os.path.isdir(dir):
									os.makedirs(dir)
								os.chdir(dir)
								file_w = open(file_name,'w')
								file_w.write(out)
								file_w.close()							
								headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1', 'Referer' : '******',}
								report = {'key':123456789, 'auth':987654321, 'sentIp':sentIp, 'receivedIp':receivedIp, 'trace_date':trace_date, 'trace_dir':file_name,}
								post_url = r'http://127.0.0.1/traceAction.php'
								post = urllib.urlencode(report)
								response = urllib2.urlopen(urllib2.Request(post_url,post,headers))
						if isinstance(get_info,dict):
							action_name = get_info['action_to_server']
							action_info = get_info[action_name]
							action[action_name](action_info)
					except:
						pass
					break  #退出连接监听循环
	except socket.timeout:  #如果建立连接后，该连接在设定的时间内无数据发来，则time out  
			print 'time out'  

	print "closing one connection" #当一个连接监听循环退出后，连接可以关掉  
	connection.close()


class thread(threading.Thread):
	
	def __init__(self, func, args=None, name=None):
		threading.Thread.__init__(self)
		self.name = name
		self.func = func
		self.args = args
		
	def run(self):
		apply(self.func, self.args)
	

''' 
建立一个python server，监听指定端口， 
如果该端口被远程连接访问，则获取远程连接，然后接收数据， 
并且做出相应反馈。 
'''  
if __name__=="__main__":  
	"Server is starting"
	dict_listen_id = {}
	action = {'alert_mail':alert_mail, 'trace_file':trace_file}
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
#	sock.bind(('localhost', 9001))  #配置soket，绑定IP地址和端口号  
	sock.bind(('0.0.0.0', 9002))  #配置soket，绑定IP地址和端口号  
	sock.listen(50) #设置最大允许连接数，各连接和server的通信遵循FIFO原则  
	print "Server is listenting port 9002, with max connection 5"
	for id in range(100):
		dict_listen_id[id] = thread(multiple_listen,(sock, action))
	while True:  #循环轮询socket状态，等待访问
		for id in dict_listen_id:
			if not dict_listen_id[id].isAlive():
				dict_listen_id[id] = thread(multiple_listen,(sock, action))
				dict_listen_id[id].start()
		time.sleep(0.1)
 

