#!/bin/bash

# slapcat|grep -v  "structuralObjectClass|entryUUID|creatorsName|createTimestamp|modifiersName|modifyTimestamp|entryCSN" > export

if [ $# -ne 1 ]; then
	echo "usage: $0 /etc/.ldap_setup"
	exit 0
fi

setup_successful=$1
rc=0

if [ -f $setup_successful ]; then
	logger "LDAP already set up, $0 exiting"
	exit 0
fi

rootpass=`openssl rand -base64 16`
hashpass=`slappasswd -s $rootpass`
uniqueid=`/sbin/ip a | grep inet | grep -v 127.0.0.1  | grep -v inet6 | awk '{print $2}' | awk -F/ '{print $1}' | awk -F. '{print $4}'`

echo "ROOTPASS: $rootpass" >> /var/tmp/ldap.log
echo "HASHPASS: $hashpass" >> /var/tmp/ldap.log

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: olcDatabase={0}config,cn=config
changetype: modify
add: olcRootPW
olcRootPW: $hashpass
EOF

rc=`expr $rc + $?`

for standardfile in /etc/openldap/schema/cosine.ldif /etc/openldap/schema/nis.ldif /etc/openldap/schema/inetorgperson.ldif /etc/openldap/schema/ppolicy.ldif; do
	echo "LDAP ADD $standardfile"
	ldapadd -Y EXTERNAL -H ldapi:/// -f $standardfile
	rc=`expr $rc + $?`
done

echo "LONG LDAPMODIFY:"
echo
ldapmodify -Y EXTERNAL -H ldapi:/// <<EOF
dn: olcDatabase={1}monitor,cn=config
changetype: modify
replace: olcAccess
olcAccess: {0}to * by dn.base="gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth"
  read by dn.base="cn=Manager,dc=example,dc=org" read by * none

dn: olcDatabase={2}hdb,cn=config
changetype: modify
replace: olcSuffix
olcSuffix: dc=example,dc=org

dn: olcDatabase={2}hdb,cn=config
changetype: modify
replace: olcRootDN
olcRootDN: cn=Manager,dc=example,dc=org

dn: olcDatabase={2}hdb,cn=config
changetype: modify
add: olcRootPW
olcRootPW: $hashpass

dn: olcDatabase={2}hdb,cn=config
changetype: modify
add: olcAccess
olcAccess: {0}to attrs=userPassword,shadowLastChange by
  dn="cn=Manager,dc=example,dc=org" write by anonymous auth by self write by set="[cn=sysadmins,ou=groups,dc=example,dc=org]/memberUid & user/uid" write by * none
olcAccess: {1}to dn.base="" by * read
olcAccess: {2}to * by dn="cn=Manager,dc=example,dc=org" write by * read
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=module,cn=config
objectClass: olcModuleList
cn: module
olcModulePath: /usr/lib64/openldap
olcModuleLoad: memberof
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: olcOverlay=memberof,olcDatabase={2}hdb,cn=config
objectClass: olcMemberOf
objectClass: olcOverlayConfig
objectClass: olcConfig
objectClass: top
olcOverlay: memberof
olcMemberOfDangling: ignore
olcMemberOfRefInt: TRUE
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=module,cn=config
objectClass: olcModuleList
cn: module
olcModulePath: /usr/lib64/openldap
olcModuleLoad: syncprov.la
EOF

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=module,cn=config
objectClass: olcModuleList
cn: module
olcModulePath: /usr/lib64/openldap
olcModuleLoad: ppolicy.la
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: olcOverlay=ppolicy,olcDatabase={2}hdb,cn=config
objectClass: olcPPolicyConfig
olcOverlay: ppolicy
olcPPolicyDefault: cn=ppolicy,ou=policies,dc=example,dc=org
olcPPolicyUseLockout: TRUE
olcPPolicyHashCleartext: TRUE
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=config
changetype: modify
replace: olcServerID
# specify uniq ID number on each server
olcServerID: $uniqueid
EOF

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=config
changetype: modify
replace: olcTLSCACertificatePath
olcTLSCACertificatePath: /etc/openldap/cacerts
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=config
changetype: modify
replace: olcTLSCertificateFile
olcTLSCertificateFile: /etc/openldap/certs/ldap.cert.pem
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=config
changetype: modify
replace: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/openldap/certs/ldap.key.pem
EOF
rc=`expr $rc + $?`

ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: olcOverlay=syncprov,olcDatabase={2}hdb,cn=config
changetype: add
objectClass: olcOverlayConfig
objectClass: olcSyncProvConfig
olcOverlay: syncprov
EOF
rc=`expr $rc + $?`

echo '
dn: olcDatabase={2}hdb,cn=config
changetype: modify
add: olcSyncRepl
olcSyncRepl: rid=001
  provider=ldaps://ldaphost1.example.org
  bindmethod=simple
  binddn="cn=Manager,dc=example,dc=org"
  credentials=password
  tls_cacert=/etc/openldap/cacerts/ca-chain.cert.pem
  tls_cert=/etc/openldap/certs/ldap.cert.pem
  tls_key=/etc/openldap/certs/ldap.key.pem
  searchbase="dc=example,dc=org"
  scope=sub
  schemachecking=on
  type=refreshAndPersist
  retry="30 5 300 3"
  interval=00:00:05:00
'

echo '
dn: olcDatabase={2}hdb,cn=config
changetype: modify
add: olcMirrorMode
olcMirrorMode: TRUE
'

echo "encountered $rc errors"

touch $setup_successful
