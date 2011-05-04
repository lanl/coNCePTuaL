#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# Interpreter of coNCePTuaL programs
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# Copyright (C) 2009, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2009).  Los Alamos National Security, LLC.  This software
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

import sys
import os
import string
import re
import math
import types
import random
from ncptl_ast import AST
from ncptl_error import NCPTL_Error
from ncptl_variables import Variables
try:
    import resource
except ImportError:
    # Not every Python installation provides the resource module.
    # Because we need it only to acquire the OS page size, it's not
    # critical; we can safely utilize a default page size.
    pass

# To support the coNCePTuaL GUI (built using Jython) we need to make
# some packages optional.
try:
    # If we can import the java module then we must be running Jython
    # (either the interpreter or the compiler).
    import java
    from gui_patches import *
except ImportError:
    # We're running from ordinary C-based Python.
    from pyncptl import *


class NCPTL_CodeGen:
    thisfile = globals()["__file__"]
    bytes_per_int = long(1.0+math.log(sys.maxint+1.0)/math.log(2.0)) / 8L
    try:
        bytes_per_page = resource.getpagesize()
    except NameError:
        # It shouldn't affect anything too seriously if we simply
        # assume 4KB pages.
        bytes_per_page = 4096
    trivial_nodes = [
        "top_level_stmt_list",
        "header_decl_list",
        "header_decl",
        "version_decl",
        "simple_stmt_list",
        "simple_stmt",
        "let_binding_list",
        "source_task",
        "target_tasks",
        "rel_expr",
        "rel_primary_expr",
        "expr",
        "primary_expr",
        "item_count"]

    #---------------------#
    # Helper class that   #
    # represents an event #
    #---------------------#

    class Event:
        def __init__(self, operation, task, srclines, peers=None, msgsize=None,
                     blocking=1, attributes=None, collective_id=None):
            "Define a new event, initially with no timing information."
            self.operation = operation
            self.task = task
            self.srclines = srclines
            if peers == None:
                self.peers = []
            else:
                self.peers = peers
            self.msgsize = msgsize
            self.blocking = blocking
            if attributes == None:
                self.attributes = []
            else:
                self.attributes = attributes
            self.collective_id = collective_id
            self.posttime = None        # We don't know when we were posted.
            self.completetime = None    # We don't know when we completed.
            self.found_match = 0        # We haven't processed a matching event

        def contents(self):
            "Return a tuple representing our internal state."
            return [self.operation, self.task, self.peers, self.msgsize,
                    self.blocking, self.attributes, self.posttime,
                    self.completetime, self.found_match]


    #---------------------#
    # Helper class that   #
    # represents a list   #
    # of events           #
    #---------------------#

    class EventList:
        def __init__(self, parent):
            "Encapsulate all of the variables that relate to event lists."
            self.parent = parent        # Parent object (of type NCPTL_CodeGen)
            self.errmsg = parent.errmsg # Error-message object
            self.events = []            # The list of events proper
            self.first_incomplete = 0   # Index of first incomplete event
            self.first_unposted = 0     # Index of first unposted event
            self.length = 0             # Number of entries in events[]

        def all_complete(self):
            "Return 1 if all events have completed, 0 otherwise."
            return self.first_incomplete >= self.length

        def push(self, event):
            """
                 Modify an event to use physical instead of virtual
                 ranks then push the event onto the end of the event
                 list.
            """
            self.events.append(event)
            self.length = self.length + 1

        def get_first_incomplete(self):
            "Return the first incomplete event in the event list."
            return self.events[self.first_incomplete]

        def try_posting_all(self):
            "Post as many events as possible."
            while self.first_unposted < self.length:
                event = self.events[self.first_unposted]
                if self.first_unposted == 0:
                    # First event posts immediately.
                    event.posttime = 0
                    self.first_unposted = self.first_unposted + 1
                elif self.events[self.first_unposted-1].completetime != None:
                    # Post only after the previous event completes.
                    prev_event = self.events[self.first_unposted-1]
                    event.posttime = prev_event.completetime + self.complete_post_overhead(prev_event, event)
                    self.first_unposted = self.first_unposted + 1
                else:
                    # We can't complete anything else.
                    break

        def complete(self, peerlist=None, nolat_peerlist=None):
            '''
                 Mark the first incomplete event as completed and
                 return the completion time.  If a list of peer events
                 is given, set the completion time to the maximum of
                 the event\'s completion time and the post time +
                 message latency of each of the peer events.  If a
                 list of "no latency" peer events is specified, do the
                 same thing but using the maximum of the completion
                 times.
            '''
            self.try_posting_all()
            this_ev = self.events[self.first_incomplete]
            if this_ev.posttime == None:
                self.errmsg.error_internal("Task %d, event %d completed before being posted" %
                                           (this_ev.task, self.first_incomplete))
            newtime = this_ev.posttime + self.post_complete_overhead(this_ev)
            if peerlist != None:
                # PEERLIST represents senders.
                for peer_ev in peerlist:
                    if peer_ev.posttime == None:
                        self.errmsg.error_internal("An event on task %d completed before being posted" % peer_ev.task)
                    newtime = max(newtime, peer_ev.posttime + self.message_latency(peer_ev))
            if nolat_peerlist != None:
                # NOLAT_PEERLIST represents equals.
                for peer_ev in nolat_peerlist:
                    if peer_ev.posttime == None:
                        self.errmsg.error_internal("An event on task %d completed before being posted" % peer_ev.task)
                    newtime = max(newtime, peer_ev.posttime + self.post_complete_overhead(peer_ev))
            this_ev.completetime = newtime
            self.first_incomplete = self.first_incomplete + 1
            return newtime

        def post_complete_overhead(self, event):
            "Return the overhead between posting and completing an event."
            return 0

        def complete_post_overhead(self, prev_ev, this_ev):
            "Return the overhead between completing an event and posting the next event."
            # Receiving a blocking message takes no time; everything else does.
            if prev_ev.operation == "RECEIVE" and prev_ev.blocking:
                return 0
            elif prev_ev.operation == "NEWSTMT":
                return 0
            else:
                return 1

        def message_latency(self, event):
            "Return the message latency for a given event."
            # Determine the set of source tasks and the set of target tasks.
            if event.operation == "REDUCE":
                # REDUCE events -- peer list contains the source and
                # target lists
                source_tasks, target_tasks = event.peers
            else:
                # Other communication events -- peer list contains
                # only the targets.
                source_tasks = [event.task]
                target_tasks = event.peers

            # Compute the maximum latency from any source to any
            # target and return that.
            latency = -1
            latency_list = self.parent.latency_list
            for source in source_tasks:
                for target in target_tasks:
                    if source == target:
                        latency = max(latency, latency_list[0][1])
                    else:
                        for taskcount, newlatency in latency_list:
                            if source/taskcount == target/taskcount:
                                # We're guaranteed to reach this point
                                # because we added (numtasks, _) to the
                                # end of latency_list.
                                latency = max(latency, newlatency)
                                break
            return latency

        def find_unmatched(self):
            "Return a list of events with no matching event."
            return filter(lambda ev: not ev.found_match, self.events)

        def delete_unposted(self):
            """
                 Delete from the first unposted event onwards (invoked
                 when a task is blocked on account of deadlock).
            """
            del self.events[self.first_unposted:]
            self.length = len(self.events)


    #----------------------#
    # Helper class that    #
    # represents a message #
    # queue                #
    #----------------------#

    class MessageQueue:
        def __init__(self, errmsg):
            "Initialize a message queue."
            self.errmsg = errmsg        # Error-message object
            self.queues = {}            # Map from source task to message size to an event queue

        def push(self, event):
            "Push a new event onto a message queue."
            source_task = event.task
            message_size = event.msgsize
            if not self.queues.has_key(source_task):
                self.queues[source_task] = {}
            if not self.queues[source_task].has_key(message_size):
                self.queues[source_task][message_size] = []
            self.queues[source_task][message_size].append(event)

        def pop_match(self, event):
            "Pop the first matching event from the queue or return None."
            result = self.peek_match(event)
            source_task = event.peers[0]
            message_size = event.msgsize
            if result != None:
                self.queues[source_task][message_size].pop(0)
                result.found_match = 1
            return result

        def unpop_match(self, event, matched_event):
            "Reinsert a previously popped event into the queue."
            source_task = event.peers[0]
            message_size = event.msgsize
            self.queues[source_task][message_size].insert(0, matched_event)

        def peek_match(self, event):
            "Return the first matching event from the queue or None."
            source_task = event.peers[0]
            message_size = event.msgsize
            try:
                return self.queues[source_task][message_size][0]
            except KeyError:
                return None
            except IndexError:
                return None


    #---------------------#
    # Exported functions  #
    # (called from the    #
    # compiler front end) #
    #---------------------#

    def __init__(self, options=[], numtasks=1L):
        "Initialize the coNCePTuaL interpreter."
        self.errmsg = NCPTL_Error()     # Placeholder until generate is called
        self.scopes = []                # Variable scopes (innermost first)
        self.numtasks = numtasks        # Number of tasks to simulate
        self.cmdline = []               # Command-line passed to the backend
        self.options = []               # Supported command-line options
        self.context = "int"            # Evaluation context (int or float)
        self.next_byte = {}             # Map from touch node to next byte to touch
        self.logstate = {}              # Map from a physical rank to log state
        self.suppress_output = 0        # 1=temporarily ignore OUTPUTS and LOGS
        self.program_uses_log_file = 0  # 1=LOGS or COMPUTES AGGREGATES was used
        self.program_can_use_log_file = 1   # 0=supress logging; 1=allow it
        self.logcolumn = 0L             # Current "column" in the log file
        self.for_time_reps = 3L         # Number of repetitions to use for FOR <time>
        self.random_seed = ncptl_seed_random_task(0L, 0L)   # Seed for the RNG
        self.mcastsync = 0L             # 1=synchronize after a multicast
        self.latency_list = [(1,1)]     # Hierarchy of message latencies
        self.timing_flag = ncptl_allocate_timing_flag()  # Used by FOR <time>
        self.type2method = {}           # Map from a node type to a method that can handle it
        self.stuck_tasks = {}           # Set of deadlocked tasks
        self.next_collective_id = 1000000   # Next available unique ID for a collective
        self.backend_name = "interpret"
        self.backend_desc = "coNCePTuaL interpreter"

        # Process the "--tasks" argument but store all others.  Note
        # that we do this "manually" without relying on
        # ncptl_parse_command_line() because we need the number of
        # tasks before we begin interpreting.
        arg = 0
        while arg < len(options):
            # Search for "-T#", "-T #" and "--tasks=#".
            taskstr = ""
            if options[arg] == "-T" and arg+1 < len(options):
                taskstr = options[arg+1]
                argname = "-T"
                arg = arg + 1
            else:
                arg_match = re.match(r'(--tasks=)(.*)', options[arg]) or re.match(r'(-T)(.*)', options[arg])
                if arg_match:
                    argname = arg_match.group(1)
                    taskstr = arg_match.group(2)

            # Verify that the task count is numeric.
            if taskstr:
                try:
                    self.numtasks = long(taskstr)
                except ValueError:
                    self.errmsg.error_fatal('%s expected a number but received "%s"' %
                                            (argname, taskstr),
                                            filename=self.backend_name)
                taskstr = ""
            else:
                self.cmdline.append(options[arg])
            arg = arg + 1

        # Point each method name in the trivial_nodes list to the
        # n_trivial_node method.
        for mname in self.trivial_nodes:
            setattr(self, "n_" + mname, self.n_trivial_node)

    def clear_events(self):
        """Restart the interpreter by clearing all of top-level state
        (needed by the coNCePTuaL GUI)."""
        self.errmsg = NCPTL_Error("internal")
        self.eventlist = map(lambda self: self.EventList(self), [self] * int(self.numtasks))
        self.msgqueue = map(lambda self: self.MessageQueue(self.errmsg), [self] * int(self.numtasks))
        self.pendingevents = map(lambda h: [], [None] * int(self.numtasks))
        self.timer_start = [0] * int(self.numtasks)
        self.counters = []
        self.counter_stack = map(lambda t: [], range(0, self.numtasks))

    def generate(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        "Interpret an AST."
        self.generate_initialize(ast, filesource, filetarget, sourcecode)
        self.process_node(ast)         # Prefix traversal (roughly)
        self.generate_finalize(ast, filesource, sourcecode)
        return []

    def compile_only(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        """
             Do nothing unless an output file was specified, in which
             case we dump event state to that file.
        """
        if outfilename != "-":
            if verbose:
                sys.stderr.write("# Dumping final event state to %s ...\n" % outfilename)
            self.dump_event_lists(outfilename)
        else:
            if verbose:
                sys.stderr.write("#    [Nothing to do here]\n")
        return outfilename

    def compile_and_link(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Pass control to compile_only, as linking is not meaningful here."
        self.compile_only(progfilename, codelines, outfilename, verbose, keepints)
        return outfilename


    #------------------#
    # Internal utility #
    # functions        #
    #------------------#

    def set_log_file_status(self, enable):
        "Force log-file usage on or off (intended to be called by derived classes)."
        if enable:
            self.program_uses_log_file = 1
            self.program_can_use_log_file = 1
        else:
            self.program_can_use_log_file = 0
            self.options = filter(lambda ev: ev[2] != "logfile", self.options)

    def dump_event_lists(self, outfilename):
        "Write an easy-to-parse list of events to a file."
        try:
            outfile = open(outfilename, "w")
            for task in range(0, self.numtasks):
                for event in self.eventlist[task].events:
                    if event.completetime == None:
                        outfile.write(self.format_plurals("Task %d posted %C %s at time %d but never completed it\n",
                                                          1, (task, event.operation, event.posttime)))
                    else:
                        outfile.write(self.format_plurals("Task %d posted %C %s at time %d and completed it at time %d\n",
                                                      1, (task, event.operation, event.posttime, event.completetime)))
            outfile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("Unable to produce %s (%s)" % (outfilename, strerror),
                                    filename=self.backend_name)

    def parse_latency_hierarchy(self, taskstr):
        """Parse a hierarchy of task counts and latencies into a list
        of {tasks, latency} tuples."""
        tasks_cost_list = []
        prev_tasks = 1
        prev_latency = 0
        found_ellipsis = 0
        numtasks = self.numtasks
        taskspec_re = re.compile(r'^(\d+)(:\d+)?$')

        # Process each comma-separated task:latency pair in turn.
        for taskspec in string.split(re.sub(r'\s+', "",
                                            string.replace(taskstr, "tasks", str(numtasks))),
                                     ","):
            # Handle a trailing ellipsis.
            if found_ellipsis:
                self.errmsg.error_fatal('"..." may appear only at the end of a task hierarchy',
                                        filename=self.backend_name)
            if taskspec == "...":
                # Repeat the previous task:latency pair until we cover all
                # numtasks tasks.
                found_ellipsis = 1
                if tasks_cost_list == []:
                    self.errmsg.error_fatal('"..." may not appear at the beginning of a task hierarchy',
                                            filename=self.backend_name)
                while prev_tasks*task_factor < numtasks:
                    prev_tasks = prev_tasks * task_factor;
                    prev_latency = prev_latency + latency_delta
                    tasks_cost_list.append((prev_tasks, prev_latency))
                continue

            # Handle the common case, a task factor followed by an
            # optional latency delta.
            taskspec_match = taskspec_re.search(taskspec)
            if not taskspec_match:
                self.errmsg.error_fatal('Unable to parse "%s" (in hierarchy "%s")' % (taskspec, taskstr),
                                        filename=self.backend_name)
            task_factor = int(taskspec_match.group(1))
            try:
                latency_delta = int(taskspec_match.group(2)[1:])
            except TypeError:
                latency_delta = 1
            if task_factor < 1:
                self.errmsg.error_fatal('Task factor must be positive in "%s"' % taskspec,
                                        filename=self.backend_name)
            prev_tasks = prev_tasks * task_factor;
            prev_latency = prev_latency + latency_delta
            tasks_cost_list.append((prev_tasks, prev_latency))

        # Append a catch-all case if necessary then return the final list.
        if tasks_cost_list[-1][0] < numtasks:
            tasks_cost_list.append((numtasks, tasks_cost_list[-1][1]+1))
        return tasks_cost_list

    def generate_initialize(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        "Perform all of the initialization needed by the generate method."

        # Define various parameters that depend upon filesource,
        # sourcecode, and/or numtasks.
        self.filesource = filesource           # Input file
        self.sourcecode = sourcecode           # coNCePTuaL source code
        self.errmsg = NCPTL_Error(filesource)  # Error-handling methods
        self.eventlist = map(lambda self: self.EventList(self),    # Map from task to event list
                             [self] * int(self.numtasks))
        self.msgqueue = map(lambda self: self.MessageQueue(self.errmsg),  # Map from source task to message size to event list
                            [self] * int(self.numtasks))
        self.pendingevents = map(lambda h: [], # Asynchronous events not yet waited for
                                 [None] * int(self.numtasks))
        self.timer_start = [0] * int(self.numtasks)   # Logical time at which the timer started
        self.counters = []                     # Per-task counters exposed to programs
        for task in range(0, self.numtasks):
            self.counters.append({})
            for varname in Variables.variables.keys():
                self.counters[task][varname] = 0L
            self.counters[task]["num_tasks"] = self.numtasks
        self.counter_stack = map(lambda t: [], range(0, self.numtasks))   # Stack of counter values
        if self.filesource == "<command line>":
            self.filename = "a.out"
        else:
            self.filename = self.filesource
        if filetarget == "-":
            # If no target filename was specified, derive the log
            # filename template from the source filename.
            filebase = re.sub(r'\.ncptl$', "", self.filename)
        else:
            # If a target filename was specified, derive the log
            # filename template from that.
            filebase = os.path.splitext(filetarget)[0]
        self.logfiletemplate = "%s-%%p.log" % os.path.basename(filebase)
        self.options.extend([
            ["numtasks", "Number of tasks to use", "tasks", "T", 1L],
            ["mcastsync",
             "Perform an implicit synchronization after a multicast (0=no; 1=yes)",
             "mcastsync", "M", 0L],
            ["latency_list",
             "Latency hierarchy as a comma-separated list of task_factor:latency_delta pairs",
             "hierarchy", "H", "tasks:1"],
            ["random_seed", "Seed for the random-number generator",
             "seed", "S", self.random_seed],
            ["logfiletmpl", "Log-file template", "logfile",
             "L", self.logfiletemplate]])

    def generate_finalize(self, ast, filesource='<stdin>', sourcecode=None):
        "Perform all of the finalization needed by the generate method."

        # Process all events in the event lists.
        self.process_all_events()

        # Cleanly shut down coNCePTuaL.
        if self.program_uses_log_file:
            for logstate in self.logstate.values():
                ncptl_log_commit_data(logstate)
                ncptl_log_write_epilogue(logstate)
                ncptl_log_close(logstate)
        ncptl_finalize()

    def invoke_hook(self, hookname, localvars, alternatepy=None, alternate=None):
        """
           Invoke a hook method if it exists, passing it a dictionary
           of the current scope's local variables.  The hook
           function's required return type varies from hook to hook.
           If the HOOKNAME method does not exist, evaluate ALTERNATEPY
           and return the result.  If ALTERNATEPY is not defined,
           return ALTERNATE.
        """
        hookmethod = getattr(self, hookname, None)
        if hookmethod:
            hookoutput = hookmethod(localvars)
            if hookoutput:
                return hookoutput
            else:
                return []
        elif alternatepy:
            return alternatepy(localvars)
        else:
            return alternate

    def process_node(self, node):
        "Given a node, invoke a method that knows how to process it."
        try:
            return self.type2method[node.type](node)
        except KeyError:
            methodname = "n_" + node.type
            methodcode = getattr(self, methodname, self.n_undefined)
            self.type2method[node.type] = methodcode
            return methodcode(node)

    def apply_binary_function(self, ffunc, node, ifunc=None):
        """
             Acquire a node's two children as either longs or floats
             depending upon the value of self.context.  Apply either
             IFUNC or FFUNC, as appropriate.  If FFUNC fails, return a
             tuple consisting of FFUNC and the two operands.  IFUNC
             defaults to FFUNC.
        """
        if len(node.kids) != 2:
            self.errmsg.error_internal("Node %s has %d children, not 2" %
                                       (node.type, len(node.kids)))
        if self.context == "int":
            value1 = long(self.process_node(node.kids[0]))
            value2 = long(self.process_node(node.kids[1]))
            if ifunc == None:
                return ffunc(value1, value2)
            else:
                return ifunc(value1, value2)
        else:
            value1 = self.process_node(node.kids[0])
            value2 = self.process_node(node.kids[1])
            try:
                return ffunc(float(value1), float(value2))
            except TypeError:
                return (ffunc, value1, value2)

    def eval_lazy_expr(self, frag, wanttype=types.LongType):
        """Evaluate strings, longs, floats, and futures (really
        tuples) in a given type context."""
        conversion = {
            (types.StringType, types.StringType) : lambda frag: frag,
            (types.LongType,   types.StringType) : lambda frag: str(frag),
            (types.FloatType,  types.StringType) : lambda frag: "%.10lg" % frag,
            (types.StringType, types.LongType)   : lambda frag: long(frag),
            (types.LongType,   types.LongType)   : lambda frag: frag,
            (types.FloatType,  types.LongType)   : lambda frag: long(frag),
            (types.StringType, types.FloatType)  : lambda frag: float(frag),
            (types.LongType,   types.FloatType)  : lambda frag: float(frag),
            (types.FloatType,  types.FloatType)  : lambda frag: frag}
        try:
            # Simple types
            return conversion[type(frag), wanttype](frag)
        except KeyError:
            if type(frag) == types.TupleType:
                # Future
                func = frag[0]
                arglist = []
                for arg in frag[1:]:
                    arglist.append(self.eval_lazy_expr(arg, wanttype))
                return self.eval_lazy_expr(apply(func, arglist), wanttype)
        except:
            pass
        self.errmsg.error_internal('Unknown expression type %s for expression "%s"' % (str(type(frag)), frag))

    def initialize_log_file(self, physrank):
        """Create a set of log files and write a prologue to each of.
        Note that repeated calls will have no adverse effect."""
        if self.logstate.has_key(physrank):
            return
        if not self.program_can_use_log_file:
            return
        ncptl_log_add_comment("Python version", re.sub(r'\s+', " ", sys.version))
        for rank in range(self.numtasks):
            self.logstate[rank] = ncptl_log_open(self.logfiletemplate, rank)
            ncptl_log_write_prologue(self.logstate[rank],
                                     sys.executable, self.logfile_uuid,
                                     self.backend_name, self.backend_desc, self.numtasks,
                                     self.options, len(self.options),
                                     string.split(string.rstrip(self.sourcecode), "\n"))
        self.program_uses_log_file = 1

    def convert_to_tuple_list(self, messagelist):
        """
             Convert all entries in a list of strings, numbers, and
             (type, value) pairs to (type, value) pairs.
        """
        result = []
        for msgfrag in messagelist:
            if type(msgfrag) == types.StringType:
                result.append(("STRING", msgfrag))
            elif type(msgfrag) == types.FloatType:
                result.append(("NUMBER", msgfrag))
            elif type(msgfrag) == types.TupleType:
                result.append(msgfrag)
            else:
                self.errmsg.error_internal('Unexpected message fragment "%s"' % msgfrag)
        return result

    def format_plurals(self, format, number, args):
        "Wrap the % operator with special cases for plurals."
        if number == 1:
            format = string.replace(format, "%S", "")
            format = string.replace(format, "%W", "was")
            format = re.sub(r'%C(?= [AEIOUaeiou])', "an", format)
            format = string.replace(format, "%C", "a")
        else:
            format = string.replace(format, "%S", "s")
            format = string.replace(format, "%W", "were")
            format = string.replace(format, "%C", str(number))
        return format % args

    def update_counters(self, event, operation=None):
        "Update various counter variables after an event completes."
        if event.suppressed:
            return
        if operation == None:
            operation = event.operation
        counters = self.counters[event.task]
        if operation == "SEND":
            counters["msgs_sent"] = counters["msgs_sent"] + 1
            counters["bytes_sent"] = counters["bytes_sent"] + event.msgsize
        elif operation == "RECEIVE":
            counters["msgs_received"] = counters["msgs_received"] + 1
            counters["bytes_received"] = counters["bytes_received"] + event.msgsize
        else:
            self.errmsg.error_internal('Event type "%s" should have been either "SEND" or "RECEIVE"' % operation)
        counters["total_bytes"] = counters["bytes_sent"] + counters["bytes_received"]
        counters["total_msgs"] = counters["msgs_sent"] + counters["msgs_received"]

    def _virtual_to_physical(self, vtask):
        "Map a virtual task ID to a physical processor number."
        if type(vtask) in (types.IntType, types.LongType):
            return int(ncptl_virtual_to_physical(self.procmap, vtask))
        elif type(vtask) in (types.ListType, types.TupleType):
            ptasks = map(lambda t, self=self: self._virtual_to_physical(t), vtask)
            if type(vtask) == types.TupleType:
                ptasks = tuple(ptasks)
            return ptasks

    def push_event(self, event):
            """
                 Modify an event to use physical instead of virtual
                 ranks and introduce a suppression flag then push the
                 event onto the end of the appropriate event list.
            """
            physrank = self._virtual_to_physical(event.task)
            event.task = physrank
            event.peers = self._virtual_to_physical(event.peers)
            event.suppressed = self.suppress_output
            self.eventlist[physrank].push(event)


    #---------------------------------#
    # AST interpretation: relational  #
    # expressions (return true/false) #
    #---------------------------------#

    def n_rel_disj_expr(self, node):
        "Return true if any of our children is true."
        if len(node.kids) == 1:
            return self.n_trivial_node(node)
        else:
            value1 = long(self.process_node(node.kids[0]))
            if value1:
                return 1L
            else:
                return long(self.process_node(node.kids[1]))

    def n_rel_conj_expr(self, node):
        "Return true only if all of our children are true."
        if len(node.kids) == 1:
            return self.n_trivial_node(node)
        else:
            value1 = long(self.process_node(node.kids[0]))
            if value1:
                return long(self.process_node(node.kids[1]))
            else:
                return 0L

    def n_eq_expr(self, node):
        "Compare our children's values."
        attr2func = {
            "op_eq": lambda a, b: a==b,
            "op_ne": lambda a, b: a!=b,
            "op_gt": lambda a, b: a>b,
            "op_lt": lambda a, b: a<b,
            "op_ge": lambda a, b: a>=b,
            "op_le": lambda a, b: a<=b}
        try:
            return self.apply_binary_function(attr2func[node.attr], node)
        except KeyError:
            pass
        if node.attr == "op_divides":
            ifunc = lambda a, b: ncptl_func_modulo(b, a) == 0L
            ffunc = lambda a, b: long(ncptl_dfunc_modulo(b, a)) == 0L
            return self.apply_binary_function(ffunc, node, ifunc)
        elif node.attr == "op_odd":
            value = long(self.process_node(node.kids[0]))
            return value % 2 != 0
        elif node.attr == "op_even":
            value = long(self.process_node(node.kids[0]))
            return value % 2 == 0
        elif node.attr == "op_in_range":
            number = self.process_node(node.kids[0])
            bounds = [self.process_node(node.kids[1]), self.process_node(node.kids[2])]
            bounds.sort()
            return bounds[0] <= number <= bounds[1]
        elif node.attr == "op_not_in_range":
            number = self.process_node(node.kids[0])
            bounds = [self.process_node(node.kids[1]), self.process_node(node.kids[2])]
            bounds.sort()
            return not (bounds[0] <= number <= bounds[1])
        elif node.attr == "op_in_range_list":
            expression = self.process_node(node.kids[0])
            rangelists = self.process_node(node.kids[1])
            for rlist in rangelists:
                if expression in rlist:
                    return 1
            return 0
        elif node.attr == "op_not_in_range_list":
            expression = self.process_node(node.kids[0])
            rangelists = self.process_node(node.kids[1])
            for rlist in rangelists:
                if expression in rlist:
                    return 0
            return 1
        else:
            self.errmsg.error_internal('Unknown eq_expr "%s"' % node.attr)


    #--------------------------------#
    # AST interpretation: arithmetic #
    # expressions (return numbers)   #
    #--------------------------------#

    def n_ifelse_expr(self, node):
        "Return one of two expressions based on a condition."
        if len(node.kids) == 3:
            value1 = self.process_node(node.kids[0])
            value2 = self.process_node(node.kids[2])
            condition = self.process_node(node.kids[1])
            if condition:
                return value1
            else:
                return value2
        else:
            return self.n_trivial_node(node)

    def n_add_expr(self, node):
        "Combine two expressions using an additive operator."
        if len(node.kids) == 1:
            return self.n_trivial_node(node)
        elif node.attr == "op_plus":
            return self.apply_binary_function((lambda a, b: a+b), node)
        elif node.attr == "op_minus":
            return self.apply_binary_function((lambda a, b: a-b), node)
        elif node.attr == "op_xor":
            ifunc = lambda a, b: a ^ b
            ffunc = lambda a, b: float(long(a) ^ long(b))
            return self.apply_binary_function(ffunc, node, ifunc)
        elif node.attr == "op_or":
            ifunc = lambda a, b: a | b
            ffunc = lambda a, b: float(long(a) | long(b))
            return self.apply_binary_function(ffunc, node, ifunc)
        else:
            self.errmsg.error_internal('Unknown add_expr "%s"' % node.attr)

    def n_mult_expr(self, node):
        "Combine two expressions using a multiplicative operator."
        if len(node.kids) == 1:
            return self.n_trivial_node(node)
        elif node.attr == "op_mult":
            return self.apply_binary_function((lambda a, b: a*b), node)
        elif node.attr == "op_div":
            def safe_divide(value1, value2, self=self, node=node):
                "Divide two numbers but report divide-by-zero errors."
                if self.context == "int":
                    numerator = self.eval_lazy_expr(value1)
                    denominator = self.eval_lazy_expr(value2)
                else:
                    numerator = self.eval_lazy_expr(value1, types.FloatType)
                    denominator = self.eval_lazy_expr(value2, types.FloatType)
                try:
                    return numerator / denominator
                except ZeroDivisionError:
                    self.errmsg.error_fatal("Divide-by-zero error (%s/%s)" % (`numerator`, `denominator`),
                                            lineno0=node.lineno0, lineno1=node.lineno1)
            return self.apply_binary_function(safe_divide, node)
        elif node.attr == "op_mod":
            return self.apply_binary_function(ncptl_dfunc_modulo, node, ncptl_func_modulo)
        elif node.attr == "op_shr":
            ffunc = lambda n, b: ncptl_dfunc_shift_left(n, -b)
            ifunc = lambda n, b: ncptl_func_shift_left(n, -b)
            return self.apply_binary_function(ffunc, node, ifunc)
        elif node.attr == "op_shl":
            return self.apply_binary_function(ncptl_dfunc_shift_left, node, ncptl_func_shift_left)
        elif node.attr == "op_and":
            ifunc = lambda a, b: a & b
            ffunc = lambda a, b: float(long(a) & long(b))
            return self.apply_binary_function(ffunc, node, ifunc)
        else:
            self.errmsg.error_internal('Unknown mult_expr "%s"' % node.attr)

    def n_unary_expr(self, node):
        "Apply a unary operator to a expression."
        # Convert our child to a number if possible.
        posvalue = self.n_trivial_node(node)
        if self.context == "int":
            posvalue = long(posvalue)
        else:
            try:
                posvalue = float(posvalue)
            except TypeError:
                pass

        # Perform the requested unary operation.
        if node.attr == None:
            return posvalue
        elif node.attr == "op_pos":
            return posvalue
        elif node.attr == "op_neg":
            try:
                return -posvalue
            except TypeError:
                return (lambda v: -v, posvalue)
        elif node.attr == "op_not":
            try:
                return ~long(posvalue)
            except TypeError:
                return (lambda v: ~long(v), posvalue)
        else:
            self.errmsg.error_internal('Unknown unary_expr "%s"' % node.attr)

    def n_power_expr(self, node):
        "Combine two expressions using a power operator."
        if len(node.kids) == 1:
            return self.n_trivial_node(node)
        else:
            return self.apply_binary_function(ncptl_dfunc_power, node, ncptl_func_power)

    def n_integer(self, node):
        "Return a constant integer."
        if self.context == "int":
            return long(node.attr)
        else:
            return float(node.attr)

    def n_ident(self, node):
        "Return the current value of an identifier."

        # Predefined variables are returned as a tuple to be evaluated
        # later.  The only exception is num_tasks because it's usable
        # in more contexts than the others.
        if node.attr == "num_tasks":
            if self.context == "int":
                return long(self.numtasks)
            else:
                return float(self.numtasks)
        if Variables.variables.has_key(node.attr):
            return (lambda self=self, v=node.attr: float(self.counters[self.physrank][v]),)

        # Now handle the general case -- user-defined variables.
        for frame in self.scopes:
            try:
                if self.context == "int":
                    return frame[node.attr]
                else:
                    return float(frame[node.attr])
            except KeyError:
                pass
        self.errmsg.error_fatal("Variable %s is not defined" % node.attr,
                                lineno0=node.lineno0, lineno1=node.lineno1)

    def n_real(self, node):
        "Evaluate an expression in floating-point context."
        prevcontext = self.context
        self.context = "float"
        result = self.process_node(node.kids[0])
        if prevcontext == "int":
            result = round(result)
        self.context = prevcontext
        return result

    def n_func_call(self, node):
        "Invoke a run-time library function and return the result."

        # Acquire the function name and parameters.
        funcname = node.attr
        funcparams = self.process_node(node.kids[0])
        if type(funcparams) != types.ListType:
            funcparams = [funcparams]
        num_params = len(funcparams)
        have_lazy_param = filter(lambda p: type(p)==types.TupleType, funcparams) != []

        # MIN and MAX are special in that they take an arbitrary
        # number of arguments.  Because SWIG doesn't yet deal with
        # variable-length argument lists we implement MIN and MAX
        # directly with Python.
        if funcname in ["MIN", "MAX"]:
            funccode = eval(string.lower(funcname))
            if have_lazy_param:
                return tuple([funccode] + funcparams)
            else:
                return apply(funccode, funcparams)

        # Ensure we have the correct number of arguments.
        function_arguments = {
            "ABS":              [1],
            "BITS":             [1],
            "CBRT":             [1],
            "CEILING":          [1],
            "FACTOR10":         [1],
            "FLOOR":            [1],
            "LOG10":            [1],
            "ROUND":            [1],
            "SQRT":             [1],
            "ROOT":             [2],
            "RANDOM_UNIFORM":   [2],
            "RANDOM_GAUSSIAN":  [2],
            "RANDOM_POISSON":   [1],
            "TREE_PARENT":      [1, 2],
            "TREE_CHILD":       [2, 3],
            "MESH_NEIGHBOR":    [3, 5, 7],
            "TORUS_NEIGHBOR":   [3, 5, 7],
            "MESH_COORDINATE":  [3, 4, 5],
            "TORUS_COORDINATE": [3, 4, 5],
            "KNOMIAL_PARENT":   [1, 2, 3],
            "KNOMIAL_CHILD":    [2, 3, 4],
            "KNOMIAL_CHILDREN": [1, 2, 3]
        }
        try:
            valid_num_params = function_arguments[funcname]
            if num_params not in valid_num_params:
                if len(valid_num_params) == 1:
                    expected_args = "%d argument(s)" % valid_num_params
                else:
                    expected_args = string.join(map(str, valid_num_params[:-1]), ", ") + \
                                    " or %d arguments" % valid_num_params[-1]
                self.errmsg.error_fatal("%s expects %s but was given %d" %
                                        (funcname, expected_args, num_params),
                                        lineno0=node.lineno0, lineno1=node.lineno1)
        except KeyError:
            self.errmsg.error_internal("unknown number of arguments to %s" % funcname)

        # All of the mesh and torus neighbor functions map to the same
        # library call.  Patch the argument list accordingly.
        if funcname=="MESH_NEIGHBOR" or funcname=="TORUS_NEIGHBOR":
            gtask = funcparams[0]
            gtorus = long(funcname=="TORUS_NEIGHBOR")
            gwidth = funcparams[1]
            gheight = 1L
            gdepth = 1L
            gdeltax = funcparams[2]
            gdeltay = 0L
            gdeltaz = 0L
            if num_params >= 5:
                gheight = funcparams[3]
                gdeltay = funcparams[4]
            if num_params >= 7:
                gdepth = funcparams[5]
                gdeltaz = funcparams[6]
            funcname = "GRID_NEIGHBOR"
            funcparams = [gtask, gtorus,
                         gwidth, gheight, gdepth,
                         gdeltax, gdeltay, gdeltaz]
        # All of the mesh and torus coordinate functions map to the same
        # library call.  Patch the argument list accordingly.
        elif funcname=="MESH_COORDINATE" or funcname=="TORUS_COORDINATE":
            gtask = funcparams[0]
            gcoord = funcparams[1]
            gwidth = funcparams[2]
            gheight = 1L
            gdepth = 1L
            if num_params >= 4:
                gheight = funcparams[3]
            if num_params >= 5:
                gdepth = funcparams[4]
            funcname = "GRID_COORD"
            funcparams = [gtask, gcoord,
                         gwidth, gheight, gdepth]
        # Tree arity defaults to 2.
        elif funcname=="TREE_PARENT" or funcname=="TREE_CHILD":
            if num_params == valid_num_params[0]:
                funcparams.append(2L)
        # k defaults to 2 in k-nomial tree and the number of tasks
        # defaults to num_tasks.
        elif funcname[:8] == "KNOMIAL_":
            if num_params < valid_num_params[-2]:
                funcparams.append(2L)
            if num_params < valid_num_params[-1]:
                funcparams.append(self.numtasks)
            if funcname == "KNOMIAL_CHILD":
                funcparams.append(0L)
            elif funcname == "KNOMIAL_CHILDREN":
                funcparams.insert(1, 0L)
                funcparams.append(1L)
                funcname = "KNOMIAL_CHILD"

        # Evaluate the function and return the result.
        funcname = string.lower(funcname)
        if have_lazy_param:
            # Lazy parameters are always evaluated in floating-point context.
            funcname = "ncptl_dfunc_" + funcname
            return tuple([globals()[funcname]] + funcparams)
        else:
            if self.context == "int":
                funcname = "ncptl_func_" + funcname
            else:
                funcname = "ncptl_dfunc_" + funcname
            return apply(globals()[funcname], funcparams)

    def n_item_size(self, node):
        "Return the desired size of a buffer."
        if len(node.kids) == 0:
            return 0L
        elif node.kids[0].type == "expr":
            node.kids[1].basevalue = self.process_node(node.kids[0])
            return self.process_node(node.kids[1])
        else:
            return self.process_node(node.kids[0])

    def n_data_type(self, node):
        "Return the number of bytes represented by a textual description."
        data_types = {
            "default"     : 0L,
            "bytes"       : 1L,
            "halfwords"   : 2L,
            "words"       : 4L,
            "integers"    : self.bytes_per_int,
            "doublewords" : 8L,
            "quadwords"   : 16L,
            "pages"       : self.bytes_per_page
        }
        try:
            return data_types[node.attr]
        except KeyError:
            self.errmsg.error_internal('unknown message alignment "%s"' % node.attr)

    def n_byte_count(self, node):
        """
             Return a number of bytes by multiplying an expression by
             a textual multiplier.
        """
        node.kids[1].basevalue = self.process_node(node.kids[0])
        return self.process_node(node.kids[1])

    def n_data_multiplier(self, node):
        """
             Convert a textual multiplier to a number of bytes.  We
             assume our parent has assigned node.basevalue to be the
             number to which the multiplier applies.
        """
        value = node.basevalue

        # Make a special case for bits because of rounding issues.
        if node.attr == "bits":
            if value % 8 == 0:
                return value/8L
            else:
                return value/8L + 1

        # Normally, we just multiply by a given number.
        kilo = 1024L
        multipliers = {
          "bytes"       : 1L,
          "kilobyte"    : kilo,
          "megabyte"    : kilo**2,
          "gigabyte"    : kilo**3,
          "halfwords"   : 2L,
          "words"       : 4L,
          "integers"    : self.bytes_per_int,
          "doublewords" : 8L,
          "quadwords"   : 16L,
          "pages"       : self.bytes_per_page
        }
        try:
            return value * multipliers[node.attr]
        except KeyError:
            self.errmsg.error_internal('Unknown data multiplier "%s"' % node.attr)

    def n_time_unit(self, node):
        "Convert from a textual time unit to a number of microseconds."
        time_map = {
            "microseconds" : 1L,
            "milliseconds" : 1000L,
            "seconds"      : 1000L*1000L,
            "minutes"      : 1000L*1000L*60L,
            "hours"        : 1000L*1000L*60L*60L,
            "days"         : 1000L*1000L*60L*60L*24L,
        }
        try:
            return time_map[node.attr]
        except KeyError:
            self.errmsg.error_internal('unknown time unit "%s"' % node.attr)

    def n_aggregate_func(self, node):
        "Return the number of an aggregate function."
        return long(eval("NCPTL_FUNC_" + string.upper(node.attr)))

    def n_an(self, node):
        "Return the constant 1."
        return 1L

    def n_message_alignment(self, node):
        """
             Return the desired message alignment (or 0 for
             any alignment).
        """
        try:
            return self.process_node(node.kids[0])
        except IndexError:
            return 0L

    def n_touch_repeat_count(self, node):
        "Return the number of times a memory region should be touched."
        try:
            # Repeat count was specified explicitly.
            return self.process_node(node.kids[0])
        except IndexError:
            # Implicit repeat count defaults to 1.
            return 1L


    #-----------------------------------#
    # AST interpretation: miscellaneous #
    # expressions (return a value of    #
    # some type or other)               #
    #-----------------------------------#

    def n_expr_list(self, node):
        "Return a list of (evaluated) expressions."
        return map(self.process_node, node.kids)

    def n_task_expr(self, node):
        "Return a variable name and list of valid tasks to bind to it."
        if node.attr == "task_all":
            # ALL TASKS or ALL TASKS <var>
            if node.kids == []:
                varname = None
            else:
                varname = node.kids[0].attr
            tasklist = range(0L, self.numtasks)
        elif node.attr == "expr":
            # TASK <expr>
            varname = None
            tasklist = []
            taskexpr = self.process_node(node.kids[0])
            if 0 <= taskexpr < self.numtasks:
                tasklist = [taskexpr]
        elif node.attr == "such_that":
            # TASK <var> SUCH THAT <rel_expr>
            varname, tasklist = self.process_node(node.kids[0])
        elif node.attr == "all_others":
            # ALL OTHER TASKS
            varname = None
            tasklist = range(0, self.virtrank) + range(self.virtrank+1, self.numtasks)
        else:
            self.errmsg.error_internal('Unknown task_expr type "%s"' % node.attr)
        return (varname, tasklist)

    def n_restricted_ident(self, node):
        """Return a variable name and a list of tasks that match a
        SUCH THAT expression."""
        tasklist = []
        self.scopes.insert(0, {})
        varname = node.kids[0].attr
        for task in range(0L, self.numtasks):
            self.scopes[0][varname] = task
            if self.process_node(node.kids[1]):
                tasklist.append(task)
        self.scopes.pop(0)
        return (varname, tasklist)

    def n_string_or_expr_list(self, node):
        "Concatenate all child values into a single list."
        result = [self.process_node(node.kids[0])]
        for child in node.kids[1:]:
            result.append(self.process_node(child))
        return result

    def n_string_or_log_comment(self, node):
        "Return the string defined by our child."
        stringval = self.process_node(node.kids[0])
        if node.attr == ["value_of"]:
            if not self.program_can_use_log_file:
                return ""
            self.program_uses_log_file = 1
            return (lambda sv, self=self: ncptl_log_lookup_string(self.logstate[self.physrank], sv), stringval)
        else:
            return stringval

    def n_string(self, node):
        "Return a string as is."
        return node.attr

    def n_such_that(self, node):
        """
             Return a list of tasks that match a given condition and a
             variable name that takes on each task number in turn.
        """
        tasklist = []
        self.scopes.insert(0, {})
        varname = node.kids[0].attr
        for task in range(0L, self.numtasks):
            self.scopes[0][varname] = task
            if self.process_node(node.kids[1]):
                tasklist.append(task)
        self.scopes.pop(0)
        return (varname, tasklist)

    def n_comma(self, node):
        "Combine all descendents' values into a list and return that."
        exprlist = [self.process_node(node.kids[0])]
        nextvalues = self.process_node(node.kids[1])
        if type(nextvalues) == types.ListType:
            exprlist.extend(nextvalues)
        else:
            exprlist.append(nextvalues)
        return exprlist

    def n_stride(self, node):
        "Return a tuple of the stride type, number of accesses, and word size."
        if node.attr in ["random", "default"]:
            return (node.attr, None, None)
        elif node.attr == "specified":
            return (node.attr, self.process_node(node.kids[0]),
                    self.process_node(node.kids[1]))
        else:
            self.errmsg.error_internal('Unknown stride "%s"' % node.attr)

    def n_range_list(self, node):
        "Return a list of range lists."
        rangelist = []
        for child in node.kids:
            range = self.process_node(child)
            if type(range) == types.ListType:
                rangelist.append(range)
            else:
                rangelist.append([range])
        return rangelist

    def n_range(self, node):
        "Fully expand the gaps in a list of numbers."

        # The easy case is that the numbers are fully enumerated.
        if node.attr == None:
            return self.process_node(node.kids[0])

        # Get the initial values (which define the sequence) and final value.
        initialvals = self.process_node(node.kids[0])
        if type(initialvals) != types.ListType:
            initialvals = [initialvals]
        finalval = self.process_node(node.kids[1])

        # Try to find the pattern in initialvals.
        if len(initialvals) == 1:
            # One initial element: One-trip loop or arithmetic progression
            if initialvals[0] == finalval:
                # Constant: Generate a one-trip loop.
                return [finalval]
            else:
                # Two-element sequence: Increment by +/- 1.
                if initialvals[0] < finalval:
                    return range(initialvals[0], finalval+1L)
                else:
                    return range(initialvals[0], finalval-1L, -1L)
        elif len(initialvals) == 2:
            # Two element range: Increment is second minus first.
            delta = initialvals[1] - initialvals[0]
            result = range(initialvals[0], finalval+delta, delta)
            if delta > 0 and result[-1] > finalval:
                result.pop()
            elif delta < 0 and result[-1] < finalval:
                result.pop()
            return result
        else:
            # See if we have an arithmetic progression.
            deltas = map(lambda a, b: b-a, initialvals[0:-1], initialvals[1:])
            if filter(lambda a, d0=deltas[0]: a!=d0, deltas) == []:
                if deltas[0] == 0:
                    # Special case for a constant progression
                    return [initialvals[0]]
                else:
                    return range(initialvals[0], finalval+1, deltas[0])

            # First look for a pattern using longs, then try floats.
            for cast in (long, float):
                ivals = map(cast, initialvals)
                zero = cast(0)

                # See if we have an increasing geometric progression.
                deltas = map(lambda a, b: b/a, ivals[0:-1], ivals[1:])
                if deltas[0] != zero and filter(lambda a, d0=deltas[0]: a!=d0, deltas) == []:
                    expansion = []
                    nextval = ivals[0]
                    while nextval <= finalval:
                        expansion.append(long(nextval))
                        nextval = nextval * deltas[0]
                    return expansion

                # See if we have a decreasing geometric progression.
                # There are a few tricky cases here.  First, rounding
                # must be taken into consideration so progressions
                # like {64, 32, 15, ..., 1} fail even each value is
                # half the previous value when rounded down.  Second,
                # expansion must be explicitly stopped when it hits 0
                # to avoid an infinite loop.
                deltas = map(lambda a, b: a/b, ivals[0:-1], ivals[1:])
                if deltas[0] != zero:
                    mapback = map(lambda a, b, d0=deltas[0]: a/d0==b, ivals[0:-1], ivals[1:])
                    if (filter(lambda a, d0=deltas[0]: a!=d0, deltas) == [] and
                        filter(lambda a: a==0, mapback) == []):
                        expansion = []
                        nextval = ivals[0]
                        while nextval >= finalval:
                            expansion.append(long(nextval))
                            if nextval == zero:
                                break
                            nextval = nextval / deltas[0]
                        return expansion

            # If there's a pattern here, we certainly can't find it.
            self.errmsg.error_fatal("Unable to find either an arithmetic or geometric pattern to {%s}\n" %
                                    string.join(map(str, initialvals+[finalval]), ", "),
                                    lineno0=node.lineno0, lineno1=node.lineno1)

    def n_aggregate_expr(self, node):
        """
             Return a pair consisting of an aggregate-function number
             and a value to write.
        """
        if node.attr == "no_aggregate":
            aggregate_number = long(NCPTL_FUNC_NO_AGGREGATE)
        elif node.attr == None:
            aggregate_number = self.process_node(node.kids[0])
        else:
            self.errmsg.error_internal('I don\'t know how to process aggregate expressions of type "%s"' % node.attr)
        return (aggregate_number, self.process_node(node.kids[-1]))

    def n_log_expr_list(self, node):
        "Return a list of (logcolumn, description, aggregate, value) tuples."
        # Assign a unique column to each log_expr_list_elt child.
        if not hasattr(node.kids[0], "logcolumn"):
            kidlist = node.kids
            for kidnum in range(0, len(kidlist)):
                kidlist[kidnum].logcolumn = self.logcolumn
                self.logcolumn = self.logcolumn + 1L
        return map(self.process_node, node.kids)

    def n_log_expr_list_elt(self, node):
        "Return a (logcolumn, description, aggregate, value) tuple."
        aggregate_number, value = self.process_node(node.kids[0])
        header = self.process_node(node.kids[1])
        return (node.logcolumn, header, aggregate_number, value)

    def n_message_spec(self, node):
        "Return a tuple that describes a particular message."
        num_messages = self.process_node(node.kids[0])
        is_unique = node.kids[1].attr
        item_size = self.process_node(node.kids[2])
        alignment = self.process_node(node.kids[3])
        touching = self.process_node(node.kids[4])
        buffer_num = self.process_node(node.kids[5])
        is_misaligned = long(node.attr)
        return (num_messages, is_unique, item_size, alignment, touching,
                buffer_num, is_misaligned)

    def n_touching_type(self, node):
        "Return a string describing how message data should be touched."
        return node.kids[0].type

    def n_buffer_number(self, node):
        'Return a buffer number to use or "auto" to use the next available.'
        if len(node.kids) == 0:
            return "auto"
        else:
            return self.process_node(node.kids[0])

    def n_recv_buffer_number(self, node):
        'Return a buffer number to use or "auto" to use the next available.'
        if len(node.kids) == 0:
            return "auto"
        else:
            return self.process_node(node.kids[0])

    def n_send_attrs(self, node):
        "Return a list of message send attributes."
        return node.attr

    def n_receive_attrs(self, node):
        "Return a list of message receive attributes."
        return node.attr


    #-----------------------------------#
    # AST interpretation: trivial       #
    # nodes and catch-all functionality #
    #-----------------------------------#

    def n_trivial_node(self, node):
        """Recursively invoke each child in turn and return the last
        child's value."""
        result = None
        for kid in node.kids:
            result = self.process_node(kid)
        return result

    def n_undefined(self, node):
        "Issue an internal-error message when given an undefined node type."
        self.errmsg.error_internal('I don\'t know how to process nodes of type "%s"' % node.type)


    #--------------------------------#
    # AST interpretation: statements #
    # (i.e., no return value),       #
    # non-communicating              #
    #--------------------------------#

    def n_program(self, node):
        "Initialize the program as a whole."
        if "--help" in self.cmdline or "-?" in self.cmdline:
            # Skip initialization if --help was specified
            help_only = 1
        else:
            # Normally, we initialize the run-time library.
            help_only = 0
            cvar.ncptl_fast_init = 1    # Time is meaningless in this backend.
            ncptl_init(NCPTL_RUN_TIME_VERSION, self.filename)
            self.procmap = ncptl_allocate_task_map(self.numtasks)
            self.touch_region_size = 0
            self.touch_region = ncptl_malloc(self.touch_region_size, 0)
            self.logfile_uuid = ncptl_log_generate_uuid()

        # Parse the command line.
        if len(node.kids) == 2:
            # The program defines its own set of command-line options.
            self.process_node(node.kids[0])
        ncptl_parse_command_line(1+len(self.cmdline),
                                 [self.backend_name]+self.cmdline,
                                 self.options, len(self.options))
        if help_only:
            self.errmsg.error_internal("Failed to exit after giving help")

        # Add the final values of the command-line variables as
        # program variables in a new scope.
        self.invoke_hook("n_program_PRE_PROCESS_OPTIONS", locals())
        self.scopes.insert(0, {})
        for opt in self.options:
            # Give derived backends first dibs on processing OPT.
            # They should return 1 if they dealt with OPT or 0 if we
            # should deal with it.
            if self.invoke_hook("n_program_PROCESS_OPTION", locals()):
                continue

            # Some options have to be handled specially.
            if opt[0] == "logfiletmpl":
                self.logfiletemplate = opt[-1]
            elif opt[0] == "random_seed":
                self.random_seed = opt[-1]
                ncptl_seed_random_task(self.random_seed, 0L)
            elif opt[0] == "numtasks":
                pass
            elif opt[0] == "mcastsync":
                self.mcastsync = opt[-1]
                if self.mcastsync not in [0L, 1L]:
                    self.errmsg.error_fatal("the --%s option accepts only 0 or 1" % opt[2])
            elif opt[0] == "latency_list":
                self.latency_list = self.parse_latency_hierarchy(opt[-1])
            else:
                self.scopes[0][opt[0]] = opt[-1]

        # Process the rest of the program.
        self.invoke_hook("n_program_PRE_KIDS", locals())
        if len(node.kids) > 0:
            self.process_node(node.kids[-1])

    def n_output_stmt(self, node):
        "Output a message to the standard output device."
        if self.suppress_output:
            return
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        self.context = "float"
        self.scopes.insert(0, {})
        for self.virtrank in map(int, tasklist):
            self.scopes[0][varname] = self.virtrank
            event = self.Event("OUTPUT", task=self.virtrank, srclines=srclines,
                               attributes=self.process_node(node.kids[1]))
            self.push_event(event)
        self.scopes.pop(0)
        self.context = "int"

    def n_let_stmt(self, node):
        "Bind values to variables and execute a statement."
        self.scopes.insert(0, {})
        self.process_node(node.kids[0])
        self.process_node(node.kids[1])
        self.scopes.pop(0)

    def n_let_binding(self, node):
        "Bind a value to a variable in the current scope."
        varname = node.kids[0].attr
        if node.attr != None:
            # We're binding to A RANDOM TASK.
            lowerbound = 0L
            upperbound = self.numtasks - 1L
            exception = -1L
            kidlist = node.kids[1:]
            for et in range(len(node.attr)-1, -1, -1):
                exprtype = node.attr[et]
                if exprtype == "E":
                    exception = self.process_node(kidlist.pop())
                elif exprtype == "L":
                    lowerbound = self.process_node(kidlist.pop())
                elif exprtype == "U":
                    upperbound = self.process_node(kidlist.pop())
                elif exprtype == "l":
                    lowerbound = self.process_node(kidlist.pop()) + 1L
                elif exprtype == "u":
                    upperbound = self.process_node(kidlist.pop()) - 1L
            value = ncptl_random_task(max(lowerbound, 0L),
                                      min(upperbound, self.numtasks-1),
                                      exception)
        else:
            # We're binding to a specific, non-random value.
            value = self.process_node(node.kids[1])
        self.scopes[0][varname] = value

    def n_touch_stmt(self, node):
        'Simulate computation by "touching" a region of memory.'
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        self.scopes.insert(0, {})
        for self.virtrank in map(int, tasklist):
            # Process the arguments to TOUCHES.
            self.scopes[0][varname] = self.virtrank
            if len(node.kids) == 4:
                # We're touching a region of the default size.
                region_bytes = self.process_node(node.kids[1])
                repeat_count = self.process_node(node.kids[2])
                stride = self.process_node(node.kids[3])
                word_size = 4L
                num_accesses = None
            else:
                # We're touching a region with a specified count and a
                # specified datatype.
                num_accesses = self.process_node(node.kids[1])
                word_size = self.process_node(node.kids[2])
                region_bytes = self.process_node(node.kids[3])
                repeat_count = self.process_node(node.kids[4])
                stride = self.process_node(node.kids[5])
            random_stride = 0
            if stride[0] == "default":
                stride_bytes = word_size
            elif stride[0] == "random":
                stride_bytes = -1L
                random_stride = 1
            else:
                stride_bytes = stride[1] * stride[2]
            if not num_accesses:
                if stride[0] == "random":
                    num_accesses = region_bytes * word_size
                else:
                    num_accesses = region_bytes / stride_bytes
                    if stride_bytes < 0:
                        num_accesses = -num_accesses
            num_accesses = repeat_count * num_accesses

            # Ensure we have enough memory allocated.
            if self.touch_region_size < region_bytes:
                self.touch_region_size = region_bytes
                self.touch_region = ncptl_realloc(self.touch_region,
                                                  self.touch_region_size,
                                                  self.bytes_per_page)

            # Start the touch from where we left off last time.
            if random_stride:
                first_byte = 0L
            else:
                if not self.next_byte.has_key(node):
                    self.next_byte[node] = 0L
                first_byte = self.next_byte[node]
                self.next_byte[node] = (self.next_byte[node] + num_accesses*stride_bytes) % region_bytes
            event = self.Event("TOUCH", task=self.virtrank, srclines=srclines,
                               attributes=[self.touch_region, region_bytes, word_size,
                                           first_byte, num_accesses, stride_bytes])
            self.push_event(event)
        self.scopes.pop(0)

    def n_touch_buffer_stmt(self, node):
        '''
             Warm up a communication buffer by "touching" it.  We
             actually do nothing here because we have no communication
             buffers in the interpreter.
        '''
        pass

    def n_reset_stmt(self, node):
        "Reset all of the counters for a particular task."
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        for self.virtrank in map(int, tasklist):
            self.push_event(self.Event("RESET", task=self.virtrank, srclines=srclines))

    def n_store_stmt(self, node):
        "Push all of the counters for a particular task."
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        for self.virtrank in map(int, tasklist):
            self.push_event(self.Event("STORE", task=self.virtrank, srclines=srclines))

    def n_restore_stmt(self, node):
        "Pop all of the counters for a particular task."
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        for self.virtrank in map(int, tasklist):
            self.push_event(self.Event("RESTORE", task=self.virtrank, srclines=srclines))

    def n_computes_for(self, node):
        '"Compute" for a given length of time.'
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        self.scopes.insert(0, {})
        for self.virtrank in map(int, tasklist):
            self.scopes[0][varname] = self.virtrank
            event = self.Event("COMPUTE", task=self.virtrank, srclines=srclines,
                               attributes=[self.process_node(node.kids[1])])
            self.push_event(event)
        self.scopes.pop(0)

    def n_sleeps_for(self, node):
        "Sleep for a given length of time."
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        self.scopes.insert(0, {})
        for self.virtrank in map(int, tasklist):
            self.scopes[0][varname] = self.virtrank
            event = self.Event("SLEEP", task=self.virtrank, srclines=srclines,
                               attributes=[self.process_node(node.kids[1])])
            self.push_event(event)
        self.scopes.pop(0)

    def n_processor_stmt(self, node):
        'Alter the mapping of task IDs to "processors".'
        varname, tasklist = self.process_node(node.kids[0])
        self.scopes.insert(0, {})
        for self.virtrank in map(int, tasklist):
            self.scopes[0][varname] = self.virtrank
            if len(node.kids) > 1:
                physrank = self.process_node(node.kids[1])
            else:
                physrank = ncptl_random_task(0, self.numtasks-1, -1)
            ncptl_assign_processor(self.virtrank, physrank, self.procmap, 0L)
            srclines = (node.lineno0, node.lineno1)
            event = self.Event("PROCSTMT", task=self.virtrank, srclines=srclines)
            self.push_event(event)
        self.scopes.pop(0)

    def n_for_count(self, node):
        "Repeat a statement a given number of times."

        # Perform the warmup repetitions if any and optional synchronization.
        if len(node.kids) == 3:
            warmups = self.process_node(node.kids[1])
            if warmups > 0L:
                suppress = self.suppress_output
                self.suppress_output = 1
                for i in range(0L, warmups):
                    self.process_node(node.kids[2])
                self.suppress_output = suppress
            if node.attr == "synchronized":
                newevents = {}
                tasklist = range(0, self.numtasks)
                coll_id = self.next_collective_id
                self.next_collective_id = self.next_collective_id + 1
                for task in tasklist:
                    self.push_event(self.Event("SYNC", task=task, peers=tasklist,
                                               srclines=(node.lineno0, node.lineno1),
                                               collective_id=coll_id))

        # Perform the regular repetitions.
        statement_node = node.kids[len(node.kids)-1]
        for i in range(0L, self.process_node(node.kids[0])):
            self.process_node(statement_node)

    def n_for_each(self, node):
        "Repeat a statement for each element in a list of ranges."
        range_lists = self.process_node(node.kids[1])
        self.scopes.insert(0, {})
        for rlist in range_lists:
            for var in rlist:
                self.scopes[0][node.kids[0].attr] = var
                self.process_node(node.kids[2])
        self.scopes.pop(0)

    def n_param_decl(self, node):
        "Declare a command-line variable."
        # Strip leading dashes off the long and short option names.
        arguments = map(self.process_node, node.kids[1:])
        arguments[1] = arguments[1][2:]
        arguments[2] = arguments[2][1]
        self.options.append([node.kids[0].attr]+arguments)

    def n_backend_decl(self, node):
        "Declare a Python variable or function."
        exec self.process_node(node.kids[0]) in globals()

    def n_for_time(self, node):
        "Repeat a statement for a given length of time."
        # Because time isn't particularly meaningful here, we simply
        # perform a fixed number of repetitions.
        for i in range(0, self.for_time_reps):
            self.process_node(node.kids[2])

    def n_if_stmt(self, node):
        "Execute a statement if a given condition is true."
        if self.process_node(node.kids[0]):
            self.process_node(node.kids[1])
        elif len(node.kids) == 3:
            self.process_node(node.kids[2])

    def n_backend_stmt(self, node):
        "Execute an arbitrary Python statement."
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        self.context = "float"
        self.scopes.insert(0, {})
        for self.virtrank in map(int, tasklist):
            self.scopes[0][varname] = self.virtrank
            event = self.Event("BACKEND", task=self.virtrank, srclines=srclines,
                               attributes=self.process_node(node.kids[1]))
            self.push_event(event)
        self.scopes.pop(0)
        self.context = "int"

    def n_assert_stmt(self, node):
        "Abort the program if a given condition is not met."
        if not self.process_node(node.kids[1]):
            ncptl_fatal("Assertion failure: %s" %
                        self.process_node(node.kids[0]))

    def n_log_stmt(self, node):
        "Write data to a log file."
        if self.suppress_output:
            return
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        self.context = "float"
        self.scopes.insert(0, {})
        for self.virtrank in map(int, tasklist):
            self.scopes[0][varname] = self.virtrank
            logdatalist = self.process_node(node.kids[1])
            event = self.Event("LOG", task=self.virtrank, srclines=srclines,
                               attributes=logdatalist)
            self.push_event(event)
        self.scopes.pop(0)
        self.context = "int"

    def n_top_level_stmt(self, node):
        "Begin a new top-level statement."
        srclines = (node.lineno0, node.lineno1)
        for task in range(0, self.numtasks):
            self.push_event(self.Event("NEWSTMT", task=task, srclines=srclines))
        for child in node.kids:
            self.process_node(child)

    def n_log_flush_stmt(self, node):
        "Compute an aggregate function across data logged up to this point."
        if self.suppress_output:
            return
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        for task in map(int, tasklist):
            self.push_event(self.Event("AGGREGATE", task=task, srclines=srclines))


    #--------------------------------#
    # AST interpretation: statements #
    # (i.e., no return value),       #
    # communicating                  #
    #--------------------------------#

    def n_empty_stmt(self, node):
        "Do nothing."
        pass

    def n_send_stmt(self, node):
        "Send messages from one task to another."
        svarname, stasklist = self.process_node(node.kids[0])
        sattribs = self.process_node(node.kids[2])
        sblocking = "asynchronously" not in sattribs
        rattribs = self.process_node(node.kids[5])
        rblocking = "asynchronously" not in rattribs
        srclines = (node.lineno0, node.lineno1)

        # Post a message from each sender to each receiver.  Note that
        # all receives are posted before any sends are posted.
        newsends = {}
        newreceives = {}
        self.scopes.insert(0, {})
        for self.virtrank in map(int, stasklist):
            sender = self.virtrank
            newsends[sender] = []
            self.scopes[0][svarname] = self.virtrank
            smsgspec = list(self.process_node(node.kids[1]))
            smsgspec.append(sattribs)
            rvarname, rtasklist = self.process_node(node.kids[3])
            self.scopes.insert(0, {})
            for self.virtrank in map(int, rtasklist):
                receiver = self.virtrank
                self.scopes[0][rvarname] = self.virtrank
                rmsgspec = list(self.process_node(node.kids[4]))
                rmsgspec.append(rattribs)
                if "unsuspecting" not in rattribs:
                    for i in range(0, rmsgspec[0]):
                        newevent = self.Event("RECEIVE", task=receiver, peers=[sender],
                                              srclines=srclines, msgsize=rmsgspec[2],
                                              blocking=rblocking, attributes=rattribs)
                        try:
                            newreceives[receiver].append(newevent)
                        except KeyError:
                            newreceives[receiver] = [newevent]
                for i in range(0, smsgspec[0]):
                    newevent = self.Event("SEND", task=sender, peers=[receiver],
                                          srclines=srclines, msgsize=smsgspec[2],
                                          blocking=sblocking, attributes=sattribs)
                    newsends[sender].append(newevent)
            self.scopes.pop(0)
        self.scopes.pop(0)
        for receiver, eventlist in newreceives.items():
            for event in eventlist:
                self.push_event(event)
        for sender, eventlist in newsends.items():
            for event in eventlist:
                self.push_event(event)

    def n_receive_stmt(self, node):
        "Receive messages from other tasks."

        # Post a message to each receiver from each sender.  As in the
        # SEND statement, the send scope is the outer scope and the
        # receive scope is the inner scope.
        activetasks = {}
        svarname, stasklist = self.process_node(node.kids[2])
        rattribs = self.process_node(node.kids[3])
        srclines = (node.lineno0, node.lineno1)
        self.scopes.insert(0, {})
        for self.virtrank in map(int, stasklist):
            sender = self.virtrank
            activetasks[sender] = 1
            self.scopes[0][svarname] = self.virtrank
            rvarname, rtasklist = self.process_node(node.kids[0])
            self.scopes.insert(0, {})
            for self.virtrank in map(int, rtasklist):
                receiver = self.virtrank
                activetasks[receiver] = 1
                self.scopes[0][rvarname] = self.virtrank
                rmsgspec = list(self.process_node(node.kids[1]))
                rmsgspec.append(rattribs)
                for i in range(0, rmsgspec[0]):
                    event = self.Event("RECEIVE", task=receiver, peers=[sender],
                                       srclines=srclines, msgsize=rmsgspec[2],
                                       blocking="asynchronously" not in rattribs,
                                       attributes=rattribs)
                    self.push_event(event)
            self.scopes.pop(0)
        self.scopes.pop(0)

    def n_awaits_completion(self, node):
        "Wait until all asynchronous messages have completed."
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        tasklist = map(int, tasklist)
        for task in tasklist:
            self.push_event(self.Event("WAIT_ALL", task=task, srclines=srclines))

    def n_sync_stmt(self, node):
        "Synchronize a subset of the tasks."
        varname, tasklist = self.process_node(node.kids[0])
        srclines = (node.lineno0, node.lineno1)
        tasklist = map(int, tasklist)
        newevents = {}
        coll_id = self.next_collective_id
        self.next_collective_id = self.next_collective_id + 1
        for task in tasklist:
            self.push_event(self.Event("SYNC", task=task, peers=tasklist,
                                       srclines=srclines, collective_id=coll_id))

    def n_mcast_stmt(self, node):
        "Multicast a message from one task to multiple others."
        svarname, stasklist = self.process_node(node.kids[0])
        sattribs = self.process_node(node.kids[3])
        if "asynchronously" in sattribs:
            self.errmsg.error_fatal("asynchronous multicasts are not yet implemented by the %s backend" % self.backend_name,
                                    lineno0=node.lineno0, lineno1=node.lineno1)
        srclines = (node.lineno0, node.lineno1)
        self.scopes.insert(0, {})
        for self.virtrank in map(int, stasklist):
            self.scopes[0][svarname] = self.virtrank
            smsgspec = list(self.process_node(node.kids[1]))
            smsgspec.append(sattribs)
            for i in range(0, smsgspec[0]):
                rvarname, rtasklist = self.process_node(node.kids[2])
                if self.virtrank in rtasklist:
                    rtasklist.remove(self.virtrank)
                tasklist = map(int, [self.virtrank]+rtasklist)
                coll_id = self.next_collective_id
                self.next_collective_id = self.next_collective_id + 1
                for task in tasklist:
                    event = self.Event("MCAST", task=task, peers=tasklist,
                                       srclines=srclines, msgsize=smsgspec[2],
                                       attributes=sattribs, collective_id=coll_id)
                    self.push_event(event)
        self.scopes.pop(0)

    def n_reduce_stmt(self, node):
        "Reduce a list of values from one set of tasks to another."
        # Acquire a list of unique source, destination, and combined tasks.
        svarname, stasklist = self.process_node(node.kids[0])
        stasklist = map(int, stasklist)
        rtasklist = {}
        self.scopes.insert(0, {})
        recv_spec_node = node.kids[1]
        data_type_node = recv_spec_node.kids[3]
        data_type = data_type_node.attr
        message_size = self.process_node(recv_spec_node.kids[0])
        if data_type == "doublewords":
            message_size = message_size * 8
        elif data_type == "integers":
            message_size = message_size * 4
        else:
            self.errmsg.error_internal('Unknown REDUCE datatype "%s"' % data_type)
        for self.virtrank in map(int, stasklist):
            self.scopes[0][svarname] = self.virtrank
            if "allreduce" in node.attr:
                rvar, rtasks = self.process_node(node.kids[0])
            else:
                rvar, rtasks = self.process_node(node.kids[3])
            for r in rtasks:
                rtasklist[r] = 1
        self.scopes.pop(0)
        rtasklist = map(int, rtasklist.keys())
        rtasklist.sort()
        tasklist = {}
        for task in stasklist + rtasklist:
            tasklist[task] = 1
        tasklist = tasklist.keys()
        tasklist.sort()

        # Push a REDUCE event onto the queues of all senders and all receivers.
        srclines = (node.lineno0, node.lineno1)
        peerlist = [stasklist, rtasklist]
        coll_id = self.next_collective_id
        self.next_collective_id = self.next_collective_id + 1
        for task in tasklist:
            event = self.Event("REDUCE", task=task, peers=peerlist,
                               srclines=srclines, msgsize=message_size,
                               attributes=data_type, collective_id=coll_id)
            self.push_event(event)


    #-------------------#
    # Event processing: #
    # top-level         #
    #-------------------#

    def process_all_events(self):
        "Process all of the events we've accumulated."
        leftovers = []           # List of leftover-event error messages
        self.context = "float"   # Some futures may need to know the context.

        # Complete all events on all tasks.
        self.initialize_opmethod()
        for task in range(0, self.numtasks):
            # Don't do anything if we know we're stuck.
            if self.stuck_tasks.has_key(task):
                continue

            # Process the current task until no incomplete events remain.
            eventlist = self.eventlist[task]
            while not eventlist.all_complete():
                errstring = self.process_fully_task_event(task)
                if errstring == None:
                    eventlist.try_posting_all()
                else:
                    leftovers.append((task, errstring))
                    break

        # Determine if any asynchronous events were not waited for.
        not_waited = {}
        for task in range(0, self.numtasks):
            if self.pendingevents[task] != []:
                if not not_waited.has_key(task):
                    not_waited[task] = {}
                for event in self.pendingevents[task]:
                    if not not_waited[task].has_key(event.operation):
                        not_waited[task][event.operation] = 1
                    else:
                        not_waited[task][event.operation] = not_waited[task][event.operation] + 1
        if not_waited != {}:
            badtasks = not_waited.keys()
            badtasks.sort()
            for task in badtasks:
                for badop, badtally in not_waited[task].items():
                    leftovers.append((task,
                                      self.format_plurals("Task %d posted %C asynchronous %s%S that %W never waited for",
                                                          badtally, (task, badop))))

        # Determine if any messages were sent but not received.
        badtasks = {}
        for task in range(0, self.numtasks):
            unmatched = filter(lambda ev: ev.operation=="SEND",
                               self.eventlist[task].find_unmatched())
            for badsend in unmatched:
                badpeer = badsend.peers[0]
                try:
                    badtasks[task][badpeer] = badtasks[task][badpeer] + 1
                except KeyError:
                    try:
                        badtasks[task][badpeer] = 1
                    except KeyError:
                        badtasks[task] = {}
                        badtasks[task][badpeer] = 1
        if badtasks != {}:
            for task, peer2tally in badtasks.items():
                badpeers = peer2tally.keys()
                badpeers.sort()
                for peer in badpeers:
                    leftovers.append((task,
                                      self.format_plurals("Task %d sent %C message%S to task %d that %W never received",
                                                          peer2tally[peer],
                                                          (task, peer))))

        # Abort if we encountered any leftover-event errors.
        if leftovers != []:
            error_message = "The program ended with the following leftover-event errors:\n   * "
            unique_leftovers = {}
            for lo in leftovers:
                unique_leftovers[lo[1]] = 1
            leftovers = unique_leftovers.keys()
            leftovers.sort()
            error_message = error_message + string.join(leftovers, "\n   * ")
            self.errmsg.warning(error_message)

    def initialize_opmethod(self):
        "Initialize the map from operation to method call that processes it."
        self.opmethod = {"SEND"      : self.process_send,
                         "RECEIVE"   : self.process_receive,
                         "WAIT_ALL"  : self.process_wait_all,
                         "SYNC"      : self.process_sync,
                         "MCAST"     : self.process_mcast,
                         "REDUCE"    : self.process_reduce,
                         "OUTPUT"    : self.process_output,
                         "RESET"     : self.process_reset,
                         "STORE"     : self.process_store,
                         "RESTORE"   : self.process_restore,
                         "LOG"       : self.process_log,
                         "AGGREGATE" : self.process_aggregate,
                         "NEWSTMT"   : self.process_newstmt,
                         "BACKEND"   : self.process_backend,
                         "PROCSTMT"  : self.process_no_op,
                         "SLEEP"     : self.process_no_op,
                         "COMPUTE"   : self.process_no_op,
                         "TOUCH"     : self.process_no_op}

    def process_fully_task_event(self, task):
        """
             Process the first incomplete event for a given task,
             recursively processing that event's dependencies on other
             tasks.  Assumption: The task contains at least one
             incomplete event.
        """

        # First check for the easy case: the task can complete immediately.
        blocked_on, numcompleted = self.process_task_while_able(task)
        if blocked_on == None:
            return None

        # Build up a list of dependencies until some task completes or
        # we encounter a cycle of dependencies (i.e., deadlock).
        dependencies = [task]
        while blocked_on != None:
            # Abort if the task is blocked on a peer which will never
            # satisfy it.
            if self.eventlist[blocked_on].all_complete():
                return ("Task %d terminated before satisfying task %d's %s operation" %
                        (blocked_on, task,
                         self.eventlist[task].get_first_incomplete().operation))

            # Stop processing the current task if it's either
            # deadlocked or blocked -- possibly indirectly -- on a
            # deadlocked task.
            dependencies.append(blocked_on)
            try:
                # Construct a list of deadlocked tasks.
                deadlock = dependencies[dependencies[:-1].index(blocked_on):]
                for deadtask in dependencies:
                    # Delete all events following a stuck event.
                    eventlist = self.eventlist[deadtask]
                    eventlist.try_posting_all()
                    eventlist.delete_unposted()
                    self.stuck_tasks[deadtask] = 1

                # Tell the user which tasks have deadlocked.
                error_message = "The following tasks have deadlocked: "
                error_message = error_message + string.join(map(str, deadlock), " --> ")
                return error_message
            except ValueError:
                pass

            # If the last link in the chain makes progress we can
            # break out of the loop and unwind the chain.
            blocked_on, numcompleted = self.process_task_while_able(blocked_on)
            if numcompleted > 0:
                break

        # Unwind the chain of dependencies by attempting to complete
        # each task in the chain (except the first, which we already
        # completed).  Note that we're not guaranteed to be successful
        # because an event may depend on multiple other events but
        # we've satisfied only one of them.
        dependencies.reverse()
        for deptask in dependencies[1:]:
            self.process_task_while_able(deptask)
        return None

    def process_task_while_able(self, task):
        """
             Keep processing incomplete events for a given task until
             we can't.  Return the task for which we're stuck waiting
             and the number of events we successfully completed.
        """
        eventlist = self.eventlist[task]
        numcompleted = 0
        while not eventlist.all_complete():
            event = eventlist.get_first_incomplete()
            try:
                blocked_on = self.opmethod[event.operation](event)
                if blocked_on == None:
                    numcompleted = numcompleted + 1
                else:
                    return (blocked_on, numcompleted)
            except KeyError:
                self.errmsg.error_internal('Unknown event type "%s"' % event.operation)
        return (None, numcompleted)


    #----------------------#
    # Event processing:    #
    # communication events #
    #----------------------#

    def process_send(self, event):
        "Process a SEND event."
        task = event.task
        if not event.blocking:
            self.pendingevents[task].append(event)
        self.msgqueue[event.peers[0]].push(event)
        self.eventlist[task].complete()
        self.update_counters(event)
        return None

    def process_receive(self, event):
        "Process a RECEIVE event."
        if event.blocking:
            # Blocked events either complete or report who's blocking them.
            matched_event = self.msgqueue[event.task].pop_match(event)
            if matched_event == None:
                return event.peers[0]
            else:
                self.eventlist[event.task].complete([matched_event])
                self.update_counters(event)
        else:
            # Asynchronous receives complete immediately.
            self.eventlist[event.task].complete()
            self.pendingevents[event.task].append(event)
        return None

    def process_wait_all(self, wait_event):
        "Process a WAIT_ALL event."
        task = wait_event.task

        # First pass: Ensure that all events are ready to complete.
        # If not, return the event on which we're blocked.
        unpop_list = []
        try:
            for event in self.pendingevents[task]:
                if event.operation == "SEND":
                    pass
                elif event.operation == "RECEIVE":
                    matched_event = self.msgqueue[task].pop_match(event)
                    if matched_event == None:
                        return event.peers[0]
                    unpop_list.insert(0, (task, event, matched_event))
                else:
                    self.errmsg.error_internal('Unrecognized event type "%s"' % event.operation)
        finally:
            # Restore the message queue to its previous state.
            for task, event, matched_event in unpop_list:
                self.msgqueue[task].unpop_match(event, matched_event)

        # Second pass: Complete all events.
        remote_senders = []
        for event in self.pendingevents[task]:
            if event.operation == "SEND":
                pass
            elif event.operation == "RECEIVE":
                matched_event = self.msgqueue[task].pop_match(event)
                remote_senders.append(matched_event)
                self.update_counters(event)
            else:
                self.errmsg.error_internal('Unrecognized event type "%s"' % event.operation)
        self.eventlist[task].complete(remote_senders)
        self.pendingevents[task] = []
        return None

    def process_sync(self, event):
        "Process a SYNC event."

        # First pass: Ensure that all events are ready to complete.
        barrier_events = []
        for peer in event.peers:
            self.eventlist[peer].try_posting_all()
            inc_ev = self.eventlist[peer].get_first_incomplete()
            if inc_ev.collective_id != event.collective_id or inc_ev.posttime == None:
                return peer
            barrier_events.append(inc_ev)

        # Second pass: Complete all events.
        for peer in event.peers:
            self.eventlist[peer].complete(barrier_events)
        return None

    def process_mcast(self, event):
        "Process an MCAST event."

        # Handle the case in which we synchronize after a multicast.
        if self.mcastsync:
            # First pass: Ensure that all events are ready to complete.
            mcast_events = []
            for peer in event.peers:
                self.eventlist[peer].try_posting_all()
                inc_ev = self.eventlist[peer].get_first_incomplete()
                if inc_ev.collective_id != event.collective_id or inc_ev.posttime == None:
                    return peer
                mcast_events.append(inc_ev)
                if inc_ev.msgsize != mcast_events[0].msgsize:
                    return inc_ev.task

            # We don't actually need to manipulate the message queue
            # to perform the multicast.  We just handle all cases at
            # once.
            rootev = mcast_events[0]
            self.eventlist[rootev.task].complete(peerlist=[mcast_events[0]],
                                                 nolat_peerlist=mcast_events[1:])
            self.update_counters(rootev, "SEND")
            for childev in mcast_events[1:]:
                self.eventlist[childev.task].complete(peerlist=[mcast_events[0]],
                                                      nolat_peerlist=mcast_events[1:])
                self.update_counters(childev, "RECEIVE")
            return None

        # Now handle the default, non-synchronizing case.
        if event.peers[0] == event.task:
            # The root of the multicast is considered a sender.
            for peer in event.peers[1:]:
                self.msgqueue[peer].push(event)
            self.eventlist[event.task].complete()
            self.update_counters(event, "SEND")
        else:
            # Everyone else in the multicast is considered a receiver.
            matched_event = self.msgqueue[event.task].pop_match(event)
            if matched_event == None:
                return event.peers[0]
            else:
                self.eventlist[event.task].complete([matched_event])
                self.update_counters(event, "RECEIVE")
        return None

    def process_reduce(self, event):
        "Process a REDUCE event."
        # Acquire a list and hash of senders and receivers.
        sendpeers, receivepeers = event.peers
        taskusage = {}
        sendpeers = map(int, sendpeers)
        receivepeers = map(int, receivepeers)
        for peer in sendpeers:
            try:
                taskusage[peer] = (1, taskusage[peer][1])
            except KeyError:
                taskusage[peer] = (1, 0)
        for peer in receivepeers:
            try:
                taskusage[peer] = (taskusage[peer][0], 1)
            except KeyError:
                taskusage[peer] = (0, 1)
        allpeers = taskusage.keys()
        allpeers.sort()

        # Wait until all of our peers have posted a matching REDUCE
        # event then give each REDUCE event a pointer to every
        # matching REDUCE event which corresponds to a sender.
        if not hasattr(event, "reduce_send_events"):
            reduce_events = []
            reduce_send_events = []
            for peer in allpeers:
                self.eventlist[peer].try_posting_all()
                inc_ev = self.eventlist[peer].get_first_incomplete()
                if inc_ev.collective_id != event.collective_id or inc_ev.posttime == None:
                    return peer
                reduce_events.append(inc_ev)
                if taskusage[peer][0] == 1:
                    reduce_send_events.append(inc_ev)
            for ev in reduce_events:
                ev.reduce_send_events = reduce_send_events

        # Give derived backends a chance to intervene.  The hook
        # function should return a process_reduce return value (None
        # or a task ID) or [] if process_reduce should not return now.
        retval = self.invoke_hook("process_reduce_READY", locals(), alternate=[])
        if type(retval) != types.ListType or retval != []:
            return retval

        # If the hash designates us a sender who is not also a
        # receiver then we can complete the event immediately and
        # return.
        task = event.task
        if taskusage[task] == (1, 0):
            self.eventlist[task].complete()
            return None

        # Process receivers and sender/receivers.
        self.eventlist[task].complete(event.reduce_send_events)
        return None


    #--------------------------#
    # Event processing:        #
    # non-communication events #
    #--------------------------#

    def process_no_op(self, event):
        "Complete an event without actually doing anything."
        self.eventlist[event.task].complete()
        return None

    def process_output(self, event):
        """
             Process an OUTPUT event.  As a side effect, the event's
             attributes are replaced with their string equivalent.
        """
        task = event.task
        self.physrank = event.task    # May be needed by futures.
        self.eventlist[task].try_posting_all()   # Update event.posttime.
        self.counters[task]["elapsed_usecs"] = event.posttime - self.timer_start[task]
        event.attributes = [string.join(map(lambda e, self=self:
                                            self.eval_lazy_expr(e, types.StringType),
                                            event.attributes), "")]
        sys.stdout.write("%s\n" % event.attributes[0])
        self.eventlist[task].complete()
        return None

    def process_reset(self, event):
        "Process a RESET event."
        task = event.task
        for countvar in self.counters[task].keys():
            self.counters[task][countvar] = 0L
        self.eventlist[task].try_posting_all()   # Update event.posttime.
        self.timer_start[task] = event.posttime
        self.eventlist[task].complete()
        return None

    def process_store(self, event):
        "Process a STORE event."
        task = event.task
        self.eventlist[task].try_posting_all()   # Update event.posttime.
        self.counter_stack[task].append((self.counters[task], self.timer_start[task], event.posttime))
        self.eventlist[task].complete()
        return None

    def process_restore(self, event):
        "Process a RESTORE event."
        task = event.task
        self.eventlist[task].try_posting_all()   # Update event.posttime.
        self.counters[task], stored_start, stored_posttime = self.counter_stack[task].pop()
        self.timer_start[task] = event.posttime - stored_posttime + stored_start
        self.eventlist[task].complete()
        return None

    def process_log(self, event):
        """
             Process a LOG event.  As a side effect, the event's
             attributes are replaced with a version consisting of a
             string header and a numeric value.
        """
        task = self.physrank = event.task    # self.physrank may be needed by a future.
        self.eventlist[task].try_posting_all()   # Update event.posttime.
        self.counters[task]["elapsed_usecs"] = event.posttime - self.timer_start[task]
        self.initialize_log_file(task)           # Safe to invoke repeatedly
        event.attributes = map(lambda attr, self=self:
                               (attr[0], self.eval_lazy_expr(attr[1], types.StringType),
                                attr[2], self.eval_lazy_expr(attr[3], types.FloatType)),
                               event.attributes)
        for column, header, aggregate_number, value in event.attributes:
            ncptl_log_write(self.logstate[task], column, header, aggregate_number, value)
        self.eventlist[task].complete()
        return None

    def process_aggregate(self, event):
        "Process an AGGREGATE event."
        task = event.task
        self.initialize_log_file(task)           # Safe to invoke repeatedly
        ncptl_log_compute_aggregates(self.logstate[task])
        self.eventlist[task].complete()
        return None

    def process_newstmt(self, event):
        "Process a NEWSTMT event."
        if self.program_uses_log_file:
            self.initialize_log_file(event.task)
            ncptl_log_commit_data(self.logstate[event.task])
        self.eventlist[event.task].complete()
        return None

    def process_backend(self, event):
        """
             Process a BACKEND event.  As a side effect, the event's
             attributes are replaced with their string equivalent.
        """
        task = event.task
        self.physrank = event.task    # May be needed by futures.
        self.eventlist[task].try_posting_all()   # Update event.posttime.
        self.counters[task]["elapsed_usecs"] = event.posttime - self.timer_start[task]
        event.attributes = [string.join(map(lambda e, self=self:
                                            self.eval_lazy_expr(e, types.StringType),
                                            event.attributes), "")]
        backend_re = re.compile(r'\[message\s+buffer\s+([^\]]+)\]', re.IGNORECASE)
        backend_code = backend_re.sub("dummy_buffer", event.attributes[0])
        dummy_buffer = []
        exec backend_code in globals(), locals()
        self.eventlist[task].complete()
        return None
