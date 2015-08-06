#!/bin/env python

import os
import time
import datetime
import sys
import json
import socket

# this file contains the output of "yum info-sec --security"
securityfile='/etc/.security_updates'
processing_header=True
package=''
block_count=0
hostname=socket.gethostname()

with open(securityfile, "r") as inputfile:
	data=inputfile.read().split('\n\n')
# each block represents a package that has security updates
for block in data:
	# skip the first block (its just yum verbose output)
	if (block_count > 0 ):
		count=0
		prev_field='text'
		dict={}
		# process each line in this package
		for line in block.split('\n'):
			# the first line in each block is the package name
			if (count == 0 ):
				dict['package']=line.strip()
			# the rest of the lines are package info fields
			else:
				if 'Update ID : '   in line  \
			 	or 'Release : '     in line  \
			 	or 'Description : ' in line  \
			 	or 'Issued : '      in line  \
			 	or 'Type : '        in line  \
			 	or 'Status : '      in line  \
			 	or 'Bugs : '        in line  \
				:
					# create a new field, ie " { 'issued': '2015-01-01'}
					object_string=line.split(':')[0].strip()
					dict[object_string]=line.split(':')[1].strip()
					prev_field=line.split(':')[0].strip()
				else:
					# add the line value to the previous field, ie append { 'issued': '2015-05-01' } + { 'issued': '00:00'} 
					if object_string == '':
						object_string='text'
					dict[object_string]+=line.strip()
			count+=1
		# append some generic fields
		dict['host']=hostname
		dict['plugin']='yum-security'
		dict['date']=str(datetime.datetime.now().isoformat())
		dict['month']=str(datetime.datetime.now().strftime("%Y-%m"))
		print json.dumps(dict)
	block_count+=1

