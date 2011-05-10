#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# Output a PICL trace to visualize a coNCePTuaL program's dynamic
# behavior
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# Copyright (C) 2011, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2011).  Los Alamos National Security, LLC.  This software
# was produced under U.S. Government contract DE-AC52-06NA25396
# for Los Alamos National Laboratory (LANL), which is operated by
# Los Alamos National Security, LLC (LANS) for the U.S. Department
# of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
# MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
# FOR THE USE OF THIS SOFTWARE. If software is modified to produce
# derivative works, such modified software should be clearly marked,
# so as not to confuse it with the version available from LANL.
# 
# Additionally, redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the
# following conditions are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer
#     in the documentation and/or other materials provided with the
#     distribution.
# 
#   * Neither the name of Los Alamos National Security, LLC, Los Alamos
#     National Laboratory, the U.S. Government, nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################

import codegen_interpret
import sys
import os
import string
import re
import types
from math import *


class NCPTL_CodeGen(codegen_interpret.NCPTL_CodeGen):

    #---------------------#
    # Exported functions  #
    # (called from the    #
    # compiler front end) #
    #---------------------#

    def __init__(self, options=None):
        "Initialize PICL tracing."
        codegen_interpret.NCPTL_CodeGen.__init__(self, options)
        self.backend_name = "picl"
        self.backend_desc = "PICL event trace"
        self.parent = self.__class__.__bases__[0]
        self.allevents = 0        # 0=comm. events only; 1=all events
        self.tasks2id = {}        # Map from a task list to a subset ID
        self.noncomm2id = {}      # Map from a non-communication event to a user-defined event ID
        self.comm_ops = ["SEND", "RECEIVE", "WAIT_ALL", "SYNC", "MCAST"]   # List of all communication operations

    def generate(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        'Interpret an AST and "trace" the events that were executed.'
        self.generate_initialize(ast, filesource, sourcecode)

        # Give every event list a pointer back to us.
        for el in self.eventlist:
            el.codegen = self

        # Remove log-file options and add an option changing the event
        # frequency and one for including all events.
        self.set_log_file_status(0)
        self.options.extend([
            ["evfreq", "PICL event frequency (Hz)", "frequency", "F", 100000L],
            ["allevents", "0=include only communication events; 1=include all events ", "all-events", "A", 0L]])

        # Perform a prefix traversal (roughly) and "trace" the results.
        self.process_node(ast)
        self.generate_finalize(ast, filesource, sourcecode)
        return self.trace_events()

    def compile_only(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Write trace code to a file."
        newin, _ = self.write_trace_code(progfilename, codelines, outfilename)
        if verbose:
            sys.stderr.write("# Files generated: %s\n" % newin)

    def compile_and_link(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Linking is not meaningful here."
        self.compile_only(progfilename, codelines, outfilename, verbose, keepints)


    #------------------#
    # Internal utility #
    # functions        #
    #------------------#

    def write_trace_code(self, progfilename, codelines, outfilename):
        "Output trace code to a file and return the modified input and output filenames."

        # Determine the names of the files to use.
        trace_extension = ".trf"
        if progfilename == "<command line>":
            progfilename = "a.out.ncptl"
        if outfilename == "-":
            outfilename, _ = os.path.splitext(progfilename)
            outfilename = outfilename + trace_extension

        # Derive the name of the trace file from outfilename.
        infilename, _ = os.path.splitext(outfilename)
        infilename = infilename + trace_extension

        # Copy CODELINES to a trace file.
        try:
            infile = open(infilename, "w")
            for oneline in codelines:
                infile.write("%s\n" % oneline)
            infile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("Unable to produce %s (%s)" % (infilename, strerror),
                                    filename=self.backend_name)

        # Return the modified input and output filenames.
        return (infilename, outfilename)

    def write_picl(self, rectype, task, begintime, endtime, beginargs, endargs,
                 beginformat="2", endformat="2"):
        "Write arbitrary begin and end PICL events."

        def port_o_str(val):
            "Define a version of str that properly converts longs in old Pythons."
            if type(val) == types.LongType:
                return "%d" % val
            else:
                return str(val)

        beginpicl = ("-3 %d %.*f %d %d %d" %
                     (rectype, self.time_digits, begintime, task, 0, len(beginargs)))
        if len(beginargs):
            beginpicl = beginpicl + " %s %s" % (beginformat, string.join(map(port_o_str, beginargs), " "))
        endpicl = ("-4 %d %.*f %d %d %d" %
                     (rectype, self.time_digits, endtime, task, 0, len(endargs)))
        if len(endargs):
            endpicl = endpicl + " %s %s" % (endformat, string.join(map(port_o_str, endargs), " "))
        self.picl_events.extend([beginpicl, endpicl])

    def allocate_task_subset(self, tasklist):
        """
             Write PICL events to define a subset of tasks for a
             collective-communication operation.  Return the
             corresponding subset ID.
        """
        if tasklist == range(0, int(self.numtasks)):
            return -1
        tasklist_string = string.join(map(lambda lng: str(int(lng)), tasklist), " ")
        if self.tasks2id.has_key(tasklist_string):
            # We've already used this subset.
            return self.tasks2id[tasklist_string]

        # Define a new subset.
        subset_id = len(self.tasks2id)
        self.tasks2id[tasklist_string] = subset_id
        self.picl_events.append("-202 -812 %.*f -1 -1 %d 2 %d %s" %
                                (self.time_digits, 0.0, len(tasklist)+1,
                                 subset_id, tasklist_string))
        return subset_id


    #----------------#
    # Hook functions #
    #----------------#

    def n_program_PROCESS_OPTION(self, localvars):
        "Process command-line options of importance to us."
        opt = localvars["opt"]
        if opt[0] == "evfreq":
            self.event_frequency = int(opt[-1])
            if self.event_frequency < 1:
                self.errmsg.error_fatal("the --%s option accepts only positive integers" % opt[2])
            self.time_increment = 1.0 / self.event_frequency
            self.time_digits = int(ceil(log10(self.event_frequency))) + 1
            return 1
        elif opt[0] == "allevents":
            self.allevents = int(opt[-1])
            if self.allevents not in [0, 1]:
                self.errmsg.error_fatal("the --%s option accepts only 0 or 1" % opt[2])
            return 1
        elif hasattr(self.parent, "n_program_PROCESS_OPTION"):
            # Give our parent a chance to process the current option.
            return self.parent.n_program_PROCESS_OPTION(self, localvars)
        else:
            return 0

    def process_reduce_READY(self, localvars):
        "Store pointers to all of our peer events then complete at the latest completion time."
        event = localvars["event"]
        if hasattr(event, "peerevents"):
            return None
        eventlist = []
        taskusage = localvars["taskusage"]
        for peer in taskusage.keys():
            eventlist.append(self.eventlist[peer].get_first_incomplete())
        for event in eventlist:
            event.peerevents = eventlist
        self.eventlist[event.task].complete(eventlist)
        return None


    #------------------#
    # Method overrides #
    #------------------#

    class EventList(codegen_interpret.NCPTL_CodeGen.EventList):
        def complete_post_overhead(self, prev_ev, this_ev):
            "Return the overhead between completing an event and posting the next event."
            prevop = prev_ev.operation
            if prevop == "RECEIVE" and prev_ev.blocking:
                # Receiving a blocking message never take any time.
                return 0
            if prevop == "NEWSTMT":
                # New statements never take any time.
                return 0
            if prevop in self.codegen.comm_ops:
                # Communication statements always take unit time.
                return 1

            # The remaining events take either no time or unit time,
            # depending upon the value of the ALLEVENTS flag.
            return self.codegen.allevents

    def process_output(self, event):
        """
             Process an OUTPUT event.  As a side effect, the event's
             attributes are replaced with their string equivalent.
             Note that, unlike in codegen_interpret, no text is
             actually output.
        """
        task = event.task
        self.physrank = event.task    # May be needed by futures.
        self.eventlist[task].try_posting_all()   # Update event.posttime.
        self.counters[task]["elapsed_usecs"] = event.posttime - self.timer_start[task]
        event.attributes = [string.join(map(self.eval_lazy_expr, event.attributes), "")]
        self.eventlist[task].complete()
        return None

    def process_log(self, event):
        "Do nothing; the PICL backend does not produce log files."
        return self.process_no_op(event)

    def process_aggregate(self, event):
        "Do nothing; the PICL backend does not produce log files."
        return self.process_no_op(event)


    #--------------------------#
    # Top-level trace function #
    #--------------------------#

    def trace_events(self):
        '"Trace" all of the events dumped by the interpret backend.'

        # Combine the event lists into a single list sorted by posting time.
        sorted_events = map(lambda ev: (ev.posttime, ev.task, ev),
                            reduce(lambda a, b: a+b,
                                   map(lambda el: el.events, self.eventlist)))
        sorted_events.sort()

        # Initialize PICL on all tasks.
        self.picl_events = []
        for task in range(0, self.numtasks):
            self.picl_events.append("-3 -901 %.*f %d %d 0" %
                                    (self.time_digits, 0.0, task, 0))

        # Define a mapping from an operation to a method.
        op2method = {
            "SEND"     : self.trace_send,
            "RECEIVE"  : self.trace_receive,
            "WAIT_ALL" : self.trace_wait_all,
            "SYNC"     : self.trace_sync,
            "MCAST"    : self.trace_mcast,
            "REDUCE"   : self.trace_reduce,
            "OUTPUT"   : self.trace_output}

        # Process every event on every task.
        maxtime = [0.0] * int(self.numtasks)
        self.pending_ops = map(lambda x: [], maxtime)
        for posttime, task, event in sorted_events:
            begintime = (posttime+1) * self.time_increment
            try:
                endtime = (event.completetime+1) * self.time_increment
            except TypeError:
                # The event never completed.
                continue
            maxtime[task] = max(maxtime[task], endtime)
            try:
                op2method[event.operation](task, event, begintime, endtime)
            except KeyError:
                self.trace_non_comm(task, event, begintime, endtime)

        # Finalize PICL on all tasks.
        for task in range(0, self.numtasks):
            self.picl_events.append("-4 -901 %.*f %d %d 0" %
                                    (self.time_digits,
                                     maxtime[task]+self.time_increment,
                                     task, 0))

        # Sort events by time and return the result.  Force stable
        # sorting using the current event number.
        sorted_events = []
        eventnum = 0
        for picl_event in self.picl_events:
            fields = string.split(picl_event)
            sorted_events.append(((float(fields[2]), int(fields[3]), eventnum), picl_event))
            eventnum = eventnum + 1
        sorted_events.sort()
        return map(lambda fe: fe[1], sorted_events)


    #------------------------#
    # Functions that produce #
    # PICL records           #
    #------------------------#

    def trace_send(self, sender, event, begintime, endtime):
        "Perform blocking and nonblocking sends."
        receiver = event.peers[0]
        bytecount = event.msgsize
        if event.blocking:
            # Blocking send
            self.write_picl(-21, sender, begintime, endtime,
                            [bytecount, 1, receiver, 0], [])
        else:
            # Nonblocking send
            self.write_picl(-27, sender, begintime, endtime,
                            [bytecount, 1, receiver, 0], [len(self.pending_ops[sender])])
            self.pending_ops[sender].append(event)

    def trace_receive(self, receiver, event, begintime, endtime):
        "Perform blocking and nonblocking receives."
        sender = event.peers[0]
        bytecount = event.msgsize
        if event.blocking:
            # Blocking receive
            self.write_picl(-52, receiver, begintime, endtime,
                            [1, sender, 0], [bytecount, 1, sender, 0])
        else:
            # Nonblocking receive
            self.write_picl(-57, receiver, begintime, endtime,
                            [1, sender, 0], [len(self.pending_ops[receiver])])
            self.pending_ops[receiver].append(event)

    def trace_wait_all(self, task, event, begintime, endtime):
        "Block until all pending sends and receives are complete."

        # Wait individually for each asynchronous send or receive.
        for event_id in range(0, len(self.pending_ops[task])):
            aevent = self.pending_ops[task][event_id]
            if aevent.operation == "SEND":
                self.write_picl(-31, task, begintime, endtime, [event_id], [])
            elif aevent.operation == "RECEIVE":
                self.write_picl(-61, task, begintime, endtime,
                                [event_id], [aevent.msgsize, 1, aevent.peers[0], 0])
            else:
                self.errmsg.error_internal('unrecognized asynchronous event type "%s"' % aevent)
        self.pending_ops[task] = []

    def trace_sync(self, task, event, begintime, endtime):
        "Synchronize a set of tasks."
        subset_id = self.allocate_task_subset(event.peers)
        self.write_picl(-402, task, begintime, endtime, [subset_id], [])

    def trace_reduce(self, task, event, begintime, endtime):
        "Reduce a value to one or more targets."
        senders, receivers = event.peers
        bytecount = event.msgsize
        if len(receivers) == 1:
            # Reduce from many to one (reduce)
            subset_id = self.allocate_task_subset(senders)
            root = receivers[0]
            if task != root:
                bytecount = -1
            self.write_picl(-790, task, begintime, endtime,
                            [event.msgsize, root, subset_id], [bytecount])
        elif senders == receivers:
            # Reduce from a set to itself (allreduce)
            subset_id = self.allocate_task_subset(senders)
            self.write_picl(-782, task, begintime, endtime,
                            [bytecount, subset_id], [subset_id])
        else:
            # Reduce from a set of tasks to a different set (reduce+bcast).
            send_subset_id = self.allocate_task_subset(senders)
            recv_subset_id = self.allocate_task_subset(receivers)
            root = receivers[0]
            if task != root:
                bytecount = -1
            minbegintime = min(map(lambda ev: 1+ev.posttime, event.peerevents)) * self.time_increment
            maxbegintime = max(map(lambda ev: 1+ev.posttime, event.peerevents)) * self.time_increment
            minendtime = min(map(lambda ev: 1+ev.completetime, event.peerevents)) * self.time_increment
            maxendtime = max(map(lambda ev: 1+ev.completetime, event.peerevents)) * self.time_increment
            midtime1 = (2*maxbegintime+minendtime) / 3.0
            midtime2 = (maxbegintime+2*minendtime) / 3.0
            if task in senders:
                self.write_picl(-790, task, begintime, midtime1,
                                [event.msgsize, root, send_subset_id], [bytecount])
            if task in receivers:
                self.write_picl(-785, task, midtime2, endtime,
                                [bytecount, root, recv_subset_id], [event.msgsize])

    def trace_mcast(self, receiver, event, begintime, endtime):
        "Multicast a message to a set of tasks."

        # We implement multicast in terms of blocking, point-to-point
        # sends and receives.
        sender = event.peers[0]
        bytecount = event.msgsize
        if sender == receiver:
            # Post all of the sends at the same time.
            for eachrecv in event.peers[1:]:
                self.write_picl(-21, sender, begintime, endtime,
                                [bytecount, 1, eachrecv, 0], [])
        else:
            # Post each receive at the receiver's convenience.
            self.write_picl(-52, receiver, begintime, endtime,
                            [1, sender, 0], [bytecount, 1, sender, 0])

    def trace_output(self, task, event, begintime, endtime):
        "Write a PICL tracemsg event whenever we output."

        # Determine the number of space-separated words in the string.
        wordlist = re.split(r'\s', event.attributes[0])
        message = string.join(wordlist, " ")
        self.write_picl(-911, task, begintime, endtime,
                        [len(message)] + wordlist, [],
                        '"%%d%s"' % (" %s" * len(wordlist)))

        # If we're told to trace all events, then OUTPUT additionally
        # needs to produce a user-defined event.
        self.trace_non_comm(task, event, begintime, endtime)

    def trace_non_comm(self, task, event, begintime, endtime):
        "Perform an arbitrary non-communication operation."
        if self.allevents == 0:
            return

        # Map each unique operation to a user-defined event ID and use that.
        try:
            op_id = self.noncomm2id[event.operation]
        except KeyError:
            op_id = len(self.noncomm2id) + 1
            self.noncomm2id[event.operation] = op_id
        self.write_picl(op_id, task, begintime, endtime, [], [])
