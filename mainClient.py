from concurrent.futures import ThreadPoolExecutor # class
from time import sleep # func
from importlib import import_module as imm # func
from datetime import datetime as dt # module
import os # module
import logging # module
import httpx # modules
# import asyncio # module

# from Crypto.PublicKey import RSA # module
# from Crypto.Cipher import PKCS1_OAEP # module
from json import dumps as jd, loads as jl # func

# import bwpgrb.bwpMain

# real globals, should never be changed
CLIENT_VERSION='230811' # ALWAYS remember to update server cli-ver !!!
URL='https://n6944f2933.imdo.co/' # unchanging unless testing
CLI=httpx.Client(timeout=5,verify=False,headers={
	'Connection': 'keep-alive',
	'Content-Type': 'text/plain',
	'Client-Version': CLIENT_VERSION
}) # reuses everytime

GAMES=('Mahjong',) # module name, available offline-mode games, still developing & adding
INTV={'keep':5,'msg':1,'gmrd':1,'gmst':3} # interval constants for periodic requests
LOG_LIM=7 # day limit for removal of logs too old
MAX_WK=5 # TPE max worker number
EXECUTOR=ThreadPoolExecutor(max_workers=MAX_WK) # multi-threading pool executor

# the capitalized pseudo-globals (defined closely before methods) are actually changeable, global-working variants

def dialog(method:str,command:str,data:dict=None):
	logging.debug(f'method={method}, command={command}, data={data}')

	if data is None: data=dict()
	assert (('method' not in data) and ('command' not in data)), 'KeyError in dialog data: conflict with reserved key.'
	data['method']=method
	data['command']=command

	response=CLI.post(url=URL,content=jd(data).encode()) # use POST only, for security
	logging.debug(f'response acquired: {response}') # 'response' should be a Response object
	res_dict=jl(response.read().decode('utf-8'))
	return res_dict

USR='' # username
def log_or_reg():
	logging.info('begin logging in or registration')
	global USR
	loc_usrs=[]
	base={'nt':'LOCALAPPDATA','posix':'HOME'} # the base location for local config to store
	# try to get local config first
	usr=''
	pwd=''
	try: # attempt to find local config
		with open(os.environ[base[os.name]]+'/vsxClient.cfg','r',encoding='utf-8') as config:
			while usr:=config.readline().strip(): # username
				loc_usrs.append((usr,config.readline().strip())) # password
		logging.debug('local config found')
	except FileNotFoundError:
		logging.debug('no local config')
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
			logging.debug(f'config chosen: {ch}')
		else:
			print('\nWill log in or register manually...')
			logging.debug('config passed: manual login')
			sleep(0.7)
	else: print('\nNo local config found...'); sleep(0.7)
