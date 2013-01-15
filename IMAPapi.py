from helpers import *
from logger import *

def parse(data):
	ret = ''
	for line in data.split('\r\n'):
		if len(line) <= 0: continue

		lline = line.lower()

		log('{IN} ' + str([line]), 'IMAP')

		if ' ' in line:
			num, command = lline.split(' ',1)
			if command == 'capability':
				ret += '* CAPABILITY IMAP4rev1 IDLE NAMESPACE MAILBOX-REFERRALS\r\n' + num + ' OK\r\n' #IMAPv4 :  STARTTLS AUTH=SKEY AUTH=PLAIN LOGINDISABLED
			elif command == 'authenticate plain':
				ret += '+ \r\n'
			elif command[:5] == 'login':
				command, user, pwd = command.split(' ',2)
				user = refstr(user)
				pwd = refstr(pwd)

				if user == 'anton' and pwd == 'test':
					ret += num + ' OK Logged in\r\n'
				else:
					ret += num + ' NO Wrong password\r\n'
			elif command == 'logout':
				ret += '* BYE IMAP4rev1 Server logging out\r\n'
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
				ret += '* 0 EXISTS\r\n'
				ret += '* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)\r\n'
				ret += num + ' OK [READ-WRITE] SELECT completed\r\n'

			elif command == 'idle':
				ret += '+ idling\r\n'

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

			elif command[:4] == 'list':
				command, params, folder = command.split(' ',2)
				params = refstr(params)
				folder = refstr(folder)

				if folder == 'inbox':
					ret += '* LIST () "/" ""\r\n'
					ret += num + ' OK LIST completed\r\n'
				else:
					ret += num + ' NO This folder is not here\r\n'

	if len(ret) > 0:
		return ret
	return True

def hello():
	return '+OK hvornum.se'