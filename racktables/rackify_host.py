#!/usr/bin/python
#
# this script accepts a hostname and optional nic, and allocates a free IP from racktables to be assigned to the host
# and creates a host entry in the DB. It assumes that eth0 indicates a VM, and any other interace is a physical host
#
import socket, struct
import _mysql
import MySQLdb
import sys
import argparse

VM_OBJTYPE = 1504
HW_OBJTYPE = 4
VM_NIC = 'eth0'

# function to convert IP address to decimal
def ip2long(ip):
  packedIP = socket.inet_aton(ip)
  return struct.unpack("!L", packedIP)[0]

def long2ip(n):
    d = 256 * 256 * 256
    q = []
    while d > 0:
        m,n = divmod(n,d)
        q.append(str(m))
        d = d/256

    return '.'.join(q)

if __name__ == "__main__":
  # parse arguments
  parser = argparse.ArgumentParser()
  parser.add_argument('host', help='host to create/update')
  parser.add_argument('ip', help='desired IP range, for example 10.90.128.11')
  parser.add_argument('--nic', help='nic to associate IP with - defaults to ' + VM_NIC)
  args = parser.parse_args()

  # read args to pretty vars
  ip = args.ip
  hostname = args.host
  if args.nic:
    interface = args.nic
  else:
    interface = VM_NIC

  # convert desired IP to decimal
  int_ip = ip2long(ip)

  # DB settings
  db_user     = 'someuser' # read from some secure file or config service
  db_password = 'somepass' # read from some secure file or config service
  last_octet = ip.split('.')
  # check for reserved IPs here ^
  
  # create host object if not already there
  conn = MySQLdb.connect(host= "localhost", \
                  user = db_user, \
                  passwd = db_password, \
                  db="racktables_db") 
  x = conn.cursor()

  # VMs are object type 4, physical servers are object type 4
  if interface == VM_NIC:
    objtype_id = VM_OBJTYPE
  else:
    objtype_id = HW_OBJTYPE

  # get host object ID (either existing or new)
  x.execute("""SELECT id from Object where name = '""" + hostname + """';""")
  try:
    for item in x.fetchone():
      host_id = item
    state = "updated host"

  # host not found in DB, create one
  except:
    x.execute("""INSERT INTO Object (name,objtype_id) values ('""" + hostname + """ ',""" + str(objtype_id)  + """);""" )
    conn.commit()
    x.execute("""SELECT id from Object where name = '""" + hostname + """';""")
    try:
      for item in x.fetchone():
        host_id = item
      state = "new host"

    # cant create object, DB must be down
    except: 
      print "unable to find/create object in db"
      sys.exit(0)

  # found object ID
  #print "object ID is: " + str(host_id)
  #print "your IP is: " + str(int_ip)

  # scan IP's in use for the next available one
  x.execute("""SELECT ip from IPv4Allocation where ip > """ + str(int_ip) + """;""")
  try:
    final_ip = 0
    ip = x.fetchone()
    previous_ip = int_ip
    while ip is not None and final_ip == 0:
      ip = x.fetchone()

      # compare gap between current IP and previous one - if gap > 1, there are free IP's! yay!
      gap = ip[0] - previous_ip
      if gap > 1:
        if previous_ip == int_ip:
          final_ip = previous_ip
        else:
          final_ip = previous_ip + 1
      previous_ip = ip[0]
    #x.close()
  except:
    print "IP range seems invalid"
    sys.exit(0)

  try:
    x.execute("""INSERT INTO IPv4Allocation (object_id,ip,name,type) values (""" + str(host_id) + """,""" + str(final_ip) + """,'""" + interface + """','regular');""" )
    conn.commit()
  except:
    print "db update failed"
    sys.exit(0)

  # print output to demonstrate your work
  print "host id    : " + str(host_id) 
  print "decimal IP : " + str(final_ip)
  print "state      : " + state
  print
  print "host       : " + hostname 
  print "IP         : " + str(long2ip(final_ip))
  print "interface  : " + interface
