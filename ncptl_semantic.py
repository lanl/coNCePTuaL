#! /usr/bin/env python

########################################################################
#
# Semantic-analysis module for the coNCePTuaL language
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
import re
import string
import copy
from ncptl_ast import AST
from ncptl_error import NCPTL_Error
from ncptl_variables import Variables
from ncptl_lexer import NCPTL_Lexer
from ncptl_parser import NCPTL_Parser

class NCPTL_Semantic:
    "Analyze the semantics of a coNCePTuaL program."

    def analyze(self, ast, filesource='<stdin>', lenient=0):
        "Search an AST for forbidden constructs."
        self.errmsg = NCPTL_Error(filesource)
        self.undeclared_vars = {}
        self.lenient = lenient
        self.infilename = filesource

        # Prepare to lex and parse fabricated param_decl nodes if
        # we're running in lenient mode.
        if self.lenient:
            self.lexer = NCPTL_Lexer()
            self.parser = NCPTL_Parser(self.lexer)

        # Initialize the AST.
        _Initialize_AST(ast, self)

        # Provide proper line numbers for all nodes.
        _Propagate_Line_Numbers_Up(ast)
        _Propagate_Line_Numbers_Down(ast)

        # Delete all empty subtrees.
        _Propagate_Emptiness_Up(ast)
        _Elide_Empty_Subtrees(ast)

        # Ensure that all variables are being used properly.
        _Identify_Definitions(ast)
        _Propagate_Scopes_Down_And_Across(ast)
        _Check_Use_Without_Def(ast)
        _Mark_Defs_Used(ast)
        _Check_Def_Without_Use(ast)
        _Check_Let_Bound_Variables(ast)

        # Ensure that command-line options are properly specified.
        _Check_Command_Line_Options(ast)

        # Ensure that message attributes are being used properly.
        _Check_Message_Attributes(ast)

        # Ensure that random variables aren't used where they don't belong.
        _Check_Random_Variables(ast)

        # Ensure that the reduce statement isn't being used incorrectly.
        _Check_Reduce_Usage(ast)

        # Return the modified AST.
        return ast


class _AST_Traversal:
    "Traverse an AST, invoking preorder and postorder methods as we go."

    def __init__(self, ast):
        "Begin the AST traversal."
        self.traverse(ast)

    def traverse(self, node):
        """
        Invoke an AST node's preorder method and the generic preorder
        method, then traverse the AST's children, and finally invoke
        the AST node's postorder method and the generic postorder
        method.
        """
        do_nothing = lambda node: None
        getattr(self, "pre_" + node.type, do_nothing)(node)
        getattr(self, "pre_any", do_nothing)(node)
        for kid in node.kids:
            self.traverse(kid)
        getattr(self, "post_" + node.type, do_nothing)(node)
        getattr(self, "post_any", do_nothing)(node)

###########################################################################

class _Initialize_AST(_AST_Traversal):
    "Prepare each AST node for semantic analysis."

    def __init__(self, ast, semobj):
        "Store a reference to the semantic-analysis object."
        self.semobj = semobj
        _AST_Traversal.__init__(self, ast)

    def pre_any(self, node):
        '''Assign a node an empty namespace (dictionary) called "sem"
        which initially contains a reference to the semantic-analysis
        object.'''
        node.sem = {"semobj": self.semobj}

###########################################################################

class _Propagate_Line_Numbers_Up(_AST_Traversal):
    "Copy line numbers from children to parents."

    def post_any(self, node):
        "Set our line numbers to encompass our children's ranges."
        if node.kids == []:
            return
        if node.lineno0 == 0:
            node.lineno0 = node.kids[0].lineno0
        if node.lineno1 == 0:
            node.lineno1 = node.kids[-1].lineno1


