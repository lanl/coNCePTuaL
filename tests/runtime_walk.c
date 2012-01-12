/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_walk_memory() works (more precisely, doesn't crash)
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

#define ACCESSES 1000000

/* Deal with systems that can't malloc() a zero-byte buffer. */
#ifdef HAVE_MALLOC
# define malloc0 malloc
#else
# define malloc0(S) malloc((S) ? (S) : sizeof(int))
#endif


/* Return the OS page size.  If we don't know what it is, return 64K. */
int find_page_size (void)
{
  int result = 0;

#ifdef OS_PAGE_SIZE
  return OS_PAGE_SIZE;
#endif

#if defined(HAVE_GETPAGESIZE)
  result = result<1 ? getpagesize() : result;
#endif
#if defined(HAVE_SYSCONF) && defined(_SC_PAGESIZE)
  result = result<1 ? sysconf(_SC_PAGESIZE) : result;
#endif
#if defined(HAVE_SYSCONF) && defined(_SC_PAGE_SIZE)
  result = result<1 ? sysconf(_SC_PAGE_SIZE) : result;
#endif
  result = result<1 ? 65536 : result;
  return result;
}


int main (void)
{
  void *buffer = ncptl_malloc (16777216, find_page_size());
  ncptl_int sizetrials[] = {4, 8, 4096, 8192, 16777216, 9973, 3989, 163, 3};
  ncptl_int stridetrials[] = {0, 4, 8, 4096, 8192, 16777216, 9973, 3989, 163, 3, 4095, NCPTL_INT_MIN};
  unsigned int i;          /* Index into sizetrials[] */
  unsigned int j;          /* Index into stridetrials[] */
  ncptl_int k;             /* Bytes per word (1, 2, 4, ..., 64) */
  ncptl_int m;             /* Byte offset at which to start touching data */

  for (i=0; i<sizeof(sizetrials)/sizeof(ncptl_int); i++)
    for (j=0; j<sizeof(stridetrials)/sizeof(ncptl_int); j++) {
      ncptl_int effective_stride = stridetrials[j] ? stridetrials[j]%sizetrials[i] : 0;

      if (effective_stride%CPU_MINIMUM_ALIGNMENT_BYTES == 0)
	for (k=1; k<=64; k*=2) {
	  /* Try to avoid misalignment problems.  If
           * CPU_MINIMUM_ALIGNMENT_BYTES is 1, we assume that
           * misalignment isn't fatal.  Otherwise, if the word size is
           * greater than 16, we know that ncptl_touch_memory() will
           * touch memory word-by-word so word-alignment is okay.
           * Otherwise, if the word size evenly divides the stride
           * then there's no problem.  Otherwise, we skip the test
           * rather than risk dying from a misalignment error. */
	  if (!(CPU_MINIMUM_ALIGNMENT_BYTES == 1
		|| k > 16
		|| effective_stride%k == 0))
	    continue;

	  /* Repeat the test using a variety of initial byte offsets. */
          for (m=0; m<3*k; m+=k)
            if (m+k < sizetrials[i]
                && sizetrials[i] >= k
                && (!effective_stride
                    || (sizetrials[i]-m)%effective_stride == 0)) {
              debug_printf ("\tAccessing a %" NICS "-byte region from offset %" NICS " bytes with stride %" NICS " bytes (%" NICS " bytes/word) ...\n",
                            sizetrials[i], m, stridetrials[j], k);
              ncptl_touch_memory (buffer, sizetrials[i], k, m, ACCESSES, stridetrials[j]);
            }
	}
    }

  RETURN_SUCCESS();
}
