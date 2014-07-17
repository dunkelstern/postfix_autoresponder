#!/usr/bin/env python
# -*- coding: utf-8 -*-

from opts import Parser, Option
import ConfigParser, os, sys, datetime, subprocess

parser = Parser(description=u"Mail autoresponse filter for postfix", options={
    "sender": Option("s", "sender",
        short_description=u"Sender of the mail"),
    "user": Option("r", "recipient",
        short_description=u"Recipient of the mail"),
    "sasl": Option("S", "sasl-username",
        short_description=u"SASL username"),
    "clientIP": Option("i", "client-ip",
        short_description=u"Client IP address (optional))"),
    "configFile": Option("c", "config",
        short_description=u"Config file to read (default '/etc/autoresponder.conf')",
        default="/etc/autoresponder.conf")
})

# parse command line
settings, arguments = parser.evaluate()
if (len(settings.keys()) == 0):
    parser.evaluate(["help"])

# user name
try:
    userName = settings["user"]
except KeyError:
    print "You have to define a user by using -r or --recipient"
    exit(1)

# open config file
configFile = settings["configFile"]
config = ConfigParser.SafeConfigParser()
config.read(configFile)
try:
    workingDir = config.get("spool", "directory")
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    print "No spool directory set in config file"
    exit(1)

# if the user has an autoresponder set read the config
responderFile = workingDir + "/" + userName + ".conf"
if os.path.isfile(responderFile):
    responder = ConfigParser.SafeConfigParser()
    responder.read(responderFile)

    # check if the responder is enabled
    if responder.get("settings", "enabled") == "1":
        # check if the responder should be active today
        now      = datetime.datetime.now();
        fromDate = datetime.datetime.strptime(responder.get("settings", "fromdate"), "%Y-%m-%dT%H:%M:%S")
        toDate   = datetime.datetime.strptime(responder.get("settings", "todate"), "%Y-%m-%dT%H:%M:%S")
        if now > fromDate and now < toDate:             
            # check if the timeout has been reached
            try:
                timeout = datetime.datetime.strptime(responder.get("timeouts", settings["sender"]), "%Y-%m-%dT%H:%M:%S")
            except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
                try:
                    responder.add_section("timeouts")
                except ConfigParser.DuplicateSectionError:
                    pass
                timeout = datetime.datetime.now() + datetime.timedelta(seconds=-100)

            # ok timeout reached, send mail
            if (timeout < datetime.datetime.now()):
                mailText =  "From: " + userName + "\r\n"
                mailText += "To: " + settings["sender"] + "\r\n"
                mailText += "Date: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\r\n"        
                mailText += "Subject: " + responder.get("mail", "subject") + "\r\n"
                mailText += "\r\n"
                mailText += responder.get("mail", "text").replace("\\n", "\r\n")        

                command = [ config.get("sendmail", "executable") ]
                command.extend(config.get("sendmail", "arguments", 0,
                    { 'recipient' : settings["sender"],
                      'sender' : settings["user"]}).split(" "))
                mail = subprocess.Popen(command, stdin=subprocess.PIPE)
                mail.stdin.write(mailText)

                # save new timeout
                newTimeout = datetime.datetime.now() + datetime.timedelta(seconds=int(responder.get("settings", "interval")))
                responder.set("timeouts", settings["sender"], newTimeout.strftime("%Y-%m-%dT%H:%M:%S"))
                with open(responderFile, 'wb') as configfile:
                    responder.write(configfile)

# re-send the mail
command = [ config.get("sendmail", "executable") ]
command.extend(config.get("sendmail", "arguments", 0,
    { 'recipient' : settings["user"],
      'sender' : settings["sender"]}).split(" "))
mail = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
