from helpers import *
from logger import *
from mailboxes import *
from time import time
from threading import *

class IMAP(Thread):
	def __init__(self, sender):
		Thread.__init__(self)

		self.user = None
		self.authed = False
		self.idle = False
		self.account = None
		self.idledata = {'lastseen' : time(), 'mailcount' : 0, 'mailboxid' : 0}
		self.mailbox = None
		self.sender = sender

		self.start()

	def parse(self, data):
		ret = ''
		for line in data.split('\r\n'):
			if len(line) <= 0: continue

			lline = line.lower()

			log('{IN} ' + str([line]), 'IMAP')

			if ' ' in line:
				num, command = lline.split(' ',1)
				if command == 'capability':
					ret += '* CAPABILITY IMAP4rev1 IDLE NAMESPACE MAILBOX-REFERRALS\r\n' + num + ' OK COMPABILITY completed\r\n' #IMAPv4 :  STARTTLS AUTH=SKEY AUTH=PLAIN LOGINDISABLED
				elif command == 'authenticate plain':
					ret += '+ \r\n'
				elif command[:5] == 'login':
					command, user, pwd = command.split(' ',2)
					user = refstr(user)
					pwd = refstr(pwd)

					# accounts = {'anton' : {'password' : 'test', 'mailboxes' : {'Inbox' : 0, 'Inboxtrash' : 1, 'Shared' : 55}}}
					# mailboxes = {0 : {'name' : 'Inbox'}, 1 : {'name' : 'Inboxtrash'}, 55 : {'name' : 'Shared'}}
					if user in accounts and accounts[user]['password'] == pwd:
						self.user = user
						self.authed = True
						ret += num + ' OK Logged in\r\n'
					else:
						ret += num + ' NO Wrong password\r\n'

				elif command[:6] == 'status':
					command, folder = command.split(' ',1)
					if '(' in folder:
						folder, params = folder.split('(',1)
						params = params[:-1] # Trailing )
					else:
						params = None
					folder = refstr(folder)

					if folder in accounts[self.user]['mailboxes']:
						mailboxid = accounts[self.user]['mailboxes'][folder]
						mailbox = mailboxes[mailboxid]

						uid = len(mailbox['mails'])-1
						unseen = 0
						recent = 0
						for mailid in mailbox['mails']:
							if 'unseen' in mailbox['mails'][mailid]['flags']:
								unseen += 1
							if time() - mailbox['mails'][mailid]['recieved'] > 1:
								recent += 1
						ret += '* "' + folder + '" (UIDNEXT ' + str(uid) + ' MESSAGES ' + str(uid+1) + ' UNSEEN ' + str(unseen) + ' RECENT ' + str(recent) + ')\r\n'
						ret += num + ' OK STATUS completed\r\n'
					else:
						ret += num + ' NO Theres no mailbox with that name\r\n'

				elif command == 'noop':
					ret += num + ' OK NOOP completed\r\n'
				elif command[:6] == 'create':
					command, folder = command.split(' ',2)
					folder = refstr(folder)
					if self.authed and not folder in accounts[self.user]['mailboxes']:
						mailboxid = len(mailboxes)
						mailboxes[mailboxid] = {'name' : refstr} # <- Fix, command+folder is lowered at the top!
						accounts[self.user]['mailboxes'][folder] = mailboxid
						ret += num + ' OK Mailbox created\r\n'
					else:
						ret += num + ' NO Failed to create the mailbox\r\n'
						print self.authed, accounts[self.user]['mailboxes']
				elif command[:9] == 'subscribe':
					command, folder = command.split(' ',2)
					folder = refstr(folder)
					if self.authed and folder in accounts[self.user]['mailboxes']:
						ret += num + ' OK Youre subscribed\r\n'
					else:
						ret += num + ' NO Folder not found\r\n'
				elif command == 'logout':
					ret += '* BYE IMAP4rev1 Server logging out\r\n'
					self.authed = False
					self.user = None
					ret += num + ' OK Logout complete\r\n'

				elif command == 'namespace':
					# Syntax for IMAPv4 namespaces are:
					# NAMESPACE NIL NIL NIL
					# Order of the nils: Personal, Others, Public/Shared
					ret += '* NAMESPACE (("INBOX" "/")) NIL (("Shared" "/"))\r\n'
					ret += num + ' OK NAMESPACE command completed\r\n'

				elif command[:6] == 'select':
					command, folder = command.split(' ',2)
					folder = refstr(folder)
					if folder in accounts[self.user]['mailboxes']:
						self.mailbox = accounts[self.user]['mailboxes'][folder]
						ret += '* 0 EXISTS\r\n'
						ret += '* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)\r\n'
						ret += num + ' OK [READ-WRITE] SELECT completed\r\n'
					else:
						ret += num + ' NO Folder does not exist!\r\n'

				elif command == 'idle':
					ret += '+ idling (' + num + ')\r\n'
					self.idle = num
					self.idledata['lastseen'] = time()

				elif command[:4] == 'lsub':
					command, params, folder = command.split(' ',2)
					params = refstr(params)
					folder = refstr(folder)
					if folder == 'inbox*':
						ret += '* LSUB () "." INBOX\r\n'
						ret += num + ' OK LSUB completed\r\n'
					elif folder == 'shared*':
						ret += '* LSUB () "." Shared\r\n'
						ret += num + ' OK LSUB completed\r\n'
					else:
						ret += num + ' NO This folder is not here\r\n'

				elif command[:3] == 'uid':
					if self.mailbox == None:
						return num + ' NO You need to select a mailbox first!\r\n'

					command, do, mails = command.split(' ',2)
					if '(' in mails:
						mails, params = mails.split('(',1)
						params = params[:-1] # Remove trailing )
					else:
						params = None

					if ':' in mails:
						start, end = mails.split(':',1)
						start = refstr(start)
						end = refstr(end)
						if end == '*':
							end = str(int(start)+1)
						elif end == start:
							end = str(int(start)+1)
					else:
						end = str(int(mails)+1)
					## DEBUG: DANGEROUS!!! ROAR!!
					start, end = int(start),int(end)

					if do == 'fetch':
						for i in range(start, end):
							mail = mailboxes[self.mailbox]['mails'][i]
							if params == 'flags':
								ret += '* ' + str(i) + ' FETCH (FLAGS (' + ' \\'.join(mail['flags']) + ') UID ' + str(i) + '\r\n' 
							else:
								print 'ERROR IN IMAP, UID GAVE UNKNOWN FLAGS'
						ret += num + ' OK UID FETCH completed\r\n'

				elif command[:4] == 'list':
					command, params, folder = command.split(' ',2)
					params = refstr(params)
					folder = refstr(folder)

					if folder in accounts[self.user]['mailboxes']:
						ret += '* LIST () "/" ""\r\n'
						ret += num + ' OK LIST completed\r\n'
					else:
						ret += num + ' NO This folder is not here\r\n'
			else:
				if lline == 'done':
					## Dunno why self.idle changes value between "5 idle" and here "13 OK IDLE.."
					ret += self.idle + ' OK IDLE terminated\r\n'
					self.idle = False

		if len(ret) > 0:
			return ret
		return True

	def run(self):
		while 1:
			if self.idle:
				if self.idledata['mailcount'] != len(mailboxes[self.idledata['mailboxid']]):
					self.sender('* ' + str(len(mailboxes[self.idledata['mailboxid']])) + ' EXISTS\r\n')
					self.idledata['mailcount'] = len(mailboxes[self.idledata['mailboxid']])
			sleep(0.1)

def hello():
	return '* OK hvornum.se'