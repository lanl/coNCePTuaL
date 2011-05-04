/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: communication statement
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * CommunicationStmt's correspond to a send_stmt or receive_stmt and are
 * associated with a TaskRow. CommunicationStmt includes both the
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

public class CommunicationStmt extends Stmt implements Cloneable {

    // the default values set when clicking "Make Default"
    // in the CommunicationDialog
    // each new CommunicationStmt defaults to these values
    // except when the CommunicationStmt is being read from a file
    private static final String  INITIAL_MESSAGE_COUNT = "1";
    private static final String  INITIAL_MESSAGE_SIZE = "0";
    private static final String  INITIAL_MESSAGE_SIZE_UNITS = "bytes";

    private static final boolean INITIAL_SOURCE_ASYNC = false;
    private static final String  INITIAL_SOURCE_VERIFICATION_OR_TOUCHING = "without verification";
    private static final String  INITIAL_SOURCE_ALIGNMENT = "0";
    private static final String  INITIAL_SOURCE_ALIGNMENT_UNITS = "bytes";
    private static final String  INITIAL_SOURCE_ALIGNMENT_MODE = "unaligned";
    private static final String  INITIAL_SOURCE_BUFFER = "default";
    private static final boolean INITIAL_SOURCE_UNIQUE_BUFFER = false;

    private static final boolean INITIAL_TARGET_ASYNC = false;
    private static final String  INITIAL_TARGET_VERIFICATION_OR_TOUCHING = "without verification";
    private static final String  INITIAL_TARGET_ALIGNMENT = "0";
    private static final String  INITIAL_TARGET_ALIGNMENT_UNITS = "bytes";
    private static final String  INITIAL_TARGET_ALIGNMENT_MODE = "unaligned";
    private static final String  INITIAL_TARGET_BUFFER = "default";
    private static final boolean INITIAL_TARGET_UNIQUE_BUFFER = false;

    private static String defaultMessageCount =
        INITIAL_MESSAGE_COUNT;
    private static String defaultMessageSize =
        INITIAL_MESSAGE_SIZE;
    private static String defaultMessageSizeUnits =
        INITIAL_MESSAGE_SIZE_UNITS;

    private static boolean defaultSourceAsync =
        INITIAL_SOURCE_ASYNC;
    private static String defaultSourceVerificationOrTouching =
        INITIAL_SOURCE_VERIFICATION_OR_TOUCHING;
    private static String defaultSourceAlignment =
        INITIAL_SOURCE_ALIGNMENT;
    private static String defaultSourceAlignmentUnits =
        INITIAL_SOURCE_ALIGNMENT_UNITS;
    private static String defaultSourceAlignmentMode =
        INITIAL_SOURCE_ALIGNMENT_MODE;
    private static String defaultSourceBuffer =
        INITIAL_SOURCE_BUFFER;
    private static boolean defaultSourceUniqueBuffer =
        INITIAL_SOURCE_UNIQUE_BUFFER;

    private static boolean defaultTargetAsync =
        INITIAL_TARGET_ASYNC;
    private static String defaultTargetVerificationOrTouching =
        INITIAL_TARGET_VERIFICATION_OR_TOUCHING;
    private static String defaultTargetAlignment =
        INITIAL_TARGET_ALIGNMENT;
    private static String defaultTargetAlignmentUnits =
        INITIAL_TARGET_ALIGNMENT_UNITS;
    private static String defaultTargetAlignmentMode =
        INITIAL_TARGET_ALIGNMENT_MODE;
    private static String defaultTargetBuffer =
        INITIAL_TARGET_BUFFER;
    private static boolean defaultTargetUniqueBuffer =
        INITIAL_TARGET_UNIQUE_BUFFER;

    // the source and target tasks
    private TaskGroup taskGroup;

    private String messageCount;
    private String messageSize;
    private String messageSizeUnits;

