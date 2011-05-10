/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_verify() works
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
  void *buffer;
  unsigned long biterrors;
  unsigned int sizetrials[] = {0, 4, 8, 4096, 8192, 65536, 9973, 3989, 163, 3};
  int aligntrials[] = {0, 4096, 512, 8, 4, 48, 37, 3};
  unsigned int j, k;

  /* Initialize the run-time library. */
  ncptl_fast_init = 1;    /* We don't need accurate timing for this test. */
  ncptl_init (NCPTL_RUN_TIME_VERSION, argv[0]);

  /* Perform a bunch of memory allocations and verify the results. */
  for (k=0; k<sizeof(aligntrials)/sizeof(int); k++) {
    if (aligntrials[k] % CPU_MINIMUM_ALIGNMENT_BYTES)
      continue;
    for (j=0; j<sizeof(sizetrials)/sizeof(int); j++) {
      debug_printf ("\tTesting and validating ncptl_malloc (%d, %d) ...\n",
		    sizetrials[j], aligntrials[k]);
      buffer = ncptl_malloc (sizetrials[j], aligntrials[k]);
      ncptl_fill_buffer (buffer, sizetrials[j], 1);
      biterrors = ncptl_verify (buffer, sizetrials[j]);
      if (biterrors) {
	debug_printf ("\t   %lu bit errors\n", biterrors);
	RETURN_FAILURE();
      }
      ncptl_free (buffer);
    }
  }

  /* Repeat the experiments with bit errors expected (i.e., VERIFY=-1). */
  for (k=0; k<sizeof(aligntrials)/sizeof(int); k++) {
    if (aligntrials[k] % CPU_MINIMUM_ALIGNMENT_BYTES)
      continue;
    for (j=0; j<sizeof(sizetrials)/sizeof(int); j++) {
      debug_printf ("\tTesting and validating ncptl_malloc (%d, %d) with errors expected ...\n",
		    sizetrials[j], aligntrials[k]);
      buffer = ncptl_malloc (sizetrials[j], aligntrials[k]);
      ncptl_fill_buffer (buffer, sizetrials[j], -1);
      biterrors = ncptl_verify (buffer, sizetrials[j]);
      if (sizetrials[j]>=2*sizeof(unsigned long) && !biterrors) {
	debug_printf ("\t   0 bit errors\n");
	RETURN_FAILURE();
      }
      ncptl_free (buffer);
    }
  }

  /* Return successfully. */
  ncptl_finalize();
  argc = 0;        /* Try to avoid "unused parameter" warnings. */
  RETURN_SUCCESS();
}
