/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_malloc(), ncptl_malloc_message(),
 * ncptl_touch_data(), and ncptl_free() work
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2012, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2012).  Los Alamos National Security, LLC.  This software
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

#define REPETITIONS 100
#define RECYCLING 3

int main (int argc, char *argv[])
{
  void *buffer[REPETITIONS];
  int sizetrials[] = {0, 4, 8, 4096, 8192, 65536, 9973, 3989, 163, 3};
  int aligntrials[] = {0, 4096, 512, 8, 4, 48, 37, 3};
  unsigned int i, j, k;
  int m;

  /* Initialize the run-time library. */
  ncptl_fast_init = 1;    /* We don't need accurate timing for this test. */
  ncptl_init (NCPTL_RUN_TIME_VERSION, argv[0]);

  /* Perform a bunch of memory allocations using ncptl_malloc() and
   * ncptl_malloc_misaligned(). */
  for (m=0; m<=1; m++)
    for (k=0; k<sizeof(aligntrials)/sizeof(int); k++) {
      if (aligntrials[k] % CPU_MINIMUM_ALIGNMENT_BYTES)
	continue;
      for (j=0; j<sizeof(sizetrials)/sizeof(int); j++) {
	debug_printf ("\tTesting ncptl_malloc%s (%d, %d) ...\n",
		      m ? "_misaligned" : "", sizetrials[j], aligntrials[k]);
	for (i=0; i<REPETITIONS; i++) {
	  /* Allocate memory. */
	  buffer[i] = (m 
		       ? ncptl_malloc_misaligned (sizetrials[j], aligntrials[k])
		       : ncptl_malloc (sizetrials[j], aligntrials[k]));
	  if (m) {
	    if ((unsigned long)buffer[i]%ncptl_pagesize != (unsigned long)aligntrials[k]%ncptl_pagesize) {
	      debug_printf ("\t   %p --> %lu   (incorrect alignment)\n",
			    buffer[i], (unsigned long)buffer[i] % ncptl_pagesize);
	      RETURN_FAILURE();
	    }
	  }
	  else
	    if (aligntrials[k] && (unsigned long)buffer[i] % aligntrials[k]) {
	      debug_printf ("\t   %p --> %lX   (incorrect alignment)\n",
			    buffer[i], (unsigned long)buffer[i] % aligntrials[k]);
	      RETURN_FAILURE();
	    }

	  /* Ensure the memory is valid. */
	  ncptl_touch_data (buffer[i], sizetrials[j]);

	  /* Realloc the memory (not when ncptl_malloc_misaligned()
	   * was used, as there's not yet a corresponding
	   * ncptl_realloc_misaligned()). */
	  if (m==0 && sizetrials[j]>=2*(int)sizeof(double) && !(aligntrials[k]%sizeof(double))) {
	    double sentinel = (double)i + j + k;

	    if (!i)
	      debug_printf ("\tTesting ncptl_realloc (%d, %d) ...\n",
			    sizetrials[j], aligntrials[k]);
	    *((double *)buffer[i]) = sentinel;

	    /* Test a decrease in buffer size. */
	    buffer[i] = ncptl_realloc (buffer[i], sizetrials[j]/2, aligntrials[k]);
	    if (aligntrials[k] && (unsigned long)buffer[i] % aligntrials[k]) {
	      debug_printf ("\t   %p --> %lX   (incorrect alignment)\n",
			    buffer[i], (unsigned long)buffer[i] % aligntrials[k]);
	      RETURN_FAILURE();
	    }
	    if (*((double *)buffer[i]) != sentinel) {
	      debug_printf ("\t   Expected %lf at position 0 but saw %lf\n",
			    sentinel, *((double *)buffer[i]));
	      RETURN_FAILURE();
	    }

	    /* Test an increase in buffer size. */
	    buffer[i] = ncptl_realloc (buffer[i], sizetrials[j]*8, aligntrials[k]);
	    if (aligntrials[k] && (unsigned long)buffer[i] % aligntrials[k]) {
	      debug_printf ("\t   %p --> %lX   (incorrect alignment)\n",
			    buffer[i], (unsigned long)buffer[i] % aligntrials[k]);
	      RETURN_FAILURE();
	    }
	    if (*((double *)buffer[i]) != sentinel) {
	      debug_printf ("\t   Expected %lf at position 0 but saw %lf\n",
			    sentinel, *((double *)buffer[i]));
	      RETURN_FAILURE();
	    }
	  }
	}
	for (i=0; i<REPETITIONS; i++)
	  ncptl_free (buffer[i]);
      }
    }

  /* Now perform a bunch of memory allocations using
   * ncptl_malloc_message(). */
  for (m=0; m<=1; m++)
    for (k=0; k<sizeof(aligntrials)/sizeof(int); k++) {
      if (aligntrials[k] % CPU_MINIMUM_ALIGNMENT_BYTES)
	continue;
      for (j=0; j<sizeof(sizetrials)/sizeof(int); j++) {
	debug_printf ("\tTesting ncptl_malloc_message (%d, %d, [0-%d], %d) ...\n",
		      sizetrials[j], aligntrials[k], RECYCLING-1, m);
	for (i=0; i<REPETITIONS; i++) {
	  buffer[i] = ncptl_malloc_message (sizetrials[j], aligntrials[k], i%RECYCLING, m);
	  if (i>=RECYCLING && buffer[i-RECYCLING]!=buffer[i]) {
	    debug_printf ("\t   buffer[%d]=%p != buffer[%d]=%p   (no recycling)\n",
			  i-RECYCLING, buffer[i-RECYCLING],
			  i, buffer[i]);
	    RETURN_FAILURE();
	  }
	  if (i && buffer[i-1]==buffer[i]) {
	    debug_printf ("\t   buffer[%d] = buffer[%d] = %p   (too much recycling)\n",
			  i-1, i, buffer[i]);
	    RETURN_FAILURE();
	  }
	  if (m) {
	    /* Specific offset from a page boundary */
	    if ((unsigned long)buffer[i]%ncptl_pagesize != (unsigned long)aligntrials[k]%ncptl_pagesize) {
	      debug_printf ("\t   %p --> %lu   (incorrect alignment)\n",
			    buffer[i], (unsigned long)buffer[i] % ncptl_pagesize);
	      RETURN_FAILURE();
	    }
	  }
	  else
	    /* Specific alignment in absolute terms */
	    if (aligntrials[k] && (unsigned long)buffer[i] % aligntrials[k]) {
	      debug_printf ("\t   %p --> %lu   (incorrect alignment)\n",
			    buffer[i], (unsigned long)buffer[i] % aligntrials[k]);
	      RETURN_FAILURE();
	    }
	  ncptl_touch_data (buffer[i], sizetrials[j]);
	}
      }
    }

  /* Return successfully. */
  ncptl_finalize();
  argc = 0;        /* Try to avoid "unused parameter" warnings. */
  RETURN_SUCCESS();
}
