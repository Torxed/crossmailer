from threading import *
from time import strftime, sleep
import sys

class logger(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.logmap = {}
		self.logpos = 0
		self.start()

	def log(self, s, src=None):
		if not src:
			src = 'CORE'
		self.logmap[len(self.logmap)] = strftime('%Y-%m-%d %H:%M:%S') + ' - [' + src + '] ' + s + '\n'

	def write(self):
		return (len(self.logmap) > self.logpos)

	def run(self):
		while 1:
			while self.write():
				sys.stdout.write(self.logmap[self.logpos])
				sys.stdout.flush()
				self.logpos += 1
			sleep(0.001)

loghandle = logger()
log = loghandle.log