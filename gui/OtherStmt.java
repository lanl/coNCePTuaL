/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: other statement
 *
 * By Nick Moss <nickm@lanl.gov>
 * Improved and corrected by Paul Beinfest <beinfest@lanl.gov> 
 *
 * This class defines the "other" statement which is used to represent
 * statements that need to be read in a coNCePTuaL program but are not able
 * to be created or modified (only deleted) by the GUI, e.g: output, assert,
 * touch buffer, processor re-assignment, and backend stmts
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2014, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2014).  Los Alamos National Security, LLC.  This software
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

public class OtherStmt extends Stmt {

    private String code;
    private String stmt_type;
    private Program program;

    public OtherStmt( Program program ){
        super( program );
        this.program = program;
    }

    // targetRow is unused
    public void paint( Graphics graphics, 
                       TaskRow sourceRow, 
                       TaskRow targetRow ){
    
        
    Vector targets = program.enumerateCollectives(code, stmt_type);
        
    if( isSelected() ){
            Rectangle bounds = sourceRow.getGlobalBounds();
            graphics.setColor( GraphicsUtility.getSelectedColor() );
            graphics.fillRect( bounds.x, bounds.y + bounds.height + 1, 
                               bounds.width, 12 );
            graphics.setColor( Color.BLACK );
        }

        GraphicsUtility graphicsUtility = new GraphicsUtility( graphics );
        graphicsUtility.setStroke( GraphicsUtility.STROKE_BOLD );
//      Rectangle bounds = sourceRow.getGlobalBounds();
//      graphics.drawLine( bounds.x, 
//                         bounds.y + bounds.height + 10,
//                         bounds.x + bounds.width, 
//                         bounds.y + bounds.height + 10);
        
        for( int i = 0; i < targets.size(); i++ ){

//          SourceTarget sourceTarget = 
//              (SourceTarget)targets.elementAt( i );

            Task task = sourceRow.getTask( ((Integer)targets.get(i)).intValue() );
            Rectangle bounds = task.getGlobalBounds();
            graphics.drawLine( bounds.x - 2, 
                               bounds.y + bounds.height + 10,
                               bounds.x + bounds.width + 2, 
                               bounds.y + bounds.height + 10);
        }
        
        graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
    }
    
    // get the coNCePTuaL code for this statement
    public String toCode(){
        return code;
    }

    // select/deselect the statement if (xg,yg) in global coordinates
    // is within the selection handle
    public boolean clickSelect( boolean isShiftOrCtrlClick, int xg, int yg ){
        boolean foundSelect = false;

        TaskRow taskRow = getTaskRow();
        Rectangle bounds = taskRow.getGlobalBounds();
        if( xg >= bounds.x &&
            xg <= bounds.x + bounds.width &&
            yg >= bounds.y + bounds.height &&
            yg <= bounds.y + bounds.height + 10 ){
            if( !isSelected() ){
                if( isShiftOrCtrlClick )
                    deselectNonOtherStmts();
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
        program.updateOtherDialog();
    }
    
    public void deselectNonOtherStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( !(component instanceof OtherStmt) )
                component.setSelected( false );
        }
    }

    public void selectRegion( Rectangle marquee ){
        if( Utility.marqueeSelects( marquee, getTaskRow().getGlobalBounds() ) )
            setSelected( true );
    }

    public void setCode( String code ){
        this.code = code;
    }
    
    public void setStmtType( String stmt_type ){
    this.stmt_type = stmt_type;
        }

    public String getCode(){
        return code;
    }
    
    public String getStmtType(){
        return stmt_type;
    }

    public void resize(){

    }
    
}
