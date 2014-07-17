# Postfix Autoresponder

Python script for automatic "Out of Office" autoresponders in Postfix

# Installation

Copy the `default.conf` to `/etc/autoresponder.conf` and set up the right paths and uid/gid for your mail system.

Copy `autoresponder.py` and `autoresponder_filter.py` to your path (for example: `/usr/local/bin`) and make them executable.

Install required packages:

    # pip install -r requirements.txt

Default config:

    [spool]
    directory=/var/mail/autoresponder
    uid=vmail
    gid=vmail
    
    [sendmail]
    executable=/usr/bin/sendmail 
    arguments=-i -f %(sender)s %(recipient)s

spool/directory -> the directory to store the autoresponders to  
spool/uid -> uid of your mail user  
spool/gif -> gid of your mail user  

sendmail/executable -> full path to your sendmail executable  
sendmail/arguments -> arguments to give sendmail, `%(sender)s` expands to sender's e-mail `%(recipient)s` expands to recipient e-mail address.

The spool/directory has to be writable by the mailserver group, everyone that should be able to set autoresponders has to be in that group (or root has to do it).

In `/etc/postfix/master.cf` extend the line

    smtp      inet  n       -       -       -       -       smtpd

by adding the following in the next line (make sure the line starts with, at least one, whitespace):

      -o content_filter=autoresponder:dummy

and add this line to the end of the file:

    autoresponder unix -    n       n       -       -       pipe
      flags=Fq user=vmail argv=/usr/local/bin/autoresponder_filter.py -s ${sender} -r ${recipient} -S ${sasl_username} -i ${client_address}

# Usage

To set up an autoresponder call the `autoresponder.py` script:

    # autoresponder.py create -u <some mail user> -s "<subject>"
    Write the text for the mail (end with ^D or a single . in a line)
    <your text>
    .

After setting the responder up it has to be enabled next:

    # autoresponder.py enable -u <some mail user>

Now if the user gets an e-mail the autoresponder is sent automatically, per default the script will send an auto response only for the first mail received from that sender once a day. Use the `help` command to get more information about other settings you may access.

# Help dump

## Available commands

    usage: /usr/local/bin/autoresponder.py [commands]
    
    Mail autoresponse tool for postfix
    
    Commands:
     create     Create new autoresponder
     remove     Remove an autoresponder
     show       Show currently set autoresponders
     enable     Enable set autoresponders
     disable    Disable set autoresponders
     help       Shows this message.

## Create command

    usage: /usr/local/bin/autoresponder.py create [options]
    
    Create new autoresponder
    
    Commands:
     help       Shows this message.
    
    Options:
     -u --user      The mail user to create the responder for
     -i --interval  The repeat interval (in seconds) for sending the same sender the autoresponse again
     -s --subject   Subject line of the auto response mail
     -f --from-date Activity window of the responder (start date, inclusive, "yyyy-mm-dd'T'hh:mm:ss")
     -t --to-date   Activity window of the responder (end date, inclusive, "yyyy-mm-dd'T'hh:mm:ss")
     -c --config    Config file to read, defaults to '/etc/autoresponder.conf'

## Other commands

    usage: /usr/local/bin/autoresponder <command> [options]
    
    Commands:
     help       Shows this message.
    
    Options:
     -u --user   Mail user to work on
     -c --config Config file to read, defaults to '/etc/autoresponder.conf'
