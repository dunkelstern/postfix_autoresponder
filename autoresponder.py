#!/usr/bin/env python
# -*- coding: utf-8 -*-

from opts import Parser, Command, Option, IntOption
from pwd import getpwnam
from grp import getgrnam
import ConfigParser, os, sys, datetime

parser = Parser(description=u"Mail autoresponse tool for postfix", commands={
    "create": Command(
        short_description=u"Create new autoresponder",
        options={
            "user": Option("u", "user",
                short_description=u"The mail user to create the responder for"),
            "interval": IntOption("i", "interval",
                short_description=u"The repeat interval (in seconds) for sending the same sender the autoresponse again",
                default=86400),
            "subject": Option("s", "subject",
                short_description=u"Subject line of the auto response mail",
                default="Out of office response"),
            "fromDate": Option("f", "from-date",
                short_description=u"Activity window of the responder (start date, inclusive, \"yyyy-mm-dd'T'hh:mm:ss\")",
                default=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
            "toDate": Option("t", "to-date",
                short_description=u"Activity window of the responder (end date, inclusive, \"yyyy-mm-dd'T'hh:mm:ss\")",
                default="9999-12-31T23:59:59"),
            "configFile": Option("c", "config",
                short_description=u"Config file to read, defaults to '/etc/autoresponder.conf'",
                default="/etc/autoresponder.conf")
        },
    ),
    "remove": Command(
        short_description=u"Remove an autoresponder",
        options={
            "user": Option("u", "user",
                short_description=u"The mail user to remove the responder from"),
            "configFile": Option("c", "config",
                short_description=u"Config file to read, defaults to '/etc/autoresponder.conf'",
                default="/etc/autoresponder.conf")
        },
    ),
    "show": Command(
        short_description=u"Show currently set autoresponders",
        options={
            "user": Option("u", "user",
                short_description=u"The mail user to show"),
            "configFile": Option("c", "config",
                short_description=u"Config file to read, defaults to '/etc/autoresponder.conf'",
                default="/etc/autoresponder.conf")
        },
    ),
    "enable": Command(
        short_description=u"Enable set autoresponders",
        options={
            "user": Option("u", "user",
                short_description=u"The user to enable the responder for"),
            "configFile": Option("c", "config",
                short_description=u"Config file to read, defaults to '/etc/autoresponder.conf'",
                default="/etc/autoresponder.conf")
        },
    ),
    "disable": Command(
        short_description=u"Disable set autoresponders",
        options={
            "user": Option("u", "user",
                short_description=u"The user to disable the responder for"),
            "configFile": Option("c", "config",
                short_description=u"Config file to read, defaults to '/etc/autoresponder.conf'",
                default="/etc/autoresponder.conf")
        },
    )
})

# parse command line
settings, arguments = parser.evaluate()
if (len(settings.keys()) == 0):
    parser.evaluate(["help"])

# open config file
configFile = settings[settings.keys()[0]][0]["configFile"]
config = ConfigParser.SafeConfigParser()
config.read(configFile)
try:
    workingDir = config.get("spool", "directory")
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    print "No spool directory set in config file"
    exit(1)

try:
    userID = config.get("spool", "uid")
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    print "No user id set in config file"
    exit(1)

try:
    groupID = config.get("spool", "gid")
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    print "No group id set in config file"
    exit(1)


# user name
try:
    userName = settings[settings.keys()[0]][0]["user"]
except KeyError:
    print "You have to define a user by using -u or --user"
    exit(1)

responderFile = workingDir + "/" + userName + ".conf"

# create responder
if 'create' in settings:
    if os.path.isfile(responderFile):
        print "Error, autoresponder for user already set, remove it first!"
        exit(1)
    responder = ConfigParser.SafeConfigParser()
    responder.add_section("settings")
    responder.set("settings", "interval", str(settings['create'][0]['interval']))
    responder.set("settings", "fromDate", settings['create'][0]['fromDate'])
    responder.set("settings", "toDate", settings['create'][0]['toDate'])
    responder.set("settings", "enabled", "0")
    responder.add_section("mail")
    responder.set("mail", "subject", str(settings['create'][0]['subject']))

    print "Write the text for the mail (end with ^D or a single . in a line)"
    mailText = ""
    run = True
    while run:
        line = sys.stdin.readline().rstrip("\n")
        if line == ".":
            run = False
        else:
            mailText += line + "\\n"
    responder.set("mail", "text", mailText)

    with open(responderFile, 'wb') as configfile:
        responder.write(configfile)
    os.chown(responderFile, getpwnam(userID).pw_uid, getgrnam(groupID).gr_gid)
    print "Autoresponder set but currently disabled"
    exit(0)

# remove responder
if 'remove' in settings:
    if not os.path.isfile(responderFile):
        print "Error, autoresponder for user not set."
        exit(1)
    else:
        os.remove(responderFile)
        print "Autoresponder removed"
        exit(0)

# show responder
if 'show' in settings:
    if not os.path.isfile(responderFile):
        print "Error, no autoresponder set for user."
    else:
        responder = ConfigParser.SafeConfigParser()
        responder.read(responderFile)
        print "Autoresponder for user: " + userName
        print "------------------------------------------------------"
        print "Enabled           : " + responder.get("settings", "enabled")
        print "Reminder interval : " + responder.get("settings", "interval") + "sec"
        print "Active from       : " + responder.get("settings", "fromdate")
        print "Active to         : " + responder.get("settings", "todate")
        print "Subject           : " + responder.get("mail", "subject")
        print "------------------------------------------------------"
        print responder.get("mail", "text").replace("\\n", "\n")

# enable responder
if 'enable' in settings:
    if not os.path.isfile(responderFile):
        print "Error, no autoresponder set for user."
    else:
        responder = ConfigParser.SafeConfigParser()
        responder.read(responderFile)
        responder.set("settings", "enabled", "1")
        with open(responderFile, 'wb') as configfile:
            responder.write(configfile)
        os.chown(responderFile, getpwnam(userID).pw_uid, getgrnam(groupID).gr_gid)
        print "Autoresponder enabled"

# disable responder
if 'disable' in settings:
    if not os.path.isfile(responderFile):
        print "Error, no autoresponder set for user."
    else:
        responder = ConfigParser.SafeConfigParser()
        responder.read(responderFile)
        responder.set("settings", "enabled", "0")
        with open(responderFile, 'wb') as configfile:
            responder.write(configfile)
        os.chown(responderFile, getpwnam(userID).pw_uid, getgrnam(groupID).gr_gid)
        print "Autoresponder disabled"