class _Propagate_Line_Numbers_Down(_AST_Traversal):
    "Copy line numbers from parents to children."

    def pre_any(self, node):
        "Ensure that all children have valid line numbers."

        # Determine if we have any work to do.
        missing_linenos = 0
        for kid in node.kids:
            if kid.lineno0 == 0 or kid.lineno1 == 0:
                missing_linenos = 1
                break
        if not missing_linenos:
            return

        # Propagate lineno1 to the right neighbor's lineno0.
        for kidnum in range(1, len(node.kids)):
            kid = node.kids[kidnum]
            if kid.lineno0 == 0:
                kid.lineno0 = node.kids[kidnum-1].lineno1
                if kid.lineno1 == 0:
                    kid.lineno1 = kid.lineno0

        # Propagate lineno0 to the left neighbor's lineno1.
        for kidnum in range(len(node.kids)-2, -1, -1):
            kid = node.kids[kidnum]
            if kid.lineno1 == 0:
                kid.lineno1 = node.kids[kidnum+1].lineno0
                if kid.lineno0 == 0:
                    kid.lineno0 = kid.lineno1

        # If all of our children are empty then give them our lineno0.
        for kid in node.kids:
            if kid.lineno0 == 0:
                kid.lineno0 = node.lineno0
            if kid.lineno1 == 0:
                kid.lineno1 = node.lineno1

    def post_any(self, node):
        "Verify that all nodes have valid line numbers."
        lineno0, lineno1 = node.lineno0, node.lineno1
        if lineno0 == 0 or lineno1 == 0 or lineno0 > lineno1:
            errmsg = node.sem["semobj"].errmsg
            errmsg.error_internal('A node of type "%s" spans invalid line numbers %d to %d' %
                                  (node.type, lineno0, lineno1))

###########################################################################

class _Propagate_Emptiness_Up(_AST_Traversal):
    "Mark parents of empty children as empty."

    def post_empty_stmt(self, node):
        "Mark empty statements as empty."
        node.sem["is_empty"] = 1

    def post_for_time(self, node):
        "Mark FOR <time> statements as nonempty."
        node.sem["is_empty"] = 0

    def post_for_count(self, node):
        "Mark FOR <count> statements as nonempty if they require synchronization."
        if "synchronized" in node.attr:
            node.sem["is_empty"] = 0

    def post_any(self, node):
        "If we're already marked, mark ourself as empty if all of our child statements are empty."
        if not node.sem.has_key("is_empty"):
            stmt_kids = 0
            empty_stmt_kids = 0
            for kid in node.kids:
                if string.find(kid.type, "stmt") != -1 or string.find(kid.type, "for_") != -1:
                    stmt_kids = stmt_kids + 1
                    if kid.sem["is_empty"]:
                        empty_stmt_kids = empty_stmt_kids + 1
            node.sem["is_empty"] = int(0 < empty_stmt_kids == stmt_kids)

class _Elide_Empty_Subtrees(_AST_Traversal):
    "Remove the children of empty nodes from the AST."

    def pre_simple_stmt_list(self, node):
        "Prune empty statements from lists of THEN-separate statements."
        newkids = filter(lambda k: not k.sem["is_empty"], node.kids)
        node.attr = node.attr - (len(node.kids)-len(newkids))
        node.kids = newkids

    def pre_if_stmt(self, node):
        "Remove empty OTHERWISE clauses from the child list."
        try:
            if node.kids[2].sem["is_empty"]:
                del node.kids[2]
        except IndexError:
            pass

    def pre_any(self, node):
        "Remove all empty children from the child list."
        if node.sem["is_empty"]:
            node.kids = []

###########################################################################

class _Identify_Definitions(_AST_Traversal):
    "Tell each ident node if it's a variable definition."

    # Define a set of node types whose first child defines a variable.
    defines_first = {"restricted_ident": 1,
                     "let_binding":      1,
                     "for_each":         1,
                     "param_decl":       1}

    def pre_task_expr(self, node):
        "Tell the variable in ALL TASKS <var> that it's a definition."
        if node.attr == "task_all" and node.kids != []:
            ident_node = node.kids[0]
            ident_node.sem["definition"] = {ident_node.attr: ident_node}

    def pre_any(self, node):
        """For certain node types, tell our first child that it's a
        variable definition."""
        if self.defines_first.has_key(node.type):
            ident_node = node.kids[0]
            ident_node.sem["definition"] = {ident_node.attr: ident_node}

    def post_ident(self, node):
        "Abort if the program tries to redefine a predefined variable."
        if node.sem.has_key("definition") and Variables.variables.has_key(node.attr):
            errmsg = node.sem["semobj"].errmsg
            errmsg.error_fatal("Redefinition of %s is not allowed" % node.printable,
                               node.lineno0, node.lineno1)


