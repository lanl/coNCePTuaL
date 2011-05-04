/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: reduce statement
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * ReduceStmt corresponds to a reduce_stmt and is associated with a
 * TaskRow. ReduceStmt includes both the data representation as
 * well as methods for its visual representation and manipulation in
 * the GUI.
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

public class ReduceStmt extends Stmt {

    // source and target task
    private TaskGroup taskGroup;

    // source fields
    private String sourceCount;
    private boolean sourceUniqueBuffer;
    private String sourceAlignment;
    private String sourceAlignmentUnits;
    private String sourceAlignmentMode;
    private String sourceUnits;
    private boolean sourceDataTouching;
    private String sourceBuffer;

    // target fields
    private String targetCount;
    private boolean targetUniqueBuffer;
    private String targetAlignment;
    private String targetAlignmentUnits;
    private String targetAlignmentMode;
    private String targetUnits;
    private boolean targetDataTouching;
    private String targetBuffer;

    public ReduceStmt( Program program ){
        super( program );

        // defaults
        sourceCount = "1";
        sourceUniqueBuffer = false;
        sourceAlignment = "0";
        sourceAlignmentUnits = "bytes";
        sourceAlignmentMode = "unaligned";
        sourceUnits = "doublewords";
        sourceDataTouching = false;
        sourceBuffer = "default";
        targetCount = "1";
        targetUniqueBuffer = false;
        targetAlignment = "0";
        targetAlignmentUnits = "bytes";
        targetAlignmentMode = "unaligned";
        targetUnits = "doublewords";
        targetDataTouching = false;
        targetBuffer = "default";

        taskGroup = new TaskGroup( program );

    }

