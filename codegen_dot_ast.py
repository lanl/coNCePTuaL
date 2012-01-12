#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# AT&T Labs' DOT graph-drawing language (part of Graphviz)
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# Copyright (C) 2012, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2012).  Los Alamos National Security, LLC.  This software
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
import re
import string
import time
import types
import os
import tempfile
from ncptl_ast import AST
from ncptl_error import NCPTL_Error
from ncptl_variables import Variables
from ncptl_config import ncptl_config


class NCPTL_CodeGen:
    thisfile = globals()["__file__"]

    #---------------------#
    # Exported functions  #
    # (called from the    #
    # compiler front end) #
    #---------------------#

    def __init__(self, options=None):
        "Initialize the DOT code generation module."
        self.errmsg = NCPTL_Error()     # Placeholder until generate is called

        # Process any arguments we were given.
        self.dot_format = "ps"          # File format that dot should generate
        self.extra_dot_code = []        # Arbitrary extra code to write
        self.show_attrs = 1             # 1=output AST node attributes; 0=don't
        self.node_code_chars = 0        # Number of characters at which to truncate node code (0=no node code; -1=all code lines)
        self.show_lines = 1             # 1=output line numbers; 0=don't
        self.show_source_code = 1       # 1=show the complete source code; 0=don't
        self.compress_graph = 0         # 1=save space by eliding chains; 0=show everything
        for arg in range(0, len(options)):
            arg_match = re.match(r'--(format|extra-dot|node-code)=(.*)', options[arg])
            if arg_match:
                argname, argvalue = arg_match.group(1), arg_match.group(2)
                if argname == "format":
                    self.dot_format = argvalue
                elif argname == "extra-dot":
                    self.extra_dot_code.append(argvalue)
                elif argname == "node-code":
                    argvalue = int(argvalue)
                    if argvalue == -1:
                        self.node_code_chars = sys.maxint
                    else:
                        self.node_code_chars = argvalue
            elif options[arg] == "--compress":
                self.compress_graph = 1
            elif options[arg] == "--no-attrs":
                self.show_attrs = 0
            elif options[arg] == "--no-lines":
                self.show_lines = 0
            elif options[arg] == "--no-source":
                self.show_source_code = 0
            elif options[arg] == "--help":
                self.show_help()
                sys.exit(0)

    def show_help(self):
        "Output a help message."
        print """\
Usage: dot_ast [OPTION...]
  --format=<string>          Output format for dot [default: "ps"]
  --node-code=<number>       Maximum number of characters of coNCePTuaL code
                             to display within a dot node [default: infinity]
  --extra-dot=<string>       Extra dot code to process within the digraph
  --compress                 Save space on the page by eliding chains of nodes
  --no-attrs                 Don't display AST node attributes
  --no-lines                 Don't display AST node line numbers
  --no-source                Don't display the coNCePTuaL source program

Help options:
  --help                     Show this help message"""

    def generate(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        "Compile an AST into a list of lines of DOT code."
        self.filesource = filesource       # Input file
        self.sourcecode = sourcecode       # coNCePTuaL source code
        self.backend_name = "dot_ast"
        self.backend_desc = "parse tree in AT&T's DOT language"
        self.errmsg = NCPTL_Error(filesource)

        # Write a DOT prologue.
        self.dotcode = []
        if self.filesource == "<command line>":
            inputfile = "the source program"
            cleanfilename = "stdin_graph"
        else:
            inputfile = os.path.abspath(self.filesource)
            cleanfilename = (re.sub(r'\W', '_',
                                    os.path.splitext(os.path.split(inputfile)[1])[0]) +
                             "_graph")
        self.dotcode.extend([
            "// " + "*" * 70,
            "// This file was generated by coNCePTuaL on %s" %
            time.asctime(time.localtime(time.time())),
            "// using the %s backend (%s)." %
            (self.backend_name, self.backend_desc),
            "// Do not modify this file; modify %s instead." % inputfile,
            "// " + "*" * 70])
        if self.sourcecode:
            self.dotcode.extend([
                "//",
                "// Entire source program",
                "// ---------------------"])
            for oneline in string.split(string.strip(self.sourcecode), "\n"):
                self.dotcode.append("//   %s" % oneline)
        self.dotcode.extend([
            "",
            "",
            "digraph %s {" % cleanfilename,
            "  /* Graph defaults */",
            '  page = "8.5, 11";',
            '  size = "7.5, 10";',
            "  node [shape=record];",
            ""])
        if self.extra_dot_code:
            self.dotcode.append("  /* Extra code specified on the command line */")
            self.dotcode.extend(map(lambda str: "  %s;" % re.sub(r'[\s;]+$', "", str),
                                    self.extra_dot_code))
            self.dotcode.append("")

        # Walk the AST in postorder fashion to produce a graphical parse tree.
        self.dotcode.append("  /* The program-specific parse tree */")
        self.dotcode.append("  subgraph cluster_parse_tree {")
        self.dotcode.append('    style = "invis";')
        self.nextnodenum = 1
        if self.compress_graph:
            self.elide_chains(ast)
        self.postorder_traversal(ast)
        self.dotcode.append("  }")
        self.dotcode.append("")

        # Optionally output the source program.
        if self.show_source_code:
            self.dotcode.append("  /* Program source code */")
            self.dotcode.append("  subgraph cluster_source_code {")
            self.dotcode.append('    style = "invis";')
            lineno = 1
            codelines = []
            for oneline in string.split(string.rstrip(self.sourcecode), "\n"):
                codelines.append("%6d)  %s" %
                                 (lineno, self.string_to_dot(oneline)))
                lineno = lineno + 1
            self.dotcode.append('    source_code [shape=plaintext, fontname="Courier",')
            self.dotcode.append('                 label="%s\\l"];' % string.join(codelines, "\\l"))
            self.dotcode.append("  }")

        # Write a DOT footer.
        self.dotcode.append("}")
        return self.dotcode

    def compile_only(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Output DOT code."
        newin, _ = self.write_dot_code(progfilename, codelines, outfilename, 1)
        if outfilename != "-":
            # If an output filename was specified explicitly, use that
            # as the target filename.
            os.rename(newin, outfilename)
            newin = outfilename
        if verbose:
            sys.stderr.write("# Files generated: %s\n" % newin)

    def compile_and_link(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Pipe the DOT code through dot."

        # Determine the names of the files to use.
        infilename, outfilename = self.write_dot_code(progfilename, codelines, outfilename, keepints)

        # Determine how to invoke dot.
        if os.environ.has_key("DOT"):
            dotprog = os.environ["DOT"]
        elif ncptl_config.has_key("DOT"):
            dotprog = ncptl_config["DOT"]
        else:
            dotprog = "dot"
        compile_string = ("%s -T%s -o %s %s" %
                          (dotprog, self.dot_format, outfilename, infilename))

        # "Link" (i.e., generate graphics from) the .dot file, then delete it.
        if verbose:
            sys.stderr.write("%s\n" % compile_string)
        dotexitcode = os.system(compile_string)
        if keepints:
            if verbose:
                sys.stderr.write("# Not deleting %s\n" % infilename)
        else:
            if verbose:
                sys.stderr.write("# Deleting %s\n" % infilename)
            try:
                os.unlink(infilename)
            except OSError, errmsg:
                sys.stderr.write("# --> %s\n" % errmsg)
        if dotexitcode != 0:
            return
        if verbose:
            sys.stderr.write("# Files generated: %s\n" % outfilename)


    #------------------#
    # Helper functions #
    #------------------#

    def string_to_dot(self, somestring):
        "Escape characters that are special to dot."
        return re.sub(r'(["<>])', r'\\\1',
                      string.replace(somestring, '\\', '\\\\'))

    def write_dot_code(self, progfilename, codelines, outfilename, keepints):
        "Output DOT code to a file and return the modified input and output filenames."

        # Determine the names of the files to use.
        if progfilename == "<command line>":
            progfilename = "a.out.ncptl"
        if outfilename == "-":
            outfilename, _ = os.path.splitext(progfilename)
            outfilename = outfilename + "." + self.dot_format
        if keepints:
            # If we plan to keep the .dot file, derive it's name from outfilename.
            infilename, _ = os.path.splitext(outfilename)
            infilename = infilename + ".dot"
        else:
            # If we plan to discard the .dot file then give it a unique name.
            tempfile.tempdir, _ = os.path.split(outfilename)
            tempfile.template = "dot_" + str(os.getpid())
            while 1:
                fbase = tempfile.mktemp()
                if not os.path.isfile(fbase + ".dot"):
                    break
            infilename = fbase + ".dot"

        # Copy CODELINES to a .dot file.
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


    #-----------------#
    # Output DOT code #
    #-----------------#

    def elide_chains(self, node):
        "Elide chains of single-child nodes from the graph."
        if len(node.kids) == 1 and len(node.kids[0].kids) == 1 and len(node.kids[0].kids[0].kids) == 1:
            elided_node = node.kids[0]
            num_elided = 0
            while len(node.kids) == 1 and len(node.kids[0].kids) == 1:
                node.kids = node.kids[0].kids
                num_elided = num_elided + 1
            elided_node.type = "(%d nodes)" % num_elided
            elided_node.attr = None
            elided_node.kids = node.kids
            node.kids = [elided_node]
        for kid in node.kids:
            self.elide_chains(kid)

    def postorder_traversal(self, node):
        "Write a node to the graph and connect it to its children."

        # Process our children first.
        for kid in node.kids:
            self.postorder_traversal(kid)

        # Keep track of the current graphical node number.
        node.nodenum = self.nextnodenum
        self.nextnodenum = self.nextnodenum + 1

        # Construct a row showing the node type and (optionally) attributes.
        labelrows = []
        if node.attr != None and self.show_attrs:
            attribs = re.sub(r'(["<>])', r'\\\1', repr(node.attr))
            labelrows.append("%s|%s" % (node.type, attribs))
        else:
            labelrows.append(node.type)

        # Optionally construct a row showing the AST node's source code.
        if self.node_code_chars > 0:
            codestring = self.string_to_dot(node.printable)
            if len(codestring) <= self.node_code_chars:
                labelrows.append(codestring)
            else:
                labelrows.append(codestring[:self.node_code_chars] + "  ...")

        # Optionally construct a row showing the AST node's line number(s).
        if self.show_lines:
            if node.lineno0 == node.lineno1:
                labelrows.append("line %d" % node.lineno0)
            else:
                labelrows.append("lines %d - %d" % (node.lineno0, node.lineno1))

        # Merge the label rows into a single label string and generate
        # a graph node.
        if node.type[-6:] == "nodes)":
            self.dotcode.append('    n%d [label="%s",color=invis];' % (node.nodenum, node.type))
        else:
            labelstr = string.join(map(lambda r: "{%s}" % r, labelrows), " | ")
            self.dotcode.append('    n%d [label="{%s}"];' % (node.nodenum, labelstr))

        # Connect the node to its children (if any).
        for child in node.kids:
            self.dotcode.append('    n%d -> n%d;' % (node.nodenum, child.nodenum))
