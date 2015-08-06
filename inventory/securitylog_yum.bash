#!/bin/bash

pgrep -f '/usr/bin/python /usr/bin/yum info-sec' > /dev/null 2>&1
if [ $? -eq 0 ]; then
	logger -p user.crit 'yum security updates not running'
	exit 0
fi 

random=`echo $[ 1 + $[ RANDOM % 60 ]]`
sleep $random

/usr/bin/yum info-sec --security 2>/dev/null | sed ':a;N;$!ba;s/===============================================================================\n/ /g' > /etc/.vimeo_security_updates 
