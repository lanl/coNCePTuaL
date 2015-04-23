#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# Output a Paraver trace to visualize a coNCePTuaL program's dynamic
# behavior
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# 
# Copyright (C) 2015, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2015).  Los Alamos National Security, LLC.  This software
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
#
########################################################################

import codegen_interpret
import sys
import os
import string
import time


class NCPTL_CodeGen(codegen_interpret.NCPTL_CodeGen):

    #---------------------#
    # Exported functions  #
    # (called from the    #
    # compiler front end) #
    #---------------------#

    def __init__(self, options=None):
        "Initialize Paraver tracing."
        codegen_interpret.NCPTL_CodeGen.__init__(self, options)
        self.backend_name = "paraver"
        self.backend_desc = "Paraver event trace"
        self.parent = self.__class__.__bases__[0]
        self.comptime = 0         # Time spent in each non-communication event
        self.inc_source = 1       # 0=exclude source lines; 1=include them
        self.inc_concev = 0       # 0=exclude coNCePTuaL event names; 1=include them
        self.dimemas_events = 0   # 1=extra events for Dimemas simulator; 0=skip
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
            ["evtime", "Paraver event time (ns)", "event-time", "P", 1000L],
            ["comptime", "Time spent in each non-communication event (ns)", "comp-time", "O", 0L],
            ["inc_source", "0=exclude references to coNCePTuaL source lines; 1=include them", "conc-source", "R", 1L],
            ["inc_concev", "0=exclude names of coNCePTuaL event types; 1=include them", "conc-events", "E", 0L],
            ["inc_dimemas", "0=no Dimemas events; 1=extra events for Dimemas simulator", "dimemas-events", "D", 0L]])

        # Perform a prefix traversal (roughly) and "trace" the results.
        self.process_node(ast)
        self.generate_finalize(ast, filesource, sourcecode)
        return self.trace_events()

    def compile_only(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Write the given trace code to a file."
        tracefile = self.write_trace_code(progfilename, codelines, outfilename)
        configfile = self.write_config_code(progfilename, outfilename)
        if verbose:
            sys.stderr.write("# Files generated: %s %s\n" % (tracefile, configfile))

    def compile_and_link(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Linking is not meaningful here."
        self.compile_only(progfilename, codelines, outfilename, verbose, keepints)


    #------------------#
    # Internal utility #
    # functions        #
    #------------------#

    def peergroup2num(self, tasklist):
        "Map a unique set of tasks to a unique integer."
        taskset = {}
        for task in tasklist:
            taskset[task] = 1
        taskset = tuple(sorted(taskset.keys()))
        try:
            return self.peergroups[taskset]
        except KeyError:
            self.peergroups[taskset] = len(self.peergroups) + 1
            return self.peergroups[taskset]

    def write_trace_code(self, progfilename, codelines, outfilename):
        "Output trace code to a file and return the corresponding filename."

        # Determine the names of the files to use.
        trace_extension = ".prv"
        if progfilename == "<command line>":
            progfilename = "a.out.ncptl"
        if outfilename == "-":
            outfilename, _ = os.path.splitext(progfilename)
            outfilename = outfilename + trace_extension

        # Derive the name of the trace file from outfilename.
        tracefilename, _ = os.path.splitext(outfilename)
        tracefilename = tracefilename + trace_extension

        # Copy CODELINES to the trace file.
        try:
            trfile = open(tracefilename, "w")
            for oneline in codelines:
                trfile.write("%s\n" % oneline)
            trfile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("Unable to produce %s (%s)" % (tracefilename, strerror),
                                    filename=self.backend_name)

        # Return the name of the trace file.
        return tracefilename

    def write_config_code(self, progfilename, outfilename):
        "Output configuration code to a file and return the corresponding filename."

        # Determine the name of the file to use.
        config_extension = ".pcf"
        origprogfilename = progfilename
        if progfilename == "<command line>":
            progfilename = "a.out.ncptl"
        if outfilename == "-":
            outfilename, _ = os.path.splitext(progfilename)
            outfilename = outfilename + config_extension

        # Derive the name of the config file from outfilename.
        configfilename, _ = os.path.splitext(outfilename)
        configfilename = configfilename + config_extension

        # Write some boilerplate text (largely copied from the output
        # of Extrae's mpi2prv command) to the configuration file.
        try:
            pcffile = open(configfilename, "w")
            pcffile.write("""\
DEFAULT_OPTIONS

LEVEL               CPU
UNITS               NANOSEC

DEFAULT_SEMANTIC

THREAD_FUNC         State As Is

STATES
 0    Idle
 1    Running
 2    Not created
 3    Waiting a message
 4    Blocking Send
 5    Synchronization
 6    Test/Probe
 7    Scheduling and Fork/Join
 8    Wait/WaitAll
 9    Blocked
10    Immediate Send
11    Immediate Receive
12    I/O
13    Group Communication
14    Tracing Disabled
15    Others
16    Send Receive

STATES_COLOR
 0    {117,195,255}
 1    {0,0,255}
 2    {255,255,255}
 3    {255,0,0}
 4    {255,0,174}
 5    {179,0,0}
 6    {0,255,0}
 7    {255,255,0}
 8    {235,0,0}
 9    {0,162,0}
10    {255,0,255}
11    {100,100,177}
12    {172,174,41}
13    {255,144,26}
14    {2,255,177}
15    {192,224,0}
16    {66,66,66}

EVENT_TYPE
 1    1000000 coNCePTuaL event
VALUES
""")
            for evname, evnum in sorted(self.op2number.items(), key=lambda name_num: name_num[1]):
                pcffile.write("%2d    %s\n" % (evnum, evname))
            pcffile.write("""
EVENT_TYPE
 1    1000001 %s source line

EVENT_TYPE
 1    2000000 Message size for a collective operation
 1    2000001 Peer group for a collective operation
""" % origprogfilename)
            if self.dimemas_events:
                pcffile.write("""
EVENT_TYPE
 9    50000001 Communication block
VALUES
 0    End of point-to-point operation
 1    Begin point-to-point send
 2    Begin point-to-point receive
 3    Begin asynchronous point-to-point send
 4    Begin asynchronous point-to-point receive
 6    Begin waiting for asynchronous event completion

EVENT_TYPE
 9    50000002 Collective block
VALUES
 0   End of collective operation
 7   Begin multicast
 8   Begin barrier
 9   Begin reduction
""")
            pcffile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("Unable to produce %s (%s)" % (configfilename, strerror),
                                    filename=self.backend_name)

        # Return the name of the configuration file.
        return configfilename


    #----------------#
    # Hook functions #
    #----------------#

    def n_program_PROCESS_OPTION(self, localvars):
        "Process command-line options of importance to us."
        opt = localvars["opt"]
        if opt[0] == "evtime":
            self.time_increment = int(opt[-1])
            if self.time_increment < 1:
                self.errmsg.error_fatal("the --%s option accepts only positive integers" % opt[2])
            return 1
        elif opt[0] == "comptime":
            self.comptime = int(opt[-1])
            if self.comptime < 0:
                self.errmsg.error_fatal("the --%s option requires a positive argument" % opt[2])
            return 1
        elif opt[0] == "inc_source":
            self.inc_source = int(opt[-1])
            if self.inc_source not in [0, 1]:
                self.errmsg.error_fatal("the --%s option accepts only 0 or 1" % opt[2])
            return 1
        elif opt[0] == "inc_concev":
            self.inc_concev = int(opt[-1])
            if self.inc_concev not in [0, 1]:
                self.errmsg.error_fatal("the --%s option accepts only 0 or 1" % opt[2])
            return 1
        elif opt[0] == "inc_dimemas":
            self.dimemas_events = int(opt[-1])
            if self.dimemas_events not in [0, 1]:
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
        def post_complete_overhead(self, event):
            "Return the overhead between posting and completing an event."
            op = event.operation
            if op == "NEWSTMT":
                # New statements never take any time.
                return 0
            elif op in self.codegen.comm_ops:
                # Communication statements always take unit time.
                return 1
            else:
                # The remaining events take the amount of time
                # specified by the --comp-time command-line option.
                return self.codegen.comptime

        def complete_post_overhead(self, prev_ev, this_ev):
            "Return the overhead between completing an event and posting the next event."
            if self.parent.dimemas_events:
                # Dimemas doesn't like it when one communication
                # operation begins at the exact same time the previous
                # operation ends.
                return 1.0 / self.parent.time_increment
            else:
                return 0

        def complete(self, peerlist=None, nolat_peerlist=None):
            """
                 Mark the first incomplete event as completed and
                 return the completion time.  We additionally keep
                 track of times at which blocking receives completed
                 and also assign CLIQUE to the set of matched
                 communication events.
            """
            newtime = codegen_interpret.NCPTL_CodeGen.EventList.complete(self, peerlist, nolat_peerlist)

            # Keep track of blocking receives.
            thisev = self.events[self.first_incomplete-1]
            if thisev.blocking:
                try:
                    if thisev.operation in ["RECEIVE", "MCAST"]:
                        self.blocking_times[newtime] = 1
                    elif thisev.operation == "WAIT_ALL" and thisev.await_receives:
                        self.blocking_times[newtime] = 1
                except AttributeError:
                    self.blocking_times = {newtime: 1}

            # Acquire a list of unique events.
            matched_events = {}
            if peerlist:
                for peerev in peerlist:
                    matched_events[peerev] = 1
            if nolat_peerlist:
                for peerev in nolat_peerlist:
                    matched_events[peerev] = 1
            try:
                matched_events[thisev] = 1
                for peerev in thisev.clique:
                    matched_events[peerev] = 1
            except AttributeError:
                pass
            matched_events = matched_events.keys()

            # Assign the unique-event list to everyone in the clique.
            for peerev in matched_events:
                peerev.clique = matched_events
            return newtime

    def process_output(self, event):
        "Do nothing; the Paraver backend does not write to standard output."
        return self.process_no_op(event)

    def process_log(self, event):
        "Do nothing; the Paraver backend does not produce log files."
        return self.process_no_op(event)

    def process_aggregate(self, event):
        "Do nothing; the Paraver backend does not produce log files."
        return self.process_no_op(event)


    #--------------------------#
    # Top-level trace function #
    #--------------------------#

    def trace_events(self):
        '"Trace" all of the events dumped by the interpret backend.'
        # Enumerate all operations that the coNCePTuaL interpreter knows about.
        self.op2number = {}
        for op in sorted(self.opmethod.keys()):
            self.op2number[op] = len(self.op2number) + 1

        # Define a mapping from each operation we care about to a method.
        op2method = {
            "SEND"     : self.trace_send,
            "RECEIVE"  : self.trace_receive,
            "WAIT_ALL" : self.trace_wait_all,
            "SYNC"     : self.trace_sync,
            "MCAST"    : self.trace_mcast,
            "REDUCE"   : self.trace_reduce}

        # Process every event on every task into an internal
        # representation of Paraver trace data, each record being a
        # tuple of {record type, start time, end time, task,
        # event-specific data}.
        self.peergroups = {}
        maxtime = 0L
        paraver_ir = []
        for evlist in self.eventlist:
            for event in evlist.events:
                # Perform event processing common to all event types.
                maxtime = max(maxtime, event.posttime, event.completetime)
                if self.inc_concev:
                    paraver_ir.append((2, event.posttime, None, event.task,
                                       [(1000000, self.op2number[event.operation])]))
                if self.inc_source:
                    paraver_ir.append((2, event.posttime, None, event.task,
                                       [(1000001, event.srclines[0])]))

                # Perform event-specific processing of each event.
                try:
                    paraver_ir.extend(op2method[event.operation](event))
                except KeyError:
                    paraver_ir.extend(self.trace_non_comm(event))

        # Output a Paraver header.
        paraver_trace = []
        timestr = time.strftime("%02d/%02m/%02Y at %02H:%02M", time.localtime())
        nodestr = "%d(1%s)" % (self.numtasks, ",1" * (self.numtasks-1))
        appstr = "%d(%s)" % (self.numtasks, string.join(["1:" + str(i) for i in range(1,self.numtasks+1)], ","))
        paraver_trace.append("#Paraver (%s):%d_ns:%s:1:%s,%d" % \
                                 (timestr, maxtime*self.time_increment+1,
                                  nodestr, appstr, len(self.peergroups)))
        for pgtasks, pgnum in sorted(self.peergroups.items(), key=lambda t_n: t_n[1]):
            paraver_trace.append("c:1:%d:%d:%s" % \
                                     (pgnum, len(pgtasks),
                                      string.join(map(str, pgtasks), ":")))

        # Sort the Paraver records by ascending time and descending
        # record type and convert each record to a string.
        for rec in sorted(paraver_ir, key=lambda ir: (ir[1], -ir[0], ir[3])):
            if rec[0] == 1:
                # State record
                rectype, begin_time, end_time, task_id, state = rec
                begin_time *= self.time_increment
                try:
                    end_time *= self.time_increment
                except TypeError:
                    # Event never finished
                    end_time = maxtime * self.time_increment
                paraver_trace.append("%d:%d:1:%d:1:%d:%d:%d" % \
                                         (rectype, task_id+1, task_id+1,
                                          begin_time, end_time, state))
            elif rec[0] == 2:
                # Event record
                rectype, begin_time, end_time, task_id, evinfo = rec
                begin_time *= self.time_increment
                evinfo_str = string.join(["%d:%d" % type_value for type_value in evinfo], ":")
                paraver_trace.append("%d:%d:1:%d:1:%d:%s" % \
                                         (rectype, task_id+1, task_id+1,
                                          begin_time, evinfo_str))
            elif rec[0] == 3:
                # Communication record
                rectype, begin_time, end_time, send_id, comm_info = rec
                begin_time *= self.time_increment
                try:
                    end_time *= self.time_increment
                except TypeError:
                    # Event never finished
                    end_time = maxtime * self.time_increment
                recv_id, size = comm_info
                paraver_trace.append("%d:%d:1:%d:1:%d:%d:%d:1:%d:1:%d:%d:%d:0" % \
                                         (rectype, send_id+1, send_id+1,
                                          begin_time, begin_time,
                                          recv_id+1, recv_id+1, end_time,
                                          end_time, size))
            else:
                self.errmsg.error_internal("unable to parse record %s" % repr(rec))
        return paraver_trace


    #------------------------#
    # Functions that produce #
    # Paraver records        #
    #------------------------#

    def trace_send(self, event):
        "Trace a blocking or nonblocking send."
        # Change the task's state.
        irlist = []
        if event.blocking:
            # Blocking send
            irlist.append((1, event.posttime, event.completetime, event.task, 4))
        else:
            # Nonblocking send
            irlist.append((1, event.posttime, event.completetime, event.task, 10))

        # Perform the communication.
        try:
            peer_event = filter(lambda e: e != event, event.clique)[0]
            irlist.append((3, event.posttime, peer_event.completetime, event.task,
                           [peer_event.task, event.msgsize]))
            if self.dimemas_events:
                if event.blocking:
                    d_event = 1
                else:
                    d_event = 3
                irlist.extend([(2, event.posttime, None, event.task, [(50000001, d_event)]),
                               (2, event.completetime, None, event.task, [(50000001, 0)])])
        except IndexError:
            # The event was never matched.
            pass
        return irlist

    def trace_receive(self, event):
        "Trace a blocking or nonblocking receive."
        irlist = []
        if event.blocking:
            # Blocking receive
            irlist.append((1, event.posttime, event.completetime, event.task, 3))
        else:
            # Nonblocking receive
            irlist.append((1, event.posttime, event.completetime, event.task, 11))
        if self.dimemas_events:
            if event.blocking:
                d_event = 2
            else:
                d_event = 4
            irlist.extend([(2, event.posttime, None, event.task, [(50000001, d_event)]),
                           (2, event.completetime, None, event.task, [(50000001, 0)])])
        return irlist

    def trace_wait_all(self, event):
        "Trace waiting until all pending sends and receives are complete."
        irlist = [(1, event.posttime, event.completetime, event.task, 8)]
        if self.dimemas_events:
            irlist.extend([(2, event.posttime, None, event.task, [(50000001, 6)]),
                           (2, event.completetime, None, event.task, [(50000001, 0)])])
        return irlist

    def trace_sync(self, event):
        "Trace synchronizing a set of tasks."
        peerlist_id = self.peergroup2num(event.peers)
        irlist = [(1, event.posttime, event.completetime, event.task, 5),
                  (2, event.posttime, None, event.task, [(2000000, 0)]),
                  (2, event.posttime, None, event.task, [(2000001, peerlist_id)])]
        if self.dimemas_events:
            irlist.extend([(2, event.posttime, None, event.task, [(50000002, 8)]),
                           (2, event.completetime, None, event.task, [(50000002, 8)])])
        return irlist

    def trace_mcast(self, event):
        "Trace the multicasting of values from multiple sources to multiple targets."
        peerlist_id = self.peergroup2num(event.peers)
        irlist = [(1, event.posttime, event.completetime, event.task, 13),
                  (2, event.posttime, None, event.task, [(2000000, event.msgsize)]),
                  (2, event.posttime, None, event.task, [(2000001, peerlist_id)])]
        if self.dimemas_events:
            irlist.extend([(2, event.posttime, None, event.task, [(50000002, 7)]),
                           (2, event.completetime, None, event.task, [(50000002, 7)])])
        return irlist

    def trace_reduce(self, event):
        "Trace the reduction of values from multiple sources to multiple targets."
        peerlist_id = self.peergroup2num(event.peers[0] + event.peers[1])
        irlist = [(1, event.posttime, event.completetime, event.task, 13),
                  (2, event.posttime, None, event.task, [(2000000, event.msgsize)]),
                  (2, event.posttime, None, event.task, [(2000001, peerlist_id)])]
        if self.dimemas_events:
            irlist.extend([(2, event.posttime, None, event.task, [(50000002, 9)]),
                           (2, event.completetime, None, event.task, [(50000002, 9)])])
        return irlist

    def trace_non_comm(self, event):
        "Trace an arbitrary non-communication operation."
        if self.comptime == 0:
            return []
        return [(1, event.posttime, event.completetime, event.task, 1)]
