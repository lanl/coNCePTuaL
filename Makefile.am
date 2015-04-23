#############################################
# Build and install the coNCePTuaL compiler #
# By Scott Pakin <pakin@lanl.gov>           #
#############################################

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
ncptl_includedir = $(includedir)/ncptl
ncptl_examplesdir = $(pkgdatadir)/examples
MOSTLYCLEANFILES = ncptl.php.tmp
CLEANFILES = empty.log $(STYLESHEETS) $(PACKAGE)_$(VERSION)	\
	     ncptl_backends.pyc ncptl_config.pyc ncptl_ast.pyc	\
	     ncptl_error.pyc ncptl_token.pyc lex.pyc yacc.pyc   \
	     $(nodist_pkgpython_DATA) $(conceptual_TEXINFOS)
DISTCLEANFILES = ncptl.h.ni ncptl.h signalmap.c substitutions.dat.in \
	         ncptl.pc.in extra_config.h ncptl-logextract 	     \
		 ncptl-logextract_keywords libncptl.i.in 	     \
		 $(nodist_pkgpython_DATA)
AUTOMAKE_OPTIONS = foreign
ACLOCAL_AMFLAGS = -I m4
bin_SCRIPTS = ncptl-logextract ncptl-logmerge ncptl-logunmerge
ncptl_examples_DATA = @EXAMPLEFILES@
STYLESHEETS = ncptl.ssh ncptl.sty ncptl.vim ncptl.lang ncptl.php \
	      ncptl-mode.el ncptl-mode.elc
STYLESHEETS_IN = ncptl.ssh.in ncptl.sty.in ncptl.vim.in ncptl.lang.in \
	         ncptl.php.in ncptl-mode.el.in
EXTRA_DIST = $(STYLESHEETS_IN) $(EXTRA_PYTHON) $(ncptl_examples_DATA)    \
	     libncptl_extras.i libncptl_wrap.c.in pyncptl.py __init__.py \
	     Makefile.simple.in	conceptual.spec.in doc/conceptual.pdf    \
	     ncptl-logextract.in ncptl-logmerge ncptl-logunmerge	 \
	     Pod2NCPTLTexi.pm README INSTALL LICENSE doc/license.html    \
	     doc/mdate-sh conceptual.apspec.in
SUBDIRS = tests doc gui

###########################################################################

# Prepare the core Python files that make up coNCePTuaL.
BACKENDS = @BACKENDS@
PYEXECS = ncptl.py ncptl-replaytrace.py
PYCOMPILER = ncptl_keywords.py ncptl_lexer.py ncptl_parser.py	 \
	     ncptl_semantic.py ncptl_error.py ncptl_variables.py \
	     ncptl_ast.py ncptl_token.py lex.py yacc.py
PYFILES = $(PYEXECS) $(PYCOMPILER) $(BACKENDS)

# Because the following are generated into the build directory, we
# can't install them from the source directory.  Hence, instead of
# nodist_pkgpython_PYTHON we use nodist_pkgpython_DATA plus a line
# in install-exec-hook.
nodist_pkgpython_DATA = ncptl_backends.py ncptl_config.py \
			   ncptl_parse_table.py

pkgpython_PYTHON = $(PYFILES)
EXTRA_PYTHON = codegen_c_mpi.py codegen_c_generic.py codegen_c_udgram.py   \
	       codegen_c_trace.py codegen_c_seq.py codegen_dot_ast.py      \
	       codegen_interpret.py codegen_picl.py codegen_latex_vis.py   \
	       codegen_c_profile.py codegen_stats.py codegen_libsea_ast.py \
	       codegen_paraver.py makehelper.py

###########################################################################

# Create a list of backends.
ncptl_backends.py: $(BACKENDS) $(top_srcdir)/makehelper.py $(top_builddir)/config.status
	$(PYTHON) $(top_srcdir)/makehelper.py backends `echo $(BACKENDS) | sed 's/codegen_c_generic.py//g'` > $@

