##############################################
# Build and install coNCePTuaL documentation #
# By Scott Pakin <pakin@lanl.gov>	     #
##############################################

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

info_TEXINFOS = conceptual.texi
GENERATED_TEXIS_DIST = ncptl-logextract-man.texi ncptl-logmerge-man.texi \
		       ncptl-logunmerge-man.texi
GENERATED_TEXIS_NODIST = keywords.texi variables.texi methods.texi           \
			 c_hooks.texi eventlist.texi aggregates.texi         \
			 placeholders.texi grammar-summary.texi license.texi \
			 langversion.texi cachevars.texi
GENERATED_TEXIS = $(GENERATED_TEXIS_DIST) $(GENERATED_TEXIS_NODIST)
TEXIMAGES = @TEXIMAGES@
TEXTIMAGES = @TEXTIMAGES@
LOGIMAGES = @LOGIMAGES@
AUXIMAGES = @AUXIMAGES@
DVIIMAGES = @DVIIMAGES@
EPSIMAGES = @EPSIMAGES@
PDFIMAGES = @PDFIMAGES@
JPEGIMAGES = @JPEGIMAGES@
PNGIMAGES = @PNGIMAGES@
IMAGEBYPRODUCTS=$(LOGIMAGES) $(AUXIMAGES) $(DVIIMAGES)
DISTIMAGES=$(TEXIMAGES) $(TEXTIMAGES) $(EPSIMAGES) \
	   backend-deps.dot gui.xcf gui.png walrus.xcf walrus.png tridiagonal.asy
BUILTIMAGES=@BUILTIMAGES@

all-local: $(GENERATED_TEXIS)

ALLTEXINFOS = $(info_TEXINFOS) $(GENERATED_TEXIS) $(srcdir)/stamp-vti $(srcdir)/version.texi
EXTRA_DIST = $(DISTIMAGES) $(GENERATED_TEXIS_DIST) $(BUILTMANS) \
	     ncptl.1.in ncptl-replaytrace.1.in
BUILTMANS = ncptl-logextract.1 ncptl-logmerge.1 ncptl-logunmerge.1
man_MANS = $(BUILTMANS) ncptl.1 ncptl-replaytrace.1
DOCFILES = conceptual.xml ncptl-logextract.pdf \
	   ncptl.pdf ncptl-replaytrace.pdf \
	   ncptl-logextract-ref.dot ncptl-logextract-ref.ps \
	   ncptl-logextract-ref.pdf ncptl-logextract.html
if LOGEXTRACT_WORKS
CLEANTEXIS = $(GENERATED_TEXIS)
endif
MOSTLYCLEANFILES = $(DOCFILES) $(BUILTIMAGES) $(CLEANTEXIS)             \
		   $(IMAGEBYPRODUCTS) DB_File.pm                        \
		   conceptual.{al,cps,ev,fi,fnd,kw,mn,nt,op,out,vr,vrs} \
		   conceptual.{aux,cp,fn,fns,ky,log,ol,pg,toc,tp,tps}   \
		   conceptual.{als,tmp,tmps} conceptual.info*
CLEANFILES = $(GENERATED_TEXIS_NODIST)
MAINTAINERCLEANFILES = conceptual.pdf gui.png gui.eps walrus.png walrus.eps

###########################################################################

# On demand, we can produce a PDF version of any man page.
.1.pdf:
	cat $< | groff -man | gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=$@ -c .setpdfwrite -f -

###########################################################################

if LOGEXTRACT_WORKS

MAINTAINERCLEANFILES += $(BUILTMANS)

# ncptl-logextract is a Perl script with embedded POD documentation.
# We can therefore produce a man page using pod2man.
ncptl-logextract.1: $(top_builddir)/ncptl-logextract $(srcdir)/mdate-sh $(top_srcdir)/makehelper.py
	pod2man --release="$(VERSION)" --center=" " --date="`$(srcdir)/mdate-sh .`" $(top_builddir)/ncptl-logextract | \
	  $(PYTHON) $(top_srcdir)/makehelper.py manpage > $@

