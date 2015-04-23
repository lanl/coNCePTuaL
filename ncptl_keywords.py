########################################################################
#
# Keyword list for the coNCePTuaL language
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
import getopt

class Keywords:
    "List the keywords that are special to the coNCePTuaL language."
    keywords = [
        "a",
        "abs",
        "absolute",
        "aggregates",
        "aligned",
        "all",
        "an",
        "and",
        "are",
        "arithmetic",
        "as",
        "assert",
        "assigned",
        "asynchronously",
        "await",
        "awaits",
        "backend",
        "be",
        "bit",
        "bits",
        "buffer",
        "buffers",
        "but",
        "byte",
        "bytes",
        "cbrt",
        "ceiling",
        "comes",
        "completion",
        "completions",
        "compute",
        "computes",
        "counters",
        "current",
        "data",
        "day",
        "days",
        "declares",
        "default",
        "deviation",
        "divides",
        "doubleword",
        "doublewords",
        "each",
        "even",
        "execute",
        "executes",
        "factor10",
        "file_data",
        "final",
        "floor",
        "for",
        "from",
        "geometric",
        "gigabyte",
        "greater",
        "group",
        "halfword",
        "halfwords",
        "harmonic",
        "histogram",
        "hour",
        "hours",
        "if",
        "in",
        "integer",
        "integers",
        "into",
        "is",
        "it",
        "its",
        "kilobyte",
        "knomial_child",
        "knomial_children",
        "knomial_parent",
        "language",
        "less",
        "let",
        "log",
        "log10",
        "logs",
        "max",
        "maximum",
        "mean",
        "median",
        "megabyte",
        "memory",
        "mesh_coordinate",
        "mesh_distance",
        "mesh_neighbor",
        "message",
        "messages",
        "microsecond",
        "microseconds",
        "millisecond",
        "milliseconds",
        "min",
        "minimum",
        "minute",
        "minutes",
        "misaligned",
        "mod",
        "multicast",
        "multicasts",
        "my",
        "nonunique",
        "not",
        "odd",
        "of",
        "or",
        "other",
        "otherwise",
        "output",
        "outputs",
        "page",
        "pages",
        "percentile",
        "plus",
        "processor",
        "processor_of",
        "processors",
        "quadword",
        "quadwords",
        "random",
        "random_gaussian",
        "random_pareto",
        "random_poisson",
        "random_uniform",
        "real",
        "receive",
        "receives",
        "reduce",
        "reduces",
        "region",
        "repetition",
        "repetitions",
        "require",
        "reset",
        "resets",
        "restore",
        "restores",
        "result",
        "results",
        "root",
        "round",
        "second",
        "seconds",
        "send",
        "sends",
        "sized",
        "sleep",
        "sleeps",
        "sqrt",
        "standard",
        "static_file_data",
        "store",
        "stores",
        "stride",
        "such",
        "sum",
        "synchronization",
        "synchronize",
        "synchronizes",
        "synchronously",
        "tag",
        "task",
        "task_of",
        "tasks",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "time",
        "times",
        "to",
        "touch",
        "touches",
        "touching",
        "tree_child",
        "tree_parent",
        "unaligned",
        "unique",
        "unsuspecting",
        "using",
        "value",
        "variance",
        "verification",
        "version",
        "warmup",
        "where",
        "while",
        "who",
        "with",
        "without",
        "word",
        "words",
        "xor"
    ]


# Enable an external script to dump a formatted version of the keyword list.
if __name__ == '__main__':
    # Parse the command line.
    try:
        longopts = [
            "first=",
            "last=",
            "apply="]
        opts, args = getopt.getopt(sys.argv[1:], "f:l:a:", longopts)
    except getopt.error:
        sys.stderr.write ("%s: bad option\n" % sys.argv[0])
        sys.exit(2)
    firstfmt = None
    lastfmt = None
    identity = lambda thing: thing
    applyfunc = "identity"
    if len(args) == 0:
        middlefmt = '%s\\n'
    else:
        middlefmt = args[0]
    for oneopt, onearg in opts:
        if oneopt in ("-f", "--first"):
            firstfmt = onearg
        if oneopt in ("-l", "--last"):
            lastfmt = onearg
        if oneopt in ("-a", "--apply"):
            applyfunc = onearg
    if not lastfmt:
        lastfmt = middlefmt
    if not firstfmt:
        firstfmt = middlefmt

    # Output a formatted keyword list.
    print eval('"%s"' % firstfmt) % eval('%s("%s")' % (applyfunc, Keywords.keywords[0])),
    for kw in Keywords.keywords[1:-1]:
        print eval('"%s"' % middlefmt) % eval('%s("%s")' % (applyfunc, kw)),
    print eval('"%s"' % lastfmt) % eval('%s("%s")' % (applyfunc, Keywords.keywords[-1])),
