#!/bin/bash

pkill -9 -f john

/usr/local/bin/dump_passwords.pl > /usr/local/john/run/passwords.txt
chmod 700 /usr/local/john/run
chmod 000 /usr/local/john/run/passwords.txt
#cd /usr/local/bin/john
nohup cpulimit -l 20 /usr/local/john/run/john passwords.txt >> /usr/local/john/run/cracked.txt & 
chmod 400 /usr/local/john/run/cracked.txt