# Convert config.h and substitutions.dat into a Python associative
# array.  Although using "cpp -dM" simplifies the task, it's not
# supported by every C preprocessor.
ncptl_config.py: $(top_builddir)/config.h $(top_builddir)/substitutions.dat \
	         $(top_srcdir)/makehelper.py $(top_builddir)/config.status
	$(PYTHON) $(top_srcdir)/makehelper.py config 			      \
	  '$(CPP) $(DEFAULT_INCLUDES) $(INCLUDES) $(AM_CPPFLAGS) $(CPPFLAGS)' \
	  $(top_builddir)/config.h $(top_builddir)/substitutions.dat > $@

# Save the SLR parse table to ncptl_parse_table.py so the parse table
# doesn't have to be regenerated every time the compiler is invoked.
ncptl_parse_table.py: $(top_srcdir)/ncptl_parser.py $(top_builddir)/ncptl_config.py
	env PYTHONPATH=$(top_builddir):$$PYTHONPATH $(PYTHON) $(top_srcdir)/ncptl_parser.py --compile
	chmod -x ncptl_parse_table.py

###########################################################################

# Compile all of the generated, non-distributed Python files then
# install symbolic links in the bin directory for all of the
# executable Python scripts.
install-data-hook: $(top_srcdir)/makehelper.py
	PYTHON=$(PYTHON) $(py_compile) --basedir $(DESTDIR)$(pkgpythondir) $(nodist_pkgpython_DATA)
	-ABS_TOP_SRCDIR=`cd $(top_srcdir) ; pwd` ; \
	  cd $(DESTDIR)$(bindir) ; \
	  for pyexec in $(PYEXECS) ; do \
	    $(RM) `basename $${pyexec} .py` ; \
	    chmod +x $(DESTDIR)$(pkgpythondir)/$${pyexec} ; \
	    $(PYTHON) $${ABS_TOP_SRCDIR}/makehelper.py rsymlink $(LN_S) $(DESTDIR)$(pkgpythondir)/$${pyexec} `basename $${pyexec} .py` ; \
	  done

uninstall-hook:
	-for binfile in $(PYEXECS) ; do \
	  $(RM) $(DESTDIR)$(bindir)/`basename $$binfile .py` ; \
	done
	-$(RM) -r $(DESTDIR)$(ncptl_includedir)
	-$(RM) -r $(DESTDIR)$(ncptl_examplesdir)
	-$(RM) -r $(DESTDIR)$(pkgpythondir)
	-$(RM) -r $(DESTDIR)$(pkgpyexecdir)
	-$(RM) -r $(DESTDIR)$(pkgdatadir)
	-$(RM) -r $(DESTDIR)$(pyexecdir)/$(LIBNCPTLMODULE)

###########################################################################

# Add support for libtool.
libtool: $(LIBTOOL_DEPS)
	$(SHELL) $(top_builddir)/config.status --recheck

###########################################################################

MOSTLYCLEANFILES += compiler_version.h
CLEANFILES += signallist.c signallist.dat

if BUILD_RUN_TIME_LIBRARY

#-------------------------------------------------------------------------#

# Build the run-time library.
lib_LTLIBRARIES = libncptl.la
libncptl_la_SOURCES = runtimelib.c mt19937-64-sdp.c userfuncs.c		    \
	              logfilefuncs.c queuefuncs.c memfuncs.c sysinfofuncs.c \
	              touchmem.c setfuncs.c runtimelib.h extra_config.h
nodist_libncptl_la_SOURCES = signalmap.c ncptl.h compiler_version.h
libncptl_la_LDFLAGS = -version-info @LIBTOOL_CURRENT@:@LIBTOOL_REVISION@:@LIBTOOL_AGE@ @LIBRARY_ENTRY_POINT@
nodist_ncptl_include_HEADERS = ncptl.h
BUILT_SOURCES = ncptl.h signalmap.c $(LIBNCPTL_WRAP_C) compiler_version.h \
		extra_config.h

# Create a header file which defines a string representing the version
# of the C compiler being used.
compiler_version.h: $(top_srcdir)/makehelper.py
	$(PYTHON) $(top_srcdir)/makehelper.py compiler '$(CC)' > $@