# now, either no local config found, or (usr,pwd) already chosen from local, or the user chooses operate manually
	from hashlib import sha3_256
	if not (usr or pwd): # not from local config choice
		logging.info('begin manual login process')
		reg_key=input('\nEnter registration code, or skip by entering nothing...?=\n')
		if reg_key:
			logging.debug(f'rk input: {reg_key}')
			res=dialog(method='post',command='chk_reg',data={'key':reg_key})
			msg=res['message']
		else:
			logging.debug('rk skipped')
			msg='Notice: Registration skipped.'
		print(msg); sleep(0.7)
		if msg.startswith('Successful'): # code correct, starts registration process
			logging.debug('rk pass')
			print('\nBegin new user registration...'); sleep(0.7)
			while True: # guarantee a valid new username
				usr=input('\nEnter new username :=\n') # all checks done by server
				res=dialog(method='post',command='chk_new_usn',data={'username':usr})['message']
				print(msg:=res['message'])
				if msg.startswith('Successful'): break
			logging.debug(f'newusr: {usr}')
			while True: # guarantee identical twice input
				pwd=input('\nEnter password :=\n')
				if input('Confirm password :=\n')!=pwd:
					print('Password unmatch !')
				else: # reg to server
					logging.debug(f'newpwd: {pwd}')
					USR=usr
					crpt=sha3_256(pwd.encode('utf-8')) # construct an encrypter, pwd -> hash
					# Note that registration sends only hash of pwd, without timestamp-initialization
					logging.debug(f'new pwdhash: {crpt.hexdigest()}')
					res=dialog(method='post',command='register',data={'username':usr,'pwd_hash':crpt.hexdigest()})
					print(res['message'])
					break
			logging.info(f"reg process completed with msg: {res['message']}")
		else: # login an existing user, manually
			logging.debug('manual login')
			print('\nBegin normal login process...'); sleep(0.7)
			while True: # has to check manual login
				usr=input('\nEnter username :=\n')
				pwd=input('Enter password :=\n')
				logging.debug(f'manual login as: {usr} {pwd}')
				crpt=sha3_256(str(
					ts:=int(dt.now().timestamp())
				).encode('utf-8'))  # initializes with current timestamp (seconds), before sending to server
				crpt.update(
					(pwd_hash:=sha3_256(pwd.encode('utf-8')).hexdigest()).encode('utf-8')
				) # pwd -> hash -> timestamped-hash
				hash_final=crpt.hexdigest()
				logging.debug(f'h_f: {hash_final}')
				if T: print(f'\n***hash check***\npwd_hash {pwd_hash}\n{ts} := {hash_final}\n')
				res=dialog(method='post',command='login',data={'username':usr,'hash':hash_final})
				print(msg:=res['message'])
				if msg.startswith('Caution'):
					logging.warning('ADMIN login')
					USR=usr='admin'
					break
				elif msg.startswith('Successful'):
					logging.info('user login')
					USR=usr
					break
	else: # choice from local config, automatic login
		logging.debug('auto login from config')
		crpt=sha3_256(str(
			ts:=int(dt.now().timestamp())
		).encode('utf-8'))  # initializes with current timestamp (seconds), before sending to server
		crpt.update(
			(pwd_hash:=sha3_256(pwd.encode('utf-8')).hexdigest()).encode('utf-8')
		) # pwd -> hash -> timestamped-hash
		hash_final=crpt.hexdigest()
		if T: print(f'\n***hash check***\npwd_hash {pwd_hash}\n{ts} := {hash_final}\n')
		res=dialog(method='post',command='login',data={'username':usr,'hash':hash_final})
		print(msg:=res['message'])
		# local config should guarantee user existence in server, with the correct password
		assert msg.startswith('Successful'),'LocalConfigLoginError'
		USR=usr
		logging.info('auto login')
	del crpt,sha3_256 # release
	# finally, refresh local user and overwrites config
	if usr!='admin': # admin mustn't be recorded into config
		if usr not in list(map(lambda x:x[0],loc_usrs)):
			loc_usrs.append((usr,pwd))
	with open(os.environ[base[os.name]]+'/vsxClient.cfg','w',encoding='utf-8') as config:
		for each in loc_usrs:
			config.writelines((each[0]+'\n',each[1]+'\n'))
	logging.info('config updated')

ALIVE=True # program keep-alive
def keep_conn(interval:int|float):
	while ALIVE:
		dialog(method='post',command='keep',data={'username':USR})
		sleep(interval)

