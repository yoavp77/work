#!/bin/bash

export IFS=$(echo -en "\n\b")

jsonify ()
{
	date=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
	host=`hostname`
	month=`date '+%Y-%m'`
        echo "{"
        echo '"host"':'"'$host'",'
        echo '"date"':'"'$date'",'
        echo '"'service'"':'"'$1'",'
        echo '"'version'"':'"'$2'",'
	echo '"'plugin'"':'"'$3'",'
	echo '"'month'"':'"'$month'"'
        echo "}"
}

submit () 
{
	curl -XPOST http://elasticserver.example.org/versions/default -d "$1" > /dev/null 2>&1
}

random=`echo $[ 1 + $[ RANDOM % 900 ]]`
sleep $random

# apache check
for pgm in `(ps -o cmd -e | grep httpd | grep -v grep|awk '{print $1}' | sort | uniq ; locate httpd | grep /httpd$) | grep -v /etc/rc.d/init.d/ | sort | uniq `; do
	if [ -x $pgm ] && [ -f $pgm ]; then
		version=`$pgm -v 2>/dev/null`
		if [ $? -eq 0 ]; then
			json=`jsonify "$pgm" "$version" "httpd" | sed ':a;N;$!ba;s/\n/ /g' `
			submit "$json"
			#curl -XPOST http://elasticserver.example.org/versions/default -d "$json"
		fi
	fi
done

for pgm in `(ps -o cmd -e | grep python | grep -v grep|awk '{print $1}' | sort | uniq ; locate python | grep /python$; locate python2.6 | grep /python2.6$; locate python2.7 | grep /python2.7$) | sort | uniq `; do
	if [ -x $pgm ] && [ -f $pgm ]; then
		version=`$pgm -V 2>&1`
		if [ $? -eq 0 ]; then
			submit "`jsonify "$pgm" "$version" "python"`"
			#curl -XPOST http://elasticserver.example.org/versions/default -d "`jsonify "$pgm" "$version" "python"`"
		fi
	fi
done

if [ -r /etc/httpd/modules/libphp5.so ] ; then
	php_version=`strings /etc/httpd/modules/libphp5.so | egrep X-Powered-By | awk '{print $2}'`
	submit "`jsonify "/etc/httpd/modules/libphp5.so" "$php_version" "php-httpd"`"
	#curl -XPOST http://elasticserver.example.org/versions/default -d "`jsonify "/etc/httpd/modules/libphp5.so" "$php_version" "php-httpd"`"
fi

for pgm in `(ps -o cmd -e | grep php | grep -v grep|awk '{print $1}' | sort | uniq | grep php ; locate php | grep /php$) | sort | uniq `; do 
	if [ -x $pgm ] && [ -f $pgm ]; then
		version=`$pgm -v 2>/dev/null| head -1`
		submit "`jsonify "$pgm" "$version" "php"`"
		#curl -XPOST http://elasticserver.example.org/versions/default -d "`jsonify "$pgm" "$version" "php"`"
	fi
done

export IFS="}"

if [ -r /etc/.security_updates ]; then
	for entry in `/usr/local/bin/yumsec_to_json.py`; do
	json="${entry}}"
		if [ "$json" != "}" ]; then
			submit "$json"
		fi
	done
fi

export IFS=$(echo -en "\n\b")

if [ -r /etc/redhat-release ]; then
	version=`cat /etc/redhat-release  | sed ':a;N;$!ba;s/\n/ /g'`
	submit "`jsonify os-version "$version" "redhat-release"`"
fi

for pgm in `(ps -o cmd -e | grep nginx | grep -v grep|awk '{print $1}' | sort | uniq | grep nginx ; locate nginx | grep /nginx$) | sort | uniq `; do
	if [ -x $pgm ] && [ -f $pgm ]; then
		version=`$pgm -v 2>&1 | head -1`
		if [ $? -eq 0 ]; then
			submit "`jsonify "$pgm" "$version" "nginx"`"
		fi
	fi
done

if [ -x /bin/rpm ]; then
	for rpm in `/bin/rpm -qa --queryformat '%{name} %{version}-%{release}\n' 2>/dev/null`; do
		pgm=`echo $rpm | awk '{print $1}'`
		version=`echo $rpm | awk '{print $2}'`
		submit "`jsonify "$pgm" "$version" "rpm"`"
	done
fi

for pgm in `(ps -o cmd -e | grep node | grep -v grep|awk '{print $1}' | sort | uniq | grep node ; locate node | grep /node$) | sort | uniq `; do
	if [ -x $pgm ] && [ -f $pgm ]; then
		version=`$pgm -v 2>/dev/null`
		if [ $? -eq 0 ]; then
			submit "`jsonify "$pgm" "$version" "node"`"
		fi
	fi
done

for pgm in `(ps -o cmd -e | grep haproxy | grep -v grep|awk '{print $1}' | sort | uniq | egrep "haproxy|haproxy443to80" ; locate haproxy | grep /haproxy$) | sort | uniq `; do 
	if [ -x $pgm ] && [ -f $pgm ]; then
		version=`$pgm -v 2>/dev/null | head -1`
		if [ $? -eq 0 ]; then
			submit "`jsonify "$pgm" "$version" "haproxy"`"
		fi
	fi
done

if [ -f /opt/dell/srvadmin/lib64/openmanage/apache-tomcat/bin/catalina.sh ]; then
	export JAVA_HOME=/opt/dell/srvadmin/lib64/openmanage/jre
	version=`bash /opt/dell/srvadmin/lib64/openmanage/apache-tomcat/bin/catalina.sh version | egrep -i "server version"`
	if [ $? -eq 0 ]; then
		submit "`jsonify "tomcat" "$version" "tomcat-dell"`"
	fi
fi