# Create a function that maps from signal names to signal numbers.
signallist.c: $(top_srcdir)/makehelper.py
	$(PYTHON) $(top_srcdir)/makehelper.py signallist_c > $@

signallist.dat: signallist.c
	$(CPP) signallist.c | egrep '^"SIG[A-Z]+" *, +[0-9]+ *.?$$' > $@

if HAVE_GPERF

signalmap.c: signallist.dat $(top_srcdir)/makehelper.py
	cat signallist.dat | \
	  $(PYTHON) $(top_srcdir)/makehelper.py signalmap_c $(GPERF) > $@

## Matches "HAVE_GPERF".
else

signalmap.c: signallist.dat $(top_srcdir)/makehelper.py
	cat signallist.dat | \
	  $(PYTHON) $(top_srcdir)/makehelper.py signalmap_c > $@

## Matches "HAVE_GPERF".
endif

#-------------------------------------------------------------------------#

# Create a log file with all headers but no data.
empty.log: $(top_srcdir)/writelog
	$(top_srcdir)/writelog emptylog-%p.log
	mv emptylog-0.log empty.log

noinst_PROGRAMS = writelog
writelog_SOURCES = writelog.c ncptl.h
writelog_LDADD = libncptl.la

# Create a program to (crudely) test the accuracy of ncptl_time().
noinst_PROGRAMS += validatetimer
validatetimer_SOURCES = validatetimer.c ncptl.h
validatetimer_LDADD = libncptl.la

#-------------------------------------------------------------------------#

## Matches "if BUILD_RUN_TIME_LIBRARY".
endif

###########################################################################

# Build (but don't install) an a2ps style sheet.
ncptl.ssh: $(top_srcdir)/ncptl.ssh.in $(top_srcdir)/ncptl_keywords.py $(top_builddir)/config.status
	KEYWORD_LIST=`$(PYTHON) $(top_srcdir)/ncptl_keywords.py --last='\"%s\"' '\"%s\",'` ; \
	cat $(top_srcdir)/ncptl.ssh.in | \
	  sed "s%MAKE SHOULD HAVE REPLACED THIS LINE%$${KEYWORD_LIST}%" > $@

# Build (but don't install) a LaTeX style.
ncptl.sty: $(top_srcdir)/ncptl.sty.in $(top_srcdir)/ncptl_keywords.py $(top_builddir)/config.status
	KEYWORD_LIST=`$(PYTHON) $(top_srcdir)/ncptl_keywords.py --last='%s' '%s,'` ; \
	cat $(top_srcdir)/ncptl.sty.in | \
	  sed "s,????/??/??,`date +%Y/%m/%d`," | \
	  sed "s%MAKE SHOULD HAVE REPLACED THIS LINE%$${KEYWORD_LIST}%" > $@

# Build (but don't install) a Vim syntax file.
ncptl.vim: $(top_srcdir)/ncptl.vim.in $(top_srcdir)/ncptl_keywords.py $(top_builddir)/config.status
	cat $(top_srcdir)/ncptl.vim.in | \
	  $(AWK) '/MAKE SHOULD HAVE REPLACED THIS LINE/ {exit}; {print}' > $@
	$(PYTHON) $(top_srcdir)/ncptl_keywords.py 'syntax keyword ncptlKeyword %s\n' >> $@
	cat $(top_srcdir)/ncptl.vim.in | \
	  $(AWK) 'enabled; /MAKE SHOULD HAVE REPLACED THIS LINE/ {enabled=1}' >> $@

# Build (but don't install) a Source-highlight language definition.
ncptl.lang: $(top_srcdir)/ncptl.lang.in $(top_srcdir)/ncptl_keywords.py $(top_builddir)/config.status
	echo 'include "function.lang"' > $@
	echo "" >> $@
	$(PYTHON) $(top_srcdir)/ncptl_keywords.py | \
	  $(AWK) '\
	    { kw[n++] = $$1 }; \
	    END { \
	      printf "keyword = \"%s", kw[0]; \
	      for (i=1; i<n; i++) \
		printf "%s%s", i%5==0 ? "\",\n          \"" : "|", kw[i]; \
	      print "\"" \
	    }' >> $@
	cat $(top_srcdir)/ncptl.lang.in >> $@

