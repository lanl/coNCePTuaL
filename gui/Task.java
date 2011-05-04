/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: task
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class contains methods for drawing a task within a task row
 * and event-handling for mouse events within its bounds.
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

public class Task extends AbstractComponent {

    // default diameter of tasks
    public static final int TASK_SIZE = 25;

    // coordinates of the task relative to its task row
    private int x;
    private int y;
    
    private Program program;
    
    public Task( Program program, int id, int x, int y ){       
        setID( id );
        this.program = program;
        setBounds( x, y, TASK_SIZE+1, TASK_SIZE+1 );
        addMouseMotionListener( program.getScrollPane() );
        addMouseListener( program.getScrollPane() );
    }
    
    public void paintComponent( Graphics graphics ){
        String idString = Integer.toString( getID() );
        if( isSelected() ){
            graphics.setColor( GraphicsUtility.getSelectedColor() );
            graphics.fillOval( 0, 0, TASK_SIZE, TASK_SIZE );
            graphics.setColor( Color.black );
            graphics.drawOval( 0, 0, TASK_SIZE, TASK_SIZE );
        }
        else{
            graphics.setColor( Color.white );
            graphics.fillOval( 0, 0, TASK_SIZE, TASK_SIZE );
            graphics.setColor( Color.black );
            graphics.drawOval( 0, 0, TASK_SIZE, TASK_SIZE );
        }
        float x = TASK_SIZE/2.0f - idString.length()*3.50f;
        float y = TASK_SIZE/2.0f + 5.0f;
        graphics.drawString( idString, (int)x, (int)y );
    }

    // get the ID of the task row that this task belongs to
    public int getRowID(){
        TaskRow taskRow = (TaskRow)getParent();
        return taskRow.getID();
    }
    
    public void mouseDragged( MouseEvent mouseEvent ){
        // sourceTask is the source task if a drag to
        // create a communication stmt is already in progress
        Task sourceTask = program.getSourceTask();
        if( sourceTask == null ){
            TaskRow taskRow = (TaskRow)getParent();
            // can only create communication stmt if there are no
            // collectives in the row
            if( !taskRow.hasSynchronize() &&
                !taskRow.hasReduce() && 
                !taskRow.hasMulticast() &&
                !taskRow.hasOther() &&
                !taskRow.hasWait() ){
                program.setSourceTask( this );
            }
            setSelectedMouseDown( true );
            repaint();
        }

        if( program.getSourceTask() != null )
            program.dragArrow( toGlobalPoint( mouseEvent.getX(), 
                                              mouseEvent.getY() ) );

    }

    public void mouseClicked( MouseEvent mouseEvent ){
        if( !isSelected() ){
            if( mouseEvent.isShiftDown() || mouseEvent.isControlDown() )
                deselectNonTasks();
            else
                // deselect all other components
                program.setAllSelected( false );
        }
        // toggle the selection state
        setSelected( !isSelected() );
        
        // set the source task for any drag in progress to null
        program.setSourceTask( null );
        program.clearDialogPane();
        program.updateState();
        repaint();
    }

    public void mouseEntered( MouseEvent mouseEvent ){
        Task sourceTask = program.getSourceTask();

        // if there is a drag in progress and it is from a
        // task in a task row to another task row after it
        if( sourceTask != null && program.appearsAfter( sourceTask, this ) ){
            setSelectedMouseDown( true );
            program.setTargetTask( this );
            repaint();
        }
    }

    public void mouseExited( MouseEvent mouseEvent ){
        Task sourceTask = program.getSourceTask();
        // if there is a drag in progress and the mouse
        // has left the target task then unset target task
        if( sourceTask != null && this != sourceTask ){
            program.setTargetTask( null );
            setSelectedMouseDown( false );
            repaint();
        }
    }

    public void mouseReleased( MouseEvent mouseEvent ){
        Task sourceTask = program.getSourceTask();
        Task targetTask = program.getTargetTask();

        // if the mouse has been released and there is a drag
        // in progress and the target task is valid then
        // create the communication edge
        if( sourceTask != null && targetTask != null ){
            program.createEdge( sourceTask, targetTask );
            program.setSourceTask( null );
            program.setTargetTask( null );
            sourceTask.setSelected( false );
            targetTask.setSelected( false );
            program.dragArrow( null );
            program.repaint();
        }
        // else release the sourceTask
        else if( sourceTask != null && targetTask == null ){
            sourceTask.setSelected( false );
            program.setSourceTask( null );
            program.dragArrow( null );
            program.repaint();
        }
    }

    public void setProgram( Program program ){
        this.program = program;
    }

    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateState();
    }

    public void setSelectedMouseDown( boolean flag ){
        super.setSelected( flag );
    }

    public void deselectNonTasks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof Task) )
                component.setSelected( false );
        }
        
    }

    public Object clone() throws CloneNotSupportedException {
        return super.clone();
    }
    
}

