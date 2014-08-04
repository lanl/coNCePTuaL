/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: communication dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining a dialog for manipulating
 * one or more selected CommunicationStmt's. The dialogs are displayed
 * in the detachable dialogPane of the main window. The implementation
 * details for the various XXXDialog.java dialogs are very similar as
 * the CommuncationDialog served as a model for the implementation of
 * the others. This file has been thoroughly commented but these
 * comments are not duplicated in the other dialog so the comments in
 * this file should be referred to as a guide for the others.
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

public class CommunicationDialog extends AbstractDialog {

    // mode constants
    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;

    // the mode as one of the above
    private int mode;

    // the DialogPane that the dialog will appear in
    private DialogPane dialogPane;

    // various Swing components that appear in the dialog
    private DialogMenu sourceGroup;
    private DialogMenu targetGroup;
    private JCheckBox sourceAsync;
    private JCheckBox targetAsync;
    private JCheckBox sourceUniqueBuffer;
    private JCheckBox targetUniqueBuffer;
    private DialogMenu messageCount;
    private DialogMenu messageSize;
    private DialogMenu messageSizeUnits;
    private DialogMenu sourceAlignment;
    private DialogMenu targetAlignment;
    private DialogMenu sourceAlignmentMode;
    private DialogMenu targetAlignmentMode;
    private DialogMenu sourceVerificationOrTouching;
    private DialogMenu targetVerificationOrTouching;
    private DialogMenu sourceAlignmentUnits;
    private DialogMenu targetAlignmentUnits;
    private DialogMenu sourceBuffer;
    private DialogMenu targetBuffer;
    private JCheckBox useSourceAttributes;

    // used for maintaining the state of the Swing components based on
    // the currently selected set of CommunicationStmt's
    private String selectSourceGroup;
    private String selectTargetGroup;
    private boolean selectSourceAsync;
    private boolean selectTargetAsync;
    private boolean selectSourceUniqueBuffer;
    private boolean selectTargetUniqueBuffer;
    private String selectMessageCount;
    private String selectMessageSize;
    private String selectMessageSizeUnits;
    private String selectSourceAlignment;
    private String selectTargetAlignment;
    private String selectSourceAlignmentMode;
    private String selectTargetAlignmentMode;
    private String selectSourceVerificationOrTouching;
    private String selectTargetVerificationOrTouching;
    private String selectSourceAlignmentUnits;
    private String selectTargetAlignmentUnits;
    private String selectSourceBuffer;
    private String selectTargetBuffer;

    // used to hold the variables in the current scope
    private Vector selectVariablesInScope;

    // since there are only two states to a checkbox
    // these values keep track of the mixed state
    private boolean isMixedSourceAsync;
    private boolean isMixedTargetAsync;
    private boolean isMixedSourceUniqueBuffer;
    private boolean isMixedTargetUniqueBuffer;

    // similar to the above, these keep track of whether the fields
    // have already been read in reading the selected
    // CommunicationStmt's
    private boolean isFirstSourceAsync;
    private boolean isFirstTargetAsync;
    private boolean isFirstSourceUniqueBuffer;
    private boolean isFirstTargetUniqueBuffer;

    public CommunicationDialog( Program program, DialogPane dialogPane ){
        super( program );
        this.dialogPane = dialogPane;
    }

    // this method is called in response to all
    // events generated from Swing components in the dialog
    public void actionPerformed( ActionEvent event ){
        // because Swing is multi-threaded, make sure events are not
        // processed as the dialog is being created
        if( mode == MODE_INIT )
            return;

        // the command associated with the event
        // usually the label of the component
        String command = event.getActionCommand();

        // the source or component that produced the event
        Object source = event.getSource();

        // "Apply" button pressed
        if( command.equals( "Apply" ) ){
            // verify all fields before applying changes
            if( verifyFields() ){
                // save the undo state
                program.pushState();

                // apply the changes to each of the selected
                // CommunicationStmt's
                applyChanges( getSelectedCommunicationStmts() );
                updateState();
                program.repaint();
            }
        }
        // "Make Default" button pressed
        else if( command.equals( "Make Default" ) ){
            if( verifyFields() )
                makeDefault();
        }

        // "Reset" button pressed so undo all changes made in the dialog
        else if( command.equals( "Reset" ) ){
            updateState();
        }

        // if any of the check boxes are clicked
        // they are no longer in a mixed state
        else if( source == sourceAsync )
            isMixedSourceAsync = false;
        else if( source == targetAsync )
            isMixedTargetAsync = false;
        else if( source == sourceUniqueBuffer )
            isMixedSourceUniqueBuffer = false;
        else if( source == targetUniqueBuffer )
            isMixedTargetUniqueBuffer = false;

        // if the "use source attributes" checkbox is clicked
        // we need to verify the fields and redraw the dialog
        // either hiding the target attributes or showing them
        else if( source == useSourceAttributes ){
            // verify the source fields
            verifySourceGroup();
            verifySourceAsync();
            verifySourceUniqueBuffer();
            verifyMessageCount();
            verifyMessageSize();
            verifyMessageSizeUnits();
            verifySourceAlignment();
            verifySourceAlignmentMode();
            verifySourceVerificationOrTouching();
            verifySourceAlignmentUnits();
            verifySourceBuffer();

            // duplicate the source fields into the target fields
            selectTargetAsync = selectSourceAsync;
            selectTargetUniqueBuffer = selectSourceUniqueBuffer;
            selectTargetAlignment = selectSourceAlignment;
            selectTargetAlignmentMode = selectSourceAlignmentMode;
            selectTargetVerificationOrTouching = selectSourceVerificationOrTouching;
            selectTargetAlignmentUnits = selectSourceAlignmentUnits;
            selectTargetBuffer = selectSourceBuffer;

            if( !useSourceAttributes.isSelected() )
                defaultMode( true );
            else
                defaultMode( false );
        }
    }

