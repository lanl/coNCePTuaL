/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_time() is at least remotely accurate
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2011, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2011).  Los Alamos National Security, LLC.  This software
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
 * ----------------------------------------------------------------------
 */

#include "ncptl_test.h"

int main (int argc, char *argv[])
{
  uint64_t starttime, stoptime, elapsedtime;
  double timing_error;
  const double error_threshold = 5.0;    /* Allow a 5% error. */
  int i;

  /* Initialize the run-time library. */
  debug_printf ("\tTesting ncptl_time() ...\n");
  ncptl_init (NCPTL_RUN_TIME_VERSION, argv[0]);

  /* Measure what should be about a million microseconds. */
  for (i=3; i>0; i--) {
    starttime = ncptl_time();
    sleep (1);
    stoptime = ncptl_time();
    elapsedtime = stoptime - starttime;

    /* Complain if we're far off. */
    timing_error = 100.0 * fabs (((double)elapsedtime-1.0e+6) / 1.0e+6);
    debug_printf ("\t   Starting time (usecs):  %25llu\n", starttime);
    debug_printf ("\t   Ending time (usecs):    %25llu\n", stoptime);
    debug_printf ("\t   Elapsed time (usecs):   %25llu\n", elapsedtime);
    debug_printf ("\t   Expected value (usecs): %25llu\n", 1000000ULL);
    debug_printf ("\t   Error:                  %27.1lf%%\n", timing_error);
    if (timing_error <= error_threshold)
      RETURN_SUCCESS();
    if (i > 1)
      debug_printf ("\tTrying again ...\n");
    else
      debug_printf ("\tGiving up.\n");
  }

  /* Return successfully. */
  ncptl_finalize();
  argc = 0;        /* Try to avoid "unused parameter" warnings. */
  RETURN_FAILURE();
}
