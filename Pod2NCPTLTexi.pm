########################################################################
#
# POD-to-Texinfo parser designed specifically for producing a
# subsection of the coNCePTuaL documentation
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

package TexinfoParser;

use Pod::Parser;
use Carp;
use warnings;
use strict;

our @ISA = qw(Pod::Parser);
our $VERSION = "1.0";

# Declare a stack of list types or "???" (meaning: need @itemize/@table)
my @list_types;

# Process POD commands.
sub command
{
    my ($parser, $command, $paragraph, $line_num) = @_;
    my $output = "";   # Resulting string

  PROCESS_COMMAND: {
      # head1 --> @subsubheading
      $command eq "head1" && do {
          $output .= "\@subsubheading ";
          $output .= $parser->interpolate($paragraph, $line_num) . "\n";
          last PROCESS_COMMAND;
      };

      # head2 --> @strong (like the standard LaTeX classes' \paragraph)
      $command eq "head2" && do {
          my $head2text = $parser->interpolate($paragraph, $line_num);
          $head2text =~ s/^\s+//;
          $head2text =~ s/\s+$//;
          $output .= "\@noindent\n\@strong{$head2text}";
          $output .= "\@ " x 4;
          last PROCESS_COMMAND;
      };

      # over --> prepare to process =item commands.
      $command eq "over" && do {
          push @list_types, "???";
          last PROCESS_COMMAND;
      };

      # item --> produce either @itemize or @table, as appropriate.
      $command eq "item" && do {
          my $item = $parser->interpolate($paragraph, $line_num);
          $item =~ s/\s+$//;

          # Begin a new @itemize/@table.
          croak "=item without =over" if $#list_types==-1;
          if ($list_types[$#list_types] eq "???") {
              if ($item eq "*") {
                  $list_types[$#list_types] = "itemize";
                  $output .= "\@itemize \@bullet\n";
              }
              elsif ($item =~ /^[0-9]/) {
                  $list_types[$#list_types] = "enumerate";
                  $output .= "\@enumerate\n";
              }
              else {
                  $list_types[$#list_types] = "table";
                  $output .= "\@table \@asis\n";
              }
          }

          # Output a new item.
	  my $itemIT = $item;
	  $itemIT =~ s/\@(copts?|coptargs)\{/\@$1IT\{/g;
	  if ($itemIT =~ /coptargs/) {
	      # Put the argument to coptargs inside the coptargs invocation.
	      $itemIT =~ s/\}//;
	      $itemIT .= "}";
	  }
          $output .= ($list_types[$#list_types] =~ /itemize|enumerate/ ?
                      "\@item\n" :
                      "\@item $itemIT\n");
          last PROCESS_COMMAND;
      };

      # back --> end the current @itemize/@table.
      $command eq "back" && do {
          $output .= "\@end $list_types[$#list_types]\n";
          pop @list_types;
          last PROCESS_COMMAND;
      };

      # for --> output the argument verbatim if it applies to texinfo.
      $command eq "for" && do {
          my ($forwhom, $text) = split " ", $parser->interpolate($paragraph, $line_num), 2;
          if ($forwhom eq "texinfo") {
              1 while chomp $text;
              $output .= $text . "\n";
          }
          last PROCESS_COMMAND;
      };

      # Anything else --> abort.
      croak "unknown command \"$command\"";
  }

    # Output the result.
    my $outfile = $parser->output_handle();
    print $outfile $output;
}


# Output verbatim text as a Texinfo @example.
sub verbatim
{
    my ($parser, $paragraph, $line_num) = @_;
    my $body = $parser->interpolate($paragraph, $line_num);
    $body =~ s/\s+$//;
    $body =~ s/\@/\@@/g;
    return if $body eq "";
    my $outfile = $parser->output_handle();
    print $outfile "\@example\n$body\n\@end example\n\n";
}


# Output blocks of text more-or-less as is.
sub textblock
{
    my ($parser, $paragraph, $line_num) = @_;

    my $outfile = $parser->output_handle();
    $paragraph =~ s/[{}]/\@$&/g;   # Must substitute _before_ interpolation.
    my $expanded = $parser->interpolate($paragraph, $line_num);

    $expanded =~ s/coNCePTuaL/\@ncptl{}/g;
    $expanded =~ s/LaTeX/\@latex{}/g;
    $expanded =~ s/\@code\{\"\}/\@CODEDQUOTE/g;
    $expanded =~ s/(?<=[\s\{\(])\"/\`\`/g;
    $expanded =~ s/\"/\'\'/g;
    $expanded =~ s/\@CODEDQUOTE/\@code\{\"\}/g;
    $expanded =~ s/same as ([^\]]+)/same as \@code{$1}/g;
    $expanded =~ s/--/---/g;
    $expanded =~ s/\@copt\{([-\w]+)\}=(\@var\{.*?\})/\@coptargs\{$1, $2\}/g;
    print $outfile $expanded;
}


# Convert interior sequences from POD to Texinfo.
sub interior_sequence
{
    my ($parser, $seq_command, $seq_argument) = @_;

    # Nonbreaking block of text
    $seq_command eq "S" && do {
        return "\@w{$seq_argument}";
    };

    # Code snippet
    $seq_command eq "C" && do {
        my $codestring = $seq_argument;
        $codestring =~ s/\@/\@\@/g;
        $codestring =~ s/[{}]/\@$&/g;
        if ($codestring =~ /^--([-\w]+)$/) {
            return "\@copt{$1}";
        }
        elsif ($codestring =~ /^--([-\w]+)=(.*)$/) {
            my $opt = $1;
            my $args = $2;
            $args =~ s/,/\@comma\{\}/g;
            return "\@coptargs{$opt, $args}";
        }
        elsif ($codestring =~ /^-([A-Za-z])$/) {
            return "\@copts{$1}";
        }
        else {
            return "\@code{$codestring}";
        }
    };

    # Italics -- assume a metasyntactic variable unless it contains an
    # "@", in which case assume an e-mail address.
    $seq_command eq "I" && do {
        if ($seq_argument =~ /\@/) {
            my $address = $seq_argument;
            $address =~ s/\@/\@\@/g;
            return "\@email{$address}";
        }
        else {
            return "\@var{$seq_argument}";
        }
    };

    # File
    $seq_command eq "F" && do {
        return "\@file{$seq_argument}";
    };

    # Bold -- assume a command-line option if beginning with "-", else
    # a program name
    $seq_command eq "B" && do {
        my $argument = $seq_argument;
        if ($argument =~ /^--([-\w]+)$/) {
            return "\@copt{$1}";
        }
        elsif ($argument =~ /^--([-\w]+)=(.*)$/) {
            my $opt = $1;
            my $args = $2;
            $args =~ s/,/\@comma\{\}/g;
            return "\@coptargs{$opt, $args}";
        }
        elsif ($argument =~ /^-([A-Za-z])$/) {
            return "\@copts{$1}";
        }
        else {
            return "\@file{$argument}";
        }
    };

    # Link to another section
    $seq_command eq "L" && do {
        my $linkname = $seq_argument;
        $linkname =~ s|[\"/]||g;
        $linkname = join " ", map {ucfirst lc} split " ", $linkname;
        return "the $linkname section";
    };

    # Named character
    $seq_command eq "E" && do {
        if ($seq_argument eq "lt") {
            return "<";
        }
        elsif ($seq_argument eq "gt") {
            return ">";
        }
        else {
            croak "unknown escape sequence \"$seq_argument\"";
        }
    };

    # Zero-width character
    $seq_command eq "Z" && return "";

    # None of the above
    croak "unknown interior sequence \"$seq_command<$seq_argument>\"";
}

1;
