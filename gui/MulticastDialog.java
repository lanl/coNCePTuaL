/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: multicast dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining the dialog for
 * manipulating a MulticastStmt. The implementation details are very
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

public class MulticastDialog extends AbstractDialog {
    
    private static final int MODE_INIT = -1;
    private static final int MODE_DEFAULT = 0;
    
    private int mode;

    private DialogPane dialogPane;

    private DialogMenu sourceGroup;
    private DialogMenu targetGroup;
    private JCheckBox async;
    private JCheckBox uniqueBuffer;
    private DialogMenu count;
    private DialogMenu messageSize;
    private DialogMenu messageSizeUnits;
    private DialogMenu alignment;
    private DialogMenu alignmentMode;
    private DialogMenu alignmentUnits;
    private DialogMenu verificationOrTouching;
    private DialogMenu buffer;
    
    private String selectSourceGroup;
    private String selectTargetGroup;
    private boolean selectAsync;
    private boolean selectUniqueBuffer;
    private String selectCount;
    private String selectMessageSize;
    private String selectMessageSizeUnits;
    private String selectAlignment;
    private String selectAlignmentMode;
    private String selectVerificationOrTouching;
    private String selectAlignmentUnits;
    private String selectBuffer;

    private Vector selectVariablesInScope;

    private boolean isMixedAsync;
    private boolean isMixedUniqueBuffer;
    private boolean isFirstAsync;
    private boolean isFirstUniqueBuffer;
    
