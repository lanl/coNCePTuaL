/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_func_sqrt() works
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2009, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2009).  Los Alamos National Security, LLC.  This software
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

#define BIGNUM 1048576

int main (void)
{
  ncptl_int i;

  debug_printf ("\tTesting ncptl_func_sqrt() ...\n");
  for (i=0; i<BIGNUM; i++) {
    ncptl_int root2 = ncptl_func_sqrt (i);
    ncptl_int alt_root2 = ncptl_func_root (2, i);

    if (root2*root2 > i) {
      debug_printf ("\t   ncptl_func_sqrt(%" NICS ") --> %" NICS " [too large]\n", i, root2);
      RETURN_FAILURE();
    }
    if ((root2+1)*(root2+1) <= i) {
      debug_printf ("\t   ncptl_func_sqrt(%" NICS ") --> %" NICS " [too small]\n", i, root2);
      RETURN_FAILURE();
    }
    if (root2 != alt_root2) {
      debug_printf ("\t   ncptl_func_sqrt(%" NICS ") --> %" NICS " but ncptl_func_root(2, %" NICS ") --> %" NICS "\n",
                    i, root2, i, alt_root2);
      RETURN_FAILURE();
    }
  }

  RETURN_SUCCESS();
}