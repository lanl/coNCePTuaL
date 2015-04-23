/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_func_file_data() works
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2015, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2015).  Los Alamos National Security, LLC.  This software
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

#define NUM_ROWS 18
#define NUM_COLS 5
#define CHAR_AT(R, C) ('!' + (R)*NUM_COLS + (C))

/* Create a test file containing a bunch of rows and columns. */
static char *create_test_file (char *colsep, char *rowsep)
{
  char *testfilename;
  FILE *testfile;
  ncptl_int i, j, k;

  testfilename = tmpnam (NULL);
  testfile = fopen (testfilename, "w");
  if (!testfile)
    return NULL;
  for (i = 0; i < NUM_ROWS; i++)
    for (j = 0; j < NUM_COLS; j++) {
      for (k = 0; k < 3; k++)
	fputc (CHAR_AT(i, j), testfile);
      fprintf (testfile, "%s", j < NUM_COLS - 1 ? colsep : rowsep);
    }
  fclose (testfile);
  return testfilename;
}


/* Ensure that a given position contains what we expect it to. */
static int test_col_row (const char *testfilename, ncptl_int col, ncptl_int row, 
			 const char *colsep, const char *rowsep, ncptl_int expected)
{
  ncptl_int value;

  value = ncptl_func_file_data (testfilename, col, row, colsep, rowsep);
  debug_printf ("\t   ncptl_func_file_data(_, %" NICS ", %" NICS ", \" \", \"\\n\") --> %" NICS,
		col, row, value);
  if (value != expected) {
    debug_printf (" (should be %" NICS ")\n", expected);
    return 0;
  }
  debug_printf ("\n");
  return 1;
}

int main (void)
{
  char *testfilename;
  char *colsep = " ";
  char *rowsep = "\n";

  /* Create a file for testing ncptl_func_file_data(). */
  debug_printf ("\tTesting ncptl_func_file_data() ...\n");
  testfilename = create_test_file (colsep, rowsep);
  if (!testfilename)
    RETURN_FAILURE();

  /* Test various combinations of positive and negative rows and columns. */
  if (!test_col_row (testfilename, 3, 4, colsep, rowsep, 222))
    RETURN_FAILURE();
  if (!test_col_row (testfilename, -2, 5, colsep, rowsep, 888))
    RETURN_FAILURE();
  if (!test_col_row (testfilename, 5, -15, colsep, rowsep, 444))
    RETURN_FAILURE();
  if (!test_col_row (testfilename, -4, -14, colsep, rowsep, 666))
    RETURN_FAILURE();

  /* Clean up and exit. */
  unlink (testfilename);
  RETURN_SUCCESS();
}