class _Propagate_Scopes_Down_And_Across(_AST_Traversal):
    "Give each node a variable scope."

    # Define a set of node types whose first child defines a variable.
    defines_first = {"restricted_ident": 1,
                     "let_binding":      1,
                     "for_each":         1,
                     "param_decl":       1}

    def pre_program(self, node):
        "Create an initial scope."
        node.sem["varscope"] = {}

    def pre_simple_stmt(self, node):
        """Give our child a copy of our scope and instruct it to
        propagate from source_task to target_task."""
        # Copy our scope to our child.
        varscope = node.sem["varscope"]
        kid = node.kids[0]
        kid.sem["varscope"] = copy.copy(varscope)

        # reduce_stmt nodes have slightly different semantics from
        # other simple_stmt nodes.
        if kid.type == "reduce_stmt":
            return

        # Find our (at most one) source_task grandchild and our (at
        # most one) target_task grandchild.
        source_task = None
        target_task = None
        for grandkid in kid.kids:
            if grandkid.type == "source_task":
                source_task = grandkid
            if grandkid.type == "target_tasks":
                target_task = grandkid
        if source_task == None:
            # for_count, for_time, etc.
            return

        # Propagate the source task's scope appropriately.
        if target_task == None:
            # Non-communication statement -- all grandchildren will
            # receive a reference to the source task's scope.
            return
        else:
            # Communication statement -- prepare to give the target
            # task a copy of the source task's scope.
            source_task.sem["varscope"] = copy.copy(varscope)
            target_task.sem["source_task"] = source_task

    def pre_receive_stmt(self, node):
        """Reverse the order of our children to force the source task
        to be evaluated before the target tasks."""
        node.kids.reverse()

    def pre_let_binding_list(self, node):
        "Tell each let binding from which node to copy its scope."
        node.kids[0].sem["copy_scope_from"] = node
        for kidnum in range(1, len(node.kids)):
            node.kids[kidnum].sem["copy_scope_from"] = node.kids[kidnum-1].kids[0]

    def pre_let_binding(self, node):
        "Copy a previous scope to ours and give our first child a copy of that."
        oldscope = node.sem["copy_scope_from"].sem["varscope"]
        node.sem["varscope"] = copy.copy(oldscope)
        node.kids[0].sem["varscope"] = copy.copy(oldscope)

    def pre_target_tasks(self, node):
        "Copy the corresponding source task's scope."
        node.sem["varscope"] = copy.copy(node.sem["source_task"].sem["varscope"])

    def pre_task_expr(self, node):
        "Inject the variable in ALL TASKS <var> into the current scope."
        if node.attr == "task_all" and node.kids != []:
            ident_node = node.kids[0]
            node.sem["varscope"][ident_node.attr] = ident_node

    def pre_param_decl(self, node):
        "Provide all of our children except the first with an empty scope."
        for kid in node.kids[1:]:
            kid.sem["varscope"] = {}

    def pre_any(self, node):
        "Store a reference to our scope in all of our children who lack one."
        varscope = node.sem["varscope"]
        for kid in node.kids:
            if not kid.sem.has_key("varscope"):
                kid.sem["varscope"] = varscope
        if self.defines_first.has_key(node.type):
            # Define a variable in our first child's scope.
            ident_node = node.kids[0]
            ident_node.sem["varscope"][ident_node.attr] = ident_node

    def post_receive_stmt(self, node):
        """Reverse the order of our children back to their original state."""
        node.kids.reverse()

    def post_let_binding_list(self, node):
        "Update our scope with the values in the final let binding's scope."
        node.sem["varscope"].update(node.kids[-1].kids[0].sem["varscope"])


