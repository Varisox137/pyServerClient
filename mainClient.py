from concurrent.futures import ThreadPoolExecutor
import os
from time import sleep

# import bwpgrb.bwpMain

CLIENT_VERSION='230517'
URL='https://n6944f2933.imdo.co/'

MAX_WK=5 # TPE max worker

def dialog(command:str,method:str,data:dict=None):
	import urllib.request as rq
	import urllib.parse as ps

	def urldecode(s:str):
		# no need to set the split() param: maxsplit, as the inner dict ['data'] has been url-encoded, '&'->'%26'
		d={}
		if s: d.update(list(map(
				lambda x:(ps.unquote_plus((s:=x.split('='))[0]),
				          ps.unquote_plus(s[1])),
				s.split('&'))))
		return d

	HEADERS={'Connection': 'keep-alive',
	         'Content-Type': 'text/plain'}
	if data is None: data=dict()
	data['command']=command
	data_enc=ps.urlencode(data).encode('utf-8')
	request=rq.Request(url=URL,data=data_enc,headers=HEADERS,method=method.upper()) # http method should be upper case
	response=rq.urlopen(request).read().decode()
	res_dict=urldecode(response)
	res_dict['data']=urldecode(res_dict['data'])
	return res_dict

USR=''
def log_or_reg():
	global USR
	loc_usrs=[]
	base={'nt':'LOCALAPPDATA','posix':'HOME'}
	# try to get local config first
	usr=''
	pwd=''
	try: # attempt to find local config
		with open(os.environ[base[os.name]]+'/vsxClient.cfg','r',encoding='utf-8') as config:
			while usr:=config.readline().strip(): # username
				loc_usrs.append((usr,config.readline().strip())) # password
	except FileNotFoundError: pass
	if loc_usrs: # local config has content
		print('\nLocal config found !'); sleep(0.7)
		print('\nExisting local users:')
		lu_num=len(loc_usrs)
		for loc_uid in range(lu_num): # starts from 0
			print(f"{str(loc_uid+1).rjust(len(str(lu_num)),' ')}: {loc_usrs[loc_uid][0]}")
		sleep(0.7)
		print('\nEnter the number of the user you want to log in as...')
		print('...or enter 0 to operate manually, either log in or register new user...')
		print('...all other input will have you logged in as the default first user.'); sleep(0.7)
		ch=input('\nLocal user number ?=\n')
		if ch!='0':
			if ch.isdigit() and (ch:=int(ch))<=lu_num: # choose user
				(usr,pwd)=loc_usrs[ch-1]
			else: # by default
				(usr,pwd)=loc_usrs[0]
		else: print('\nWill log in or register manually...'); sleep(0.7)
	else: print('\nNo local config found...'); sleep(0.7)
	# now, either no local config found, or (usr,pwd) already chosen from local, or just choose to log in manually
	from hashlib import sha3_256
	if not (usr or pwd):
		reg_key=input('\nEnter registration code, or skip by entering nothing...?=\n')
		if reg_key:
			res=dialog(command='chk_reg',method='post',data={'key':(reg_key if reg_key.isalnum() else '')})
			msg=res['message']
		else: msg='Notice: Registration skipped.'
		print(msg); sleep(0.7)
		if msg.startswith('Successful'): # code pass, create new user
			print('\nBegin new user registration...'); sleep(0.7)
			while True: # guarantee a valid new username
				usr=input('\nEnter new username :=\n')
				res=dialog(command='chk_new_usn',method='post',data={'username':usr})['message']
				print(msg:=res['message'])
				if msg.startswith('Successful'): break
			while True: # guarantee identical twice input
				pwd=input('\nEnter password :=\n')
				if input('Confirm password :=\n')!=pwd:
					print('Password unmatch !')
				else: # reg to server
					USR=usr
					res=dialog(command='register',method='post',data={'username':usr,'password':pwd})
					print(res['message'])
					break
		else: # login an existing user
			print('\nBegin normal login process...'); sleep(0.7)
			while True: # has to check manual login
				crpt=sha3_256()
				usr=input('\nEnter username :=\n')
				pwd=input('Enter password :=\n')
				crpt.update(pwd.encode('utf-8'))
				res=dialog(command='login',method='post',data={'username':usr,'pwd_hash':crpt.hexdigest()})
				print(msg:=res['message'])
				if msg.startswith('Caution'):
					USR=usr='admin'
					break
				elif msg.startswith('Successful'):
					USR=usr
					break
	else: # local config auto login
		crpt=sha3_256(pwd.encode('utf-8'))
		res=dialog(command='login',method='post',data={'username':usr,'pwd_hash':crpt.hexdigest()})
		print(msg:=res['message'])
		# local config should guarantee user existence in server, with the correct password
		assert msg.startswith('Successful'),'LocalConfigLoginError'
		USR=usr
	# finally, refresh local user and overwrites config
	if usr!='admin': # admin mustn't be recorded into config
		if usr not in list(map(lambda x:x[0],loc_usrs)):
			loc_usrs.append((usr,pwd))
	with open(os.environ[base[os.name]]+'/vsxClient.cfg','w',encoding='utf-8') as config:
		for each in loc_usrs:
			config.writelines((each[0]+'\n',each[1]+'\n'))

