#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import asyncore
from threading import *
from time import sleep, strftime, localtime, time
from os import _exit
from socket import *
from helpers import *
from random import randint

from SMTPapi import parse as smtp_parse
from IMAPapi import IMAP as imaplib
from SMTPapi import hello as smtp_hello
from IMAPapi import hello as imap_hello

from mailboxes import *

from logger import *

class looper(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.start()
	def run(self):
		log('Iniating asyncore loop')
		asyncore.loop()
		log('Asyncore died')

class sender(Thread):
	def __init__(self, sock_send, source):
		Thread.__init__(self)

		self.s = sock_send
		self.bufferpos = 0
		self.buffer = {}
		self.source = source

		self.start()

	def send(self, what):
		if what[-2:] != '\r\n':
			what += '\r\n'
		self.buffer[len(self.buffer)] = what

	def writable(self):
		return (len(self.buffer) > self.bufferpos)

	def run(self):
		while 1:
			if self.writable():
				logout = str([self.buffer[self.bufferpos].replace('\r\n','')])
				if len(logout) >= 45:
					logout = logout[:45] + '...'
				log('{OUT} ' + logout, self.source)
				self.s(self.buffer[self.bufferpos])
				self.bufferpos += 1

class SOCK(Thread, asyncore.dispatcher):
	def __init__(self, _s=None, config=None):
		self.conf = config
		Thread.__init__(self)

		self._s = _s

		self.inbuffer = ''
		#self.buffer = ''
		self.lockedbuffer = False
		self.lockedoutbuffer = False
		self.is_writable = False

		self.exit = False

		if _s:
			asyncore.dispatcher.__init__(self, _s)
			self.sender = sender(self.send, self.conf['NAME'])

			## Only add a parser if theres a client socket present.
			## There's no need to start a parser for a binded socket.
			if 'PARSER' in self.conf:
				self.parser = self.conf['PARSER']()
			else:
				self.parser = None

			if 'INIT' in self.conf:
				self.sender.send(self.conf['INIT']() + '\r\n')
		else:
			asyncore.dispatcher.__init__(self)
			self.create_socket(AF_INET, SOCK_STREAM)
			#if self.allow_reuse_address:
			#	self.set_resue_addr()

			log('Iniated socket on "' + self.conf['SERVER'] + '":' + str(self.conf['PORT']), self.conf['NAME'])
			self.bind((self.conf['SERVER'], self.conf['PORT']))
			self.listen(5)

			self.sender = None

		self.start()

	def parse(self):
		self.lockedbuffer = True
		if self.parser:
			r = self.parser.parse(self.inbuffer)
			if r not in (True, False, None):
				self.sender.send(r)
			else:
				if 'NAME' in self.conf:
					log('{Empty} Parser responded empty', self.conf['NAME'])
				else:
					log('{Empty} Parser responded empty', 'Unknown')
		else:
			print 'IN:',[self.inbuffer]
		self.inbuffer = ''
		self.lockedbuffer = False

	def readable(self):
		return True
	def handle_connect(self):
		print 'Connected!'
	def handle_accept(self):
		(conn_sock, client_address) = self.accept()
		log('Iniating connection with: ' + str(client_address), self.conf['NAME'])
		if self.verify_request(conn_sock, client_address):
			self.process_request(conn_sock, client_address)
	def process_request(self, sock, addr):
		log('	Accepted: ' + str(addr), self.conf['NAME'])
		if not 'INIT' in self.conf:
			self.conf['INIT'] = None
		x = SOCK(sock, config={'PARSER' : self.conf['PARSER'], 'INIT' : self.conf['INIT'], 'NAME' : self.conf['NAME']})
	def verify_request(self, conn_sock, client_address):
		return True
	def handle_close(self):
		self.close()
	def handle_read(self):
		data = self.recv(8192)
		while self.lockedbuffer:
			sleep(0.01)
		self.inbuffer += data
	def writable(self):
		return True
	def handle_write(self):
		pass
		#while self.bufferpos < len(self.buffer):
		#	if not self.buffer[self.bufferpos][-2:] == '\r\n':
		#		self.buffer[self.bufferpos] += '\r\n'

		#	sent = self.send(self.buffer[self.bufferpos])
		#	if 'NAME' in self.conf:
		#		log('{Sent} ' + str(self.buffer[self.bufferpos][:20]).strip('\r\n'), self.conf['NAME'])
		#	else:
		#		log('{Sent} ' + str(self.buffer[self.bufferpos][:20]).strip('\r\n'), 'Unknown')
		#	self.bufferpos += 1

		#self.is_writable = False

	def run(self):
		while not self.exit:
			if len(self.inbuffer) > 0:
				self.parse()
			sleep(0.01)
		self.close()


imap = SOCK(config={'NAME' : 'IMAP', 'SERVER' : '', 'PORT' : 143, 'PARSER' : imaplib, 'INIT' : imap_hello})
#smtp = SOCK(config={'NAME' : 'SMTP', 'SERVER' : '', 'PORT' : 25, 'PARSER' : smtp_parse, 'INIT' : smtp_hello})

l = looper()
try:
	while 1:
		sleep(0.1)
except:
	_exit(0)