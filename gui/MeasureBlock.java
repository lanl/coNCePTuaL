/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: measure block
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class holds a block of AbstractComponents around which a measurement
 * is wrapped. A measurement:
 *   -resets counters
 *   -logs
 *   -computes aggregates if the measure block contains only a loop
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

public class MeasureBlock extends Block {
    
    private Program program;

    // pixel width of the border is inset from bounds
    private static final int BORDER_INSET = 5;

    // pixel width of the highlighted selection border
    private static final int BORDER_SELECT_INSET = 6;
    
    // the length of the top and bottom part of the border
    private static final int BORDER_TOP_BOTTOM_LENGTH = 20;

    // the task group that the measurement applies to in resetting counters,
    // logging, and computing aggregates
    private TaskGroup taskGroup;

    // the expressions to be measured, e.g: the mean of bytes_received
    private Vector measureExpressions;

    // whether or not to reset counters at the start of the block
    private boolean reset;
    
    public MeasureBlock( Program program ){
        super( program );
        this.program = program;
        
        // defaults
        measureExpressions = new Vector();
        taskGroup = new TaskGroup( program );
        setTaskGroup( "task 0" );
        reset = true;
    }
    
    // enable or disable reset counters
    public void setReset( boolean reset ){
        this.reset = reset;
    }

    public boolean getReset(){
        return reset;
    }

    public void setTaskGroup( TaskGroup taskGroup ){
        this.taskGroup = taskGroup;
    }

    public void setTaskGroup( String taskGroupString ){
        taskGroup.setSource( taskGroupString ); 
    }

    public TaskGroup getTaskGroup(){
        return taskGroup;
    }

    public Vector getMeasureExpressions(){
        return measureExpressions;
    }

    public void clearMeasureExpressions(){
        measureExpressions.clear();
    }

    public void addMeasureExpression( MeasureExpression measureExpression ){
        measureExpressions.add( measureExpression );
    }


    // set the aggregate function of the MeasureExpression at index
    // creates one or more measureExpressions if there is no
    // MeasureExpression at index
    public void setAggregate( String aggregate, 
                              int index ){
        while( index >= measureExpressions.size() ){
            MeasureExpression expression = new MeasureExpression();
            measureExpressions.add( expression );
        }

        MeasureExpression expression 
            = (MeasureExpression)measureExpressions.elementAt( index );
        expression.aggregate = aggregate;
    }
    
    // set the primary expression of the MeasureExpression at index
    // creates one or more measureExpressions if there is no
    // MeasureExpression at index
    public void setExpression( String expression, 
                               int index ){
        while( index >= measureExpressions.size() ){
            MeasureExpression measureExpression = new MeasureExpression();
            measureExpressions.add( measureExpression );
        }
        
        MeasureExpression measureExpression 
            = (MeasureExpression)measureExpressions.elementAt( index );
        measureExpression.expression = expression;
    }

    // set the comment of the MeasureExpression at index
    // creates one or more measureExpressions if there is no
    // MeasureExpression at index
    public void setComment( String comment, 
                            int index ){

        while( index >= measureExpressions.size() ){
            MeasureExpression expression = new MeasureExpression();
            measureExpressions.add( expression );
        }
        
        MeasureExpression expression 
            = (MeasureExpression)measureExpressions.elementAt( index );
        expression.comment = comment;

    }

    public void paintComponent( Graphics graphics ){
        Rectangle bounds = getBounds();
        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_BOLD );

        if( isSelected() ){
            graphics.setColor( GraphicsUtility.getSelectedColor() );
            // top
            graphics.fillRect( 0, 0, bounds.width, BORDER_SELECT_INSET * 2
                               + getTopSpacing() - 5 );
            
            // left
            graphics.fillRect( 0, 0, BORDER_SELECT_INSET * 2, bounds.height );
            
            // bottom
            graphics.fillRect( 0, bounds.height - BORDER_SELECT_INSET * 2, 
                               bounds.width, bounds.height );

            // right
            graphics.fillRect( bounds.width - BORDER_SELECT_INSET * 2, 0,
                               bounds.width, bounds.height );
            graphics.setColor( Color.black );
        }

        // these constants need to be changed
        
        drawCaption( graphics );
        
        // left brace
        // top
        graphics.drawLine( BORDER_INSET, BORDER_INSET, 
                           BORDER_INSET + BORDER_TOP_BOTTOM_LENGTH, 
                           BORDER_INSET );
        
        // left
        graphics.drawLine( BORDER_INSET, BORDER_INSET, 
                           BORDER_INSET, bounds.height - BORDER_INSET );

        // bottom
        graphics.drawLine( BORDER_INSET, bounds.height - BORDER_INSET, 
                           BORDER_INSET + BORDER_TOP_BOTTOM_LENGTH, 
                           bounds.height - BORDER_INSET );
        
