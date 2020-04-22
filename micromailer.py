#!/usr/bin/python
'''
micromailer v0.1 - Copyright 2020 James Slaughter,
This file is part of micromailer v0.1.

micromailer v0.1 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

micromailer v0.1 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with micromailer v0.1.  If not, see <http://www.gnu.org/licenses/>.
'''

#python import
import sys
import os
import subprocess
import re
import json
import simplejson
import datetime
import time
import smtplib
import hashlib
import urllib2
import csv
from collections import defaultdict
from datetime import date
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from array import *
from termcolor import colored

#programmer generated imports
from controller import controller
from fileio import fileio

'''
Usage()
Function: Display the usage parameters when called
'''
def Usage():
    print 'Usage: [required] --recipients OR --recipientsfile --subject --body OR --bodyfile [optional] --attachments --debug --help'
    print 'Example: /opt/integ/micromailer.py --recipients user@work.com --body \'Hello World!\' --attachments file.txt --debug'
    print 'Required Arguments:'
    print '--recipients OR --recipientsfile - one or more email addresses enclosed in \' \'.'
    print '--subject - e-mail subect enclosed in \' \'.'
    print '--body OR --bodyfile - e-mail body text enclosed in \' \'.'
    print 'Optional Arguments:'
    print '--attachments - One or more attachment file names enclosed in \' \'.'
    print '--debug - Prints verbose logging to the screen to troubleshoot issues.  Recommend piping (>>) to a text file due to the amount of text...'
    print '--help - You\'re looking at it!'
    sys.exit(-1)

'''
ConfRead()
Function: - Reads in the integ.conf config file and assigns some of the important
            variables
'''
def ConfRead():
        
    ret = 0
    intLen = 0
    FConf = fileio()
    FLOG = fileio()
    data = ''
    emailalerting = ''
    emailpassthrough = ''

    try:
        #Conf file hardcoded here
        with open('/opt/micromailer/micromailer.conf', 'r') as read_file:
            data = json.load(read_file)
    except:
        print '[x] Unable to read configuration file!  Terminating...'
        FLOG.WriteLogFile(CON.logfile, '[x] Unable to read configuration file!  Terminating...\n')
        return -1
    
    CON.logfile = data['logfile']
    CON.server = data['server']
    CON.serverport = data['server_port']
    emailpassthrough = data['emailpassthrough']
    if (emailpassthrough == 'True'):
        CON.emailpassthrough = True
    CON.email = data['email']
    CON.password = data['password']
  
    if (CON.debug == True):
        print '[DEBUG] data: ', data
        print '[DEBUG] CON.logfile: ' + str(CON.logfile)
        print '[DEBUG] CON.server: ' + str(CON.server)
        print '[DEBUG] CON.serverport: ' + str(CON.serverport)
        print '[DEBUG] CON.emailpassthrough: ' + str(CON.emailpassthrough)
        print '[DEBUG] CON.email: ' + str(CON.email)
        print '[DEBUG] CON.password: ' + str(CON.password)

        if (CON.emailpassthrough == False): 
            if (len(CON.password) < 3):
                print '[x] Please enter a valid sender e-mail password in the micromailer.conf file.  Terminating...'
                FLOG.WriteLogFile(CON.logfile, '[x] Please enter a valid sender e-mail password in the micromailer.conf file.  Terminating...\n')            
                print ''
                return -1
        else:
            print '[*] E-mail passthrough is active, ignoring password...'
            FLOG.WriteLogFile(CON.logfile, '[*] E-mail passthrough is active, ignoring password...\n')    
         
    print '[*] Finished configuration successfully.\n'
    FLOG.WriteLogFile(CON.logfile, '[*] Finished configuration successfully.\n')
            
    return 0

'''
Parse() - Parses program arguments
'''
def Parse(args):        
    option = ''
                    
    print '[*] Arguments: \n'
    for i in range(len(args)):
        if args[i].startswith('--'):
            option = args[i][2:]           

            if option == 'help':
                return -1  

            if option == 'debug':
                CON.debug = True
                print option + ': ' + str(CON.debug)

            if option == 'recipients':
                CON.recipients = args[i+1].split()
                for recp_out in CON.recipients:
                    print option + ': ' + recp_out + '\n'
                print ''

            if option == 'recipientsfile':
                CON.recipients_file = args[i+1]
                print option + ': ' + CON.recipients_file + '\n'

            if option == 'subject':
                CON.email_subject = args[i+1]
                print option + ': ' + CON.email_subject + '\n'

            if option == 'body':
                CON.body = args[i+1]
                print option + ': ' + CON.body + '\n'

            if option == 'bodyfile':
                CON.body_file = args[i+1]
                print option + ': ' + CON.body_file + '\n'

            if option == 'attachments':
                CON.attachments = args[i+1].split()
                for attc_out in CON.attachments:
                    print option + ': ' + attc_out + '\n'
                print '' 

                                       
    #These are required params so length needs to be checked after all 
    #are read through               
    
    if ((len(CON.recipients) < 1) and (len(CON.recipients_file) < 1)):
        print colored('[x] recipients OR recipientsfile are required arguments.', 'red', attrs=['bold'])
        print ''
        return -1 

    if ((len(CON.recipients) > 1) and (len(CON.recipients_file) > 1)):
        print colored('[x] recipients AND recipientsfile may not be used concurrently.', 'red', attrs=['bold'])
        print ''
        return -1 

    if len(CON.email_subject) < 1:
        print colored('[x] subject is a required argument.', 'red', attrs=['bold'])
        print ''
        return -1 

    if ((len(CON.body) < 1) and (len(CON.body_file) < 1)):
        print colored('[x] body OR bodyfile are required arguments.', 'red', attrs=['bold'])
        print ''
        return -1 

    if ((len(CON.body) > 1) and (len(CON.body_file) > 1)):
        print colored('[x] body AND bodyfile may not be used concurrently.', 'red', attrs=['bold'])
        print ''
        return -1 

    return 0

