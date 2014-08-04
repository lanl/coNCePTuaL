/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: let dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining the dialog for
 * manipulating a LetBlock. The implementation details are very
 * similar to CommunicationDialog, see the comments in
 * CommunicationDialog.java for more information.
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

public class LetDialog extends AbstractDialog {

    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;

    private int mode;

    private DialogPane dialogPane;

    private String selectCode;

    public LetDialog( Program program, DialogPane dialogPane ){
        super( program );
        this.dialogPane = dialogPane;
    }


    public void actionPerformed( ActionEvent event ){
        if( mode == MODE_INIT )
            return;

        String command = event.getActionCommand();

        if( command.equals( "OK" ) ){
            deselectAllLetBlocks();
            updateState();
            program.updateState();
            program.repaint();
        }

    }

    public void defaultMode(){
        mode = MODE_INIT;

        dialogPane.clear();

        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        JTextField codeField = new JTextField( selectCode, 50 );
        codeField.setEditable( false );
        pane1.add( codeField );

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane2 );

        JButton okButton = new JButton( "OK" );
        pane2.add( okButton );
        okButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_DEFAULT;
    }

    public void updateState(){
        selectCode = null;

        Vector selectedLetBlocks = getSelectedLetBlocks();

        for( int i = 0; i < selectedLetBlocks.size(); i++ ){
            LetBlock block =
                (LetBlock)selectedLetBlocks.elementAt( i );
            readCode( block );
        }

        if( selectedLetBlocks.size() > 0 )
            defaultMode();
    }

    public void deselectAllLetBlocks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof LetBlock ){
                component.setSelected( false );
            }
        }
    }

    public Vector getSelectedLetBlocks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedLetBlocks = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof LetBlock )
                selectedLetBlocks.add( component );
        }
        return selectedLetBlocks;
    }

    public void windowClosing( WindowEvent event ) {
        deselectAllLetBlocks();
        updateState();
        program.updateState();
        program.repaint();
    }

    private void readCode( LetBlock block ){
        if( selectCode == null )
            selectCode = block.getCode();
        else if( !selectCode.equals( block.getCode() ) )
            selectCode = "-";
    }

    private void writeCode( LetBlock block ){
        if( !selectCode.equals( "-" ) )
            block.setCode( selectCode );
    }

    private void applyChanges( Vector letBlocks ){
        for( int i = 0; i < letBlocks.size(); i++ ){
            LetBlock block =
                (LetBlock)letBlocks.elementAt( i );
            writeCode( block );
        }
    }

    private boolean verifyCode(){
        return true;
    }

    private boolean verifyFields(){
        if( verifyCode() )
            return true;
        return false;
    }

}