    // set up or redraw the dialog. if displayTargetAttributes is true
    // then force the dialog to show the target attributes, else they
    // are shown only when they differ from the source attributes
    public void defaultMode( boolean displayTargetAttributes ){

        // set mode to init so events triggered in setting up the
        // dialog are ignored, after the dialog is finished being
        // set up, mode is set to MODE_DEFAULT
        mode = MODE_INIT;

        // clear the dialogPane of all components
        dialogPane.clear();

        // source attributes

        // using the FlowLayout there will be one JPanel for each row
        // of components
        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "source: " ) );

        // use a fixed width menu so variations in the contents
        // of the menu don't cause the dialogs to appear inconsistent
        sourceGroup = new DialogMenu( 430 );

        // add to the menu the source task from the selected
        // CommunicationStmt's
        sourceGroup.addItem( selectSourceGroup );

        // add the default source tasks
        // the DialogMenu takes care not to add duplicate items
        sourceGroup.addSourceTaskDescriptions();

        // allow changes in the menu to trigger an event
        sourceGroup.addActionListener( this );

        // make the menu editable this gives the benefit of a text field
        // while still having presets available in the menu
        sourceGroup.setEditable( true );

        // set the selected item to the first item in the menu
        // (the value read from the selected CommunicationStmt's)
        sourceGroup.setSelectedIndex( 0 );
        pane1.add( sourceGroup );

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        pane2.add( new JLabel( "size: " ) );
        messageSize = new DialogMenu( 150 );
        messageSize.addItem( selectMessageSize );
        addScopeVariables( messageSize );
        messageSize.setEditable( true );
        pane2.add( messageSize );

        messageSizeUnits = new DialogMenu();
        messageSizeUnits.addItem( selectMessageSizeUnits );
        messageSizeUnits.addSizeUnits();
        pane2.add( messageSizeUnits );

        pane2.add( new JLabel( "count: " ) );
        messageCount = new DialogMenu( 150 );
        messageCount.addItem( selectMessageCount );
        addScopeVariables( messageCount );
        messageCount.setEditable( true );
        pane2.add( messageCount );

        JPanel pane2b = new JPanel();
        pane2b.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2b );

        sourceAsync = new JCheckBox();

        // set check state
        sourceAsync.setSelected( selectSourceAsync );

        pane2b.add( sourceAsync );
        pane2b.add( new JLabel( "asynchronous" ) );

        sourceUniqueBuffer = new JCheckBox();
        sourceUniqueBuffer.setSelected( selectSourceUniqueBuffer );

        pane2b.add( sourceUniqueBuffer );

        pane2b.add( new JLabel( "unique buffer" ) );

        sourceVerificationOrTouching = new DialogMenu();
        sourceVerificationOrTouching.addItem( selectSourceVerificationOrTouching );
        sourceVerificationOrTouching.addItem( "without verification" );
        sourceVerificationOrTouching.addItem( "without data touching" );
        sourceVerificationOrTouching.addItem( "with verification" );
        sourceVerificationOrTouching.addItem( "with data touching" );

        pane2b.add( sourceVerificationOrTouching );

        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane3 );

        sourceAlignment = new DialogMenu( 150 );
        sourceAlignment.addItem( selectSourceAlignment );
        addScopeVariables( sourceAlignment );
        sourceAlignment.setEditable( true );

        pane3.add( sourceAlignment );

        sourceAlignmentUnits = new DialogMenu();
        sourceAlignmentUnits.addItem( selectSourceAlignmentUnits );
        sourceAlignmentUnits.addSizeUnits();
        pane3.add( sourceAlignmentUnits );

        sourceAlignmentMode = new DialogMenu();
        sourceAlignmentMode.addItem( selectSourceAlignmentMode );
        sourceAlignmentMode.addItem( "unaligned" );
        sourceAlignmentMode.addItem( "aligned" );
        sourceAlignmentMode.addItem( "misaligned" );
        pane3.add( sourceAlignmentMode );

        pane3.add( new JLabel( "buffer: " ) );

        sourceBuffer = new DialogMenu( 150 );
        sourceBuffer.addItem( selectSourceBuffer );
        sourceBuffer.addItem( "default" );
        sourceBuffer.setEditable( true );
        pane3.add( sourceBuffer );

        // add horizontal separator
        dialogPane.add( new JSeparator() );

        // target attributes
        JPanel pane4 = new JPanel();
        pane4.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane4 );

        pane4.add( new JLabel( "target: " ) );

        targetGroup = new DialogMenu( 430 );
        targetGroup.addItem( selectTargetGroup );
        targetGroup.addTargetTaskDescriptions();
        targetGroup.setEditable( true );
        pane4.add( targetGroup );

        useSourceAttributes = new JCheckBox();

        // if not told to explicitly display target attributes
        // and all the target attributes match source attributes
        // then check the "use source attributes" check box
        // which will cause the target attributes to not be displayed
        if( !displayTargetAttributes &&
            selectSourceAsync == selectTargetAsync &&
            selectSourceUniqueBuffer == selectTargetUniqueBuffer &&
            selectSourceAlignment.equals( selectTargetAlignment ) &&
            selectSourceAlignmentMode.equals( selectTargetAlignmentMode ) &&
            selectSourceVerificationOrTouching.equals( selectTargetVerificationOrTouching ) &&
            selectSourceAlignmentUnits.equals( selectTargetAlignmentUnits ) &&
            selectSourceBuffer.equals( selectTargetBuffer ) )
            useSourceAttributes.setSelected( true );

        pane4.add( useSourceAttributes );
        pane4.add( new JLabel( "use source attributes" ) );
        useSourceAttributes.addActionListener( this );

        if( !useSourceAttributes.isSelected() ){

            JPanel pane5 = new JPanel();
            pane5.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( pane5 );

            targetAsync = new JCheckBox();
            targetAsync.setSelected( selectTargetAsync );

            pane5.add( targetAsync );
            pane5.add( new JLabel( "asynchronous" ) );

            targetUniqueBuffer = new JCheckBox();
            targetUniqueBuffer.setSelected( selectTargetUniqueBuffer );

            pane5.add( targetUniqueBuffer );
            pane5.add( new JLabel( "unique buffer" ) );

            targetVerificationOrTouching = new DialogMenu();
            targetVerificationOrTouching.addItem( selectTargetVerificationOrTouching );
            targetVerificationOrTouching.addItem( "without verification" );
            targetVerificationOrTouching.addItem( "without data touching" );
            targetVerificationOrTouching.addItem( "with verification" );
            targetVerificationOrTouching.addItem( "with data touching" );
            pane5.add( targetVerificationOrTouching );

            JPanel pane6 = new JPanel();
            pane6.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( pane6 );

            targetAlignment = new DialogMenu( 150 );
            targetAlignment.addItem( selectTargetAlignment );
            addScopeVariables( targetAlignment );
            targetAlignment.setEditable( true );
            pane6.add( targetAlignment );

            targetAlignmentUnits = new DialogMenu();
            targetAlignmentUnits.addItem( selectTargetAlignmentUnits );
            targetAlignmentUnits.addSizeUnits();
            pane6.add( targetAlignmentUnits );

            targetAlignmentMode = new DialogMenu();
            targetAlignmentMode.addItem( selectTargetAlignmentMode );
            targetAlignmentMode.addItem( "unaligned" );
            targetAlignmentMode.addItem( "aligned" );
            targetAlignmentMode.addItem( "misaligned" );
            pane6.add( targetAlignmentMode );

            pane6.add( new JLabel( "buffer: " ) );

            targetBuffer = new DialogMenu( 150 );
            targetBuffer.addItem( selectTargetBuffer );
            targetBuffer.addItem( "default" );
            targetBuffer.setEditable( true );
            pane6.add( targetBuffer );

        }

        JPanel pane7 = new JPanel();
        pane7.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane7 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton makeDefaultButton = new JButton( "Make Default" );
        JButton resetButton = new JButton( "Reset" );
        pane7.add( applyButton );
        pane7.add( makeDefaultButton );
        pane7.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        makeDefaultButton.addActionListener( this );

        // finalize the dialogPane and flag as non-empty so the help
        // text will not be displayed
        dialogPane.finalize();
        dialogPane.setEmpty( false );

        // set mode to MODE_DEFAULT so events will no longer be
        // ignored
        mode = MODE_DEFAULT;
    }

    // update the state of the dialog
    // based on the selected CommunicationStmt's
    public void updateState(){
        selectSourceGroup = null;
        selectTargetGroup = null;

        isMixedSourceAsync = false;
        isMixedTargetAsync = false;
        isMixedSourceUniqueBuffer = false;
        isMixedTargetUniqueBuffer = false;

        isFirstSourceAsync = true;
        isFirstTargetAsync = true;
        isFirstSourceUniqueBuffer = true;
        isFirstTargetUniqueBuffer = true;

        selectSourceAsync = false;
        selectTargetAsync = false;
        selectSourceUniqueBuffer = false;
        selectTargetUniqueBuffer = false;

        selectMessageCount = null;
        selectMessageSize = null;
        selectMessageSizeUnits = null;
        selectSourceAlignment = null;
        selectTargetAlignment = null;
        selectSourceAlignmentMode = null;
        selectTargetAlignmentMode = null;
        selectSourceVerificationOrTouching = null;
        selectTargetVerificationOrTouching = null;
        selectSourceAlignmentUnits = null;
        selectTargetAlignmentUnits = null;
        selectSourceBuffer = null;
        selectTargetBuffer = null;

        selectVariablesInScope = new Vector();

        Vector selectedCommunicationStmts = getSelectedCommunicationStmts();

        // read each of the fields from each of the
        // CommunicationStmt's
        for( int i = 0; i < selectedCommunicationStmts.size(); i++ ){
            CommunicationStmt stmt =
                (CommunicationStmt)selectedCommunicationStmts.elementAt( i );

            readSourceGroup( stmt );
            readTargetGroup( stmt );
            readSourceAsync( stmt );
            readTargetAsync( stmt );
            readSourceUniqueBuffer( stmt );
            readTargetUniqueBuffer( stmt );
            readMessageCount( stmt );
            readMessageSize( stmt );
            readMessageSizeUnits( stmt );
            readSourceAlignment( stmt );
            readTargetAlignment( stmt );
            readSourceAlignmentMode( stmt );
            readTargetAlignmentMode( stmt );
            readSourceVerificationOrTouching( stmt );
            readTargetVerificationOrTouching( stmt );
            readSourceAlignmentUnits( stmt );
            readTargetAlignmentUnits( stmt );
            readSourceBuffer( stmt );
            readTargetBuffer( stmt );

            readVariablesInScope( stmt );
        }

        // if one ore more CommunicationStmt's are selected, then
        // display the dialog
        if( selectedCommunicationStmts.size() > 0 )
            defaultMode( false );
    }

    // deselect all tasks
    public void deselectAllTasks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Task ){
                component.setSelected( false );
            }
        }
    }

    // get all selected tasks
    public Vector getSelectedTasks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedTasks = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Task )
                selectedTasks.add( component );
        }
        return selectedTasks;
    }

    // not currently needed because the dialog is displayed in
    // dialogPane of the main window
    public void windowClosing( WindowEvent event ) {
        deselectAllTasks();
        updateState();
        program.repaint();
    }

    // the following methods read the fields of a CommunicationStmt
    // and translate it into the value to set in the corrseponding Swing
    // component, "-" is a special value used internally used to
    // represent mixed state and that this field should not be changed
    // when the "Apply" button is pressed.

    private void readSourceGroup( CommunicationStmt stmt ){
        if( selectSourceGroup == null )
            selectSourceGroup = stmt.getTaskGroup().toCodeSource();
        else if( !selectSourceGroup.equals( stmt.getTaskGroup().toCodeSource() ) )
            selectSourceGroup = "-";
    }

    private void readTargetGroup( CommunicationStmt stmt ){
        if( selectTargetGroup == null )
            selectTargetGroup = stmt.getTaskGroup().toCodeTarget();
        else if( !selectTargetGroup.equals( stmt.getTaskGroup().toCodeTarget() ) )
            selectTargetGroup = "-";
    }

    private void readSourceAsync( CommunicationStmt stmt ){
        if( isFirstSourceAsync )
            selectSourceAsync = stmt.getSourceAsync();
        else if( selectSourceAsync != stmt.getSourceAsync() )
            isMixedSourceAsync = true;
        isFirstSourceAsync = false;
    }

    private void readTargetAsync( CommunicationStmt stmt ){
        if( isFirstTargetAsync )
            selectTargetAsync = stmt.getTargetAsync();
        else if( selectTargetAsync != stmt.getTargetAsync() )
            isMixedTargetAsync = true;
        isFirstTargetAsync = false;
    }

    private void readSourceUniqueBuffer( CommunicationStmt stmt ){
        if( isFirstSourceUniqueBuffer )
            selectSourceUniqueBuffer = stmt.getSourceUniqueBuffer();
        else if( selectSourceUniqueBuffer != stmt.getSourceUniqueBuffer() )
            isMixedSourceUniqueBuffer = true;
        isFirstSourceUniqueBuffer = false;
    }

    private void readTargetUniqueBuffer( CommunicationStmt stmt ){
        if( isFirstTargetUniqueBuffer )
            selectTargetUniqueBuffer = stmt.getTargetUniqueBuffer();
        else if( selectTargetUniqueBuffer != stmt.getTargetUniqueBuffer() )
            isMixedTargetUniqueBuffer = true;
        isFirstTargetUniqueBuffer = false;
    }

    private void readMessageCount( CommunicationStmt stmt ){
        if( selectMessageCount == null )
            selectMessageCount = stmt.getMessageCount();
        else if( !selectMessageCount.equals( stmt.getMessageCount() ) )
            selectMessageCount = "-";
    }

    private void readMessageSize( CommunicationStmt stmt ){
        if( selectMessageSize == null )
            selectMessageSize = stmt.getMessageSize();
        else if( !selectMessageSize.equals( stmt.getMessageSize() ) )
            selectMessageSize = "-";
    }

    private void readMessageSizeUnits( CommunicationStmt stmt ){
        if( selectMessageSizeUnits == null )
            selectMessageSizeUnits = stmt.getMessageSizeUnits();
        else if( !selectMessageSizeUnits.equals( stmt.getMessageSizeUnits() ) )
            selectMessageSizeUnits = "-";
    }

    private void readSourceAlignment( CommunicationStmt stmt ){
        if( selectSourceAlignment == null )
            selectSourceAlignment = stmt.getSourceAlignment();
        else if( !selectSourceAlignment.equals( stmt.getSourceAlignment() ) )
            selectSourceAlignment = "-";
    }

    private void readTargetAlignment( CommunicationStmt stmt ){
        if( selectTargetAlignment == null )
            selectTargetAlignment = stmt.getTargetAlignment();
        else if( !selectTargetAlignment.equals( stmt.getTargetAlignment() ) )
            selectTargetAlignment = "-";
    }

    private void readSourceAlignmentMode( CommunicationStmt stmt ){
        if( selectSourceAlignmentMode == null )
            selectSourceAlignmentMode = stmt.getSourceAlignmentMode();
        else if( !selectSourceAlignmentMode.equals( stmt.getSourceAlignmentMode() ) )
            selectSourceAlignmentMode = "-";
    }

    private void readTargetAlignmentMode( CommunicationStmt stmt ){
        if( selectTargetAlignmentMode == null )
            selectTargetAlignmentMode = stmt.getTargetAlignmentMode();
        else if( !selectTargetAlignmentMode.equals( stmt.getTargetAlignmentMode() ) )
            selectTargetAlignmentMode = "-";
    }

    private void readSourceVerificationOrTouching( CommunicationStmt stmt ){
        if( selectSourceVerificationOrTouching == null )
            selectSourceVerificationOrTouching = stmt.getSourceVerificationOrTouching();
        else if( !selectSourceVerificationOrTouching.equals( stmt.getSourceVerificationOrTouching() ) )
            selectSourceVerificationOrTouching = "-";
    }

    private void readTargetVerificationOrTouching( CommunicationStmt stmt ){
        if( selectTargetVerificationOrTouching == null )
            selectTargetVerificationOrTouching = stmt.getTargetVerificationOrTouching();
        else if( !selectTargetVerificationOrTouching.equals( stmt.getTargetVerificationOrTouching() ) )
            selectTargetVerificationOrTouching = "-";
    }

    private void readSourceAlignmentUnits( CommunicationStmt stmt ){
        if( selectSourceAlignmentUnits == null )
            selectSourceAlignmentUnits = stmt.getSourceAlignmentUnits();
        else if( !selectSourceAlignmentUnits.equals( stmt.getSourceAlignmentUnits() ) )
            selectSourceAlignmentUnits = "-";
    }

    private void readTargetAlignmentUnits( CommunicationStmt stmt ){
        if( selectTargetAlignmentUnits == null )
            selectTargetAlignmentUnits = stmt.getTargetAlignmentUnits();
        else if( !selectTargetAlignmentUnits.equals( stmt.getTargetAlignmentUnits() ) )
            selectTargetAlignmentUnits = "-";
    }

    private void readSourceBuffer( CommunicationStmt stmt ){
        if( selectSourceBuffer == null )
            selectSourceBuffer = stmt.getSourceBuffer();
        else if( !selectSourceBuffer.equals( stmt.getSourceBuffer() ) )
            selectSourceBuffer = "-";
    }

    private void readTargetBuffer( CommunicationStmt stmt ){
        if( selectTargetBuffer == null )
            selectTargetBuffer = stmt.getTargetBuffer();
        else if( !selectTargetBuffer.equals( stmt.getTargetBuffer() ) )
            selectTargetBuffer = "-";
    }

    // deselect all CommunicationStmt's
    public void deselectAllCommunicationStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof CommunicationStmt ){
                component.setSelected( false );
            }
        }
    }

    // get all selected CommunicationStmts's
    public Vector getSelectedCommunicationStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedCommunicationStmts = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof CommunicationStmt )
                selectedCommunicationStmts.add( component );
        }
        return selectedCommunicationStmts;
    }

    // the following writeXXX() methods apply the values in the dialog
    // fields to the selected CommunicationStmt's after the fields
    // have been verified by the verifyXXX() methods
    private void writeSourceGroup( CommunicationStmt stmt ){
        if( !selectSourceGroup.equals( "-" ) )
            stmt.setSourceGroup( selectSourceGroup );
    }

    private void writeTargetGroup( CommunicationStmt stmt ){
        if( !selectTargetGroup.equals( "-" ) )
            stmt.setTargetGroup( selectTargetGroup );
    }

    private void writeSourceAsync( CommunicationStmt stmt ){
        if( !isMixedSourceAsync )
            stmt.setSourceAsync( selectSourceAsync );
    }

    private void writeTargetAsync( CommunicationStmt stmt ){
        if( !isMixedTargetAsync )
            stmt.setTargetAsync( selectTargetAsync );
    }

    private void writeSourceUniqueBuffer( CommunicationStmt stmt ){
        if( !isMixedSourceUniqueBuffer )
            stmt.setSourceUniqueBuffer( selectSourceUniqueBuffer );
    }

    private void writeTargetUniqueBuffer( CommunicationStmt stmt ){
        if( !isMixedTargetUniqueBuffer )
            stmt.setTargetUniqueBuffer( selectTargetUniqueBuffer );
    }

    private void writeMessageCount( CommunicationStmt stmt ){
        if( !selectMessageCount.equals( "-" ) )
            stmt.setMessageCount( selectMessageCount );
    }

    private void writeMessageSize( CommunicationStmt stmt ){
        if( !selectMessageSize.equals( "-" ) )
            stmt.setMessageSize( selectMessageSize );
    }

    private void writeMessageSizeUnits( CommunicationStmt stmt ){
        if( !selectMessageSizeUnits.equals( "-" ) )
            stmt.setMessageSizeUnits( selectMessageSizeUnits );
    }

    private void writeSourceAlignment( CommunicationStmt stmt ){
        if( !selectSourceAlignment.equals( "-" ) )
            stmt.setSourceAlignment( selectSourceAlignment );
    }

    private void writeTargetAlignment( CommunicationStmt stmt ){
        if( !selectTargetAlignment.equals( "-" ) )
            stmt.setTargetAlignment( selectTargetAlignment );
    }

    private void writeSourceAlignmentMode( CommunicationStmt stmt ){
        if( !selectSourceAlignmentMode.equals( "-" ) )
            stmt.setSourceAlignmentMode( selectSourceAlignmentMode );
    }

    private void writeTargetAlignmentMode( CommunicationStmt stmt ){
        if( !selectTargetAlignmentMode.equals( "-" ) )
            stmt.setTargetAlignmentMode( selectTargetAlignmentMode );
    }

    private void writeSourceVerificationOrTouching( CommunicationStmt stmt ){
        if( !selectSourceVerificationOrTouching.equals( "-" ) )
            stmt.setSourceVerificationOrTouching( selectSourceVerificationOrTouching );
    }

    private void writeTargetVerificationOrTouching( CommunicationStmt stmt ){
        if( !selectTargetVerificationOrTouching.equals( "-" ) )
            stmt.setTargetVerificationOrTouching( selectTargetVerificationOrTouching );
    }

    private void writeSourceAlignmentUnits( CommunicationStmt stmt ){
        if( !selectSourceAlignmentUnits.equals( "-" ) )
            stmt.setSourceAlignmentUnits( selectSourceAlignmentUnits );
    }

    private void writeTargetAlignmentUnits( CommunicationStmt stmt ){
        if( !selectTargetAlignmentUnits.equals( "-" ) )
            stmt.setTargetAlignmentUnits( selectTargetAlignmentUnits );
    }

    private void writeSourceBuffer( CommunicationStmt stmt ){
        if( !selectSourceBuffer.equals( "-" ) )
            stmt.setSourceBuffer( selectSourceBuffer );
    }

    private void writeTargetBuffer( CommunicationStmt stmt ){
        if( !selectTargetBuffer.equals( "-" ) )
            stmt.setTargetBuffer( selectTargetBuffer );
    }

    // the following makeDefaultXXX() methods are called when
    // the "Make Default" button is clicked to set the the defaults
    // associatied with CommunicationStmt as static values
    private void makeDefaultSourceAsync(){
        if( !isMixedSourceAsync )
            CommunicationStmt.setDefaultSourceAsync( selectSourceAsync );
    }

    private void makeDefaultTargetAsync(){
        if( !isMixedTargetAsync )
            CommunicationStmt.setDefaultTargetAsync( selectTargetAsync );
    }

    private void makeDefaultSourceUniqueBuffer(){
        if( !isMixedSourceUniqueBuffer )
            CommunicationStmt.setDefaultSourceUniqueBuffer( selectSourceUniqueBuffer );
    }

    private void makeDefaultTargetUniqueBuffer(){
        if( !isMixedTargetUniqueBuffer )
            CommunicationStmt.setDefaultTargetUniqueBuffer( selectTargetUniqueBuffer );
    }

    private void makeDefaultMessageCount(){
        if( !selectMessageCount.equals( "-" ) )
            CommunicationStmt.setDefaultMessageCount( selectMessageCount );
    }

    private void makeDefaultMessageSize(){
        if( !selectMessageSize.equals( "-" ) )
            CommunicationStmt.setDefaultMessageSize( selectMessageSize );
    }

    private void makeDefaultMessageSizeUnits(){
        if( !selectMessageSizeUnits.equals( "-" ) )
            CommunicationStmt.setDefaultMessageSizeUnits( selectMessageSizeUnits );
    }

    private void makeDefaultSourceAlignment(){
        if( !selectSourceAlignment.equals( "-" ) )
            CommunicationStmt.setDefaultSourceAlignment( selectSourceAlignment );
    }

    private void makeDefaultTargetAlignment(){
        if( !selectTargetAlignment.equals( "-" ) )
            CommunicationStmt.setDefaultTargetAlignment( selectTargetAlignment );
    }

    private void makeDefaultSourceAlignmentMode(){
        if( !selectSourceAlignmentMode.equals( "-" ) )
            CommunicationStmt.setDefaultSourceAlignmentMode( selectSourceAlignmentMode );
    }

    private void makeDefaultTargetAlignmentMode(){
        if( !selectTargetAlignmentMode.equals( "-" ) )
            CommunicationStmt.setDefaultTargetAlignmentMode( selectTargetAlignmentMode );
    }

    private void makeDefaultSourceVerificationOrTouching(){
        if( !selectSourceVerificationOrTouching.equals( "-" ) )
            CommunicationStmt.setDefaultSourceVerificationOrTouching( selectSourceVerificationOrTouching );
    }

    private void makeDefaultTargetVerificationOrTouching(){
        if( !selectTargetVerificationOrTouching.equals( "-" ) )
            CommunicationStmt.setDefaultTargetVerificationOrTouching( selectTargetVerificationOrTouching );
    }

    private void makeDefaultSourceAlignmentUnits(){
        if( !selectSourceAlignmentUnits.equals( "-" ) )
            CommunicationStmt.setDefaultSourceAlignmentUnits( selectSourceAlignmentUnits );
    }

    private void makeDefaultTargetAlignmentUnits(){
        if( !selectTargetAlignmentUnits.equals( "-" ) )
            CommunicationStmt.setDefaultTargetAlignmentUnits( selectTargetAlignmentUnits );
    }

    private void makeDefaultSourceBuffer(){
        if( !selectSourceBuffer.equals( "-" ) )
            CommunicationStmt.setDefaultSourceBuffer( selectSourceBuffer );
    }

    private void makeDefaultTargetBuffer(){
        if( !selectTargetBuffer.equals( "-" ) )
            CommunicationStmt.setDefaultTargetBuffer( selectTargetBuffer );
    }

    // apply the fields of the dialog to the currently selected
    // CommunicationStmt's after they have been verified
    private void applyChanges( Vector communicationStmts ){
        for( int i = 0; i < communicationStmts.size(); i++ ){
            CommunicationStmt stmt =
                (CommunicationStmt)communicationStmts.elementAt( i );
            writeSourceGroup( stmt );
            writeTargetGroup( stmt );
            writeSourceAsync( stmt );
            writeTargetAsync( stmt );
            writeSourceUniqueBuffer( stmt );
            writeTargetUniqueBuffer( stmt );
            writeMessageCount( stmt );
            writeMessageSize( stmt );
            writeMessageSizeUnits( stmt );
            writeSourceAlignment( stmt );
            writeTargetAlignment( stmt );
            writeSourceAlignmentMode( stmt );
            writeTargetAlignmentMode( stmt );
            writeSourceVerificationOrTouching( stmt );
            writeTargetVerificationOrTouching( stmt );
            writeSourceAlignmentUnits( stmt );
            writeTargetAlignmentUnits( stmt );
            writeSourceBuffer( stmt );
            writeTargetBuffer( stmt );
        }
    }

    // set defaults for the CommunicationStmt
    private void makeDefault(){
        makeDefaultSourceAsync();
        makeDefaultTargetAsync();
        makeDefaultSourceUniqueBuffer();
        makeDefaultTargetUniqueBuffer();
        makeDefaultMessageCount();
        makeDefaultMessageSize();
        makeDefaultMessageSizeUnits();
        makeDefaultSourceAlignment();
        makeDefaultTargetAlignment();
        makeDefaultSourceAlignmentMode();
        makeDefaultTargetAlignmentMode();
        makeDefaultSourceVerificationOrTouching();
        makeDefaultTargetVerificationOrTouching();
        makeDefaultSourceAlignmentUnits();
        makeDefaultTargetAlignmentUnits();
        makeDefaultSourceBuffer();
        makeDefaultTargetBuffer();
    }

    // the following verifyXXX() methods verify the various
    // fields of the dialog via program.verifyField() which
    // passes the field to the parser for verification as the
    // appropriate start type. if verification failed then an
    // error dialog is displayed

    private boolean verifySourceGroup(){
        selectSourceGroup = (String)sourceGroup.getSelectedItem();
        if( program.verifyField( selectSourceGroup, "source_task",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectSourceGroup +
                                     "\" is not a valid source task description" );
            return false;
        }
    }

    private boolean verifyTargetGroup(){
        selectTargetGroup = (String)targetGroup.getSelectedItem();
        if( program.verifyField( selectTargetGroup, "target_task",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTargetGroup +
                                     "\" is not a valid target task description" );
            return false;
        }
    }

    private boolean verifySourceAsync(){
        if( !isMixedSourceAsync )
            selectSourceAsync = sourceAsync.isSelected();
        return true;
    }

    private boolean verifyTargetAsync(){
        if( !isMixedTargetAsync ){
            if( useSourceAttributes.isSelected() )
                selectTargetAsync = selectSourceAsync;
            else
                selectTargetAsync = targetAsync.isSelected();
        }
        return true;
    }

    private boolean verifySourceUniqueBuffer(){
        if( !isMixedSourceUniqueBuffer )
            selectSourceUniqueBuffer = sourceUniqueBuffer.isSelected();
        return true;
    }

    private boolean verifyTargetUniqueBuffer(){
        if( !isMixedTargetUniqueBuffer ){
            if( useSourceAttributes.isSelected() )
                selectTargetUniqueBuffer = selectSourceUniqueBuffer;
            else
                selectTargetUniqueBuffer = targetUniqueBuffer.isSelected();
        }
        return true;
    }

    private boolean verifyMessageCount(){
        selectMessageCount = (String)messageCount.getSelectedItem();
        if( program.verifyField( selectMessageCount, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectMessageCount +
                                     "\" is not a valid expression for message count" );
            return false;
        }
    }

    private boolean verifyMessageSize(){
        selectMessageSize = (String)messageSize.getSelectedItem();
        if( program.verifyField( selectMessageSize, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectMessageSize +
                                     "\" is not a valid expression for message size" );
            return false;
        }
    }

    private boolean verifyMessageSizeUnits(){
        selectMessageSizeUnits = (String)messageSizeUnits.getSelectedItem();
        return true;
    }

    private boolean verifySourceAlignment(){
        selectSourceAlignment = (String)sourceAlignment.getSelectedItem();
        if( program.verifyField( selectSourceAlignment, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectSourceAlignment +
                                     "\" is not a valid expression for source alignment" );
            return false;
        }
    }

    private boolean verifyTargetAlignment(){
        if( useSourceAttributes.isSelected() ){
            selectTargetAlignment = selectSourceAlignment;
            return true;
        }
        selectTargetAlignment = (String)targetAlignment.getSelectedItem();
        if( program.verifyField( selectTargetAlignment, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTargetAlignment +
                                     "\" is not a valid expression for target alignment" );
            return false;
        }
    }

    private boolean verifySourceAlignmentMode(){
        selectSourceAlignmentMode = (String)sourceAlignmentMode.getSelectedItem();
        return true;
    }

    private boolean verifyTargetAlignmentMode(){
        if( useSourceAttributes.isSelected() )
            selectTargetAlignmentMode = selectSourceAlignmentMode;
        else
            selectTargetAlignmentMode =
                (String)targetAlignmentMode.getSelectedItem();
        return true;
    }

    private boolean verifySourceVerificationOrTouching(){
        selectSourceVerificationOrTouching = (String)sourceVerificationOrTouching.getSelectedItem();
        return true;
    }

    private boolean verifyTargetVerificationOrTouching(){
        if( useSourceAttributes.isSelected() )
            selectTargetVerificationOrTouching =
                selectSourceVerificationOrTouching;
        else
            selectTargetVerificationOrTouching = (String)targetVerificationOrTouching.getSelectedItem();
        return true;
    }

    private boolean verifySourceAlignmentUnits(){
        selectSourceAlignmentUnits = (String)sourceAlignmentUnits.getSelectedItem();
        return true;
    }

    private boolean verifyTargetAlignmentUnits(){
        if( useSourceAttributes.isSelected() )
            selectTargetAlignmentUnits =
                selectSourceAlignmentUnits;
        else
            selectTargetAlignmentUnits =
                (String)targetAlignmentUnits.getSelectedItem();
        return true;
    }

    private boolean verifySourceBuffer(){
        selectSourceBuffer = (String)sourceBuffer.getSelectedItem();
        if( selectSourceBuffer.equals( "default" ) ||
            program.verifyField( selectSourceBuffer, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectSourceBuffer +
                                     "\" is not a valid expression for source buffer" );
            return false;
        }
    }

    private boolean verifyTargetBuffer(){
        if( useSourceAttributes.isSelected() ){
            selectTargetBuffer = selectSourceBuffer;
            return true;
        }
        selectTargetBuffer = (String)targetBuffer.getSelectedItem();
        if( selectTargetBuffer.equals( "default" ) ||
            program.verifyField( selectTargetBuffer, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTargetBuffer +
                                     "\" is not a valid expression for target buffer" );
            return false;
        }
    }

    // verify all the fields of the dialog by calling
    // each of the verifyXXX() methods
    private boolean verifyFields(){
        if( verifySourceGroup() &&
            verifyTargetGroup() &&
            verifySourceAsync() &&
            verifySourceUniqueBuffer() &&
            verifyMessageCount() &&
            verifyMessageSize() &&
            verifyMessageSizeUnits() &&
            verifySourceAlignment() &&
            verifySourceAlignmentMode() &&
            verifySourceVerificationOrTouching() &&
            verifySourceAlignmentUnits() &&
            verifySourceBuffer() &&
            verifyTargetAsync() &&
            verifyTargetUniqueBuffer() &&
            verifyTargetAlignment() &&
            verifyTargetAlignmentMode() &&
            verifyTargetVerificationOrTouching() &&
            verifyTargetAlignmentUnits() &&
            verifyTargetBuffer() )
            return true;
        return false;
    }

    // determine the variables in stmt's scope
    private void readVariablesInScope( CommunicationStmt stmt ){
        selectVariablesInScope =
            stmt.getVariablesInScope( selectVariablesInScope );
    }

    // add the scope variables to a DialogMenu
    private void addScopeVariables( DialogMenu menu ){
        for( int i = 0; i < selectVariablesInScope.size(); i++ ){
            String variable =
                (String)selectVariablesInScope.elementAt( i );
            menu.addItem( variable );
        }
    }

}
