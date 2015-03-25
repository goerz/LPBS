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

""" Utility functions and classes for managing Jobs  """

import os
import sys
import signal
import logging
import pprint
import time
import datetime
import cPickle as pickle
from glob import glob


def get_cpu_mem_info(pid):
    """ Return tuple (cput, mem, vmem, threads) with CPU time in seconds, total
        memory (resident set size) and virtual memory in bytes, all ccumulated
        for for the process with the given PID and all subprocesses;
        and number of threads, for the last process in the subprocess chain
    """
    cput = 0
    mem = 0
    vmem = 0
    threads = 0
    try:
        import psutil
        try:
            process = psutil.Process(pid)
            try:
                cput = int(sum(process.get_cpu_times()))
            except psutil.AccessDenied:
                logging.debug("psutil: Access denied for get_cpu_times")
                cput = 0
            try:
                (mem, vmem) = process.get_memory_info()
                mem = int(mem)
                vmem = int(vmem)
            except psutil.AccessDenied:
                logging.debug("psutil: Access denied for get_memory_info")
                (mem, vmem) = (0, 0)
            children = process.get_children()
            if len(children) == 0:
                try:
                    threads = len(process.get_threads())
                except psutil.AccessDenied:
                    logging.debug("psutil: Access denied for get_threads")
                    threads = 0
            else:
                for child in children:
                    (cput_child, mem_child, vmem_child, threads_child) \
                    = get_cpu_mem_info(child.pid)
                    cput = cput + cput_child
                    mem = mem + mem_child
                    vmem = vmem + vmem_child
                    if threads_child > 0:
                        threads = threads_child
        except psutil.NoSuchProcess:
            logging.warn("Process %s is not running anymore" % pid)
            return (0, 0, 0, 0)
    except ImportError:
        logging.debug("psutil not available. Cannot get CPU/mem information")
        return (0, 0, 0, 0)
    return (cput, mem, vmem, threads)


def format_bytes(bytes):
    """ Return string representation for number of bytes """
    remaining = bytes
    mbytes = remaining / 1048576
    remaining = remaining - mbytes * 1048576
    if mbytes > 0:
        return "%i MB" % mbytes
    kbytes = remaining / 1024
    remaining = remaining - kbytes * 1024
    if kbytes > 0:
        return "%i KB" % kbytes
    return str(bytes)