class _Check_Use_Without_Def(_AST_Traversal):
    "Abort if we encounter an undefined variable."

    def pre_ident(self, node):
        "Abort if we're not in our own scope."
        if node.sem["varscope"].has_key(node.attr):
            # We're in scope so everything's okay.
            return
        elif Variables.variables.has_key(node.attr):
            # We're a predefined variable so we can't be undefined.
            return
        else:
            # We're an undefined variable.
            semobj = node.sem["semobj"]
            if semobj.lenient:
                # The user requested that we automatically define all
                # undefined variables as command-line arguments.
                semobj.undeclared_vars[node.attr] = node
            else:
                semobj.errmsg.error_fatal("Variable %s must be declared before being used" % node.printable,
                                          node.lineno0, node.lineno1)


class _Mark_Defs_Used(_AST_Traversal):
    "Mark every used definition as such."

    def pre_ident(self, node):
        "Mark our corresponding definition as used."
        if not node.sem.has_key("definition"):
            try:
                # We're an ordinary variable.
                defining_node = node.sem["varscope"][node.attr]
                defining_node.sem["use"] = 1
            except KeyError:
                # We're a predefined variable.
                pass


class _Check_Def_Without_Use(_AST_Traversal):
    "Issue a warning message if a variable is defined but never used."

    def post_ident(self, node):
        "Complain if we're an unused definition."
        if node.sem.has_key("definition") and not node.sem.has_key("use"):
            errmsg = node.sem["semobj"].errmsg
            errmsg.warning("Variable %s is defined but never used" % node.printable,
                           node.lineno0, node.lineno1)


class _Check_Let_Bound_Variables(_AST_Traversal):
    "Ensure that let bindings properly utilize variable names."

    def pre_ident(self, node):
        "Keep track of the usage of all predefined variables."
        if Variables.variables.has_key(node.attr):
            node.sem["predefined_usage"] = {node.attr: [node]}

    def post_let_binding(self, node):
        "Ensure that our right-hand side uses no predefined variables."
        for varname, nodelist in node.kids[1].sem["predefined_usage"].items():
            if varname != "num_tasks":
                firstnode = nodelist[0]
                semobj = node.sem["semobj"]
                semobj.errmsg.error_fatal('"%s" is not allowed within a let binding' % firstnode.printable,
                                          firstnode.lineno0, firstnode.lineno1)

    def post_any(self, node):
        "Propagate upwards the list of predefined variables used below."
        predefined_usage = {}
        for kid in [node] + node.kids:
            try:
                kid_predefined_usage = kid.sem["predefined_usage"]
                for varname, nodelist in kid_predefined_usage.items():
                    try:
                        predefined_usage[varname].extend(nodelist)
                    except KeyError:
                        predefined_usage[varname] = copy.copy(nodelist)
            except KeyError:
                pass
        node.sem["predefined_usage"] = predefined_usage

###########################################################################

