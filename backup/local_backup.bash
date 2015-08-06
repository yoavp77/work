#!/bin/bash

if [ ! -s /etc/backupdirs ]; then
	logger -p user.crit "nothing to back up, $0 exiting"
	exit 0
fi

notification=sysadmins@example.org
myhost=`hostname | awk -F. '{print $1}'`
rightnow=`date '+%Y%m%d'`
random=`echo $[ 1 + $[ RANDOM % 60 ]]`
option=""
sleep $random

destination=backups.example.org
inlv=`/sbin/ifconfig | grep 10.140. | wc -l`

tar czf /var/tmp/$myhost.$rightnow.tgz -T /etc/backupdirs >> /var/tmp/.tar.$$.log 2>&1

if [ $? -gt 1 ]; then
        export EMAIL="$myhost Backups <backups@example.org>"
        echo -e "Error creating a backup tar file on `hostname` from the following directories:\n\n`cat /etc/backupdirs` \n\nsent from $0" | /usr/bin/mutt -s "$myhost Backup Error #1" -a /var/tmp/.tar.$$.log -- $notification
else
        status=`curl -s $option -X PUT --data-binary @/var/tmp/$myhost.$rightnow.tgz https://$destination:8090/$myhost/$myhost.$rightnow.tgz | grep success | wc -l`
        if [ $status -ne 1 ]; then
                status=`curl -s $option -X PUT --data-binary @/var/tmp/$myhost.$rightnow.tgz https://$destination:8090/$myhost/$myhost.$rightnow.tgz | grep success | wc -l`
                if [ $status -ne 1 ]; then
                        export EMAIL="$myhost Backups <backups@example.org>"
                        echo -e "Error copying backup tar file on `hostname` from \n\n`cat /etc/backupdirs` \n\nsent from $0" | /usr/bin/mutt -s "$myhost Backup Error #2" $notification
                fi
        fi
fi

rm -f /var/tmp/$myhost.$rightnow.tgz
rm -f /var/tmp/.tar.$$.log
