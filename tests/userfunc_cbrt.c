/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_func_cbrt() works
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

#include "ncptl_test.h"

#define BIGNUM 262144

int main (void)
{
  ncptl_int i;

  debug_printf ("\tTesting ncptl_func_cbrt() on non-negative integers ...\n");
  for (i=0; i<BIGNUM; i++) {
    ncptl_int root3 = ncptl_func_cbrt (i);
    ncptl_int alt_root3 = ncptl_func_root (3, i);

    if (root3*root3*root3 > i) {
      debug_printf ("\t   ncptl_func_cbrt(%" NICS ") --> %" NICS " [too large]\n", i, root3);
      RETURN_FAILURE();
    }
    if ((root3+1)*(root3+1)*(root3+1) <= i) {
      debug_printf ("\t   ncptl_func_cbrt(%" NICS ") --> %" NICS " [too small]\n", i, root3);
      RETURN_FAILURE();
    }
    if (root3 != alt_root3) {
      debug_printf ("\t   ncptl_func_cbrt(%" NICS ") --> %" NICS " but ncptl_func_root(3, %" NICS ") --> %" NICS "\n",
                    i, root3, i, alt_root3);
      RETURN_FAILURE();
    }
  }

  RETURN_SUCCESS();
}
