#!/bin/bash

if [ $# -lt 1 ]; then
	echo "usage: $0 <ip-list>"
	exit 0
fi
export PATH=$PATH:/usr/sbin/

notification=sysadmins@example/com
alertsfile=/var/tmp/.autodiscover_alerts.$1
send_email="false"
err_msg="Found new IP's that do not appear to be monitored by nagios (or dont have reverse DNS so I cant figure out what to look for in nagios)\n\n"
nagiosdir="/etc/nagios/org/hosts/discovery/"

find /var/tmp/ -maxdepth 1 -name .autodiscover_alerts.$1 -mtime +7 -exec rm -f {} \;

touch $alertsfile

set -o pipefail

for ip in $@; do
	# HARD CODED IPS TO IGNORE
	if [ $ip != 192.168.1.1 ] \
	&& [ $ip != 192.168.1.255 ] \
	; then
		ping -c 1 -W 1 $ip > /dev/null 2>&1
		if [ $? -eq 0 ]; then
			hostname=`host $ip | awk '{print $NF}' | awk -F. '{print $1}'`
			if [ $? -eq 0 ]; then
				lookfor=$hostname
			else
				lookfor=$ip
			fi
		
			found="false"
			for file in `find /etc/nagios/org -type f -exec grep -il $lookfor {} \;`; do
				count=`grep $lookfor $file | grep host_name | wc -l`
				if [ $count -ge 1 ]; then
					found="true"
				fi
			done
		
			if [ $found == "false" ]; then
				already_alerted=`grep $ip $alertsfile | wc -l`
				if [ $already_alerted -eq 0 ]; then
					echo $ip >> $alertsfile
					send_email="true"
					err_msg="${err_msg}${ip} $hostname\n"
					if [ $hostname != "3(NXDOMAIN)" ]; then
						echo "define host{"                                             >> $nagiosdir/${hostname}.cfg
						echo "   host_name                    $hostname"                >> $nagiosdir/${hostname}.cfg
						echo "   hostgroups                   linux,genericdisk,nrpe"   >> $nagiosdir/${hostname}.cfg
						echo "   alias                        $hostname"                >> $nagiosdir/${hostname}.cfg
						echo "   address                      $hostname"                >> $nagiosdir/${hostname}.cfg
						echo "   use                          template-host"            >> $nagiosdir/${hostname}.cfg
						echo "}"                                                        >> $nagiosdir/${hostname}.cfg
					fi
				fi
			fi
		fi
	fi

done

if [ $send_email == "true" ]; then
	export EMAIL="Nagios Autodiscovery <autodiscovery@example.com>"
	echo -e "$err_msg\n\n\nThis email was sent from $0 on `hostname`" | mutt -s "Unmonitored Servers Found" $notification
	service nagios reload
fi
