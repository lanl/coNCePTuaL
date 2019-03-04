/* ----------------------------------------------------------------------
 *
 * Ensure that the various ncptl_log*() functions work
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2003, Triad National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2003).  Triad National Security, LLC.  This software
 * was produced under U.S. Government contract 89233218CNA000001 for
 * Los Alamos National Laboratory (LANL), which is operated by Los
 * Alamos National Security, LLC (Triad) for the U.S. Department
 * of Energy. The U.S. Government has rights to use, reproduce,
 * and distribute this software.  NEITHER THE GOVERNMENT NOR TRIAD
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
 *   * Neither the name of Triad National Security, LLC, Los Alamos
 *     National Laboratory, the U.S. Government, nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY TRIAD AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TRIAD OR CONTRIBUTORS BE
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

/* NOTE: For more stringent testing, run this program with the
 * NCPTL_CHECKPOINT environment variable set to 1. */

#include "ncptl_test.h"

#define BUFFERSIZE 1024    /* Upper bound on VALID_OUTPUT's line length */

int main (int argc, char *argv[])
{
  char *template = "conftest-log-%p.log";
  int tasknum = 123;
  char *filename = "conftest-log-123.log";
  char *valid_output[] = {
    "\"Integers\",\"Summary #1\",\"Summary #2\",\"Summary \\\"1a\\\"\",\"Summary \\\"2a\\\"\",\"Info #1\",\"Info #2\",\"Info #3\",\"Numbers A\",\"Numbers B\",\"Squares\",\"Squares\"\n",
    "\"(all data)\",\"(median)\",\"(mean)\",\"(med. abs. dev.)\",\"(std. dev.)\",\"(median)\",\"(minimum)\",\"(maximum)\",\"(all data)\",\"(median)\",\"(hist. values)\",\"(hist. tallies)\"\n",
    "0,5,5,3,3.31662479,4.5,1,8,-6,0,0,1\n",
    "7,,,,,,,,-5,,1,2\n",
    "3,,,,,,,,-4,,4,2\n",
    "10,,,,,,,,-3,,9,2\n",
    "6,,,,,,,,-2,,16,2\n",
    "2,,,,,,,,-1,,25,2\n",
    "9,,,,,,,,0,,36,2\n",
    "5,,,,,,,,1,,,\n",
    "1,,,,,,,,2,,,\n",
    "8,,,,,,,,3,,,\n",
    "4,,,,,,,,4,,,\n",
    ",,,,,,,,5,,,\n",
    ",,,,,,,,6,,,\n",
    "\n",
    "\"Powers of two\",\"Average\",\"Average\"\n",
    "\"(all data)\",\"(harm. mean)\",\"(geom. mean)\"\n",
    "1,5.004887586,22.627417\n",
    "2,,\n",
    "4,,\n",
    "8,,\n",
    "16,,\n",
    "32,,\n",
    "64,,\n",
    "128,,\n",
    "256,,\n",
    "512,,\n"
  };
  FILE *logfile;
  NCPTL_LOG_FILE_STATE *logstate;
  char *logfile_uuid;
  int i, j;

  /* See if we can tolerate writing an empty log file. */
  debug_printf ("\tTesting the various ncptl_log*() functions ...\n");
  ncptl_init (NCPTL_RUN_TIME_VERSION, argv[0]);
  logstate = ncptl_log_open (template, tasknum);
  ncptl_log_close (logstate);

  /* Reopen the log file. */
  logstate = ncptl_log_open (template, tasknum);

  /* Write some known values that we can later check.  Here, we're
   * testing whether ncptl_log_write() can handle writing to columns
   * out of order and whether it can handle gaps in the numbering. */
  for (i=0; i<11; i++) {
    double somevalue = (double) ((i*7) % 11);

    ncptl_log_write (logstate, 2, "Summary #1", NCPTL_FUNC_MEDIAN, 0.0, somevalue);
    ncptl_log_write (logstate, 3, "Summary #2", NCPTL_FUNC_MEAN, 0.0, somevalue);
    ncptl_log_write (logstate, 5, "Summary \"1a\"", NCPTL_FUNC_MAD, 0.0, somevalue);
    ncptl_log_write (logstate, 6, "Summary \"2a\"", NCPTL_FUNC_STDEV, 0.0, somevalue);
    ncptl_log_write (logstate, 0, "Integers", NCPTL_FUNC_NO_AGGREGATE, 0.0, somevalue);
  }

#ifdef HAVE_NANOSLEEP
  /* Delay for a second to give the checkpointer a chance to run
   * (assuming NCPTL_CHECKPOINT is set to 1). */
  ncptl_udelay (1000000, 1);
#endif

  /* Start a second data set.  Here, we're testing whether new columns
   * can be appended to the right of existing ones. */
  for (i=0; i<8; i++) {
    double somevalue = (double) ((i*3) % 8 + 1);

    ncptl_log_write (logstate, 11, "Info #1", NCPTL_FUNC_MEDIAN, 0.0, somevalue);
    ncptl_log_write (logstate, 12, "Info #2", NCPTL_FUNC_MINIMUM, 0.0, somevalue);
    ncptl_log_write (logstate, 13, "Info #3", NCPTL_FUNC_MAXIMUM, 0.0, somevalue);
  }

#ifdef HAVE_NANOSLEEP
  /* Delay for two seconds to give the checkpointer a chance to run --
   * possibly twice (assuming NCPTL_CHECKPOINT is set to 1). */
  ncptl_udelay (2000000, 1);
#endif

  /* Start a third data set.  Here, we're testing histogramming and
   * also the ability to have two NCPTL_FUNC_NO_AGGREGATEs in the same
   * table. */
  for (i=-6; i<=6; i++) {
    ncptl_log_write (logstate, 14, "Numbers A", NCPTL_FUNC_NO_AGGREGATE, 0.0, (double)i);
    ncptl_log_write (logstate, 15, "Numbers B", NCPTL_FUNC_MEDIAN, 0.0, (double)i);
    ncptl_log_write (logstate, 16, "Squares",   NCPTL_FUNC_HISTOGRAM, 0.0, (double)(i*i));
  }

  /* Write what we have so far to disk. */
  ncptl_log_commit_data (logstate);

#ifdef HAVE_NANOSLEEP
  /* Delay for one second to give the checkpointer a chance to run
   * (assuming NCPTL_CHECKPOINT is set to 1) but find nothing to do. */
  ncptl_udelay (1000000, 1);
#endif

  /* Start a fourth data set.  Here, we're checking whether
   * ncptl_log_commit_data() functions as it's supposed to. */
  for (i=0, j=1; i<10; i++, j<<=1) {
    ncptl_log_write (logstate, 0, "Powers of two", NCPTL_FUNC_NO_AGGREGATE, 0.0, (double)j);
    ncptl_log_write (logstate, 1, "Average", NCPTL_FUNC_HARMONIC_MEAN, 0.0, (double)j);
    ncptl_log_write (logstate, 2, "Average", NCPTL_FUNC_GEOMETRIC_MEAN, 0.0, (double)j);
  }

  /* Flush and close the log file. */
  ncptl_log_close (logstate);

  /* Verify the contents of the log file against VALID_OUTPUT. */
  if (!(logfile=fopen(filename, "r"))) {
    debug_printf ("\t   Unable to open \"%s\" for reading\n", filename);
    RETURN_FAILURE();
  }
  for (i=0; i<(int)(sizeof(valid_output)/sizeof(char *)); i++) {
    char buffer[BUFFERSIZE];
    if (!fgets(buffer, BUFFERSIZE, logfile)) {
      debug_printf ("\t   Unable to read %d bytes from %s\n",
                    BUFFERSIZE, filename);
      RETURN_FAILURE();
    }
    if (strcmp(buffer, valid_output[i])) {
      debug_printf ("\t   Mismatch in line %d of the log file:\n", i+1);
      debug_printf ("\t     CORRECT: %s", valid_output[i]);
      debug_printf ("\t     ACTUAL:  %s", buffer);
      RETURN_FAILURE();
    }
  }
  fclose (logfile);

  /* Ensure that we can write a prologue and epilogue to the log file. */
  logstate = ncptl_log_open (template, tasknum);
  logfile_uuid = ncptl_log_generate_uuid();
  ncptl_log_write_prologue (logstate, "runtime_logfile", logfile_uuid,
                            "N/A", "N/A", tasknum+1, NULL, 0, NULL);
  ncptl_free (logfile_uuid);
  ncptl_log_write_epilogue (logstate);
  ncptl_log_close (logstate);

  /* Delete the log file and exit successfully. */
  unlink (filename);
  ncptl_finalize();
  argc = 0;        /* Try to avoid "unused parameter" warnings. */
  RETURN_SUCCESS();
}