    // source fields
    private boolean sourceAsync;
    private String sourceVerificationOrTouching;
    private String sourceAlignment;
    private String sourceAlignmentUnits;
    private String sourceAlignmentMode;
    private String sourceBuffer;
    private boolean sourceUniqueBuffer;

    // target fields
    private boolean targetAsync;
    private String targetVerificationOrTouching;
    private String targetAlignment;
    private String targetAlignmentUnits;
    private String targetAlignmentMode;
    private String targetBuffer;
    private boolean targetUniqueBuffer;

    private boolean unsuspecting;

    // receiving row for split receive/send
    private TaskRow targetRow;

    // a threshold that determines how close a click has to
    // be to be registered as a select
    private static final double SELECT_DISTANCE_THRESHOLD = 40;

    public CommunicationStmt( Program program ){
        super( program );

        // defaults
        taskGroup = new TaskGroup( program );
        taskGroup.setSource( 0 );
        taskGroup.setTarget( 1 );

        unsuspecting = false;

        messageCount = defaultMessageCount;
        messageSize = defaultMessageSize;
        messageSizeUnits = defaultMessageSizeUnits;

        sourceAsync = defaultSourceAsync;
        sourceVerificationOrTouching = defaultSourceVerificationOrTouching;
        sourceAlignment = defaultSourceAlignment;
        sourceAlignmentUnits = defaultSourceAlignmentUnits;
        sourceAlignmentMode = defaultSourceAlignmentMode;
        sourceBuffer = defaultSourceBuffer;
        sourceUniqueBuffer = defaultSourceUniqueBuffer;

        targetAsync = defaultTargetAsync;
        targetVerificationOrTouching = defaultTargetVerificationOrTouching;
        targetAlignment = defaultTargetAlignment;
        targetAlignmentUnits = defaultTargetAlignmentUnits;
        targetAlignmentMode = defaultTargetAlignmentMode;
        targetBuffer = defaultTargetBuffer;
        targetUniqueBuffer = defaultTargetUniqueBuffer;

        targetRow = null;
    }

    // methods for setting the various fields

    public void setSourceGroup( String sourceGroup ){
        taskGroup.setSource( sourceGroup );
    }

    public void setTargetGroup( String targetGroup ){
        taskGroup.setTarget( targetGroup );
    }

    public void setMessageCount( String messageCount ){
        this.messageCount = messageCount;
    }

    public void setMessageSize( String messageSize ){
        this.messageSize = messageSize;
    }

    public void setMessageSizeUnits( String messageSizeUnits ){
        this.messageSizeUnits = messageSizeUnits;
    }

    public void setUnsuspecting( boolean unsuspecting ){
        this.unsuspecting = unsuspecting;
    }

    public void setSourceAsync( boolean sourceAsync ){
        this.sourceAsync = sourceAsync;
    }

    public void setSourceVerificationOrTouching( String sourceVerificationOrTouching ){
        this.sourceVerificationOrTouching = sourceVerificationOrTouching;
    }

    public void setSourceAlignment( String sourceAlignment ){
        this.sourceAlignment = sourceAlignment;
    }

    public void setSourceAlignmentUnits( String sourceAlignmentUnits ){
        this.sourceAlignmentUnits = sourceAlignmentUnits;
    }

    public void setSourceAlignmentMode( String sourceAlignmentMode ){
        this.sourceAlignmentMode = sourceAlignmentMode;
    }

    public void setSourceBuffer( String sourceBuffer ){
        this.sourceBuffer = sourceBuffer;
    }

    public void setSourceUniqueBuffer( boolean sourceUniqueBuffer ){
        this.sourceUniqueBuffer = sourceUniqueBuffer;
    }

    public void setTargetAsync( boolean targetAsync ){
        this.targetAsync = targetAsync;
    }

    public void setTargetVerificationOrTouching( String targetVerificationOrTouching ){
        this.targetVerificationOrTouching = targetVerificationOrTouching;
    }

    public void setTargetAlignment( String targetAlignment ){
        this.targetAlignment = targetAlignment;
    }

