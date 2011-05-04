/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: loop
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class holds a single coNCePTual loop and as a Block, is a
 * container for other components. The loop may be a "repetitions",
 * "for each", or "timed" loop.
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

public class Loop extends Block {

    // constants for each of the loop types
    public static final int LOOP_TYPE_REPETITIONS = 0;
    public static final int LOOP_TYPE_FOR_EACH = 1;
    public static final int LOOP_TYPE_TIMED = 2;

    private Program program;

    // the type as one of the constants above
    private int type;

    // repetitions loop fields
    private String numReps;
    private String numWarmups;
    private boolean sync;

    // for each loop fields
    private String sequenceName;
    private Vector sequences;

    // timed loop fields
    private String time;
    private String timeUnits;

    // this task group computes aggregates at the end of the loop
    // if non-null
    private TaskGroup computeAggregatesGroup;

    // the size of the highlighted border when the loop is selected
    private static final int SELECT_BORDER_SIZE = 12;

    // the inset of the border (bounding arrows)
    private static final int BORDER_INSET = 5;

    public Loop( Program program ){
        super( program );
        this.program = program;

        // defaults
        type = LOOP_TYPE_REPETITIONS;
        numReps = "1";
        numWarmups = "0";
        sequenceName = "loop";
        sync = false;
        time = "1";
        timeUnits = "seconds";
        sequences = new Vector();
        sequences.add( "1, 2, 4, ..., 64" );

        computeAggregatesGroup = null;
    }

    public void paintComponent( Graphics graphics ){
        Rectangle bounds = getBounds();
        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_BOLD );

        if( isSelected() ){
            graphics.setColor( GraphicsUtility.getSelectedColor() );
            graphics.fillRect( 0, 0, bounds.width, SELECT_BORDER_SIZE );
            graphics.fillRect( 0, 0, SELECT_BORDER_SIZE, bounds.height );
            graphics.fillRect( 0, bounds.height - SELECT_BORDER_SIZE,
                               bounds.width, SELECT_BORDER_SIZE );
            graphics.fillRect( bounds.width - SELECT_BORDER_SIZE, 0,
                               SELECT_BORDER_SIZE, bounds.height );
            graphics.setColor( Color.BLACK );
        }
        graphics.drawString( getCaption(), 10, 10 );

