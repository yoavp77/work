#!/bin/bash

notification="user@exmple.org"
who | awk -F'(' '{print $NF}' | sort | uniq > /var/tmp/who.now
touch /var/tmp/who.prev

diffcount=`comm -23 /var/tmp/who.now /var/tmp/who.prev | wc -l`

if [ $diffcount -ne 0 ]; then
        export EMAIL="Login Alert <loginalert@example.com>"
        w | mutt -s "New Login Detected On `hostname`" $notification
        sort /var/tmp/who.now /var/tmp/who.prev | uniq > /tmp/logins.$$
        mv /tmp/logins.$$ /var/tmp/who.prev
fi

usercount=`who | wc -l`
/usr/local/bin/graphitify logins.`hostname` $usercount `date '+%s'`