    public MulticastDialog( Program program, DialogPane dialogPane ){
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
                applyChanges( getSelectedMulticastStmts() );
                updateState();
                program.updateState();
                program.repaint();
            }
        }
        
        else if( command.equals( "Reset" ) )
            updateState();
        else if( source == async )
            isMixedAsync = false;
        else if( source == uniqueBuffer )
            isMixedUniqueBuffer = false;
        
    }
    
    public void defaultMode(){
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

        pane1.add( sourceGroup );

        JPanel pane1b = new JPanel();
        pane1b.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1b );

        pane1b.add( new JLabel( "target: " ) );
        
        targetGroup = new DialogMenu( 430 );
        targetGroup.addItem( selectTargetGroup );
        targetGroup.addTargetTaskDescriptions();
        targetGroup.setEditable( true );
        
        pane1b.add( targetGroup );
        
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
        count = new DialogMenu( 150 );
        count.addItem( selectCount );
        addScopeVariables( count );
        count.setEditable( true );
        pane2.add( count );

        JPanel pane2b = new JPanel();
        pane2b.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2b );

        async = new JCheckBox();
        async.setSelected( selectAsync );

        pane2b.add( async );
        pane2b.add( new JLabel( "asynchronous" ) );

        uniqueBuffer = new JCheckBox();
        uniqueBuffer.setSelected( selectUniqueBuffer );
        
        pane2b.add( uniqueBuffer );

        pane2b.add( new JLabel( "unique buffer" ) );

        verificationOrTouching = new DialogMenu();
        
        verificationOrTouching.addItem( selectVerificationOrTouching );
        verificationOrTouching.addItem( "without verification" );
        verificationOrTouching.addItem( "without data touching" );
        verificationOrTouching.addItem( "with verification" );
        verificationOrTouching.addItem( "with data touching" );
        
        pane2b.add( verificationOrTouching );
        
        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane3 );
        
        alignment = new DialogMenu();
        alignment.addItem( selectAlignment );
        addScopeVariables( alignment );
        alignment.setEditable( true );
        
        pane3.add( alignment );
        
        alignmentUnits = new DialogMenu();
        alignmentUnits.addItem( selectAlignmentUnits );
        alignmentUnits.addSizeUnits();
        pane3.add( alignmentUnits );
        
        alignmentMode = new DialogMenu();
        alignmentMode.addItem( selectAlignmentMode );
        alignmentMode.addItem( "unaligned" );
        alignmentMode.addItem( "aligned" );
        alignmentMode.addItem( "misaligned" );
        pane3.add( alignmentMode );     

        pane3.add( new JLabel( "buffer: " ) );
        
        buffer = new DialogMenu( 150 );
        buffer.addItem( selectBuffer );
        buffer.addItem( "default" );
        buffer.setEditable( true );
        pane3.add( buffer );

        JPanel pane7 = new JPanel();
        pane7.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane7 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        pane7.add( applyButton );
        pane7.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_DEFAULT;
    }

    public void updateState(){
        selectSourceGroup = null;
        selectTargetGroup = null;

        isMixedAsync = false;
        isMixedUniqueBuffer = false;
        
        isFirstAsync = true;
        isFirstUniqueBuffer = true;
        
        selectAsync = false;
        selectUniqueBuffer = false;

        selectCount = null;
        selectMessageSize = null;
        selectMessageSizeUnits = null;
        selectAlignment = null;
        selectAlignmentMode = null;
        selectVerificationOrTouching = null;
        selectAlignmentUnits = null;
        selectBuffer = null;
        
        selectVariablesInScope = new Vector();

        Vector selectedMulticastStmts = getSelectedMulticastStmts(); 

        for( int i = 0; i < selectedMulticastStmts.size(); i++ ){
            MulticastStmt stmt = 
                (MulticastStmt)selectedMulticastStmts.elementAt( i );
            
            readSourceGroup( stmt );
            readTargetGroup( stmt );
            readAsync( stmt );
            readUniqueBuffer( stmt );
            readCount( stmt );
            readMessageSize( stmt );
            readMessageSizeUnits( stmt );
            readAlignment( stmt );
            readAlignmentMode( stmt );
            readVerificationOrTouching( stmt );
            readAlignmentUnits( stmt );
            readBuffer( stmt );
            
            readVariablesInScope( stmt );
        }
        
        if( selectedMulticastStmts.size() > 0 )
            defaultMode();
    }

    public void windowClosing( WindowEvent event ) {
        deselectMulticastStmts();
        updateState();
        program.repaint();
    }

    private void readSourceGroup( MulticastStmt stmt ){
        if( selectSourceGroup == null )
            selectSourceGroup = stmt.getTaskGroup().toCodeSource();
        else if( !selectSourceGroup.equals( stmt.getTaskGroup().toCodeSource() ) )
            selectSourceGroup = "-";
    }

    private void readTargetGroup( MulticastStmt stmt ){
        if( selectTargetGroup == null )
            selectTargetGroup = stmt.getTaskGroup().toCodeTarget();
        else if( !selectTargetGroup.equals( stmt.getTaskGroup().toCodeTarget() ) )
            selectTargetGroup = "-";
    }

    private void readAsync( MulticastStmt stmt ){
        if( isFirstAsync )
            selectAsync = stmt.getAsync();
        else if( selectAsync != stmt.getAsync() )
            isMixedAsync = true;
        isFirstAsync = false;
    }

    private void readUniqueBuffer( MulticastStmt stmt ){
        if( isFirstUniqueBuffer )
            selectUniqueBuffer = stmt.getUniqueBuffer();
        else if( selectUniqueBuffer != stmt.getUniqueBuffer() )
            isMixedUniqueBuffer = true;
        isFirstUniqueBuffer = false;
    }

    private void readCount( MulticastStmt stmt ){
        if( selectCount == null )
            selectCount = stmt.getCount();
        else if( !selectCount.equals( stmt.getCount() ) )
            selectCount = "-";
    }

    private void readMessageSize( MulticastStmt stmt ){
        if( selectMessageSize == null )
            selectMessageSize = stmt.getMessageSize();
        else if( !selectMessageSize.equals( stmt.getMessageSize() ) )
            selectMessageSize = "-";
    }

    private void readMessageSizeUnits( MulticastStmt stmt ){
        if( selectMessageSizeUnits == null )
            selectMessageSizeUnits = stmt.getMessageSizeUnits();
        else if( !selectMessageSizeUnits.equals( stmt.getMessageSizeUnits() ) )
            selectMessageSizeUnits = "-";
    }
    
    private void readAlignment( MulticastStmt stmt ){
        if( selectAlignment == null )
            selectAlignment = stmt.getAlignment();
        else if( !selectAlignment.equals( stmt.getAlignment() ) )
            selectAlignment = "-";
    }
    
    private void readAlignmentMode( MulticastStmt stmt ){
        if( selectAlignmentMode == null )
            selectAlignmentMode = stmt.getAlignmentMode();
        else if( !selectAlignmentMode.equals( stmt.getAlignmentMode() ) )
            selectAlignmentMode = "-";
    }
    
    private void readVerificationOrTouching( MulticastStmt stmt ){
        if( selectVerificationOrTouching == null )
            selectVerificationOrTouching = stmt.getVerificationOrTouching();
        else if( !selectVerificationOrTouching.equals( stmt.getVerificationOrTouching() ) )
            selectVerificationOrTouching = "-";
    }

    private void readAlignmentUnits( MulticastStmt stmt ){
        if( selectAlignmentUnits == null )
            selectAlignmentUnits = stmt.getAlignmentUnits();
        else if( !selectAlignmentUnits.equals( stmt.getAlignmentUnits() ) )
            selectAlignmentUnits = "-";
    }
    
    private void readBuffer( MulticastStmt stmt ){
        if( selectBuffer == null )
            selectBuffer = stmt.getBuffer();
        else if( !selectBuffer.equals( stmt.getBuffer() ) )
            selectBuffer = "-";
    }

    public void deselectMulticastStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof MulticastStmt ){
                component.setSelected( false );
            }
        }
    }

    public Vector getSelectedMulticastStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedMulticastStmts = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof MulticastStmt )
                selectedMulticastStmts.add( component );
        }
        return selectedMulticastStmts;
    }

    private void writeSourceGroup( MulticastStmt stmt ){
        if( !selectSourceGroup.equals( "-" ) )
            stmt.setSourceGroup( selectSourceGroup );
    }

    private void writeTargetGroup( MulticastStmt stmt ){
        if( !selectTargetGroup.equals( "-" ) )
            stmt.setTargetGroup( selectTargetGroup );
    }

    private void writeAsync( MulticastStmt stmt ){
        if( !isMixedAsync )
            stmt.setAsync( selectAsync );
    }
    
    private void writeUniqueBuffer( MulticastStmt stmt ){
        if( !isMixedUniqueBuffer )
            stmt.setUniqueBuffer( selectUniqueBuffer );
    }

    private void writeCount( MulticastStmt stmt ){
        if( !selectCount.equals( "-" ) )
            stmt.setCount( selectCount );
    }

    private void writeMessageSize( MulticastStmt stmt ){
        if( !selectMessageSize.equals( "-" ) )
            stmt.setMessageSize( selectMessageSize );
    }

    private void writeMessageSizeUnits( MulticastStmt stmt ){
        if( !selectMessageSizeUnits.equals( "-" ) )
            stmt.setMessageSizeUnits( selectMessageSizeUnits );
    }

    private void writeAlignment( MulticastStmt stmt ){
        if( !selectAlignment.equals( "-" ) )
            stmt.setAlignment( selectAlignment );
    }

    private void writeAlignmentMode( MulticastStmt stmt ){
        if( !selectAlignmentMode.equals( "-" ) )
            stmt.setAlignmentMode( selectAlignmentMode );
    }

    private void writeVerificationOrTouching( MulticastStmt stmt ){
        if( !selectVerificationOrTouching.equals( "-" ) )
            stmt.setVerificationOrTouching( selectVerificationOrTouching );
    }

    private void writeAlignmentUnits( MulticastStmt stmt ){
        if( !selectAlignmentUnits.equals( "-" ) )
            stmt.setAlignmentUnits( selectAlignmentUnits );
    }

    private void writeBuffer( MulticastStmt stmt ){
        if( !selectBuffer.equals( "-" ) )
            stmt.setBuffer( selectBuffer );
    }

    private void applyChanges( Vector communicationStmts ){
        for( int i = 0; i < communicationStmts.size(); i++ ){
            MulticastStmt stmt = 
                (MulticastStmt)communicationStmts.elementAt( i );
            writeSourceGroup( stmt );
            writeTargetGroup( stmt );
            writeAsync( stmt );
            writeUniqueBuffer( stmt );
            writeCount( stmt );
            writeMessageSize( stmt );
            writeMessageSizeUnits( stmt );
            writeAlignment( stmt );
            writeAlignmentMode( stmt );
            writeVerificationOrTouching( stmt );
            writeAlignmentUnits( stmt );
            writeBuffer( stmt );
        }
    }

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
        if( program.verifyField( selectSourceGroup, "target_task",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectSourceGroup +  
                                     "\" is not a valid target task description" );
            return false;
        }
    }

    private boolean verifyAsync(){
        if( !isMixedAsync )
            selectAsync = async.isSelected();
        return true;
    }
    
    private boolean verifyUniqueBuffer(){
        if( !isMixedUniqueBuffer )
            selectUniqueBuffer = uniqueBuffer.isSelected();
        return true;
    }
    
    private boolean verifyCount(){
        selectCount = (String)count.getSelectedItem();
        if( program.verifyField( selectCount, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectCount +  
                                     "\" is not a valid expression for count" );
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
    
    private boolean verifyAlignment(){
        selectAlignment = (String)alignment.getSelectedItem();
        if( program.verifyField( selectAlignment, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectAlignment +  
                                     "\" is not a valid expression for alignment" );
            return false;
        }
    }
    
    private boolean verifyAlignmentMode(){
        selectAlignmentMode = (String)alignmentMode.getSelectedItem();
        return true;
    }
    
    private boolean verifyVerificationOrTouching(){
        selectVerificationOrTouching = (String)verificationOrTouching.getSelectedItem();
        return true;
    }
    
    private boolean verifyAlignmentUnits(){
        selectAlignmentUnits = (String)alignmentUnits.getSelectedItem();
        return true;
    }
        
    private boolean verifyBuffer(){
        selectBuffer = (String)buffer.getSelectedItem();
        if( selectBuffer.equals( "default" ) || 
            program.verifyField( selectBuffer, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectBuffer +  
                                     "\" is not a valid expression for buffer" );
            return false;
        }
    }
    
    private boolean verifyFields(){
        if( verifySourceGroup() &&
            verifyTargetGroup() &&
            verifyAsync() &&
            verifyUniqueBuffer() &&
            verifyCount() &&
            verifyMessageSize() &&
            verifyMessageSizeUnits() &&
            verifyAlignment() &&
            verifyAlignmentMode() &&
            verifyVerificationOrTouching() &&
            verifyAlignmentUnits() &&
            verifyBuffer() )
            return true;
        return false;
    }

    private void readVariablesInScope( MulticastStmt stmt ){
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
