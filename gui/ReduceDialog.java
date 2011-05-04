/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: reduce dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class implements the dialog for manipulating a ReduceStmt. The
 * implementation details are similar to CommunicationDialog, see the
 * comments in CommunicationDialog.java for more information.
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2009, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2009).  Los Alamos National Security, LLC.  This software
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
 * ----------------------------------------------------------------------
 */

package gov.lanl.c3.ncptl;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;

import java.util.*;

public class ReduceDialog extends AbstractDialog {

    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;

    private int mode;

    private DialogPane dialogPane;

    private DialogMenu sourceGroup;
    private DialogMenu targetGroup;
    private JCheckBox sourceUniqueBuffer;
    private JCheckBox targetUniqueBuffer;
    private DialogMenu sourceCount;
    private DialogMenu targetCount;
    private DialogMenu sourceUnits;
    private DialogMenu targetUnits;
    private DialogMenu sourceAlignment;
    private DialogMenu targetAlignment;
    private DialogMenu sourceAlignmentUnits;
    private DialogMenu targetAlignmentUnits;
    private DialogMenu sourceAlignmentMode;
    private DialogMenu targetAlignmentMode;
    private JCheckBox sourceDataTouching;
    private JCheckBox targetDataTouching;
    private DialogMenu sourceBuffer;
    private DialogMenu targetBuffer;
    private JCheckBox useSourceAttributes;

    // source fields
    private String selectSourceGroup;
    private String selectSourceCount;
    private boolean selectSourceUniqueBuffer;
    private String selectSourceAlignment;
    private String selectSourceAlignmentUnits;
    private String selectSourceAlignmentMode;
    private String selectSourceUnits;
    private boolean selectSourceDataTouching;
    private String selectSourceBuffer;

    // target fields
    private String selectTargetGroup;
    private String selectTargetCount;
    private boolean selectTargetUniqueBuffer;
    private String selectTargetAlignment;
    private String selectTargetAlignmentUnits;
    private String selectTargetAlignmentMode;
    private String selectTargetUnits;
    private boolean selectTargetDataTouching;
    private String selectTargetBuffer;

    private Vector selectVariablesInScope;

    private boolean isMixedSourceDataTouching;
    private boolean isMixedTargetDataTouching;
    private boolean isMixedSourceUniqueBuffer;
    private boolean isMixedTargetUniqueBuffer;
    private boolean isFirstSourceDataTouching;
    private boolean isFirstTargetDataTouching;
    private boolean isFirstSourceUniqueBuffer;
    private boolean isFirstTargetUniqueBuffer;

    public ReduceDialog( Program program, DialogPane dialogPane ){
        super( program );
        this.dialogPane = dialogPane;
    }

    public void actionPerformed( ActionEvent event ){
        if( mode == MODE_INIT )
            return;

        String command = event.getActionCommand();
        Object source = event.getSource();

        if( command.equals( "Apply" ) ){
            if( verifyFields() ){
                program.pushState();
                applyChanges( getSelectedReduceStmts() );
                updateState();
                program.updateState();
                program.repaint();
            }
        }

        else if( command.equals( "Reset" ) )
            updateState();
        else if( source == sourceDataTouching )
            isMixedSourceDataTouching = false;
        else if( source == targetDataTouching )
            isMixedTargetDataTouching = false;
        else if( source == sourceUniqueBuffer )
            isMixedSourceUniqueBuffer = false;
        else if( source == targetUniqueBuffer )
            isMixedTargetUniqueBuffer = false;
        else if( source == useSourceAttributes ){
            verifySourceGroup();
            verifySourceUniqueBuffer();
            verifySourceCount();
            verifySourceAlignment();
            verifySourceAlignmentUnits();
            verifySourceAlignmentMode();
            verifySourceDataTouching();
            verifySourceBuffer();
            verifySourceUnits();

            selectTargetUniqueBuffer = selectSourceUniqueBuffer;
            selectTargetCount = selectSourceCount;
            selectTargetAlignment = selectSourceAlignment;
            selectTargetAlignmentUnits = selectSourceAlignmentUnits;
            selectTargetAlignmentMode = selectSourceAlignmentMode;
            selectTargetDataTouching = selectSourceDataTouching;
            selectTargetBuffer = selectSourceBuffer;
            selectTargetUnits = selectSourceUnits;

            defaultMode( !useSourceAttributes.isSelected() );
        }
    }

