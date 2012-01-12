#! /usr/bin/env python

########################################################################
#
# Jython side of the coNCePTuaL GUI
#
# By Nick Moss <nickm@lanl.gov>
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

from ncptl_variables import Variables
from ncptl_lexer import NCPTL_Lexer
from ncptl_parser import NCPTL_Parser
from codegen_interpret import NCPTL_CodeGen
import java

class GUIPyInterface( java.lang.Object ):
    def __init__(self, numtasks):
        "@sig public GUI_Interface( int numtasks )"
        self.lexer = NCPTL_Lexer()
        self.parser = NCPTL_Parser( self.lexer )
        self.codegen = NCPTL_CodeGen(options=[], numtasks=numtasks)
        self.codegen.procmap = None

    def get_language_version( self ):
        "@sig public java.lang.String get_language_version()"
        return self.parser.language_version

    def parse( self, sourcecode, filesource, start ):
        "@sig public java.lang.Object parse( java.lang.String sourcecode, java.lang.String filesource, java.lang.String start )"
        try:
            return self.parser.parsetokens(
               self.lexer.tokenize( sourcecode, filesource ), filesource, start )
        except:
            # Convert SystemExit (and other) exceptions into something
            # that Jython will pass through to Java.
            raise Exception

    def get_comments( self ):
        "@sig public java.lang.Object get_comments()"
        return self.lexer.line2comment

    def process_node( self, node ):
        "@sig public java.lang.Object process_node( java.lang.Object node )"
        self.codegen.clear_events()
        self.codegen.fake_semantic_analysis( node )
        return self.codegen.process_node( node )

    def get_eventlists( self ):
        "@sig public java.lang.Object get_eventlists()"
        return self.codegen.eventlist

    def set_numtasks( self, numtasks ):
        "@sig public void set_numtasks( int numtasks )"
        self.codegen.numtasks = numtasks

    def is_source_task_expr( self, node ):
        "@sig public boolean is_source_task_expr( java.lang.Object node )"
        try:
            self.parser._make_source_task( [node], 0 )
            return 1
        except:
            return 0

    def is_target_task_expr( self, node ):
        "@sig public boolean is_target_task_expr( java.lang.Object node )"
        try:
            self.parser._make_target_tasks( [node], 0 )
            return 1
        except:
            return 0

    def get_predeclared_variables( self ):
        "@sig public java.lang.String[] get_predeclared_variables()"
        return Variables.variables.keys()
