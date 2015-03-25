# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2015 by Michael Goerz                                   #
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

""" Notifications and Logging """

import email
import smtplib
import socket
import logging
try:
    import gntp
    import gntp.notifier as gntp_notifier
except ImportError:
    gntp_notifier = None


COND_STRT = 1 # Begun execution
COND_STOP = 2 # Execution terminated
COND_ABRT = 3 # Execution aborted
COND_ABER = 4 # Execution failed


class Notifier:
    """ Notifier for a single job  """
    def __init__(self, job_id, options=None):
        logging.debug("Setting up Notifier for %s" % job_id)
        self.notifications = {
            'growl' : False,
            'mail' : False
        }
        self.job_id = job_id
        self.job_name = options.job_name
        self.job_retcode = -1
        self.growl_types = ["Job Started", "Job Finished", "Job Aborted",
                            "Job Failed", "Other"] # types of growl messages
        self.growl = {}
        self.growl['sticky'] = False
        self.growl['hostnames'] = []
        self.growl['passwords'] = []
        self.mail = {}
        self.mail['recipients'] = []
        self.mail['use_tls'] = True
        self.mail['mail_conditions'] = [True, True, True, True]
        self.mail['from'] = ''
        self.mail['authenticate'] = False
        self.mail['username'] = ''
        self.mail['password'] = 'secret'
        self.mail['smtp_server'] = 'localhost'
        self._message_id = ''
        self._growl_notifiers = []

        if options is not None:

            # Transfer email options to Notifier
            if options.config.getboolean("Notification", 'send_mail'):
                self.notifications['mail'] = True
                self.mail['authenticate'] = \
                options.config.getboolean("Mail", 'authenticate')
                self.mail['sender'] =  options.config.get("Mail", 'from')
                self.mail['username'] =  options.config.get("Mail", 'username')
                self.mail['password'] =  options.config.get("Mail", 'password')
                self.mail['smtp_server'] =  options.config.get("Mail", 'smtp')
                if options.email_addresses is not None:
                    for item in options.email_addresses:
                        for address in item.split(","):
                            self.mail['recipients'].append(address)

            # Transfer growl options to Notifier
            if options.config.getboolean("Notification", 'send_growl'):
                self.notifications['growl'] = True
                self.growl['sticky'] \
                = options.config.getboolean("Growl", 'sticky')
                for hostname in \
                options.config.get("Growl", "hostname").split(","):
                    self.growl['hostnames'].append(hostname.strip())
                for password in \
                options.config.get("Growl", "password").split(","):
                    self.growl['passwords'].append(password.strip())
                # If there are less passwords given than hostnames, assume that
                # the last password is valid for all remaining hostnames
                while ( len(self.growl['passwords'])
                < len(self.growl['hostnames']) ):
                    self.growl['passwords'].append(self.growl['passwords'][-1])
                # Construct growl_notifiers
                if gntp_notifier is None:
                    logging.error("gntp module not availalble. Will not send "
                    "growl notifications")
                else:
                    for i, hostname in enumerate(self.growl['hostnames']):
                        try:
                            hostname, port = hostname.split(":", 2)
                        except ValueError:
                            port = 23053
                        try:
                            port = int(port)
                        except ValueError:
                            logging.debug("Can't parse port '%s'", port)
                            port = 23053
                        password = self.growl['passwords'][i]
                        growl_notifier = self._register_growl(hostname, port,
                        password, force=True)
                        if growl_notifier is not None:
                            self._growl_notifiers.append(growl_notifier)


    def notify(self, condition, message=None):
        """ Send notification for the given condition COND_STRT, COND_STOP,
            COND_ABRT, or COND_ABER. If message is given, it is appended to the
            auto-generated notification text
        """
        logging.debug("Sending notification for condition %i", condition)
        if self.notifications['mail']:
            self.notify_email(condition, message)
        if self.notifications['growl']:
            self.notify_growl(condition, message)


    def notify_growl(self, condition, message=None):
        """ Send notification via growl """
        logging.debug("Sending growl notification for condition %i", condition)
        titles = ["Begun execution", "Execution Terminated",
                  "Execution aborted", "Execution failed"]
        try:
            growl_type = self.growl_types[condition-1]
            title = "LPBS: %s" % titles[condition-1]
        except IndexError:
            logging.debug("Handling unknown codition in notify_growl")
            growl_type = self.growl_types[-1] # "Other"
            title = "LPBS"
        for growl_notifier in self._growl_notifiers:
            logging.debug("Sending growl notification to host %s",
                          growl_notifier.hostname)
            try:
                if test_socket(growl_notifier.hostname, growl_notifier.port):
                    growl_notifier.notify(noteType=growl_type, title=title,
                    description=self._get_notify_description(condition,
                    message), icon="", sticky=self.growl['sticky'],
                    priority=1)
            except socket.error, error:
                logging.warn("Can't connect to growl on %s",
                              growl_notifier.hostname)
                logging.debug("%s", error)


    def _get_notify_description(self, condition, message=None):
        """ Return the description text for the notification in the given
            condition. If message is given, it is appended to the description
        """
        description  = "PBS Job ID: %s\n" % self.job_id
        description += "Job Name: %s\n" % self.job_name
        if condition == COND_STRT:
            description += "Begun execution\n"
        elif condition == COND_STOP:
            description += "Execution Terminated\n"
            description += "Exit Status = %s\n" % self.job_retcode
        elif condition == COND_ABRT:
            description += "Execution Aborted\n"
        elif condition == COND_ABER:
            description += "Execution Failed\n"
        if message is not None:
            description += "\n" + message
        return description

    def _register_growl(self, hostname, port=23053, password='', force=False):
        """ Return a GrowlNotifier that's registered with the given
            hostname:port and the given password. If registration fails, return
            None unless force is True, in which case the unregistered
            GrowlNotifier is returned
        """
        logging.debug("Registering with growl on %s:%s", hostname, port)
        growl_notifier = gntp_notifier.GrowlNotifier(
        applicationName="LPBS",
        notifications=self.growl_types,
        defaultNotifications=["Job Started"],
        hostname=hostname.strip(),
        port=port,
        password=password.strip())
        try:
            if test_socket(hostname, port):
                growl_notifier.register()
        except socket.error, error:
            logging.warn("Can't connect to growl on %s:%s",
                          growl_notifier.hostname, port)
            logging.debug("%s", error)
            if not force:
                return None
        except gntp.BaseError, error:
            logging.warn("GNTP Exception")
            logging.debug("%s", error)
            return None
        return growl_notifier

    def notify_email(self, condition, message=None):
        """ Notify by email """
        if not self.mail['mail_conditions'][condition-1]:
            logging.debug("Skipping email notification for condition %i",
                          condition)
            return
        logging.debug("Sending email notification for condition %i", condition)
        for recipient in self.mail['recipients']:
            logging.debug("Sending email to %s", recipient)
            msg = email.Message.Message()
            fromaddr = self.mail['sender']
            smpt_server = self.mail['smtp_server']

            message_id = email.utils.make_msgid('lpbs')
            msg.add_header("Subject", "LPBS JOB %s" % self.job_id)
            msg.add_header("Message-Id", message_id)
            msg.add_header("From", self.mail['from'])
            msg.add_header("To", recipient)
            if condition == COND_STRT:
                self._message_id = message_id
            else:
                msg.add_header("In-Reply-To:", self._message_id)
                msg.add_header("References:", self._message_id)
            msg.set_charset("UTF-8")
            description = self._get_notify_description(condition, message)
            msg.set_payload(description, charset="UTF-8")

            try:
                server = smtplib.SMTP(smpt_server)
                if self.mail['use_tls']:
                    server.starttls()
                if self.mail['authenticate']:
                    username = self.mail['username']
                    password = self.mail['password']
                    server.login(username, password)
                server.sendmail(fromaddr, recipient, msg.as_string())
                server.quit()
            except socket.error, error:
                logging.warn("Can't connect to smtp server")
                logging.debug("%s", error)
            except smtplib.SMTPAuthenticationError, error:
                logging.warn("SMTP Authentication Error")
                logging.debug("%s", error)
            except smtplib.SMTPException, error:
                logging.warn("SMTP Exception")
                logging.debug("%s", error)


def test_socket(host, port, timeout=10):
    """ Check if we can open a socket to the given host:port within the number
        of seconds specified by timeout. Return True if a connection could be
        made, False otherwise.
    """
    sock = socket.socket()
    try:
        sock.settimeout(timeout)
        sock.connect((host, port))
        return True
    except socket.error, error:
        logging.debug("test_socket(%s,%s,%s) failed: %s",
                      host, port, timeout, error)
        return False