    public void setTargetAlignmentUnits( String targetAlignmentUnits ){
        this.targetAlignmentUnits = targetAlignmentUnits;
    }

    public void setTargetAlignmentMode( String targetAlignmentMode ){
        this.targetAlignmentMode = targetAlignmentMode;
    }

    public void setTargetBuffer( String targetBuffer ){
        this.targetBuffer = targetBuffer;
    }

    public void setTargetUniqueBuffer( boolean targetUniqueBuffer ){
        this.targetUniqueBuffer = targetUniqueBuffer;
    }


    public void setTargetRow( TaskRow targetRow ){
        this.targetRow = targetRow;
    }


    // acessor methods for the various fields

    public TaskGroup getTaskGroup(){
        return taskGroup;
    }

    public String getSourceGroup(){
        return taskGroup.toCodeSource();
    }

    public String getTargetGroup(){
        return taskGroup.toCodeTarget();
    }

    public String getMessageCount(){
        return messageCount;
    }

    public String getMessageSize(){
        return messageSize;
    }

    public String getMessageSizeUnits(){
        return messageSizeUnits;
    }

    public boolean getSourceAsync(){
        return sourceAsync;
    }

    public String getSourceVerificationOrTouching(){
        return sourceVerificationOrTouching;
    }

    public String getSourceAlignment(){
        return sourceAlignment;
    }

    public String getSourceAlignmentUnits(){
        return sourceAlignmentUnits;
    }

    public String getSourceAlignmentMode(){
        return sourceAlignmentMode;
    }

    public String getSourceBuffer(){
        return sourceBuffer;
    }

    public boolean getSourceUniqueBuffer(){
        return sourceUniqueBuffer;
    }

    public boolean getTargetAsync(){
        return targetAsync;
    }

    public String getTargetVerificationOrTouching(){
        return targetVerificationOrTouching;
    }

    public String getTargetAlignment(){
        return targetAlignment;
    }

    public String getTargetAlignmentUnits(){
        return targetAlignmentUnits;
    }

    public String getTargetAlignmentMode(){
        return targetAlignmentMode;
    }

    public String getTargetBuffer(){
        return targetBuffer;
    }

    public boolean getTargetUniqueBuffer(){
        return targetUniqueBuffer;
    }

    public TaskRow getTargetRow(){
        return targetRow;
    }

    public boolean getUnsuspecting(){
        return unsuspecting;
    }

    // paint the CommunicationStmt as an arrow from the appropriate
    // task(s) in sourceRow to task(s) in targetRow
    public void paint( Graphics graphics,
                       TaskRow sourceRow,
                       TaskRow targetRow ){

        // because this is a CommunicationStmt, targetRow must not be null
        assert targetRow != null;

        // get the list of sources and targets
        Vector sourceTargets = taskGroup.enumerate();

        if( paintUnknown( graphics,
                          sourceTargets,
                          sourceRow,
                          "variable tasks: point to point communication",
                          isSelected() ) )
            return;

        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );

        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget =
                (SourceTarget)sourceTargets.elementAt( i );

            Task sourceTask = sourceRow.getTask( sourceTarget.source );

            Task targetTask;
            if( this.targetRow != null )
                targetTask = this.targetRow.getTask( sourceTarget.target );
            else
                targetTask = targetRow.getTask( sourceTarget.target );
            if( sourceTask == null || targetTask == null )
                return;

            // calculate the endpoints
            Rectangle sourceBounds = sourceTask.getGlobalBounds();
            Rectangle targetBounds = targetTask.getGlobalBounds();
            int x1 = sourceBounds.x + sourceBounds.width/2;
            int y1 = sourceBounds.y + sourceBounds.height;
            int x2 = targetBounds.x + targetBounds.width/2;
            int y2 = targetBounds.y;

