/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: multicast statement
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * MulticastStmt's correspond to a multicast_stmt and are
 * associated with a TaskRow. MulticastStmt includes both the
 * data representation as well as methods for its visual representation
 * and manipulation in the GUI.
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

public class MulticastStmt extends Stmt {

    private TaskGroup taskGroup;
    private boolean async;
    private String count;
    private boolean uniqueBuffer;
    private String messageSize;
    private String messageSizeUnits;
    private String alignment;
    private String alignmentUnits;
    private String alignmentMode;
    private String verificationOrTouching;
    private String buffer;

    public MulticastStmt( Program program ){
        super( program );

        // defaults
        async = false;
        count = "1";
        uniqueBuffer = false;
        messageSize = "0";
        messageSizeUnits = "bytes";
        alignment = "0";
        alignmentUnits = "bytes";
        alignmentMode = "unaligned";
        verificationOrTouching = "without data touching";
        buffer = "default";

        taskGroup = new TaskGroup( program );
    }

    public void paint( Graphics graphics,
                       TaskRow sourceRow,
                       TaskRow targetRow ){

        Vector sourceTargets = taskGroup.enumerate();

        Vector sourceTasks =
            SourceTarget.getSources( sourceTargets );

        if( paintUnknown( graphics,
                          sourceTargets,
                          sourceRow,
                          "variable tasks: multicast",
                          isSelected() ) )
            return;

        if( isSelected() ){
            Rectangle bounds = sourceRow.getGlobalBounds();
            graphics.setColor( GraphicsUtility.getSelectedColor() );
            graphics.fillRect( bounds.x + TaskRow.TASK_SPACING,
                               bounds.y + bounds.height,
                               bounds.width - TaskRow.TASK_SPACING*2,
                               Block.COMPONENT_SPACING );
            graphics.setColor( Color.BLACK );
        }

        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_BOLD );

        // draw source group arrows
        for( int i = 0; i < sourceTasks.size(); i++ ){
            Integer ti = (Integer)sourceTasks.elementAt( i );
            Task task = sourceRow.getTask( ti.intValue() );
            if (task == null)
                // bug workaround by SDP
                continue;
            Rectangle bounds = task.getGlobalBounds();
            graphicsUtility.drawArrow( 6, bounds.x + bounds.width/2,
                                       bounds.y + bounds.height,
                                       bounds.x + bounds.width/2,
                                       bounds.y + bounds.height +
                                       Block.COMPONENT_SPACING/2 );
        }
        // draw target group arrows
        Vector targetTasks =
            SourceTarget.getTargets( taskGroup.enumerate() );

        for( int i = 0; i < targetTasks.size(); i++ ){
            Integer ti = (Integer)targetTasks.elementAt( i );
            Task task = targetRow.getTask( ti.intValue() );
            if (task == null)
                // bug workaround by SDP
                continue;
            Rectangle bounds = task.getGlobalBounds();
            graphicsUtility.drawArrow( 6, bounds.x + bounds.width/2,
                                       bounds.y - Block.COMPONENT_SPACING/2,
                                       bounds.x + bounds.width/2,
                                       bounds.y );
        }
        // draw horizontal line
        Rectangle bounds = sourceRow.getGlobalBounds();
        graphics.drawLine( bounds.x + TaskRow.TASK_SPACING,
                           bounds.y+bounds.height+Block.COMPONENT_SPACING/2,
                           bounds.x+bounds.width - TaskRow.TASK_SPACING,
                           bounds.y+bounds.height+Block.COMPONENT_SPACING/2 );

        graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
    }

    // return the coNCePTuaL code
    public String toCode(){
        // source tasks
        String code = taskGroup.toCodeSource();

        // source async
        if( async )
            code += " asynchronously";

        // "multicasts" or "multicast"
        code += " " +
            Utility.wordForm( taskGroup.toCodeSource(), "multicasts" );

        // source message spec

        // messageCount
        if( count.equals( "1" ) )
            code += " a";
        else
            code += " " + count;

        // unique
        if( uniqueBuffer )
            code += " unique";

        // size
        if( !messageSize.equals( "0" ) ){
            code += " " + messageSize;

            // size units
            code += " " + Utility.toSingular( messageSizeUnits );
        }

        // alignment
        if( !alignmentMode.equals( "unaligned" ) ){
            code += " " + alignment + " " +
                Utility.toSingular( alignmentUnits ) + " " +
                alignmentMode;
        }

        // "message" or "messages"
        code += " " + Utility.wordForm( count, "messages" );

        // verification or data touching
        if( verificationOrTouching.equals( "with verification" ) ||
            verificationOrTouching.equals( "with data touching" ) )
            code += " " + verificationOrTouching;

        // buffer
        if( !buffer.equals( "default" ) )
            code += " from buffer " + buffer;

        // target tasks
        code += " to " + taskGroup.toCodeTarget();

        return code;
    }

    public void setSourceGroup( String taskGroupString ){
        taskGroup.setSource( taskGroupString );
    }

    public void setTargetGroup( String taskGroupString ){
        taskGroup.setTarget( taskGroupString );
    }

    // select/deselect if click (xg,yg) in global coordinates is
    // within the bounds for the MulticastStmt
    public boolean clickSelect( boolean isShiftOrCtrlClick, int xg, int yg ){
        boolean foundSelect = false;

        Vector sourceTargets = taskGroup.enumerate();
        if( sourceTargets.size() == 1 &&
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            return clickSelectUnknown( taskRow,
                                       new Point( xg, yg ) );
        }

        TaskRow taskRow = getTaskRow();
        Rectangle bounds = taskRow.getGlobalBounds();
        if( xg >= bounds.x &&
            xg <= bounds.x + bounds.width &&
            yg >= bounds.y + bounds.height &&
            yg <= bounds.y + bounds.height + Block.COMPONENT_SPACING ){
            if( !isSelected() )
                deselectNonMulticastStmts();
            else
                program.setAllSelected( false );
            setSelected( !isSelected() );
            program.updateState();
            foundSelect = true;
        }
        return foundSelect;
    }

    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateMulticastDialog();
    }

    public void deselectNonMulticastStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof MulticastStmt ) )
                component.setSelected( false );
        }
    }

    // accessor methods

    TaskGroup getTaskGroup(){
        return taskGroup;
    }

    boolean getAsync(){
        return async;
    }

    String getCount(){
        return count;
    }

    boolean getUniqueBuffer(){
        return uniqueBuffer;
    }

    String getMessageSize(){
        return messageSize;
    }

    String getMessageSizeUnits(){
        return messageSizeUnits;
    }

    String getAlignment(){
        return alignment;
    }

    String getAlignmentUnits(){
        return alignmentUnits;
    }

    String getAlignmentMode(){
        return alignmentMode;
    }

    String getVerificationOrTouching(){
        return verificationOrTouching;
    }

    String getBuffer(){
        return buffer;
    }

    // mutator methods

    void setAsync( boolean async ){
        this.async = async;
    }

    void setCount( String count ){
        this.count = count;
    }

    void setUniqueBuffer( boolean uniqueBuffer ){
        this.uniqueBuffer = uniqueBuffer;
    }

    void setMessageSize( String messageSize ){
        this.messageSize = messageSize;
    }

    void setMessageSizeUnits( String messageSizeUnits ){
        this.messageSizeUnits = messageSizeUnits;
    }

    void setAlignment( String alignment ){
        this.alignment = alignment;
    }

    void setAlignmentUnits( String alignmentUnits ){
        this.alignmentUnits = alignmentUnits;
    }

    void setAlignmentMode( String alignmentMode ){
        this.alignmentMode = alignmentMode;
    }

    void setVerificationOrTouching( String verificationOrTouching ){
        this.verificationOrTouching = verificationOrTouching;
    }

    void setBuffer( String buffer ){
        this.buffer = buffer;
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
        bounds.height = Block.COMPONENT_SPACING;

        if( Utility.marqueeSelects( marquee, bounds ) )
            setSelected( true );
    }

    // resize the task group this needs to be done after num_tasks is
    // changed
    public void resize(){
        taskGroup.resize();
    }

}