ALIVE=True
def keep_conn(interval:int|float):
	while ALIVE:
		dialog(command='keep',method='post',data={'username':USR})
		sleep(interval)

CUR_RM=''
CMD_LS=[]
def command_cycle():
	global REC,CUR_RM,CMD_LS
	print('\nNow you\'ve entered the command cycle.')
	print('Getting full command list...'); sleep(0.7)
	res=dialog(command='get_cmd_ls',method='get')
	print(res['message'])
	cmd_ls=res['data']['commands'].split() # command list
	cmd_des=res['data']['description'] # command description
	lobby=True
	while True:
		sleep(0.7)
		print('\nCommands available:'); sleep(0.7)
		print(cmd_des); sleep(0.7)
		print('\nNotice that you should type the full name, or the first letter, of the commands...')
		print('...but luckily the cases of input doesn\'t matter, which is good news.'); sleep(0.7)
		cmd=input('\nYour command ?=\n').lower(); sleep(0.7)
		match cmd:
			case 'quit'|'q':
				terminate()
			case 'public'|'p':
				msg=input('Enter the message you want to say to everyone :=\n')
				res=dialog(command='pub_chat',method='post',data={'username':USR,'message':msg})
				print(res['message'])
				REC[0]+=1
			case 'enter'|'e':
				if not lobby: print('Already in a room!'); continue
				res=dialog(command='rms_get',method='get')
				print(res['message'])
				print('Existing rooms:')
				rm_ls=res['data']['rooms'].split('&')
				print('\n'.join(rm_ls) if rm_ls else '\n')
				print('Enter the id of an existing room you want to enter...')
				print('...or a new id for a new room you want to create...')
				print('...in both cases the id must be consist of only alphabets and numbers...')
				print('...and also with a minimum length of 4.'); sleep(0.7)
				rm=input('RoomID ?=\n')
				if len(rm)<4 or not rm.isalnum():
					print('RoomID illegal !')
				else:
					CUR_RM=rm # mark current room
					lobby=False
					if rm not in list(REC[1].keys()): # haven't entered this room during this login
						REC[1][rm]=0 # initialize room history read position record
					if rm in rm_ls: # room exists in server
						res=dialog(command='enter',method='post',data={'username':USR,'roomid':rm})
					else: # room doesn't exist, thus create it
						res=dialog(command='create',method='post',data={'username':USR,'roomid':rm})
					print(res['message'])
			case 'room'|'r':
				if lobby: print('Not in a room yet!'); continue
				msg=input('Enter the message you want to say to your room members :=\n')
				res=dialog(command='rm_chat',method='post',data={'username':USR,'message':msg})
				print(res['message'])
				REC[1][CUR_RM]+=1
			case 'leave'|'l':
				if lobby: print('Not in a room yet!'); continue
				lobby=True
				res=dialog(command='leave',method='post',data={'username':USR})
				print(res['message'])
			case _:
				if T:
					match cmd:
						case 'get_pub_msg':
							pub_rec=REC[0]
							res=dialog(command=cmd,method='get',data={'last':pub_rec})
							print(res['message'])
							pub_msg=res['data']['messages']
							if pub_msg:
								print(pub_msg+'\n')
								REC[0]+=len(pub_msg.split('\n'))
						case 'get_rm_msg':
							rm_rec=REC[1][CUR_RM]
							res=dialog(command=cmd,method='get',data={'username':USR,'last':rm_rec})
							print(res['message'])
							rm_msg=res['data']['messages']
							if rm_msg:
								print(rm_msg+'\n')
								REC[1][CUR_RM]+=len(rm_msg.split('\n'))
						case _:
							print('Command incorrect !')
				elif cmd not in cmd_ls: print('Command incorrect!')