# Do the same for ncptl-logmerge.
ncptl-logmerge.1: $(top_srcdir)/ncptl-logmerge $(srcdir)/mdate-sh $(top_srcdir)/makehelper.py
	pod2man --release="$(VERSION)" --center=" " --date="`$(srcdir)/mdate-sh .`" $(top_srcdir)/ncptl-logmerge | \
	  $(PYTHON) $(top_srcdir)/makehelper.py manpage > $@

# Do the same for ncptl-logunmerge.
ncptl-logunmerge.1: $(top_srcdir)/ncptl-logunmerge $(srcdir)/mdate-sh $(top_srcdir)/makehelper.py
	pod2man --release="$(VERSION)" --center=" " --date="`$(srcdir)/mdate-sh .`" $(top_srcdir)/ncptl-logunmerge | \
	  $(PYTHON) $(top_srcdir)/makehelper.py manpage > $@

# On demand, we can produce a dynamic HTML document which enables the
# user to expand and collapse the rather massive options list.
ncptl-logextract.html: $(top_builddir)/ncptl-logextract $(srcdir)/mdate-sh
	$(PERL) $(top_builddir)/ncptl-logextract --dhtml-man
	$(HTMLTIDY) ncptl-logextract.html ; true

# On demand, we can produce a poster-sized ncptl-logextract command-line
# options reference page.
ncptl-logextract-ref.pdf: ncptl-logextract-ref.ps
	ps2pdf -r100 -g3300x4675 ncptl-logextract-ref.ps ncptl-logextract-ref.pdf

ncptl-logextract-ref.ps: ncptl-logextract-ref.dot
	neato -Tps ncptl-logextract-ref.dot > ncptl-logextract-ref.ps

ncptl-logextract-ref.dot: $(top_builddir)/ncptl-logextract $(srcdir)/mdate-sh
	$(PERL) $(top_builddir)/ncptl-logextract --options-poster > ncptl-logextract-ref.dot

## Matches "LOGEXTRACT_WORKS"
endif

###########################################################################

# Store the current version of the coNCePTuaL language.
langversion.texi: $(top_srcdir)/ncptl_parser.py $(top_builddir)/ncptl_config.py
	echo "@set LANGUAGE-VERSION `PYTHONPATH=$(top_builddir):$$PYTHONPATH $(PYTHON) $(top_srcdir)/ncptl_parser.py -V`" > $@

# Just in case ncptl_config.py hasn't already been built we specify a
# rule to build it.
$(top_builddir)/ncptl_config.py:
	cd $(top_builddir) ; $(MAKE) $(AM_MAKEFLAGS) ncptl_config.py

# Produce an itemized list of keywords.
keywords.texi: $(top_srcdir)/ncptl_keywords.py
	echo "@itemize @bullet" > $@
	$(PYTHON) $(top_srcdir)/ncptl_keywords.py --apply=string.upper "@item\n@keyw{%s}\n\n" >> $@
	echo "@end itemize" >> $@

# Produce an itemized list of variables.
variables.texi: $(top_srcdir)/ncptl_variables.py
	echo "@table @asis" > $@
	$(PYTHON) $(top_srcdir)/ncptl_variables.py "@item @ocode{%s}\n%s\n\n" >> $@
	echo "@end table" >> $@

# Produce a list of methods that a backend must implement.
methods.texi: $(top_srcdir)/codegen_c_generic.py $(top_srcdir)/makehelper.py
	cat $(top_srcdir)/codegen_c_generic.py | \
	  $(PYTHON) $(top_srcdir)/makehelper.py methods > $@

# Produce a list of hooks that a derivative of codegen_c_generic.py
# may implement.
c_hooks.texi: $(top_srcdir)/codegen_c_generic.py $(top_srcdir)/makehelper.py
	cat $(top_srcdir)/codegen_c_generic.py | \
	  $(PYTHON) $(top_srcdir)/makehelper.py c_hooks > $@

# Produce a summary of all EBNF rules listed in the document.
grammar-summary.texi: $(srcdir)/conceptual.texi $(top_srcdir)/makehelper.py
	cat $(srcdir)/conceptual.texi | $(PYTHON) $(top_srcdir)/makehelper.py grammar > $@

# Acquire a list of events defined by codegen_c_generic.py.
eventlist.texi: $(top_srcdir)/codegen_c_generic.py $(top_srcdir)/makehelper.py
	cat $(top_srcdir)/codegen_c_generic.py | \
	  $(PYTHON) $(top_srcdir)/makehelper.py eventlist > $@