CUR_RM='' # the current room the user is now in
CUR_GM='' # the current game of the room the user is in; initialized as '' (no game)
CMD_LS=[] # available command list
def command_cycle():
	logging.info('enters command cycle')
	global REC,CUR_RM,CUR_GM,CMD_LS
	print('\nNow you\'ve entered the command cycle.')
	print('Getting full command list...'); sleep(0.7)
	res=dialog(method='get',command='get_cmd_ls')
	print(res['message'])
	CMD_LS=res['data']['commands'].split() # command list
	cmd_des=res['data']['description'] # command description
	# lobby: bool is deprecated, can be replaced by CUR_RM (whether empty string)
	while True:
		while GM_MOD: # blocks the command cycle here if game starts; needs improvements
			sleep(min(INTV['gmrd'],INTV['gmst']))
		sleep(0.7)
		print('\nCommands available:'); sleep(0.7)
		for each in cmd_des.split('\n\n'):
			print(each,end='\n\n'); sleep(0.3)
		print('Notice that you should type the full name, or the first letter, of the commands...')
		print('...but luckily the cases of input doesn\'t matter, which is good news.'); sleep(0.7)
		cmd=input('\nYour command ?=\n').lower(); sleep(0.7)
		logging.debug(f'wT with cmd: {cmd}')
		match cmd:
			case 'quit'|'q':
				terminate()
			case 'public'|'p':
				msg=input('Enter the message you want to say to everyone :=\n')
				logging.debug(f'p_msg: {msg}')
				res=dialog(method='post',command='pub_chat',data={'username':USR,'message':msg})
				print(res['message'])
				REC[0]+=1
			case 'enter'|'e':
				if CUR_RM: print('Already in a room!'); continue
				res=dialog(method='get',command='get_rms')
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
					if rm not in list(REC[1].keys()): # haven't entered this room during this login
						REC[1][rm]=0 # initialize room history read position record
					if rm in rm_ls: # room exists in server
						logging.debug(f'e: {rm}')
						res=dialog(method='post',command='enter',data={'username':USR,'roomid':rm})
					else: # room doesn't exist, thus create it
						logging.debug(f'c: {rm}')
						res=dialog(method='post',command='create',data={'username':USR,'roomid':rm})
					print(res['message'])
			case 'room'|'r':
				if not CUR_RM: print('Not in a room yet!'); continue
				msg=input('Enter the message you want to say to your room members :=\n')
				logging.debug(f'r_msg: {msg}')
				res=dialog(method='post',command='rm_chat',data={'username':USR,'message':msg})
				print(res['message'])
				REC[1][CUR_RM]+=1
			case 'leave'|'l':
				if not CUR_RM: print('Not in a room yet!'); continue
				CUR_RM='' # resets room
				res=dialog(method='post',command='leave',data={'username':USR})
				print(res['message'])
			case 'setup'|'game_setup'|'s'|'gsu': # game choosing and setup; for Room Hosts only
				if not CUR_RM: print('Not in a room yet!'); continue
				if CUR_GM:
					print('Already loaded a game in current room! Please get ready!'); continue
				res=dialog(method='get',command='get_gms') # should return with ['data']['games']=' '.join(games_list)
				print(res['message'])
				print('Games available: '+res['data']['games'])
				game=input('Enter the game you want to play:\n')
				logging.debug(f'gsu: {game}')
				if game in res['data']['games'].split():
					# first get required args for game setup
					res=dialog(method='get',command='get_gm_req',data={'game':game}) # no need to verify if host or not
					print(res['message'])
					print('Required params for game setup:\n'+(req:=res['data']['required'])) # req uses sep==','
					params=input('Please input the proper params for gameplay:\n')
					while len(params.split(' '))!=len(req.split(',')):
						print('Parameter count error!')
						params=input('Please input the proper params for gameplay:\n')
					logging.debug(f'params: {params}')
					res=dialog(method='post',command='gm_setup',data={
						'username':USR,'game':game,'params':params}) # param checking done by server
					print(msg:=res['message'])
					if msg.startswith('Successful'): # game-setup request fulfilled
						CUR_GM=game
				else:
					print("Game doesn't exist!")
			case 'ready'|'game_ready'|'rd'|'gr': # getting ready for gameplay
				if not CUR_GM:
					print('Game not set up yet!'); continue
				res=dialog(method='post',command='gm_ready',data={'username':USR})
				print(res['message'])
			case 'start'|'game_start'|'st'|'gst':
				if not CUR_GM:
					print('Game not set up yet!'); continue
				res=dialog(method='post',command='gm_start',data={'username':USR})
				print(res['message'])
				# TBD: remember to remove (reset) GM_MOD after game ends
			case _:
				if T:
					match cmd:
						case 'get_pub_msg':
							pub_rec=REC[0]
							res=dialog(method='get',command=cmd,data={'last':pub_rec})
							print(res['message'])
							pub_msg=res['data']['messages']
							if pub_msg:
								print(pub_msg+'\n')
								REC[0]+=len(pub_msg.split('\n'))
						case 'get_rm_msg':
							rm_rec=REC[1][CUR_RM]
							res=dialog(method='get',command=cmd,data={'username':USR,'last':rm_rec})
							print(res['message'])
							rm_msg=res['data']['messages']
							if rm_msg:
								print(rm_msg+'\n')
								REC[1][CUR_RM]+=len(rm_msg.split('\n'))
						case _:
							print('Command incorrect !')
				elif cmd not in CMD_LS: print('Command incorrect!')

