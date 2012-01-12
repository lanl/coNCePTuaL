/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: generic block
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * GenericBlock is used to implement a non-selectable block with a
 * label such as the sub-blocks in an IfBlock for "then" and
 * "otherwise"
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

public class GenericBlock extends Block {

    private static final int BORDER_INSET = 5;

    private Program program;

    private TaskGroup taskGroup;

    private String caption;

    public GenericBlock( Program program ){
        super( program );
        this.program = program;
    }
    
    public void paintComponent( Graphics graphics ){
        Rectangle bounds = getBounds();
        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_BOLD );

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

    public void setProgram( Program program ){
        this.program = program;
        super.setProgram( program );
    }

    public String toCode(){
        return "";
    }

    public String getCaption(){
        return caption;
    }

    public void setCaption( String caption ){
        this.caption = caption;
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
    
    public void setSelected( boolean flag ){
        super.setSelected( flag );
        program.updateMeasureDialog();
    }

    // draw caption at top-left of block
    public void drawCaption( Graphics graphics ){
        graphics.drawString( caption, BORDER_INSET+10, BORDER_INSET+12 );
    }

    public Object clone() throws CloneNotSupportedException {
        GenericBlock genericBlock = new GenericBlock( program );
        genericBlock.setCaption( caption );
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            genericBlock.add( (AbstractComponent)component.clone() );
        }
        return genericBlock;
    }
    
}