# Build (but don't install) a GeSHi language definition.
ncptl.php: $(top_srcdir)/ncptl.php.in $(top_srcdir)/ncptl_keywords.py $(top_builddir)/config.status
	$(PYTHON) $(top_srcdir)/ncptl_keywords.py --last="\'%s\'" "\'%s'," | \
	  fmt -63 | $(AWK) '{print "            " $$0}' > ncptl.php.tmp
	cat $(top_srcdir)/ncptl.php.in | \
	  $(SED) -e "/'MAKE SHOULD HAVE REPLACED THIS LINE'/{" \
		 -e "r ncptl.php.tmp" \
		 -e "d" \
		 -e "}" > $@
	$(RM) ncptl.php.tmp

# Build (but don't install) an Emacs major mode.
ncptl-mode.el: $(top_srcdir)/ncptl-mode.el.in $(top_srcdir)/ncptl_keywords.py $(top_builddir)/config.status
	KEYWORD_LIST=`$(PYTHON) $(top_srcdir)/ncptl_keywords.py '\"%s\"'` ; \
	cat $(top_srcdir)/ncptl-mode.el.in | \
	  sed "s%MAKE SHOULD HAVE REPLACED THIS LINE%$${KEYWORD_LIST}%" > $@

noinst_LISP = ncptl-mode.el

# Build all of the above plus a byte-compiled version of ncptl-mode.el.
stylesheets: $(STYLESHEETS)
	@echo "---------------------------------------------------------------------------"
	@echo The following stylesheets were generated and should be installed manually
	@echo in appropriate locations for your system:
	@echo ""
	@for sty in $(STYLESHEETS) ; do \
	  if [ -e $$sty ] ; then \
	    echo "  * $$sty" ; \
	  fi ; \
	done
	@echo "---------------------------------------------------------------------------"

###########################################################################

# Work around Automake 1.6's inability to handle an AM_CONFIG_HEADER
# and an AC_CONFIG_FILES that refer to the same file.  See
# configure.ac for more information.
ncptl.h: $(top_builddir)/config.status ncptl.h.ni $(top_srcdir)/configure.ac $(ACLOCAL_M4)
	cd $(top_builddir) && $(SHELL) ./config.status $@
	cd $(top_srcdir) && $(AUTOHEADER)
	touch $(srcdir)/ncptl.h.ni

###########################################################################

RPMBUILD = rpmbuild
RPMDIR = $(top_builddir)/rpmdir

# Build RPM source and binary packages.

rpms: smart-distcheck $(top_srcdir)/conceptual.spec
	-$(RM) -r $(RPMDIR)
	mkdir $(RPMDIR)
	mkdir $(RPMDIR)/SOURCES
	mkdir $(RPMDIR)/BUILD
	mkdir $(RPMDIR)/SRPMS
	mkdir $(RPMDIR)/RPMS
	$(INSTALL_DATA) $(distdir).tar.gz $(RPMDIR)/SOURCES/
	PREVDIR=`pwd` ; cd $(RPMDIR) ; ABSRPMDIR=`pwd` ; cd $${PREVDIR} ; \
	  $(RPMBUILD) --define="_topdir $${ABSRPMDIR}" -ba $(top_srcdir)/conceptual.spec
	cp $(RPMDIR)/SRPMS/*.rpm $(RPMDIR)/RPMS/*/*.rpm .
	$(RM) -r $(RPMDIR)

# Build Debian source and binary packages.

dpkg: smart-distcheck $(top_srcdir)/debian
	-$(RM) -r $(distdir)
	tar -xzvf $(distdir).tar.gz
	-cd $(distdir) && \
	  echo "" | dh_make --email @PACKAGE_BUGREPORT@ --single \
	    --defaultless --file ../$(distdir).tar.gz ; \
	  $(RM) -r debian ; \
	  cp -r ../debian debian ; \
	  $(RM) -r debian/CVS ; \
	  debuild $(DEBUILD_OPTS) --no-tgz-check --lintian-opts -i --profile debian
	$(RM) -r $(distdir)

