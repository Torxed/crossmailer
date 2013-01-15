from helpers import *
from logger import *

def parse(data):
	ret = ''
	for line in data.split('\r\n'):
		lline = line.lower()
		if len(line) <= 0: continue

		log('{IN} ' + str([line]), 'SMTP')
		if lline[:4] == 'ehlo':
			ret += '250 OK, hi to you too\r\n'
		elif lline[:4] == 'quit':
			ret += '221 Ok bye bye!\r\n'

	if len(ret) > 0:
		return ret
	return True

def hello():
	return '220 hvornum.se ESMTP CrossMailer'