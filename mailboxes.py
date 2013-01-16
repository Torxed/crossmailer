from pickle import load, dump
from helpers import *
from logger import *

from time import time # Should not need to be here, debug!


accounts = {'anton' : {'password' : 'test', 'mailboxes' : {'inbox' : 0, 'shared' : 55}}}
mailboxes = {0 : {'name' : 'Inbox', 'mails' : {0 : {'flags' : ['seen'], 'recieved' : time()}}}, 55 : {'name' : 'Shared', 'mails' : {0 : {'flags' : ['unseen'], 'recieved' : time()}}}}