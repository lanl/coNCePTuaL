########################################################################
#
# Code generation module for the coNCePTuaL language:
# CAIDA's LibSea graph file format
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

import sys
import re
import string
import time
import os
import math
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
        "Initialize the LibSea code generation module."
        self.errmsg = NCPTL_Error()     # Placeholder until generate is called

        # Process any arguments we were given.
        self.source_truncate = 100      # Truncate node source code after this many characters
        for arg in range(0, len(options)):
            arg_match = re.match(r'--(node-code)=(.*)', options[arg])
            if arg_match:
                argname, argvalue = arg_match.group(1), arg_match.group(2)
                if argname == "node-code":
                    argvalue = int(argvalue)
                    if argvalue == -1:
                        self.source_truncate = sys.maxint
                    else:
                        self.source_truncate = argvalue
        for arg in range(0, len(options)):
            if options[arg] == "--help":
                self.show_help()
                sys.exit(0)

    def show_help(self):
        "Output a help message."
        print """\
Usage: libsea_ast [OPTION...]
  --node-code=<number>       Truncate node source code after this many
                             characters [default: 100]

Help options:
  --help                     Show this help message"""

    def generate(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        "Compile an AST into a list of lines of LibSea code."
        self.filesource = filesource       # Input file
        self.sourcecode = sourcecode       # coNCePTuaL source code
        self.backend_name = "libsea_graph"
        self.backend_desc = "parse tree in CAIDA's LibSea graph format"
        self.errmsg = NCPTL_Error(filesource)
        self.next_global_ID = 0            # Next LibSea ID to assign to a node

        # Write a LibSea prologue.
        self.libseacode = []
        if self.filesource == "<command line>":
            inputfile = "the source program"
            cleanfilename = "stdin_graph"
        else:
            inputfile = os.path.abspath(self.filesource)
            cleanfilename = (re.sub(r'\W', '_',
                                    os.path.splitext(os.path.split(inputfile)[1])[0]) +
                             "_graph")
        self.libseacode.extend([
                "#" * 78,
                "# This file was generated by coNCePTuaL on %s" %
                time.asctime(time.localtime(time.time())),
                "# using the %s backend (%s)." %
                (self.backend_name, self.backend_desc),
                "# Do not modify this file; modify %s instead." % inputfile,
                "#" * 78])
        if self.sourcecode:
            self.libseacode.extend([
                "#",
                "# Entire source program",
                "# ---------------------"])
            for oneline in string.split(string.strip(self.sourcecode), "\n"):
                self.libseacode.append("#   %s" % oneline)
            self.libseacode.extend([
                    "#",
                    "#" * 78,
                    ""])

        # Acquire information about the graph structure.
        self.assign_node_IDs(ast)
        nodes = sorted(self.accumulate_nodes(ast))
        nodefmtwidth = int(math.ceil(math.log10(len(nodes))))
        links = sorted(self.accumulate_edges(ast))
        linkfmtwidth = int(math.ceil(math.log10(len(links))))

        # Produce LibSea code for the graph metadata.
        self.libseacode.extend([
                "Graph",
                "{",
                "  ### metadata ###",
                '  @name="%s";' % os.path.splitext(os.path.basename(filesource))[0],
                '  @description="Parse tree for %s";' % inputfile,
                "  @numNodes=%d;" % len(nodes),
                "  @numLinks=%d;" % len(links),
                "  @numPaths=0;",
                "  @numPathLinks=0;",
                ""])

        # Produce LibSea code for the graph structural data.
        self.libseacode.extend([
                "  ### structural data ###",
                "  @links=["])
        for src, dest in links[:-1]:
            self.libseacode.append("    { %*d; %*d; }," % \
                                       (linkfmtwidth, src, linkfmtwidth, dest))
        self.libseacode.append("    { %*d; %*d; }" % \
                                   (linkfmtwidth, links[-1][0],
                                    linkfmtwidth, links[-1][1]))
        self.libseacode.extend([
                "  ];",
                "  @paths=;",
                ""])

        # Produce LibSea code for the graph attribute data.
        self.libseacode.extend([
                "  ### attribute data ###",
                "  @enumerations=;",
                "  @attributeDefinitions=["])
        self.libseacode.extend(self.format_attribute("Type", 1, nodes))
        self.libseacode.extend(self.format_attribute("Attribute", 2, nodes))
        self.libseacode.extend(self.format_attribute("Source_code", 3, nodes))
        self.libseacode.extend(self.format_selection_attr("Is_simple_stmt",
                                                          [n[0] for n in nodes if n[1] == "simple_stmt"]))
        self.libseacode.extend(self.format_selection_attr("Is_constant",
                                                          [n[0] for n in nodes if n[4]]))
        self.libseacode.extend(self.format_selection_attr("Is_definition",
                                                          [n[0] for n in nodes if n[5]]))
        self.libseacode.extend(self.format_selection_attr("Is_leaf",
                                               self.accumulate_leaves(ast)))
        self.libseacode.extend([
                "    {",
                "      @name=$Is_root_node;",
                "      @type=bool;",
                "      @default=|| false ||;",
                "      @nodeValues=[ { 0; T; } ];   # Root node",
                "      @linkValues=["])
        for linknum in range(len(links)-1):
            self.libseacode.append("        { %*d; T; }," % (linkfmtwidth, linknum))
        self.libseacode.extend([
                "        { %*d; T; }" % (linkfmtwidth, len(links)-1),
                "      ];",
                "      @pathValues=;",
                "    }",
                "  ];",
                "  @qualifiers=[",
                "    {",
                "      @type=$spanning_tree;",
                "      @name=$Parse_tree;",
                '      @description="Abstract syntax tree corresponding to %s";' % inputfile,
                "      @attributes=[",
                "        { @attribute=7; @alias=$root; },",
                "        { @attribute=7; @alias=$tree_link; }",
                "      ];",
                "    }",
                "  ];",
                ""])

        # Produce LibSea code for the remaining (unused) graph features.
        self.libseacode.extend([
                "  ### visualization hints ###",
                "  ; ; ; ;",
                "",
                "  ### interface hints ###",
                "  ; ; ; ; ;",
                "}"])

        # Return the complete LibSea graph.
        return self.libseacode

    def compile_only(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Output LibSea code."
        if progfilename == "<command line>":
            progfilename = "a.out.ncptl"
        if outfilename == "-":
            outfilename, _ = os.path.splitext(progfilename)
            outfilename = outfilename + ".graph"
        try:
            outfile = open(outfilename, "w")
            for oneline in codelines:
                outfile.write("%s\n" % oneline)
            outfile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("Unable to produce %s (%s)" % (outfilename, strerror),
                                    filename=self.backend_name)
        if verbose:
            sys.stderr.write("# Files generated: %s\n" % outfilename)

    def compile_and_link(self, progfilename, codelines, outfilename, verbose=0, keepints=0):
        "Output LibSea code."
        self.compile_only(progfilename, codelines, outfilename, verbose, keepints)


    #------------------#
    # Helper functions #
    #------------------#

    def escape_string(self, somestring):
        "Escape characters that are special to LibSea."
        replacements = [
            ("\\", "\\\\"),
            ("\"", "\\\""),
            ("\n", "\\n"),
            ("\r", "\\r"),
            ("\t", "\\t"),
            ("\f", "\\f"),
            ("\b", "\\b")]
        for old, new in replacements:
            somestring = string.replace(somestring, old, new)
        return somestring

    def format_attribute(self, name, idx, nodelist):
        "Return LibSea attribute code for a single attribute."
        nodefmtwidth = int(math.ceil(math.log10(len(nodelist))))
        libseacode = []
        libseacode.extend([
                "    {",
                "      @name=$%s;" % name,
                "      @type=string;",
                "      @default=;",
                "      @nodeValues=["])
        for node in nodelist[:-1]:
            libseacode.append('        { %*d; "%s"; },' % \
                                       (nodefmtwidth, node[0],
                                        self.escape_string(node[idx])))
        libseacode.extend([
                '        { %*d; "%s"; }' % \
                    (nodefmtwidth, nodelist[-1][0],
                     self.escape_string(nodelist[-1][idx])),
                "      ];",
                "      @linkValues=;",
                "      @pathValues=;",
                "    },"])
        return libseacode

    def format_selection_attr(self, name, idlist):
        "Return LibSea attribute code marking only those elements in a given list as true."
        nodefmtwidth = int(math.ceil(math.log10(len(idlist))))
        libseacode = []
        libseacode.extend([
                "    {",
                "      @name=$%s;" % name,
                "      @type=bool;",
                "      @default=|| false ||;",
                "      @nodeValues=["])
        for node_id in idlist[:-1]:
            libseacode.append("        { %*d; T; }," % (nodefmtwidth, node_id))
        libseacode.extend([
                "        { %*d; T; }" % (nodefmtwidth, idlist[-1]),
                "      ];",
                "      @linkValues=;",
                "      @patValues=;",
                "    },"])
        return libseacode

    def assign_node_IDs(self, node):
        "Assign a unique ID to each node."

        # Assign ourself a unique ID.
        node.node_ID = self.next_global_ID
        self.next_global_ID += 1

        # Assign a unique ID to each of our children.
        for kid in node.kids:
            self.assign_node_IDs(kid)

    def accumulate_nodes(self, node):
        "Return a list of node descriptions."

        if node.attr == None:
            attrstr = "-"
        else:
            attrstr = str(node.attr)
        if len(node.printable) <= self.source_truncate:
            sourcestr = node.printable
        else:
            sourcestr = node.printable[:self.source_truncate] + " ..."
        nodeinfo = [(node.node_ID, node.type, attrstr, sourcestr,
                     node.sem["is_constant"], node.sem.has_key("definition"))]
        for kid in node.kids:
            nodeinfo.extend(self.accumulate_nodes(kid))
        return nodeinfo

    def accumulate_edges(self, node):
        "Return a list of links between node IDs."
        links = []
        for kid in node.kids:
            links.append((node.node_ID, kid.node_ID))
        for kid in node.kids:
            links.extend(self.accumulate_edges(kid))
        return links

    def accumulate_leaves(self, node):
        "Return a list of node IDs for leaf nodes."
        leaves = []
        if node.kids == []:
            leaves = [node.node_ID]
        else:
            for kid in node.kids:
                leaves.extend(self.accumulate_leaves(kid))
        return leaves