REC=[0,{}] # chat history record (the position of already-read/last-received messages)
# in the form of [pub_rec,{rid:rm_rec,rid:rm_rec...}], with types: rid->str, rec->int
def msg_refr(interval:int|float): # refreshes, if to receive new chat messages
	global REC
	while ALIVE:
		if CUR_RM:
			rm_rec=REC[1][CUR_RM]
			res=dialog(method='get',command='get_rm_msg',data={'username':USR,'last':rm_rec})
			if T: print(res['message'])
			rm_msg=res['data']['messages']
			if rm_msg:
				print('\n-------------     New Room Messages!     -------------'
				      +rm_msg+'\n'+
				      '-------------     Message Ends     -------------\n')
				REC[1][CUR_RM]+=len(rm_msg.split('\n'))
		pub_rec=REC[0]
		pub_msg=dialog(method='get',command='get_pub_msg',data={'last':pub_rec})['data']['messages']
		if pub_msg:
			print('\n-------------     New Public Messages!     -------------'
			      +pub_msg+'\n'+
			      '-------------     Message Ends     -------------\n')
			REC[0]+=len(pub_msg.split('\n'))
		sleep(interval)

GM_ST={'info_rec':0,'player':''} # in-game status
GM_MOD=None # should be of type 'module'
def __get_gm_rd(interval:int|float): # comes into effect on room entrance, and stops on game start
	global CUR_GM,GM_MOD
	while ALIVE:
		if CUR_RM:
			if not GM_MOD: # in room, game not started
				res=dialog(method='get',command='get_gm_rd',data={'username':USR})
				if T: print(res['message'])
				data=res['data'] # might be empty if game not set up
				if data and not CUR_GM:
					CUR_GM=data['name'] # no output here, since sys msg is added when host set up the game
				if 'ready' in data:
					print('\nCurrent players ready for the game:\n'+(data['ready'] or 'None'))
				else: # game started
					GM_MOD=imm(CUR_GM+'4Client') # imports the local game module
				sleep(interval)
			else:
				return True # game started
		else: sleep(interval)

def __get_gm_st(interval:int|float): # comes into effect on game start, and fades on game finish
	global GM_ST
	while ALIVE:
		if GM_MOD:
			res=dialog(method='get',command='get_gm_st',data={'username':USR,'last':GM_ST['info'][0]})
			if T: print(res['message'])
			data=res['data']
			if data:
				if info:=data['info']: # data['info'] is unread sys info ('\n'-joined); can be empty
					print('\n-------------     New GameSys Messages!     -------------'
						  +info+ # refreshes public game_sys information, such as who did what
						  '\n-------------     Message Ends     -------------\n')
					GM_ST['info_rec']+=len(data['info'].split('\n'))
				if GM_ST['player']!=data['status']:
					GM_ST['player']=data['status'] # replace old user_status
					decision=GM_MOD.handle_status(GM_ST[1]) # decision-making; temporarily no time limit
					if decision:
						res=dialog(method='post',command='gm_op',data={'username':USR,'operation':decision})
						print(res['message'])
		else: # game ends
			return True
		sleep(interval)