            // highlight the edge if selected
            if( isSelected() ){
                graphics.setColor( GraphicsUtility.getSelectedColor() );
                graphicsUtility.setStroke( GraphicsUtility.STROKE_HIGHLIGHT );
                graphicsUtility.drawLine( x1, y1, x2, y2 );
                graphics.setColor( Color.black );
                graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
            }
            graphicsUtility.drawArrow( 6, x1, y1, x2, y2 );
        }
    }

    // this method is called to output the coNCePTuaL code corresponding to a
    // receive_stmt - it reverses the ordering of source and target
    // and their attributes
    public String toCodeReceive(){
        // target tasks
        String code = taskGroup.toCodeTarget();

        // target async
        if( targetAsync )
            code += " asynchronously";

        // "receives" or "receive"
        code += Utility.wordForm( taskGroup.toCodeTarget(), " receives" );

        // target message spec

        // messageCount
        if( messageCount.equals( "1" ) )
            code += " a";
        else
            code += " " + messageCount;

        // unique
        if( targetUniqueBuffer )
            code += " unique";

        // size
        if( !messageSize.equals( "0" ) ){
            code += " " + messageSize;

            // size units
            code += " " + Utility.toSingular( messageSizeUnits );
        }

        // alignment
        if( !targetAlignmentMode.equals( "unaligned" ) ){
            code += " " + targetAlignment + " " +
                Utility.toSingular( targetAlignmentUnits ) + " " +
                targetAlignmentMode;
        }

        // "message" or "messages"
        code += " " + Utility.wordForm( messageCount, "messages" );

        // verification or data touching
        if( targetVerificationOrTouching.equals( "with verification" ) ||
            targetVerificationOrTouching.equals( "with data touching" ) )
            code += " " + targetVerificationOrTouching;

        // buffer
        if( !targetBuffer.equals( "default" ) )
            code += " from buffer " + targetBuffer;

        // from source
        code += " from " + taskGroup.toCodeSource();

        return code;
    }

    // this method is called to output the coNCePTuaL code
    // corresponding to a send_stmt
    public String toCode(){
        // source tasks
        String code = taskGroup.toCodeSource();

        // source async
        if( sourceAsync )
            code += " asynchronously";

        // "sends" or "send"
        code += " " + Utility.wordForm( taskGroup.toCodeSource(), "sends" );

        // source message spec

        // messageCount
        if( messageCount.equals( "1" ) )
            code += " a";
        else
            code += " " + messageCount;

        // unique
        if( sourceUniqueBuffer )
            code += " unique";

        // size
        if( !messageSize.equals( "0" ) ){
            code += " " + messageSize;

            // size units
            code += " " + Utility.toSingular( messageSizeUnits );
        }

        // alignment
        if( !sourceAlignmentMode.equals( "unaligned" ) ){
            code += " " + sourceAlignment + " " +
                Utility.toSingular( sourceAlignmentUnits ) + " " +
                sourceAlignmentMode;
        }

        // "message" or "messages"
        code += " " + Utility.wordForm( messageCount, "messages" );

        // verification or data touching
        if( sourceVerificationOrTouching.equals( "with verification" ) ||
            sourceVerificationOrTouching.equals( "with data touching" ) )
            code += " " + sourceVerificationOrTouching;

        // buffer
        if( !sourceBuffer.equals( "default" ) )
            code += " from buffer " + sourceBuffer;


        code += " to";

        // unsuspecting
        if( targetRow != null )
            code += " unsuspecting ";

        code += " " + taskGroup.toCodeTarget();

        // the remaining code only needs to be printed when the message receive fields differ from the send ones
        if( targetRow != null ||
            (sourceAsync == targetAsync &&
            sourceUniqueBuffer == targetUniqueBuffer &&
            sourceAlignmentMode.equals( targetAlignmentMode ) &&
            sourceAlignment.equals( targetAlignment ) &&
            sourceAlignmentUnits.equals( targetAlignmentUnits ) &&
            sourceVerificationOrTouching.equals( targetVerificationOrTouching ) &&
            sourceBuffer.equals( targetBuffer )) )
            return code;


        // "receives it" or "receive it"
        code += " who " + Utility.wordForm( taskGroup.toCodeTarget(), "receives" ) + " it";

        // target message spec

        // async
        if( targetAsync )
            code += " asynchronously";
        else if( sourceAsync != targetAsync )
            code += " synchronously";

        if( targetUniqueBuffer ||
            targetAlignmentMode.equals( "aligned" ) ||
            targetAlignmentMode.equals( "misaligned" ) ){

            code += " as";

            // "a" or nothing
            if( Utility.wordForm( messageCount, "messages" ).equals( "message" ) )
                code += " a";

            // unique
            if( targetUniqueBuffer )
                code += " unique";

            // alignment
            if( !targetAlignmentMode.equals( "unaligned" ) ){
                code += " " + targetAlignment + " " +
                    Utility.toSingular( targetAlignmentUnits ) + " " +
                    targetAlignmentMode;
            }

            // "message" or "messages"
            code += " " + Utility.wordForm( messageCount, "messages" );
        }

        // verification or data touching
        if( targetVerificationOrTouching.equals( " with verification" ) ||
            targetVerificationOrTouching.equals( " with data touching" ) )
            code += " " + targetVerificationOrTouching;

        // buffer
        if( !targetBuffer.equals( "default" ) )
            code += " into buffer " + targetBuffer;

        return code;
    }

    // this method processes a click (x,y) passed to it in
    // global coordinates and determines if the CommunicationStmt should
    // be selected in response to it
    public boolean clickSelect( boolean isShiftOrCtrlClick, TaskRow sourceRow,
                                TaskRow targetRow, int x, int y ){
        assert targetRow != null;

        boolean foundSelect = false;

        Vector sourceTargets = taskGroup.enumerate();

        double distance = Double.POSITIVE_INFINITY;

        // draw unknown source and target
        if( sourceTargets.size() == 1 &&
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            return clickSelectUnknown( sourceRow,
                                       new Point( x, y ) );
        }
        else{
            // find the distance to the closest edge

            for( int i = 0; i < sourceTargets.size(); i++ ){
                SourceTarget sourceTarget =
                    (SourceTarget)sourceTargets.elementAt( i );

                Task sourceTask = sourceRow.getTask( sourceTarget.source );

                Task targetTask;
                if( this.targetRow != null )
                    targetTask = this.targetRow.getTask( sourceTarget.target );
                else
                    targetTask = targetRow.getTask( sourceTarget.target );

                Rectangle sourceBounds = sourceTask.getGlobalBounds();
                Rectangle targetBounds = targetTask.getGlobalBounds();
                int x1 = sourceBounds.x + sourceBounds.width/2;
                int y1 = sourceBounds.y + sourceBounds.height;
                int x2 = targetBounds.x + targetBounds.width/2;
                int y2 = targetBounds.y;
                distance =
                    Math.min( distance,
                              (Math.sqrt( (x1-x)*(x1-x) + (y1-y)*(y1-y) ) +
                               Math.sqrt( (x2-x)*(x2-x) + (y2-y)*(y2-y) ) -
                               Math.sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2)))*
                              Math.sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2)));
            }
        }
        if( distance < SELECT_DISTANCE_THRESHOLD ){
            if( !isSelected() ){
                if( isShiftOrCtrlClick )
                    deselectNonCommunicationStmts();
                else
                    program.setAllSelected( false );
            }
            setSelected( !isSelected() );
            foundSelect = true;
            sourceRow.repaint();
        }
        return foundSelect;
    }

    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateCommunicationDialog();
        program.updateState();
    }

    public void deselectNonCommunicationStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof CommunicationStmt) )
                component.setSelected( false );
        }

    }

    // called when a selection rectangle is being dragged
    // selects CommunicationStmts if they are contained within marquee
    public void selectRegion( Rectangle marquee ){

        TaskRow sourceRow = getTaskRow();
        Block block = (Block)sourceRow.getParent();
        TaskRow targetRow = this.targetRow;
        if( targetRow == null )
            targetRow = (TaskRow)block.componentAt( sourceRow.getID() + 1 );

        Vector sourceTargets = taskGroup.enumerate();

        if( sourceTargets.size() == 1 &&
            ((SourceTarget)sourceTargets.elementAt( 0 )).unknown ){
            selectRegionUnknown( sourceRow,
                                 marquee );
            return;
        }

        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget =
                (SourceTarget)sourceTargets.elementAt( i );

            Task sourceTask = sourceRow.getTask( sourceTarget.source );

            Task targetTask = targetRow.getTask( sourceTarget.target );

            Rectangle sourceBounds = sourceTask.getGlobalBounds();
            Rectangle targetBounds = targetTask.getGlobalBounds();
            Point p1 = new Point( sourceBounds.x + sourceBounds.width/2,
                                  sourceBounds.y + sourceBounds.height );
            Point p2 = new Point( targetBounds.x + targetBounds.width/2,
                                  targetBounds.y );

            if( Utility.contains( marquee, p1 ) ||
                Utility.contains( marquee, p2 ) ||
                Utility.intersects( p1, p2, marquee ) )
                setSelected( true );
        }
    }

    // re-enumerate the task group
    // usually called after num_tasks has changed
    public void resize(){
        taskGroup.resize();
    }

    // the following methods set the default values
    // called after clicking "Make Default" in the CommunicationDialog

    public static void setDefaultMessageCount( String _defaultMessageCount ){
        defaultMessageCount = _defaultMessageCount;
    }

    public static void setDefaultMessageSize( String _defaultMessageSize ){
        defaultMessageSize = _defaultMessageSize;
    }

    public static void setDefaultMessageSizeUnits( String _defaultMessageSizeUnits ){
        defaultMessageSizeUnits = _defaultMessageSizeUnits;
    }

    public static void setDefaultSourceAsync( boolean _defaultSourceAsync ){
        defaultSourceAsync = _defaultSourceAsync;
    }

    public static void setDefaultSourceVerificationOrTouching( String _defaultSourceVerificationOrTouching ){
        defaultSourceVerificationOrTouching = _defaultSourceVerificationOrTouching;
    }

    public static void setDefaultSourceAlignment( String _defaultSourceAlignment ){
        defaultSourceAlignment = _defaultSourceAlignment;
    }

    public static void setDefaultSourceAlignmentUnits( String _defaultSourceAlignmentUnits ){
        defaultSourceAlignmentUnits = _defaultSourceAlignmentUnits;
    }

    public static void setDefaultSourceAlignmentMode( String _defaultSourceAlignmentMode ){
        defaultSourceAlignmentMode = _defaultSourceAlignmentMode;
    }

    public static void setDefaultSourceBuffer( String _defaultSourceBuffer ){
        defaultSourceBuffer = _defaultSourceBuffer;

    }

    public static void setDefaultSourceUniqueBuffer( boolean _defaultSourceUniqueBuffer ){
        defaultSourceUniqueBuffer = _defaultSourceUniqueBuffer;
    }

    public static void setDefaultTargetAsync( boolean _defaultTargetAsync ){
        defaultTargetAsync = _defaultTargetAsync;

    }

    public static void setDefaultTargetVerificationOrTouching( String _defaultTargetVerificationOrTouching ){
        defaultTargetVerificationOrTouching = _defaultTargetVerificationOrTouching;
    }

    public static void setDefaultTargetAlignment( String _defaultTargetAlignment ){
        defaultTargetAlignment = _defaultTargetAlignment;
    }

    public static void setDefaultTargetAlignmentUnits( String _defaultTargetAlignmentUnits ){
        defaultTargetAlignmentUnits = _defaultTargetAlignmentUnits;
    }

    public static void setDefaultTargetAlignmentMode( String _defaultTargetAlignmentMode ){
        defaultTargetAlignmentMode = _defaultTargetAlignmentMode;
    }

    public static void setDefaultTargetBuffer( String _defaultTargetBuffer ){
        defaultTargetBuffer = _defaultTargetBuffer;
    }

    public static void setDefaultTargetUniqueBuffer( boolean _defaultTargetUniqueBuffer ){
        defaultTargetUniqueBuffer = _defaultTargetUniqueBuffer;
    }

    public Object clone() throws CloneNotSupportedException {
        CommunicationStmt stmt = (CommunicationStmt)super.clone();
        stmt.targetRow = null;
        stmt.taskGroup = (TaskGroup)stmt.taskGroup.clone();
        return stmt;
    }

    // this method is called in ProgramReader and is used
    // to override any values that may have been set by
    // clicking "Make Default"
    public void clear(){
        messageCount = INITIAL_MESSAGE_COUNT;
        messageSize = INITIAL_MESSAGE_SIZE;
        messageSizeUnits = INITIAL_MESSAGE_SIZE_UNITS;

        sourceAsync = INITIAL_SOURCE_ASYNC;
        sourceVerificationOrTouching = INITIAL_SOURCE_VERIFICATION_OR_TOUCHING;
        sourceAlignment = INITIAL_SOURCE_ALIGNMENT;
        sourceAlignmentUnits = INITIAL_SOURCE_ALIGNMENT_UNITS;
        sourceAlignmentMode = INITIAL_SOURCE_ALIGNMENT_MODE;
        sourceBuffer = INITIAL_SOURCE_BUFFER;
        sourceUniqueBuffer = INITIAL_SOURCE_UNIQUE_BUFFER;

        targetAsync = INITIAL_TARGET_ASYNC;
        targetVerificationOrTouching = INITIAL_TARGET_VERIFICATION_OR_TOUCHING;
        targetAlignment = INITIAL_TARGET_ALIGNMENT;
        targetAlignmentUnits = INITIAL_TARGET_ALIGNMENT_UNITS;
        targetAlignmentMode = INITIAL_TARGET_ALIGNMENT_MODE;
        targetBuffer = INITIAL_TARGET_BUFFER;
        targetUniqueBuffer = INITIAL_TARGET_UNIQUE_BUFFER;
    }

    public static void resetDefaults(){
        defaultMessageCount = INITIAL_MESSAGE_COUNT;
        defaultMessageSize = INITIAL_MESSAGE_SIZE;
        defaultMessageSizeUnits = INITIAL_MESSAGE_SIZE_UNITS;

        defaultSourceAsync = INITIAL_SOURCE_ASYNC;
        defaultSourceVerificationOrTouching =
            INITIAL_SOURCE_VERIFICATION_OR_TOUCHING;
        defaultSourceAlignment = INITIAL_SOURCE_ALIGNMENT;
        defaultSourceAlignmentUnits = INITIAL_SOURCE_ALIGNMENT_UNITS;
        defaultSourceAlignmentMode = INITIAL_SOURCE_ALIGNMENT_MODE;
        defaultSourceBuffer = INITIAL_SOURCE_BUFFER;
        defaultSourceUniqueBuffer = INITIAL_SOURCE_UNIQUE_BUFFER;

        defaultTargetAsync = INITIAL_TARGET_ASYNC;
        defaultTargetVerificationOrTouching =
            INITIAL_TARGET_VERIFICATION_OR_TOUCHING;
        defaultTargetAlignment = INITIAL_TARGET_ALIGNMENT;
        defaultTargetAlignmentUnits = INITIAL_TARGET_ALIGNMENT_UNITS;
        defaultTargetAlignmentMode = INITIAL_TARGET_ALIGNMENT_MODE;
        defaultTargetBuffer = INITIAL_TARGET_BUFFER;
        defaultTargetUniqueBuffer = INITIAL_TARGET_UNIQUE_BUFFER;
    }

}
