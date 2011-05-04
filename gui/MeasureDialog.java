/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: measure dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is responsible for maintaining the dialog for
 * manipulating a MeasureBlock. The implementation details are very
 * similar to CommunicationDialog, see the comments in
 * CommunicationDialog.java for more information.
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

public class MeasureDialog extends AbstractDialog {

    // there is one MeasureItem for each MeasureExpression in the
    // MeasureBlock
    static class MeasureItem {
        public DialogMenu aggregate;
        public DialogMenu expression;
        public DialogMenu comment;
        public String selectAggregate;
        public String selectExpression;
        public String selectComment;
    }

    private DialogPane dialogPane;

    private static final int MODE_INIT = -2;
    private static final int MODE_DEFAULT = 0;

    private int mode;

    private DialogMenu taskGroup;
    private DialogMenu insideOutside;

    private String selectTaskGroup;
    private String selectInsideOutside;
    private Vector measureItems;

    private Vector selectVariablesInScope;

    private boolean changeInsideOutside;

    public MeasureDialog( Program program, DialogPane dialogPane ){
        super( program );

        this.dialogPane = dialogPane;

        measureItems = new Vector();
    }

    public void actionPerformed( ActionEvent event ){
        if( mode == MODE_INIT )
            return;

        String command = event.getActionCommand();
        Object source = event.getSource();

        if( command.equals( "Apply" ) ){
            if( verifyFields( true ) ){
                program.pushState();
                applyChanges( getSelectedMeasureBlocks() );
                updateState();
                program.updateState();
            }
        }
        else if( command.equals( "Reset" ) )
            updateState();
        else if( command.equals( "Add Expression" ) ){
            verifyFields( false );
            MeasureItem item = new MeasureItem();
            item.selectAggregate = "";
            item.selectExpression = "";
            item.selectComment = "";
            measureItems.add( item );
            defaultMode();
        }
        else if( command.equals( "delete" ) ){
            verifyFields( false );
            IdButton idButton = (IdButton)source;
            measureItems.removeElementAt( idButton.getID() );
            defaultMode();
        }
    }

    public void defaultMode(){
        mode = MODE_INIT;

        dialogPane.clear();

        JPanel pane1 = new JPanel();
        pane1.setLayout( new FlowLayout( FlowLayout.LEFT ) );
        dialogPane.add( pane1 );

        taskGroup = new DialogMenu( 430 );
        taskGroup.addItem( selectTaskGroup );
        taskGroup.addSourceTaskDescriptions();
        taskGroup.setEditable( true );
        pane1.add( taskGroup );

        if( selectInsideOutside != null ){
            insideOutside = new DialogMenu();
            insideOutside.addItem( selectInsideOutside );
            insideOutside.addItem( "inside loop" );
            insideOutside.addItem( "outside loop" );
            pane1.add( insideOutside );
        }

        pane1.add( new JLabel( " measures:" ) );

        for( int i = 0; i < measureItems.size(); i++ ){
            MeasureItem item = (MeasureItem)measureItems.elementAt( i );

            JPanel expressionPane = new JPanel();
            expressionPane.setLayout( new FlowLayout( FlowLayout.LEFT ) );
            dialogPane.add( expressionPane );

            item.aggregate = new DialogMenu();
            item.aggregate.addItem( item.selectAggregate );
            item.aggregate.addItem( "" );
            item.aggregate.addItem( "the" );
            item.aggregate.addItem( "the mean of" );
            item.aggregate.addItem( "the harmonic mean of" );
            item.aggregate.addItem( "the geometric mean of" );
            item.aggregate.addItem( "the median of" );
            item.aggregate.addItem( "the standard deviation of" );
            item.aggregate.addItem( "the variance of" );
            item.aggregate.addItem( "the sum of" );
            item.aggregate.addItem( "the minimum of" );
            item.aggregate.addItem( "the maximum of" );
            item.aggregate.addItem( "the final" );
            item.aggregate.addItem( "a histogram of" );
            expressionPane.add( item.aggregate );

            item.expression = new DialogMenu( 150 );
            item.expression.addItem( item.selectExpression );
            addScopeVariables( item.expression );
            item.expression.addItem( "(1E6*total_bytes)/(1M*elapsed_usecs)" );
            item.expression.setEditable( true );
            expressionPane.add( item.expression );

            expressionPane.add( new JLabel( " comment:" ) );

            item.comment = new DialogMenu( 150 );
            item.comment.addItem( item.selectComment );
            item.comment.setEditable( true );
            expressionPane.add( item.comment );

            IdButton idButton = new IdButton( "delete", i );
            idButton.addActionListener( this );
            expressionPane.add( idButton );
        }

        JPanel pane2 = new JPanel();
        pane2.setLayout( new FlowLayout( FlowLayout.CENTER ) );
        dialogPane.add( pane2 );

        JButton applyButton = new JButton( "Apply" );
        dialogPane.setDefaultButton( applyButton );
        JButton resetButton = new JButton( "Reset" );
        JButton addButton = new JButton( "Add Expression" );
        pane2.add( applyButton );
        pane2.add( resetButton );
        pane2.add( addButton );
        addButton.addActionListener( this );
        applyButton.addActionListener( this );
        resetButton.addActionListener( this );
        dialogPane.finalize();
        dialogPane.setEmpty( false );
        mode = MODE_DEFAULT;
    }

