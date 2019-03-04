/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: compute dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining the compute dialog for
 * manipulating a ComputeStmt. The implementation details are very similar to
 * CommunicationDialog, see the comments in CommunicationDialog.java
 * for more information.
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2003, Triad National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2003).  Triad National Security, LLC.  This software
 * was produced under U.S. Government contract 89233218CNA000001 for
 * Los Alamos National Laboratory (LANL), which is operated by Los
 * Alamos National Security, LLC (Triad) for the U.S. Department
 * of Energy. The U.S. Government has rights to use, reproduce,
 * and distribute this software.  NEITHER THE GOVERNMENT NOR TRIAD
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
 *   * Neither the name of Triad National Security, LLC, Los Alamos
 *     National Laboratory, the U.S. Government, nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY TRIAD AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TRIAD OR CONTRIBUTORS BE
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

public class ComputeDialog extends AbstractDialog {

    private static final int MODE_INIT = -2;
    private static final int MODE_MIXED = -1;
    private static final int MODE_COMPUTES_FOR = 0;
    private static final int MODE_SLEEPS_FOR = 1;
    private static final int MODE_TOUCHES_MEMORY = 2;
    
    private int mode;

    private DialogPane dialogPane;
    
    private DialogMenu computeType;
    private DialogMenu taskGroup;
    private DialogMenu computeTime;
    private DialogMenu computeTimeUnits;
    private DialogMenu sleepTime;
    private DialogMenu sleepTimeUnits;
    private DialogMenu touchCount;
    private DialogMenu touchCountUnits;
    private DialogMenu touchRegion;
    private DialogMenu touchRegionUnits;
    private DialogMenu touchTimes;
    private DialogMenu touchStride;
    private DialogMenu touchStrideUnits;
    
    private int selectComputeType;
    private String selectTaskGroup;
    private String selectComputeTime;
    private String selectComputeTimeUnits;
    private String selectSleepTime;
    private String selectSleepTimeUnits;
    private String selectTouchCount;
    private String selectTouchCountUnits;
    private String selectTouchRegion;
    private String selectTouchRegionUnits;
    private String selectTouchTimes;
    private String selectTouchStride;
    private String selectTouchStrideUnits;

    private Vector selectVariablesInScope;
    
    public ComputeDialog( Program program, DialogPane dialogPane ){
        super( program );
        this.dialogPane = dialogPane;
    }

    public void actionPerformed( ActionEvent event ){
        if( mode == MODE_INIT )
            return;
        
        String command = event.getActionCommand();
        Object source = event.getSource();

        if( command.equals( "comboBoxChanged" ) && 
            source == computeType ){
            String type = (String)computeType.getSelectedItem();
            if( type.equals( "computes for" ) )
                computeMode();
            else if( type.equals( "sleeps for" ) )
                sleepMode();
            else if( type.equals( "touches memory" ) )
                touchMemoryMode();
            else
                assert false;
        }
        else if( command.equals( "Apply" ) ){
            if( verifyFields() ){
                program.pushState();
                applyChanges( getSelectedComputeStmts() );
                //deselectAllComputeStmts();
                program.updateState();
                updateState();
                program.repaint();
            }
        }
        else if( command.equals( "Reset" ) ){
            //deselectAllComputeStmts();
            updateState();
            //program.updateState();
            //program.repaint();
        }
    }

