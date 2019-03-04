#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# Use LaTeX + PSTricks to visualize a coNCePTuaL program's dynamic
# behavior
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# 
# Copyright (C) 2003, Triad National Security, LLC
# All rights reserved.
# 
# Copyright (2003).  Triad National Security, LLC.  This software
# was produced under U.S. Government contract 89233218CNA000001 for
# Los Alamos National Laboratory (LANL), which is operated by Los
# Alamos National Security, LLC (Triad) for the U.S. Department
# of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR TRIAD
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
#   * Neither the name of Triad National Security, LLC, Los Alamos
#     National Laboratory, the U.S. Government, nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY TRIAD AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TRIAD OR CONTRIBUTORS BE
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
import tempfile
import time
import string
import re
import types
import random
from math import *      # May be needed by --arrow-width
from ncptl_config import ncptl_config
from pyncptl import *


class NCPTL_CodeGen(codegen_interpret.NCPTL_CodeGen):

    #---------------------#
    # Exported functions  #
    # (called from the    #
    # compiler front end) #
    #---------------------#

    def __init__(self, options=None):
        "Initialize visualization."
        codegen_interpret.NCPTL_CodeGen.__init__(self, options)
        self.backend_name = "latex_vis"
        self.backend_desc = "LaTeX-based communication visualization"
        self.parent = self.__class__.__bases__[0]
        self.allevents = 0        # 0=only comm. events take time; 1=all events do
        self.nodediameter = 0.4   # A node's diameter in inches
        self.binary_tasks = 0     # 1=output tasks in binary; 0=decimal
        self.annotations = 0      # 0=no annotations; 1=annotate comms.; 2=annotate everything; 3=use the OMITTED_OP method to decide
        self.sourcelines = 0      # 1=include source-code lines in annotations; 0=don't
        self.timeline = 1         # 1=indicate the direction of time; 0=don't
        self.comm_ops = {}        # List of all communication operations
        self.zerolatency = 0      # 1=messages arrive at the same time they're sent; 0=one time unit later
        self.arrowwidth = None    # Function to map a message size to a line width or None for default
        self.arrowwidth_string = "N/A"    # String version of the above
        self.arrowstagger = 2     # Number of points by which to stagger overlapping arrows
        self.arrowoffset = {}     # Previous PSTricks offset of a given arrow
        self.collectives_drawn = {}  # Set of collectives already drawn
        for op in ("SEND", "RECEIVE", "WAIT_ALL", "SYNC", "MCAST", "REDUCE"):
            self.comm_ops[op] = 1
        self.omitted_op = lambda o: 1  # Map from an operation to {1=annotate; 0=don't annotate}

    def generate(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        'Interpret an AST and visualize the events that were executed.'
        self.generate_initialize(ast, filesource, sourcecode)

        # Give every event list a pointer back to us and an indication
        # of its associated task number.
        for task in range(0, self.numtasks):
            self.eventlist[task].codegen = self
            self.eventlist[task].task = task

        # Remove log-file options and add an option for showing all events.
        self.set_log_file_status(0)
        self.options.extend([
            ["arrowwidth",
             "Python expression to map m, representing a message size in bytes, to an arrow width in points",
             "arrow-width", "R", "1"],
            ["binary", "Display task numbers in binary rather than decimal (0=decimal; 1=binary)",
             "binary-tasks", "B", 0L],
            ["zerolatency", "Depict communication as having zero latency (0=unit latency; 1=zero latency)",
             "zero-latency", "Z", 0L],
            ["sourcelines",
             "Associate source-code line numbers with each event annotation (0=no; 1=yes)",
             "source-lines", "L", 0L],
            ["arrowstagger",
             "Number of points by which to stagger overlapping arrows",
             "stagger", "G", 2L],
            ["annotate",
             'Annotation level (0=no annotations; 1=annotate communication events; 2=annotate all events; "<event>..."=annotate only the specified events)',
             "annotate", "A", "0"],
            ["allevents",
             "Events requiring nonzero time to complete (0=only communication events; 1=every event)",
             "every-event", "E", 0L]])

        # Perform a prefix traversal (roughly) and visualize the results.
        self.process_node(ast)
        self.generate_finalize(ast, filesource, sourcecode)
        return self.visualize_events(filesource, filetarget, sourcecode)

    def compile_only(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Run latex on the input file to produce DVI output."

        # Determine the names of the files to use.
        infilename, outfilename = self.write_latex_code(progfilename, codelines, outfilename, keepints)
        infilebase = os.path.basename(os.path.splitext(infilename)[0])
        dvifilename = infilebase + ".dvi"

        # Run latex on the input file.
        latexcmd = self.lookup_variable("LATEX", "latex")
        latex_string = "%s -interaction=nonstopmode %s" % (latexcmd, infilename)
        if verbose:
            sys.stderr.write("\n%s\n" % latex_string)
        exitstatus = os.system(latex_string)
        if exitstatus:
            self.errmsg.error_fatal("command aborted with exit code %d" % (exitstatus>>8))

        # Rename the DVI file if necessary.
        if dvifilename != outfilename:
            if verbose:
                sys.stderr.write("# Renaming %s to %s ...\n" % (dvifilename, outfilename))
            os.rename(dvifilename, outfilename)

        # Clean up intermediate files unless instructed not to.
        intermediates = (infilename, infilebase+".aux", infilebase+".log")
        intermediates_str = string.join(intermediates, ", ")
        if keepints:
            if verbose:
                sys.stderr.write("# Not deleting %s\n" % intermediates_str)
        else:
            if verbose:
                sys.stderr.write("# Deleting %s\n" % intermediates_str)
            for delfilename in intermediates:
                try:
                    os.remove(delfilename)
                except OSError, errmsg:
                    sys.stderr.write("# %s --> %s\n" % (delfilename, errmsg))

        # Finish up.
        if verbose:
            sys.stderr.write("# Files generated: %s\n" % outfilename)

    def compile_and_link(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Pipe the LaTeX code through latex and dvips."

        # Determine the names of the files to use.
        infilename, outfilename = self.write_latex_code(progfilename, codelines, outfilename, keepints)
        infilebase = os.path.basename(os.path.splitext(infilename)[0])

        # Determine the names of the commands to invoke.
        latexcmd = self.lookup_variable("LATEX", "latex")
        dvipscmd = self.lookup_variable("DVIPS", "dvips")

        # Run latex on the input file.
        latex_string = "%s -interaction=nonstopmode %s" % (latexcmd, infilename)
        if verbose:
            sys.stderr.write("\n%s\n" % latex_string)
        exitstatus = os.system(latex_string)
        if exitstatus:
            self.errmsg.error_fatal("command aborted with exit code %d" % (exitstatus>>8))

        # Run dvips on the generated .dvi file.
        dvifilename = infilebase + ".dvi"
        if outfilename == dvifilename:
            dvips_outfile = infilebase + ".%d" % random.randint(100000, 999999)
        else:
            dvips_outfile = outfilename
        dvips_string = "%s -E %s -o %s" % (dvipscmd, dvifilename, dvips_outfile)
        if verbose:
            sys.stderr.write("\n%s\n" % dvips_string)
        exitstatus = os.system(dvips_string)
        if exitstatus:
            self.errmsg.error_fatal("command aborted with exit code %d" % (exitstatus>>8))
        if verbose:
            sys.stderr.write("\n")
        if outfilename == dvifilename:
            if verbose:
                sys.stderr.write("# Renaming %s to %s ...\n" % (dvips_outfile, outfilename))
            os.rename(dvips_outfile, outfilename)

        # Fix the PostScript bounding box.
        self.fix_bounding_box(outfilename, verbose)

        # Clean up intermediate files unless instructed not to.
        intermediates = [infilename, infilebase+".aux", infilebase+".log"]
        if outfilename != dvifilename:
            intermediates.append(dvifilename)
        intermediates_str = string.join(intermediates, ", ")
        if keepints:
            if verbose:
                sys.stderr.write("# Not deleting %s\n" % intermediates_str)
        else:
            if verbose:
                sys.stderr.write("# Deleting %s\n" % intermediates_str)
            for delfilename in intermediates:
                try:
                    os.remove(delfilename)
                except OSError, errmsg:
                    sys.stderr.write("# %s --> %s\n" % (delfilename, errmsg))

        # Finish up.
        if verbose:
            sys.stderr.write("# Files generated: %s\n" % outfilename)
        return outfilename


    #------------------#
    # Internal utility #
    # functions        #
    #------------------#

    def lookup_variable(self, varname, defvalue):
        "Look for a variable in the environment and coNCePTuaL configuration file."
        if os.environ.has_key(varname):
            return os.environ[varname]
        elif ncptl_config.has_key(varname):
            return ncptl_config[varname]
        else:
            return defvalue

    def get_filenames(self, progfilename, outfilename, keepints):
        "Return the desired input (.tex) and output (.eps) filenames."
        if progfilename == "<command line>":
            progfilename = "a.out.ncptl"
        if outfilename == "-":
            outfilename = os.path.splitext(progfilename)[0]
            outfilename = outfilename + ".eps"
        if keepints:
            # If we plan to keep the .tex file, derive it's name from outfilename.
            infilename = os.path.splitext(outfilename)[0]
            infilename = infilename + ".tex"
        else:
            # If we plan to discard the .tex file then give it a unique name.
            tempfile.tempdir = os.path.dirname(outfilename)
            tempfile.template = "latex_" + str(os.getpid())
            while 1:
                fbase = tempfile.mktemp()
                if not os.path.isfile(fbase + ".tex"):
                    break
            infilename = fbase + ".tex"
        return (infilename, outfilename)

    def get_bboxes_from_ghostscript(self, gscmd, gs_string, verbose=0):
        """Invoke Ghostscript with -sDEVICE=bbox on a file and return
        the BoundingBox and/or HiResBoundingBox."""
        if verbose:
            sys.stderr.write("%s\n" % gs_string)
        gs_pipe = os.popen(gs_string, "r")
        newbbox = filter(lambda s: string.find(s, "BoundingBox:") != -1,
                         gs_pipe.readlines())
        exitstatus = gs_pipe.close()
        if exitstatus:
            self.errmsg.warning("Command %s aborted with exit code %d" % (repr(gscmd), exitstatus>>8))
            sys.stderr.write("\n")
            return []
        if newbbox == []:
            self.errmsg.warning("Command %s failed to return a valid bounding box" % repr(gscmd))
            sys.stderr.write("\n")
            return []
        return newbbox

    def fix_bounding_box(self, epsfilename, verbose=0):
        "Try running Ghostscript to tighten the bounding box."

        # Read the entire EPS file into memory.
        old_epsfile = open(epsfilename)
        old_eps = old_epsfile.readlines()
        old_epsfile.close()

        # Run Ghostscript once just to verify that it works.
        gscmd = self.lookup_variable("GS", "gs")
        gs_string = ("%s -r72 -q -dNOPAUSE -dBATCH -sDEVICE=bbox -c '<< /ImagingBBox [ -100000. -100000. 100000. 100000. ] >> setpagedevice' - 2>&1 < %s" %
                     (gscmd, epsfilename))
        new_bbox = self.get_bboxes_from_ghostscript(gscmd, gs_string, verbose)
        if new_bbox == []:
            return

        # Patch the EPS file to translate the image's origin to (0, 0).
        set_papersize = "-sPAPERSIZE=a0"
        old_bbox = filter(lambda s: s[0:14]=="%%BoundingBox:", old_eps)
        bbox_match = re.match(r'%%BoundingBox:\s*([-\d]+)\s+([-\d]+)\s+([-\d]+)\s+([-\d]+)', old_bbox[0])
        if old_bbox != [] and bbox_match:
            old_bbox = old_bbox[0]
            old_coords = []
            for c in range(4):
                old_coords.append(int(bbox_match.group(c+1)))
            xlated_coords = (0, 0, old_coords[2]-old_coords[0], old_coords[3]-old_coords[1])
            inserted = 0
            for lineno in range(len(old_eps)):
                if old_eps[lineno] == old_bbox:
                    old_eps[lineno] = "%%%%BoundingBox: %d %d %d %d\n" % xlated_coords
                elif old_eps[lineno][:10] == "%%EndSetup":
                    inserted = lineno + 1
                elif not inserted and old_eps[lineno][0] != "%":
                    inserted = lineno
            if inserted:
                old_eps.insert(inserted, "%d %d translate\n" % (-old_coords[0], -old_coords[1]))
            set_papersize = "-g%dx%d" % (2*xlated_coords[2], 2*xlated_coords[3])
            old_epsfile = open(epsfilename, "w")
            old_epsfile.writelines(old_eps)
            old_epsfile.close()
            old_bbox = string.strip(old_bbox)
        else:
            old_bbox = "[not found]"

        # When Ghostscript calculates the size of the bounding box it
        # truncates it at the paper size.  Hence, we run Ghostscript a
        # second time, explicitly specifying a paper size that is
        # hopefully much larger than necessary.  (We previously
        # doubled the estimated bounding-box size.)
        gs_string = ("%s %s -r72 -q -dNOPAUSE -dBATCH -sDEVICE=bbox -c '<< /ImagingBBox [ -100000. -100000. 100000. 100000. ] >> setpagedevice' - 2>&1 < %s" %
                     (gscmd, set_papersize, epsfilename))
        new_bbox = self.get_bboxes_from_ghostscript(gscmd, gs_string, verbose)
        if new_bbox == []:
            return

        # Replace the old bounding box with a new, tighter one.
        try:
            xlated_bbox = "[not found]"
            new_bbox = map(string.strip, new_bbox)
            new_epsfile = open(epsfilename, "w", 0666)
            for oneline in map(string.rstrip, old_eps):
                if oneline[0:14] == "%%BoundingBox:":
                    xlated_bbox = oneline
                    for oneline in new_bbox:
                        new_epsfile.write("%s\n" % oneline)
                else:
                    new_epsfile.write("%s\n" % oneline)
            new_epsfile.close()
            if verbose:
                sys.stderr.write("# Original PostScript bounding box:\n")
                sys.stderr.write("#    %s\n" % old_bbox)
                sys.stderr.write("# Translated PostScript bounding box:\n")
                sys.stderr.write("#    %s\n" % xlated_bbox)
                sys.stderr.write("# Refined PostScript bounding boxes:\n")
                for oneline in new_bbox:
                    sys.stderr.write("#    %s\n" % oneline)
                sys.stderr.write("\n")
        except IOError, (errno, strerror):
            self.errmsg.warning("Unable to tighten %s's bounding box (%s)" % (epsfilename, strerror),
                                    filename=self.backend_name)

    def write_latex_code(self, progfilename, codelines, outfilename, keepints):
        """
             Output the given LaTeX code to a file and return the
             input and output filenames.
        """
        infilename, outfilename = self.get_filenames(progfilename, outfilename, keepints)
        try:
            infile = open(infilename, "w")
            for oneline in codelines:
                infile.write("%s\n" % oneline)
            infile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("unable to produce %s (%s)" % (infilename, strerror),
                                    filename=self.backend_name)

        # Return the input and output filenames.
        return (infilename, outfilename)

    def task_time_to_node(self, task, evtime):
        "Map a {task, time} pair to a psmatrix node (really coordinates)."
        return "{%d,%d}" % (evtime+1, task+1)

    def draw_separator(self, tasktimelist, extraparams=None):
        "Draw a horizontal separator rule."
        # Initialize the list of parameters.
        params = [r'\ruleparams']
        if extraparams:
            params.extend(extraparams)
        params = string.join(params, ",")

        # Draw the rule.
        latexcode = []
        latexcode.append(r"\drawline[%s]" % params)
        for taskval, timeval in tasktimelist:
            for angle in (180, 0):
                latexcode.append(r"  ([angle=%d]M-1-%d-%d|!\nbetween<%d-%d,%d-%d>)" %
                                 (angle, timeval+2, taskval+1,
                                  timeval+1, timeval+2, taskval+1, taskval+1))
        return latexcode

    def draw_arrow(self, sendtask, sendtime, recvtask, recvtime, msgsize, drawcmd=None, extraparams=None):
        "Return code to draw an arrow from a sender to a receiver."
        # Initialize the list of parameters.
        params = []
        if extraparams:
            params.extend(extraparams)

        # Draw an arrow with the appropriate size, shape, and other
        # parameters.
        if drawcmd == None:
            if recvtime == sendtime:
                # We were run with --zero-latency=1 and are sending
                # and receiving in the same time step.
                drawcmd = r"\nccurve"
                if recvtask > sendtask:
                    angleA = 45
                    angleB = 135
                    ncurv = 1.0 / (recvtask-sendtask)
                elif sendtask > recvtask:
                    angleA = -135
                    angleB = -45
                    ncurv = 1.0 / (sendtask-recvtask)
                else:
                    if params == []:
                        params = ""
                    else:
                        params = "[" + string.join(params, ",") + "]"
                    return [r"\nccircle%s{<-}%s{0.75}" % (params, self.task_time_to_node(sendtask, sendtime))]
                params.extend([
                    "angleA=%g" % angleA,
                    "angleB=%g" % angleB,
                    "ncurv=%g" % ncurv])
            else:
                # Use lines for short distances and arcs for long
                # distances unless otherwise specified.
                if recvtime - sendtime > 1:
                    drawcmd = r"\ncarc"
                else:
                    drawcmd = r"\ncline"

            # Extend the list of parameters with a linewidth and arrowscale.
            if self.arrowwidth != None:
                # Specify the arrow line width and arrowhead scale.
                # The arrowhead scale is 2.0 when the linewidth is
                # 1.0bp and scales the arrow width proportional to the
                # line width.
                try:
                    linewidth = float(self.arrowwidth(float(msgsize)))
                except:
                    self.errmsg.error_fatal('An "%s" error occurred on "%s" while evaluating the Python expression "%s"' %
                                            (sys.exc_info()[0], sys.exc_info()[1], self.arrowwidth_string))
                arrowscale = (3.0+linewidth) / (1.0+linewidth)
                params.extend([
                    "linewidth=%gbp" % linewidth,
                    "arrowscale=%g" % arrowscale])

            # Separate otherwise overlapping arrows.
            arrowdesc = (sendtask, sendtime, recvtask, recvtime)
            try:
                arrowoffset = self.arrowoffset[arrowdesc]
                if arrowoffset > 0:
                    arrowoffset = -arrowoffset
                else:
                    arrowoffset = self.arrowstagger - arrowoffset
            except KeyError:
                arrowoffset = 0
            self.arrowoffset[arrowdesc] = arrowoffset
            if arrowoffset != 0:
                params.extend(["offset=%gbp" % arrowoffset])

        # Define the sending and receiving nodes.
        if floor(sendtime) != ceil(sendtime) or floor(recvtime) != ceil(recvtime):
            if sendtask != recvtask or sendtime >= recvtime:
                self.errmsg.error_internal("Fractional times are implemented only for downward, vertical arrows")
            drawcmd = r"\psline"
            if floor(sendtime) == ceil(sendtime):
                sendnode = "([angle=270]M-1-%d-%d)" % (sendtime+1, sendtask+1)
            else:
                sendnode = (r"(!\nbetween<%d-%d,%d-%d>)" %
                            (floor(sendtime)+1, ceil(sendtime)+1,
                             sendtask+1, sendtask+1))
            if floor(recvtime) == ceil(recvtime):
                recvnode = "([angle=90]M-1-%d-%d)" % (recvtime+1, recvtask+1)
            else:
                recvnode = (r"(!\nbetween<%d-%d,%d-%d>)" %
                            (floor(recvtime)+1, ceil(recvtime)+1,
                             recvtask+1, recvtask+1))
        else:
            sendnode = self.task_time_to_node(sendtask, sendtime)
            recvnode = self.task_time_to_node(recvtask, recvtime)

        # Finalize the parameters, get the list of nodes, and draw the arrow.
        if params == []:
            params = ""
        else:
            params = "[" + string.join(params, ",") + "]"
        return [drawcmd + params + sendnode + recvnode]

    def task_to_label(self, task):
        "Convert a task number to a string."
        if self.binary_tasks:
            # Binary (fixed number of bits)
            numbits = int(ncptl_func_bits(self.numtasks-1))
            bitlist = [0] * numbits
            for b in range(0, numbits):
                if task & (1<<b):
                    bitlist[b] = 1
            bitlist.reverse()
            return string.join(map(str, bitlist), "")
        else:
            # Decimal
            return str(int(task))


    #----------------#
    # Hook functions #
    #----------------#

    def n_program_PROCESS_OPTION(self, localvars):
        "Process command-line options of importance to us."
        opt = localvars["opt"]

        # Define a helper function to process flag-style options.
        def boolean_option(self=self, opt=opt):
            "Return the value of the current option if it's 0 or 1, else abort."
            result = int(opt[-1])
            if result not in [0, 1]:
                self.errmsg.error_fatal("the --%s option accepts only 0 or 1" % opt[2])
            return result

        if opt[0] == "sourcelines":
            self.sourcelines = boolean_option()
            return 1
        elif opt[0] == "allevents":
            self.allevents = boolean_option()
            return 1
        elif opt[0] == "binary":
            self.binary_tasks = boolean_option()
            return 1
        elif opt[0] == "zerolatency":
            self.zerolatency = boolean_option()
            return 1
        elif opt[0] == "arrowwidth":
            if opt[-1] == "1":
                # Do nothing if we were given the default width.
                return 1
            try:
                self.arrowwidth = eval("lambda m: " + opt[-1])
            except:
                self.errmsg.error_fatal('An "%s" error ("%s") occurred while parsing the Python expression "%s"' % (sys.exc_info()[0], sys.exc_info()[1], opt[-1]))
            self.arrowwidth_string = opt[-1]
            return 1
        elif opt[0] == "annotate":
            # Ensure that the --annotate option was given either a
            # list of strings or the numbers 0, 1, or 2.  Define the
            # OMITTED_OP method as an appropriate event filter.
            try:
                # Number -- ensure value is valid.
                self.annotations = int(opt[-1])
                if self.annotations == 0:
                    # OMITTED_OP isn't used if we're not displaying annotations.
                    pass
                elif self.annotations == 1:
                    # Display only communication events.
                    self.omitted_op = lambda o, co=self.comm_ops: not co.has_key(o)
                elif self.annotations == 2:
                    # Display everything except new-statement events.
                    self.omitted_op = lambda o: o == "NEWSTMT"
                else:
                    # Complain about bad input.
                    self.errmsg.error_fatal("if --%s is given a number, that number must be either 0, 1, or 2" % opt[2])
            except ValueError:
                # String -- split based on commas or spaces and define
                # the OMITTED_OP function to look up a value in the
                # resulting list.
                self.annotations = 3
                keepers = {}
                for op in re.split(r'[\s,]*', opt[-1]):
                    keepers[string.upper(op)] = 1
                self.omitted_op = lambda o, k=keepers: not k.has_key(o)
            return 1
        elif opt[0] == "arrowstagger":
            self.arrowstagger = opt[-1]
            return 1
        elif hasattr(self.parent, "n_program_PROCESS_OPTION"):
            # Give our parent a chance to process the current option.
            return self.parent.n_program_PROCESS_OPTION(self, localvars)
        else:
            return 0

    def process_reduce_READY(self, localvars):
        "Store pointers to all of our peer events."
        event = localvars["event"]
        try:
            if self.reduces_processed.has_key(event.collective_id):
                return
        except AttributeError:
            self.reduces_processed = {}
            pass
        self.reduces_processed[event.collective_id] = 1
        taskusage = localvars["taskusage"]
        clique = {}
        for peer in taskusage.keys():
            clique[self.eventlist[peer].get_first_incomplete()] = 1
        clique = clique.keys()
        for event in clique:
            event.clique = clique
        return None


    #------------------#
    # Method overrides #
    #------------------#

    def process_wait_all(self, wait_event):
        "Process a WAIT_ALL event.  Keep track of corresponding sends/receives."
        wait_event.await_receives = len(filter(lambda ev: ev.operation == "RECEIVE",
                                               self.pendingevents[wait_event.task]))
        wait_event.await_sends = len(filter(lambda ev: ev.operation == "SEND",
                                            self.pendingevents[wait_event.task]))
        return codegen_interpret.NCPTL_CodeGen.process_wait_all(self, wait_event)

    class EventList(codegen_interpret.NCPTL_CodeGen.EventList):
        def message_latency(self, event):
            "Return the message latency for a given event."
            return self.__class__.__bases__[0].message_latency(self, event) - self.codegen.zerolatency

        def post_complete_overhead(self, event):
            "Return the overhead between posting and completing an event."
            # Blocking receives, multicasts, and wait-alls can't
            # complete in the same time step in which they're posted.
            if event.blocking and (event.operation in ["RECEIVE", "MCAST"]
                                   or (event.operation == "WAIT_ALL"
                                       and (event.await_receives
                                            or event.await_sends))
                                   or (event.operation == "REDUCE"
                                       and event.task in event.peers[1])):
                return 1
            else:
                return 0

        def complete_post_overhead(self, prev_ev, this_ev):
            "Return the overhead between completing an event and posting the next event."
            prevop = prev_ev.operation
            prev_is_comm = self.codegen.comm_ops.has_key(prevop)

            if self.codegen.zerolatency and prev_is_comm and prev_ev.blocking:
                # Blocking communication operations have unit overhead
                # to make up for having zero latency.
                return 1
            if prevop == "SEND" and prev_ev.blocking:
                # Completing a blocking send takes unit time.
                return 1
            if prev_is_comm:
                # No other communication statement takes any time to complete.
                return 0
            if prevop == "NEWSTMT":
                # New statements never take any time to complete.
                return 0

            # The remaining events take either no time or unit time to
            # complete depending upon the value of the ALLEVENTS flag.
            return self.codegen.allevents

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
        "Do nothing; visualization backends do not produce output."
        return self.process_no_op(event)

    def process_log(self, event):
        "Do nothing; visualization backends do not produce log files."
        return self.process_no_op(event)

    def process_aggregate(self, event):
        "Do nothing; visualization backends do not produce log files."
        return self.process_no_op(event)


    #----------------------------------#
    # Top-level visualization function #
    #----------------------------------#

    def visualize_events(self, filesource, filetarget, sourcecode):
        'Visualize all of the events dumped by the interpret backend.'

        # Tell each event its offset into the corresponding task's event list.
        for eventlist in self.eventlist:
            for eventnum in range(0, len(eventlist.events)):
                eventlist.events[eventnum].offset = eventnum

        # Combine all of the event lists and sort the result first by
        # posting time and then by task number.
        eventlist = []
        eventnum = 0
        for evlist in self.eventlist:
            for event in evlist.events:
                eventlist.append((event.posttime, event.task, eventnum, event))
                eventnum = eventnum + 1
        eventlist.sort()
        eventlist = map(lambda (pt, tn, en, ev): ev, eventlist)

        # Find the maximum event completion or posting time.
        self.maxtime = max(filter(lambda ct: ct!=None, map(lambda ev: ev.completetime, eventlist)) +
                           map(lambda ev: ev.posttime, eventlist))

        # Produce a LaTeX prologue.
        latexcode = []
        latexcode.extend(self.latex_header_comments(filesource, filetarget, sourcecode, eventlist))
        latexcode.append("")
        latexcode.extend(self.latex_preamble())
        latexcode.append("")

        # Draw all of the nodes (one for each {task, time} pair).
        latexcode.extend(self.latex_draw_nodes())
        latexcode.append("")

        # Define a mapping from an operation to a method.
        op2method = {
            "SEND"     : self.vis_send,
            "SYNC"     : self.vis_sync,
            "MCAST"    : self.vis_mcast,
            "REDUCE"   : self.vis_reduce}

        # Process every event on every task.
        latexcode.extend([
            r"% Draw all of the communication operations.",
            r"% PLACEHOLDER: COMMUNICATION",
            r"\psset{linecolor=\sendrecvcolor}"])
        for event in eventlist:
            try:
                latexcode.extend(op2method[event.operation](event))
            except KeyError:
                pass
        latexcode.append("")

        # Draw Xs atop deadlocked nodes.
        latexcode.extend([
            r'% Draw an "X" atop every permanently blocked node.',
            r"% PLACEHOLDER: DEADLOCK"])
        for task in range(0, self.numtasks):
            if self.stucktimes[task] != None:
                latexcode.append(r'\drawX{%d}' % task)
        latexcode.append("")

        # Optionally annotate event postings and completions.
        if self.annotations > 0:
            latexcode.extend(self.latex_annotate_nodes(eventlist))
            latexcode.append("")

        # Produce a LaTeX epilogue.
        latexcode.extend(self.latex_epilogue())

        # Return the resulting LaTeX code.
        return latexcode


    #------------------------#
    # Functions that produce #
    # boilerplate LaTeX code #
    #------------------------#

    def latex_header_comments(self, filesource, filetarget, sourcecode, eventlist):
        "Create a log file, convert to LaTeX comments, and delete the file."

        # Define a helper function to use below.
        def op_list_to_string(oplist):
            'Concatenate the strings in OPLIST or return "[none]" if OPLIST is empty.'
            if oplist == []:
                return "[none]"
            else:
                return string.join(oplist, " ")

        # Acquire a list of which operations are annotated and which aren't.
        ops_used = {}
        for event in eventlist:
            ops_used[event.operation] = 1
        ops_used = ops_used.keys()
        ops_used.sort()
        ops_annotated = []
        ops_not_annotated = []
        for op in ops_used:
            if self.omitted_op(op):
                ops_not_annotated.append(op)
            else:
                ops_annotated.append(op)
        ops_used = op_list_to_string(ops_used)
        ops_annotated = op_list_to_string(ops_annotated)
        ops_not_annotated = op_list_to_string(ops_not_annotated)

        # We have to reinitialize the run-time library because
        # codegen_interpret already called ncptl_finalize().
        ncptl_init(NCPTL_RUN_TIME_VERSION, self.filename)

        # Add a few extra prologue comments.
        if filesource != "<command line>":
            filesource = os.path.abspath(filesource)
        ncptl_log_add_comment("Source program", filesource)
        ncptl_log_add_comment("Python version", re.sub(r'\s+', " ", sys.version))
        ncptl_log_add_comment("Events annotated", ops_annotated)
        ncptl_log_add_comment("Events not annotated", ops_not_annotated)

        # Create a dummy log file.
        try:
            logfiledesc, logfiletemplate = tempfile.mkstemp(".log", self.backend_name + "-%p-")
        except AttributeError:
            # Handle old Python versions (tested on v1.5).
            tempfile.template = self.backend_name + "-0-"
            logfiletemplate = string.replace(tempfile.mktemp(), "-0-", "-%p-")
        logstate = ncptl_log_open(logfiletemplate, 0L)
        ncptl_log_write_prologue(logstate, sys.executable, self.logfile_uuid,
                                 self.backend_name, self.backend_desc, self.numtasks,
                                 self.options, len(self.options),
                                 string.split(string.rstrip(sourcecode), "\n"))
        ncptl_log_write_epilogue(logstate)
        ncptl_log_close(logstate)
        try:
            os.close(logfiledesc)
        except NameError:
            pass

        # That's the last library call we plan to make.
        ncptl_finalize()

        # Read the contents of the log file into an array and convert
        # hash marks to percent signs (the LaTeX comment character).
        latexcode = []
        logfilename = string.replace(logfiletemplate, "-%p-", "-0-")
        try:
            logfile = open(logfilename)
            for oneline in logfile.readlines():
                latexcode.append(re.sub(r'^#+',
                                        lambda h: "%" * len(h.group(0)),
                                        string.rstrip(oneline)))
            logfile.close()
            os.remove(logfilename)
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("unable to produce %s (%s)" % (logfilename, strerror),
                                    filename=self.backend_name)

        # Separate the epilogue comments from the rest of latexcode.
        commentline = latexcode[0]
        self.epilogue = latexcode
        self.epilogue = self.epilogue[self.epilogue.index(commentline)+1:]
        self.epilogue = self.epilogue[self.epilogue.index(commentline)+1:]
        latexcode = latexcode[:len(latexcode)-len(self.epilogue)]

        # Post-process the generated code.
        latexcmd = self.lookup_variable("LATEX", "latex")
        dvipscmd = self.lookup_variable("DVIPS", "dvips")
        infilename, outfilename = map(os.path.basename,
                                      self.get_filenames(filesource, filetarget, 1))
        infilebase = os.path.basename(os.path.splitext(infilename)[0])
        dvifilename = infilebase + ".dvi"
        latexcode[1:4] = [
            "%",
            "% Platform parameters",
            "% -------------------"]
        latexcode[:0] = [
            latexcode[0],
            "%",
            "% LaTeX + PSTricks code to display graphically a program's",
            "% dynamic communication pattern",
            "%",
            "%% Compile %s into %s using the following commands:" % (infilename, outfilename),
            "%",
            "%%    %s %s" % (latexcmd, infilename),
            "%%    %s -E %s -o %s" % (dvipscmd, dvifilename, outfilename),
            "%",
            "%% You can then safely remove the %s, %s," % (infilename, infilebase+".aux"),
            "%% %s, and %s files." % (infilebase+".log", dvifilename),
            "%"]
        return latexcode

    def latex_preamble(self):
        "Return a LaTeX preamble."
        if self.annotations > 0:
            # Allocate extra room for annotation text.
            colsep = 120
        else:
            colsep = 30
        latexcode = []
        latexcode.extend([
            r"% Initialize LaTeX and PSTricks.",
            r"\documentclass{minimal}",
            r"\usepackage{mathptmx}",
            r"\usepackage{pst-eps}",
            r"\usepackage{pst-node}",
            r"% PLACEHOLDER: PACKAGES",
            r"",
            r"% Configure PSTricks.",
            r"\SpecialCoor",
            r"\psset{%",
            r"  xunit=1pt,",
            r"  yunit=1pt,",
            r"  linewidth=1bp,",
            r"  colsep=%dbp," % colsep,
            r"  rowsep=30bp,",
            r"  arrows=->,",
            r"  arrowscale=2,",
            r"  arrowinset=0.2,",
            r"  mnode=circle%",
            r"}",
            r"",
            r"% Define colors for a variety of purposes.   We use a helper macro,",
            r"% \viscolor, to simplify automatic substitution of colors.",
            r"\newcommand*{\viscolor}[1]{%",
            r"  \def\viscolorhelper##1=##2!{\expandafter\def\csname##1color\endcsname{##2}}%",
            r"  \viscolorhelper#1!%",
            r"}",
            r"\viscolor{node=black}",
            r"\viscolor{sendrecv=blue}",
            r"\viscolor{barrier=green}",
            r"\viscolor{blocked=red}",
            r"\viscolor{timeline=black}",
            r"\viscolor{reduce=magenta}",
            r"% PLACEHOLDER: COLORS",
            r"",
            r"% Force all nodes to be the same size, regardless of content.",
            r"\newcommand*{\task}[1]{\makebox[15bp]{#1}}",
            r"\let\idle=\task",
            r"% PLACEHOLDER: NODESHAPE",
            r"",
            r"% Define a set of parameters for drawing separator rules.",
            r"\newlength{\ruleoffset}",
            r"\setlength{\ruleoffset}{26bp}",
            r"\newcommand*{\ruleparams}{%",
            r"  arrows=-,",
            r"  linewidth=4bp",
            r"}",
            r"",
            r"% Define a macro which refers to a point between two coordinates.",
            r"\def\nbetween<#1-#2,#3-#4>{%",
            r"  tx@NodeDict begin",
            r"    N@M-1-#1-#3 GetCenter exch",
            r"    N@M-1-#2-#4 GetCenter 3 1 roll",
            r"    add 2 div",
            r"    3 1 roll",
            r"    add 2 div",
            r"  end",
            r"}",
            r"",
            r"% Define a macro to simplify drawing separator lines.",
            r"\newcommand*{\drawline}[1][]{%",
            r"  \expandafter\psline\expandafter[#1]%",
            r"}",
            r"",
            r'% Define a macro for drawing an "X" on a blocked task.',
            r"\newcommand*{\drawX}[1]{%",
            r"  \psline[linecolor=\blockedcolor,linewidth=2bp,arrows=-,nodesep=10bp]%",
            r"    ([angle=45]dead#1)([angle=-135]dead#1)",
            r"  \psline[linecolor=\blockedcolor,linewidth=2bp,arrows=-,nodesep=10bp]%",
            r"    ([angle=-45]dead#1)([angle=135]dead#1)",
            r"}",
            r""])
        if self.annotations > 0:
            latexcode.extend([
                r"% Define a macro which attaches annotations to a node.",
                r"\newcommand*{\annotnode}[2]{%",
                r"  \nput{0}{#1}{%",
                r"    \fontsize{7}{8}\selectfont",
                r"    \begin{tabular}{@{}l@{}}#2\end{tabular}}%",
                r"}",
                r""])
        latexcode.extend([
            r"% PLACEHOLDER: DOCUMENT",
            r"",
            r"% The picture begins here.",
            r"\begin{document}",
            r"\thispagestyle{empty}",
            r"% PLACEHOLDER: TEXTOEPS",
            r"\begin{TeXtoEPS}"])
        return latexcode

    def latex_draw_nodes(self):
        "Draw all {task, time} pairs."

        # Output some boilerplate text.
        latexcode = []
        latexcode.append(r"% Draw every task at every time.")
        latexcode.append(r"% PLACEHOLDER: PSMATRIX")
        if self.timeline == 1:
            # Reserve space for the timeline arrow.
            latexcode.append(r"\hspace*{40bp}    % Reserve space for the timeline arrow.")
        latexcode.append(r"\psset{linecolor=\nodecolor}")
        latexcode.append(r"\begin{psmatrix}")

        # Find the time at which each task gets stuck (e.g., because
        # of deadlock).
        self.stucktimes = {}
        for task in range(0, self.numtasks):
            self.stucktimes[task] = None
            eventlist = self.eventlist[task]
            for ev in eventlist.events:
                if ev.completetime == None:
                    self.stucktimes[task] = ev.posttime

        # Find the times at which each task is nonidle.
        nonidle_task_times = {}
        for task in range(0, self.numtasks):
            eventlist = self.eventlist[task]
            for ev in eventlist.events:
                if not self.omitted_op(ev.operation):
                    nonidle_task_times[(task, ev.posttime)] = 1
                    nonidle_task_times[(task, ev.completetime)] = 1

        # Produce code for one row of {time, task} nodes.
        for row in range(0, self.maxtime+1):
            rowcode = []
            for col in range(0, self.numtasks):
                if self.stucktimes[col] == row:
                    # Task col is blocked at time row.
                    rowcode.append(r'\task{\rnode{dead%d}{%s}}' %
                                   (col, self.task_to_label(col)))
                elif nonidle_task_times.has_key((col, row)):
                    # Task col is not blocked at time row.
                    rowcode.append(r'\task{%s}' % self.task_to_label(col))
                else:
                    # Task col is idle at time row.
                    rowcode.append(r'\idle{%s}' % self.task_to_label(col))
            latexcode.append(string.join(rowcode, " & "))
            if row < self.maxtime:
                latexcode[-1] = latexcode[-1] + r' \\[0pt]'
        latexcode.append(r"\end{psmatrix}")
        if self.annotations > 0:
            # Reserve space for the last column of annotations.
            latexcode.append(r"\hspace*{40bp}    % Reserve space for the last column of annotations.")
        return latexcode

    def latex_annotate_nodes(self, eventlist):
        "State the events that occurred at each {task, time} pair."
        node2actions = {}
        omitted_op = self.omitted_op
        comm_ops = self.comm_ops

        # Define a helper function that constructs an action string.
        def store_action(task, time, actionstring, event, node2actions=node2actions, self=self):
            "Associate an action string with a {task, time} pair."

            # Optionally attach line numbers to the action string.
            if self.sourcelines:
                lineno0, lineno1 = event.srclines
                if lineno0 == lineno1:
                    actionstring = actionstring + " [%d]" % lineno0
                else:
                    actionstring = actionstring + " [%d-%d]" % (lineno0, lineno1)
            actionstring = string.replace(actionstring, "_", r"\_")

            # Associate the action string with psmatrix node coordinates.
            node = self.task_time_to_node(task, time)
            try:
                node2actions[node].append(actionstring)
            except KeyError:
                node2actions[node] = [actionstring]

        # Build up a mapping from psmatrix node name to a list of
        # event actions which occur at that node.
        for event in eventlist:
            # Omit certain annotations entirely.
            task = event.task
            op = event.operation
            if omitted_op(op):
                continue

            # Handle non-communicating events differently from
            # communicating events.
            if not comm_ops.has_key(op):
                # Non-communicating operations oughtn't have separate
                # posting and completing times.  Here, we call the
                # unified time the "execution" time.
                if event.posttime != event.completetime:
                    self.errmsg.warning("a %s operation was posted at logical time %d but didn't complete until logical time %d" %
                                        (op, event.posttime, event.completetime))
                store_action(task, event.posttime, "Execute " + op, event)
                continue

            # Store a communicating event's posting-time information
            # and completion-time information.
            if event.blocking:
                async = ""
            else:
                async = "async. "
            store_action(task, event.posttime, "Post " + async + op, event)
            if event.completetime != None:
                store_action(task, event.completetime, "Complete " + async + op, event)

        # Annotate each node with its events.
        latexcode = []
        latexcode.append(r"% Annotate each node with all of the events that occur there.")
        latexcode.append(r"% PLACEHOLDER: ANNOTATIONS")
        nodelist = node2actions.keys()
        nodelist.sort()
        for node in nodelist:
            latexcode.append(r"\annotnode%s{%s}" % (node, string.join(node2actions[node], r" \\ ")))
        return latexcode

    def latex_epilogue(self):
        "Return a LaTeX epilogue."
        latexcode = []
        if self.timeline == 1:
            latexcode.extend([
            r"% Draw a timeline.",
            r"\psset{%",
            r"  linecolor=\timelinecolor,",
            r"  offset=-40bp,",
            r"  nodesep=-20bp,",
            r"  linewidth=2bp,",
            r"  arrowscale=2%",
            r"}",
            r"% PLACEHOLDER: TIMELINE",
            r"\ncline{1,1}{%d,1}" % (self.maxtime+1),
            r"\lput*{90}{Time}",
            r""])
        latexcode.extend([
            r"% Finish up.",
            r"\end{TeXtoEPS}",
            r"% PLACEHOLDER: END"])
        latexcode.extend([""] + self.epilogue)
        latexcode.append(r"\end{document}")
        return latexcode


    #-----------------------------#
    # Functions that use PSTricks #
    # to visualize events         #
    #-----------------------------#

    def vis_send(self, event):
        "Visualize a send operation."
        peer_events = filter(lambda ev, event=event: ev!=event and ev.operation!="SEND", event.clique)
        try:
            recv_ev = peer_events[0]
            return self.draw_arrow(event.task, event.posttime, recv_ev.task, recv_ev.completetime, event.msgsize)
        except IndexError:
            # The event never completed.
            return []

    def vis_sync(self, event):
        "Visualize a barrier operation."

        # Only the first task actually draws anything.
        if event.task != event.peers[0]:
            return []

        # Split the list of peers into contiguous ranges.
        peerlist = event.peers
        peerlist.sort()
        peer_ranges = [[peerlist[0]]]
        for peer in peerlist[1:]:
            if peer == peer_ranges[-1][-1] + 1:
                # Contiguous
                peer_ranges[-1].append(peer)
            else:
                # Not contiguous
                peer_ranges.append([peer])

        # Draw a barrier line for each contiguous range.
        latexcode = []
        for contig in peer_ranges:
            latexcode.extend(self.draw_separator([(contig[0], event.completetime-1),
                                                  (contig[-1], event.completetime-1)],
                                                 extraparams=[r"linecolor=\barriercolor"]))
        return latexcode

    def vis_mcast(self, event):
        "Visualize a multicast operation."

        # The root doesn't draw anything.
        if event.task == event.peers[0]:
            return []

        # Find the matching send event.
        for send_ev in event.clique:
            if send_ev.task == event.peers[0]:
                break
        return self.draw_arrow(send_ev.task, send_ev.posttime,
                               event.task, event.completetime, event.msgsize)

    def vis_reduce(self, event):
        "Visualize a reduction operation."
        # Categorize each peer as a sender and/or receiver.
        senders, receivers = event.peers
        sendhash = {}
        recvhash = {}
        for peer in senders:
            sendhash[peer] = 1
        for peer in receivers:
            recvhash[peer] = 1
        sendevents = []
        recvevents = []
        for ev in event.clique:
            if sendhash.has_key(ev.task):
                sendevents.append(ev)
            if recvhash.has_key(ev.task):
                recvevents.append(ev)

        # Find the maximum completion time of any event in the clique.
        maxcompletetime = max(map(lambda ev: ev.completetime, event.clique))

        # Draw a separator to signify synchronization of senders.
        latexcode = []
        if not self.collectives_drawn.has_key(event.collective_id):
            self.collectives_drawn[event.collective_id] = 1
            event.clique.sort(lambda ev1, ev2: ev1.task-ev2.task)
            tasktimelist = []
            for ev in event.clique:
                tasktimelist.append((ev.task, ev.posttime))
            latexcode.extend(self.draw_separator(tasktimelist,
                                                 extraparams=[r"linecolor=\reducecolor"]))

        # Prepare to disable arrow staggering.
        arrowoffset = self.arrowoffset

        # Draw an arrow from the Post REDUCE down to the separator.
        if sendhash.has_key(event.task):
            latexcode.extend(self.draw_arrow(event.task, event.posttime,
                                             event.task, event.posttime+0.5, event.msgsize,
                                             extraparams=[r"linecolor=\reducecolor"]))

        # Draw an arrow from the separator down to the Complete REDUCE.
        if recvhash.has_key(event.task):
            latexcode.extend(self.draw_arrow(event.task, event.posttime+0.5,
                                             event.task, event.completetime,
                                             event.msgsize,
                                             extraparams=[r"linecolor=\reducecolor"]))

        # Re-enable arrow staggering and return the arrow-drawing code.
        self.arrowoffset = arrowoffset
        return latexcode
