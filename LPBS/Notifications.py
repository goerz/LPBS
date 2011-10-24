# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2011 by Michael Goerz                                   #
#    http://michaelgoerz.net                                               #
#                                                                          #
#    This program is free software; you can redistribute it and/or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 3 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

import shlex
import email
import smtplib
import subprocess
import os
from Config import full_expand

""" Notifications and Logging """

JOB_MESSAGE_ID = {}

def notify(subject, job_id, message, options, category=''):
    """ Send notification
    """
    if options.config.getboolean("Notification", 'local_growl'):
        notify_local_growl(subject, job_id, message, options)
    if options.config.getboolean("Notification", 'send_mail'):
        if category in options.mail_options:
            for entry in options.email_addresses:
                for address in entry.split(","):
                    notify_email(address.strip(), subject, job_id, message,
                                 options)


def notify_local_growl(subject, job_id, message, options):
    sticky = ''
    if options.config.getboolean("Growl", 'sticky'): sticky = '-s'
    p = subprocess.Popen([options.config.get("Growl", 'growlnotify'),
                          '-t', "LPBS: %s" % subject, sticky], 
                          stdin=subprocess.PIPE).stdin
    p.write(message)
    p.close()


def notify_email(recipient, subject, job_id, message, options):

    msg = email.Message.Message()
    fromaddr = options.config.get("Mail", 'from')
    smpt_server = options.config.get("Mail", 'smtp')

    message_id = email.utils.make_msgid('lpbs')
    msg.add_header("Subject", "LPBS JOB %s" % job_id)
    msg.add_header("Message-Id", message_id)
    msg.add_header("From", fromaddr)
    msg.add_header("To", recipient)
    if (JOB_MESSAGE_ID.has_key(job_id)):
        msg.add_header("In-Reply-To:", JOB_MESSAGE_ID[job_id])
        msg.add_header("References:", JOB_MESSAGE_ID[job_id])
    msg.set_charset("UTF-8")
    msg.set_payload(message, charset="UTF-8")

    server = smtplib.SMTP(smpt_server)
    if (options.config.getboolean("Mail", 'tls')):
        server.starttls()
    if (options.config.getboolean("Mail", 'authenticate')):
        username = options.config.get('Mail', 'username')
        password = options.config.get('Mail', 'password')
        server.login(username,password)
    server.sendmail(fromaddr, recipient, msg.as_string())
    server.quit()

    if not JOB_MESSAGE_ID.has_key(job_id):
        JOB_MESSAGE_ID[job_id] = message_id


def log(message, options):
    timestamp = email.Utils.formatdate(localtime=True)
    logfile = full_expand(os.path.join(os.environ['LPBS_HOME'], 
                                       options.config.get('LPBS', 'logfile')))
    try:
        log_fh = open(logfile, 'a')
        print >> log_fh, "%s  \t  %s" % (timestamp, message)
        log_fh.close()
    except IOError:
        pass