# Build an Autopackage package.  For now we assume that "make
# smart-distcheck" produces a .tar.gz file.

autopackage: smart-distcheck $(top_srcdir)/conceptual.apspec
	-$(RM) -r $(distdir)
	GZIP=$(GZIP_ENV) gunzip -c $(distdir).tar.gz | $(am__untar)
	ABS_TOP_SRCDIR=`cd $(top_srcdir) ; pwd` ; \
	  cd $(distdir) ; \
	  $(MAKEPACKAGE) $${ABS_TOP_SRCDIR}/conceptual.apspec
	mv $(distdir)/coNCePTuaL_$(VERSION).package .
	$(RM) -r $(distdir)

if HAVE_MSGDIGEST

# "make distcheck" is a slow operation.  When producing a complete
# coNCePTuaL release, we have to invoke "make distcheck" three times:
# once to build a Debian package, once to build an RPM, and once to
# build an Autopackage.  To save time, we use $(MSGDIGEST) to
# determine if an existing tarball was produced by "make distcheck"
# and therefore does not need to be regenerated.  Note that "make
# smart-distcheck" assumes that we are producing a .tar.gz file.

smart-distcheck:
	SUMFILE=$(distdir).sum ; \
	  REGENERATE=yes ; \
	  if [ -e $$SUMFILE ] ; then \
	    if $(MSGDIGEST) -c $$SUMFILE ; then \
	      REGENERATE=no ; \
	    fi ; \
	  fi ; \
	  if [ "$$REGENERATE" = yes ] ; then \
	    $(MAKE) $(AM_MAKEFLAGS) distcheck ; \
	  fi

distcheck-hook:
	$(MSGDIGEST) $(distdir).tar.gz > $(distdir).sum

## Matches "HAVE_MSGDIGEST".
else

# Without a message-digest utility we can't be particularly smart
# about avoiding time-consuming "make distcheck" builds.  If possible,
# you should install a message-digest utility such as sha1sum or
# md5sum and re-run the configure script.

smart-distcheck: distcheck

## Matches "HAVE_MSGDIGEST".
endif

.PHONY: smart-distcheck

###########################################################################

# Clean up any directories we might have created.
mostlyclean-local:
	-$(RM) -r $(JARDIR)
	-$(RM) -r $(RPMDIR)
	-$(RM) -r build

###########################################################################

# Forward documentation requests to the doc subdirectory.
pdf docbook:
	cd doc && $(MAKE) $(AM_MAKEFLAGS) $@

# Build explicitly named PDF and HTML files.
%.pdf %.html:
	cd doc && $(MAKE) $(AM_MAKEFLAGS) $@

# The following is needed by "make dist".
doc/conceptual.pdf:
	cd doc && $(MAKE) $(AM_MAKEFLAGS) pdf

# Forward GUI-building requests to the gui subdirectory.
gui: $(nodist_pkgpython_DATA)
	cd gui && $(MAKE) $(AM_MAKEFLAGS) $@

.PHONY: pdf docbook gui

###########################################################################

# Build a module file.
modulefile: $(PACKAGE)_$(VERSION)
	@echo "---------------------------------------------------------------------------"
	@echo "The $(PACKAGE)_$(VERSION) modulefile should be installed in an appropriate"
	@echo "location for your system (i.e., in one of the directories listed in"
	@echo "the MODULEPATH environment variable)."
	@echo "---------------------------------------------------------------------------"

$(PACKAGE)_$(VERSION): doc/mdate-sh $(top_srcdir)/makehelper.py
	$(PYTHON) $(top_srcdir)/makehelper.py modulefile $(VERSION) $(bindir) $(mandir) $(libdir) > $@

.PHONY: modulefile

###########################################################################

