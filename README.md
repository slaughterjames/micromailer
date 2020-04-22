# micromailer
VERY lightweight Python-based e-mail dispatcher

Usage: [required] --recipients OR --recipientsfile --subject --body OR --bodyfile [optional] --attachments --debug --help
Example: /opt/integ/micromailer.py --recipients user@work.com --body 'Hello World!' --attachments file.txt --debug
Required Arguments:
--recipients OR --recipientsfile - one or more email addresses enclosed in ' '.
--subject - e-mail subect enclosed in ' '.
--body OR --bodyfile - e-mail body text enclosed in ' '.
Optional Arguments:
--attachments - One or more attachment file names enclosed in ' '.
--debug - Prints verbose logging to the screen to troubleshoot issues.  Recommend piping (>>) to a text file due to the amount of text...
--help - You're looking at it!