'''
send_email()
Function: - Sends the alert e-mail from the address specified
            in the configuration file to potentially several addresses
            specified in the "recipients.txt" file or the --recipients flag.
'''
def send_email():

    base_filename = ''
    FLOG = fileio()

    for recipient_entry in CON.recipients:
        
        print '\r\n[-] Sending e-mail to: ' + recipient_entry.strip()
        FLOG.WriteLogFile(CON.logfile, '[-] Sending e-mail to: ' + recipient_entry.strip() + '\n')

        # Build the email message
        msg = MIMEMultipart()
        msg['Subject'] = CON.email_subject.strip()
        msg['From']    = CON.email.strip()
        msg['To']      = recipient_entry
        msg.attach(MIMEText(CON.body))

        if (len(CON.attachments) >= 1):
            for attachment_entry in CON.attachments:

                if (CON.debug == True):        
                    print '\n[DEBUG] attachment_entry: ' + attachment_entry
                    FLOG.WriteLogFile(CON.logfile, '[DEBUG] attachment_entry: ' + attachment_entry + '\n')

                base_filename = os.path.basename(attachment_entry)
                if (CON.debug == True):        
                    print '\n[DEBUG] base_filename: ' + base_filename
                    FLOG.WriteLogFile(CON.logfile, '[DEBUG] base_filename: ' + base_filename + '\n')

                part = MIMEBase('application', "octet-stream")
                part.set_payload(open(attachment_entry, "rb").read())
                Encoders.encode_base64(part)

                part.add_header('Content-Disposition', 'attachment; filename=' + base_filename)

                msg.attach(part)
                print '[-] Added attachment: ' +  attachment_entry  + '\n'
                FLOG.WriteLogFile(CON.logfile, '[-] Added attachment: ' +  attachment_entry + '\n')
    
        server = smtplib.SMTP(CON.server,int(CON.serverport))

        if (CON.emailpassthrough == False):
            server.ehlo()
            server.starttls()
            server.login(CON.email.strip(),CON.password.strip())

        server.sendmail(recipient_entry,recipient_entry,msg.as_string())
        server.quit()
    
        print '[*] E-mail sent!\n'
        FLOG.WriteLogFile(CON.logfile, '[*] E-mail sent!\n')  
    
    return 0

'''
Terminate()
Function: - Attempts to exit the program cleanly when called  
'''     
def Terminate(exitcode):
    sys.exit(exitcode)

'''
Execute()
Function: - Does the doing
'''
def Execute():

    FI = fileio() 

    #Do we have body text from the command line or a read-in file?
    if ((len(CON.body) < 1) and (len(CON.body_file) >= 1)):
        FI.ReadFile(CON.body_file)
        for bodyline in FI.fileobject:
            CON.body +=bodyline

    #Do we have a recipients list from the command line or a read-in file?
    if ((len(CON.recipients) < 1) and (len(CON.recipients_file) >= 1)):
        FI.ReadFile(CON.recipients_file)
        for recipline in FI.fileobject:
            CON.recipients.append(recipline)

    #Launch the main function
    send_email()
       
    return 0

'''
This is the mainline section of the program and makes calls to the 
various other sections of the code
'''
if __name__ == '__main__':

    ret = 0 
    count = 0  

    CON = controller()
    FLOG = fileio() 

    ret = Parse(sys.argv)
    if (ret == -1):
        Usage()
        Terminate(ret) 

    ret = ConfRead()    
    if (ret == -1):
        print '[x] Terminated reading the configuration file...'
        Terminate(ret)  

    print '\n[*] Begining run: ' + str(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")) + '\n'
    FLOG.WriteLogFile(CON.logfile.strip(), '[*] Begining run: ' + str(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")) + '\n')
    print '\n[*] Executing micromailer.py v0.1...'
    FLOG.WriteLogFile(CON.logfile.strip(), '[*] Executing micromailer.py v0.1...\n')

    Execute()

    print '\n[*] Program Complete: ' + str(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")) + '\n'
    FLOG.WriteLogFile(CON.logfile, '[*] Program Complete: ' + str(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")) + '\n')
    FLOG.WriteLogFile(CON.logfile, '*******************************************************************************************\n')

    Terminate(ret)

'''
END OF LINE
'''