    public void updateState(){
        selectTaskGroup = null;
        selectInsideOutside = null;

        measureItems.clear();

        selectVariablesInScope = new Vector();

        Vector selectedMeasureBlocks = getSelectedMeasureBlocks();

        for( int i = 0; i < selectedMeasureBlocks.size(); i++ ){
            MeasureBlock block =
                (MeasureBlock)selectedMeasureBlocks.elementAt( i );

            readTaskGroup( block );
            readInsideOutside( block );
            readMeasureItems( block );
            readVariablesInScope( block );
        }

        if( selectedMeasureBlocks.size() > 0 )
            defaultMode();
    }

    public void deselectAllMeasureBlocks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof MeasureBlock )
                component.setSelected( false );
        }
    }

    public Vector getSelectedMeasureBlocks(){
        Vector selectedComponents = program.getAllSelected( new Vector() );
        Vector selectedMeasureBlocks = new Vector();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof MeasureBlock )
                selectedMeasureBlocks.add( component );
        }
        return selectedMeasureBlocks;
    }


    private void readTaskGroup( MeasureBlock block ){
        if( selectTaskGroup == null )
            selectTaskGroup = block.getTaskGroup().toCodeSource();
        else if( !selectTaskGroup.equals( block.getTaskGroup().toCodeSource() ) )
            selectTaskGroup = "-";
    }

    // selectInsideOutside is:
    // null - before the first measure block is read
    // "" - if no measure blocks are outer or inner
    // "-" - if multiple measure blocks in mixed states
    // "inside loop" - if measure block appears as the only component of a loop
    // "outside loop" - if measure block contains only a loop
    private void readInsideOutside( MeasureBlock block ){
        String type = null;

        // check if block is "inside loop"
        Block parentBlock = (Block)block.getParent();
        if( parentBlock instanceof Loop &&
            parentBlock.numComponents() == 1 ){
            type = "inside loop";
        }
        else if( block.numComponents() == 1 &&
                 block.componentAt( 0 ) instanceof Loop ){
            type = "outside loop";
        }
        if( selectInsideOutside == null )
            selectInsideOutside = type;
        else if( !selectInsideOutside.equals( type ) )
            selectInsideOutside = "-";
    }

    private void readMeasureItems( MeasureBlock block ){
        Vector measureExpressions = block.getMeasureExpressions();
        for( int i = 0; i < measureExpressions.size(); i++ ){
            MeasureExpression expression =
                (MeasureExpression)measureExpressions.elementAt( i );

            if( i >= measureItems.size() ){
                MeasureItem item = new MeasureItem();
                item.selectAggregate = expression.aggregate;
                item.selectExpression = expression.expression;
                item.selectComment = expression.comment;
                measureItems.add( item );
            }
            else{
                MeasureItem item = (MeasureItem)measureItems.elementAt( i );
                if( !item.selectAggregate.equals( expression.aggregate ) )
                    item.selectAggregate = "-";
                if( !item.selectExpression.equals( expression.expression ) )
                    item.selectExpression = "-";
                if( !item.selectComment.equals( expression.comment ) )
                    item.selectComment = "-";
            }
        }
    }

    private void writeTaskGroup( MeasureBlock block ){
        if( !selectTaskGroup.equals( "-" ) )
            block.setTaskGroup( selectTaskGroup );
    }

    private void writeMeasureItems( MeasureBlock block ){
        block.clearMeasureExpressions();
        for( int i = 0; i < measureItems.size(); i++ ){
            MeasureItem item = (MeasureItem)measureItems.elementAt( i );
            MeasureExpression expression = new MeasureExpression();
            expression.aggregate = item.selectAggregate;
            expression.expression = item.selectExpression;
            expression.comment = item.selectComment;
            block.addMeasureExpression( expression );
        }
    }

    private void writeInsideOutside( MeasureBlock block ){
        if( selectInsideOutside == null )
            return;

        if( !changeInsideOutside ){
            if( selectInsideOutside.equals( "inside loop" ) ){
                Loop loop = (Loop)block.getParent();
                loop.setComputeAggregatesGroup( block.getTaskGroup() );
            }
            return;
        }

        // move the measure block inside the loop
        if( selectInsideOutside.equals( "inside loop" ) ){
            Block parentBlock = (Block)block.getParent();
            int position = parentBlock.findPosition( block );
            Loop loop = (Loop)block.componentAt( 0 );
            loop.detach();
            block.detach();
            block.takeComponents( loop );
            loop.add( block );
            parentBlock.insertAt( loop, position );
            loop.setComputeAggregatesGroup( block.getTaskGroup() );
        }
        // move the measure block outside the loop
        else if( selectInsideOutside.equals( "outside loop" ) ){
            Loop loop = (Loop)block.getParent();
            Block parentBlock = (Block)loop.getParent();
            int position = parentBlock.findPosition( loop );
            block.detach();
            loop.detach();
            loop.takeComponents( block );
            block.add( loop );
            parentBlock.insertAt( block, position );
            loop.setComputeAggregatesGroup( (TaskGroup)null );
        }
    }

    private boolean verifyTaskGroup( boolean complain ){
        selectTaskGroup = (String)taskGroup.getSelectedItem();
        if( program.verifyField( selectTaskGroup, "source_task",
                                 selectVariablesInScope ) )
            return true;
        else if( complain )
            program.showErrorDialog( "\"" + selectTaskGroup +
                                     "\" is not a valid task description" );
        return false;
    }

    private boolean verifyMeasureItems( boolean complain ){
        for( int i = 0; i < measureItems.size(); i++ ){
            MeasureItem item = (MeasureItem)measureItems.elementAt( i );
            item.selectAggregate = (String)item.aggregate.getSelectedItem();

            item.selectExpression = (String)item.expression.getSelectedItem();
            if( !program.verifyField( item.selectExpression, "expr",
                                      selectVariablesInScope ) ){
                if( complain )
                    program.showErrorDialog( "\"" + item.selectExpression +
                                             "\" is not a valid expression" );
                return false;
            }

            item.selectComment = (String)item.comment.getSelectedItem();
        }
        return true;
    }

    private boolean verifyInsideOutside( boolean complain ){
        if( selectInsideOutside == null )
            return true;

        if( !selectInsideOutside.equals( (String)insideOutside.getSelectedItem() ) )
            changeInsideOutside = true;
        else
            changeInsideOutside = false;

        selectInsideOutside = (String)insideOutside.getSelectedItem();
        return true;
    }

    private void applyChanges( Vector measureBlocks ){
        for( int i = 0; i < measureBlocks.size(); i++ ){
            MeasureBlock block =
                (MeasureBlock)measureBlocks.elementAt( i );
            writeTaskGroup( block );
            writeInsideOutside( block );
            writeMeasureItems( block );
        }
    }

    private boolean verifyFields( boolean complain ){

        if( verifyTaskGroup( complain ) &&
            verifyInsideOutside( complain ) &&
            verifyMeasureItems( complain ) )
            return true;

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
        deselectAllMeasureBlocks();
        updateState();
        program.repaint();
    }

    private void readVariablesInScope( MeasureBlock block ){
        selectVariablesInScope =
            block.getAllVariablesInScope( selectVariablesInScope );
    }

}