class JobInfo:
    """ Class for holding Job Info """
    def __init__(self, job_id=None):
        """ Initialize """
        self.job_id = job_id
        self.pid = None
        self.name = None
        self.owner = None
        self.start_time = 0
        self.server = None
        self.exec_host = None
        self.error_path = None
        self.output_path = None
        self.resources_used = {}
        self.join_path = None
        self.mail_points = None
        self.variable_list = None
        self.lockfile = None
    def __str__(self):
        """ Retrun string representation """
        return pprint.pformat(self.__dict__)
    def full_info(self):
        """ Return multi-line string with full information about the job """
        full_info_str  = "Job Id: %s\n" % self.job_id
        full_info_str += "    Job_Name = %s\n" % self.name
        full_info_str += "    Job_Owner = %s\n" % self.owner
        full_info_str += "    server = %s\n" % self.server
        full_info_str += "    exec_host = %s\n" % self.exec_host
        full_info_str += "    PID = %s\n" % self.pid
        full_info_str += "    Error_Path = %s\n" % self.error_path
        full_info_str += "    Join_Path = %s\n" % self.join_path
        full_info_str += "    Mail_Points = %s\n" % self.mail_points
        full_info_str += "    Output_Path = %s\n" % self.output_path
        for field in self.resources_used.keys():
            full_info_str += "    resources_used.%s = %s\n" % (field,
                                                     self.resources_used[field])
        return full_info_str
    def short_info(self, print_header=False):
        """ Return one-line string with summary of job information """
        short_info_str = ""
        if print_header:
            short_info_str += "%-20s %-15s %-15s %-15s\n" % (
                              'Job id', 'Name', 'User', 'Walltime')
            short_info_str += "%-20s %-15s %-15s %-15s\n" % (
                              '-'*20, '-'*15, '-'*15, '-'*15 )

        walltime = ""
        if self.resources_used.has_key('walltime'):
            walltime = self.resources_used['walltime']
        short_info_str += "%-20s %-15s %-15s %-15s" % (
                          self.job_id[:20], self.name[:15], self.owner[:15],
                          walltime[:15])
        return short_info_str
    def set_lock(self, pid):
        """ Create a lock file and store job information inside """
        if self.job_id is None:
            raise ValueError("Can't set lock unless job_id is set")
        self.lockfile = os.path.join(os.environ['LPBS_HOME'],
                                     "%s.lock" % self.job_id)
        self.pid = pid
        lock = open(self.lockfile, 'w')
        pickle.dump(self, lock)
        lock.close()
    def read_lock(self, lockfile):
        """ Read job info from existing lock file. Raise an IOError if the
            lockfile cannot be read
        """
        lock = open(lockfile, 'r')
        temp = pickle.load(lock)
        lock.close()
        logging.debug("Read JobInfo from lock:\n%s", temp)
        self.__dict__ = temp.__dict__
        if self.start_time > 0:
            walltime = int(time.time() - self.start_time)
            self.resources_used['walltime'] \
            = str(datetime.timedelta(seconds=walltime))
        (cput, mem, vmem, threads) = get_cpu_mem_info(self.pid)
        if cput > 0:
            self.resources_used['cput'] \
            = str(datetime.timedelta(seconds=cput))
        if mem > 0:
            self.resources_used['mem'] = format_bytes(mem)
        if vmem > 0:
            self.resources_used['vmem'] = format_bytes(vmem)
        if threads > 0:
            self.resources_used['threads'] = threads
        self.job_id = os.path.splitext(os.path.basename(lockfile))[0]
        self.lockfile = lockfile
    def release_lock(self):
        """ Delete lock """
        if self.job_id is None:
            raise ValueError("Can't release lock unless job_id is set")
        lockfile = os.path.join(os.environ['LPBS_HOME'], "%s.lock"
                                % self.job_id)
        logging.debug("Releasing lock: %s", lockfile)
        try:
            os.unlink(lockfile)
        except OSError:
            pass


def get_new_job_id(options):
    """ Return a fresh, unused job ID """
    sequencefile = os.path.join(os.environ['LPBS_HOME'],
                                options.config.get('LPBS', 'sequence_file'))
    # read previous sequence number and up-one
    try:
        sequencefile_fh = open(sequencefile, 'r')
        sequence = int(sequencefile_fh.read())
        sequencefile_fh.close()
    except IOError, error:
        sequence = 0
    sequence = sequence + 1
    # write new sequence number back to sequence file
    try:
        sequencefile_fh = open(sequencefile, 'w')
        sequencefile_fh.write(str(sequence))
        sequencefile_fh.close()
    except IOError, error:
        print >> sys.stderr, "Could not write to %s:\n%s" \
                             % (sequencefile, error)
        return None
    id_host = options.config.get("Server", 'hostname')
    id_domain = options.config.get("Server", 'domain')
    if options.config.getboolean('LPBS', 'username_in_jobid'):
        return "%s.%s.%s.%s" \
                % (sequence, id_host, id_domain, os.environ['USER'])
    else:
        return "%s.%s.%s" % (sequence, id_host, id_domain)



def pid_for_job_id(job_id):
    """ For a given Job_ID, return the process ID, or None if the given job id
        does not exist or is not accessible
    """
    lock_files = glob(os.path.join(os.environ['LPBS_HOME'], '*.lock'))
    for lock_file in lock_files:
        if os.path.basename(lock_file).startswith(job_id):
            job_info = JobInfo()
            try:
                job_info.read_lock(lock_file)
                return(job_info.pid)
            except IOError, error:
                logging.debug("Failed to open lock: %s", error)
                return None
    logging.debug("No lock file found for job_id %s", job_id)
    return None


def send_sig_to_job_id(job_id, sig=signal.SIGTERM):
    """ Send a sig to the given job id """
    pid = pid_for_job_id(job_id)
    if pid is not None:
        try:
            os.kill(pid, sig)
            logging.info("Sent signal %s to job %s (PID %s)", sig, job_id, pid)
        except OSError, error:
            logging.debug("Sent signal %s to job %s (PID %s)", sig, job_id, pid)
            logging.debug("Failed to send signal: %s", error)
    else:
        logging.debug("Skipped sending signal %s to job %s (pid not found)",
                      sig, job_id)
