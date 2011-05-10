/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: source target
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * SourceTarget is a (source,target) pair used in enumerating a TaskGroup
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

package gov.lanl.c3.ncptl;

import java.util.*;

public class SourceTarget {
    public int source;
    public int target;
    public boolean unknown = false;

    public SourceTarget( int source, int target ){
        this.source = source;
        this.target = target;
    }

    // returns a vector of sources Integers from an
    // input Vector or SourceTarget's
    public static Vector getSources( Vector sourceTargets ){
        Vector sources = new Vector();
        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget =
                (SourceTarget)sourceTargets.elementAt( i );
            Integer source = new Integer( sourceTarget.source );
            if( sources.indexOf( source ) < 0 )
                sources.add( source );
        }
        return sources;
    }

    // returns a vector of target Integers from an
    // input Vector of SourceTarget's
    public static Vector getTargets( Vector sourceTargets ){
        Vector targets = new Vector();
        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget =
                (SourceTarget)sourceTargets.elementAt( i );
            Integer target = new Integer( sourceTarget.target );
            if( targets.indexOf( target ) < 0 )
                targets.add( target );
        }
        return targets;
    }
}
