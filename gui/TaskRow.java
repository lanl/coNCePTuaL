/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: task row
 *
 * By Nick Moss <nickm@lanl.gov>
 * Improved and corrected by Paul Beinfest <beinfest@lanl.gov> 
 *
 * TaskRow is a horizontal row of Task components. It is a primarily a
 * graphical construct and a container for statements. Methods are
 * defined for representing a TaskRow visually, handling events, and
 * determining which tasks are already allocated by Stmt's.
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

package gov.lanl.c3.ncptl;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;
import java.util.*;

public class TaskRow extends AbstractComponent {

    // vector containg Task components
    private Vector tasks;

    private Program program;
    
    // horizontal spacing between each Task
    public static final int TASK_SPACING = 5;

    // the amount of padding on the left and right
    public static final int PADDING_X = 15;
    
    // in traversing the stmts in the task row, traverseCursor points
    // to the current stmt
    private int traverseCursor;

    // vector containing Stmt components
    private Vector stmts;

    // dragStart is in local coordinates
    // set when dragging the mouse
    Point dragStart;

    public TaskRow( Program program ){          
        
        traverseCursor = 0;
        this.program = program;
        tasks = new Vector();
        stmts = new Vector();
        dragStart = new Point();

        setNumTasks( program.getNumTasks() );
    }
    
