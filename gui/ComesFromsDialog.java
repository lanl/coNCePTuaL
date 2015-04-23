/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: comes from dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining the dialog for modifying
 * the command-line options associated with a program. The
 * implementation follows the model of CommunicationDialog.java, see
 * the comments there for more information.
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

public class ComesFromsDialog extends AbstractDialog {

    class ComesFromItem {
        
        // the Swing components associated with each ComesFrom
        public ComesFromItem(){
            identifier = new JTextField( 10 );
            description = new JTextField( 26 );
            longOption = new JTextField( 7 );
            shortOption = new JTextField( 2 );
            defaultValue = new JTextField( 7 );
        }

        public JTextField identifier;
        public JTextField description;
        public JTextField longOption;
        public JTextField shortOption;
        public JTextField defaultValue;
    }

    // mode constants
    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;
    
    // the mode as one of the above
    private int mode;

    // the pane that the dialog will be displayed in
    private DialogPane dialogPane;

    // a vector of ComesFromItem's
    private Vector comesFromItems;
    
    public ComesFromsDialog( Program program, DialogPane dialogPane ){
        super( program );
        this.dialogPane = dialogPane;
    }
    
    // this method is called in response to all
    // events generated from GUI components in the dialog
    public void actionPerformed( ActionEvent event ){

        // do not process events as the dialog is being created
        if( mode == MODE_INIT )
            return;
        
        // the command associated with the event
        String command = event.getActionCommand();
        
        // the source or component that produced the event
        Object source = event.getSource();
        
        if( command.equals( "Apply" ) ){
            if( verifyFields( true ) ){
                program.pushState();
                applyChanges();
            }
        }
        else if( command.equals( "Reset" ) ){
            updateState();
        }
        else if( command.equals( "delete" ) ){
            verifyFields( false );
            IdButton idButton = (IdButton)source;
            comesFromItems.removeElementAt( idButton.getID() );
            defaultMode();
        }
        else if( command.equals( "Add Option" ) ){
            verifyFields( false );
            ComesFromItem item = new ComesFromItem();
            item.identifier.setText( "" );
            item.description.setText( "" );
            item.shortOption.setText( "" );
            item.longOption.setText( "" );
            item.defaultValue.setText( "" );
            comesFromItems.add( item );
            defaultMode();
        }
    }
    
    public void defaultMode(){
        mode = MODE_INIT;

        dialogPane.clear();
        
        for( int i = 0; i < comesFromItems.size(); i++ ){
            ComesFromItem item = 
                (ComesFromItem)comesFromItems.elementAt( i );

            JPanel pane1 = new JPanel();
            pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( pane1 );

            pane1.add( new JLabel( "variable name:" ) );
            pane1.add( item.identifier );
            pane1.add( new JLabel( "help text:" ) );
            pane1.add( item.description );

            JPanel pane2 = new JPanel();
            pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( pane2 );

            pane2.add( new JLabel( "long option:" ) );
            pane2.add( item.longOption );
            pane2.add( new JLabel( "short option:" ) );
            pane2.add( item.shortOption );
            pane2.add( new JLabel( "default value:" ) );
            pane2.add( item.defaultValue );
            IdButton deleteButton = new IdButton( "delete", i );
            deleteButton.addActionListener( this );
            pane2.add( deleteButton );
            dialogPane.add( new JSeparator() );

        }

        JPanel buttonPane = new JPanel();
        buttonPane.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( buttonPane );

        JButton applyButton = new JButton( "Apply" );
        JButton resetButton = new JButton( "Reset" );
        JButton addOptionButton = new JButton( "Add Option" );
        buttonPane.add( applyButton );
        buttonPane.add( resetButton );
        buttonPane.add( addOptionButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        addOptionButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_DEFAULT;
    }

    
    public void windowClosing( WindowEvent event ) {
        program.updateState();
        program.repaint();
    }

    private boolean verifyFields( boolean complain ){
        for( int i = 0; i < comesFromItems.size(); i++ ){
            ComesFromItem item = 
                (ComesFromItem)comesFromItems.elementAt( i );
            if( !program.verifyField( item.identifier.getText(), 
                                      "ident", null ) ){
                if( complain )
                    program.showErrorDialog( "\"" + item.identifier.getText() + "\" is not a valid name" );
                return false;
            }
            if( !item.longOption.getText().matches( "--\\w+" ) ){
                if( complain )
                    program.showErrorDialog( "\"" + item.longOption.getText() + "\" is not a valid long option" );
                return false;
            }
            if( !item.shortOption.getText().matches( "-\\w+" ) ){
                if( complain )
                    program.showErrorDialog( "\"" + item.shortOption.getText() + "\" is not a valid short option" );
                return false;
            }
            if( !program.verifyField( item.defaultValue.getText(), 
                                      "expr", null ) ){
                if( complain )
                    program.showErrorDialog( "\"" + item.defaultValue.getText() + "\" is not a valid default value" );
                return false;
            }
        }
        return true;
    }

    public void updateState(){
        Vector comesFroms = program.getComesFroms();
        comesFromItems = new Vector();
        for( int i = 0; i < comesFroms.size(); i++ ){
            ComesFrom comesFrom = (ComesFrom)comesFroms.elementAt( i );
            ComesFromItem item = new ComesFromItem();
            item.identifier.setText( comesFrom.identifier );
            item.description.setText( comesFrom.description );
            item.longOption.setText( comesFrom.longOption );
            item.shortOption.setText( comesFrom.shortOption );
            item.defaultValue.setText( comesFrom.defaultValue );
            comesFromItems.add( item );
        }
        // if empty, add sample
        if( comesFromItems.size() == 0 ){
            ComesFromItem item = new ComesFromItem();
            item.identifier.setText( "reps" );
            item.description.setText( "Number of repetitions" );
            item.shortOption.setText( "-r" );
            item.longOption.setText( "--reps" );
            item.defaultValue.setText( "1" );
            comesFromItems.add( item );
        }
        defaultMode();
    }

    public void applyChanges(){
        Vector comesFroms = new Vector();
        for( int i = 0; i < comesFromItems.size(); i++ ){
            ComesFromItem item = 
                (ComesFromItem)comesFromItems.elementAt( i );
            ComesFrom comesFrom = new ComesFrom();
            comesFrom.identifier = item.identifier.getText();
            comesFrom.description = item.description.getText();
            comesFrom.longOption = item.longOption.getText();
            comesFrom.shortOption = item.shortOption.getText();
            comesFrom.defaultValue = item.defaultValue.getText();
            comesFroms.add( comesFrom );
        }
        program.setComesFroms( comesFroms );
    }
    
}