# Attach the coNCePTuaL license to every file we distribute.  Also,
# remove all DISTCLEANFILES from the distribution, as they'll be
# regenerated by configure.  Finally, as a particularly obnoxious
# kludge, rebuild stamp-vti now while we still have write access to
# the doc directory; this prevents "make distcheck" from bombing when
# it tries to regenerate stamp-vti in a read-only doc directory.
dist-hook: $(top_builddir)/LICENSE $(top_srcdir)/makehelper.py
	cd $(distdir) ; $(RM) $(DISTCLEANFILES)
	find $(distdir) -type f | \
	  xargs $(PYTHON) $(top_srcdir)/makehelper.py add-license $(top_srcdir)/LICENSE
	-cd doc ; \
	  $(RM) stamp-vti ; \
	  $(MAKE) $(AM_MAKEFLAGS) stamp-vti
	-$(INSTALL_DATA) doc/stamp-vti $(distdir)/doc

###########################################################################

# Create a LICENSE file from license.html.

$(top_builddir)/LICENSE: $(top_srcdir)/doc/license.html $(top_srcdir)/makehelper.py
	cat $(top_srcdir)/doc/license.html | \
	  $(PYTHON) $(top_srcdir)/makehelper.py license-text > $(top_builddir)/LICENSE

CLEANFILES += LICENSE


# Output the current value of pkgdatadir for use by
# conceptual.apspec.in in creating a Zero Install Injector wrapper
# script.

show-pkgdatadir:
	@echo $(pkgdatadir)

###########################################################################

# Output configuration parameters that the user may want to override.
# (This target is called by configure.)

showenv:
	@echo '    CC          = $(CC)'
	@echo '    CPPFLAGS    = $(CPPFLAGS)'
	@echo '    CFLAGS      = $(CFLAGS)'
	@echo '    CCLD        = $(CCLD)'
	@echo '    LDFLAGS     = $(LDFLAGS)'
	@echo '    LIBS        = $(LIBS)'
	@echo '    '
	@echo '    MPICC       = $(MPICC)'
	@echo '    MPICPPFLAGS = $(MPICPPFLAGS)'
	@echo '    MPICFLAGS   = $(MPICFLAGS)'
	@echo '    MPILDFLAGS  = $(MPILDFLAGS)'
	@echo '    MPILIBS     = $(MPILIBS)'
	@echo '    '
	@echo '    PYTHON      = $(PYTHON)'

###########################################################################

# If BUILD_PYMODULE is false, we assume a worst-case scenario -- that
# swig is broken, Python.h is missing, and the compiler chokes on
# libncptl_write.c.
if BUILD_PYMODULE

SWIG_OUTPUTS = libncptl_wrap.c pyncptl.py __init__.py

# We can't run the coNCePTuaL interpreter (part of "make check") without
# first creating a few modules it needs.  We then symlink the SWIG
# outputs from the source directory to the target directory because
# that's where "makehelper.py install" expects to find them.  Note that
# we use "test -f" instead of "test -e" because the Bourne shell (at
# least, on a Solaris 9 system I tried) doesn't honor "test -e".
all-local: $(nodist_pkgpython_DATA) $(SWIG_OUTPUTS)
	for swout in libncptl_wrap.c pyncptl.py ; do \
	  test -f $(top_builddir)/$$swout || $(LN_S) $(top_srcdir)/$$swout $(top_builddir)/$$swout ; \
	done

# Define a dummy number (the hexadecimal version of the string
# "coNCePTuaL") which we can detect and replace.
DUMMYNUMBER = 0x636F4E4365505475614C

# Generate a SWIG interface file by processing special comments in
# ncptl.h, ensuring that every function prototype ends in ");" (with
# no intervening line break), converting enumerated types to
# preprocessor defines, and replacing "LOG_AGGREGATE" with "int"
# (which is a lot easier than trying to get SWIG to map the type
# correctly).
libncptl.i.in: ncptl.h.in
	cat $(top_srcdir)/ncptl.h.in | \
	  sed "s,^/[*] SWIG: \\(.*\\) [*]/,\\1," | \
	  sed "s,^extern .*[^;,]\$$,&;," | \
	  $(AWK) -F, '\
	    in_enum && /}/ {in_enum=0; next}; \
	    in_enum {printf "#define %s %d\n", $$1, in_enum++-1}; \
	    /typedef enum {/ {in_enum=1}; \
	    !in_enum' | \
	  sed "s,LOG_AGGREGATE,int,g" | \
	  sed 's,[@]NICS[@],"$(DUMMYNUMBER)",g' | \
	  sed 's,[@]LIBTOOL_CURRENT[@],$(DUMMYNUMBER),g' > $@