    public void paint( Graphics graphics,
                       TaskRow sourceRow,
                       TaskRow targetRow ){

        Vector sourceTargets = taskGroup.enumerate_ignoring_targets();

        Vector sourceTasks = SourceTarget.getSources( sourceTargets );

        if( paintUnknown( graphics,
                          sourceTargets,
                          sourceRow,
                          "variable tasks: reduce",
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
        Vector targetTasks = SourceTarget.getSources( taskGroup.enumerate_targets_as_sources() );
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

        // reduce or reduces
        code += " " +
            Utility.wordForm( taskGroup.toCodeSource(), "reduces" );

        // count
        if( sourceCount.equals( "1" ) )
            code += " a";
        else
            code += " " + sourceCount;

        // unique
        if( sourceUniqueBuffer )
            code += " unique";

        // alignment
        if( !sourceAlignmentMode.equals( "unaligned" ) ){
            code += " " + sourceAlignment + " " +
                Utility.toSingular( sourceAlignmentUnits ) + " " +
                sourceAlignmentMode;
        }

        // units
        code += " " + Utility.wordForm( sourceCount, sourceUnits );

        // data touching
        if( sourceDataTouching )
            code += " with data touching";

        // buffer
        if( !sourceBuffer.equals( "default" ) )
            code += " from buffer " + sourceBuffer;

        // target tasks
        code += " to " + taskGroup.toCodeTarget();

        if( sourceCount.equals( targetCount ) &&
            sourceUniqueBuffer == targetUniqueBuffer &&
            sourceAlignmentMode.equals( targetAlignmentMode ) &&
            sourceAlignment.equals( targetAlignment ) &&
            sourceAlignmentUnits.equals( targetAlignmentUnits ) &&
            sourceUnits.equals( targetUnits ) &&
            sourceDataTouching == targetDataTouching )
            return code;

        code += " who receives the result as";

        // count
        if( targetCount.equals( "1" ) )
            code += " a";
        else
            code += " " + targetCount;

        // unique
        if( targetUniqueBuffer )
            code += " unique";

        // alignment
        if( !targetAlignmentMode.equals( "unaligned" ) ){
            code += " " + targetAlignment + " " +
                Utility.toSingular( targetAlignmentUnits ) + " " +
                targetAlignmentMode;
        }

        // units
        code += " " + Utility.wordForm( targetCount, targetUnits );

        // data touching
        if( targetDataTouching )
            code += " with data touching";

        // buffer
        if( !targetBuffer.equals( "default" ) )
            code += " into buffer " + targetBuffer;

        return code;
    }

    public void setSourceGroup( String taskGroupString ){
        taskGroup.setSource( taskGroupString );
    }

    public void setTargetGroup( String taskGroupString ){
        taskGroup.setTarget( taskGroupString );
    }

    // select/deselect the ReduceStmt if click (xg, yg) in global coordinates
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
            yg <= bounds.y + bounds.height + Block.COMPONENT_SPACING ){
            if( !isSelected() )
                deselectNonReduceStmts();
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
        program.updateReduceDialog();
    }

    public void deselectNonReduceStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof ReduceStmt) )
                component.setSelected( false );
        }
    }

    // accessor methods

    TaskGroup getTaskGroup(){
        return taskGroup;
    }

    String getSourceCount(){
        return sourceCount;
    }

    boolean getSourceUniqueBuffer(){
        return sourceUniqueBuffer;
    }

    String getSourceAlignment(){
        return sourceAlignment;
    }

    String getSourceAlignmentUnits(){
        return sourceAlignmentUnits;
    }

    String getSourceAlignmentMode(){
        return sourceAlignmentMode;
    }

    String getSourceUnits(){
        return sourceUnits;
    }

    boolean getSourceDataTouching(){
        return sourceDataTouching;
    }

    String getSourceBuffer(){
        return sourceBuffer;
    }

    String getTargetCount(){
        return targetCount;
    }

    boolean getTargetUniqueBuffer(){
        return targetUniqueBuffer;
    }

    String getTargetAlignment(){
        return targetAlignment;
    }

    String getTargetAlignmentUnits(){
        return targetAlignmentUnits;
    }

    String getTargetAlignmentMode(){
        return targetAlignmentMode;
    }

    String getTargetUnits(){
        return targetUnits;
    }

    boolean getTargetDataTouching(){
        return targetDataTouching;
    }

    String getTargetBuffer(){
        return targetBuffer;
    }

    // mutator methods

    void setSourceCount( String sourceCount ){
        this.sourceCount = sourceCount;
    }

    void setSourceUniqueBuffer( boolean sourceUniqueBuffer ){
        this.sourceUniqueBuffer = sourceUniqueBuffer;
    }

    void setSourceAlignment( String sourceAlignment ){
        this.sourceAlignment = sourceAlignment;
    }

    void setSourceAlignmentUnits( String sourceAlignmentUnits ){
        this.sourceAlignmentUnits = sourceAlignmentUnits;
    }

    void setSourceAlignmentMode( String sourceAlignmentMode ){
        this.sourceAlignmentMode = sourceAlignmentMode;
    }

    void setSourceUnits( String sourceUnits ){
        this.sourceUnits = sourceUnits;
    }

    void setSourceDataTouching( boolean sourceDataTouching ){
        this.sourceDataTouching = sourceDataTouching;
    }

    void setSourceBuffer( String sourceBuffer){
        this.sourceBuffer = sourceBuffer;
    }

    void setTargetCount( String targetCount ){
        this.targetCount = targetCount;
    }

    void setTargetUniqueBuffer( boolean targetUniqueBuffer ){
        this.targetUniqueBuffer = targetUniqueBuffer;
    }

    void setTargetAlignment( String targetAlignment ){
        this.targetAlignment = targetAlignment;
    }

    void setTargetAlignmentUnits( String targetAlignmentUnits ){
        this.targetAlignmentUnits = targetAlignmentUnits;
    }

    void setTargetAlignmentMode( String targetAlignmentMode ){
        this.targetAlignmentMode = targetAlignmentMode;
    }

    void setTargetUnits( String targetUnits ){
        this.targetUnits = targetUnits;
    }

    void setTargetDataTouching( boolean targetDataTouching ){
        this.targetDataTouching = targetDataTouching;
    }

    void setTargetBuffer( String targetBuffer ){
        this.targetBuffer = targetBuffer;
    }

    // select this ReduceStmt if it is sufficiently enclosed by the
    // selection marquee
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

    public void resize(){
        taskGroup.resize();
    }

}