REC=[0,{}] # chat history position record, in the form of [pub,{rid:rm,rid:rm...}]
def msg_refr(interval:int|float):
	global REC
	while ALIVE:
		if CUR_RM:
			rm_rec=REC[1][CUR_RM]
			rm_msg=dialog(command='get_rm_msg',method='get',data={'username':USR,'last':rm_rec})['data']['messages']
			if rm_msg:
				print('\n-------------     New Messages!     -------------'
				      +rm_msg+'\n'+
				      '-------------     Messages Ends     -------------\n')
				REC[1][CUR_RM]+=len(rm_msg.split('\n'))
		pub_rec=REC[0]
		pub_msg=dialog(command='get_pub_msg',method='get',data={'last':pub_rec})['data']['messages']
		if pub_msg:
			print('\n-------------     New Messages!     -------------'
			      +pub_msg+'\n'+
			      '-------------     Messages Ends     -------------\n')
			REC[0]+=len(pub_msg.split('\n'))
		sleep(interval)

EXECUTOR=ThreadPoolExecutor(max_workers=MAX_WK)
def terminate():
	global ALIVE
	ALIVE=False
	res=dialog(command='logout',method='post',data={'username':USR})
	print(res['message'])
	EXECUTOR.shutdown(cancel_futures=True)
	sleep(1)
	input('Program finished, press enter to quit......\n')
	exit()

def admin_mode():
	pass

GAMES=('Splendor',) # module name, available offline-mode games, still developing & adding
if __name__=='__main__':
	T=bool(input('test mode ?')=='s'); sleep(0.7)
	print('\nClient version : '+CLIENT_VERSION+'\n'); sleep(0.7)
	try:
		print(dialog(command='try',method='post')['message']) # check if server is online; btw res should have ['data']=={}
	except Exception:
		from traceback import print_exc
		print_exc()
		sleep(1)
		print("\nOops! Seems the Server isn't online...")
		print('Starting offline mode......\n'); sleep(0.7)
		if not input('press enter to start a mini-game ?'):
			game_name=input('enter the name of the game you want to play ?=')
			if game_name in GAMES:
				from importlib import import_module
				game=import_module(game_name)
				game.game_main()
		input('Program finished, press enter to quit......\n')
	else: # server online
		print("\nWelcome to Varisox137's server! (still improving yet)"); sleep(0.7)
		log_or_reg() # login or registration, USR set
		sleep(0.7)
		if USR=='admin':
			EXECUTOR.submit(admin_mode)
		elif not T:
			EXECUTOR.submit(command_cycle)
			EXECUTOR.submit(keep_conn,5)
			EXECUTOR.submit(msg_refr,1)
		else:
			EXECUTOR.submit(keep_conn,5)
			EXECUTOR.submit(command_cycle)