if HAVE_SWIG

# We have SWIG; use it to create libncptl_wrap.c.in and pyncptl.py.
# Older versions of SWIG don't produce pyncptl.py so we have to
# generate it ourself.
libncptl_wrap.c.in pyncptl.py __init__.py: libncptl.i.in libncptl_extras.i ncptl_config.py
	$(RM) $@
	$(SWIG) $(SWIGFLAGS) -python -I$(srcdir) -o libncptl_wrap.tmp libncptl.i.in
	$(AWK) '/NCPTL_RUN_TIME_VERSION/ {sub(/$(DUMMYNUMBER)/, "@LIBTOOL_" "CURRENT@")}; \
		/NICS/ {sub(/"$(DUMMYNUMBER)"/, "@NICS" "@")}; \
		{print}' libncptl_wrap.tmp > libncptl_wrap.c.in
	$(RM) libncptl_wrap.tmp
	env PYTHONPATH=$(top_builddir):$$PYTHONPATH $(PYTHON) $(top_srcdir)/makehelper.py pyncptl

LIBNCPTL_WRAP_C = libncptl_wrap.c

## Matches "HAVE_SWIG".
else

# Issue a warning message if ncptl.h.in is modified but we can't
# rebuild the Python interface to match.
libncptl_wrap.c.in pyncptl.py: ncptl.h.in
	@echo '========================================================'
	@echo 'WARNING: ncptl.h.in was modified but configure could not'
	@echo 'locate SWIG.  As a result, the Python interface to the  '
	@echo 'coNCePTuaL run-time library may not function correctly. '
	@echo '========================================================'

## Matches "HAVE_SWIG".
endif

# Whether or not we have SWIG we perform all of the necessary
# variable substitutions on libncptl_wrap.c.in to produce
# libncptl_wrap.c.
libncptl_wrap.c: libncptl_wrap.c.in $(top_builddir)/config.status
	$(SHELL) $(top_builddir)/config.status --file=libncptl_wrap.c.ni:libncptl_wrap.c.in
	$(SHELL) $(top_builddir)/config.status --header=libncptl_wrap.c:libncptl_wrap.c.ni

# The preceding commands to generate libncptl_wrap.c leave a stamp
# file lying around.
distclean-local:
	$(RM) stamp-h*


# Use Python's distutils to build the pyncptl package, which interfaces the
# coNCePTuaL run-time library to Python.
install-exec-hook: $(SWIG_OUTPUTS)
	chmod -R u+w $(DESTDIR)$(libdir)
	-env PYTHONPATH=$(top_builddir):$$PYTHONPATH $(PYTHON) $(top_srcdir)/makehelper.py install $(top_builddir) --prefix=$(DESTDIR)$(exec_prefix) --install-platlib=$(DESTDIR)$(pyexecdir) --install-purelib=$(DESTDIR)$(pythondir)

## Matches "if BUILD_PYMODULE".
else
install-exec-hook:
	@:
endif

CLEANFILES += libncptlmodule.la libncptl_wrap.lo pyncptl.pyc libncptl_wrap.c \
	      libncptl_wrap.c.ni ncptl_parse_table.pyc
MAINTAINERCLEANFILES = $(SWIG_OUTPUTS) libncptl.i.in libncptl.i \
		       libncptl_wrap.c.in $(distdir).sum

# Prevent "make distcheck" from complaining about our generated but
# distributed files.
distcleancheck_listfiles = find . -type f ! \( -name ncptl-log\*.1 -o -name libncptl_wrap.c.in -o -name pyncptl.py -o -name __init__.py \) -print

###########################################################################