class _Check_Command_Line_Options(_AST_Traversal):
    "Ensure that command-line arguments are used properly."

    def __init__(self, ast):
        "Define a set of parameter maps for use by the other methods."
        ast.sem["semobj"].parameter_maps = {"ident":     {},
                                            "longname":  {},
                                            "shortname": {}}
        _AST_Traversal.__init__(self, ast)

    def pre_param_decl(self, node):
        "Perform various checks on parameter declarations."

        # Ensure that the long name and short name follow the Unix conventions.
        semobj = node.sem["semobj"]
        errmsg = semobj.errmsg
        shortnode = node.kids[3]
        shortname = shortnode.attr
        if not re.search (r'^-[a-z0-9]$', shortname):
            errmsg.error_fatal('"%s" is not a valid short command-line option (must be a "-" followed by a single lowercase letter or digit)' % shortname,
                               shortnode.lineno0, shortnode.lineno1)
        longnode = node.kids[2]
        longname = longnode.attr
        if not re.search (r'^--[-\w]+$', longname):
            errmsg.error_fatal('"%s" is not a valid long command-line option (must be a "--" followed by one or more letters/digits/dashes/underscores)' % longname,
                               longnode.lineno0, longnode.lineno1)

        # Ensure that no command-line variable names are duplicated.
        identnode = node.kids[0]
        identname = identnode.attr
        ident_map = semobj.parameter_maps["ident"]
        try:
            # Command-line variable was previously defined.
            previdentnode = ident_map[identname]
            errmsg.error_fatal("Variable %s is defined in multiple COMES FROM declarations (previous was on line %d)" %
                               (identnode.printable, previdentnode.lineno0),
                               identnode.lineno0, identnode.lineno1)
        except KeyError:
            # This is the variable's first occurrence.
            ident_map[identname] = identnode

        # Ensure that no long option names are duplicated.
        longname_map = semobj.parameter_maps["longname"]
        try:
            # Long name was previously defined.
            prevlongnode = longname_map[longname]
            errmsg.error_fatal("Long option %s is defined in multiple COMES FROM declarations (previous was on line %d)" %
                               (longnode.printable, prevlongnode.lineno0),
                               longnode.lineno0, longnode.lineno1)
        except KeyError:
            # This is the variable's first occurrence.
            longname_map[longname] = longnode

        # Ensure that no short option names are duplicated.
        shortname_map = semobj.parameter_maps["shortname"]
        try:
            # Short name was previously defined.
            prevshortnode = shortname_map[shortname]
            errmsg.error_fatal("Short option %s is defined in multiple COMES FROM declarations (previous was on line %d)" %
                               (shortnode.printable, prevshortnode.lineno0),
                               shortnode.lineno0, shortnode.lineno1)
        except KeyError:
            # This is the variable's first occurrence.
            shortname_map[shortname] = shortnode

        # Ensure that no predefined variables are used in the
        # default-value expression.
        try:
            exprnode = node.kids[4]
            predefs = copy.copy(exprnode.sem["predefined_usage"])
            if predefs != {}:
                errmsg.error_fatal("%s cannot appear within parameter %s's default value" % (predefs.keys()[0], identname),
                                   exprnode.lineno0, exprnode.lineno1)
        except KeyError:
            pass

    def post_program(self, node):
        """Fabricate header_decl subtrees for all automatically
        declared command-line options."""

        # If we're not running in lenient mode then we don't need to
        # fabricate any subtrees.
        semobj = node.sem["semobj"]
        if not semobj.lenient:
            return

        # Construct a list of header_decl nodes.
        newoptions = []
        longname_map = semobj.parameter_maps["longname"]
        shortname_map = semobj.parameter_maps["shortname"]
        for identnode in semobj.undeclared_vars.values():
            # Select a long name and ensure that it's unique.
            longname = "--" + identnode.attr
            base_longname = longname
            nextnum = 2
            while longname_map.has_key(longname):
                longname = "%s%d" % (base_longname, nextnum)
                nextnum = nextnum + 1
            longname_map[longname] = identnode

            # Select a short name and ensure that it's unique.
            shortname = "-" + identnode.attr[0]
            if shortname_map.has_key(shortname):
                for altshort in string.lower(longname[2:]) + string.lowercase + string.digits:
                    if altshort == "-":
                        continue
                    shortname = "-" + altshort
                    if not shortname_map.has_key(shortname):
                        break
            if shortname_map.has_key(shortname):
                # This should never occur except in pathological cases.
                semobj.errmsg.error_fatal('Unable to find a replacement option for duplicate option "-%s"' % identnode.attr[0])
            shortname_map[shortname] = identnode

            # Invoke the parser to fabricate a header_decl node.
            description = string.capitalize(identnode.printable[0]) + identnode.printable[1:]
            param_decl_string = '%s is "%s" and comes from "%s" or "%s" with default 0' % \
                                (identnode.attr, description, longname, shortname)
            param_decl_lexemes = semobj.lexer.tokenize(param_decl_string,
                                                       semobj.infilename)
            header_decl = semobj.parser.parsetokens(param_decl_lexemes,
                                                    filesource=semobj.infilename,
                                                    start="header_decl")
            self._assign_line_numbers(header_decl, identnode.lineno0)
            newoptions.append(header_decl)

        # Return if we have no new options to declare.
        if newoptions == []:
            return

        # Inject the header_decl into the AST.
        kid = node.kids[0]
        if kid.type == "header_decl_list":
            # Easy case -- we already have a header_decl_list.
            kid.attr = kid.attr + len(newoptions)
            kid.kids.extend(newoptions)
            for optnode in newoptions:
                _Initialize_AST(optnode, semobj)
        else:
            # Difficult case -- we have to create a header_decl_list.
            header_decl_list = semobj.parser._str2ast("header_decl_list",
                                                      attr=len(newoptions),
                                                      kids=newoptions,
                                                      lineno0=newoptions[0].lineno0,
                                                      lineno1=newoptions[-1].lineno1)
            node.kids.insert(0, header_decl_list)
            _Initialize_AST(header_decl_list, semobj)

    def _assign_line_numbers(self, node, lineno):
        "Assign line numbers to every node in an AST."
        node.lineno0 = lineno
        node.lineno1 = lineno
        for kid in node.kids:
            self._assign_line_numbers(kid, lineno)

