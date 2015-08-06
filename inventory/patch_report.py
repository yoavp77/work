#!/usr/bin/python

# gets a list of all versions of a specific package and prints a table listing the servers they are installed on and whether or not they can be upgraded

import json
import calendar
import time
import sys
import pycurl
import StringIO
import collections
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-1", "--one", help="first run", action="store_true")
parser.add_argument("-p", "--package", help="package to process", action="store")
args = parser.parse_args()

today=str(calendar.timegm(time.gmtime()))
yesterday=str(calendar.timegm(time.gmtime())-86400)
allvals=[]
table=''
upgrades={}
upgrades['5.3.3-22.el6']='5.3.3-40.el6_6'
upgrades['5.3.3-23.el6_4']='5.3.3-40.el6_6'
upgrades['5.3.3-26.el6']='5.3.3-40.el6_6'
upgrades['5.3.3-27.el6_5']='5.3.3-40.el6_6'
upgrades['5.3.3-27.el6_5.1']='5.3.3-40.el6_6'
upgrades['5.3.3-27.el6_5.2']='5.3.3-40.el6_6'
upgrades['5.3.3-38.el6']='5.3.3-40.el6_6'
upgrades['5.3.3-40.el6_6']='5.3.3-40.el6_6'
upgrades['5.4.14-1.el6.remi']='5.4.40-1.el6.remi'
upgrades['5.4.16-23.el7_0.3']='5.4.16-23.el7_0.3'
upgrades['5.4.33-1.el6.remi']='5.4.40-1.el6.remi'
upgrades['2.2.15-39.el6.centos']='latest'

request_json='\
{ \
  "query": { \
    "filtered": { \
      "query": { \
        "bool": { \
          "should": [ \
            { \
              "query_string": { \
                "query": "*" \
              } \
            } \
          ] \
        } \
      }, \
      "filter": { \
        "bool": { \
          "must": [ \
            { \
              "range": { \
                "date": { \
                  "from": \
                  ' + yesterday + '000 \
                  ,"to": \
                  ' + today + '000 \
                } \
              } \
            }, \
            { \
              "fquery": { \
                "query": { \
                  "query_string": { \
                    "query": "plugin:rpm" \
                  } \
                }, \
                "_cache": true \
              } \
            }, \
            { \
              "fquery": { \
                "query": { \
                  "query_string": { \
                    "query": "service: ' + args.package + '" \
                  } \
                }, \
                "_cache": true \
              } \
            } \
          ] \
        } \
      } \
    } \
  }, \
  "highlight": { \
    "fields": {}, \
    "fragment_size": 2147483647, \
    "pre_tags": [ \
      "@start-highlight@" \
    ], \
    "post_tags": [ \
      "@end-highlight@" \
    ] \
  }, \
  "size": 500, \
  "sort": [ \
    { \
      "host": { \
        "order": "desc", \
        "ignore_unmapped": true \
      } \
    } \
  ] \
} \
'

b = StringIO.StringIO()
c = pycurl.Curl()
c.setopt(pycurl.URL, 'http://elasticserver.example.org:9200/versions/_search?pretty')
#c.setopt(pycurl.URL, 'nms2:5000')
#c.setopt(pycurl.HTTPHEADER, ['Accept: application/json'])
c.setopt(pycurl.WRITEFUNCTION, b.write)
c.setopt(pycurl.VERBOSE, 0)
#c.setopt(pycurl.POST, 1)
c.setopt(pycurl.CUSTOMREQUEST, "GET")
c.setopt(pycurl.POSTFIELDS, request_json)
c.perform()
data = json.loads(b.getvalue())

#with open('all_php_versions.json') as data_file:    
    #data = json.load(data_file)

for record in data['hits']['hits']:
	if not args.one:
		table+="| " +  record['_source']['service'] 
		table+="| " +  record['_source']['version']  
		try:
			upgrades[record['_source']['version']]
		except KeyError:
			latest_version='unknown'
		else:
			latest_version=upgrades[record['_source']['version']]
                table+="| " +  latest_version
		table+="| " +  "FUNCTION"
		table+="| " +  record['_source']['host']  
		table+="| |\n"
	allvals.append(record['_source']['service'] + "-" + record['_source']['version'])


if args.one:
	for element in set(allvals):
		print element
else:
	print table
