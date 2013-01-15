from os import popen
from logger import *

def refstr(s):
	return s.strip(" \t:,\r\n\"'")

def humantime(t):
	scale = ['sec', 'min', 'hours']
	i = 0
	while t >= 60:
		t = t/60
		i += 1
	return str(int(t)), scale[i]

def sysfunc(command):
	ret = ''
	for l in popen(command, 'r'):
		ret += l
	return ret

def compare(obj, otherobj):
	return (str(obj).lower() == str(otherobj).lower()[:len(str(obj))])
	
def _in(obj, otherobj):
	return (str(obj).lower() in str(otherobj).lower())