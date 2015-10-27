#!/bin/bash

exit 0

flagfile=/etc/.freeipa_configured

if [ ! -f $flagfile ]; then
        logger -t "chefscript: `basename $0`" -p local0.notice "configuring freeipa"
        randompass=`/usr/bin/openssl rand -base64 8`
        /usr/sbin/ipa-server-install --hostname=`hostname -f` -n ipa.example.com -r IPA.EXAMPLE.COM -U -a "$randompass" -p "$randompass" >> /root/example_freeipa.log 2>&1
        if [ $? -eq 0 ]; then
                touch $flagfile
                logger -t "chefscript: `basename $0`" -p local0.notice "much success in configuring freeipa"
        else
                logger -t "chefscript: `basename $0`" -p local0.notice "failed to configure freeipa"
        fi
fi