# Write a list of all placeholders defined by the latex_vis backend.
placeholders.texi: $(top_srcdir)/codegen_latex_vis.py $(top_srcdir)/makehelper.py
	$(PYTHON) $(top_srcdir)/makehelper.py placeholders $(top_srcdir)/codegen_latex_vis.py > $@

# Produce a list of aggregate functions and their definition.
aggregates.texi: $(top_srcdir)/ncptl.h.in
	echo "@table @asis" > $@
	cat $(top_srcdir)/ncptl.h.in | sed 's/[*\/]//g' | \
	  $(AWK) '/NCPTL_FUNC_/ {fname=$$1; sub(/,$$/, "", fname); $$1=""; printf "@item @ocode{%s}\n%s\n\n", fname, substr($$0,2)}' >> $@
	echo "@end table" >> $@

# Produce a list of cache variables that are used by configure.
cachevars.texi: $(top_srcdir)/makehelper.py \
		$(top_srcdir)/configure.ac $(top_builddir)/config.log
	$(PYTHON) $(top_srcdir)/makehelper.py cache-vars $(top_srcdir)/configure.ac $(top_builddir)/config.log > $@

# Convert the ncptl-logextract, ncptl-logmerge, and ncptl-logunmerge man pages to Texinfo format.
if LOGEXTRACT_WORKS
ncptl-logextract-man.texi: $(top_builddir)/ncptl-logextract $(top_srcdir)/Pod2NCPTLTexi.pm
	echo "@menu" > $@
	echo "* ncptl-logextract manual page::   The result of running \`\`ncptl-logextract --man''" >> $@
	echo "@end menu" >> $@
	echo "" >> $@
	echo "@c PUT_LICENSE_""TEXT_HERE" >> $@
	echo "" >> $@
	echo "@node ncptl-logextract manual page,  , ncptl-logextract, ncptl-logextract" >> $@
	$(PERL) -I$(top_srcdir) -MCarp=verbose $(top_builddir)/ncptl-logextract --texinfo-man >> $@

ncptl-logmerge-man.texi: $(top_srcdir)/ncptl-logmerge $(top_srcdir)/Pod2NCPTLTexi.pm
	echo "@menu" > $@
	echo "* ncptl-logmerge manual page::     The result of running \`\`ncptl-logmerge --man''" >> $@
	echo "@end menu" >> $@
	echo "" >> $@
	echo "@c PUT_LICENSE_""TEXT_HERE" >> $@
	echo "" >> $@
	echo "@node ncptl-logmerge manual page,  , ncptl-logmerge, ncptl-logmerge" >> $@
	$(PERL) -I$(top_srcdir) -MCarp=verbose $(top_srcdir)/ncptl-logmerge --texinfo-man >> $@

ncptl-logunmerge-man.texi: $(top_srcdir)/ncptl-logunmerge $(top_srcdir)/Pod2NCPTLTexi.pm DB_File.pm
	echo "@menu" > $@
	echo "* ncptl-logunmerge manual page::   The result of running \`\`ncptl-logunmerge --man''" >> $@
	echo "@end menu" >> $@
	echo "" >> $@
	echo "@c PUT_LICENSE_""TEXT_HERE" >> $@
	echo "" >> $@
	echo "@node ncptl-logunmerge manual page,  , ncptl-logunmerge, ncptl-logunmerge" >> $@
	$(PERL) -I$(top_srcdir) -MCarp=verbose $(top_srcdir)/ncptl-logunmerge --texinfo-man >> $@
	-$(RM) DB_File.pm

# We want to be able to build ncptl-logunmerge-man.texi even if we
# lack the not-always-present DB_File.pm.
DB_File.pm:
	if ! $(PERL) -e 'use DB_File' ; then \
	  echo 'package DB_File;' > $@ ; \
	  echo 'use vars qw(@ISA @EXPORT $$DB_HASH);' >> $@ ; \
	  echo 'push @ISA, qw(Exporter);' >> $@ ; \
	  echo '@EXPORT = qw($$DB_HASH);' >> $@ ; \
	  echo '1;' >> $@ ; \
	fi
