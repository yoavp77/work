#!/usr/bin/env python

# lots of single-use imports
from datetime import datetime, timedelta
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from errno import EEXIST
from getpass import getuser
from json import loads
from operator import itemgetter
from Queue import Queue
#from smtplib import SMTP
import smtplib
#from socket import gethostname
from time import time
from threading import Thread
from urllib2 import Request, urlopen
import os
import sys
import argparse

# additional imports
import pycurl
import json
import StringIO
import socket
import shutil
import re
import types
import locale

# this is used to validate that metrics are numeric
NumberTypes = (types.IntType, types.LongType, types.FloatType, types.ComplexType)

# retrun total number of running machines per second for a given date
def get_tran_hours(tran_date):
    b = StringIO.StringIO()
    c = pycurl.Curl()
    # URL to return a json from graphite with a count of machines per second
    graphite_url_integral='http://graphite.df.vimeows.com/render?height=800&width=1840&title=TC+Machines+AWS&salt=1425569237655&tz=UTC&lineWidth=2&template=vimeo&hideLegend=0&target=alias(integral(sumSeries(stats.gauges.ec2_region_instance_type.*.c38xlarge)),"vals")&areaMode=stacked&from=00:00_'
    c.setopt(pycurl.URL, graphite_url_integral + tran_date + '&until=23:59_' + tran_date + '&format=json')
    c.setopt(pycurl.HTTPHEADER, ['Accept: application/json'])
    c.setopt(pycurl.WRITEFUNCTION, b.write)
    c.setopt(pycurl.VERBOSE, 0)
    c.perform()
    tran_hours = json.loads(b.getvalue())
    # find the last valid numeric value in the graphite json (often the last value is garbage)
    last_value=len(tran_hours[0]['datapoints']) - 1
    while (not isinstance(tran_hours[0]['datapoints'][last_value][0], NumberTypes)):
        last_value-=1
    # the last value in the json is the total of machine hours for this time period
    count=tran_hours[0]['datapoints'][last_value][0]
    return int(count)
def write_graph_to_file(tran_date,file_name):
    d = pycurl.Curl()
    graphite_url_sum='http://graphite.df.vimeows.com/render?height=400&width=940&title=TC+Machines+AWS&salt=1425569237655&tz=UTC&lineWidth=2&template=vimeo&hideLegend=0&target=groupByNode(stats.gauges.ec2_region_instance_type.*.c1xlarge,3,%27sumSeries%27)&target=groupByNode(stats.gauges.ec2_region_instance_type.*.c38xlarge,3,%27sumSeries%27)&areaMode=stacked&from=00:00_'
    #c.setopt(pycurl.URL, graphite_url_integral + workdate + '&until=23:59_' + workdate + '&format=json')
    #c.setopt(pycurl.WRITEFUNCTION, b.write)
    #c.perform()
    #last_week_tran_hours = json.loads(b.getvalue())
    # save the image that shows instance launch times to a file that can be attached to an email
    with open(file_name,'w') as myfile:
        d.setopt(pycurl.URL, graphite_url_sum + tran_date + '&until=23:59_' + tran_date)
        d.setopt(d.WRITEFUNCTION, myfile.write)
        d.setopt(pycurl.HTTPHEADER, ['Accept: application/json'])
        d.perform()
    myfile.closed
    return 0

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-d", "--date", help="date to use, for example 20150101 (defaults to today)", action="store")
    parser.add_argument("-e", "--email", help="email to send report to", action="store")

    guesstimate=0.0469

    # parse arguments
    args = parser.parse_args()

    # default date to parse is today
    if args.date:
        workdate=str(args.date)
    else:
        workdate=str(datetime.now().strftime("%Y%m%d"))
    count=get_tran_hours(workdate)

    # send an email if necessary
    if args.email:
        tmpfile='/var/tmp/.graph_file_today.jpg'
        lastweekfile='/var/tmp/.graph_file_lastweek.jpg'

        lastweekdate=datetime.strptime(workdate,"%Y%m%d") - timedelta(days=7)
        lastweekcount=get_tran_hours(lastweekdate.strftime("%Y%m%d"))

        # write graph attachments to file
        write_graph_to_file(workdate,tmpfile)
        write_graph_to_file(lastweekdate.strftime("%Y%m%d"),lastweekfile)

        # send out the email
        strFrom = 'Tran Bill <tranbill@vimeo.com>'
        strTo = args.email
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = 'EC2 Tran Bill ' + datetime.strptime(workdate,"%Y%m%d").strftime('%Y-%m-%d') + ' $' + str(int(count * guesstimate))
        msgRoot['From'] = strFrom
        msgRoot['To'] = strTo
        msgRoot.preamble = 'This is a multi-part message in MIME format.'
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        msgText = MIMEText('This is the alternative plain text message.')
        msgAlternative.attach(msgText)

        # We reference the image in the IMG SRC attribute by the ID we give it below
        msgText = MIMEText('Hours: ' + str(int(count)) + ' Estimated bill: $' + str(int(count * guesstimate)) + '<br><img src="cid:image1"><br>Prev weeks hours: ' + str(lastweekcount) + ' Estimated Bill: $' +  str(int(lastweekcount * guesstimate)) + ' <br><img src="cid:image2"><br>Sent from ' + sys.argv[0] + ' on ' + socket.gethostname(), 'html')
        msgAlternative.attach(msgText)

        # This example assumes the image is in the current directory
        fp = open(tmpfile, 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        fp = open(lastweekfile, 'rb')
        msgImage2 = MIMEImage(fp.read())
        fp.close()
        msgImage2.add_header('Content-ID', '<image2>')
        msgRoot.attach(msgImage2)
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)
        smtp = smtplib.SMTP()
        smtp.connect('mailhost')
        #smtp.login('exampleuser', 'examplepass')
        smtp.sendmail(strFrom, strTo, msgRoot.as_string())
        smtp.quit()
    else:
        print workdate + " " + str(int(count))
        
    
