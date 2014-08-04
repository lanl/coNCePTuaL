/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: wait dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class implements the dialog for manipulating a
 * WaitStmt. The implementation details are similar to
 * CommunicationDialog, see the comments in CommunicationDialog.java
 * for more information.
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

public class WaitDialog extends AbstractDialog {

    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;

    private int mode;

    private DialogPane dialogPane;

    private DialogMenu taskGroup;

    private String selectTaskGroup;

    private Vector selectVariablesInScope;

    public WaitDialog( Program program, DialogPane dialogPane ){
        super( program );

        this.dialogPane = dialogPane;
    }

    public void actionPerformed( ActionEvent event ){
        if( mode == MODE_INIT )
            return;

        String command = event.getActionCommand();

        if( command.equals( "Apply" ) ){
            if( verifyFields() ){
                program.pushState();
                applyChanges( getSelectedWaitStmts() );
                updateState();
                program.repaint();
            }
        }
        else if( command.equals( "Reset" ) )
            updateState();
    }

    public void defaultMode(){
        mode = MODE_INIT;

        dialogPane.clear();

        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "await completion on: " ) );

        taskGroup = new DialogMenu( 430 );
        taskGroup.addItem( selectTaskGroup );
        taskGroup.addSourceTaskDescriptions();
        taskGroup.setEditable( true );

        pane1.add( taskGroup );

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane2 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        pane2.add( applyButton );
        pane2.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_DEFAULT;
    }

    public void updateState(){
        selectTaskGroup = null;

        selectVariablesInScope = new Vector();

        Vector selectedWaitStmts = getSelectedWaitStmts();

        for( int i = 0; i < selectedWaitStmts.size(); i++ ){
            WaitStmt stmt =
                (WaitStmt)selectedWaitStmts.elementAt( i );
            readTaskGroup( stmt );
            readVariablesInScope( stmt );
        }

        if( selectedWaitStmts.size() > 0 )
            defaultMode();
    }

    public void deselectAllWaitStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof WaitStmt ){
                component.setSelected( false );
            }
        }
    }

    public Vector getSelectedWaitStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedSyncs = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof WaitStmt )
                selectedSyncs.add( component );
        }
        return selectedSyncs;
    }

    public void windowClosing( WindowEvent event ) {
        deselectAllWaitStmts();
        updateState();
        program.updateState();
        program.repaint();
    }

    private void readTaskGroup( WaitStmt stmt ){
        if( selectTaskGroup == null )
            selectTaskGroup = stmt.getTaskGroup().toCodeSource();
        else if( !selectTaskGroup.equals( stmt.getTaskGroup().toCodeSource() ) )
            selectTaskGroup = "-";
    }

    private void writeTaskGroup( WaitStmt stmt ){
        if( !selectTaskGroup.equals( "-" ) )
            stmt.setTaskGroup( selectTaskGroup );
    }

    private void applyChanges( Vector syncStmts ){
        for( int i = 0; i < syncStmts.size(); i++ ){
            WaitStmt stmt =
                (WaitStmt)syncStmts.elementAt( i );
        writeTaskGroup( stmt );
        }
    }

    private boolean verifyTaskGroup(){
        selectTaskGroup = (String)taskGroup.getSelectedItem();
        if( program.verifyField( selectTaskGroup, "source_task",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTaskGroup +
                                     "\" is not a valid task description" );
            return false;
        }
    }

    private boolean verifyFields(){
        if( verifyTaskGroup() )
            return true;
        return false;
    }

    private void readVariablesInScope( WaitStmt stmt ){
        selectVariablesInScope =
            stmt.getVariablesInScope( selectVariablesInScope );
    }

}
