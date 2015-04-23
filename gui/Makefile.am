###################################
# Build the coNCePTuaL GUI	  #
# By Scott Pakin <pakin@lanl.gov> #
###################################

# ----------------------------------------------------------------------
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
# ----------------------------------------------------------------------

@DEFINE_RM@

GUIJAVA = AbstractComponent.java AbstractDialog.java AST.java \
	  AutoScrollPane.java Block.java ComesFrom.java \
	  ComesFromsDialog.java CommunicationDialog.java \
	  CommunicationStmt.java ComputeDialog.java ComputeStmt.java \
	  Cursor.java DialogMenu.java DialogPane.java \
	  ExitDialog.java ExitWindowListener.java ExtendDialog.java \
	  GenericBlock.java GraphicsUtility.java IdButton.java IfBlock.java \
	  IfDialog.java LetBlock.java LetDialog.java LoadDialog.java \
	  LoopDialog.java Loop.java MainMenu.java MeasureBlock.java \
	  MeasureDialog.java MeasureExpression.java MulticastDialog.java \
	  MulticastStmt.java ncptlFileFilter.java ncptlGUIApplet.java \
	  ncptlGUI.java ncptlGUIMain.java OtherDialog.java OtherStmt.java \
	  Program.java ProgramReader.java ProgramWriter.java \
	  ReduceDialog.java ReduceStmt.java SettingsDialog.java \
	  SourceTarget.java Stmt.java SynchronizeDialog.java \
	  SynchronizeStmt.java TaskGroup.java Task.java TaskRow.java \
	  ToolBar.java Utility.java WaitDialog.java WaitStmt.java

GUIPY_PARENT = ncptl_keywords.py ncptl_lexer.py ncptl_parser.py	 \
	       ncptl_semantic.py ncptl_variables.py ncptl_ast.py \
	       ncptl_token.py codegen_interpret.py ncptl_config.py
GUIPY_PARENT_EXPLICIT = ncptl_error.py lex.py yacc.py ncptl_parse_table.py

EXTRA_DIST = $(LOCAL_PY) $(GUIJAVA)

# The following line utilizes a GNU Make extension (addprefix).
PARENT_PY = $(addprefix $(top_builddir)/,$(GUIPY_PARENT))
LOCAL_PY = GUIPyInterface.py gui_patches.py
GENERATED_PY = strop.py resource.py

# Support indexing of our Java source files and Python wrappers.
ETAGS_ARGS = $(GUIJAVA) $(LOCAL_PY)
TAGS_DEPENDENCIES = $(GUIJAVA) $(LOCAL_PY)

PYJARCONTENTS = $(PARENT_PY) $(LOCAL_PY)
JARDIR = jarbuild
PACKAGE_DIR = gov/lanl/c3/ncptl
PACKAGE_JARDIR = $(JARDIR)/$(PACKAGE_DIR)
DIR_FROM_PACKAGE_JARDIR = ../../../../..
JARPACKAGE = gov.lanl.c3.ncptl
JARFILE = ncptlGUI-$(PACKAGE_VERSION).jar
JFLAGS = -O -source 1.4 -sourcepath . -classpath $(JARFILE):$$CLASSPATH

# The following line utilizes a GNU Make extension (addprefix).
GUICLASS = $(addprefix $(PACKAGE_JARDIR)/,$(GUIJAVA:.java=.class))

gui: $(JARFILE)

.PHONY: gui

###########################################################################

# Create the build tree needed for compiling the GUI.

stamp-jardir $(PACKAGE_JARDIR): $(PYJARCONTENTS) $(top_builddir)/config.status
	$(INSTALL) -d $(PACKAGE_JARDIR)
	cp $(PYJARCONTENTS) $(JARDIR)
	for pyfile in $(GENERATED_PY) ; do \
	  echo "raise ImportError" > $(JARDIR)/$$pyfile ; \
	done
	cd $(PACKAGE_JARDIR) ; \
	  for jfile in $(GUIJAVA) ; do \
	    $(RM) $$jfile ; \
	    $(LN_S) $(DIR_FROM_PACKAGE_JARDIR)/$$jfile . ; \
	  done
	touch stamp-jardir

###########################################################################

# Compile all of the Python files needed by the GUI.
#
# Note that we have to patch ncptl_parse_table.py, lex.py, and yacc.py
# to make those work with the current version of Jython (2.2alpha1).

stamp-pyclasses: stamp-jardir \
	   $(JARDIR)/ncptl_error.py $(JARDIR)/ncptl_parse_table.py \
	   $(JARDIR)/lex.py $(JARDIR)/yacc.py
	cd $(JARDIR) ; \
	  $(JYTHONC) --compiler $(JAVAC) --compileropts "$(JFLAGS)" --core --jar $(JARFILE) --package $(JARPACKAGE) *.py
	touch stamp-pyclasses

$(JARDIR)/ncptl_error.py: $(top_srcdir)/ncptl_error.py stamp-jardir
	cat $(top_srcdir)/ncptl_error.py | sed -e 's/SystemExit/Exception/g' > $@

$(JARDIR)/ncptl_parse_table.py: $(top_srcdir)/makehelper.py $(top_builddir)/ncptl_parse_table.py stamp-jardir
	$(PYTHON) $(top_srcdir)/makehelper.py split-parsetab $(top_builddir)/ncptl_parse_table.py > $@

$(JARDIR)/lex.py: $(top_srcdir)/makehelper.py $(top_srcdir)/lex.py stamp-jardir
	$(PYTHON) $(top_srcdir)/makehelper.py patch-ply lex $(top_srcdir)/lex.py > $@

$(JARDIR)/yacc.py: $(top_srcdir)/makehelper.py $(top_srcdir)/yacc.py stamp-jardir
	$(PYTHON) $(top_srcdir)/makehelper.py patch-ply yacc $(top_srcdir)/yacc.py > $@

###########################################################################

# Compile all of the Java source files that constitute the GUI.

# The following line utilizes a GNU Make extension ("%" pattern matching).
$(PACKAGE_JARDIR)/%.class: %.java stamp-pyclasses
	cd $(JARDIR) ; \
	  $(JAVAC) $(JFLAGS) $(PACKAGE_DIR)/$<

stamp-javaclasses: $(GUICLASS)
	touch stamp-javaclasses

###########################################################################

# Produce a complete jar file.

if JAR_SUPPORTS_E

$(JARFILE): stamp-pyclasses stamp-javaclasses
	cd $(JARDIR) ; \
	  $(JAR) -ufe $(JARFILE) gov.lanl.c3.ncptl.ncptlGUIMain gov/lanl/c3/ncptl/*.class
	cp $(JARDIR)/$(JARFILE) $@

## Matches "JAR_SUPPORTS_E".
else

$(JARFILE): stamp-pyclasses stamp-javaclasses $(JARDIR)/MAIN-CLASS.MF
	cd $(JARDIR) ; \
	  $(JAR) -ufm $(JARFILE) MAIN-CLASS.MF gov/lanl/c3/ncptl/*.class
	cp $(JARDIR)/$(JARFILE) $@

$(JARDIR)/MAIN-CLASS.MF: stamp-jardir
	echo "Main-Class: gov.lanl.c3.ncptl.ncptlGUIMain" > $@

## Matches "JAR_SUPPORTS_E".
endif

###########################################################################

clean-local:
	-$(RM) stamp-pyclasses stamp-javaclasses stamp-jardir
	-$(RM) -r $(JARDIR) $(JARFILE)
