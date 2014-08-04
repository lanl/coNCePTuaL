/* ----------------------------------------------------------------------
 *
 * Manually verify that the coNCePTuaL run-time library's ncptl_time()
 * routine has some relation to reality.
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

#include <stdio.h>
#include <ncptl.h>     /* We expect to be built from the source directory. */

int
main (int argc, char *argv[])
{
  ncptl_int starttime, stoptime;    /* coNCePTuaL's view of time */
  volatile int onechar;             /* Dummy character read from the user */
  int wallclocktime = 60;           /* Seconds of wall-clock time */

  /* Initialize coNCePTuaL and the desired wall-clock time. */
  ncptl_init (NCPTL_RUN_TIME_VERSION, argv[0]);
  if (argc > 1)
    wallclocktime = atoi(argv[1]);
  if (wallclocktime < 1)
    ncptl_fatal ("You must specify at least one second of delay");

  /* Provide instructions to the user. */
  printf ("Press <Enter> to start the clock ...");
  fflush (stdout);
  onechar = getchar();
  printf ("Press <Enter> again in exactly %d seconds ...", wallclocktime);
  fflush (stdout);

  /* Measure elapsed time and report the results. */
  starttime = ncptl_time();
  onechar = getchar();
  stoptime = ncptl_time();
  printf ("\n");
  printf ("coNCePTuaL measured %f seconds.\n", (stoptime-starttime)/1.0e6);
  printf ("coNCePTuaL timer error = %f%%\n",
	  100.0 * (stoptime-starttime-1.0e6*wallclocktime) / (1.0e6*wallclocktime));

  return 0;
}
