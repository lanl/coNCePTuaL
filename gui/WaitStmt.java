/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: wait statement
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * WaitStmt corresponds to a awaits_completion stmt and is associated
 * with a TaskRow. WaitStmt includes both the data representation as
 * well as methods for its visual representation and manipulation in
 * the GUI.
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

public class WaitStmt extends Stmt {
    private TaskGroup taskGroup;
    
    public WaitStmt( Program program ){
        super( program );
    }

    // targetRow is unused
    public void paint( Graphics graphics, 
                       TaskRow sourceRow, 
                       TaskRow targetRow ){
        Vector sourceTargets = taskGroup.enumerate();
        if( paintUnknown( graphics, 
                          sourceTargets, 
                          sourceRow,
                          "variable tasks: wait",
                          isSelected() ) )
            return;

        if( isSelected() ){
            Rectangle bounds = sourceRow.getGlobalBounds();
            graphics.setColor( GraphicsUtility.getSelectedColor() );
            graphics.fillRect( bounds.x, bounds.y + bounds.height + 1, 
                               bounds.width, 12 );
            graphics.setColor( Color.BLACK );
        }

        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_BOLD );
        for( int i = 0; i < sourceTargets.size(); i++ ){

            SourceTarget sourceTarget = 
                (SourceTarget)sourceTargets.elementAt( i );

            Task task = sourceRow.getTask( sourceTarget.source );
            Rectangle bounds = task.getGlobalBounds();
            graphics.drawLine( bounds.x - 2, 
                               bounds.y + bounds.height + 10,
                               bounds.x + bounds.width + 2, 
                               bounds.y + bounds.height + 10);
        }
        graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
    }
    
    public String toCode(){
        return taskGroup.toCodeSource() + " " + 
            Utility.wordForm( taskGroup.toCodeSource(), "awaits" ) + " completion";
    }

    public void setTaskGroup( TaskGroup taskGroup ){
        this.taskGroup = taskGroup;
    }

    public void setTaskGroup( String taskGroupString ){
        TaskGroup taskGroup = new TaskGroup( program );
        taskGroup.setSource( taskGroupString ); 
        setTaskGroup( taskGroup );
    }

    public TaskGroup getTaskGroup(){
        return taskGroup;
    }

    // select/deselect the WaitStmt if click (xg, yg) in global coordinates
    // is within its selection bounds
    public boolean clickSelect( boolean isShiftOrCtrlClick, int xg, int yg ){
        boolean foundSelect = false;

        TaskRow taskRow = getTaskRow();
        Rectangle bounds = taskRow.getGlobalBounds();
        
        Vector sourceTargets = taskGroup.enumerate();
        if( sourceTargets.size() == 1 && 
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            return clickSelectUnknown( taskRow,
                                       new Point( xg, yg ) );
        }
        
        if( xg >= bounds.x &&
            xg <= bounds.x + bounds.width &&
            yg >= bounds.y + bounds.height &&
            yg <= bounds.y + bounds.height + 10 ){
            if( !isSelected() ){
                if( isShiftOrCtrlClick )
                    deselectNonWaitStmts();
                else
                    program.setAllSelected( false );
            }
            setSelected( !isSelected() );
            program.updateState();
            foundSelect = true;
        }
        return foundSelect;
    }

    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateWaitDialog();
    }
    
    public void deselectNonWaitStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof WaitStmt) )
                component.setSelected( false );
        }
    }

    public void selectRegion( Rectangle marquee ){
        Rectangle bounds = getTaskRow().getGlobalBounds();
        
        Vector sourceTargets = taskGroup.enumerate();
        if( sourceTargets.size() == 1 && 
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            selectRegionUnknown( getTaskRow(), 
                                 marquee );
            return;
        }

        bounds.x += 10;
        bounds.width -= 10;
        bounds.y = bounds.y + bounds.height;
        bounds.height = 10;

        if( Utility.marqueeSelects( marquee, bounds ) )
            setSelected( true );
    }

    
    public void resize(){
        taskGroup.resize();
    }
    
}
