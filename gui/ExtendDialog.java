/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: extend dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining the "extend communication
 * pattern" dialog. The format is very similar to CommunicationDialog,
 * see the comments in CommunicationDialog.java for more information.
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

public class ExtendDialog extends AbstractDialog {

    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;

    private int mode;

    private DialogPane dialogPane;

    private JTextField repeat;

    private String selectRepeat;

    public ExtendDialog( Program program, DialogPane dialogPane ){
        super( program );

        this.dialogPane = dialogPane;
    }

    public void actionPerformed( ActionEvent event ){
        if( mode == MODE_INIT )
            return;

        String command = event.getActionCommand();

        if( command.equals( "OK" ) ){
            if( verifyFields() ){
                program.pushState();
                program.extendPattern( Integer.parseInt( selectRepeat ) );
                dialogPane.setEmpty( true );
                program.updateState();
                program.repaint();
            }
        }

        else if( command.equals( "Cancel" ) ){
            dialogPane.setEmpty( true );
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

        pane1.add( new JLabel( "repeat pattern every: " ) );

        repeat = new JTextField( 5 );
        repeat.setText( "1" );
        pane1.add( repeat );

        pane1.add( new JLabel( " tasks" ) );

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane2 );

        JButton okButton = new JButton( "OK" );
        JButton cancelButton = new JButton( "Cancel" );
        pane2.add( okButton );
        pane2.add( cancelButton );
        okButton.addActionListener( this );
        cancelButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        dialogPane.setDefaultButton( okButton );
        mode = MODE_DEFAULT;
    }

    public void updateState(){
        defaultMode();
    }

    private boolean verifyRepeat(){
        selectRepeat = repeat.getText();
        try{
            if( Integer.parseInt( selectRepeat ) > 0 )
                return true;
        }
        catch( NumberFormatException e ){
        }
        program.showErrorDialog( "\"" + repeat.getText() +
                                 "\" is not a valid positive integer" );
        return false;
    }

    private boolean verifyFields(){
        if( verifyRepeat() )
            return true;
        return false;
    }

    public void windowClosing( WindowEvent event ) {
        dialogPane.setEmpty( true );
        program.updateState();
        program.repaint();
    }

}