def get_gm_pgrs(): # get game progress
	interval=min(INTV['gmrd'],INTV['gmst'])
	gm_rd=EXECUTOR.submit(__get_gm_rd,INTV['gmrd']) # is of type EXECUTOR.Future
	while not gm_rd.done(): sleep(interval)
	del gm_rd
	gm_st=EXECUTOR.submit(__get_gm_st,INTV['gmst'])
	while not gm_st.done(): sleep(interval)
	del gm_st
	pass # TBD: recover the command_cycle, or else

def terminate(): # includes exit() method
	logging.info('terminating program')
	global ALIVE
	ALIVE=False
	res=dialog(method='post',command='logout',data={'username':USR})
	logging.debug('user logout')
	print(res['message'])
	logging.debug('TPE shutdown')
	sleep(1)
	input('\nProgram finished, press enter to quit......\n')
	EXECUTOR.shutdown(cancel_futures=True)

def handle_error(err: Exception):
	logging.info(f'handling error: {err}')
	if T: print(type(err))
	from urllib.error import URLError
	from http.client import RemoteDisconnected
	if SF:=isinstance(err, (URLError, RemoteDisconnected)): # server failed
		print("\nOops! Seems the server isn't online now......")
	else:
		print('\nOops! An error has just occurred......')
	logging.debug(f'SF: {SF}')
	from traceback import print_exc
	print_exc(); sleep(1)
	print('Starting offline mode......\n'); sleep(0.7)
	if not input('press enter to start a mini-game ?'):
		game_name = input('enter the name of the game you want to play ?=')
		if game_name in GAMES:  # TBD
			pass
	if not SF:  # server connection working, can request to log out
		terminate()
	else:
		input('Program finished, press enter to quit......\n')
		os._exit(1)

def admin_mode():
	pass

def log_init():
	try:
		os.mkdir('./log')
	except FileExistsError: pass
	logging.basicConfig(
		filename=f"./log/{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}.log",filemode='w',
		format='\n%(asctime)s ——— %(name)s ——— %(levelname)s <—— from: %(funcName)s\n%(message)s',
		level=logging.DEBUG)
	logging.debug('Logging config initialized.')
	# finally, delete log files too old (e.g. 7 days or older)
	cmd='dir' if os.name=='nt' else 'ls'
	file_list=os.popen(f'{cmd} "./log/"').readlines()[6:-2]
	# res[0]/[1] = Drive/Serial
	# \n
	# res[3] = directory
	# \n
	# res[4]/[5] = '.'/'..'
	# res[6:-2] := wanted filename_list
	# res[-2] = files
	# res[-1] = folders
	import re
	for each in file_list[:-1]: # the last one is current log
		name=each.split()[-1] # actual filename only
		if re.match(re.compile(r'\d\d\d\d_\d\d_\d\d_\d\d_\d\d_\d\d.log'),name):
			file_time=int(''.join(name[:-4].split('_')))
			cur_time=int(dt.now().strftime('%Y%m%d%H%M%S'))
			if cur_time-file_time>LOG_LIM*100**3: # more than 7 days
				os.remove(f'./log/{name}')
	logging.info('cleanup logs from too long ago')

if __name__=='__main__':
	log_init()
	T=bool(input('test mode ?')); sleep(0.7)
	logging.debug(f'T: {T}')
	print('\nClient version : '+CLIENT_VERSION+'\n'); sleep(0.7)
	try:
		print(trial:=dialog(method='post',command='try')['message'])
		assert trial.startswith('Successful')
		logging.debug('trial passed')
		print("\nWelcome to Varisox137's server! (still improving yet)"); sleep(0.7)
		log_or_reg() # login or registration, USR set
		sleep(1)
		if USR=='admin':
			print('\nTBD......')
			EXECUTOR.submit(admin_mode)
		elif not T:
			EXECUTOR.submit(command_cycle)
			EXECUTOR.submit(keep_conn,INTV['keep'])
			EXECUTOR.submit(msg_refr,INTV['msg'])
			EXECUTOR.submit(get_gm_pgrs)
		else:
			EXECUTOR.submit(keep_conn,INTV['keep']*60)
			EXECUTOR.submit(command_cycle)
	except Exception as e:
		handle_error(e)
