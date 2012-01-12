/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: if dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining the dialog for
 * manipulating an IfBlock. The implementation details are very
 * similar to CommunicationDialog, see the comments in
 * CommunicationDialog.java for more information.
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

public class IfDialog extends AbstractDialog {

    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;

    private int mode;

    private DialogPane dialogPane;

    private DialogMenu condition;

    private String selectCondition;

    private Vector selectVariablesInScope;

    public IfDialog( Program program, DialogPane dialogPane  ){
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
                applyChanges( getSelectedIfBlocks() );
                updateState();
                program.updateState();
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

        pane1.add( new JLabel( "condition: " ) );

        condition = new DialogMenu( 430 );
        condition.addItem( selectCondition );
        addScopeVariables( condition );
        condition.setEditable( true );

        pane1.add( condition );

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
        selectCondition = null;

        selectVariablesInScope = new Vector();

        Vector selectedIfBlocks = getSelectedIfBlocks();

        for( int i = 0; i < selectedIfBlocks.size(); i++ ){
            IfBlock block =
                (IfBlock)selectedIfBlocks.elementAt( i );
            readCondition( block );
            readVariablesInScope( block );
        }

        if( selectedIfBlocks.size() > 0 )
            defaultMode();
    }

    public void deselectAllIfBlocks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof IfBlock ){
                component.setSelected( false );
            }
        }
    }

    public Vector getSelectedIfBlocks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedSyncs = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof IfBlock )
                selectedSyncs.add( component );
        }
        return selectedSyncs;
    }

    public void windowClosing( WindowEvent event ) {
        deselectAllIfBlocks();
        updateState();
        program.updateState();
        program.repaint();
    }

    private void readCondition( IfBlock block ){
        if( selectCondition == null )
            selectCondition = block.getCondition();
        else if( !selectCondition.equals( block.getCondition() ) )
            selectCondition = "-";
    }

    private void writeCondition( IfBlock block ){
        if( !selectCondition.equals( "-" ) )
            block.setCondition( selectCondition );
    }

    private void applyChanges( Vector ifBlocks ){
        for( int i = 0; i < ifBlocks.size(); i++ ){
            IfBlock block =
                (IfBlock)ifBlocks.elementAt( i );
        writeCondition( block );
        }
    }

    private boolean verifyCondition(){
        selectCondition = (String)condition.getSelectedItem();
        if( program.verifyField( selectCondition, "rel_expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectCondition +
                                     "\" is not a valid condition" );
            return false;
        }
    }

    private boolean verifyFields(){
        if( verifyCondition() )
            return true;
        return false;
    }

    private void readVariablesInScope( IfBlock block ){
        selectVariablesInScope =
            block.getVariablesInScope( selectVariablesInScope );
    }

    private void addScopeVariables( DialogMenu menu ){
        for( int i = 0; i < selectVariablesInScope.size(); i++ ){
            String variable =
                (String)selectVariablesInScope.elementAt( i );
            menu.addItem( variable );
        }
    }

}
