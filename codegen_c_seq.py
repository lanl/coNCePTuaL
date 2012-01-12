#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# Minimal C-based backend -- all communication
# operations result in a compiler error
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


import codegen_c_generic

class NCPTL_CodeGen(codegen_c_generic.NCPTL_CodeGen):
    def __init__(self, options):
        "Initialize the sequential C code generation module."
        self.backend_name = "c_seq"
        self.backend_desc = "C, sequential code only"
        codegen_c_generic.NCPTL_CodeGen.__init__(self, options)

        # We don't have our own command-line options but we handle
        # --help, nevertheless.
        for arg in range(0, len(options)):
            if options[arg] == "--help":
                # Output a help message.
                self.show_help()
                raise SystemExit, 0

    def code_def_init_uuid_BCAST(self, locals):
        '"Broadcast" logfile_uuid to all tasks.'
        pass
