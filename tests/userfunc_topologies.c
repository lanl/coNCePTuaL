/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_func_tree_parent(), ncptl_func_tree_child(),
 * ncptl_func_mesh_neighbor(), ncptl_func_mesh_coord(),
 * ncptl_func_knomial_parent(), and ncptl_func_knomial_child() all
 * work
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

#define GRIDWIDTH  4
#define GRIDHEIGHT 2
#define GRIDDEPTH  3

int main (void)
{
  ncptl_int parent2[] = {        /* Map to parent in a 2-ary tree */
    -1,
    0, 0,
    1, 1,
    2, 2,
    3, 3,
    4, 4,
    5, 5,
    6, 6
  };
  ncptl_int parent3[] = {        /* Map to parent in a 3-ary tree */
    -1,
    0, 0, 0,
    1, 1, 1,
    2, 2, 2,
    3, 3, 3,
    4, 4, 4,
    5, 5, 5,
    6, 6, 6
  };
  ncptl_int child2[][2] = {      /* Map to children in a 2-ary tree */
    { 1,  2},
    { 3,  4},
    { 5,  6},
    { 7,  8},
    { 9, 10},
    {11, 12},
    {13, 14}
  };
  ncptl_int child3[][3] = {      /* Map to children in a 3-ary tree */
    { 1,  2,  3},
    { 4,  5,  6},
    { 7,  8,  9},
    {10, 11, 12}
  };
  ncptl_int mesh_neighbor_pos[] = {   /* Map to {+x, +y, +z} neighbor in a 4x3x2 mesh */
    17, 18, 19, -1,
    21, 22, 23, -1,
    -1, -1, -1, -1,
    -1, -1, -1, -1,
    -1, -1, -1, -1,
    -1, -1, -1, -1
  };
  ncptl_int torus_neighbor_pos[] = {  /* Map to {+x, +y, +z} neighbor in a 4x3x2 torus */
    17, 18, 19, 16,
    21, 22, 23, 20,
    13, 14, 15, 12,
     5,  6,  7,  4,
     9, 10, 11,  8,
     1,  2,  3,  0
  };
  ncptl_int partial_torus_neighbor_pos[] = {  /* Map to {+x, +y, +z} neighbor in a 4x3x2 mesh that wraps in y only */
    17, 18, 19, -1,
    21, 22, 23, -1,
    13, 14, 15, -1,
    -1, -1, -1, -1,
    -1, -1, -1, -1,
    -1, -1, -1, -1
  };
  ncptl_int parent2k[] = {      /* Map to parent in a 2-nomial tree */
    -1, 0,  0, 1,
     0, 1,  2, 3
  };
  ncptl_int parent3k[] = {      /* Map to parent in a 3-nomial tree */
    -1,  0,  0,   0,  1,  2,   0,  1,  2,
     0,  1,  2,   3,  4,  5,   6,  7,  8,
     0,  1,  2,   3,  4,  5,   6,  7,  8
  };
  ncptl_int child2k[][3] = {    /* Map to children in a 2-nomial tree */
    { 1,  2,  4},
    { 3,  5, -1},
    { 6, -1, -1},
    { 7, -1, -1},
    {-1, -1, -1},
    {-1, -1, -1},
    {-1, -1, -1},
    {-1, -1, -1}
  };
  ncptl_int child3k[][6] = {    /* Map to children in a 3-nomial tree */
    { 1,  2,  3,   6,  9, 18},
    { 4,  7, 10,  19, -1, -1},
    { 5,  8, 11,  20, -1, -1},

    {12, 21, -1,  -1, -1, -1},
    {13, 22, -1,  -1, -1, -1},
    {14, 23, -1,  -1, -1, -1},

    {15, 24, -1,  -1, -1, -1},
    {16, 25, -1,  -1, -1, -1},
    {17, 26, -1,  -1, -1, -1},

    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},

    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},

    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},

    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},

    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},

    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1},
    {-1, -1, -1,  -1, -1, -1}
  };
  ncptl_int knomial_sizes[3];   /* Three different tree sizes to try */
  ncptl_int i, j, k;
  ncptl_int x, y, z;

  /* Test ncptl_func_tree_parent(). */
  debug_printf ("\tTesting ncptl_func_tree_parent() ...\n");
  for (i=0; i<(ncptl_int)(sizeof(parent2)/sizeof(ncptl_int)); i++) {
    debug_printf ("\t   ncptl_func_tree_parent (%" NICS ", 2) --> %" NICS,
                  i, ncptl_func_tree_parent(i, 2));
    if (ncptl_func_tree_parent(i, 2) != parent2[i]) {
      debug_printf (" (should be %" NICS ")\n", parent2[i]);
      RETURN_FAILURE();
    }
    else
      debug_printf ("\n");
  }
  for (i=0; i<(ncptl_int)(sizeof(parent3)/sizeof(ncptl_int)); i++) {
    debug_printf ("\t   ncptl_func_tree_parent (%" NICS ", 3) --> %" NICS,
                  i, ncptl_func_tree_parent(i, 3));
    if (ncptl_func_tree_parent(i, 3) != parent3[i]) {
      debug_printf (" (should be %" NICS ")\n", parent3[i]);
      RETURN_FAILURE();
    }
    else
      debug_printf ("\n");
  }
  debug_printf ("\n");

  /* Test ncptl_func_tree_child(). */
  debug_printf ("\tTesting ncptl_func_tree_child() ...\n");
  for (i=0; i<(ncptl_int)(sizeof(child2)/(2*sizeof(ncptl_int))); i++)
    for (j=0; j<2; j++) {
      debug_printf ("\t   ncptl_func_tree_child (%" NICS ", %" NICS ", 2) --> %" NICS,
                    i, j, ncptl_func_tree_child(i, j, 2));
      if (ncptl_func_tree_child(i, j, 2) != child2[i][j]) {
        debug_printf (" (should be %" NICS ")\n", child2[i][j]);
        RETURN_FAILURE();
      }
      else
        debug_printf ("\n");
    }
  for (i=0; i<(ncptl_int)(sizeof(child3)/(3*sizeof(ncptl_int))); i++)
    for (j=0; j<3; j++) {
      debug_printf ("\t   ncptl_func_tree_child (%" NICS ", %" NICS ", 3) --> %" NICS,
                    i, j, ncptl_func_tree_child(i, j, 3));
      if (ncptl_func_tree_child(i, j, 3) != child3[i][j]) {
        debug_printf (" (should be %" NICS ")\n", child3[i][j]);
        RETURN_FAILURE();
      }
      else
        debug_printf ("\n");
    }
  debug_printf ("\n");

  /* Test ncptl_func_mesh_neighbor(). */
  debug_printf ("\tTesting ncptl_func_mesh_neighbor() ...\n");
  for (i=0; i<(ncptl_int)(sizeof(mesh_neighbor_pos)/sizeof(ncptl_int)); i++) {
    ncptl_int neighbor = ncptl_func_mesh_neighbor (4, 3, 2,
                                                   0, 0, 0,
                                                   i,
                                                   +1, +1, +1);
    debug_printf ("\t   ncptl_func_mesh_neighbor (4, 3, 2, 0, 0, 0, %2" NICS
                  ", +1, +1, +1) --> %3" NICS,
                  i, neighbor);
    if (mesh_neighbor_pos[i] != neighbor) {
      debug_printf (" (should be %" NICS ")\n", mesh_neighbor_pos[i]);
      RETURN_FAILURE();
    }
    else
      debug_printf ("\n");
  }
  for (i=0; i<(ncptl_int)(sizeof(torus_neighbor_pos)/sizeof(ncptl_int)); i++) {
    ncptl_int neighbor = ncptl_func_mesh_neighbor (4, 3, 2,
                                                   1, 1, 1,
                                                   i,
                                                   +1, +1, +1);
    debug_printf ("\t   ncptl_func_mesh_neighbor (4, 3, 2, 1, 1, 1, %2" NICS
                  ", +1, +1, +1) --> %3" NICS,
                  i, neighbor);
    if (torus_neighbor_pos[i] != neighbor) {
      debug_printf (" (should be %" NICS ")\n", torus_neighbor_pos[i]);
      RETURN_FAILURE();
    }
    else
      debug_printf ("\n");
  }
  for (i=0; i<(ncptl_int)(sizeof(partial_torus_neighbor_pos)/sizeof(ncptl_int)); i++) {
    ncptl_int neighbor = ncptl_func_mesh_neighbor (4, 3, 2,
                                                   0, 1, 0,
                                                   i,
                                                   +1, +1, +1);
    debug_printf ("\t   ncptl_func_mesh_neighbor (4, 3, 2, 0, 1, 0, %2" NICS
                  ", +1, +1, +1) --> %3" NICS,
                  i, neighbor);
    if (partial_torus_neighbor_pos[i] != neighbor) {
      debug_printf (" (should be %" NICS ")\n", partial_torus_neighbor_pos[i]);
      RETURN_FAILURE();
    }
    else
      debug_printf ("\n");
  }
  debug_printf ("\n");

  /* Test ncptl_func_mesh_coord(). */
  debug_printf ("\tTesting ncptl_func_mesh_coord() ...\n");
  for (z=0; z<GRIDDEPTH; z++)
    for (y=0; y<GRIDHEIGHT; y++)
      for (x=0; x<GRIDWIDTH; x++) {
        ncptl_int taskID = x + GRIDWIDTH*(y + GRIDHEIGHT*z);
        ncptl_int coords[3];

        for (i=0; i<3; i++)
          coords[i] =
            ncptl_func_mesh_coord (GRIDWIDTH, GRIDHEIGHT, GRIDDEPTH, taskID, i);
        debug_printf ("\t   ncptl_func_mesh_coord (%d, %d, %d, %2" NICS
                      ", {0,1,2}) --> {%" NICS ",%" NICS ",%" NICS "}",
                      GRIDWIDTH, GRIDHEIGHT, GRIDDEPTH, taskID,
                      coords[0], coords[1], coords[2]);
        if (x!=coords[0] || y!=coords[1] || z!=coords[2]) {
          debug_printf (" (should be {%" NICS ",%" NICS ",%" NICS "})\n",
                        x, y, z);
          RETURN_FAILURE();
        }
        debug_printf ("\n");
      }
  debug_printf ("\n");

  /* Test ncptl_func_mesh_distance(). */
  debug_printf ("\tTesting ncptl_func_mesh_distance() ...\n");
  for (z=0; z<GRIDDEPTH; z++)
    for (y=0; y<GRIDHEIGHT; y++)
      for (x=0; x<GRIDWIDTH; x++) {
        ncptl_int taskID_1 = x + GRIDWIDTH*(y + GRIDHEIGHT*z);
        ncptl_int xdelta, ydelta, zdelta;

        for (zdelta=0; zdelta<GRIDDEPTH; zdelta++)
          for (ydelta=0; ydelta<GRIDHEIGHT; ydelta++)
            for (xdelta=0; xdelta<GRIDWIDTH; xdelta++) {
              ncptl_int newz = (z + zdelta) % GRIDDEPTH;
              ncptl_int newy = (y + ydelta) % GRIDHEIGHT;
              ncptl_int newx = (x + xdelta) % GRIDWIDTH;
              ncptl_int abs_xdelta = (x <= newx) ? xdelta : GRIDWIDTH - xdelta;
              ncptl_int abs_ydelta = (y <= newy) ? ydelta : GRIDHEIGHT - ydelta;
              ncptl_int abs_zdelta = (z <= newz) ? zdelta : GRIDDEPTH - zdelta;
              ncptl_int taskID_2 = newx + GRIDWIDTH*(newy + GRIDHEIGHT*newz);
              ncptl_int expected_meshdist;
              ncptl_int meshdist;
              ncptl_int expected_torusdist;
              ncptl_int torusdist;

              /* Determine the correct distances. */
              expected_meshdist = abs_xdelta + abs_ydelta + abs_zdelta;
              expected_torusdist = 0;
              expected_torusdist += abs_xdelta <= GRIDWIDTH/2 ? abs_xdelta : GRIDWIDTH - abs_xdelta;
              expected_torusdist += abs_ydelta <= GRIDHEIGHT/2 ? abs_ydelta : GRIDHEIGHT - abs_ydelta;
              expected_torusdist += abs_zdelta <= GRIDDEPTH/2 ? abs_zdelta : GRIDDEPTH - abs_zdelta;

              /* Validate distance on a mesh. */
              meshdist =
                ncptl_func_mesh_distance (GRIDWIDTH, GRIDHEIGHT, GRIDDEPTH,
                                          0, 0, 0,
                                          taskID_1, taskID_2);
              debug_printf ("\t   ncptl_func_mesh_distance (%d, %d, %d, 0, 0, 0, %" NICS
                            ", %" NICS ") --> %" NICS,
                            GRIDWIDTH, GRIDHEIGHT, GRIDDEPTH,
                            taskID_1, taskID_2, meshdist);
              if (meshdist != expected_meshdist) {
                debug_printf (" (should be %" NICS ")\n", expected_meshdist);
                RETURN_FAILURE();
              }
              debug_printf ("\n");

              /* Validate distance on a full torus. */
              torusdist =
                ncptl_func_mesh_distance (GRIDWIDTH, GRIDHEIGHT, GRIDDEPTH,
                                          1, 1, 1,
                                          taskID_1, taskID_2);
              debug_printf ("\t   ncptl_func_mesh_distance (%d, %d, %d, 1, 1, 1, %" NICS
                            ", %" NICS ") --> %" NICS,
                            GRIDWIDTH, GRIDHEIGHT, GRIDDEPTH,
                            taskID_1, taskID_2, torusdist);
              if (torusdist != expected_torusdist) {
                debug_printf (" (should be %" NICS ")\n", expected_torusdist);
                RETURN_FAILURE();
              }
              debug_printf ("\n");
            }
      }
  debug_printf ("\n");

  /* Test ncptl_func_knomial_parent(). */
  debug_printf ("\tTesting ncptl_func_knomial_parent() ...\n");
  knomial_sizes[0] = sizeof(parent2k)/sizeof(ncptl_int);
  knomial_sizes[1] = 1000;
  knomial_sizes[2] = knomial_sizes[0] - 1;
  for (j=0; j<3; j++) {
    if (j == 2)
      parent2k[sizeof(parent2k)/sizeof(ncptl_int) - 1] = -1;
    for (i=0; i<(ncptl_int)(sizeof(parent2k)/sizeof(ncptl_int)); i++) {
      debug_printf ("\t   ncptl_func_knomial_parent (%" NICS ", 2, %" NICS ") --> %" NICS,
                    i, knomial_sizes[j],
                    ncptl_func_knomial_parent(i, 2, knomial_sizes[j]));
      if (ncptl_func_knomial_parent(i, 2, knomial_sizes[j]) != parent2k[i]) {
        debug_printf (" (should be %" NICS ")\n", parent2k[i]);
        RETURN_FAILURE();
      }
      else
        debug_printf ("\n");
    }
  }
  knomial_sizes[0] = sizeof(parent3k)/sizeof(ncptl_int);
  knomial_sizes[1] = 1000;
  knomial_sizes[2] = knomial_sizes[0] - 1;
  for (j=0; j<3; j++) {
    if (j == 2)
      parent3k[sizeof(parent3k)/sizeof(ncptl_int) - 1] = -1;
    for (i=0; i<(ncptl_int)(sizeof(parent3k)/sizeof(ncptl_int)); i++) {
      debug_printf ("\t   ncptl_func_knomial_parent (%" NICS ", 3, %" NICS ") --> %" NICS,
                    i, knomial_sizes[j],
                    ncptl_func_knomial_parent(i, 3, knomial_sizes[j]));
      if (ncptl_func_knomial_parent(i, 3, knomial_sizes[j]) != parent3k[i]) {
        debug_printf (" (should be %" NICS ")\n", parent3k[i]);
        RETURN_FAILURE();
      }
      else
        debug_printf ("\n");
    }
  }
  debug_printf ("\n");

  /* Test ncptl_func_knomial_child(). */
  knomial_sizes[0] = sizeof(child2k)/(3*sizeof(ncptl_int));
  knomial_sizes[1] = knomial_sizes[0] - 1;
  debug_printf ("\tTesting ncptl_func_knomial_child() ...\n");
  for (k=0; k<2; k++) {
    if (k == 1)
      child2k[3][0] = -1;
    for (i=0; i<(ncptl_int)(sizeof(child2k)/(3*sizeof(ncptl_int))); i++)
      for (j=0; j<2; j++) {
        ncptl_int result = ncptl_func_knomial_child(i, j, 2, knomial_sizes[k], 0);
        debug_printf ("\t   ncptl_func_knomial_child (%" NICS ", %" NICS
                      ", 2, %" NICS ", 0) --> %" NICS,
                      i, j, knomial_sizes[k], result);
        if (result != child2k[i][j]) {
          debug_printf (" (should be %" NICS ")\n", child2k[i][j]);
          RETURN_FAILURE();
        }
        else
          debug_printf ("\n");
      }
  }
  knomial_sizes[0] = sizeof(child3k)/(6*sizeof(ncptl_int));
  knomial_sizes[1] = knomial_sizes[0] - 1;
  for (k=0; k<2; k++) {
    if (k == 1)
      child3k[8][1] = -1;
    for (i=0; i<(ncptl_int)(sizeof(child3k)/(6*sizeof(ncptl_int))); i++)
      for (j=0; j<2; j++) {
        ncptl_int result = ncptl_func_knomial_child(i, j, 3, knomial_sizes[k], 0);
        debug_printf ("\t   ncptl_func_knomial_child (%" NICS ", %" NICS
                      ", 3, %" NICS ", 0) --> %" NICS,
                      i, j, knomial_sizes[k], result);
        if (result != child3k[i][j]) {
          debug_printf (" (should be %" NICS ")\n", child3k[i][j]);
          RETURN_FAILURE();
        }
        else
          debug_printf ("\n");
      }
  }

  RETURN_SUCCESS();
}
