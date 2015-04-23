/* ----------------------------------------------------------------------
 *
 * Ensure that the various ncptl_queue_*() functions work properly
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

#define QUEUESIZE 991
#define SOMEPRIME 457

int main (void)
{
  NCPTL_QUEUE *intqueue;       /* Queue of integers */
  int *queuedata;              /* Contents of INTQUEUE */
  ncptl_int queuedatalen;      /* Length of INTQUEUE */
  int somevalue;               /* Value to push/pop from the queue */
  int prevvalue = -1;          /* Previous value of SOMEVALUE */
  int prevprevvalue = -1;      /* Previous value of PREVVALUE */
  int *lastvalues[2];          /* Pointer to last two values pushed onto INTQUEUE */
  int i, j;

  /* Initialize the queue. */
  debug_printf ("\tTesting the various ncptl_queue_*() functions ...\n");
  intqueue = ncptl_queue_init (sizeof(int));

  /* Perform the test twice to ensure that an intermediate
   * ncptl_queue_empty() works. */
  for (j=0; j<2; j++) {
    /* Push a bunch of unique values (ensured by the relative
     * primeness of QUEUESIZE AND SOMEPRIME). */
    for (i=0, somevalue=0;
	 i<QUEUESIZE;
	 i++, somevalue=(somevalue+SOMEPRIME)%QUEUESIZE) {
      if (somevalue)
	ncptl_queue_push (intqueue, (void *) &somevalue);
      else
	*(int *) ncptl_queue_allocate (intqueue) = somevalue;
      prevprevvalue = prevvalue;
      prevvalue = somevalue;
    }

    /* Pop and re-push the last two values. */
    lastvalues[0] = ncptl_queue_pop_tail (intqueue);
    if (*lastvalues[0] != prevvalue)
      debug_printf ("\t   Expected the final queue entry to contain %d but it actually contains %d\n",
		    prevvalue, *lastvalues[0]);
    lastvalues[1] = ncptl_queue_pop_tail (intqueue);
    if (*lastvalues[1] != prevprevvalue)
      debug_printf ("\t   Expected the penultimate queue entry to contain %d but it actually contains %d\n",
		    prevprevvalue, *lastvalues[1]);
    ncptl_queue_push(intqueue, (void *) lastvalues[1]);
    *(int *) ncptl_queue_allocate (intqueue) = *lastvalues[0];

    /* Verify the queue length. */
    queuedatalen = ncptl_queue_length (intqueue);
    if (queuedatalen != QUEUESIZE) {
      debug_printf ("\t   Expected the queue to contain %d elements but it actually contains %" NICS " elements\n",
		    QUEUESIZE, queuedatalen);
      RETURN_FAILURE();
    }

    /* Verify the queue contents using ncptl_queue_contents(). */
    queuedata = (int *) ncptl_queue_contents (intqueue, j);  /* Don't copy, then copy. */
    for (i=0, somevalue=0;
	 i<QUEUESIZE;
	 i++, somevalue=(somevalue+SOMEPRIME)%QUEUESIZE)
      if (queuedata[i] != somevalue) {
	debug_printf ("\t   Expected intqueue[%d] to contain %d but it actually contains %d\n",
		      i, somevalue, queuedata[i]);
	RETURN_FAILURE();
      }

    /* Verify the queue contents using ncptl_queue_pop(). */
    for (i=0, somevalue=0;
	 i<QUEUESIZE;
	 i++, somevalue=(somevalue+SOMEPRIME)%QUEUESIZE) {
      int queuevalue = *(int *)ncptl_queue_pop (intqueue);
      if (queuevalue != somevalue) {
	debug_printf ("\t   Expected intqueue[%d] to contain %d but it actually contains %d\n",
		      i, somevalue, queuevalue);
	RETURN_FAILURE();
      }
    }

    /* Empty the queue before the next iteration. */
    ncptl_queue_empty (intqueue);
  }
  RETURN_SUCCESS();
}
