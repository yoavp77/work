#!/bin/bash

if [ $# -ne 1 ]; then
	echo -e "usage: $0 <class C subnet>\n\nexample:\n$0 10.90.128"
	exit 1
fi

set -o pipefail

notification="user@example"
msg="The following hosts exist in DNS but are missing from the inventory at http://racks.example:\n\n"
rc=0

for num in {2..255}; do
	host=`host ${1}.${num} | awk '{print $NF}' | awk -F. '{print $1}'`
	if [ $? -eq 0 ]; then
		if [ "$host" != "3(NXDOMAIN)" ]; then
			in_racks=`echo "select count(name) from RackObject where name = \"${host}\";" | /usr/bin/mysql -u racktables_user --password=\`cat /etc/.dbpass\` racktables_db | grep -v count `
			if [ $? -eq 0 ]; then
				if [ $in_racks -eq 0 ]; then	
					rc=1
					msg="$msg\n${host} ${1}.${num}"
				fi
			fi
		fi
	fi
done

if [ $rc -ne 0 ]; then
	touch /var/tmp/.rackscheck_${1}.old
	echo "$msg" > /var/tmp/.rackscheck_${1}.new
	diff /var/tmp/.rackscheck_${1}.new /var/tmp/.rackscheck_${1}.old > /dev/null 2>&1
	if [ $? -ne 0 ]; then
		export EMAIL="Racks <racks@example>"
		echo -e "$msg\n\nThis message was sent from $0 on `hostname`" | mutt -s "Hosts In $1.0 Missing In Racktables" $notification
		mv -f /var/tmp/.rackscheck_${1}.new /var/tmp/.rackscheck_${1}.old
	fi
fi