###########################################################################

class _Check_Message_Attributes(_AST_Traversal):
    "Ensure that message attributes don't conflict with each other."

    def pre_send_stmt(self, node):
        """Ensure that WITH VERIFICATION is used either by both the
        sender and receiver or by neither the sender nor the
        receiver."""
        semobj = node.sem["semobj"]
        sendAST = node.kids[1].kids[4].kids[0]
        recvAST = node.kids[4].kids[4].kids[0]
        send_touching = sendAST.type
        recv_touching = recvAST.type
        if send_touching == "verification" and recv_touching != "verification":
            semobj.errmsg.error_fatal("A message sent WITH VERIFICATION must also be received WITH VERIFICATION",
                                      node.lineno0, node.lineno1)
        if send_touching != "verification" and recv_touching == "verification":
            semobj.errmsg.error_fatal("A message received WITH VERIFICATION must also be sent WITH VERIFICATION",
                                      node.lineno0, node.lineno1)

    def pre_message_spec(self, node):
        "Enforce the mutual incompatibility of UNIQUE and FROM/INTO BUFFER."
        is_unique = node.kids[1].attr
        buffer_type = node.kids[5].attr
        if is_unique and buffer_type in ["from", "into"]:
            semobj = node.sem["semobj"]
            semobj.errmsg.error_fatal("UNIQUE and %s BUFFER are mutually exclusive" % string.upper(buffer_type),
                                      node.lineno0, node.lineno1)

###########################################################################

class _Check_Random_Variables(_AST_Traversal):
    "Ensure that the RANDOM_* functions are not used inappropriately."

    def pre_func_call(self, node):
        "Remember which nodes refer to random variables."
        if node.attr[:7] == "RANDOM_":
            node.sem["random_func_nodes"] = [node]

    def post_task_expr(self, node):
        "Prohibit task expressions from using random variables."
        self.post_any(node)
        try:
            random_node = node.sem["random_func_nodes"][0]
            semobj = node.sem["semobj"]
            semobj.errmsg.error_fatal('"%s" is not allowed within a task description' % random_node.printable,
                                      random_node.lineno0, random_node.lineno1)
        except IndexError:
            pass

    def post_if_stmt(self, node):
        "Prohibit the expression in an IF statement from using a random variable."
        try:
            random_node = node.kids[0].sem["random_func_nodes"][0]
            semobj = node.sem["semobj"]
            semobj.errmsg.error_fatal('"%s" is not allowed within an IF condition' % random_node.printable,
                                      random_node.lineno0, random_node.lineno1)
        except IndexError:
            pass

    def post_let_binding(self, node):
        "Prohibit the right-hand side of a let binding from using a random variable."
        try:
            random_node = node.kids[1].sem["random_func_nodes"][0]
            semobj = node.sem["semobj"]
            semobj.errmsg.error_fatal('"%s" is not allowed within a let binding' % random_node.printable,
                                      random_node.lineno0, random_node.lineno1)
        except IndexError:
            pass

    def post_any(self, node):
        "Propagate upwards the list of random variables used below."
        random_func_nodes = []
        for kid in [node] + node.kids:
            try:
                random_func_nodes.extend(kid.sem["random_func_nodes"])
            except KeyError:
                pass
        node.sem["random_func_nodes"] = random_func_nodes
        if node.type in ["message_spec", "reduce_message_spec"]:
            self._check_message_spec(node)

    def _check_message_spec(self, node):
        """Prohibit random variables from being used in any type of
        message specifications."""
        try:
            random_node = node.sem["random_func_nodes"][0]
            semobj = node.sem["semobj"]
            semobj.errmsg.error_fatal('"%s" is not allowed within a message specification' % random_node.printable,
                                      random_node.lineno0, random_node.lineno1)
        except IndexError:
            pass

