#! /usr/bin/env python

########################################################################
#
# Functions defined in the runtime-library but that cannot be called
# directly from the GUI; adapted from userfuncs.c
#
# By Nick Moss <nickm@lanl.gov>
#
# ----------------------------------------------------------------------
#
# Copyright (C) 2012, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2012).  Los Alamos National Security, LLC.  This software
# was produced under U.S. Government contract DE-AC52-06NA25396
# for Los Alamos National Laboratory (LANL), which is operated by
# Los Alamos National Security, LLC (LANS) for the U.S. Department
# of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
# MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
# FOR THE USE OF THIS SOFTWARE. If software is modified to produce
# derivative works, such modified software should be clearly marked,
# so as not to confuse it with the version available from LANL.
# 
# Additionally, redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the
# following conditions are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer
#     in the documentation and/or other materials provided with the
#     distribution.
# 
#   * Neither the name of Los Alamos National Security, LLC, Los Alamos
#     National Laboratory, the U.S. Government, nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
#
########################################################################

import math

def ncptl_seed_random_task( p1, p2 ):
    return 0

def ncptl_allocate_timing_flag():
    return 0

def ncptl_func_sqrt( num ):
    return ncptl_func_root( 2, num )

def ncptl_dfunc_sqrt( num ):
    return math.sqrt( num )

def ncptl_func_cbrt( num ):
    return ncptl_func_root( 3, num )

def ncptl_dfunc_cbrt( num ):
    return math.pow( num, 1.0/3.0 )

def ncptl_func_root( root, num ):
    return math.floor( ncptl_dfunc_root( root, num ) )

def ncptl_dfunc_root( root, num ):
    return math.pow( num, 1.0/root )

def ncptl_func_bits( num ):
    numbits = 0
    while num > 0:
        numbits += 1
        num >>= 1
    return numbits

def ncptl_dfunc_bits( num ):
    return ncptl_func_bits( math.ceil( num ) )

def ncptl_func_shift_left( num, bits ):
    if bits >= 0:
        return num << bits
    else:
        return num >> -bits

def ncptl_dfunc_shift_left( num, bits ):
    return ncptl_func_shift_left( math.floor( num ), math.floor( num ) )


def ncptl_func_log10( num ):
    return math.floor( math.log10( num ) )

def ncptl_dfunc_log10( num ):
    return math.log10( num )

def ncptl_dfunc_factor10( num ):
    if num == 0:
        return 0
    else:
        if num > 0:
            floorlog10 = math.floor( math.log10( num ) )
            pow10 = math.pow( 10.0, floorlog10 )
            factor = math.floor( num/pow10 )
            return factor*pow10
        else:
            floorlog10 = math.floor( math.log10( -num ) )
            pow10 = math.pow( 10.0, floorlog10 )
            factor = math.floor( -num/pow10 )
            return -factor*pow10

def ncptl_func_factor10( num ):
    return math.floor( ncptl_dfunc_bits( num ) )

def ncptl_func_abs( num ):
    if num < 0:
        return -num
    else:
        return num

def ncptl_dfunc_abs( num ):
    if num < 0:
        return -num
    else:
        return num

def ncptl_func_power( base, exponent ):
    if exponent < 0:
        result = 0

        if base == 1:
            result = 1
        elif base == -1:
            if exponential & 1:
                result = -1
            else:
                result = 1
        else:
            result = 0
        return result
    return math.pow( base, exponent )


def ncptl_dfunc_power( base, exponent ):
    return math.pow( base, exponent )

def ncptl_func_modulo( numerator, denominator ):
    if denominator < 0:
        denominator = -denominator
    result = numerator % denominator
    if result < 0:
        return result + denominator
    else:
        return result

def ncptl_dfunc_modulo( numerator, denominator ):
    return ncptl_func_modulo( math.floor( numerator ), math.floor( denominator ) )

def ncptl_func_floor( num ):
    return math.floor( num )

def ncptl_dfunc_floor( num ):
    return math.floor( num )

def ncptl_func_ceiling( num ):
    return math.ceil( num )

def ncptl_dfunc_ceiling( num ):
    return math.ceil( num )

def ncptl_func_round( num ):
    return num

def ncptl_func_round( num ):
    return math.floor( num )

def ncptl_func_tree_parent( task, arity ):
    if task <= 0:
        return -1
    else:
        (task - 1)/arity

def ncptl_dfunc_tree_parent( task, arity ):
    return ncptl

def ncptl_func_tree_child( task, child, arity ):
    if arity < 1:
        raise Exception
    if child < 0 or child >= arity:
        return -1
    return task*arity + child + 1


