/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: task group
 *
 * By Nick Moss <nickm@lanl.gov>
 * Improved and corrected by Paul Beinfest <beinfest@lanl.gov>
 *
 * A TaskGroup couples a source task expression with an optional
 * target task expression and is used by CommunicationStmt,
 * ComputeStmt, and other classes derived from Stmt. Task expressions
 * are run through the parser and enumerated by process_node() in
 * codegen_interpret then cached internally.
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

package gov.lanl.c3.ncptl;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.border.*;
import javax.swing.event.*;
import java.util.*;

public class TaskGroup implements Cloneable {

    // the source task expression, e.g:
    // "all tasks t such that t < 5"
    private String sourceDescription;

    // the target task expression, e.g:
    // "all other tasks"
    // for some statements such as ComputeStmt, this field is unused
    private String targetDescription;

    // the wait statement description, e.g:
    // "all tasks" or "all tasks t such that t is even" (added by P.B)
    private String waitDescription;

    private Program program;

    // a vector containing the cached (source,target) pairs
    private Vector sourceTargets;

    // a vector containing only targets, used for reductions (added by SDP)
    private Vector targetTargets;

    // a vector containing the cached (source,target) pairs awaiting
    // completion (added by P.B.)
    private Vector awaitCompletion;

    public TaskGroup( Program program ){
        this.program = program;
        sourceTargets = null;
        targetTargets = null;
        sourceDescription = null;
        targetDescription = null;
        awaitCompletion = null;
        waitDescription = null;
    }

    public void setSource( int taskNum ){
        sourceDescription = "task " + taskNum;
        sourceTargets = null;
    }

    public void setTarget( int taskNum ){
        targetDescription = "task " + taskNum;
        sourceTargets = null;
        targetTargets = null;
    }

    public void setSource( String sourceDescription ){
        this.sourceDescription = sourceDescription;
        sourceTargets = null;
    }

    public void setTarget( String targetDescription ){
        this.targetDescription = targetDescription;
        sourceTargets = null;
        targetTargets = null;
    }

    public void setWait(String waitDescription) {
        this.waitDescription = waitDescription;
        awaitCompletion = null;
    }

    public Vector enumerate(){
        if( sourceTargets == null ){
            if( targetDescription == null )
                sourceTargets =
                    program.enumerateTaskGroup( sourceDescription );
            else
                sourceTargets =
                    program.enumerateTaskGroup( sourceDescription,
                                                targetDescription );

            if (waitDescription != null) {
                awaitCompletion = program.enumerateCollectives(waitDescription, null);
                sourceTargets = Utility.union(sourceTargets, awaitCompletion);
            }
        }

        return sourceTargets;
    }

    // same as enumerate but used for reductions, whose targets are
    // independent from the sources (added by SDP)
    public Vector enumerate_ignoring_targets(){
        if( sourceTargets == null )
            sourceTargets =
              program.enumerateTaskGroup( sourceDescription );

        return sourceTargets;
    }

    // same as enumerate but used for reductions, whose targets are
    // also <source_task>s (added by SDP)
    public Vector enumerate_targets_as_sources(){
        if( targetTargets == null )
            targetTargets =
              program.enumerateTaskGroup( targetDescription );

        return targetTargets;
    }

    public String toCodeSource(){
        return sourceDescription;
    }

    public String toCodeTarget(){
        return targetDescription;
    }

    // called when num_tasks is modified. clears the cache forcing the
    // TaskGroup to be re-enumerated
    public void resize(){
        sourceTargets = null;
    }

    public Object clone() throws CloneNotSupportedException {
        return super.clone();
    }

}
