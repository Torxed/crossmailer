from helpers import *
from logger import *
from mailboxes import *
from base64 import b64encode as enc
from base64 import b64decode as dec

class SMTP(Thread):
	def __init__(self, sender):
		Thread.__init__(self)

		self.user = None
		self.authed = False

		self.mailbox = None
		self.sender = sender

		self.authed = -1
		self.recievingmaildata = None

		self.start()

	def parse(self, data):
		ret = ''
		for line in data.split('\r\n'):
			lline = line.lower()
			if len(line) <= 0: continue

			log('{IN} ' + str([line]), 'SMTP')

			if self.recievingmaildata != None and self.authed >= 2:
				if lline[:8] == 'rcpt to:':
					self.recievingmaildata['to'] = lline[9:]
					ret += '250 OK\r\n'
				elif lline == 'data':
					ret += '354 End data with <CR><LF>.<CR><LF>\r\n'
				else:
					if not 'data' in self.recievingmaildata:
						self.recievingmaildata['data'] = ''
					self.recievingmaildata['data'] += line + '\r\n'
					if self.recievingmaildata['data'][-5:] == '\r\n.\r\n':
						ret += '250 OK: queued as 1\r\n'
						self.recievingmaildata = None
			elif self.authed == 0:
				self.user = dec(line)
				ret += '334 ' + enc('Password:') + '\r\n'
				self.authed = 1
			elif self.authed == 1:
				pwd = dec(line)
				if self.user in accounts and accounts[self.user]['password'] == pwd:
					ret += '235 Authentication successful\r\n'
					self.authed = 2
				else:
					ret += '535 authentication failed (#5.7.1)\r\n'
					self.authed = -1
			else:
				if lline[:4] == 'ehlo':
					ret += '250-Hello phatop\r\n'
					ret += '250-AUTH LOGIN\r\n' # More login options: PLAIN DIGEST-MD5 GSSAPI
					ret += '250 ENHANCEDSTATUSCODES\r\n'
				elif lline[:4] == 'quit':
					ret += '221 Ok bye bye!\r\n'
				elif lline[:4] == 'auth':
					ret += '334 ' + enc('Username:') + '\r\n'
					self.authed = 0
				elif lline[:10] == 'mail from:' and self.authed >= 2:
					self.recievingmaildata = {}
					self.recievingmaildata['from'] = lline[11:]
					ret += '250 OK\r\n'
				else:
					pass # Need to authenticate

		if len(ret) > 0:
			return ret
		return True

def hello():
	return '220 hvornum.se ESMTP CrossMailer'