def ncptl_dfunc_tree_child( task, child, arity ):
    return ncptl_func_tree_child( math.floor( task ), math.floor( child), math.floor( arity ) )

def ncptl_func_mesh_coord( task, coord, width, height, depth ):
    gridelts = width * height * depth

    if gridelts == 0:
        raise Exception

    if width < 0 or height < 0 or depth < 0:
        raise Exception

    if task < 0 or task >= gridelts:
        return -1

    xpos = task % width
    ypos = (task % (width*height)) / width
    zpos = task / (width*height)

    if coord == 0:
        return xpos
    elif coord == 1:
        return ypos
    elif coord == 2:
        return zpos
    else:
        raise Exception

    return -1

def ncptl_dfunc_mesh_coord( task, coord, width, height, depth ):
    return ncptl_func_mesh_coord( math.floor( task ), math.floor( coord ), math.floor( width ), math.floor( height ), math.floor( depth ) )


def ncptl_func_mesh_neighbor( task, torus, width, height, depth, xdelta, ydelta, zdelta ):
    gridelts = width * height * depth

    if gridelts == 0:
        raise Exception

    if width < 0 or height < 0 or depth < 0:
        raise Exception

    if task < 0 or task >= gridelts:
        return -1

    xpos = task % width
    ypos = (task % (width*height)) / width
    zpos = task / (width*height)

    if torus:
        xpos = ncptl_func_modulo( xpos + xdelta, width )
        ypos = ncptl_func_modulo( ypos + ydelta, height )
        zpos = ncptl_func_modulo( zpos + zdelta, depth )
    else:
        xpos += xdelta
        ypos += ydelta
        zpos += zdelta

        if (xpos < 0 or (xpos >= width and width > 0) or ypos < 0 or (ypos >= height and height > 0) or zpos < 0 or (zpos >= depth and depth > 0)):
            return -1
    return zpos*height*width + ypos*width + xpos

def ncptl_dfunc_mesh_neighbor( task, torus, width, height, depth, xdelta, ydelta, zdelta ):
    return math.floor( ncptl_func_mesh_neighbor( math.floor( task ), math.floor( torus ), math.floor( width ), math.floor( height ), math.floor( depth ), math.floor( xdelta ), math.floor( ydelta ), math.floor( zdelta ) ) )

def knomial_numdigits( arity, number ):
    numdigits = 1
    powk = arity

    while powk - 1 < number:
        numdigits += 1
        powk *= arity

    return numdigits

def knomial_getdigit( arity, number, digit ):
    return (number / ncptl_func_power( arity, digit )) % arity

def knomial_setdigit( arity, number, digit, newdigit ):
    result = number
    shift_amount = ncptl_func_power( arity, digit )
    result -= knomial_getdigit( arity, number, digit ) * shift_amount
    result += newdigit * shift_amount
    return result

def ncptl_func_knomial_parent( task, arity, numtasks ):
    if arity < 2:
        raise Exception
    if task <= 0 or task >= numtasks:
        return -1

    digit = digit=knomial_numdigits(arity, numtasks-1)-1
    while digit >= 0:
        if knomial_getdigit( arity, task, digit ):
            return knomial_setdigit( arity, task, digit, 0 )
        digit -= 1
    raise Exception
    return -1

def ncptl_dfunc_knomial_parent( task, arity, numtasks ):
    return ncptl_func_knomial_parent( math.floor( task ), math.floor( arity ), math.floor( numtasks ) )

def ncptl_func_knomial_child( task, child, arity, numtasks, count_only ):
    children = []

    if arity < 2:
        raise Exception

    if task >= numtasks or child < 0:
        return -1

    digit = knomial_numdigits( arity, numtasks - 1 ) - 1
    while digit >= 0:
        test = knomial_getdigit( arity, task, digit )
        if knomial_getdigit( arity, task, digit ):
            break
        nonz = arity - 1
        while nonz >= 1:
            childID = knomial_setdigit( arity, task, digit, nonz )
            if childID < numtasks:
                children.append( childID )
            nonz -= 1
        digit -= 1

    num_children = len( children )
    if count_only:
        return num_children
    elif child < num_children:
        return children[num_children-child-1]
    else:
        return -1

def ncptl_dfunc_knomial_child( task, child, arity, numtasks, count_only ):
    return ncptl_func_knomial_child( math.floor( task ), math.floor( child ), math.floor( arity ), math.floor( numtasks ), math.floor( count_only ) )

def ncptl_func_min( count, list ):
    return min( list )

def ncptl_dfunc_min( count, list ):
    return min( list )