###########################################################################

class _Check_Reduce_Usage(_AST_Traversal):
    "Ensure that reduce statements are being used meaningfully."

    def _compare_item_counts(self, first, second):
        "Recursively compare two item_count ASTs."
        if (first.type == "an" and second.printable == "1") or \
           (first.printable == "1" and second.type == "an"):
            # Treat "A" and "AN" as "1".
            return 1
        elif first.type != second.type:
            # Different data types imply a mismatch.
            return 0
        elif len(first.kids) != len(second.kids):
            # Different numbers of children implies a mismatch.
            return 0
        elif first.type == "integer":
            # Integer literals must match.
            return first.attr == second.attr
        else:
            # Recursively compare all of the children.
            matched = 1
            for kidnum in range(0, len(first.kids)):
                matched = matched and self._compare_item_counts(first.kids[kidnum
], second.kids[kidnum])
            return matched

    def pre_reduce_stmt(self, node):
        "Perform a variety of tests of reduce statements."
        # Ensure that only INTEGERS or DOUBLEWORDS are being reduced.
        semobj = node.sem["semobj"]
        source_data_node = node.kids[1].kids[3]
        source_data_attr = source_data_node.attr
        target_data_node = node.kids[2].kids[3]
        target_data_attr = target_data_node.attr
        if source_data_attr not in ["integers", "doublewords"]:
            semobj.errmsg.error_fatal("only INTEGERS and DOUBLEWORDS can be reduced, not %s" %
                                      string.upper(source_data_attr),
                                      source_data_node.lineno0,
                                      source_data_node.lineno1)
        if target_data_attr not in ["integers", "doublewords"]:
            semobj.errmsg.error_fatal("only INTEGERS and DOUBLEWORDS can be reduced, not %s" %
                                      string.upper(target_data_attr),
                                      target_data_node.lineno0,
                                      target_data_node.lineno1)

        # Ensure that the reduce target specifies the same number of
        # INTEGER or DOUBLEWORD values as the reduce source.
        if source_data_attr != target_data_attr:
            semobj.errmsg.error_fatal('"%s" cannot reduce to "%s"' %
                                      (source_data_node.printable,
                                       target_data_node.printable),
                                      source_data_node.lineno0,
                                      target_data_node.lineno1)
        source_tally_node = node.kids[1].kids[0]
        target_tally_node = node.kids[2].kids[0]
        if not self._compare_item_counts(source_tally_node, target_tally_node):
            source_tally_printable = source_tally_node.printable
            if source_tally_node.kids[0].type == "an":
                source_tally_printable = "1"
            target_tally_printable = target_tally_node.printable
            if target_tally_node.kids[0].type == "an":
                target_tally_printable = "1"
            semobj.errmsg.error_fatal("The number of %s to reduce (%s) must match the number of %s in the result (%s)" %
                                      (source_data_attr, source_tally_printable,
                                       target_data_attr, target_tally_printable),
                                      source_tally_node.lineno0,
                                      target_tally_node.lineno1)

        # Forbid WITH VERIFICATION in the touching_type.
        source_touching_node = node.kids[1].kids[4].kids[0]
        target_touching_node = node.kids[2].kids[4].kids[0]
        if source_touching_node.type == "verification" and source_touching_node.attr == "verification":
            semobj.errmsg.error_fatal('"%s" is not allowed within a REDUCE statement' %
                                      source_touching_node.printable,
                                      source_touching_node.lineno0,
                                      source_touching_node.lineno1)
        if target_touching_node.type == "verification" and target_touching_node.attr == "verification":
            semobj.errmsg.error_fatal('"%s" is not allowed within a REDUCE statement' %
                                      target_touching_node.printable,
                                      target_touching_node.lineno0,
                                      target_touching_node.lineno1)
