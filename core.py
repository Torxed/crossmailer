#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import asyncore
from threading import *
from time import sleep, strftime, localtime, time
from os import _exit
from socket import *
from helpers import *

from SMTPapi import parse as smtp_parse
from IMAPapi import parse as imap_parse
from SMTPapi import hello as smtp_hello
from IMAPapi import hello as imap_hello

class looper(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.start()
	def run(self):
		log('Iniating asyncore loop')
		asyncore.loop()
		log('Asyncore died')

class SOCK(Thread, asyncore.dispatcher):
	def __init__(self, _s=None, config=None):
		self.conf = config
		Thread.__init__(self)

		self.inbuffer = ''
		self.buffer = ''
		self.lockedbuffer = False
		self.is_writable = False

		self.exit = False

		if _s:
			asyncore.dispatcher.__init__(self, _s)
			if 'INIT' in self.conf:
				self._send(self.conf['INIT']())
		else:
			asyncore.dispatcher.__init__(self)
			self.create_socket(AF_INET, SOCK_STREAM)
			#if self.allow_reuse_address:
			#	self.set_resue_addr()

			log('Iniated socket on "' + self.conf['SERVER'] + '":' + str(self.conf['PORT']), self.conf['NAME'])
			self.bind((self.conf['SERVER'], self.conf['PORT']))
			self.listen(5)

		self.start()

	def parse(self):
		self.lockedbuffer = True
		if 'PARSER' in self.conf:
			self.conf['PARSER'](self.inbuffer)
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
		return (len(self.buffer) > 0)
	def handle_write(self):
		while self.is_writable:
			sent = self.send(self.buffer)
			if 'NAME' in self.conf:
				log('Sent: ' + str([sent]), self.conf['NAME'])
			else:
				log('Sent: ' + str([sent]), 'Unknown')

			self.buffer = self.buffer[sent:]
			if len(self.buffer) <= 0:
				self.is_writable = False
			sleep(0.01)
	def _send(self, what):
		self.buffer += what + '\r\n'
		self.is_writable = True
	def handle_error(self):
		print 'Error, closing socket!'
		self.close()

	def run(self):
		while not self.exit:
			if len(self.inbuffer) > 0:
				r = self.parse()
				if r in (True, False, None):
					pass
				else:
					self._send(r)
			sleep(0.01)
		self.close()


imap = SOCK(config={'NAME' : 'IMAP', 'SERVER' : '', 'PORT' : 143, 'PARSER' : imap_parse, 'INIT' : imap_hello})
smtp = SOCK(config={'NAME' : 'SMTP', 'SERVER' : '', 'PORT' : 25, 'PARSER' : smtp_parse, 'INIT' : smtp_hello})

l = looper()
try:
	while 1:
		sleep(0.1)
except:
	_exit(0)