        graphicsUtility.drawArrow( 8, BORDER_INSET, BORDER_INSET, BORDER_INSET, bounds.height - BORDER_INSET );
        graphicsUtility.drawArrow( 8, BORDER_INSET, bounds.height - BORDER_INSET, bounds.width - BORDER_INSET, bounds.height - BORDER_INSET );
        graphicsUtility.drawArrow( 8, bounds.width - BORDER_INSET, bounds.height - BORDER_INSET, bounds.width - BORDER_INSET, BORDER_INSET );
        graphicsUtility.drawArrow( 8, bounds.width - BORDER_INSET, BORDER_INSET, bounds.width - 50, BORDER_INSET );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
    }

    // remove all sequences
    public void clearSequences(){
        sequences.clear();
    }

    // set the first sequence
    public void setSequence( String sequence ){
        setSequence( 0, sequence );
    }

    // set the sequence indexed by index
    public void setSequence( int index, String sequence ){
        while( index >= sequences.size() )
            sequences.add( "" );

        sequences.setElementAt( sequence, index );
    }

    // add a sequences to the end of the sequences list
    public void addSequence( String sequence ){
        sequences.add( sequence );
    }

    // set the loop type
    // type must be one of:
    // LOOP_TYPE_REPETITIONS, LOOP_TYPE_FOR_EACH, or LOOP_TYPE_TIMED
    public void setLoopType( int type ){
        this.type = type;
    }

    // set the numner of repetitions
    public void setNumReps( String numReps ){
        this.numReps = numReps;
    }

    // set the number of warmup repetitions
    public void setNumWarmups( String numWarmups ){
        this.numWarmups = numWarmups;
    }

    // set synchronize before warmups
    public void setSync( boolean flag ){
        this.sync = flag;
    }

    // set the name of the variable bound to the sequences
    public void setSequenceName( String sequenceName ){
        this.sequenceName = sequenceName;
    }

    // for a timed loop, set the time
    public void setTime( String time ){
        this.time = time;
    }

    // for a timed loop, set the time units
    public void setTimeUnits( String timeUnits ){
        this.timeUnits = timeUnits;
    }

    // set the task group to compute aggregates on at the end of the loop
    public void setComputeAggregatesGroup( TaskGroup computeAggregatesGroup ){
        this.computeAggregatesGroup = computeAggregatesGroup;
    }

    // same as a above but take a task string instead of a TaskGroup
    public void setComputeAggregatesGroup( String computeAggregatesGroupString ){
        TaskGroup taskGroup = new TaskGroup( program );
        taskGroup.setSource( computeAggregatesGroupString );
        setComputeAggregatesGroup( taskGroup );
    }

    // accessor methods for getting the fields set as by the above methods

    public int getLoopType(){
        return type;
    }

    public String getNumReps(){
        return numReps;
    }

    public String getNumWarmups(){
        return numWarmups;
    }

    public boolean getSync(){
        return sync;
    }

    public String getSequence(){
        return (String)sequences.elementAt( 0 );
    }

    public Vector getSequences(){
        return sequences;
    }

    public String getSequenceName(){
        return sequenceName;
    }

    public String getTime(){
        return time;
    }

    public String getTimeUnits(){
        return timeUnits;
    }

    public TaskGroup getComputeAggregatesGroup(){
        return computeAggregatesGroup;
    }

    // process a mouseClicked event
    // select the loop if the mouse was clicked within the edges of
    // the border
    public void mouseClicked( MouseEvent mouseEvent ){
        int x = mouseEvent.getX();
        int y = mouseEvent.getY();

        Rectangle bounds = getBounds();

        // left, top, bottom, right edge
        if( (x >= 0 && x <= SELECT_BORDER_SIZE) ||
            (y >= 0 && y <= SELECT_BORDER_SIZE) ||
            (y >= bounds.height - SELECT_BORDER_SIZE && y <= bounds. height) ||
            (x >= bounds.width - SELECT_BORDER_SIZE && x <= bounds.width ) ){
            if( isSelected() )
                program.setAllSelected( false );
            else{
                program.setAllSelected( false );
                setSelected( true );
                program.updateLoopDialog();
            }
            program.updateState();
            repaint();
        }
        else
            super.mouseClicked( mouseEvent );
    }

    public void setProgram( Program program ){
        this.program = program;
        super.setProgram( program );
    }

    // returns the code for the header of the loop, not code for
    // the entire loop that it contains
    public String toCode(){
        String code;
        switch( type ){
        case LOOP_TYPE_REPETITIONS:
            code = "for " + numReps + " " +
                Utility.wordForm( numReps, "repetitions" );

            if( !numWarmups.equals( "0" ) ){
                code += " plus " + numWarmups +
                    " warmup " + Utility.wordForm( numWarmups, "repetitions" );
                if( sync )
                    code += " and a synchronization";
            }
            return code;
        case LOOP_TYPE_FOR_EACH:
            code = "for each " + sequenceName + " in ";
            for( int i = 0; i < sequences.size(); i++ ){
                String sequence = (String)sequences.elementAt( i );
                if( i > 0 )
                    code += ", ";
                code += "{" + sequence + "}";
            }
            return code;
        case LOOP_TYPE_TIMED:
            code = "for " + time + " " + Utility.wordForm( time, timeUnits );
            return code;
        default:
            assert false;
            return "";
        }
    }

    // generate the code corresponding to the compute aggregates
    public String toCodeComputeAggregates(){
        if( computeAggregatesGroup == null )
            return null;
        else
            return computeAggregatesGroup.toCodeSource() + " " +
                Utility.wordForm( computeAggregatesGroup.toCodeSource(), "computes" )
                + " aggregates";
    }

    // get the caption for the loop's visual representation
    // the caption is an abbreviated form of the code
    // the caption appears in the upper-left corner of the loop
    public String getCaption(){
        String caption = "";
        switch( type ){
        case LOOP_TYPE_REPETITIONS:
            if( !numWarmups.equals( "0" ) ){
                caption += numWarmups + " " +
                    Utility.wordForm( numWarmups, "warmups" ) + " + ";
                if( sync )
                    caption += "sync + ";
            }
            caption += numReps + " " + Utility.wordForm( numReps, "reps" );
            return caption;
        case LOOP_TYPE_FOR_EACH:
            caption = sequenceName + " in ";
            for( int i = 0; i < sequences.size(); i++ ){
                String sequence = (String)sequences.elementAt( i );
                if( i > 0 )
                    caption += ", ";
                caption += "{" + sequence + "}";
            }

            return caption;
        case LOOP_TYPE_TIMED:
            return toCode();
        default:
            assert false;
            return "";
        }
    }

    // get all selected sub-components and self if selected
    public Vector getAllSelected( Vector selectedComponents ){
        if( isSelected() )
            selectedComponents.add( this );
        selectedComponents = super.getAllSelected( selectedComponents );
        return selectedComponents;
    }

    // set the selection state of all sub-components
    public void setAllSelected( boolean flag ){
        setSelected( flag );
        super.setAllSelected( flag );
    }

    // set the selection state and update the GUI and loop dialog
    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateState();
        program.updateLoopDialog();
    }

    // get all variables in the scope of this loop
    public Vector getVariablesInScope( Vector variables ){
        if( type == LOOP_TYPE_FOR_EACH )
            variables.add( sequenceName );
        return super.getVariablesInScope( variables );
    }

    // get all variables in the scope of this loop, including
    // predeclared variables
    public Vector getAllVariablesInScope( Vector variables ){
        if( type == LOOP_TYPE_FOR_EACH )
            variables.add( sequenceName );
        return super.getAllVariablesInScope( variables );
    }

    // clone this loop and all of its sub-components
    public Object clone() throws CloneNotSupportedException {
        Loop loop = new Loop( program );
        loop.type = type;
        loop.numReps = numReps;
        loop.numWarmups = numWarmups;
        loop.sync = sync;
        loop.sequenceName = sequenceName;
        loop.time = time;
        loop.timeUnits = timeUnits;
        loop.sequences = (Vector)sequences.clone();

        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)components.elementAt( i );
            loop.add( (AbstractComponent)component.clone() );
        }
        return loop;
    }

}
