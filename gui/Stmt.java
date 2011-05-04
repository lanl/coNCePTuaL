/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: statement
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * Stmt is the abstract base class for CommunicationStmt, ComputeStmt,
 * etc. Statements are associated with a task row and apply to tasks
 * in a single task row or between tasks in consecutive task rows
 * (such as in a CommunicationStmt).
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

package gov.lanl.c3.ncptl;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;
import java.util.*;

abstract public class Stmt extends AbstractComponent {

    private boolean isSelected;
    protected Program program;

    // the task row that this stmt belongs to
    protected TaskRow taskRow;

    Stmt( Program program ){
        this.program = program;
    }

    // paint the stmt from sourceRow to targetRow
    // for some statements, e.g: ComputeStmt, targetRow will be
    // passed as null
    abstract public void paint( Graphics graphics,
                                TaskRow sourceRow,
                                TaskRow targetRow );

    // get the coNCePTuaL code for this statement
    abstract public String toCode();

    public Vector getVariablesInScope( Vector variables ){
        return taskRow.getVariablesInScope( variables );
    }

    public Vector getAllVariablesInScope( Vector variables ){
        return taskRow.getAllVariablesInScope( variables );
    }

    // dragging the marquee around this component, allow it to be
    // selected if its bounds are sufficiently contained in marquee
    public void selectRegion( Rectangle marquee ){

    }

    // process a click, selecting or deselecting the stmt
    // if clock point (xg,yg) in global coordinates
    // is within the statement-specific bounds
    // returns true if the stmt was selected
    public boolean clickSelect( boolean isShiftOrCtrlClick, int xg, int yg ){
        return false;
    }

    // detach the stmt from its task row
    public void detach(){
        taskRow.remove( this );
    }

    // set the task row that the stmt belongs to
    public void setTaskRow( TaskRow taskRow ){
        this.taskRow = taskRow;
    }

    // get the task row that the stmt belongs to
    public TaskRow getTaskRow(){
        return taskRow;
    }

    // called when num_tasks is modified
    abstract public void resize();

    boolean paintUnknown( Graphics graphics,
                          Vector sourceTargets,
                          TaskRow taskRow,
                          String label,
                          boolean selected ){

        if( sourceTargets.size() >= 1 &&
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            Rectangle sourceBounds = taskRow.getGlobalBounds();
            Rectangle bounds = new Rectangle();
            bounds.x = sourceBounds.x + TaskRow.PADDING_X;
            bounds.y = sourceBounds.y + sourceBounds.height + 5;
            bounds.width = sourceBounds.width - TaskRow.PADDING_X*2;
            bounds.height = sourceBounds.height - 5;

            GraphicsUtility graphicsUtility =
                new GraphicsUtility( graphics );

            if( selected ){
                graphics.setColor( graphicsUtility.getSelectedColor() );
                graphicsUtility.setStroke( GraphicsUtility.STROKE_HIGHLIGHT );
                graphics.fillRect( bounds.x, bounds.y,
                                   bounds.width, bounds.height );
                graphics.setColor( Color.black );
                graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
            }

            graphics.drawRect( bounds.x, bounds.y,
                                 bounds.width, bounds.height );
            graphics.drawString( label, sourceBounds.x + TaskRow.PADDING_X + 5,
                                   sourceBounds.y + sourceBounds.height + 21 );
            return true;
        }
        return false;
    }

    boolean clickSelectUnknown( TaskRow taskRow, Point p ){

        Rectangle sourceBounds = taskRow.getGlobalBounds();
        Rectangle bounds = new Rectangle();
        bounds.x = sourceBounds.x + TaskRow.PADDING_X;
        bounds.y = sourceBounds.y + sourceBounds.height + 5;
        bounds.width = sourceBounds.width - TaskRow.PADDING_X*2;
        bounds.height = sourceBounds.height - 5;
        if( Utility.contains( bounds, p ) ){
            if( !isSelected() ){
                program.setAllSelected( false );
                setSelected( true );
            }
            else
                setSelected( false );
            program.updateState();
            return true;
        }
        else
            return false;
    }

    void selectRegionUnknown( TaskRow taskRow, Rectangle marquee ){

        Rectangle sourceBounds = taskRow.getGlobalBounds();
        Rectangle bounds = new Rectangle();
        bounds.x = sourceBounds.x + TaskRow.PADDING_X;
        bounds.y = sourceBounds.y + sourceBounds.height + 5;
        bounds.width = sourceBounds.width - TaskRow.PADDING_X*2;
        bounds.height = sourceBounds.height - 5;
        if( Utility.marqueeSelects( marquee, bounds ) )
            setSelected( true );
    }

}
