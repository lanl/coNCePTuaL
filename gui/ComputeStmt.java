/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: compute statement
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * ComputeStmt derives from the Stmt class, and like other Stmt's, is
 * associated with a TaskRow. ComputeStmt combines the functionality
 * of computes_for, sleeps_for, and touch_stmt coNCePTuaL statements.
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

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;
import java.util.*;

public class ComputeStmt extends Stmt {

    private int type;

    // the height in pixels of the rectangle drawn when the
    // ComputeStmt is selected
    private static final int SELECTED_HEIGHT = 12;

    // the height in pixels of the caption text, e.g: "cmp", "slp", or "tch"
    private static final int CAPTION_HEIGHT = 10;

    // type constants for each of the dialog/statement types
    static final int TYPE_COMPUTES_FOR = 0;
    static final int TYPE_SLEEPS_FOR = 1;
    static final int TYPE_TOUCHES_MEMORY = 2;
    
    // the fields used by the various types
    private TaskGroup taskGroup;
    private String computeTime;
    private String computeTimeUnits;
    private String sleepTime;
    private String sleepTimeUnits;
    private String touchCount;
    private String touchCountUnits;
    private String touchRegion;
    private String touchRegionUnits;
    private String touchTimes;
    private String touchStride;
    private String touchStrideUnits;

    public ComputeStmt( Program program ){
        super( program );

        // default values
        computeTime = "1";
        computeTimeUnits = "seconds";
        sleepTime = "1";
        sleepTimeUnits = "seconds";
        touchCount = "0";
        touchCountUnits = "bytes";
        touchRegion = "0";
        touchRegionUnits = "bytes";
        touchTimes = "1";
        touchStride = "default";
        touchStrideUnits = "bytes";

        taskGroup = new TaskGroup( program );
    }

