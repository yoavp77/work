#!/usr/bin/env python
# 

import sys
import os
import datetime

Domain = 'example.com'
EmailDomain = 'example.com' # if your mail domain is different this will becom user@abc.com 
ConnectDC = 'ldap://localhost:389'
# if 14 days remains to expire password then it will send email to that user 
# until user update the new password
PwdWarnDays = 7
pwdMaxAge = 90 # default password expire in 45 days as per ldap ppolicy  

def GetUserDetails():
        """ This Function Will save all details in file
        it will use ldap search query for the same."""
        # Create bind dn eg. dc=example,dc=com
        BindDN = ','.join([ 'dc=' + d for d in Domain.split('.') ])
        #
        import ldap 
        l = ldap.initialize(ConnectDC)
        # Perform Ldap Search
        return  l.search_s(
                BindDN,
                ldap.SCOPE_SUBTREE,
                '(mail=*)',['mail','pwdChangedTime','uid']
            )

def MailOut(email,expiration,uid):
	# Import smtplib for the actual sending function
	import smtplib
	# Import the email modules we'll need
	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText
	msg = MIMEMultipart('alternative')
	relay = ""
	msg['Subject'] = "example Password Expiration - " + str(expiration) + " Days"
	msg['From'] = "example Ops <opsteam@example.com>"
	msg['To'] = email
	text = "Your password for the example user directory (LDAP) will expire in " + str(expiration) + "  days. This is the password that is used to log in to internal example systems such as GitHub, HipChat, etc.\nYour username is " + uid + " and you can reset your password at https://password.examplews.com/change or reach out to example Ops (opsteam@example.com) for questions.\nPasswords expire every 90 days and have complexity requirements - read more about it at https://github.examplews.com/example/example/wiki/Passwords "
	html = """\
<html> \
  <head></head> \
  <body> \
<p>Your password for the example user directory (LDAP) will expire  in """ + str(expiration) + """ days. This is the password that is used to log in to internal example systems such as <a href="http://github.examplews.com">GitHub</a>, <a href="hipchat.examplews.com">HipChat</a>, etc. <br><br>Your username is """ + uid + """ and you can reset your password at <a href="https://password.examplews.com/change">https://password.examplews.com/change</a> or reach out to <a href="mailto:opsteam@example.com?Subject=Password%20Reset">example Ops</a> for questions. <br><br>Passwords expire every 90 days and have certain complexity requirements - read more about it <a href="https://github.examplews.com/example/example/wiki/Passwords">here</a> \
    </p> \
  </body> \
</html> \
""" 
	part1 = MIMEText(text, 'plain')
	part2 = MIMEText(html, 'html')
	msg.attach(part1)
	msg.attach(part2)
        
        # special relay server for specialgroup.com emails
	if "thespecialgroup.com" in email:
		relay = "mail.specialrelay.net."
	else:
		relay = "localhost"
	s = smtplib.SMTP(relay)
	s.sendmail("sysadmins@example.com", email, msg.as_string())
	s.quit
	#print email + " " + str(expiration)

def CheckExpiry():
         """ 
         This Function will Check each user ExpiryWarning
         if it more thans WarningDays then it will send Emails
         to that particuler user
         """
         for k,v in Users:
                    mail = ''.join(v['mail'])
                    if 'pwdChangedTime' not in v:
                            pass
                    try:
                          l = ''.join(v['pwdChangedTime'])
                    except:
                            pass

                    if 'pwdChangedTime' in v:
                        # To extrace year month day
                        d1 = datetime.date.today()
                        d2 = datetime.date(int(l[0:4]),int(l[4:6]),int(l[6:8]))
                        DaysOfPasswordChange = (d1 - d2).days
                        d2 = d2.strftime('%d, %b %Y')

                        ExpireIn = pwdMaxAge - DaysOfPasswordChange

                        # if password not changed before X days 
                        if ExpireIn <= PwdWarnDays:
                            #print mail + ' ' + str(ExpireIn) + ' ' + ''.join(v['uid'])
                            MailOut(mail,str(ExpireIn),''.join(v['uid']))

if __name__ == '__main__':
	Users = GetUserDetails()
	CheckExpiry()