        // right brace
        // top
        graphics.drawLine( bounds.width - BORDER_INSET 
                           - BORDER_TOP_BOTTOM_LENGTH,
                           BORDER_INSET, 
                           bounds.width - BORDER_INSET, 
                           BORDER_INSET );
        // right
        graphics.drawLine( bounds.width - BORDER_INSET, 
                           BORDER_INSET, 
                           bounds.width - BORDER_INSET, 
                           bounds.height - BORDER_INSET );
        // bottom
        graphics.drawLine( bounds.width - BORDER_INSET 
                           - BORDER_TOP_BOTTOM_LENGTH,
                           bounds.height - BORDER_INSET,
                           bounds.width - BORDER_INSET, 
                           bounds.height - BORDER_INSET );

        graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
    }

    public void mouseClicked( MouseEvent mouseEvent ){
        int x = mouseEvent.getX();
        int y = mouseEvent.getY();

        Rectangle bounds = getBounds();

        // if the mouse is clicked within the border then select/deselect
        if( y <= BORDER_INSET * 2 + getTopSpacing() ||
            y >= bounds.height - BORDER_INSET * 3 || 
            x <= BORDER_INSET * 3 ||
            x >= bounds.width - BORDER_INSET * 3 ){
            if( isSelected() )
                program.setAllSelected( false );
            else{
                program.setAllSelected( false );
                setSelected( true );
            }
            program.updateState();
        }
        else
            super.mouseClicked( mouseEvent );
    }

    public void setProgram( Program program ){
        this.program = program;
        super.setProgram( program );
    }

    // get the coNCePTuaL code corresponding to the resets counters
    public String toCodeReset(){
        String reset = "reset";
        String form = "their";

        if( Utility.wordForm( taskGroup.toCodeSource(), "s" ).equals( "s" ) ||
            taskGroup.toCodeSource().toLowerCase().matches( ".*task .*" ) ){
            form = "its";
            reset = "resets";
        }
        
        return taskGroup.toCodeSource() + " " + reset + " " 
            + form + " counters";
    }
    
    // get the coNCePTuaL code corresponding to the log statement
    public String toCodeLog(){
        if( measureExpressions.size() == 0 )
            return null;
        String code = "";
        code += taskGroup.toCodeSource() + " ";

        String log = "log";
        if( Utility.wordForm( taskGroup.toCodeSource(), "s" ).equals( "s" ) ||
            taskGroup.toCodeSource().toLowerCase().matches( ".*task .*" ) ){
            log = "logs";
        }

        code += log + " ";
        for( int i = 0; i < measureExpressions.size(); i++ ){
            MeasureExpression expression =
                (MeasureExpression)measureExpressions.elementAt( i );
            if( i > 0 )
                code += " and ";
            if( !expression.aggregate.equals( "" ) )
                code += expression.aggregate + " ";
            code += expression.expression + " as " + 
                "\"" + expression.comment + "\"";
        }
        return code;
    }

    // get all selected sub-components
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
    
    // set the selection state and update the measure dialog
    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateMeasureDialog();
    }

    // draw the caption in the top part of the MeasureBlock
    // this is an abbreviated form of the coNCePTuaL code
    public void drawCaption( Graphics graphics ){
        String header;

        if( Utility.wordForm( taskGroup.toCodeSource(), "s" ).equals( "s" ) ||
            taskGroup.toCodeSource().toLowerCase().matches( ".*task .*" ) ){
            if( measureExpressions.size() == 0 )
                header = " resets counters";
            else
                header = " measures:";
        }
        else {
            if( measureExpressions.size() == 0 )
                header = " reset counters";
            else
                header = " measure:";
        }
        
        graphics.drawString( taskGroup.toCodeSource() + header, 
                             BORDER_INSET + BORDER_TOP_BOTTOM_LENGTH + 5, 
                             10 );
        int i = 0;
        for( i = 0; i < measureExpressions.size(); i++ ){
            MeasureExpression expression = 
                (MeasureExpression)measureExpressions.elementAt( i );
            String item = "";
            if( !expression.aggregate.equals( "" ) )
                item += expression.aggregate + " ";
            item += expression.expression;
            graphics.drawString( item, 
                                 BORDER_INSET + BORDER_TOP_BOTTOM_LENGTH + 5, 
                                 14*(i+2)-5 );
        }
        if( getTopSpacing() != 14*i+10 ){
            setTopSpacing( 14*i+10 );
            align();
        }
    }

    // clone the MeasureBlock and all of its sub-components
    public Object clone() throws CloneNotSupportedException {
        MeasureBlock measureBlock = new MeasureBlock( program );

        for( int i = 0; i < measureExpressions.size(); i++ ){
            MeasureExpression expression = 
                (MeasureExpression)measureExpressions.elementAt( i );
            measureBlock.measureExpressions.add( expression.clone() );
        }
        measureBlock.reset = reset;
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            measureBlock.add( (AbstractComponent)component.clone() );
        }
        return measureBlock;
    }
    
}