    // targetRow is unused
    public void paint( Graphics graphics, 
                       TaskRow sourceRow, 
                       TaskRow targetRow ){
        Vector sourceTargets = taskGroup.enumerate();

        if( paintUnknown( graphics, 
                          sourceTargets, 
                          sourceRow,
                          "variable tasks: compute",
                          isSelected() ) )
            return;

        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget =
                (SourceTarget)sourceTargets.elementAt( i );

            Task task = sourceRow.getTask( sourceTarget.source );
            Rectangle bounds = task.getGlobalBounds();
            if( isSelected() ){
                graphics.setColor( GraphicsUtility.getSelectedColor() );
                graphics.fillRect( bounds.x, bounds.y + bounds.height + 1, 
                                   bounds.width - 1, SELECTED_HEIGHT );
                graphics.setColor( Color.BLACK );
            }
            String label = "cmp";
            switch( type ){
            case TYPE_SLEEPS_FOR:
                label = " slp";
                break;
            case TYPE_TOUCHES_MEMORY:
                label = " tch";
                break;
            }
            if( sourceTarget.unknown )
                label = "   ?  ";

            graphics.drawString( label, bounds.x, 
                                 bounds.y + bounds.height + CAPTION_HEIGHT );
        }
    }
    
    public String toCode(){
        String code = "";
        if( type == TYPE_COMPUTES_FOR ){
            code = taskGroup.toCodeSource();
            code += " " + 
                Utility.wordForm( taskGroup.toCodeSource(), "computes" );
            code += " for " + computeTime + " " + 
                Utility.wordForm( computeTime, computeTimeUnits );
        }
        else if( type == TYPE_SLEEPS_FOR ){
            code = taskGroup.toCodeSource();
            code += " " + 
                Utility.wordForm( taskGroup.toCodeSource(), "sleeps" );
            code += " for " + sleepTime + " " + 
                Utility.wordForm( sleepTime, sleepTimeUnits );
        }
        else if( type == TYPE_TOUCHES_MEMORY ){
            String t = Utility.wordForm( taskGroup.toCodeSource(), "touches" );
            if( t.equals( "touche" ) )
                t = "touch";
            code = taskGroup.toCodeSource() + " " + t;
            if( !touchCount.equals( "" ) )
                code += " " + touchCount + " " + touchCountUnits + " of";
            code += " a " + touchRegion + " " + touchRegionUnits 
                + " memory region";
            if( !touchTimes.equals( "1" ) )
                code += touchTimes + " times";
            if( touchStride.equals( "random" ) )
                code += " with random stride";
            else if( !touchStride.equals( "default" ) )
                code += " with stride " + touchStride + " " + touchStrideUnits;
        }
        return code;
    }

    public void setType( int type ){
        this.type = type;
    }

    public void setTaskGroup( TaskGroup taskGroup ){
        this.taskGroup = taskGroup;
    }

    public void setTaskGroup( String taskGroupString ){
        taskGroup.setSource( taskGroupString ); 
    }

    public void setComputeTime( String computeTime ){
        this.computeTime = computeTime;
    }

    public void setComputeTimeUnits( String computeTimeUnits ){
        this.computeTimeUnits = computeTimeUnits;
    }

    public void setSleepTime( String sleepTime ){
        this.sleepTime = sleepTime;
    }

    public void setSleepTimeUnits( String sleepTimeUnits ){
        this.sleepTimeUnits = sleepTimeUnits;
    }

    public void setTouchCount( String touchCount ){
        this.touchCount = touchCount;
    }

    public void setTouchCountUnits( String touchCountUnits ){
        this.touchCountUnits = touchCountUnits;
    }

    public void setTouchRegion( String touchRegion ){
        this.touchRegion = touchRegion;
    }

    public void setTouchRegionUnits( String touchRegionUnits ){
        this.touchRegionUnits = touchRegionUnits;
    }

    public void setTouchTimes( String touchTimes ){
        this.touchTimes = touchTimes;
    }
    
    public void setTouchStride( String touchStride ){
        this.touchStride = touchStride;
    }

    public void setTouchStrideUnits( String touchStrideUnits ){
        this.touchStrideUnits = touchStrideUnits;
    }

    public int getType(){
        return type;
    }
    
    public TaskGroup getTaskGroup(){
        return taskGroup;
    }
    
    public String getComputeTime(){
        return computeTime;
    }

    public String getComputeTimeUnits(){
        return computeTimeUnits;
    }

    public String getSleepTime(){
        return sleepTime;
    }

    public String getSleepTimeUnits(){
        return sleepTimeUnits;
    }

    public String getTouchCount(){
        return touchCount;
    }

    public String getTouchCountUnits(){
        return touchCountUnits;
    }

    public String getTouchRegion(){
        return touchRegion;
    }

    public String getTouchRegionUnits(){
        return touchRegionUnits;
    }

    public String getTouchTimes(){
        return touchTimes;
    }

    public String getTouchStride(){
        return touchStride;
    }

    public String getTouchStrideUnits(){
        return touchStrideUnits;
    }

    // (xg,yg) is a point in global coordinates
    public boolean clickSelect( boolean isShiftOrCtrlClick, int xg, int yg ){
        boolean foundSelect = false;

        Vector sourceTargets = taskGroup.enumerate();
        if( sourceTargets.size() == 1 && 
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            return clickSelectUnknown( getTaskRow(),
                                       new Point( xg, yg ) );
        }
        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget = 
                (SourceTarget)sourceTargets.elementAt( i );
            TaskRow taskRow = getTaskRow();
            Task task = taskRow.getTask( sourceTarget.source );
            Rectangle bounds = task.getGlobalBounds();
            if( xg >= bounds.x &&
                xg <= bounds.x + bounds.width &&
                yg >= bounds.y + bounds.height &&
                yg <= bounds.y + bounds.height + CAPTION_HEIGHT ){
                if( !isSelected() ){
                    if( isShiftOrCtrlClick )
                        deselectNonComputeStmts();
                    else
                        program.setAllSelected( false );
                }
                setSelected( !isSelected() );
                program.updateState();
                foundSelect = true;
            }
        }
        return foundSelect;
    }

    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateComputeDialog();
    }
    
    public void deselectNonComputeStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof ComputeStmt) )
                component.setSelected( false );
        }
        
    }

    public void selectRegion( Rectangle marquee ){
        Vector sourceTargets = taskGroup.enumerate();
        
        if( sourceTargets.size() == 1 && 
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            selectRegionUnknown( getTaskRow(), 
                                 marquee );
            return;
        }

        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget = 
                (SourceTarget)sourceTargets.elementAt( i );
            TaskRow taskRow = getTaskRow();
            Task task = taskRow.getTask( sourceTarget.source );
            Rectangle bounds = task.getGlobalBounds();
            Rectangle stmtBounds = new Rectangle();
            stmtBounds.x = bounds.x;
            stmtBounds.width = bounds.width;
            stmtBounds.y = bounds.y;
            stmtBounds.height = bounds.height + CAPTION_HEIGHT;
            if( Utility.marqueeSelects( marquee, stmtBounds ) ){
                setSelected( true );
                return;
            }
            
        }
    }

    public void resize(){
        taskGroup.resize();
    }
    
}

