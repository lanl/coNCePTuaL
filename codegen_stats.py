#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# Output program statistics
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

import sys
import string
import re
import time
import types
import codegen_interpret
from pyncptl import *

class NCPTL_CodeGen(codegen_interpret.NCPTL_CodeGen):

    #---------------------#
    # Exported functions  #
    # (called from the    #
    # compiler front end) #
    #---------------------#

    def __init__(self, options=None):
        "Initialize program statistics."
        # Process the "--exclude" argument but store all others.
        # Note that we do this "manually" without relying on
        # ncptl_parse_command_line() because we want to allow
        # "--exclude" to be specified repeatedly, which
        # ncptl_parse_command_line() doesn't support.
        self.exclusions = {}        # Hash of categories/fields to omit
        filtered_options = []       # Options left after removing --exclude
        for arg in range(0, len(options)):
            arg_match = re.match(r'--exclude=(.*)', options[arg])
            if arg_match:
                self.exclusions[arg_match.group(1)] = 1
            else:
                filtered_options.append(options[arg])

        # Invoke our parent's constructor.
        codegen_interpret.NCPTL_CodeGen.__init__(self, filtered_options)

        # Initialize our remaining state.
        self.backend_name = "stats"
        self.backend_desc = "program statistics"
        self.parent = self.__class__.__bases__[0]
        self.virt2physmap = map(lambda dummy: {}, range(0, self.numtasks))
        self.phys2virtmap = map(lambda dummy: {}, range(0, self.numtasks))
        self.expandlists = 0        # 0=show numeric ranges; 1=show all numbers
        self.format2func = {        # How to output data in a given format
            "text"      : self.output_text_statistics,
            "sep"       : self.output_separated_statistics,
            "excelcsv"  : self.output_excel_csv_statistics}
        self.outputformat = "text"  # Which of the above to use
        self.outputseparator = ","  # Column separator to use for type "sep"

    def generate(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        'Interpret an AST and output statistics on the executed events.'
        self.generate_initialize(ast, filesource, sourcecode)
        self.sourcecode = sourcecode

        # Remove log-file options and add a few backend-specific options.
        self.set_log_file_status(0)
        self.options.extend([
            ["outputformat",
             'Output format, either "text", "excelcsv", or "sep:<string>"',
             "format", "F", "text"],
            ["expandlists",
             "0=collapse lists of numbers into ranges; 1=show all numbers",
             "expand-lists", "E", 0],
            ["exclusions",
             "Name of a category or individual field to exclude from output",
             "exclude", "X", ""]])

        # Perform a prefix traversal (roughly).
        self.process_node(ast)
        self.generate_finalize(ast, filesource, sourcecode)

        # Gather and reporta variety of statistics.
        self.gather_statistics()
        return self.format2func[self.outputformat]()

    def compile_only(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Write CODELINES to a file."
        if verbose:
            if outfilename == "-":
                pretty_outfilename = "standard output"
            else:
                pretty_outfilename = outfilename
            sys.stderr.write("# Writing statistics to %s ...\n" % pretty_outfilename)
        try:
            if outfilename == "-":
                for oneline in codelines:
                    print oneline
            else:
                outfile = open(outfilename, "w")
                for oneline in codelines:
                    outfile.write("%s\n" % oneline)
                outfile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("Unable to produce %s (%s)" % (outfilename, strerror),
                                    filename=self.backend_name)

    def compile_and_link(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Pass control to compile_only, as linking is not meaningful here."
        self.compile_only(progfilename, codelines, outfilename, verbose, keepints)


    #------------------#
    # Internal utility #
    # functions        #
    #------------------#

    def long_to_str(self, longnum):
        "Convert a long to a string even in old Python versions."
        longstr = str(longnum)
        if longstr[-1] == "L":
            return longstr[:-1]
        else:
            return longstr

    def safe_dict_append(self, somedict, somekey, somevalue):
        "Append a value to a possibly undefined list in a dictionary."
        try:
            somedict[somekey].append(somevalue)
        except KeyError:
            somedict[somekey] = [somevalue]

    def safe_dict_increment(self, somedict, somekey, increment=1):
        "Increment a possibly undefined value in a dictionary."
        try:
            somedict[somekey] = somedict[somekey] + increment
        except KeyError:
            somedict[somekey] = increment

    def list_to_range_string(self, numberlist):
        "Convert a list of numbers (sorted) to a list of comma-separated ranges."
        if len(numberlist) == 0:
            return "none"
        if self.expandlists:
            return string.join(map(self.long_to_str, numberlist), ", ")
        rangebounds = [[numberlist[0], numberlist[0]]]
        for num in numberlist:
            if num <= rangebounds[-1][1] + 1:
                rangebounds[-1][1] = num
            else:
                rangebounds.append([num, num])
        rangelist = []
        for rstart, rstop in rangebounds:
            if rstop == rstart:
                rangelist.append(self.long_to_str(rstop))
            elif rstop == rstart + 1:
                rangelist.append("%s, %s" %
                                 (self.long_to_str(rstart), self.long_to_str(rstop)))
            else:
                rangelist.append("%s-%s" %
                                 (self.long_to_str(rstart), self.long_to_str(rstop)))
        return string.join(rangelist, ", ")


    #----------------#
    # Hook functions #
    #----------------#

    def n_program_PROCESS_OPTION(self, localvars):
        "Process command-line options of importance to us."
        opt = localvars["opt"]
        if opt[0] == "expandlists":
            self.expandlists = int(opt[-1])
            if self.expandlists not in [0, 1]:
                self.errmsg.error_fatal("the --%s option accepts only 0 or 1" % opt[2])
            return 1
        elif opt[0] == "outputformat":
            self.outputformat = opt[-1]
            if re.match(r'sep\b', self.outputformat):
                if self.outputformat == "sep":
                    self.errmsg.error_fatal("missing argument to --%s=%s" % (opt[2], opt[-1]))
                self.output_separator = self.outputformat[4:]
                self.outputformat = "sep"
            elif not self.format2func.has_key(self.outputformat):
                self.errmsg.error_fatal('unrecognized output format "%s"' % self.outputformat)
            return 1
        elif opt[0] == "exclusions":
            # We already processed --exclude in __init__.
            return 1
        elif hasattr(self.parent, "n_program_PROCESS_OPTION"):
            # Give our parent a chance to process the current option.
            return self.parent.n_program_PROCESS_OPTION(self, localvars)
        else:
            return 0


    #------------------#
    # Method overrides #
    #------------------#

    def n_processor_stmt(self, node):
        'Alter the mapping of task IDs to "processors".'
        self.parent.n_processor_stmt(self, node)

        # Remember all virtual-to-physical and physical-to-virtual
        # mappings, including maps to self.
        for task in range(0, self.numtasks):
            proc = ncptl_virtual_to_physical(self.procmap, task)
            self.virt2physmap[task][proc] = 1
        for proc in range(0, self.numtasks):
            task = ncptl_physical_to_virtual(self.procmap, proc)
            self.phys2virtmap[proc][task] = 1

    def process_output(self, event):
        "Do nothing; statistics backends do not produce output."
        return self.process_no_op(event)

    def process_log(self, event):
        "Do nothing; statistics backends do not produce log files."
        return self.process_no_op(event)

    def process_aggregate(self, event):
        "Do nothing; statistics backends do not produce log files."
        return self.process_no_op(event)


    #----------------------#
    # Statistics-gathering #
    # functions            #
    #----------------------#

    def report_all_events(self):
        "Report the number of events of each type performed by all processors."
        optallies = {}
        for task in range(0, self.numtasks):
            for event in self.eventlist[task].events:
                self.safe_dict_increment(optallies, event.operation)
        oplist = optallies.keys()
        oplist.sort()
        stats = []
        for op in oplist:
            stats.append(("Total number of %s events" % op, optallies[op]))
        self.statistics.append(("Event tallies", stats))

    def report_processor_event_sets(self):
        "Report the set of events performed by each processor."
        eventsets = {}
        for task in range(0, self.numtasks):
            taskeventset = {}
            for event in self.eventlist[task].events:
                taskeventset[event.operation] = 1
            taskeventsetkeys = taskeventset.keys()
            taskeventsetkeys.sort()
            self.safe_dict_append(eventsets, tuple(taskeventsetkeys), task)
        stats = []
        eventsetkeys = eventsets.keys()
        eventsetkeys.sort()
        for eset in eventsetkeys:
            stats.append(("Processors executing only {%s}" %
                          string.join(eset, ", "),
                          self.list_to_range_string(eventsets[eset])))
        self.statistics.append(("Per-processor event sets", stats))

    def report_processor_events(self):
        "Report the number of events of each type performed by each processor."
        # See which events each processor executed.
        optallies = {}
        for task in range(0, self.numtasks):
            taskoptallies = {}
            for event in self.eventlist[task].events:
                self.safe_dict_increment(taskoptallies, event.operation)
            for event_tally in taskoptallies.items():
                self.safe_dict_append(optallies, event_tally, task)

        # Summarize and report our findings.
        stats = []
        optallykeys = optallies.keys()
        optallykeys.sort()
        for optally in optallykeys:
            if optally[1] == 1:
                eventstr = "event"
            else:
                eventstr = "events"
            stats.append(("Processors executing %s %s %s" %
                          (self.long_to_str(optally[1]), optally[0], eventstr),
                          optallies[optally]))
        self.statistics.append(("Per-processor event tallies", stats))

    def report_all_traffic(self):
        "Report the total number of bytes and messages sent."
        total_bytes = 0
        total_messages = 0
        unique_sizes = {}
        for task in range(0, self.numtasks):
            for event in self.eventlist[task].events:
                if event.operation == "SEND" or (event.operation == "MCAST" and event.peers[0] == task):
                    for peer in event.peers:
                        if peer != task:
                            total_bytes = total_bytes + event.msgsize
                            total_messages = total_messages + 1
                    unique_sizes[event.msgsize] = 1
        unique_sizes = unique_sizes.keys()
        unique_sizes.sort()
        stats = [("Total messages sent",       total_messages),
                 ("Total bytes sent",          total_bytes),
                 ("Unique message sizes sent", unique_sizes)]
        self.statistics.append(("Message traffic", stats))

    def report_processor_traffic(self):
        "Report the number of bytes and messages sent/received by processor."
        bytes_sent = {}
        msgs_sent = {}
        bytes_rcvd = {}
        msgs_rcvd = {}
        for task in range(0, self.numtasks):
            task_bytes_sent = 0
            task_msgs_sent = 0
            task_bytes_rcvd = 0
            task_msgs_rcvd = 0
            for event in self.eventlist[task].events:
                if event.operation == "SEND" or (event.operation == "MCAST" and event.peers[0] == task):
                    for peer in event.peers:
                        if peer != task:
                            task_bytes_sent = task_bytes_sent + event.msgsize
                            task_msgs_sent = task_msgs_sent + 1
                elif event.operation == "RECEIVE" or (event.operation == "MCAST" and event.peers[0] != task):
                    task_bytes_rcvd = task_bytes_rcvd + event.msgsize
                    task_msgs_rcvd = task_msgs_rcvd + 1
            self.safe_dict_append(bytes_sent, task_bytes_sent, task)
            self.safe_dict_append(bytes_rcvd, task_bytes_rcvd, task)
            self.safe_dict_append(msgs_sent, task_msgs_sent, task)
            self.safe_dict_append(msgs_rcvd, task_msgs_rcvd, task)
        stats = []

        def append_data(send_recv, dictionary, bytes_msgs, stats=stats, self=self):
            "Append send/receive byte/message data to the STATS array."
            sorted_dict = dictionary.keys()
            sorted_dict.sort()
            for val in sorted_dict:
                if val == 1:
                    valsuffix = ""
                else:
                    valsuffix = "s"
                stats.append(("Processors %s a total of %s %s%s" %
                              (send_recv, self.long_to_str(val), bytes_msgs, valsuffix),
                              dictionary[val]))

        append_data("sending", bytes_sent, "byte")
        append_data("receiving", bytes_rcvd, "byte")
        append_data("sending", msgs_sent, "message")
        append_data("receiving", msgs_rcvd, "message")
        self.statistics.append(("Per-processor message traffic", stats))

    def report_bisection(self):
        "Report the traffic which crossed the middle of the network."
        if self.numtasks < 2:
            return
        bisection_bytes = 0
        bisection_messages = 0
        midtask = self.numtasks / 2
        for task in range(0, self.numtasks):
            halftask = task / midtask
            for event in self.eventlist[task].events:
                if event.operation == "SEND" or (event.operation == "MCAST" and event.peers[0] == task):
                    for peer in event.peers:
                        if peer != task and peer/midtask != halftask:
                            bisection_bytes = bisection_bytes + event.msgsize
                            bisection_messages = bisection_messages + 1
        stats = [("Bisection messages", bisection_messages),
                 ("Bisection bytes",    bisection_bytes)]
        self.statistics.append(("Network bisection crossings", stats))

    def report_processor_peers(self):
        "Report the peers of each processor as relative offsets."
        peer_deltas = {}
        for task in range(0, self.numtasks):
            task_peer_deltas = {}
            for event in self.eventlist[task].events:
                if event.operation == "SEND":
                    task_peer_deltas[event.peers[0]-task] = 1
            task_peer_deltas = task_peer_deltas.keys()
            task_peer_deltas.sort()
            self.safe_dict_append(peer_deltas, tuple(task_peer_deltas), task)
        stats = []
        deltalist = peer_deltas.keys()
        deltalist.sort()
        for delta in deltalist:
            if len(delta) > 0:
                deltastr = []
                for d in delta:
                    if d > 0:
                        deltastr.append("+" + str(d))
                    else:
                        deltastr.append(str(d))
                deltastr = string.join(deltastr, ", ")
                stats.append(("Processors posting SEND events to offsets {%s}" % deltastr,
                              peer_deltas[delta]))
        if stats:
            self.statistics.append(("Processor SEND-event peers", stats))

    def report_virtual_physical(self):
        "Report all mappings between tasks and processors."
        stats = []
        for proc in range(0, self.numtasks):
            phys2virtmap = self.phys2virtmap[proc].copy()
            try:
                del phys2virtmap[proc]
            except KeyError:
                pass
            if phys2virtmap:
                tasklist = phys2virtmap.keys()
                tasklist.sort()
                procstr = self.long_to_str(proc)
                stats.append(("Tasks assigned to processor %s (besides %s)" % (procstr, procstr), tasklist))
        for task in range(0, self.numtasks):
            virt2physmap = self.virt2physmap[task].copy()
            try:
                del virt2physmap[task]
            except KeyError:
                pass
            if virt2physmap:
                proclist = virt2physmap.keys()
                proclist.sort()
                taskstr = self.long_to_str(task)
                stats.append(("Processors to which task %s was assigned (besides %s)" % (taskstr, taskstr), proclist))
        if stats:
            self.statistics.append(("Processor/task mappings", stats))

    def report_parameters(self):
        "Report various execution parameters."
        stats = [("Number of processors", self.numtasks),
                 ("Random-number seed", self.random_seed)]
        ncptl_command = []
        for arg in sys.argv:
            clean_arg = arg
            clean_arg = string.replace(clean_arg, "\\", "\\\\")
            clean_arg = string.replace(clean_arg, '"', '\\"')
            if string.find(clean_arg, " ") != -1:
                clean_arg = string.replace(clean_arg, "'", "\\'")
                clean_arg = "'%s'" % clean_arg
            ncptl_command.append(clean_arg)
        ncptl_command = string.join(ncptl_command, " ")
        stats.append(("Command line", ncptl_command))
        stats.append(("Timestamp", time.asctime(time.localtime(time.time()))))
        self.statistics.append(("Execution parameters", stats))

    def gather_statistics(self):
        "Report a variety of statistics."
        self.statistics = []
        self.report_parameters()
        self.report_all_traffic()
        self.report_processor_traffic()
        self.report_processor_peers()
        self.report_bisection()
        self.report_virtual_physical()
        self.report_all_events()
        self.report_processor_event_sets()
        self.report_processor_events()


    #----------------------#
    # Statistics-reporting #
    # functions            #
    #----------------------#

    def get_statistics_triples(self):
        "Return statistics as triples of (category, key, value)"
        triples = []
        inttypes = [types.IntType, types.LongType]
        for category, database in self.statistics:
            if self.exclusions.has_key(category):
                continue
            for key, value in database:
                if self.exclusions.has_key(key):
                    continue
                if type(value) == types.ListType:
                    valuefield = self.list_to_range_string(value)
                elif type(value) == types.StringType:
                    valuefield = value
                elif type(value) in inttypes:
                    valuefield = value
                else:
                    self.errmsg.error_internal("Unknown variable type %s" % type(value))
                triples.append((category, key, valuefield))
        return triples

    def output_text_statistics(self):
        "Output as text all of the statistics gathered."

        # Sort the statistics triples into tuples of {category,
        # key/value list}.
        catcontents = []
        prevcategory = ""
        for category, key, value in self.get_statistics_triples():
            if category != prevcategory:
                catcontents.append((category, []))
                prevcategory = category
            catcontents[-1][-1].append((key, value))

        # Process each category in turn.
        output = []
        for category, keys_values in catcontents:
            # Output the category header.
            output.append(category)
            output.append("-" * len(category))

            # Find the maximum key length and value digits (when an integer).
            maxkeylen = 0
            maxintdigits = 0
            for key, value in keys_values:
                if maxkeylen < len(key):
                    maxkeylen = len(key)
                if type(value) != types.StringType:
                    valuestr = self.long_to_str(value)
                    if maxintdigits < len(valuestr):
                        maxintdigits = len(valuestr)

            # Format each {key: value} pair.
            for key, value in keys_values:
                keystring = "%-*.*s" % (maxkeylen+1, maxkeylen+1, key+":")
                if type(value) == types.StringType:
                    valuestring = value
                else:
                    valuestring = "%*.*s" % (maxintdigits, maxintdigits, self.long_to_str(value))
                output.append("  %s %s" % (keystring, valuestring))
            if category != catcontents[-1][0]:
                output.append("")
        return output

    def output_separated_statistics(self):
        "Output statistics in an easy-to-parse format."
        output = []
        prevcategory = ""
        separator_appeared_lines = []
        lineno = 1
        for category, key, value in self.get_statistics_triples():
            def format_sep_string(somestring):
                "Escape double quotes and backslashes then add double quotes."
                return '"' + string.replace(string.replace(somestring, "\\", "\\\\"), '"', '\\"') + '"'
            if category == prevcategory:
                categorystring = ""
            else:
                categorystring = format_sep_string(category)
            prevcategory = category
            keystring = format_sep_string(key)
            if type(value) == types.StringType:
                valuestring = format_sep_string(value)
            else:
                valuestring = self.long_to_str(value)
            if (self.output_separator
                and string.find(string.join((categorystring, keystring, valuestring), ""),
                                self.output_separator) != -1):
                separator_appeared_lines.append(lineno)
            output.append(string.join((categorystring, keystring, valuestring),
                                      self.output_separator))
            lineno = lineno + 1
        if separator_appeared_lines:
            lineliststring = self.list_to_range_string(separator_appeared_lines)
            if len(separator_appeared_lines) == 1:
                self.errmsg.warning('Column separator %s appears within a field in line %s' %
                                    (repr(self.output_separator), lineliststring))
            else:
                self.errmsg.warning('Column separator %s appears within a field in the following lines: %s' %
                                (repr(self.output_separator), lineliststring))
        return output

    def output_excel_csv_statistics(self):
        "Output statistics in Microsoft Excel's quirky CSV format."
        output = []
        prevcategory = ""
        for category, key, value in self.get_statistics_triples():
            def format_excel_string(somestring):
                "Apply Excel's string-formatting rules (inferred, not documented)."
                excelstring = somestring
                excelstring = string.replace(excelstring, '"', '""')
                if string.find(excelstring, "-") != -1 and string.find(excelstring, ",") == -1:
                    needequals = 1
                elif re.match(r'^[-+.\d]+$', excelstring):
                    needequals = 1
                else:
                    needequals = 0
                excelstring = '"' + excelstring + '"'
                if needequals:
                    excelstring = "=" + excelstring
                return excelstring
            if category == prevcategory:
                categorystring = ""
            else:
                categorystring = format_excel_string(category)
            prevcategory = category
            keystring = format_excel_string(key)
            if type(value) == types.StringType:
                valuestring = format_excel_string(value)
            else:
                valuestring = self.long_to_str(value)
            output.append("%s,%s,%s" % (categorystring, keystring, valuestring))
        return output