def ncptl_func_max( count, list ):
    return max( list )

def ncptl_dfunc_max( count, list ):
    return max( list )

def patch_max( list ):
    max = None
    for i in list:
        if max == None or i > max:
            max = i
    return max

def patch_min( list ):
    min = None
    for i in list:
        if min == None or i < min:
            min = i
    return min

def ncptl_virtual_to_physical(procmap, vtask):
    return vtask

def ncptl_assign_processor(virtID, physID, procmap, physrank):
    pass

def _get_mesh_coordinates(width, height, depth, task):
    # Abort if we were given unreasonable mesh dimensions.
    meshelts = width * height * depth
    if not meshelts:
        raise Exception, "coordinate calculations can't be performed on a zero-sized mesh/torus"
    if width<0 or height<0 or depth<0:
        raise Exception, "meshes/tori may not have negative dimensions"

    # Tasks that are outside of the mesh have no valid coordinates.
    if task<0 or task>=meshelts:
        return (-1, -1, -1)

    # Map the task number from Z to Z^3.
    xpos = task % width
    ypos = (task % (width*height)) / width
    zpos = task / (width*height)
    return (xpos, ypos, zpos)

def ncptl_func_mesh_coord(width, height, depth, task, coord):
    xpos, ypos, zpos = _get_mesh_coordinates(width, height, depth, task)
    if coord in [0, 1, 2]:
        return [xpos, ypos, zpos][coord]
    else:
        raise Exception, "mesh/torus coordinate must be 0, 1, or 2 (for x, y, or z, respectively)"

def ncptl_dfunc_mesh_coord(width, height, depth, task, coord):
    return ncptl_func_mesh_coord(int(width), int(height), int(depth), int(task), int(coord))

def ncptl_func_mesh_neighbor(width, height, depth,
                             xtorus, ytorus, ztorus,
                             task,
                             xdelta, ydelta, zdelta):
    # Find and validate the mesh coordinates.
    xpos, ypos, zpos = _get_mesh_coordinates(width, height, depth, task)
    if xpos == -1:
        return -1

    # Add deltas to each coordinate in turn.  If we fall off the end
    # of a row, column, or pile, we wrap around (torus case) or return
    # an invalid neighbor (mesh case).
    xpos += xdelta
    ypos += ydelta
    zpos += zdelta
    if xtorus:
        xpos = ncptl_func_modulo(xpos, width)
    if ytorus:
        ypos = ncptl_func_modulo(ypos, height)
    if ztorus:
        zpos = ncptl_func_modulo(zpos, depth)
    if xpos<0 or xpos>=width or ypos<0 or ypos>=height or zpos<0 or zpos>=depth:
        return -1

    # Map back from Z^3 to Z.
    return zpos*height*width + ypos*width + xpos

def ncptl_dfunc_mesh_neighbor(width, height, depth,
                              xtorus, ytorus, ztorus,
                              task,
                              xdelta, ydelta, zdelta):
    return ncptl_func_mesh_neighbor(int(width), int(height), int(depth),
                                    int(xtorus), int(ytorus), int(ztorus),
                                    int(task),
                                    int(xdelta), int(ydelta), int(zdelta))

def ncptl_func_mesh_distance(width, height, depth,
                             xtorus, ytorus, ztorus,
                             task1, task2):
    # Find and validate the mesh coordinates.
    xpos1, ypos1, zpos1 = _get_mesh_coordinates(width, height, depth, task1)
    if xpos1 == -1:
        return -1
    xpos2, ypos2, zpos2 = _get_mesh_coordinates(width, height, depth, task2)
    if xpos2 == -1:
        return -1

    # Compute the distance between each pair of coordinates on a mesh.
    xdelta = ncptl_func_abs(xpos1 - xpos2)
    ydelta = ncptl_func_abs(ypos1 - ypos2)
    zdelta = ncptl_func_abs(zpos1 - zpos2)

    # See if we can take shortcuts across any torus edges.
    if xtorus and xdelta > width/2:
        xdelta = width - xdelta
    if ytorus and ydelta > height/2:
        ydelta = height - ydelta
    if ztorus and zdelta > depth/2:
        zdelta = depth - zdelta

    # Return the Manhattan distance between the two tasks.
    return xdelta + ydelta + zdelta

def ncptl_dfunc_mesh_distance(width, height, depth,
                              xtorus, ytorus, ztorus,
                              task1, task2):
    return ncptl_func_mesh_distance(int(width), int(height), int(depth),
                                    int(xtorus), int(ytorus), int(ztorus),
                                    int(task1), int(task2))
