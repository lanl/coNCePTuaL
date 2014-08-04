/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_parse_command_line() works
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2014, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2014).  Los Alamos National Security, LLC.  This software
 * was produced under U.S. Government contract DE-AC52-06NA25396
 * for Los Alamos National Laboratory (LANL), which is operated by
 * Los Alamos National Security, LLC (LANS) for the U.S. Department
 * of Energy. The U.S. Government has rights to use, reproduce,
 * and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
 * MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
 * FOR THE USE OF THIS SOFTWARE. If software is modified to produce
 * derivative works, such modified software should be clearly marked,
 * so as not to confuse it with the version available from LANL.
 * 
 * Additionally, redistribution and use in source and binary forms,
 * with or without modification, are permitted provided that the
 * following conditions are met:
 * 
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 * 
 *   * Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer
 *     in the documentation and/or other materials provided with the
 *     distribution.
 * 
 *   * Neither the name of Los Alamos National Security, LLC, Los Alamos
 *     National Laboratory, the U.S. Government, nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 * OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
 * OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
 * BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * 
 *
 * ----------------------------------------------------------------------
 */

#include "ncptl_test.h"

int main (int argc, char *argv[])
{
  char *test_argv[6]; /* Hardwired argv[] for testing. */
  ncptl_int testvar;  /* Variable that ncptl_parse_command_line() should set */
  char *stringvar;    /* A string variable for ncptl_parse_command_line() */
  NCPTL_CMDLINE arglist[] = {    /* Arguments to test. */
    { NCPTL_TYPE_INT,
      NULL,
      "testing",
      't',
      "Test of ncptl_parse_command_line()",
      {0}
    },
    { NCPTL_TYPE_STRING,
      NULL,
      "somestring",
      's',
      "Another test of ncptl_parse_command_line()",
      {0}
    }
  };

  /* Initialize the run-time library and the ARGLIST array. */
  debug_printf ("\tTesting ncptl_parse_command_line() ...\n");
  ncptl_fast_init = 1;    /* We don't need accurate timing for this test. */
  ncptl_init (NCPTL_RUN_TIME_VERSION, argv[0]);
  arglist[0].variable = (CMDLINE_VALUE *) &testvar;
  arglist[0].defaultvalue.intval = 123;
  arglist[1].variable = (CMDLINE_VALUE *) &stringvar;
  arglist[1].defaultvalue.stringval = "abc123";

  /* Ensure that testvar receives its default value when given an
   * empty command line. */
  test_argv[0] = argv[0];
  test_argv[1] = NULL;
  testvar = 999;
  stringvar = "xxx999";
  ncptl_parse_command_line(1, test_argv, arglist, 2);
  debug_printf ("\tExpected 123;      got %" NICS ".\n", testvar);
  debug_printf ("\tExpected \"abc123\"; got \"%s\".\n", stringvar);
  if (testvar != 123)
    RETURN_FAILURE();
  if (strcmp (stringvar, "abc123"))
    RETURN_FAILURE();

  /* Ensure that short arguments work. */
  test_argv[1] = "-t";
  test_argv[2] = "456";
  test_argv[3] = "-s";
  test_argv[4] = "def456";
  test_argv[5] = NULL;
  testvar = 999;
  stringvar = "xxx999";
  ncptl_parse_command_line(5, test_argv, arglist, 2);
  debug_printf ("\tExpected 456;      got %" NICS ".\n", testvar);
  debug_printf ("\tExpected \"def456\"; got \"%s\".\n", stringvar);
  if (testvar != 456)
    RETURN_FAILURE();
  if (strcmp (stringvar, "def456"))
    RETURN_FAILURE();

  /* Ensure that long arguments work. */
#if defined(USE_POPT) || defined(USE_GETOPT_LONG)
  test_argv[1] = "--testing";
  test_argv[2] = "789";
  test_argv[3] = "--somestring";
  test_argv[4] = "ghi789";
  test_argv[5] = NULL;
  testvar = 999;
  stringvar = "xxx999";
  ncptl_parse_command_line(5, test_argv, arglist, 2);
  debug_printf ("\tExpected 789;      got %" NICS ".\n", testvar);
  debug_printf ("\tExpected \"ghi789\"; got \"%s\".\n", stringvar);
  if (testvar != 789)
    RETURN_FAILURE();
  if (strcmp (stringvar, "ghi789"))
    RETURN_FAILURE();
#endif

  /* Ensure that suffixed arguments work. */
  test_argv[1] = "-t";
  test_argv[2] = "1011e+2";
  test_argv[3] = NULL;
  testvar = 999;
  ncptl_parse_command_line(3, test_argv, arglist, 2);
  debug_printf ("\tExpected 101100;      got %" NICS ".\n", testvar);
  if (testvar != 101100)
    RETURN_FAILURE();

  /* Return successfully. */
  ncptl_finalize();
  argc = 0;        /* Try to avoid "unused parameter" warnings. */
  RETURN_SUCCESS();
}
