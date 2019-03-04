/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: cursor
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class defines the cursor component which is the visual marker
 * and insertion point for adding new components to the program.
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2003, Triad National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2003).  Triad National Security, LLC.  This software
 * was produced under U.S. Government contract 89233218CNA000001 for
 * Los Alamos National Laboratory (LANL), which is operated by Los
 * Alamos National Security, LLC (Triad) for the U.S. Department
 * of Energy. The U.S. Government has rights to use, reproduce,
 * and distribute this software.  NEITHER THE GOVERNMENT NOR TRIAD
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
 *   * Neither the name of Triad National Security, LLC, Los Alamos
 *     National Laboratory, the U.S. Government, nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY TRIAD AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TRIAD OR CONTRIBUTORS BE
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

public class Cursor extends AbstractComponent {

    // the height of the cursor in pixels
    private static final int CURSOR_HEIGHT = 10;

    // is the cursor visiable
    private boolean isVisible;

    // the program the cursor belongs to
    private Program program;

    public Cursor( Program program ){           
        this.program = program;
        isVisible = true;

        // set the height of the cursor. the width will be adjusted
        // automatically by the block it resides in
        setBounds( 0, 0, 0, CURSOR_HEIGHT );
    }
    
    public void paintComponent( Graphics graphics ){
        if( !isVisible )
            return;
        
        Rectangle bounds = getBounds();
        graphics.setColor( GraphicsUtility.getSelectedColor() );
        graphics.fillRect( 0, 0, bounds.width, bounds.height );
        graphics.setColor( Color.BLACK );
    }

    public void setVisible( boolean flag ){
        isVisible = flag;
    }

    public boolean isVisible(){
        return isVisible;
    }

    // don't allow the cursor to be selected
    public void setSelected( boolean flag ){
        
    }

    public Object clone() throws CloneNotSupportedException {
        return new Cursor( program );
    }
    
    // allow clicking on the cursor to have the same effect as
    // clicking within the program pane
    public void mouseClicked( MouseEvent mouseEvent ){
        if( !mouseEvent.isShiftDown() && !mouseEvent.isControlDown() ){
            program.setAllSelected( false );
            program.updateState();
        }
    }
    
}

