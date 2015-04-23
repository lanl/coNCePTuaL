/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: let block
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class defines the data and visual representations for a
 * let-binding and the components enclosed within its scope as a
 * block.
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2015, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2015).  Los Alamos National Security, LLC.  This software
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

public class LetBlock extends Block {

    private static final int BORDER_INSET = 5;

    private Program program;

    // the coNCePTuaL code corrsepond to the header of this LetBlock
    private String code;

    // variables defined in the scope of this LetBlock
    private Vector variables;

    public LetBlock( Program program ){
        super( program );
        this.program = program;

        variables = new Vector();

        code = "";
    }

    public void paintComponent( Graphics graphics ){
        Rectangle bounds = getBounds();
        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_BOLD );

        if( isSelected() ){
            graphics.setColor( GraphicsUtility.getSelectedColor() );

            // top
            graphics.fillRect( 0, 0, bounds.width, BORDER_INSET*2 );

            // left
            graphics.fillRect( 0, 0, BORDER_INSET*2, bounds.height );

            // bottom
            graphics.fillRect( 0, bounds.height - BORDER_INSET*2,
                               bounds.width, bounds.height );

            // right
            graphics.fillRect( bounds.width - BORDER_INSET*2, 0,
                               bounds.width, bounds.height );

            graphics.setColor( Color.black );
        }

        drawCaption( graphics );

        // left brace

        // top
        graphics.drawLine( BORDER_INSET, BORDER_INSET,
                           bounds.width - BORDER_INSET, BORDER_INSET );

        // left
        graphics.drawLine( BORDER_INSET, BORDER_INSET, BORDER_INSET,
                           bounds.height - BORDER_INSET );

        // bottom
        graphics.drawLine( BORDER_INSET,
                           bounds.height - BORDER_INSET,
                           bounds.width - BORDER_INSET,
                           bounds.height - BORDER_INSET );

        // right
        graphics.drawLine( bounds.width - BORDER_INSET,
                           BORDER_INSET,
                           bounds.width - BORDER_INSET,
                           bounds.height - BORDER_INSET );

        graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
    }

    public void mouseClicked( MouseEvent mouseEvent ){
        int x = mouseEvent.getX();
        int y = mouseEvent.getY();

        Rectangle bounds = getBounds();

        if( y <= BORDER_INSET*2 ||
            y >= bounds.height - BORDER_INSET*2 ||
            x <= BORDER_INSET*2 ||
            x >= bounds.width - BORDER_INSET*2 ){
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

    public String toCode(){
        return code;
    }

    public String getCode(){
        return code;
    }

    public void setCode( String code ){
        this.code = code;
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

    // draw caption in upper left corner
    public void drawCaption( Graphics graphics ){
        graphics.drawString( code, BORDER_INSET+10, BORDER_INSET+12 );
    }

    // set the selection state and update the LetDialog
    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateLetDialog();
    }

    // add a variable to this scope
    public void addVariable( String variable ){
        variables.add( variable );
    }

    // return all variables defined in the scope of the LetBlock
    public Vector getVariablesInScope( Vector variables ){
        for( int i = 0; i < this.variables.size(); i++ )
            variables.add( this.variables.elementAt( i ) );

        return super.getVariablesInScope( variables );
    }

    // return all variables defined in the scope of the LetBlock,
    // including predeclared variables
    public Vector getAllVariablesInScope( Vector variables ){
        for( int i = 0; i < this.variables.size(); i++ )
            variables.add( this.variables.elementAt( i ) );

        return super.getAllVariablesInScope( variables );
    }

    // clone this component and all sub-components
    public Object clone() throws CloneNotSupportedException {
        LetBlock letBlock = new LetBlock( program );
        letBlock.code = code;
        letBlock.variables = (Vector)variables.clone();
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)components.elementAt( i );
            letBlock.add( (AbstractComponent)component.clone() );
        }
        return letBlock;
    }

}
