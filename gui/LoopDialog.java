/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: loop dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class maintains the dialog for manipulating a Loop. The
 * implementation details are very similar to CommunicationDialog, see
 * the comments in CommunicationDialog.java for more information.
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
import java.awt.Container;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;

import java.util.*;

public class LoopDialog extends AbstractDialog {

    static class SequenceItem{
        public String selectSequence;
        public JTextField sequence;
    }

    private static final int MODE_INIT = -2;
    private static final int MODE_MIXED = -1;
    private static final int MODE_REPETITIONS = 0;
    private static final int MODE_SEQUENCE = 1;
    private static final int MODE_TIMED = 2;
    
    private int mode;

    private DialogPane dialogPane;
    
    // shared between modes
    private DialogMenu loopType;
    
    // repetitions mode
    private DialogMenu numReps;
    private DialogMenu numWarmups;
    private JCheckBox sync;

    // sequence mode
    private JTextField sequenceName;
    private Vector sequenceItems;
    
    // timed mode
    private DialogMenu time;
    private DialogMenu timeUnits;
    
    private boolean isSyncMixed;
    private boolean isFirstSync;

    private int selectLoopType;
    private String selectNumReps;
    private String selectNumWarmups;
    private boolean selectSync;
    private String selectSequenceName;
    private String selectTime;
    private String selectTimeUnits;
    private Vector selectVariablesInScope;

    public LoopDialog( Program program, DialogPane dialogPane ){
        super( program );

        this.dialogPane = dialogPane;

        sequenceItems = new Vector();
    }

    public void actionPerformed( ActionEvent event ){
        if( mode == MODE_INIT )
            return;

        String command = event.getActionCommand();
        Object source = event.getSource();
        
        if( command.equals( "comboBoxChanged" ) && 
            source == loopType ){
            String type = (String)loopType.getSelectedItem();
            if( type.equals( "repetitions" ) )
                repetitionsMode();
            else if( type.equals( "sequence" ) )
                sequenceMode();
            else if( type.equals( "timed" ) )
                timedMode();
            else
                assert false;
        }
        else if( command.equals( "Apply" ) ){
            if( verifyFields( true ) ){
                program.pushState();
                applyChanges( getSelectedLoops() );
                updateState();
                program.updateState();
            }
        }
        else if( command.equals( "Reset" ) )
            updateState();
        else if( command.equals( "Add Sequence" ) ){
            if( !verifyFields( false ) )
                return;
            SequenceItem item = new SequenceItem();
            item.selectSequence = "";
            sequenceItems.add( item );
            sequenceMode();
        }
        else if( command.equals( "delete" ) ){
            verifyFields( false );
            IdButton idButton = (IdButton)source;
            sequenceItems.removeElementAt( idButton.getID() );
            sequenceMode();
        }
        else if( source == sync )
            isSyncMixed = false;
    }
    