    public void defaultMode( boolean showTargetAttributes ){
        mode = MODE_INIT;

        dialogPane.clear();

        // source attributes

        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "source: " ) );

        sourceGroup = new DialogMenu( 430 );
        sourceGroup.addItem( selectSourceGroup );
        sourceGroup.addSourceTaskDescriptions();
        sourceGroup.setEditable( true );

        sourceGroup.setSelectedIndex( 0 );
        pane1.add( sourceGroup );

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        pane2.add( new JLabel( "count: " ) );
        sourceCount = new DialogMenu( 150 );
        sourceCount.addItem( selectSourceCount );
        addScopeVariables( sourceCount );
        sourceCount.setEditable( true );
        pane2.add( sourceCount );

        sourceUnits = new DialogMenu();
        sourceUnits.addItem( selectSourceUnits );
        sourceUnits.addItem( "integers" );
        sourceUnits.addItem( "doublewords" );
        pane2.add( sourceUnits );

        sourceUniqueBuffer = new JCheckBox();
        sourceUniqueBuffer.setSelected( selectSourceUniqueBuffer );

        pane2.add( sourceUniqueBuffer );

        pane2.add( new JLabel( "unique buffer" ) );

        sourceDataTouching = new JCheckBox();
        sourceDataTouching.setSelected( selectSourceDataTouching );

        pane2.add( sourceDataTouching );

        pane2.add( new JLabel( "with data touching" ) );

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

        dialogPane.add( new JSeparator() );

        // target attributes

        JPanel pane4 = new JPanel();
        pane4.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane4 );

        pane4.add( new JLabel( "target: " ) );

        targetGroup = new DialogMenu( 430 );
        targetGroup.addItem( selectTargetGroup );
        targetGroup.addSourceTaskDescriptions();
        targetGroup.setEditable( true );
        pane4.add( targetGroup );

        useSourceAttributes = new JCheckBox();

        if( !showTargetAttributes &&
            selectSourceCount.equals( selectTargetCount ) &&
            selectSourceUnits.equals( selectTargetUnits ) &&
            selectSourceUniqueBuffer == selectTargetUniqueBuffer &&
            selectSourceAlignment.equals( selectTargetAlignment ) &&
            selectSourceAlignmentUnits.equals( selectTargetAlignmentUnits ) &&
            selectSourceAlignmentMode.equals( selectTargetAlignmentMode ) &&
            selectSourceDataTouching == selectTargetDataTouching &&
            selectSourceBuffer.equals( selectTargetBuffer ) )
            useSourceAttributes.setSelected( true );

        pane4.add( useSourceAttributes );
        pane4.add( new JLabel( "use source attributes" ) );
        useSourceAttributes.addActionListener( this );

        if( !useSourceAttributes.isSelected() ){
            JPanel pane6 = new JPanel();
            pane6.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( pane6 );

            pane6.add( new JLabel( "count: " ) );
            targetCount = new DialogMenu( 150 );
            targetCount.addItem( selectTargetCount );
            addScopeVariables( targetCount );
            targetCount.setEditable( true );
            pane6.add( targetCount );

            targetUnits = new DialogMenu();
            targetUnits.addItem( selectTargetUnits );
            targetUnits.addItem( "integers" );
            targetUnits.addItem( "doublewords" );
            pane6.add( targetUnits );

            targetUniqueBuffer = new JCheckBox();
            targetUniqueBuffer.setSelected( selectTargetUniqueBuffer );

            pane6.add( targetUniqueBuffer );

            pane6.add( new JLabel( "unique buffer" ) );

            targetDataTouching = new JCheckBox();
            targetDataTouching.setSelected( selectTargetDataTouching );

            pane6.add( targetDataTouching );
            pane6.add( new JLabel( "with data touching" ) );

            JPanel pane7 = new JPanel();
            pane7.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( pane7 );

            targetAlignment = new DialogMenu( 150 );
            targetAlignment.addItem( selectTargetAlignment );
            addScopeVariables( targetAlignment );
            targetAlignment.setEditable( true );

            pane7.add( targetAlignment );

            targetAlignmentUnits = new DialogMenu();
            targetAlignmentUnits.addItem( selectTargetAlignmentUnits );
            targetAlignmentUnits.addSizeUnits();
            pane7.add( targetAlignmentUnits );

            targetAlignmentMode = new DialogMenu();
            targetAlignmentMode.addItem( selectTargetAlignmentMode );
            targetAlignmentMode.addItem( "unaligned" );
            targetAlignmentMode.addItem( "aligned" );
            targetAlignmentMode.addItem( "misaligned" );
            pane7.add( targetAlignmentMode );

            pane7.add( new JLabel( "buffer: " ) );
            targetBuffer = new DialogMenu( 150 );
            targetBuffer.addItem( selectTargetBuffer );
            targetBuffer.addItem( "default" );
            targetBuffer.setEditable( true );
            pane7.add( targetBuffer );
        }

        JPanel pane8 = new JPanel();
        pane8.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane8 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        pane8.add( applyButton );
        pane8.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_DEFAULT;
    }

    public void updateState(){
        selectSourceGroup = null;
        selectTargetGroup = null;

        isMixedSourceDataTouching = false;
        isMixedTargetDataTouching = false;
        isMixedSourceUniqueBuffer = false;
        isMixedTargetUniqueBuffer = false;

        isFirstSourceDataTouching = true;
        isFirstTargetDataTouching = true;
        isFirstSourceUniqueBuffer = true;
        isFirstTargetUniqueBuffer = true;

        selectSourceUniqueBuffer = false;
        selectTargetUniqueBuffer = false;

        selectSourceCount = null;
        selectTargetCount = null;
        selectSourceUnits = null;
        selectTargetUnits = null;
        selectSourceAlignment = null;
        selectTargetAlignment = null;
        selectSourceAlignmentUnits = null;
        selectTargetAlignmentUnits = null;
        selectSourceAlignmentMode = null;
        selectTargetAlignmentMode = null;
        selectSourceBuffer = null;
        selectTargetBuffer = null;

        selectVariablesInScope = new Vector();

        Vector selectedReduceStmts = getSelectedReduceStmts();

        for( int i = 0; i < selectedReduceStmts.size(); i++ ){
            ReduceStmt stmt =
                (ReduceStmt)selectedReduceStmts.elementAt( i );

            readSourceGroup( stmt );
            readTargetGroup( stmt );
            readSourceDataTouching( stmt );
            readTargetDataTouching( stmt );
            readSourceUniqueBuffer( stmt );
            readTargetUniqueBuffer( stmt );
            readSourceCount( stmt );
            readTargetCount( stmt );
            readSourceUnits( stmt );
            readTargetUnits( stmt );
            readSourceAlignment( stmt );
            readTargetAlignment( stmt );
            readSourceAlignmentUnits( stmt );
            readTargetAlignmentUnits( stmt );
            readSourceAlignmentMode( stmt );
            readTargetAlignmentMode( stmt );
            readSourceDataTouching( stmt );
            readTargetDataTouching( stmt );
            readSourceBuffer( stmt );
            readTargetBuffer( stmt );

            readVariablesInScope( stmt );
        }

        if( selectedReduceStmts.size() > 0 )
            defaultMode( false );
    }

    public void deselectAllReduceStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof ReduceStmt ){
                component.setSelected( false );
            }
        }
    }

    public Vector getSelectedReduceStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedTasks = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof ReduceStmt )
                selectedTasks.add( component );
        }
        return selectedTasks;
    }

    public void windowClosing( WindowEvent event ) {
        deselectAllReduceStmts();
        updateState();
        program.updateState();
        program.repaint();
    }

    // readXXX() methods

    private void readSourceGroup( ReduceStmt stmt ){
        if( selectSourceGroup == null )
            selectSourceGroup = stmt.getTaskGroup().toCodeSource();
        else if( !selectSourceGroup.equals( stmt.getTaskGroup().toCodeSource() ) )
            selectSourceGroup = "-";
    }

    private void readTargetGroup( ReduceStmt stmt ){
        if( selectTargetGroup == null )
            selectTargetGroup = stmt.getTaskGroup().toCodeTarget();
        else if( !selectTargetGroup.equals( stmt.getTaskGroup().toCodeTarget() ) )
            selectTargetGroup = "-";
    }

    private void readSourceDataTouching( ReduceStmt stmt ){
        if( isFirstSourceDataTouching )
            selectSourceDataTouching = stmt.getSourceDataTouching();
        else if( selectSourceDataTouching != stmt.getSourceDataTouching() )
            isMixedSourceDataTouching = true;
        isFirstSourceDataTouching = false;
    }

    private void readTargetDataTouching( ReduceStmt stmt ){
        if( isFirstTargetDataTouching )
            selectTargetDataTouching = stmt.getTargetDataTouching();
        else if( selectTargetDataTouching != stmt.getTargetDataTouching() )
            isMixedTargetDataTouching = true;
        isFirstTargetDataTouching = false;
    }

    private void readSourceUniqueBuffer( ReduceStmt stmt ){
        if( isFirstSourceUniqueBuffer )
            selectSourceUniqueBuffer = stmt.getSourceUniqueBuffer();
        else if( selectSourceUniqueBuffer != stmt.getSourceUniqueBuffer() )
            isMixedSourceUniqueBuffer = true;
        isFirstSourceUniqueBuffer = false;
    }

    private void readTargetUniqueBuffer( ReduceStmt stmt ){
        if( isFirstTargetUniqueBuffer )
            selectTargetUniqueBuffer = stmt.getTargetUniqueBuffer();
        else if( selectTargetUniqueBuffer != stmt.getTargetUniqueBuffer() )
            isMixedTargetUniqueBuffer = true;
        isFirstTargetUniqueBuffer = false;
    }

    private void readSourceCount( ReduceStmt stmt ){
        if( selectSourceCount == null )
            selectSourceCount = stmt.getSourceCount();
        else if( !selectSourceCount.equals( stmt.getSourceCount() ) )
            selectSourceCount = "-";
    }

    private void readTargetCount( ReduceStmt stmt ){
        if( selectTargetCount == null )
            selectTargetCount = stmt.getTargetCount();
        else if( !selectTargetCount.equals( stmt.getTargetCount() ) )
            selectTargetCount = "-";
    }

    private void readSourceUnits( ReduceStmt stmt ){
        if( selectSourceUnits == null )
            selectSourceUnits = stmt.getSourceUnits();
        else if( !selectSourceUnits.equals( stmt.getSourceUnits() ) )
            selectSourceUnits = "-";
    }

    private void readTargetUnits( ReduceStmt stmt ){
        if( selectTargetUnits == null )
            selectTargetUnits = stmt.getTargetUnits();
        else if( !selectTargetUnits.equals( stmt.getTargetUnits() ) )
            selectTargetUnits = "-";
    }

    private void readSourceAlignment( ReduceStmt stmt ){
        if( selectSourceAlignment == null )
            selectSourceAlignment = stmt.getSourceAlignment();
        else if( !selectSourceAlignment.equals( stmt.getSourceAlignment() ) )
            selectSourceAlignment = "-";
    }

    private void readTargetAlignment( ReduceStmt stmt ){
        if( selectTargetAlignment == null )
            selectTargetAlignment = stmt.getTargetAlignment();
        else if( !selectTargetAlignment.equals( stmt.getTargetAlignment() ) )
            selectTargetAlignment = "-";
    }

    private void readSourceAlignmentMode( ReduceStmt stmt ){
        if( selectSourceAlignmentMode == null )
            selectSourceAlignmentMode = stmt.getSourceAlignmentMode();
        else if( !selectSourceAlignmentMode.equals( stmt.getSourceAlignmentMode() ) )
            selectSourceAlignmentMode = "-";
    }

    private void readTargetAlignmentMode( ReduceStmt stmt ){
        if( selectTargetAlignmentMode == null )
            selectTargetAlignmentMode = stmt.getTargetAlignmentMode();
        else if( !selectTargetAlignmentMode.equals( stmt.getTargetAlignmentMode() ) )
            selectTargetAlignmentMode = "-";
    }

    private void readSourceAlignmentUnits( ReduceStmt stmt ){
        if( selectSourceAlignmentUnits == null )
            selectSourceAlignmentUnits = stmt.getSourceAlignmentUnits();
        else if( !selectSourceAlignmentUnits.equals( stmt.getSourceAlignmentUnits() ) )
            selectSourceAlignmentUnits = "-";
    }

    private void readTargetAlignmentUnits( ReduceStmt stmt ){
        if( selectTargetAlignmentUnits == null )
            selectTargetAlignmentUnits = stmt.getTargetAlignmentUnits();
        else if( !selectTargetAlignmentUnits.equals( stmt.getTargetAlignmentUnits() ) )
            selectTargetAlignmentUnits = "-";
    }

    private void readSourceBuffer( ReduceStmt stmt ){
        if( selectSourceBuffer == null )
            selectSourceBuffer = stmt.getSourceBuffer();
        else if( !selectSourceBuffer.equals( stmt.getSourceBuffer() ) )
            selectSourceBuffer = "-";
    }

    private void readTargetBuffer( ReduceStmt stmt ){
        if( selectTargetBuffer == null )
            selectTargetBuffer = stmt.getTargetBuffer();
        else if( !selectTargetBuffer.equals( stmt.getTargetBuffer() ) )
            selectTargetBuffer = "-";
    }


    // writeXXX() methods

    private void writeSourceGroup( ReduceStmt stmt ){
        if( !selectSourceGroup.equals( "-" ) )
            stmt.setSourceGroup( selectSourceGroup );
    }

    private void writeTargetGroup( ReduceStmt stmt ){
        if( !selectTargetGroup.equals( "-" ) )
            stmt.setTargetGroup( selectTargetGroup );
    }

    private void writeSourceDataTouching( ReduceStmt stmt ){
        if( !isMixedSourceDataTouching )
            stmt.setSourceDataTouching( selectSourceDataTouching );
    }

    private void writeTargetDataTouching( ReduceStmt stmt ){
        if( !isMixedTargetDataTouching )
            stmt.setTargetDataTouching( selectTargetDataTouching );
    }

    private void writeSourceUniqueBuffer( ReduceStmt stmt ){
        if( !isMixedSourceUniqueBuffer )
            stmt.setSourceUniqueBuffer( selectSourceUniqueBuffer );
    }

    private void writeTargetUniqueBuffer( ReduceStmt stmt ){
        if( !isMixedTargetUniqueBuffer )
            stmt.setTargetUniqueBuffer( selectTargetUniqueBuffer );
    }

    private void writeSourceCount( ReduceStmt stmt ){
        if( !selectSourceCount.equals( "-" ) )
            stmt.setSourceCount( selectSourceCount );
    }

    private void writeTargetCount( ReduceStmt stmt ){
        if( !selectTargetCount.equals( "-" ) )
            stmt.setTargetCount( selectTargetCount );
    }

    private void writeSourceUnits( ReduceStmt stmt ){
        if( !selectSourceUnits.equals( "-" ) )
            stmt.setSourceUnits( selectSourceUnits );
    }

    private void writeTargetUnits( ReduceStmt stmt ){
        if( !selectTargetUnits.equals( "-" ) )
            stmt.setTargetUnits( selectTargetUnits );
    }

    private void writeSourceAlignment( ReduceStmt stmt ){
        if( !selectSourceAlignment.equals( "-" ) )
            stmt.setSourceAlignment( selectSourceAlignment );
    }

    private void writeTargetAlignment( ReduceStmt stmt ){
        if( !selectTargetAlignment.equals( "-" ) )
            stmt.setTargetAlignment( selectTargetAlignment );
    }

    private void writeSourceAlignmentMode( ReduceStmt stmt ){
        if( !selectSourceAlignmentMode.equals( "-" ) )
            stmt.setSourceAlignmentMode( selectSourceAlignmentMode );
    }

    private void writeTargetAlignmentMode( ReduceStmt stmt ){
        if( !selectTargetAlignmentMode.equals( "-" ) )
            stmt.setTargetAlignmentMode( selectTargetAlignmentMode );
    }

    private void writeSourceAlignmentUnits( ReduceStmt stmt ){
        if( !selectSourceAlignmentUnits.equals( "-" ) )
            stmt.setSourceAlignmentUnits( selectSourceAlignmentUnits );
    }

    private void writeTargetAlignmentUnits( ReduceStmt stmt ){
        if( !selectTargetAlignmentUnits.equals( "-" ) )
            stmt.setTargetAlignmentUnits( selectTargetAlignmentUnits );
    }

    private void writeSourceBuffer( ReduceStmt stmt ){
        if( !selectSourceBuffer.equals( "-" ) )
            stmt.setSourceBuffer( selectSourceBuffer );
    }

    private void writeTargetBuffer( ReduceStmt stmt ){
        if( !selectTargetBuffer.equals( "-" ) )
            stmt.setTargetBuffer( selectTargetBuffer );
    }

    private void applyChanges( Vector communicationStmts ){
        for( int i = 0; i < communicationStmts.size(); i++ ){
            ReduceStmt stmt =
                (ReduceStmt)communicationStmts.elementAt( i );
            writeSourceGroup( stmt );
            writeTargetGroup( stmt );
            writeSourceDataTouching( stmt );
            writeTargetDataTouching( stmt );
            writeSourceUniqueBuffer( stmt );
            writeTargetUniqueBuffer( stmt );
            writeSourceCount( stmt );
            writeTargetCount( stmt );
            writeSourceUnits( stmt );
            writeTargetUnits( stmt );
            writeSourceAlignment( stmt );
            writeTargetAlignment( stmt );
            writeSourceAlignmentMode( stmt );
            writeTargetAlignmentMode( stmt );
            writeSourceAlignmentUnits( stmt );
            writeTargetAlignmentUnits( stmt );
            writeSourceBuffer( stmt );
            writeTargetBuffer( stmt );
        }
    }

    // verifyXXX() methods

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
        if( program.verifyField( selectSourceGroup, "source_task",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTargetGroup +
                                     "\" is not a valid target task description" );
            return false;
        }
    }

    private boolean verifySourceDataTouching(){
        if( !isMixedSourceDataTouching )
            selectSourceDataTouching = sourceDataTouching.isSelected();
        return true;
    }

    private boolean verifyTargetDataTouching(){
        if( !isMixedTargetDataTouching ){
            if( useSourceAttributes.isSelected() )
                selectTargetDataTouching = selectSourceDataTouching;
            else
                selectTargetDataTouching = targetDataTouching.isSelected();
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

    private boolean verifySourceCount(){
        selectSourceCount = (String)sourceCount.getSelectedItem();
        if( program.verifyField( selectSourceCount, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectSourceCount +
                                     "\" is not a valid expression for source count" );
            return false;
        }
    }

    private boolean verifyTargetCount(){
        if( useSourceAttributes.isSelected() ){
            selectTargetCount = selectSourceCount;
            return true;
        }

        selectTargetCount = (String)targetCount.getSelectedItem();

        if( program.verifyField( selectTargetCount, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTargetCount +
                                     "\" is not a valid expression for target count" );
            return false;
        }

    }

    private boolean verifySourceUnits(){
        selectSourceUnits = (String)sourceUnits.getSelectedItem();
        return true;
    }

    private boolean verifyTargetUnits(){
        if( useSourceAttributes.isSelected() )
            selectTargetUnits = selectSourceUnits;
        else
            selectTargetUnits = (String)targetUnits.getSelectedItem();
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

    private boolean verifyFields(){
        if( verifySourceGroup() &&
            verifyTargetGroup() &&
            verifySourceDataTouching() &&
            verifySourceUniqueBuffer() &&
            verifySourceCount() &&
            verifySourceUnits() &&
            verifySourceAlignment() &&
            verifySourceAlignmentMode() &&
            verifySourceAlignmentUnits() &&
            verifySourceBuffer() &&
            verifyTargetDataTouching() &&
            verifyTargetUniqueBuffer() &&
            verifyTargetCount() &&
            verifyTargetUnits() &&
            verifyTargetAlignment() &&
            verifyTargetAlignmentMode() &&
            verifyTargetAlignmentUnits() &&
            verifyTargetBuffer() )
            return true;
        return false;
    }

    private void readVariablesInScope( ReduceStmt stmt ){
        selectVariablesInScope =
            stmt.getVariablesInScope( selectVariablesInScope );
    }

    private void addScopeVariables( DialogMenu menu ){
        for( int i = 0; i < selectVariablesInScope.size(); i++ ){
            String variable =
                (String)selectVariablesInScope.elementAt( i );
            menu.addItem( variable );
        }
    }

}