endif

# Convert the coNCePTuaL copyright and license agreement to Texinfo
# format.  license.texi in fact depends on $(srcdir)/license.html but
# specifying that explicitly introduces a circular dependency, as
# Automake "knows" that .html files are created from .texi files and
# not the other way around.
license.texi: $(top_srcdir)/makehelper.py
	cat $(srcdir)/license.html | \
	  $(PYTHON) $(top_srcdir)/makehelper.py license-texi > $@

###########################################################################

html-local: conceptual.html
	$(INSTALL_DATA) $(PNGIMAGES) conceptual.html

conceptual.html: $(ALLTEXINFOS) $(PNGIMAGES)

conceptual.dvi: $(ALLTEXINFOS) $(EPSIMAGES)

conceptual.info: $(ALLTEXINFOS) $(TEXTIMAGES)

# I like PDF documentation.
.texi.pdf:
	TEXINPUTS="$(srcdir)$(PATH_SEPARATOR)$$TEXINPUTS" \
	MAKEINFO='$(MAKEINFO) $(AM_MAKEINFOFLAGS) $(MAKEINFOFLAGS) -I $(srcdir)' \
	PDFTEX=$(PDFTEX) \
	$(TEXI2DVI) --pdf $<

conceptual.pdf: $(ALLTEXINFOS) $(PDFIMAGES)

# We perform a few special touchups for the final run of Texinfo.
# First, we manually add a couple of "see" references to the index, as
# Texinfo doesn't seem to support such things.  Second, some index
# entries get wrapped in an \xeatspaces; others don't.  This
# discrepancy causes repeated entries in the index.  The solution is
# to manually remove all of the \xeatspaces macro calls.  Third, we
# re-typeset "coNCePTuaL" in small caps in the table of contents.
pdf: conceptual.pdf $(top_srcdir)/makehelper.py
	echo '\entry{average}{\see\ {\tt MEAN}}{average}' >> conceptual.al
	echo '\entry{MPI}{\see\ Message\ Passing\ Interface}{MPI}' >> conceptual.al
	echo '\entry{HPET}{\see\ High-Precision\ Event\ Timers}{HPET}' >> conceptual.al
	echo '\entry{PLY}{\see\ Python\ Lex--Yacc}{PLY}' >> conceptual.al
	$(PYTHON) $(top_srcdir)/makehelper.py xeatspaces conceptual.al > conceptual.tmp
	$(PYTHON) $(top_srcdir)/makehelper.py canon-keywords conceptual.tmp > conceptual.tmp2
	mv conceptual.tmp2 conceptual.tmp
	texindex conceptual.tmp
	(echo '\def\see{{\it see\/}}' ; \
	 cat conceptual.tmps | \
	   sed -e 's/{LaTeX}/{\\LaTeX}/' \
	       -e 's/{TeX}/{\\TeX}/') > conceptual.als
	sed 's/coNCePTuaL/\\sc{coNCePTuaL}/g' conceptual.toc > conceptual.tmp
	mv conceptual.tmp conceptual.toc
	$(PDFTEX) conceptual.texi

# DocBook is nice and general.	Produce DocBook documentation, too.
.texi.xml:
	$(MAKEINFO) $(AM_MAKEINFOFLAGS) $(MAKEINFOFLAGS) -I $(srcdir) --docbook $<

# We don't know a priori what format DocBook will be converted to.
# Hence, we build the images in a variety of formats.
conceptual.xml: $(ALLTEXINFOS) $(BUILTIMAGES) $(TEXTIMAGES)

docbook: conceptual.xml


if HAVE_TEX

# Convert the images needed by the Texinfo documentation into the
# format needed by each backend.
.tex.dvi:
	if [ `grep -c documentclass $<` -gt 0 ] ; then \
	  $(LATEX) $< ;                                \
	else                                           \
	  $(TEX) $< ;                                  \
	fi

# Dvips "sees" only text, which means that graphics are not included
# in the resulting bounding box.  As a hack, we explicitly add a small
# border around each image we process.
.dvi.eps:
	$(DVIPS) -E -Ppdf -Pcmz -o - $< | \
	  $(PERL) -ne 's/^(\%\%(?:HiRes)?BoundingBox:) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)/sprintf "%s %s %s %s %s", $$1, $$2-5, $$3-5, $$4+5, $$5+5/e; print' > $@