    // set up the dialog for the compute mode
    public void computeMode(){
        mode = MODE_INIT;

        dialogPane.clear();
        
        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "type: " ) );
        computeType = new DialogMenu();
        computeType.addItem( "computes for" );
        computeType.addItem( "sleeps for" );
        computeType.addItem( "touches memory" );
        computeType.addActionListener( this );
        computeType.setSelectedIndex( MODE_COMPUTES_FOR );
        pane1.add( computeType );
        
        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        taskGroup = new DialogMenu( 430 );
        taskGroup.addItem( selectTaskGroup );
        taskGroup.addSourceTaskDescriptions();
        taskGroup.addActionListener( this );
        taskGroup.setEditable( true );
        pane2.add( taskGroup );

        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane3 );

        pane3.add( new JLabel( "computes for: " ) );
        computeTime = new DialogMenu( 150 );
        computeTime.addItem( selectComputeTime );
        addScopeVariables( computeTime );
        computeTime.setEditable( true );
        pane3.add( computeTime );

        computeTimeUnits = new DialogMenu();
        computeTimeUnits.addItem( selectComputeTimeUnits );
        computeTimeUnits.addItem( "microseconds" );
        computeTimeUnits.addItem( "milliseconds" );
        computeTimeUnits.addItem( "seconds" );
        computeTimeUnits.addItem( "minutes" );
        computeTimeUnits.addItem( "hours" );
        computeTimeUnits.addItem( "days" );
        pane3.add( computeTimeUnits );
        
        JPanel pane4 = new JPanel();
        pane4.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane4 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        pane4.add( applyButton );
        pane4.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_COMPUTES_FOR;
    }

    // set up the dialog for the sleep mode
    public void sleepMode(){
        mode = MODE_INIT;
        dialogPane.clear();
        
        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "type: " ) );
        computeType = new DialogMenu();
        computeType.addItem( "computes for" );
        computeType.addItem( "sleeps for" );
        computeType.addItem( "touches memory" );
        computeType.addActionListener( this );
        computeType.setSelectedIndex( MODE_SLEEPS_FOR );
        pane1.add( computeType );

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        taskGroup = new DialogMenu( 430 );
        taskGroup.addItem( selectTaskGroup );
        taskGroup.addSourceTaskDescriptions();
        taskGroup.setEditable( true );
        pane2.add( taskGroup );

        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane3 );

        pane3.add( new JLabel( "sleeps for: " ) );
        sleepTime = new DialogMenu( 150 );
        sleepTime.addItem( selectSleepTime );
        addScopeVariables( sleepTime );
        sleepTime.setEditable( true );
        pane3.add( sleepTime );

        sleepTimeUnits = new DialogMenu();
        sleepTimeUnits.addItem( selectSleepTimeUnits );
        sleepTimeUnits.addItem( "microseconds" );
        sleepTimeUnits.addItem( "milliseconds" );
        sleepTimeUnits.addItem( "seconds" );
        sleepTimeUnits.addItem( "minutes" );
        sleepTimeUnits.addItem( "hours" );
        sleepTimeUnits.addItem( "days" );
        pane3.add( sleepTimeUnits );

        JPanel pane4 = new JPanel();
        pane4.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane4 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        pane4.add( applyButton );
        pane4.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_SLEEPS_FOR;
    }

    // set up the dialog for the touch mode

    public void touchMemoryMode(){
        mode = MODE_INIT;
        dialogPane.clear();
        
        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "type: " ) );
        computeType = new DialogMenu();
        computeType.addItem( "computes for" );
        computeType.addItem( "sleeps for" );
        computeType.addItem( "touches memory" );
        computeType.addActionListener( this );
        computeType.setSelectedIndex( MODE_TOUCHES_MEMORY );
        pane1.add( computeType );

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        taskGroup = new DialogMenu( 430 );
        taskGroup.addItem( selectTaskGroup );
        taskGroup.addSourceTaskDescriptions();
        taskGroup.setEditable( true );
        pane2.add( taskGroup );
        
        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane3 );

        pane3.add( new JLabel( "touches " ) );
        touchCount = new DialogMenu( 150 );
        touchCount.addItem( selectTouchCount );
        addScopeVariables( touchCount );
        touchCount.setEditable( true );
        pane3.add( touchCount );

        touchCountUnits = new DialogMenu();
        touchCountUnits.addItem( selectTouchCountUnits );
        touchCountUnits.addSizeUnits();
        pane3.add( touchCountUnits );

        JPanel pane4 = new JPanel();
        pane4.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane4 );

        pane4.add( new JLabel( "of a " ) );
        touchRegion = new DialogMenu( 150 );
        touchRegion.addItem( selectTouchRegion );
        addScopeVariables( touchRegion );
        touchRegion.setEditable( true );
        pane4.add( touchRegion );

        touchRegionUnits = new DialogMenu();
        touchRegionUnits.addItem( selectTouchRegionUnits );
        touchRegionUnits.addSizeUnits();
        pane4.add( touchRegionUnits );
        pane4.add( new JLabel( "memory region" ) );
        
        JPanel pane5 = new JPanel();
        pane5.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane5 );

        touchTimes = new DialogMenu( 150 );
        touchTimes.addItem( selectTouchTimes );
        addScopeVariables( touchTimes );
        touchTimes.setEditable( true );
        pane5.add( touchTimes );
        pane5.add( new JLabel( " times" ) ); 

        JPanel pane6 = new JPanel();
        pane6.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane6 );
        
        pane6.add( new JLabel( "with stride " ) );
        touchStride = new DialogMenu( 150 );
        touchStride.addItem( selectTouchStride );
        touchStride.addItem( "default" );
        addScopeVariables( touchStride );
        touchStride.setEditable( true );
        pane6.add( touchStride );

        touchStrideUnits = new DialogMenu();
        touchStrideUnits.addItem( selectTouchStrideUnits );
        touchStrideUnits.addSizeUnits();
        pane6.add( touchStrideUnits );

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
        mode = MODE_TOUCHES_MEMORY;
    }

    public void updateState(){
        selectTaskGroup = null;
        selectComputeTime = null;
        selectComputeTimeUnits = null;
        selectSleepTime = null;
        selectSleepTimeUnits = null;
        selectTouchCount = null;
        selectTouchCountUnits = null;
        selectTouchRegion = null;
        selectTouchRegionUnits = null;
        selectTouchTimes = null;
        selectTouchStride = null;
        selectTouchStrideUnits = null;
        selectComputeType = MODE_INIT;
        
        selectVariablesInScope = new Vector();
        
        Vector selectedComputeStmts = getSelectedComputeStmts(); 
        
        for( int i = 0; i < selectedComputeStmts.size(); i++ ){
            ComputeStmt stmt = 
                (ComputeStmt)selectedComputeStmts.elementAt( i );
            
            readComputeType( stmt );
            readTaskGroup( stmt );
            readComputeTime( stmt );
            readComputeTimeUnits( stmt );
            readSleepTime( stmt );
            readSleepTimeUnits( stmt );
            readTouchCount( stmt );
            readTouchCountUnits( stmt );
            readTouchRegion( stmt );
            readTouchRegionUnits( stmt );
            readTouchTimes( stmt );
            readTouchStride( stmt );
            readTouchStrideUnits( stmt );

            readVariablesInScope( stmt );
        }
        
        if( selectedComputeStmts.size() > 0 ){
            switch( selectComputeType ){
            case MODE_COMPUTES_FOR:
                computeMode();
                break;
            case MODE_SLEEPS_FOR:
                sleepMode();
                break;
            case MODE_TOUCHES_MEMORY:
                touchMemoryMode();
                break;
            }
        }
    }

    public void deselectAllComputeStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof ComputeStmt )
                component.setSelected( false );
        }
    }

    public Vector getSelectedComputeStmts(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedComputeStmts = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof ComputeStmt )
                selectedComputeStmts.add( component );
        }
        return selectedComputeStmts;
    }
    

    private void readComputeType( ComputeStmt stmt ){
        if( selectComputeType == MODE_INIT ){
            if( stmt.getType() == ComputeStmt.TYPE_COMPUTES_FOR )
                selectComputeType = MODE_COMPUTES_FOR;
            else if( stmt.getType() == ComputeStmt.TYPE_SLEEPS_FOR )
                selectComputeType = MODE_SLEEPS_FOR;
            else if( stmt.getType() == ComputeStmt.TYPE_TOUCHES_MEMORY )
                selectComputeType = MODE_TOUCHES_MEMORY;
            else
                assert false;
        }
        // needs to be fixed
        else if( stmt.getType() != selectComputeType ) 
            selectComputeType = MODE_MIXED;
    }

    private void readTaskGroup( ComputeStmt stmt ){
        if( selectTaskGroup == null )
            selectTaskGroup = stmt.getTaskGroup().toCodeSource();
        else if( !selectTaskGroup.equals( stmt.getTaskGroup().toCodeSource() ) )
            selectTaskGroup = "-";
    }

    private void readComputeTime( ComputeStmt stmt ){
        if( selectComputeTime == null )
            selectComputeTime = stmt.getComputeTime();
        else if( !selectComputeTime.equals( stmt.getComputeTime() ) )
            selectComputeTime = "-";
    }

    private void readComputeTimeUnits( ComputeStmt stmt ){
        if( selectComputeTimeUnits == null )
            selectComputeTimeUnits = stmt.getComputeTimeUnits();
        else if( !selectComputeTimeUnits.equals( stmt.getComputeTimeUnits() ) )
            selectComputeTimeUnits = "-";
    }

    private void readSleepTime( ComputeStmt stmt ){
        if( selectSleepTime == null )
            selectSleepTime = stmt.getSleepTime();
        else if( !selectSleepTime.equals( stmt.getSleepTime() ) )
            selectSleepTime = "-";
    }

    private void readSleepTimeUnits( ComputeStmt stmt ){
        if( selectSleepTimeUnits == null )
            selectSleepTimeUnits = stmt.getSleepTimeUnits();
        else if( !selectSleepTimeUnits.equals( stmt.getSleepTimeUnits() ) )
            selectSleepTimeUnits = "-";
    }

    private void readTouchCount( ComputeStmt stmt ){
        if( selectTouchCount == null )
            selectTouchCount = stmt.getTouchCount();
        else if( !selectTouchCount.equals( stmt.getTouchCount() ) )
            selectTouchCount = "-";
    }

    private void readTouchCountUnits( ComputeStmt stmt ){
        if( selectTouchCountUnits == null )
            selectTouchCountUnits = stmt.getTouchCountUnits();
        else if( !selectTouchCountUnits.equals( stmt.getTouchCountUnits() ) )
            selectTouchCountUnits = "-";
    }

    private void readTouchRegion( ComputeStmt stmt ){
        if( selectTouchRegion == null )
            selectTouchRegion = stmt.getTouchRegion();
        else if( !selectTouchRegion.equals( stmt.getTouchRegion() ) )
            selectTouchRegion = "-";
    }

    private void readTouchRegionUnits( ComputeStmt stmt ){
        if( selectTouchRegionUnits == null )
            selectTouchRegionUnits = stmt.getTouchRegionUnits();
        else if( !selectTouchRegionUnits.equals( stmt.getTouchRegionUnits() ) )
            selectTouchRegionUnits = "-";
    }

    private void readTouchTimes( ComputeStmt stmt ){
        if( selectTouchTimes == null )
            selectTouchTimes = stmt.getTouchTimes();
        else if( !selectTouchTimes.equals( stmt.getTouchTimes() ) )
            selectTouchTimes = "-";
    }

    private void readTouchStride( ComputeStmt stmt ){
        if( selectTouchStride == null )
            selectTouchStride = stmt.getTouchStride();
        else if( !selectTouchStride.equals( stmt.getTouchStride() ) )
            selectTouchStride = "-";
    }

    private void readTouchStrideUnits( ComputeStmt stmt ){
        if( selectTouchStrideUnits == null )
            selectTouchStrideUnits = stmt.getTouchStrideUnits();
        else if( !selectTouchStrideUnits.equals( stmt.getTouchStrideUnits() ) )
            selectTouchStrideUnits = "-";
    }

    private void writeComputeType( ComputeStmt stmt ){
        selectComputeType = computeType.getSelectedIndex();
        if( selectComputeType == MODE_COMPUTES_FOR )
            stmt.setType( ComputeStmt.TYPE_COMPUTES_FOR );
        else if( selectComputeType == MODE_SLEEPS_FOR )
            stmt.setType( ComputeStmt.TYPE_SLEEPS_FOR );
        else if( selectComputeType == MODE_TOUCHES_MEMORY )
            stmt.setType( ComputeStmt.TYPE_TOUCHES_MEMORY );
    }
    
    private void writeTaskGroup( ComputeStmt stmt ){
        if( !selectTaskGroup.equals( "-" ) )
            stmt.setTaskGroup( selectTaskGroup );
    }

    private void writeComputeTime( ComputeStmt stmt ){
        if( !selectComputeTime.equals( "-" ) )
            stmt.setComputeTime( selectComputeTime );
    }

    private void writeComputeTimeUnits( ComputeStmt stmt ){
        if( !selectComputeTimeUnits.equals( "-" ) )
            stmt.setComputeTimeUnits( selectComputeTimeUnits );
    }

    private void writeSleepTime( ComputeStmt stmt ){
        if( !selectSleepTime.equals( "-" ) )
            stmt.setSleepTime( selectSleepTime );
    }
    
    private void writeSleepTimeUnits( ComputeStmt stmt ){
        if( !selectSleepTimeUnits.equals( "-" ) )
            stmt.setSleepTimeUnits( selectSleepTimeUnits );
    }

    private void writeTouchCount( ComputeStmt stmt ){
        if( !selectTouchCount.equals( "-" ) )
            stmt.setTouchCount( selectTouchCount );
    }

    private void writeTouchCountUnits( ComputeStmt stmt ){
        if( !selectTouchCountUnits.equals( "-" ) )
            stmt.setTouchCountUnits( selectTouchCountUnits );
    }

    private void writeTouchRegion( ComputeStmt stmt ){
        if( !selectTouchRegion.equals( "-" ) )
            stmt.setTouchRegion( selectTouchRegion );
    }
    
    private void writeTouchRegionUnits( ComputeStmt stmt ){
        if( !selectTouchRegionUnits.equals( "-" ) )
            stmt.setTouchRegionUnits( selectTouchRegionUnits );
    }
    
    private void writeTouchTimes( ComputeStmt stmt ){
        if( !selectTouchTimes.equals( "-" ) )
            stmt.setTouchTimes( selectTouchTimes );
    }
    
    private void writeTouchStride( ComputeStmt stmt ){
        if( !selectTouchStride.equals( "-" ) )
            stmt.setTouchStride( selectTouchStride );
    }

    private void writeTouchStrideUnits( ComputeStmt stmt ){
        if( !selectTouchStrideUnits.equals( "-" ) )
            stmt.setTouchStrideUnits( selectTouchStrideUnits );
    }
    
    private boolean verifyComputeType(){
        selectComputeType = computeType.getSelectedIndex();
        return true;
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

    private boolean verifyComputeTime(){
        selectComputeTime = (String)computeTime.getSelectedItem();
        if( program.verifyField( selectComputeTime, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectComputeTime +  
                                     "\" is not a valid expression for time" );
            return false;
        }
    }

    private boolean verifyComputeTimeUnits(){
        selectComputeTimeUnits = (String)computeTimeUnits.getSelectedItem();
        return true;
    }

    private boolean verifySleepTime(){
        selectSleepTime = (String)sleepTime.getSelectedItem();
        if( program.verifyField( selectSleepTime, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectSleepTime +  
                                     "\" is not a valid expression for time" );
            return false;
        }
    }

    private boolean verifySleepTimeUnits(){
        selectSleepTimeUnits = (String)sleepTimeUnits.getSelectedItem();
        return true;
    }
    
    private boolean verifyTouchCount(){
        selectTouchCount = (String)touchCount.getSelectedItem();
        if( program.verifyField( selectTouchCount, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTouchCount +  
                                     "\" is not a valid expression for touch count" );
            return false;
        }
    }
    
    private boolean verifyTouchCountUnits(){
        selectTouchCountUnits = (String)touchCountUnits.getSelectedItem();
        return true;
    }
    
    private boolean verifyTouchRegion(){
        selectTouchRegion = (String)touchRegion.getSelectedItem();
        if( program.verifyField( selectTouchRegion, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTouchRegion +  
                                     "\" is not a valid expression region size" );
            return false;
        }
    }

    private boolean verifyTouchRegionUnits(){
        selectTouchRegionUnits = (String)touchRegionUnits.getSelectedItem();
        return true;
    }

    private boolean verifyTouchTimes(){
        selectTouchTimes = (String)touchTimes.getSelectedItem();
        if( program.verifyField( selectTouchTimes, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTouchTimes +  
                                     "\" is not a valid expression for touch times" );
            return false;
        }
    }

    private boolean verifyTouchStride(){
        selectTouchStride = (String)touchStride.getSelectedItem();
        if( selectTouchStride.equals( "default" ) )
            return true;

        if( program.verifyField( selectTouchStride, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTouchStride +  
                                     "\" is not a valid expression for touch stride" );
            return false;
        }
    }

    private boolean verifyTouchStrideUnits(){
        selectTouchStrideUnits = (String)touchStrideUnits.getSelectedItem();
        return true;
    }

    private void applyChanges( Vector computeStmts ){
        for( int i = 0; i < computeStmts.size(); i++ ){
            ComputeStmt stmt = 
                (ComputeStmt)computeStmts.elementAt( i );
            writeComputeType( stmt );
            writeTaskGroup( stmt );
            if( mode == MODE_COMPUTES_FOR ){
                writeComputeTime( stmt );
                writeComputeTimeUnits( stmt );
            }
            else if( mode == MODE_SLEEPS_FOR ){
                writeSleepTime( stmt );
                writeSleepTimeUnits( stmt );
            }
            else if( mode == MODE_TOUCHES_MEMORY ){
                writeTouchCount( stmt );
                writeTouchCountUnits( stmt );
                writeTouchRegion( stmt );
                writeTouchRegionUnits( stmt );
                writeTouchTimes( stmt );
                writeTouchStride( stmt );
                writeTouchStrideUnits( stmt );
            }
        }
    }

    private boolean verifyFields(){
        
        if( mode == MODE_COMPUTES_FOR ){
            if( verifyComputeType() &&
                verifyTaskGroup() &&
                verifyComputeTime() &&
                verifyComputeTimeUnits() )
                return true;
        }
        else if( mode == MODE_SLEEPS_FOR ){
            if( verifyComputeType() &&
                verifyTaskGroup() &&
                verifySleepTime() &&
                verifySleepTimeUnits() )
                return true;
        }
        else if( mode == MODE_TOUCHES_MEMORY ){
            if( verifyComputeType() &&
                verifyTaskGroup() &&
                verifyTouchCount() &&
                verifyTouchCountUnits() &&
                verifyTouchRegion() &&
                verifyTouchRegionUnits() &&
                verifyTouchTimes() &&
                verifyTouchStride() &&
                verifyTouchStrideUnits() )
                return true;
        }

        return false;
    }

    private void addScopeVariables( DialogMenu menu ){
        for( int i = 0; i < selectVariablesInScope.size(); i++ ){
            String variable = 
                (String)selectVariablesInScope.elementAt( i );
            menu.addItem( variable );
        }
    }

    public void windowClosing( WindowEvent event ) {
        deselectAllComputeStmts();
        updateState();
        program.repaint();
    }
    
    private void readVariablesInScope( ComputeStmt stmt ){
        selectVariablesInScope = 
            stmt.getVariablesInScope( selectVariablesInScope );
    }

}