    public void repetitionsMode(){
        mode = MODE_INIT;

        dialogPane.clear();

        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "loop type: " ) );
        loopType = new DialogMenu();
        loopType.addItem( "repetitions" );
        loopType.addItem( "sequence" );
        loopType.addItem( "timed" );
        loopType.addActionListener( this );
        loopType.setSelectedIndex( MODE_REPETITIONS );
        pane1.add( loopType );
        
        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        pane2.add( new JLabel( "warmup repetitions:" ) );
        numWarmups = new DialogMenu( 150 );
        numWarmups.addItem( selectNumWarmups );
        addScopeVariables( numWarmups );
        numWarmups.setEditable( true );
        pane2.add( numWarmups );

        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane3 );

        sync = new JCheckBox();
        sync.setSelected( selectSync );
        sync.addActionListener( this );
        pane3.add( sync );
        pane3.add( new JLabel( "synchronize after warmups" ) );

        JPanel pane4 = new JPanel();
        pane4.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane4 );

        pane4.add( new JLabel( "repetitions:" ) );
        numReps = new DialogMenu( 150 );
        numReps.addItem( selectNumReps );
        addScopeVariables( numReps );
        numReps.setEditable( true );
        pane4.add( numReps );

        JPanel pane5 = new JPanel();
        pane5.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane5 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        pane5.add( applyButton );
        pane5.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_REPETITIONS;
    }

    public void sequenceMode(){
        mode = MODE_INIT;
        
        dialogPane.clear();
        
        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "loop type: " ) );
        loopType = new DialogMenu();
        loopType.addItem( "repetitions" );
        loopType.addItem( "sequence" );
        loopType.addItem( "timed" );
        loopType.addActionListener( this );
        loopType.setSelectedIndex( MODE_SEQUENCE );
        pane1.add( loopType );
        
        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        pane2.add( new JLabel( "variable name: " ) );
        sequenceName = new JTextField( 20 );
        sequenceName.setText( selectSequenceName );
        pane2.add( sequenceName );


        for( int i = 0; i < sequenceItems.size(); i++ ){
            SequenceItem item = (SequenceItem)sequenceItems.elementAt( i );

            JPanel sequencePane = new JPanel();
            sequencePane.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( sequencePane );
            
            sequencePane.add( new JLabel( "sequence " + (i + 1) + ": " ) );
            item.sequence = new JTextField( 40 );
            item.sequence.setText( item.selectSequence );
            sequencePane.add( item.sequence );

            IdButton idButton = new IdButton( "delete", i );
            idButton.addActionListener( this );
            sequencePane.add( idButton );
        }

        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane3 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        JButton addSequenceButton = new JButton( "Add Sequence" );
        pane3.add( applyButton );
        pane3.add( resetButton );
        pane3.add( addSequenceButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        addSequenceButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_SEQUENCE;
    }

    public void timedMode(){
        mode = MODE_INIT;
        
        dialogPane.clear();
        
        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        pane1.add( new JLabel( "loop type: " ) );
        loopType = new DialogMenu();
        loopType.addItem( "repetitions" );
        loopType.addItem( "sequence" );
        loopType.addItem( "timed" );
        loopType.addActionListener( this );

        loopType.setSelectedIndex( MODE_TIMED );
        pane1.add( loopType );
        
        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane2 );

        pane2.add( new JLabel( "time: " ) );
        time = new DialogMenu( 150 );
        time.setEditable( true );
        time.addItem( selectTime );
        addScopeVariables( time );
        pane2.add( time );
        
        timeUnits = new DialogMenu();
        timeUnits.addItem( selectTimeUnits );
        timeUnits.addItem( "microseconds" );
        timeUnits.addItem( "milliseconds" );
        timeUnits.addItem( "seconds" );
        timeUnits.addItem( "minutes" );
        timeUnits.addItem( "hours" );
        timeUnits.addItem( "days" );
        pane2.add( timeUnits );
        
        JPanel pane3 = new JPanel();
        pane3.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane3 );
        
        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        pane3.add( applyButton );
        pane3.add( resetButton );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_TIMED;
    }
    
    public void updateState(){
        selectLoopType = MODE_INIT;
        selectNumReps = null;
        selectSync = false;
        selectNumWarmups = null;
        selectSequenceName = null;
        selectTime = null;
        selectTimeUnits = null;
        selectVariablesInScope = new Vector();
        isSyncMixed = false;
        isFirstSync = true;

        sequenceItems.clear();

        Vector selectedLoops = getSelectedLoops(); 

        for( int i = 0; i < selectedLoops.size(); i++ ){
            Loop loop = (Loop)selectedLoops.elementAt( i );
            readLoopType( loop );
            readNumReps( loop );
            readSync( loop );
            readNumWarmups( loop );
            readSequenceItems( loop );
            readSequenceName( loop );
            readTime( loop );
            readTimeUnits( loop );
            readVariablesInScope( loop );
        }
        
        if( selectedLoops.size() > 0 ){
            switch( selectLoopType ){
            case MODE_REPETITIONS:
                repetitionsMode();
                break;
            case MODE_SEQUENCE:
                sequenceMode();
                break;
            case MODE_TIMED:
                timedMode();
                break;
            }
        }
    }

    public void deselectAllLoops(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Loop ){
                component.setSelected( false );
            }
        }
    }
    
    public Vector getSelectedLoops(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedLoops = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Loop )
                selectedLoops.add( component );
        }
        return selectedLoops;
    }

    public void windowClosing( WindowEvent event ) {
        deselectAllLoops();
        updateState();
        program.repaint();
    }

    private void readLoopType( Loop loop ){
        if( selectLoopType == MODE_INIT ){
            if( loop.getLoopType() == Loop.LOOP_TYPE_REPETITIONS )
                selectLoopType = MODE_REPETITIONS;
            else if( loop.getLoopType() == Loop.LOOP_TYPE_FOR_EACH )
                selectLoopType = MODE_SEQUENCE;
            else if( loop.getLoopType() == Loop.LOOP_TYPE_TIMED )
                selectLoopType = MODE_TIMED;
            else
                assert false;
        }
        else if( loop.getLoopType() != selectLoopType ) 
            selectLoopType = MODE_MIXED;
    }
    
    private void readNumReps( Loop loop ){
        if( selectNumReps == null )
            selectNumReps = loop.getNumReps();
        else if( !selectNumReps.equals( loop.getNumReps() ) )
            selectNumReps = "-";
    }
    
    private void readSync( Loop loop ){
        if( isFirstSync )
            selectSync = loop.getSync();
        else if( selectSync != loop.getSync() )
            isSyncMixed = true;
        isFirstSync = false;
    }
    
    private void readNumWarmups( Loop loop ){
        if( selectNumWarmups == null )
            selectNumWarmups = loop.getNumWarmups();
        else if( !selectNumWarmups.equals( loop.getNumWarmups() ) )
            selectNumWarmups = "-";
    }

    private void readSequenceItems( Loop loop ){
        Vector sequences = loop.getSequences();
        for( int i = 0; i < sequences.size(); i++ ){
            String sequence = (String)sequences.elementAt( i );

            if( i >= sequenceItems.size() ){
                SequenceItem item = new SequenceItem();
                item.selectSequence = sequence;
                sequenceItems.add( item );
            }
            else{
                SequenceItem item = (SequenceItem)sequenceItems.elementAt( i );
                if( !item.selectSequence.equals( sequence ) )
                    item.selectSequence = "-";
                else
                    item.selectSequence = sequence;
            }
        }
    }

    private void readSequenceName( Loop loop ){
        if( selectSequenceName == null )
            selectSequenceName = loop.getSequenceName();
        else if( !selectSequenceName.equals( loop.getSequenceName() ) )
            selectSequenceName = "-";
    }

    private void readTime( Loop loop ){
        if( selectTime == null )
            selectTime = loop.getTime();
        else if( !selectTime.equals( loop.getTime() ) )
            selectTime = "-";
    }

    private void readTimeUnits( Loop loop ){
        if( selectTimeUnits == null )
            selectTimeUnits = loop.getTimeUnits();
        else if( !selectTimeUnits.equals( loop.getTimeUnits() ) )
            selectTimeUnits = "-";
    }

    private void readVariablesInScope( Loop loop ){
        selectVariablesInScope = 
            loop.getVariablesInScope( selectVariablesInScope );
    }

    private void writeLoopType( Loop loop ){
        selectLoopType = loopType.getSelectedIndex();
        if( selectLoopType == MODE_REPETITIONS )
            loop.setLoopType( Loop.LOOP_TYPE_REPETITIONS );
        else if( selectLoopType == MODE_SEQUENCE )
            loop.setLoopType( Loop.LOOP_TYPE_FOR_EACH );
        else if( selectLoopType == MODE_TIMED )
            loop.setLoopType( Loop.LOOP_TYPE_TIMED );
    }
    
    private void writeNumReps( Loop loop ){
        if( !selectNumReps.equals( "-" ) )
            loop.setNumReps( selectNumReps );
    }

    private void writeNumWarmups( Loop loop ){
        if( !selectNumWarmups.equals( "-" ) )
            loop.setNumWarmups( selectNumWarmups );
    }

    private void writeSync( Loop loop ){
        if( !isSyncMixed )
            loop.setSync( selectSync );
    }

    private void writeSequenceItems( Loop loop ){
        loop.clearSequences();
        
        for( int i = 0; i < sequenceItems.size(); i++ ){
            SequenceItem item = (SequenceItem)sequenceItems.elementAt( i );

            if( !item.selectSequence.equals( "" ) )
                loop.addSequence( item.selectSequence );
        }
    }

    private void writeSequenceName( Loop loop ){
        if( !selectSequenceName.equals( "-" ) )
            loop.setSequenceName( selectSequenceName );
    }

    private void writeTime( Loop loop ){
        if( !selectTime.equals( "-" ) )
            loop.setTime( selectTime );
    }

    private void writeTimeUnits( Loop loop ){
        if( !selectTimeUnits.equals( "-" ) )
            loop.setTimeUnits( selectTimeUnits );
    }
    
    private boolean verifyLoopType(){
        selectLoopType = loopType.getSelectedIndex();
        return true;
    }
    
    private boolean verifyNumReps(){
        selectNumReps = (String)numReps.getSelectedItem();
        if( program.verifyField( selectNumReps, "expr", 
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectNumReps +  
                                     "\" is not a valid expression for reps" );
            return false;
        }
    }

    private boolean verifyNumWarmups(){
        selectNumWarmups = (String)numWarmups.getSelectedItem();
        if( program.verifyField( selectNumWarmups, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectNumWarmups +  
                                     "\" is not a valid expression for warmups" );
            return false;
        }
    }

    private boolean verifySync(){
        if( !isSyncMixed )
            selectSync = sync.isSelected();
        return true;
    }

    private boolean verifySequenceItems( boolean complain ){
        for( int i = 0; i < sequenceItems.size(); i++ ){
            SequenceItem item = (SequenceItem)sequenceItems.elementAt( i );
            
            item.selectSequence = item.sequence.getText();
            if( !item.selectSequence.equals( "" ) && 
                !program.verifyField( "{" + item.selectSequence + "}", "range",
                                      selectVariablesInScope ) ){
                if( complain )
                    program.showErrorDialog( "\"" + item.selectSequence +  
                                             "\" is not a valid sequence" );
                return false;
            }
        }
        return true;
    }

    private boolean verifySequenceName(){
        selectSequenceName = Utility.toIdentifier( sequenceName.getText() );
        return true;
    }

    private boolean verifyTime(){
        selectTime = (String)time.getSelectedItem();
        if( program.verifyField( selectTime, "expr",
                                 selectVariablesInScope ) )
            return true;
        else{
            program.showErrorDialog( "\"" + selectTime +  
                                     "\" is not a valid expression for time" );
            return false;
        }
    }

    private boolean verifyTimeUnits(){
        selectTimeUnits = (String)timeUnits.getSelectedItem();
        return true;
    }

    private void applyChanges( Vector loops ){
        for( int i = 0; i < loops.size(); i++ ){
            Loop loop = (Loop)loops.elementAt( i );
            if( mode == MODE_REPETITIONS ){
                writeLoopType( loop );
                writeNumReps( loop );
                writeNumWarmups( loop );
                writeSync( loop );
            }
            else if( mode == MODE_SEQUENCE ){
                writeLoopType( loop );
                writeSequenceItems( loop );
                writeSequenceName( loop );
            }
            else if( mode == MODE_TIMED ){
                writeLoopType( loop );
                writeTime( loop );
                writeTimeUnits( loop );
            }
        }
    }

    private boolean verifyFields( boolean complain ){
        if( mode == MODE_REPETITIONS ){
            if( verifyLoopType()
                && verifyNumReps()
                && verifyNumWarmups()
                && verifySync() )
                return true;
        }
        else if( mode == MODE_SEQUENCE ){
            if( verifyLoopType()
                && verifySequenceItems( complain )
                && verifySequenceName() )
                return true;
        }
        else if( mode == MODE_TIMED ){
            if( verifyLoopType()
                && verifyTime()
                && verifyTimeUnits() )
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

}
