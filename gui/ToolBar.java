/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: tool bar
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class maintains the tool bar of actions displayed in the main
 * pane.
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
import javax.swing.border.*;
import javax.swing.event.*;

public class ToolBar extends JPanel 
    implements ActionListener {
    
    public JToolBar toolBar;

    private Program program;

    private static final int SEPARATOR_WIDTH = 8;
    
    // toolbar buttons
    private JButton addRowButton, deleteButton, 
        loopButton, measureButton, computeButton, 
        synchronizeButton, reduceButton, multicastButton, waitButton,
        communicateButton, normalizeButton, extendButton;
    
    public ToolBar( Program program ){  
        this.program = program;
        
        toolBar = new JToolBar( "ToolBar" );

        // separate the toolbar buttons into 2 rows 
        FlowLayout flowLayout = new FlowLayout();
        flowLayout.setHgap( 0 );
        toolBar.setLayout( flowLayout );
        toolBar.setPreferredSize( new Dimension( 400, 65 ) );

        toolBar.setFloatable( true );
        toolBar.setMargin( new Insets( 0, 0, 0, 0 ) );

        addRowButton = new JButton( "Add Row" );
        addRowButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        addRowButton.setToolTipText( "Add a task row at the cursor or insert one at the selected task row" );
        addRowButton.setMnemonic( KeyEvent.VK_A );
        toolBar.add( addRowButton );
        addRowButton.addActionListener( this );
        
        deleteButton = new JButton( "Delete" );
        deleteButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        deleteButton.setToolTipText( "Delete selected components" );
        deleteButton.setMnemonic( KeyEvent.VK_D );
        toolBar.add( deleteButton );
        deleteButton.addActionListener( this );

        toolBar.addSeparator( new Dimension( SEPARATOR_WIDTH, 5 ) );

        loopButton = new JButton( "Loop" );
        loopButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        loopButton.setToolTipText( "Add a loop around selected components" );
        loopButton.setMnemonic( KeyEvent.VK_L );
        toolBar.add( loopButton );
        loopButton.addActionListener( this );
        
        measureButton = new JButton( "Measure" );
        measureButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        measureButton.setToolTipText( "Add a measurement block around selected components" );
        measureButton.setMnemonic( KeyEvent.VK_M );
        toolBar.add( measureButton );
        measureButton.addActionListener( this );

        computeButton = new JButton( "Compute" );
        computeButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        computeButton.setToolTipText( "Compute on selected tasks" );
        computeButton.setMnemonic( KeyEvent.VK_P );
        toolBar.add( computeButton );
        computeButton.addActionListener( this );
        
        toolBar.addSeparator( new Dimension( SEPARATOR_WIDTH, 5 ) );
        
        communicateButton = new JButton( "Communicate" );
        communicateButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        communicateButton.setToolTipText( "Add point to point communication between selected tasks" );
        communicateButton.setMnemonic( KeyEvent.VK_C );
        toolBar.add( communicateButton );
        communicateButton.addActionListener( this );

        waitButton = new JButton( "Wait" );
        waitButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        waitButton.setToolTipText( "Await completion on selected tasks or at cursor" );
        waitButton.setMnemonic( KeyEvent.VK_W );
        toolBar.add( waitButton );
        waitButton.addActionListener( this );

        extendButton = new JButton( "Extend" );
        extendButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        extendButton.setToolTipText( "Extend a communication or computation pattern across an entire row" );
        extendButton.setMnemonic( KeyEvent.VK_X );
        toolBar.add( extendButton );
        extendButton.addActionListener( this );

        toolBar.addSeparator( new Dimension( SEPARATOR_WIDTH, 5 ) );
        
        synchronizeButton = new JButton( "Synchronize" );
        synchronizeButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        synchronizeButton.setToolTipText( "Synchronize on selected tasks or at cursor" );
        synchronizeButton.setMnemonic( KeyEvent.VK_S );
        toolBar.add( synchronizeButton );
        synchronizeButton.addActionListener( this );
        
        reduceButton = new JButton( "Reduce" );
        reduceButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        reduceButton.setToolTipText( "Reduce on selected tasks or at cursor" );
        reduceButton.setMnemonic( KeyEvent.VK_R );
        toolBar.add( reduceButton );
        reduceButton.addActionListener( this );

        multicastButton = new JButton( "Multicast" );
        multicastButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        multicastButton.setToolTipText( "Multicast on selected tasks at the cursor" );
        multicastButton.setMnemonic( KeyEvent.VK_T );
        toolBar.add( multicastButton );
        multicastButton.addActionListener( this );

        toolBar.addSeparator( new Dimension( SEPARATOR_WIDTH, 5 ) );

        normalizeButton = new JButton( "Normalize" );
        normalizeButton.setFont( new Font( "sansserif", Font.BOLD, 10 ) );
        normalizeButton.setToolTipText( "Put the program into standard form as it will appear when saved and re-opened" );
        normalizeButton.setMnemonic( KeyEvent.VK_N );
        toolBar.add( normalizeButton );
        normalizeButton.addActionListener( this );
        
    }

    // methods to enable the various buttons

    public void enableAddRow( boolean flag ){
        addRowButton.setEnabled( flag );
    }

    public void enableDelete( boolean flag ){
        deleteButton.setEnabled( flag );
    }
    
    public void enableLoop( boolean flag ){
        loopButton.setEnabled( flag );
    }

    public void enableMeasure( boolean flag ){
        measureButton.setEnabled( flag );
    }

    public void enableCompute( boolean flag ){
        computeButton.setEnabled( flag );
    }

    public void enableSynchronize( boolean flag ){
        synchronizeButton.setEnabled( flag );
    }

    public void enableReduce( boolean flag ){
        reduceButton.setEnabled( flag );
    }

    public void enableMulticast( boolean flag ){
        multicastButton.setEnabled( flag );
    }

    public void enableWait( boolean flag ){
        waitButton.setEnabled( flag );
    }

    public void enableExtend( boolean flag ){
        extendButton.setEnabled( flag );
    }

    public void enableCommunicate( boolean flag ){
        communicateButton.setEnabled( flag );
    }

    public void enableNormalize( boolean flag ){
        normalizeButton.setEnabled( flag );
    }
    
    public boolean isEnabledAddRow(){
        return addRowButton.isEnabled();
    }

    // methods to check if the various buttons are enabled

    public boolean isEnabledDelete(){
        return deleteButton.isEnabled();
    }
    
    public boolean isEnabledLoop(){
        return loopButton.isEnabled();
    }

    public boolean isEnabledMeasure(){
        return measureButton.isEnabled();
    }

    public boolean isEnabledCompute(){
        return computeButton.isEnabled();
    }

    public boolean isEnabledSynchronize(){
        return synchronizeButton.isEnabled();
    }

    public boolean isEnabledReduce(){
        return reduceButton.isEnabled();
    }

    public boolean isEnabledMulticast(){
        return multicastButton.isEnabled();
    }

    public boolean isEnabledWait(){
        return waitButton.isEnabled();
    }

    public boolean isEnabledExtend(){
        return extendButton.isEnabled();
    }

    public boolean isEnabledCommunicate(){
        return communicateButton.isEnabled();
    }

    public boolean isEnabledNormalize(){
        return normalizeButton.isEnabled();
    }

    // handle each of the buttons being pressed

    public void actionPerformed( ActionEvent event ) {
        String command = event.getActionCommand();
        
        if( command.equals( "Add Row" ) )
            program.addTaskRow();
        else if( command.equals( "Delete" ) )
            program.deleteSelectedComponents();
        else if( command.equals( "Loop" ) )
            program.addLoop();
        else if( command.equals( "Measure" ) )
            program.addMeasure();
        else if( command.equals( "Compute" ) )
            program.addCompute();
        else if( command.equals( "Synchronize" ) )
            program.addSynchronize();
        else if( command.equals( "Reduce" ) )
            program.addReduce();
        else if( command.equals( "Multicast" ) )
            program.addMulticast();
        else if( command.equals( "Communicate" ) )
            program.addCommunicate();
        else if( command.equals( "Wait" ) )
            program.addWait();
        else if( command.equals( "Normalize" ) )
            program.normalize();
        else if( command.equals( "Extend" ) )
            program.showExtendDialog();
    }
    
}