    public void paintStmts( Graphics graphics ){
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            Block parentBlock = (Block)getParent();
            AbstractComponent nextComponent = 
                parentBlock.componentAt( getID() + 1 );
            if( nextComponent != null && nextComponent instanceof TaskRow )
                stmt.paint( graphics, this, (TaskRow)nextComponent );
            else
                stmt.paint( graphics, this, null );
        }
    }

    public void paintComponent( Graphics graphics ){
        Rectangle bounds = getBounds();
        
        if( isSelected() ){
            graphics.setColor( GraphicsUtility.getSelectedColor() );
            graphics.fillRect( 0, 0, bounds.width, bounds.height );
            graphics.setColor( Color.BLACK );
        }

    }

    // remove all Stmt's of type CommunicationStmt, ReduceStmt,
    // and MulticastStmt
    public void clearCommunicationStmts(){
        int i = 0;
        for( ;; ){
            if( i == stmts.size() )
                break;
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( stmt instanceof CommunicationStmt || 
                stmt instanceof ReduceStmt || 
                stmt instanceof MulticastStmt )
                stmts.remove( stmt );
            else
                i++;
        }
    }
    
    // allow all Stmt's and Task's to be selected by the selection
    // marquee
    public void selectRegion( Rectangle marquee ){
        for( int i = 0; i < tasks.size(); i++ ){
            Task task = (Task)tasks.elementAt( i );
            task.selectRegion( marquee );
        }

        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            stmt.selectRegion( marquee );
        }

        super.selectRegion( marquee );
    }
    
    public void setSelectAll( boolean flag ){
        for( int i = 0; i < tasks.size(); i++ ){
            Task task = (Task)tasks.elementAt( i );
            task.setSelectAll( flag );
        }
        super.setSelectAll( flag );
    }

    public void mousePressed( MouseEvent mouseEvent ){
        dragStart.x = mouseEvent.getX();
        dragStart.y = mouseEvent.getY();
    }
    
    public void mouseDragged( MouseEvent mouseEvent ){
        Rectangle dragRect = new Rectangle();
        
        // swap start and end points if needed
        if( mouseEvent.getX() < dragStart.x ){
            dragRect.x = mouseEvent.getX();
            dragRect.width = dragStart.x - mouseEvent.getX();
        }
        else{
            dragRect.x = dragStart.x;
            dragRect.width = mouseEvent.getX() - dragStart.x;
        }
        
        if( mouseEvent.getY() < dragStart.y ){
            dragRect.y = mouseEvent.getY();
            dragRect.height = dragStart.y - mouseEvent.getY();
        }
        else{
            dragRect.y = dragStart.y;
            dragRect.height = mouseEvent.getY() - dragStart.y;
        }

        Point globalXY = toGlobalPoint( dragRect.x, dragRect.y );
        Rectangle globalDragRect = dragRect;
        globalDragRect.x = globalXY.x;
        globalDragRect.y = globalXY.y;
        program.dragSelection( globalDragRect );
    }

    public void mouseClicked( MouseEvent mouseEvent ){
        Rectangle bounds = getBounds();

        // only allow the left and right edges of the TaskRow to be
        // selected
        if( mouseEvent.getX() > 12 && 
            mouseEvent.getX() < bounds.width - 12 )
            return;
        
        if( !isSelected() ){
            if( mouseEvent.isShiftDown() || mouseEvent.isControlDown() )
                deselectNonTaskRows();
            else
                program.setAllSelected( false );
        }

        setSelected( !isSelected() );
        program.clearDialogPane();
        program.updateState();
        repaint();
    }

    public void mouseReleased( MouseEvent mouseEvent ){
        program.dragSelection( null );
    }

    // move the cursor to the next Stmt
    public Stmt traverseNext(){
        if( traverseCursor < stmts.size() ){
            Stmt stmt = (Stmt)stmts.elementAt( traverseCursor );
            traverseCursor++;
            return stmt;
        }
        else
            return null;
    }
    
    // reset the cursor to the beginning of the statements
    public void traverseReset(){
        traverseCursor = 0;
    }

    // return true if the TaskRow has any stmts that are collectives
    // or otherwise require an entire TaskRow
    public boolean hasCollectives(){
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( 
//          stmt instanceof SynchronizeStmt || 
                stmt instanceof ReduceStmt || 
                stmt instanceof MulticastStmt 
//              stmt instanceof WaitStmt || 
//              stmt instanceof OtherStmt )
                )
                return true;
        }
        return false;
    }

    // return true if the TaskRow has a SynchronizeStmt
    public boolean hasSynchronize(){
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( stmt instanceof SynchronizeStmt )
                return true;
        }
        return false;
    }

    // return true if the TaskRow has a ReduceStmt
    public boolean hasReduce(){
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( stmt instanceof ReduceStmt )
                return true;
        }
        return false;
    }

    // return true if the TaskRow has a OtherStmt
    public boolean hasOther(){
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( stmt instanceof OtherStmt )
                return true;
        }
        return false;
    }

    // return true if the TaskRow has a MulticastStmt
    public boolean hasMulticast(){
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( stmt instanceof MulticastStmt )
                return true;
        }
        return false;
    }

    // return true if the TaskRow has a WaitStmt
    public boolean hasWait(){
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( stmt instanceof WaitStmt )
                return true;
        }
        return false;
    }

    // return true if the TaskRow has any Stmt's
    public boolean hasStmts(){
        if( stmts.size() > 0 )
            return true;
        return false;
    }
    
    // get Task number taskNum
    public Task getTask( int taskNum ){
        if( taskNum < tasks.size() )
            return (Task)tasks.elementAt( taskNum );
        else
            return null;
    }

    // add stmt to the TaskRow
    public void add( Stmt stmt ){
        stmt.setTaskRow( this );
        stmts.add( stmt );
    }

    public void setProgram( Program program ){
        for( int i = 0; i < tasks.size(); i++ ){
            Task task = (Task)tasks.elementAt( i );
            task.setProgram( program );
        }
        this.program = program;
    }

    // return the allocated tasks
    // a task that is already allocated should not be used as a source task
    // in another Stmt in the same task row
    public Vector getAllocatedTasks(){
        Vector allocated = new Vector();
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );

            if( stmt instanceof CommunicationStmt ){
                CommunicationStmt commStmt = (CommunicationStmt)stmt;

                TaskGroup taskGroup = commStmt.getTaskGroup();
                Vector sourceTargets = taskGroup.enumerate();
                
                if( sourceTargets.size() == 1 && 
                    ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ) {

                    return program.getAllTasks();
                }
                
                if( !commStmt.getSourceAsync() ){
                    
                    Vector sources = 
                        SourceTarget.getSources( sourceTargets );

                    allocated = 
                        Utility.union( allocated, sources );
                }

                if( !commStmt.getUnsuspecting() &&
                    !commStmt.getTargetAsync() ){
                    Vector targets = 
                        SourceTarget.getTargets( sourceTargets );
                    
                    allocated = 
                        Utility.union( allocated, targets );
                }       
            }
                //  count any tasks associated with "collective" operations as allocated (added by P.B.)
            if (stmt instanceof WaitStmt) {
                        Vector awaitingCompletion = program.enumerateCollectives(stmt.toCode(), "wait_stmt");
                        allocated = Utility.union(allocated, awaitingCompletion);
            }
            if (stmt instanceof SynchronizeStmt) {
                        Vector awaitingCompletion = program.enumerateCollectives(stmt.toCode(), "sync_stmt");
                        allocated = Utility.union(allocated, awaitingCompletion);
            }
            if (stmt instanceof OtherStmt) {
                        Vector awaitingCompletion = program.enumerateCollectives(stmt.toCode(), ((OtherStmt)stmt).getStmtType());
                        allocated = Utility.union(allocated, awaitingCompletion);
            }
            else if( stmt instanceof ComputeStmt ){
                TaskGroup taskGroup = 
                    ((ComputeStmt)stmt).getTaskGroup();

                Vector sourceTargets = taskGroup.enumerate();

                Vector sources = 
                    SourceTarget.getSources( sourceTargets );
                
                allocated = 
                    Utility.union( allocated, sources );
            }
        }
        return allocated;
    }

    // get all selected sub-components
    public Vector getAllSelected( Vector selectedComponents ){
        if( isSelected() )
            selectedComponents.add( this );
        
        for( int i = 0; i < tasks.size(); i++ ){
            Task task = (Task)tasks.elementAt( i );
            if( task.isSelected() )
                selectedComponents.add( task );
        }
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            if( stmt.isSelected() )
                selectedComponents.add( stmt );
        }
        return selectedComponents;
    }

    // set the selection state of all sub-components
    public void setAllSelected( boolean flag ){
        setSelected( flag );
        for( int i = 0; i < tasks.size(); i++ ){
            Task task = (Task)tasks.elementAt( i );
            task.setAllSelected( flag );
        }
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            stmt.setSelectedOnly( flag );
        }
    }

    // remove stmt from the task row
    public void remove( Stmt stmt ){
        stmts.remove( stmt );
    }

    public void deselectNonTaskRows(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof TaskRow) )
                component.setSelected( false );
        }
        
    }
    
    // resize the task row to contain numTasks tasks
    public void setNumTasks( int numTasks ){
        tasks.clear();
        removeAll();

        Task task = null;
        
        for( int i = 0; i < numTasks; i++ ){
            task = new Task( program, i, 
                             i*(Task.TASK_SIZE + TASK_SPACING)+PADDING_X, 0 );
            tasks.add( task );
            super.add( task );
        }
        if( task != null ){
            Rectangle lastBounds = task.getBounds();
            setBounds( 0, 0, lastBounds.x + lastBounds.width + 1 + PADDING_X, lastBounds.height + 1 );
        }

        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            stmt.resize();
        }
    }
    
    // cause resize to be called on all stmts
    public void resize(){
        for( int i = 0; i < stmts.size(); i++ )
            ((Stmt)stmts.elementAt( i )).resize();
    }

    // clone the task row and all of its sub-components
    public Object clone() throws CloneNotSupportedException {
        TaskRow taskRow = new TaskRow( program );
        for( int i = 0; i < stmts.size(); i++ ){
            Stmt stmt = (Stmt)stmts.elementAt( i );
            Stmt clonedStmt = (Stmt)stmt.clone();
            clonedStmt.setTaskRow( taskRow );
            taskRow.add( clonedStmt );
        }
        return taskRow;
    }
    
    // take (remove all) stmts from taskRow and add them to this task row
    public void takeStmts( TaskRow taskRow ){
        while( taskRow.stmts.size() > 0 )
            add( (Stmt)taskRow.stmts.remove( 0 ) );
    }
}
