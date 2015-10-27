#!/bin/bash

if [ $# -ne 2 ]; then
	echo "usage: $0 <user|group> <msg>"
	exit 1
fi

echo "JID=alerts@chat.jabber.com/alerts" > ~/.xsend
echo "PASSWORD=alerts123" >> ~/.xsend

sent="false"

for user in `ldapsearch -x "(cn=$1)" memberuid | grep -i memberuid | grep -v ^# | awk '{print $NF}'`; do
	sent="true"
	/usr/local/bin/xsend.py $user@example.com "$2"  > /dev/null 2>&1
done

for user in `ldapsearch -x "(uid=$1)" | grep ^uid: | awk '{print $NF}'`; do 
	sent="true"
	echo "sending a message to $user"
	/usr/local/bin/xsend.py $user@example.com "$2"  > /dev/null 2>&1
done

if [ "$sent" == "false" ]; then
	echo "no notifications sent"
	exit 1
fi
