/* ----------------------------------------------------------------------
 *
 * Ensure that the various ncptl_set_*() functions work properly
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

#define SETSIZE 7
#define NUMKEYS 2243

int key2value[NUMKEYS];        /* Set from keys to values */


/* Assign an element of key2value[] -- called by ncptl_set_walk(). */
void process_key_value (void *keyptr, void *valueptr)
{
  key2value[*(int *)keyptr] += *(int *)valueptr;
}


int main (void)
{
  NCPTL_SET *intset;           /* Set which maps integers to integers */
  int i, j;

  /* Initialize the set. */
  debug_printf ("\tTesting the various ncptl_set_*() functions ...\n");
  intset = ncptl_set_init (SETSIZE, sizeof(int), sizeof(int));

  /* Perform the test twice to ensure that an intermediate
   * ncptl_set_empty() works. */
  for (i=0; i<2; i++) {
    /* Insert a bunch of key:value pairs into the set in a scrambled
     * order (ensured by the use of relatively prime numbers). */
    for (j=0; j<NUMKEYS; j++) {
      int key = (j*281) % NUMKEYS;
      int value = key*10;
      ncptl_set_insert (intset, (void *)&key, (void *)&value);
    }

    /* Ensure the set contains the correct number of elements. */
    if (ncptl_set_length(intset) != NUMKEYS) {
      debug_printf ("\t   Expected the set to contain %d elements but it instead contains %" NICS " elements\n",
		    NUMKEYS, ncptl_set_length(intset));
      RETURN_FAILURE();
    }

    /* Ensure -- by searching in a scrambled order -- that every key
     * is found. */
    for (j=0; j<NUMKEYS; j++) {
      int key = (j*83) % NUMKEYS;
      int *value = (int *) ncptl_set_find (intset, (void *)&key);
      if (!value) {
	debug_printf ("\t   Failed to find the key \"%d\" in the set\n", key);
	RETURN_FAILURE();
      }
      if (*value != key*10) {
	debug_printf ("\t   Expected \"%d\" to set to \"%d\" but it instead setped to \"%d\"\n", key, key*10, *value);
	RETURN_FAILURE();
      }
    }

    /* Repeat in a different scrambled order. */
    for (j=0; j<NUMKEYS; j++) {
      int key = (j*11261) % NUMKEYS;
      int *value = (int *) ncptl_set_find (intset, (void *)&key);
      if (!value) {
	debug_printf ("\t   Failed to find the key \"%d\" in the set\n", key);
	RETURN_FAILURE();
      }
      if (*value != key*10) {
	debug_printf ("\t   Expected \"%d\" to set to \"%d\" but it instead setped to \"%d\"\n", key, key*10, *value);
	RETURN_FAILURE();
      }
    }

    /* Ensure that walking the set returns every key:value pair exactly once. */
    for (j=0; j<NUMKEYS; j++)
      key2value[j] = 0;
    ncptl_set_walk (intset, process_key_value);
    for (j=0; j<NUMKEYS; j++)
      if (key2value[j] != j*10) {
	debug_printf ("\t   After walking, expected \"%d\" to set to \"%d\" but it instead setped to \"%d\"\n", j, j*10, key2value[j]);
	RETURN_FAILURE();
      }

    /* Remove all of the even-numbered keys. */
    for (j=0; j<NUMKEYS; j++) {
      int key = (j*739) % NUMKEYS;
      if ((key&1) == 0)
	ncptl_set_remove (intset, (void *)&key);
    }

    /* Ensure the set contains the correct number of elements. */
    if (ncptl_set_length(intset) != NUMKEYS/2) {
      debug_printf ("\t   Expected the set to contain %d elements but it instead contains %" NICS " elements\n",
		    NUMKEYS/2, ncptl_set_length(intset));
      RETURN_FAILURE();
    }

    /* Verify that all of the even-numbered keys have been removed. */
    for (j=0; j<NUMKEYS; j++) {
      int key = (j*9007) % NUMKEYS;
      int *value = (int *) ncptl_set_find (intset, (void *)&key);
      if (key&1) {
	/* Odd number -- should still be in the set. */
	if (!value) {
	  debug_printf ("\t   Failed to find the key \"%d\" in the set\n", key);
	  RETURN_FAILURE();
	}
	if (*value != key*10) {
	  debug_printf ("\t   Expected \"%d\" to set to \"%d\" but it instead setped to \"%d\"\n", key, key*10, *value);
	  RETURN_FAILURE();
	}
      }
      else {
	/* Even number -- had better not be in the set. */
	if (value) {
	  debug_printf ("\t   Failed to remove the key \"%d\" from the set\n", key);
	  RETURN_FAILURE();
	}
      }
    }

    /* Wipe clean the entire set. */
    ncptl_set_empty (intset);

    /* Ensure the set contains the correct number of elements. */
    if (ncptl_set_length(intset) != 0) {
      debug_printf ("\t   Expected the set to contain 0 elements but it instead contains %" NICS " elements\n",
		    ncptl_set_length(intset));
      RETURN_FAILURE();
    }
  }
  RETURN_SUCCESS();
}
