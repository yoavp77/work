#!/usr/bin/python

# random stuff
import random
import socket
import time
import datetime
import calendar
import os
import sys
# string stuff
import string
# configtools stuff
from example import ExampleConfig
# email stuff
import smtplib
import poplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# server to relay emails through
relay = "localhost"
# max amount of time to wait for an email to get through
maxWait = 300
# indication of whether the email has arrived at the mailbox
emailArrived = None
# directory to keep result files in
resultDir = "/var/tmp/.relaydelay/"

if not os.path.exists(resultDir):
	os.makedirs(resultDir)

# read pop3 password from config
password = ExampleConfig().get('relay.pop3.password')

# process all pop3 accounts
accounts = ExampleConfig().get('relay.pop3.account')
for pop3Account in accounts:
	timestamp = calendar.timegm(time.gmtime())

	# set up some email stuff
	msg = MIMEMultipart('alternative')
	msg['From'] = "Ops <opsteam@example.com>"
	text = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(500))
	part1 = MIMEText(text, 'plain')
	msg.attach(part1)
	s = smtplib.SMTP(relay)
	##################

	# unique email subject with hostname + timestamp
	msg['Subject'] = "Example Email Delay Check (" + socket.gethostname() + "-" + str(timestamp) + ")"

	# read destination email address from config
	msg['To'] = pop3Account.split(';')[0]

	# send out an email
	s.sendmail("sysadmins@example.com", msg['To'], msg.as_string())

	# poll pop3 mailbox
	emailArrived = None
	M = poplib.POP3_SSL(pop3Account.split(';')[1])
	M.user(pop3Account.split(';')[0])
	M.pass_(password)
	delay = 0

	# check if the email has arrived in the mailbox
	while (emailArrived == None) and (delay < maxWait):
		numMessages = len(M.list()[1])

		# process all emails in the mailbox
		for i in range(numMessages):
			for j in M.retr(i+1)[1]:
				# check this email for the unique random text generated above - if it has arrived, we can exit and stop incrementing 'delay'
				if text in j:
					emailArrived = True
					emailToDelete = i+1

		# no luck yet, sleep X seconds and check mailbox again
		delay = calendar.timegm(time.gmtime()) - timestamp
		time.sleep(1)

		# POP mailbox again
		M = poplib.POP3_SSL(pop3Account.split(';')[1])
		M.user(pop3Account.split(';')[0])
		M.pass_(password)

	# clean up pop3 mailbox
	#for i in range(numMessages):
		#for j in M.retr(i+1)[1]:
			#if socket.gethostname() in j:
				#M.dele(i+1)
	M.dele(emailToDelete)
	M.quit()

	# write delay results to a dedicated file
	fileDelay = open(resultDir + pop3Account.split(';')[0].split('@')[1].split('.')[0] + "_" + str(datetime.date.today().isocalendar()[1]),'a')
	fileDelay.write(str(delay) + "\n")
	fileDelay.close()
	# once the email has arrived (or maxwait has been reached), sent the metric to graphite
	sock = socket.socket()
	sock.connect(("carbon", 2003))
	sock.sendall(socket.gethostname() + ".delay." + pop3Account.split(';')[0].split('@')[1].split('.')[0] + " " + str(delay) + " " + str(int(time.time())))
	sock.close()

s.quit