## Matches "HAVE_TEX"
else

.tex.dvi:
	@echo '==========================================================='
	@echo 'WARNING: $< was modified but configure could'
	@echo 'not locate tex.  As a result, $@ will not be '
	@echo 'regenerated.'
	@echo '==========================================================='

.dvi.eps:
	@echo '==========================================================='
	@echo 'WARNING: $< was modified but configure could'
	@echo 'not locate a TeX distribution.  As a result, $@'
	@echo 'will not be regenerated.'
	@echo '==========================================================='

## Matches "HAVE_TEX"
endif

if HAVE_DOT
.dot.eps:
	$(DOT) -Tps $< > $@
endif

.eps.pdf:
	epstopdf --outfile=$@ $<

.eps.jpg:
	$(GS) -dNOPAUSE -dBATCH -q -dDEVICEXRESOLUTION=1000	       \
	  -dDEVICEYRESOLUTION=1000 -sDEVICE=ppmraw -sOutputFile=- $< | \
	  pnmcrop | pnmscale 0.1 | ppmtojpeg > $@

.eps.png:
	$(GS) -dNOPAUSE -dBATCH -q -dDEVICEXRESOLUTION=1000 	       \
	  -dDEVICEYRESOLUTION=1000 -sDEVICE=ppmraw -sOutputFile=- $< | \
	  pnmcrop | pnmscale 0.1 | pnmtopng -transparent white > $@

.PRECIOUS: $(EPSIMAGES)

###########################################################################

# We have some special cases for gui.* and walrus.*, which are
# generated from GIMP images.

if HAVE_GIMP

gui.png: gui.xcf
	(echo '(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "$(srcdir)/gui.xcf" "gui.xcf")))' ; \
	 echo '       (drawable (car (gimp-image-merge-visible-layers image 0))))' ; \
	 echo '  (plug-in-autocrop RUN-NONINTERACTIVE image drawable)' ; \
	 echo '  (file-png-save RUN-NONINTERACTIVE image drawable' ; \
	 echo '		        "gui.png" "gui.png"' ; \
	 echo '		        FALSE 9 TRUE FALSE FALSE FALSE TRUE))' ; \
	 echo '(gimp-quit FALSE)') | \
	  gimp --no-interface --batch -

walrus.png: walrus.xcf
	(echo '(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "$(srcdir)/walrus.xcf" "walrus.xcf")))' ; \
	 echo '       (drawable (car (gimp-image-merge-visible-layers image 0))))' ; \
	 echo '  (plug-in-autocrop RUN-NONINTERACTIVE image drawable)' ; \
	 echo '  (file-png-save RUN-NONINTERACTIVE image drawable' ; \
	 echo '		        "walrus.png" "walrus.png"' ; \
	 echo '		        FALSE 9 TRUE FALSE FALSE FALSE TRUE))' ; \
	 echo '(gimp-quit FALSE)') | \
	  gimp --no-interface --batch -

.xcf.eps:
	(echo '(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "$(srcdir)/$<" "$<")))' ; \
	 echo '       (drawable (car (gimp-image-flatten image))))' ; \
	 echo '  (plug-in-autocrop RUN-NONINTERACTIVE image drawable)' ; \
	 echo '  (file-eps-save RUN-NONINTERACTIVE image drawable' ; \
	 echo '		        "$@" "$@"' ; \
	 echo '		        0.0 0.0 0.0 0.0' ; \
	 echo '		        0 1 0 1 0 2))' ; \
	 echo '(gimp-quit FALSE)') | \
	  gimp --no-interface --batch -


gui.eps: $(srcdir)/gui.xcf

walrus.eps: $(srcdir)/walrus.xcf

## Matches "HAVE_GIMP"
endif

###########################################################################

# We have a special cases for tridiagonal.*, which are generated from
# Asymptote code.

if HAVE_ASY

tridiagonal.eps: tridiagonal.asy
	asy tridiagonal.asy

tridiagonal.pdf: tridiagonal.asy
	asy -f pdf tridiagonal.asy

## Matches "HAVE_ASY"
endif

###########################################################################
