/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: program
 *
 * By Nick Moss <nickm@lanl.gov>
 * Improved and corrected by Paul Beinfest <beinfest@lanl.gov>
 * Modifications for Eclipse by Paul Beinfest <beinfest@lanl.gov>
 * Printing support and some bug fixes by Scott Pakin <pakin@lanl.gov>
 *
 * Program is the top-level container of all other components in a
 * program. It contains various methods for manipulating a program,
 * e.g: adding components, event-handling, and maintaining program
 * state and the various dialogs.
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
import java.awt.print.*;
import javax.swing.*;
import javax.swing.event.*;
import java.util.*;
import java.io.*;
import java.security.*;
import org.python.core.*;
import gov.lanl.c3.ncptl.*;

public class Program extends AbstractComponent
    implements KeyListener, Printable {

    // a vector of RowSelection's are used to determine program state
    // in order to determine which toolbar buttons to enable. there
    // will be one RowSelection for each task row that contains any
    // selected tasks
    public static class RowSelection {
        public Vector tasks;  // the selected tasks
        public Block block; // the parent block of the task row
        public TaskRow taskRow; // the task row
    }

    // ProgramState is used to implement undo and contains all the
    // needed information to restore a program to a previous state. A
    // stack of ProgramState's is used whereby a ProgramState is a
    // cloned snapshot of the program that is pushed onto the stack
    // whenever a change to the program is made.
    public static class ProgramState {
        public Vector comesFroms;
        public Block mainBlock;
    }

    // initial number of tasks to display
    public static final int DEFAULT_NUM_TASKS = 16;

    // the initial minimum height of the scroll pane
    private static final int DEFAULT_MIN_HEIGHT = 2000;

    // the amount of additional space on the left and right
    private static final int X_PADDING = 180;

    // the amount of additional space at the bottom
    private static final int Y_PADDING = 200;

    // the main block of the program
    private Block mainBlock;

    // source and target task when dragging from task to task to
    // create a communication statement
    private Task sourceTask;
    private Task targetTask;

    // used when creating block components to determine the rows
    // around which to create the block
    private TaskRow sourceRow;
    private TaskRow targetRow;

    // the cursor is the insertion point for adding new components
    private Cursor cursor;

    // the toolbar of action buttons at the top of the main pane
    private ToolBar toolBar;

    // the selection rectangle, null when not dragging a selection
    private Rectangle dragRect;

    // the point where dragging selection rectangle originated
    private Point dragStart;

    // command-line options associated with the program
    private Vector comesFroms;

    // the language version number
    private String version;

    // using when dragging between tasks to create a CommunicationStmt
    private Point dragArrowStart;
    private Point dragArrowEnd;

    // all of the dialogs
    private CommunicationDialog communicationDialog;
    private ComputeDialog computeDialog;
    private MeasureDialog measureDialog;
    private LoopDialog loopDialog;
    private ReduceDialog reduceDialog;
    private SynchronizeDialog synchronizeDialog;
    private MulticastDialog multicastDialog;
    private SettingsDialog settingsDialog;
    private WaitDialog waitDialog;
    private ExtendDialog extendDialog;
    private LetDialog letDialog;
    private OtherDialog otherDialog;
    private IfDialog ifDialog;
    private ComesFromsDialog comesFromsDialog;

    // used to interface with the parser and lexer
    private GUIPyInterface pyInterface;

    // the top-level Swing or AWT container
    // either a JFrame, Frame, or JApplet
    private Container container;

    // the number of tasks to display
    private int numTasks;

    // the currently selected tasks by row
    private Vector rowSelections;

    // the file path of the current program
    private String filePath;

    // the pane in which the dialogs are displayed at the bottom of
    // the main pane
    private DialogPane dialogPane;

    // a vector containing the already selected components, used when
    // shift-dragging to add to a selection
    private Vector alreadySelected;

    // the paste buffer
    private Vector pasteComponents;

    // the main menu attached to the top of the frame
    private MainMenu mainMenu;

    // a stack of the previous program states used for undo
    private Vector programStates;

    // used for resizing the scroll pane area
    private Rectangle lastBounds;

    // the auto-scrollable scroll pane
    private AutoScrollPane scrollPane;

    // comments not associated with a component at the very beginning
    // of the program
    private String startComments;

    // comments not associated with a component at the very end of the
    // program
    private String endComments;

    // true if all changes to the program have been saved. used for
    // presenting a dialog asking the user if changes should be saved
    // on exiting
    private boolean saved;

    // string representing the complete program
    private String progString;

    // dialog box for the user to open or save a program
    private JFileChooser fileChooser;

    public Program( Container container ){
        communicationDialog = null;
        computeDialog = null;
        measureDialog = null;
        loopDialog = null;
        reduceDialog = null;
        waitDialog = null;
        extendDialog = null;
        ifDialog = null;
        sourceTask = null;
        targetTask = null;
        dragRect = null;
        sourceRow = null;
        targetRow = null;
        filePath = null;
        dialogPane = null;
        mainMenu = null;

        this.container = container;

        mainBlock = new Block( this );
        add( mainBlock );
        cursor = new Cursor( this );
        dragStart = new Point();
        comesFroms = new Vector();
        pasteComponents = new Vector();
        pyInterface = new GUIPyInterface( DEFAULT_NUM_TASKS );
        version = pyInterface.get_language_version();
        setNumTasks( DEFAULT_NUM_TASKS );
        alreadySelected = new Vector();
        programStates = new Vector();
        lastBounds = null;
        scrollPane = null;
        startComments = null;
        endComments = null;
        saved = true;
        setFocusable( true );
        requestFocusInWindow();
        addKeyListener( this );
        try {
            fileChooser = new JFileChooser();
            fileChooser.setFileFilter( new ncptlFileFilter() );
        } catch( AccessControlException error ) {
            fileChooser = null;
        }
    }

    // updates the toolbar and menus based on which components are
    // selected and the position of the cursor
    public void updateState(){

        Rectangle bounds = mainBlock.getBounds();
        if( lastBounds == null || lastBounds.width != bounds.width ||
            lastBounds.height != bounds.height ){
            setPreferredSize( new Dimension( numTasks*(Task.TASK_SIZE+TaskRow.TASK_SPACING) + X_PADDING, Math.max( DEFAULT_MIN_HEIGHT, bounds.height + Y_PADDING ) ) );
            lastBounds = bounds;
        }

        // only update when not dragging a selection rectangle
        if( dragRect != null )
            return;

        boolean enableDelete = false;
        boolean enableMeasure = false;
        boolean enableLoop = false;
        boolean cursorVisible = true;

        // get all selected components
        Vector selectedComponents = mainBlock.getAllSelected( new Vector() );

        // only enable undo if there is something to undo
        if( programStates.size() > 0 )
            mainMenu.enableUndo( true );
        else
            mainMenu.enableUndo( false );

        mainMenu.enableCut( false );
        mainMenu.enableCopy( false );
        mainMenu.enablePaste( false );

        // determine if extend should be enabled
        if( enableExtend( selectedComponents ) )
            toolBar.enableExtend( true );
        else
            toolBar.enableExtend( false );

        if( sameRowStmts( selectedComponents ) ){
            mainMenu.enableCut( true );
            mainMenu.enableCopy( true );
        }

        // only enable normalize when the program is non-empty
        if( mainBlock.numComponents() > 0 )
            toolBar.enableNormalize( true );
        else
            toolBar.enableNormalize( false );

        // get the selected components by row
        rowSelections = getRowSelections( selectedComponents );

        // loop through selected components to determine what should
        // be enabled
        for( int i = 0; i < selectedComponents.size(); i++ ){
            cursorVisible = false;
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );

            if( component instanceof Block ){
                mainMenu.enableCut( true );
                mainMenu.enableCopy( true );
                enableDelete = true;
                enableMeasure = true;
                enableLoop = true;
            }
            else if( component instanceof Stmt )
                enableDelete = true;
            else if( component instanceof TaskRow ){
                enableDelete = true;

                mainMenu.enableCut( true );
                mainMenu.enableCopy( true );

                // traverse the task row's parent block
                // for other selected task rows to determine
                // if "Loop" or "Measure" should be enabled
                Block block = (Block)component.getParent();
                block.traverseReset();
                TaskRow firstRow = null;
                TaskRow lastRow = null;
                AbstractComponent currentComponent;
                while( (currentComponent = block.traverseNext()) != null ){
                    if( currentComponent instanceof TaskRow &&
                        currentComponent.isSelected() ){
                        if( firstRow == null )
                            firstRow = (TaskRow)currentComponent;
                        lastRow = (TaskRow)currentComponent;
                    }
                }
                if( firstRow != null && lastRow != null ){
                    sourceRow = firstRow;
                    targetRow = lastRow;
                    enableMeasure = true;
                    enableLoop = true;
                }
            }
        }

        cursor.setVisible( cursorVisible );

        toolBar.enableDelete( enableDelete );
        toolBar.enableMeasure( enableMeasure );
        toolBar.enableLoop( enableLoop );

        toolBar.enableSynchronize( false );
        toolBar.enableReduce( false );
        toolBar.enableMulticast( false );
        toolBar.enableCommunicate( false );
        toolBar.enableWait( false );
        toolBar.enableCompute( false );
        toolBar.enableAddRow( false );

        if( cursor.isVisible() ){
            // determine if pasting stmts should be enabled
            if( pasteComponents.size() > 0 &&
                !sameRowStmts( pasteComponents ) )
                mainMenu.enablePaste( true );

            toolBar.enableAddRow( true );

            // determine if insertion of collectives should be enabled
            // by examining the component just before the cursor
            Block block = (Block)cursor.getParent();
            int cursorPosition = block.findPosition( cursor );
            AbstractComponent component = block.componentAt( cursorPosition-1 );
            if( component instanceof TaskRow &&
                !((TaskRow)component).hasStmts() ){
                toolBar.enableSynchronize( true );
                toolBar.enableReduce( true );
                toolBar.enableMulticast( true );
                toolBar.enableWait( true );
            }
        }
        else{
            // determine if statements can be pasted onto the selection
            if( (selectedComponents.size() == 1 &&
                selectedComponents.elementAt( 0 ) instanceof TaskRow &&
                sameRowStmts( pasteComponents )) ||
                enableTaskPasteStmts( selectedComponents, pasteComponents ) )
                mainMenu.enablePaste( true );

            // determine how individual tasks being selected should
            // enable various actions

            // with tasks selected in a single row
            if( rowSelections.size() == 1 ){
                RowSelection rowSelection =
                    (RowSelection)rowSelections.elementAt( 0 );
                if( !rowSelection.taskRow.hasCollectives() &&
                    rowSelection.tasks.size() > 0 )
                    toolBar.enableCompute( true );
                if( !rowSelection.taskRow.hasStmts() ){
                    toolBar.enableSynchronize( true );
                    toolBar.enableWait( true );
                }
            }

            // with tasks selected in two consecutive rows
            else if( rowSelections.size() == 2 ){
                RowSelection sourceRowSelection =
                    (RowSelection)rowSelections.elementAt( 0 );
                RowSelection targetRowSelection =
                    (RowSelection)rowSelections.elementAt( 1 );
                if( sourceRowSelection.block == targetRowSelection.block ){
                    if( !sourceRowSelection.taskRow.hasCollectives() )
                        toolBar.enableCommunicate( true );
                    if( !sourceRowSelection.taskRow.hasStmts() &&
                        sourceRowSelection.taskRow.getID()  ==
                        targetRowSelection.taskRow.getID() - 1 ){
                        toolBar.enableReduce( true );
                        toolBar.enableMulticast( true );
                    }
                }
            }
            // enable "Add Row" to allow a task row to be inserted at
            // the single currently selected row
            if( selectedComponents.size() == 1 &&
                selectedComponents.elementAt( 0 ) instanceof TaskRow )
                toolBar.enableAddRow( true );

        }
        // if nothing is selected and the dialogPane is not already
        // occupied, then display the help messages
        if( selectedComponents.size() == 0 ||
            dialogPane.isEmpty() ){
            dialogPane.clear();
            updateHelpPane();
            dialogPane.finalize();
            dialogPane.setEmpty( true );

            // request the focus so KeyListener methods will work
            requestFocusInWindow();
        }
        repaint();
    }

    public Vector getComesFroms(){
        return comesFroms;
    }

    public void setComesFroms( Vector comesFroms ){
        this.comesFroms = comesFroms;
    }

    public void paintComponent( Graphics graphics ){
        Rectangle programBounds = getBounds();
        Rectangle bounds = mainBlock.getBounds();

        // center the main block
        mainBlock.setBounds( (programBounds.width - bounds.width) / 2,
                             bounds.y, bounds.width, bounds.height );

        mainBlock.paintStmts( graphics );

        // draw the drag selection rectangle if a drag selection is in
        // progress
        if( dragRect != null ){
            GraphicsUtility graphicsUtility =
                new GraphicsUtility( graphics );
            graphicsUtility.setStroke( GraphicsUtility.STROKE_DASH );
            graphics.drawRect( dragRect.x, dragRect.y,
                                        dragRect.width, dragRect.height );
            graphicsUtility.setStroke( GraphicsUtility.STROKE_NORMAL );
        }

        // draw a dashed arrow if there is a drag from task in
        // progress to create a CommunicationStmt
        if( dragArrowStart != null ){
            GraphicsUtility graphicsUtility =
                new GraphicsUtility( graphics );
            graphicsUtility.drawArrow( 6.0f, dragArrowStart.x,
                                       dragArrowStart.y,
                                       dragArrowEnd.x,
                                       dragArrowEnd.y );
        }
    }

    // add a row at the current cursor position or insert one at the
    // selected task row
    public void addTaskRow(){
        pushState();
        // insert a row at the cursor
        if( cursor.isVisible() ){
            Block cursorBlock = (Block)cursor.getParent();
            int cursorPosition = cursorBlock.findPosition( cursor );
            cursor.detach();
            TaskRow taskRow = new TaskRow( this );
            cursorBlock.insertAt( taskRow, cursorPosition );
            cursorBlock.insertAt( cursor, cursorPosition + 1 );
        }
        // insert a row after the selected task row
        else{
            Vector selectedComponents = getAllSelected( new Vector() );
            TaskRow taskRow = (TaskRow)selectedComponents.elementAt( 0 );
            Block parentBlock = (Block)taskRow.getParent();
            TaskRow newRow = new TaskRow( this );
            newRow.takeStmts( taskRow );
            parentBlock.insertAt( newRow, taskRow.getID() + 1 );
        }
        updateState();
        repaint();
    }

    // delete the selected components updating the dialogs as
    // necessary
    public void deleteSelectedComponents(){
        // save undo state
        pushState();

        boolean updateLoopDialog = false;
        boolean updateMeasureDialog = false;
        boolean updateCommunicationDialog = false;
        boolean updateComputeDialog = false;
        boolean updateReduceDialog = false;
        boolean updateSynchronizeDialog = false;
        boolean updateMulticastDialog = false;
        boolean updateWaitDialog = false;
        boolean updateOtherDialog = false;
        boolean updateIfDialog = false;
        boolean updateLetDialog = false;

        boolean removedSelected = false;
        int i = 0;
        Vector selectedComponents = getAllSelected( new Vector() );
        while( i < selectedComponents.size() ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );

            if( component instanceof Loop ||
                component instanceof TaskRow ||
                component instanceof MeasureBlock ||
                component instanceof CommunicationStmt ||
                component instanceof ComputeStmt ||
                component instanceof SynchronizeStmt ||
                component instanceof ReduceStmt ||
                component instanceof MulticastStmt ||
                component instanceof WaitStmt ||
                component instanceof OtherStmt ||
                component instanceof IfBlock ||
                component instanceof LetBlock ){

                if( component instanceof Loop )
                    updateLoopDialog = true;
                else if( component instanceof MeasureBlock )
                    updateMeasureDialog = true;
                else if( component instanceof CommunicationStmt )
                    updateCommunicationDialog = true;
                else if( component instanceof ComputeStmt )
                    updateComputeDialog = true;
                else if( component instanceof ReduceStmt )
                    updateReduceDialog = true;
                else if( component instanceof SynchronizeStmt )
                    updateSynchronizeDialog = true;
                else if( component instanceof MulticastStmt )
                    updateMulticastDialog = true;
                else if( component instanceof WaitStmt )
                    updateWaitDialog = true;
                else if( component instanceof OtherStmt )
                    updateOtherDialog = true;
                else if( component instanceof IfBlock )
                    updateIfDialog = true;
                else if( component instanceof LetBlock )
                    updateLetDialog = true;

                // if the component is a block
                // remove its children and add them to the parent block
                if( component instanceof Block &&
                    !(component instanceof IfBlock) ){
                    Block block = (Block)component;
                    Block parentBlock = (Block)component.getParent();
                    int position = parentBlock.findPosition( component );
                    for( ;; ){
                        AbstractComponent childComponent =
                            block.componentAt( 0 );
                        if( childComponent == null )
                            break;
                        childComponent.detach();
                        parentBlock.insertAt( childComponent, position++ );
                    }
                }

                component.detach();
                selectedComponents.remove( component );
                removedSelected = true;
            }
            else
                i++;
        }
        if( updateLoopDialog )
            updateLoopDialog();
        if( updateMeasureDialog )
            updateMeasureDialog();
        if( updateCommunicationDialog )
            updateCommunicationDialog();
        if( updateComputeDialog )
            updateComputeDialog();
        if( updateReduceDialog )
            updateReduceDialog();
        if( updateSynchronizeDialog )
            updateSynchronizeDialog();
        if( updateMulticastDialog )
            updateMulticastDialog();
        if( updateWaitDialog )
            updateWaitDialog();
        if( updateOtherDialog )
            updateOtherDialog();
        if( updateIfDialog )
            updateIfDialog();
        if( updateLetDialog )
            updateLetDialog();

        if( removedSelected )
            updateState();
    }

    public void setSourceTask( Task task ){
        sourceTask = task;
    }

    public Task getSourceTask(){
        return sourceTask;
    }

    public void setTargetTask( Task task ){
        targetTask = task;
    }

    public Task getTargetTask(){
        return targetTask;
    }

    public TaskRow getSourceRow(){
        return sourceRow;
    }

    public TaskRow getTargetRow(){
        return targetRow;
    }

    // add a loop at the cursor or around the selected components
    public void addLoop(){
        // save undo state
        pushState();

        Loop loop = new Loop( this );

        // find the first selected component that is a block or task row
        Vector selectedComponents = getAllSelected( new Vector() );
        AbstractComponent firstComponent = null;
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Block ||
                component instanceof TaskRow ){
                firstComponent = component;
                break;
            }
        }

        assert firstComponent != null;
        AbstractComponent lastComponent = null;

        // find the last component in the same block that is of
        // the same type (if any)
        Block parentBlock = (Block)firstComponent.getParent();
        selectedComponents = parentBlock.getSelected();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Block ||
                component instanceof TaskRow ){
                lastComponent = component;
            }
        }

        if( lastComponent == firstComponent )
            lastComponent = null;


        if( lastComponent == null ){
            int insertPosition = parentBlock.findPosition( firstComponent );

            // take the component from its block and add it to the loop
            firstComponent.detach();
            loop.add( firstComponent );
            parentBlock.insertAt( loop, insertPosition );
        }
        else{
            // detach the components from firstComponent to
            // lastComponent and add them to the loop
            int startPosition = parentBlock.findPosition( firstComponent );
            int endPosition = parentBlock.findPosition( lastComponent );
            for( int i = startPosition; i <= endPosition; i++ ){
                AbstractComponent component =
                    parentBlock.componentAt( startPosition );
                component.detach();
                loop.add( component );
            }
            parentBlock.insertAt( loop, startPosition );
        }
        // deselect everything then select the loop
        setAllSelected( false );
        loop.setSelected( true );
        updateState();
    }

    // add a conditional at the cursor or around the selected components
    public void addConditional(){
        // save undo state
        pushState();

        // if the cursor is visible then insert the conditional at the
        // cursor position
        if( cursor.isVisible() ){
            Block block = (Block)cursor.getParent();
            int cursorPosition = block.findPosition( cursor );
            IfBlock ifBlock = new IfBlock( this );
            block.insertAt( ifBlock, cursorPosition );
            setAllSelected( false );
            ifBlock.setSelected( true );
            updateState();
            return;
        }

        // add the conditional around the selected components
        Vector selectedComponents = getAllSelected( new Vector() );
        AbstractComponent sourceComponent = null;

        // attempt to find a Loop or MeasureBlock as the sourceComponent
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Loop ||
                component instanceof MeasureBlock ){
                sourceComponent = component;
                break;
            }
        }
        IfBlock ifBlock = new IfBlock( this );
        GenericBlock thenBlock = ifBlock.getThenBlock();

        // add everything from the same block beginning at sourceComponent
        if( sourceComponent != null ){
            Block parentBlock = (Block)sourceComponent.getParent();
            int insertPosition = parentBlock.findPosition( sourceComponent );
            sourceComponent.detach();
            thenBlock.add( sourceComponent );
            parentBlock.insertAt( ifBlock, insertPosition );
        }

        // the start and end task rows were already determined in
        // updateState()
        else{
            Block parentBlock = (Block)sourceRow.getParent();
            int startPosition = parentBlock.findPosition( sourceRow );
            int endPosition = parentBlock.findPosition( targetRow );
            for( int i = startPosition; i <= endPosition; i++ ){
                AbstractComponent component =
                    parentBlock.componentAt( startPosition );
                component.detach();
                thenBlock.add( component );
            }
            parentBlock.insertAt( ifBlock, startPosition );
        }
        setAllSelected( false );
        ifBlock.setSelected( true );
        updateState();
    }

    // called automatically when the window is resized
    public void setSize( int width, int height ){
        // previously, the offscreen image was resized here
        super.setSize( width, height );
    }

    public void setToolBar( ToolBar toolBar ){
        this.toolBar = toolBar;
    }

    public ToolBar getToolBar(){
        return toolBar;
    }

    // called when dragging a selection rectangle, recursively calls
    // selectRegion on all components to allow them to be selected if
    // the component is sufficiently contained in rect. rect will be
    // passed as null at the end of dragging a selection which will
    // cause updateState() to be called
    public void dragSelection( Rectangle rect ){
        if( rect != null && dragRect == null )
            updateState();

        dragRect = rect;
        if( dragRect != null ){
            setAllSelected( false );
            for( int i = 0; i < alreadySelected.size(); i++ ){
                AbstractComponent component =
                    (AbstractComponent)alreadySelected.elementAt( i );
                component.setSelected( true );
            }
            mainBlock.selectRegion( dragRect );
        }
        else{
            dragSelectionDialogs();
            updateState();
        }
        repaint();
    }

    // draw a dashed arrow while dragging from sourceTask to create a
    // CommunicationStmt
    public void dragArrow( Point target ){
        if( target == null ){
            dragArrowStart = null;
            repaint();
            return;
        }
        Rectangle bounds = sourceTask.getGlobalBounds();
        dragArrowStart = new Point( bounds.x + bounds.width/2,
                                    bounds.y + bounds.height );
        if( targetTask == null )
            dragArrowEnd = new Point( target.x, target.y );
        else{
            Rectangle targetBounds = targetTask.getGlobalBounds();
            dragArrowEnd = new Point( targetBounds.x + targetBounds.width/2,
                                      targetBounds.y );
        }
        repaint();
    }

    // dragSelectionDialogs() is called at the end of dragging a
    // selection and allows the communication dialog to be displayed
    // after dragging to select multiple CommunicationStmt's (only
    // when the currently selected components consist only of
    // CommunicationStmt's)
    public void dragSelectionDialogs(){
        Vector selectedComponents = getAllSelected( new Vector() );
        if( selectedComponents.size() == 1 )
            updateDialogs();
        else{
            boolean allCommunicationStmts = true;
            for( int i = 0; i < selectedComponents.size(); i++ ){
                AbstractComponent component =
                    (AbstractComponent)selectedComponents.elementAt( i );
                if( !(component instanceof CommunicationStmt) ){
                    allCommunicationStmts = false;
                    break;
                }
            }
            if( allCommunicationStmts )
                updateCommunicationDialog();
        }
    }

    // clears the selected components unless shift or control was down
    public void mousePressed( MouseEvent mouseEvent ){
        container.requestFocus();
        if( mouseEvent.isShiftDown() || mouseEvent.isControlDown() )
            setAlreadySelected();
        else
            clearAlreadySelected();

        // a mousePressed event is received at the start of dragging
        // so set the dragStart point
        dragStart.x = mouseEvent.getX();
        dragStart.y = mouseEvent.getY();
    }

    // called whenever the mouse is moved when dragging
    public void mouseDragged( MouseEvent mouseEvent ){
        Rectangle dragRect = new Rectangle();

        // swap start and end points if needed
        if( mouseEvent.getX() < dragStart.x ){
            dragRect.x = mouseEvent.getX();
            dragRect.width = dragStart.x - mouseEvent.getX();
        }
        else{
            dragRect.x = dragStart.x;
            dragRect.width = mouseEvent.getX() - dragStart.x;
        }

        if( mouseEvent.getY() < dragStart.y ){
            dragRect.y = mouseEvent.getY();
            dragRect.height = dragStart.y - mouseEvent.getY();
        }
        else{
            dragRect.y = dragStart.y;
            dragRect.height = mouseEvent.getY() - dragStart.y;
        }

        dragSelection( dragRect );
    }

    // when the mouse is clicked, deselect all components unless shift
    // or control is down
    public void mouseClicked( MouseEvent mouseEvent ){
        if( !mouseEvent.isShiftDown() && !mouseEvent.isControlDown() ){
            setAllSelected( false );
            updateState();
        }
    }

    // the mouse was released, so if a drag selection was in progress,
    // release it
    public void mouseReleased( MouseEvent mouseEvent ){
        if( dragRect != null )
            dragSelection( null );
    }

    // move the cursor to the specified position in block.
    // doesn't allow the cursor to be inserted between any rows
    // with communication edges directed to the following task row
    public void moveCursor( Block block, int position ){
        // save the old cursor position so it can be re-attached
        // if the position is invalid
        Block oldBlock = (Block)cursor.getParent();
        int oldPosition = oldBlock.findPosition( cursor );
        cursor.detach();
        AbstractComponent component = block.componentAt( position - 1 );
        if( component != null && component instanceof TaskRow ){
            TaskRow taskRow = (TaskRow)component;
            taskRow.traverseReset();
            Stmt stmt;
            while( (stmt = taskRow.traverseNext()) != null ){
                // if stmt is one of the following, don't allow the
                // cursor to be inserted, move it back to its former
                // position and return
                if( stmt instanceof CommunicationStmt ||
                    stmt instanceof ReduceStmt ||
                    stmt instanceof MulticastStmt ){
                    oldBlock.insertAt( cursor, oldPosition );
                    return;
                }
            }
        }
        block.insertAt( cursor, position );
        setAllSelected( false );
        updateState();
    }

    public void addComesFrom( ComesFrom comesFrom ){
        comesFroms.add( comesFrom );
    }

    public void setVersion( String version ){
        this.version = version;
    }

    public String getVersion(){
        return version;
    }

    public Block getMainBlock(){
        return mainBlock;
    }

    // create a communication edge between two tasks
    public void createEdge( Task sourceTask, Task targetTask ){
        // save undo state
        pushState();

        // get source and target row and block that the tasks belong to
        TaskRow sourceRow = (TaskRow)sourceTask.getParent();
        Block sourceBlock = (Block)sourceRow.getParent();
        TaskRow targetRow = (TaskRow)targetTask.getParent();
        Block targetBlock = (Block)targetRow.getParent();

        int cursorPosition = sourceBlock.findPosition( cursor );
        boolean cursorDetached = false;

        // the cursor needs to be temporarily detached
        // in case it is directly between the source and target row
        if( sourceBlock == targetBlock &&
            cursorPosition == sourceTask.getRowID() + 1 &&
            cursorPosition == targetTask.getRowID() - 1 ){
            cursor.detach();
            cursorPosition++;
            cursorDetached = true;
        }

        // create the CommunicationStmt
        CommunicationStmt stmt = new CommunicationStmt( this );
        stmt.setSourceGroup( "task " + sourceTask.getID() );
        stmt.setTargetGroup( "task " + targetTask.getID() );

        // if the source task and target task are not in the same
        // block or are not in consecutive rows, then this is a split
        // send/receive
        if( sourceBlock != targetBlock ||
            sourceTask.getRowID() != targetTask.getRowID() - 1 )
            stmt.setTargetRow( (TaskRow)targetTask.getParent() );

        sourceRow.add( stmt );

        // if the cursor was detached, move it back to its former position
        // just after the target row
        if( cursorDetached )
            sourceBlock.insertAt( cursor, cursorPosition );

        setAllSelected( false );
        stmt.setSelected( true );
    }

    // clear the program of all components and command-line options
    public void clear(){
        comesFroms.clear();
        mainBlock.clear();
        mainBlock.add( cursor );
        updateState();
    }

    public void detachCursor(){
        cursor.detach();
    }

    // attach the cursor at the end of the main block
    public void attachCursor(){
        cursor.detach();
        mainBlock.add( cursor );
    }

    // the following methods set each of the dialogs and are called
    // after the dialogs are created in the GUI initialization

    public void setCommunicationDialog( CommunicationDialog communicationDialog ){
        this.communicationDialog = communicationDialog;
    }

    public void setComputeDialog( ComputeDialog computeDialog ){
        this.computeDialog = computeDialog;
    }

    public void setMeasureDialog( MeasureDialog measureDialog ){
        this.measureDialog = measureDialog;
    }

    public void setLoopDialog( LoopDialog loopDialog ){
        this.loopDialog = loopDialog;
    }

    public void setReduceDialog( ReduceDialog reduceDialog ){
        this.reduceDialog = reduceDialog;
    }

    public void setSynchronizeDialog( SynchronizeDialog synchronizeDialog ){
        this.synchronizeDialog = synchronizeDialog;
    }

    public void setMulticastDialog( MulticastDialog multicastDialog ){
        this.multicastDialog = multicastDialog;
    }

    public void setWaitDialog( WaitDialog waitDialog ){
        this.waitDialog = waitDialog;
    }

    public void setExtendDialog( ExtendDialog extendDialog ){
        this.extendDialog = extendDialog;
    }

    public void setIfDialog( IfDialog ifDialog ){
        this.ifDialog = ifDialog;
    }

    public void setLetDialog( LetDialog letDialog ){
        this.letDialog = letDialog;
    }

    public void setOtherDialog( OtherDialog otherDialog ){
        this.otherDialog = otherDialog;
    }

    public void setSettingsDialog( SettingsDialog settingsDialog ){
        this.settingsDialog = settingsDialog;
    }

    public void setComesFromsDialog( ComesFromsDialog comesFromsDialog ){
        this.comesFromsDialog = comesFromsDialog;
    }

    public void setDialogPane( DialogPane dialogPane ){
        this.dialogPane = dialogPane;
    }

    // append to the vector selectedComponents all selected
    // sub-components contained in the component
    public Vector getAllSelected( Vector selectedComponents ){
        return mainBlock.getAllSelected( selectedComponents );
    }

    // set the selection state of all sub-components
    public void setAllSelected( boolean flag ){
        mainBlock.setAllSelected( flag );
    }

    // the following methods cause each of the dialogs to be updated
    // according to the selected components. no update will be made
    // when a selection rectangle is being dragged

    public void updateLoopDialog(){
        if( dragRect != null )
            return;
        loopDialog.updateState();
    }

    public void updateMeasureDialog(){
        if( dragRect != null )
            return;
        measureDialog.updateState();
    }

    public void updateCommunicationDialog(){
        if( dragRect != null )
            return;
        communicationDialog.updateState();
    }

    public void updateComputeDialog(){
        if( dragRect != null )
            return;
        computeDialog.updateState();
    }

    public void updateSynchronizeDialog(){
        if( dragRect != null )
            return;
        synchronizeDialog.updateState();
    }

    public void updateReduceDialog(){
        if( dragRect != null )
            return;
        reduceDialog.updateState();
    }

    public void updateMulticastDialog(){
        if( dragRect != null )
            return;
        multicastDialog.updateState();
    }

    public void updateWaitDialog(){
        if( dragRect != null )
            return;
        waitDialog.updateState();
    }

    public void updateIfDialog(){
        if( dragRect != null )
            return;
        ifDialog.updateState();
    }

    public void updateOtherDialog(){
        if( dragRect != null )
            return;
        otherDialog.updateState();
    }

    public void updateLetDialog(){
        if( dragRect != null )
            return;
        letDialog.updateState();
    }

    public void updateSettingsDialog(){
        settingsDialog.updateState();
    }

    // update all dialogs
    public void updateDialogs(){
        updateLoopDialog();
        updateCommunicationDialog();
        updateComputeDialog();
        updateMeasureDialog();
        updateSynchronizeDialog();
        updateReduceDialog();
        updateMulticastDialog();
        updateWaitDialog();
        updateOtherDialog();
        updateIfDialog();
        updateLetDialog();
    }

    // this method is called recursively upward to determine all
    // variables within a component's scope and ends here after
    // appending comes froms
    public Vector getVariablesInScope( Vector variables ){
        // add comes froms
        for( int i = 0; i < comesFroms.size(); i++ ){
            ComesFrom comesFrom = (ComesFrom)comesFroms.elementAt( i );
            variables.add( comesFrom.identifier );
        }

        return variables;
    }

    // this method is the same as getVariablesInScope() but also
    // includes predeclared variables
    public Vector getAllVariablesInScope( Vector variables ){
        // get the initial set of variables
        getVariablesInScope( variables );

        // add predeclared variables
        String[] predeclared = pyInterface.get_predeclared_variables();
        for( int i = 0; i < predeclared.length; i++ ){
            variables.add( predeclared[ i ] );
        }

        return variables;
    }

    // add a ComputeStmt on the selected task
    public void addCompute(){
        // save the undo state
        pushState();

        RowSelection rowSelection =
            (RowSelection)rowSelections.elementAt( 0 );
        ComputeStmt stmt = new ComputeStmt( this );
        stmt.setTaskGroup( Utility.getTaskDescription( numTasks, rowSelection.tasks ) );
        rowSelection.taskRow.add( stmt );
        setAllSelected( false );
        stmt.setSelected( true );
        updateState();
        updateComputeDialog();
    }

    // add a MeasureBlock around the selected component(s)
    public void addMeasure(){
        // save the undo state
        pushState();

        MeasureBlock measureBlock = new MeasureBlock( this );

        // create a new default meausre expression
        MeasureExpression expression = new MeasureExpression();
        expression.aggregate = "";
        expression.expression = "elapsed_usecs";
        expression.comment = "Elapsed time (usecs)";
        measureBlock.addMeasureExpression( expression );

        // find the first selected component that is a block or task row
        Vector selectedComponents = getAllSelected( new Vector() );
        AbstractComponent firstComponent = null;
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Block ||
                component instanceof TaskRow ){
                firstComponent = component;
                break;
            }
        }

        assert firstComponent != null;
        AbstractComponent lastComponent = null;

        // find the last component in that same block (if any)
        Block parentBlock = (Block)firstComponent.getParent();
        selectedComponents = parentBlock.getSelected();
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Block ||
                component instanceof TaskRow ){
                lastComponent = component;
            }
        }

        if( lastComponent == firstComponent )
            lastComponent = null;

        // if only a Loop was selected, add the MeasureBlock inside it
        if( firstComponent instanceof Loop &&
            lastComponent == null ){
            Loop loop = (Loop)firstComponent;
            // steal the components inside the loop and add them to
            // the MeasureBlock
            measureBlock.takeComponents( loop );
            loop.add( measureBlock );
            loop.setComputeAggregatesGroup( measureBlock.getTaskGroup() );
        }
        // a single component was selected that isn't a Loop so simply
        // add it inside the MeasureBlock
        else if( lastComponent == null ){
            int insertPosition = parentBlock.findPosition( firstComponent );
            firstComponent.detach();
            measureBlock.add( firstComponent );
            parentBlock.insertAt( measureBlock, insertPosition );
        }
        // a series of components residing in the same block are
        // selected so add all of them inside the MeasureBlock
        else{
            int startPosition = parentBlock.findPosition( firstComponent );
            int endPosition = parentBlock.findPosition( lastComponent );
            for( int i = startPosition; i <= endPosition; i++ ){
                AbstractComponent component =
                    parentBlock.componentAt( startPosition );
                component.detach();
                measureBlock.add( component );
            }
            parentBlock.insertAt( measureBlock, startPosition );
        }
        setAllSelected( false );
        measureBlock.setSelected( true );
        measureDialog.updateState();
        updateState();
        repaint();
    }

    // add a SynchronizeStmt either at the cursor to the previous task
    // row or on the selected tasks in a task row. checks were already
    // made in updateState() to ensure that the SynchronizeStmt could
    // be added to the relevant task row
    public void addSynchronize(){
        // save the undo state
        pushState();

        // add at the cursor
        if( cursor.isVisible() ){
            Block block = (Block)cursor.getParent();
            int cursorPosition = block.findPosition( cursor );
            TaskRow taskRow = (TaskRow)block.componentAt( cursorPosition-1 );
            SynchronizeStmt stmt = new SynchronizeStmt( this );

            // default
            stmt.setTaskGroup( "all tasks" );

            taskRow.add( stmt );
            setAllSelected( false );
            stmt.setSelected( true );
        }
        // add on the selected tasks of a task row
        else{
            RowSelection rowSelection =
                (RowSelection)rowSelections.elementAt( 0 );
            SynchronizeStmt stmt = new SynchronizeStmt( this );
            stmt.setTaskGroup( Utility.getTaskDescription( numTasks, rowSelection.tasks ) );
            setAllSelected( false );
            stmt.setSelected( true );
            rowSelection.taskRow.add( stmt );
        }
        updateState();
        updateSynchronizeDialog();
    }

    // add a WaitStmt either at the cursor to the previous task
    // row or on the selected tasks in a task row. checks were already
    // made in updateState() to ensure that the WaitStmt could
    // be added to the relevant task row
    public void addWait(){
        // save undo state
        pushState();

        if( cursor.isVisible() ){
            Block block = (Block)cursor.getParent();
            int cursorPosition = block.findPosition( cursor );
            TaskRow taskRow = (TaskRow)block.componentAt( cursorPosition-1 );
            WaitStmt stmt = new WaitStmt( this );

            // default
            stmt.setTaskGroup( "all tasks" );

            taskRow.add( stmt );
            setAllSelected( false );
            stmt.setSelected( true );
        }
        else{
            RowSelection rowSelection =
                (RowSelection)rowSelections.elementAt( 0 );
            WaitStmt stmt = new WaitStmt( this );
            stmt.setTaskGroup( Utility.getTaskDescription( numTasks, rowSelection.tasks ) );
            setAllSelected( false );
            stmt.setSelected( true );
            rowSelection.taskRow.add( stmt );
        }
        updateState();
        updateWaitDialog();
    }

    // add a ReduceStmt either at the cursor to the previous task row
    // or on the selected tasks of two consecutive rows. checks were
    // already made in updateState() to ensure that the ReduceStmt could
    // be added to the relevant task rows
    public void addReduce(){
        // save undo state
        pushState();

        // add the reduce to the task row just before the cursor
        if( cursor.isVisible() ){
            Block block = (Block)cursor.getParent();
            int cursorPosition = block.findPosition( cursor );
            TaskRow sourceRow = (TaskRow)block.componentAt( cursorPosition-1 );
            AbstractComponent nextComponent =
                block.componentAt( cursorPosition+1);
            if( nextComponent == null || !(nextComponent instanceof TaskRow ) ){
                TaskRow targetRow = new TaskRow( this );
                block.insertAt( targetRow, cursorPosition );
            }
            moveCursor( block, cursorPosition + 1 );
            ReduceStmt stmt = new ReduceStmt( this );

            // defaults
            stmt.setSourceGroup( "all tasks" );
            stmt.setTargetGroup( "task 0" );

            setAllSelected( false );
            stmt.setSelected( true );
            sourceRow.add( stmt );
        }
        else{
            RowSelection sourceRowSelection =
                (RowSelection)rowSelections.elementAt( 0 );
            RowSelection targetRowSelection =
                (RowSelection)rowSelections.elementAt( 1 );
            ReduceStmt stmt = new ReduceStmt( this );
            stmt.setSourceGroup( Utility.getTaskDescription( numTasks, sourceRowSelection.tasks ) );
            stmt.setTargetGroup( Utility.getTaskDescription( numTasks, targetRowSelection.tasks ) );
            setAllSelected( false );
            stmt.setSelected( true );
            sourceRowSelection.taskRow.add( stmt );
        }
        updateState();
        updateReduceDialog();
    }

    // add a MulticastStmt either at the cursor to the previous task row
    // or on the selected tasks of two consecutive rows. checks were
    // already made in updateState() to ensure that the MulticastStmt could
    // be added to the relevant task rows
    public void addMulticast(){
        // save undo state
        pushState();

        // add the MulticastStmt to the task just before the cursor
        if( cursor.isVisible() ){
            Block block = (Block)cursor.getParent();
            int cursorPosition = block.findPosition( cursor );
            TaskRow sourceRow = (TaskRow)block.componentAt( cursorPosition-1 );
            AbstractComponent nextComponent =
                block.componentAt( cursorPosition+1);
            if( nextComponent == null ||
                !(nextComponent instanceof TaskRow ) ){
                TaskRow targetRow = new TaskRow( this );
                block.insertAt( targetRow, cursorPosition );
            }
            moveCursor( block, cursorPosition + 1 );
            MulticastStmt stmt = new MulticastStmt( this );

            // default source and target task
            stmt.setSourceGroup( "task 0" );
            stmt.setTargetGroup( "all other tasks" );

            setAllSelected( false );
            stmt.setSelected( true );
            sourceRow.add( stmt );
        }

        // add the MulticastStmt to selected tasks in two consecutive
        // rows
        else{
            RowSelection sourceRowSelection =
                (RowSelection)rowSelections.elementAt( 0 );
            RowSelection targetRowSelection =
                (RowSelection)rowSelections.elementAt( 1 );
            MulticastStmt stmt = new MulticastStmt( this );
            stmt.setSourceGroup( Utility.getTaskDescription( numTasks, sourceRowSelection.tasks ) );
            stmt.setTargetGroup( Utility.getTaskDescription( numTasks, targetRowSelection.tasks ) );
            setAllSelected( false );
            stmt.setSelected( true );
            sourceRowSelection.taskRow.add( stmt );
        }
        updateState();
        updateMulticastDialog();
    }

    // add point to point communication between selected tasks in two
    // task rows. although multiple source and target tasks may be
    // used, a single CommunicationStmt is added. checks were already
    // made in updateState() to ensure that the CommunicationStmt
    // could be created on the selected tasks and rows.
    public void addCommunicate(){
        // save undo state
        pushState();

        RowSelection sourceRowSelection =
            (RowSelection)rowSelections.elementAt( 0 );
        RowSelection targetRowSelection =
            (RowSelection)rowSelections.elementAt( 1 );
        CommunicationStmt stmt = new CommunicationStmt( this );
        stmt.setSourceGroup( Utility.getTaskDescription( numTasks, sourceRowSelection.tasks ) );
        stmt.setTargetGroup( Utility.getTaskDescription( numTasks, targetRowSelection.tasks ) );

        // if the selected tasks are in non-consecutive task rows
        // then create a split send-receive CommunicationStmt
        if( sourceRowSelection.taskRow.getID() !=
            targetRowSelection.taskRow.getID() - 1 )
            stmt.setTargetRow( targetRowSelection.taskRow );

        setAllSelected( false );
        stmt.setSelected( true );
        sourceRowSelection.taskRow.add( stmt );

        updateState();
        updateCommunicationDialog();
    }

    // provide a synchronized wrapper around pyInterface.parse
    private synchronized PyObject doParse( String code, String fileName, String start ){
      return (PyObject)pyInterface.parse( code, fileName, start );
    }

    // parse code as type start and return the AST
    public AST parse( String code, String fileName, String start ){
        // parsing can be a slow operation so we set a "busy" mouse
        // pointer while we parse
        java.awt.Cursor prevCursor = container.getCursor();
        container.setCursor( new java.awt.Cursor( java.awt.Cursor.WAIT_CURSOR ) );
        AST codeAST;
        try {
          codeAST = new AST( doParse( code, fileName, start ), null );
        } catch (Exception e) {
          codeAST = null;
        } finally {
          container.setCursor( prevCursor );
        }
        return codeAST;
    }

    // get the comments from the last run of the lexer
    public PyDictionary getComments(){
        return (PyDictionary)pyInterface.get_comments();
    }

    // use codegen_interpret to enumerate a task description using
    // only source task_expr such as in a ComputeStmt
    public Vector enumerateTaskGroup( String sourceDescription ){

        PyObject node = doParse( sourceDescription, "internal", "task_expr" );

        Vector sourceTargets = new Vector();

        try{
            PyTuple pyTuple = (PyTuple)pyInterface.process_node( node );
            PyList pyList = (PyList)pyTuple.__getitem__( 1 );

            for( int i = 0; i < pyList.__len__(); i++ ){
                if( pyList.__finditem__( i ) instanceof PyLong ){
                    PyLong pyLong = (PyLong)(pyList.__finditem__( i ));
                    Integer taskNum = new Integer( (int)pyLong.doubleValue() );
                    sourceTargets.add( new SourceTarget( taskNum.intValue(), 0 ) );
                }
                else if( pyList.__finditem__( i ) instanceof PyInteger ){
                    PyInteger pyInteger = (PyInteger)(pyList.__finditem__( i ));
                    Integer taskNum = new Integer( pyInteger.getValue() );
                    sourceTargets.add( new SourceTarget( taskNum.intValue(), 0 ) );
                }
                else
                    assert false;

            }
        }
        catch( Exception e ){
            System.err.println( "info: unable to enumerate task description \""
				+ sourceDescription + "\"");
            SourceTarget sourceTarget = new SourceTarget( 0, 0 );
            sourceTarget.unknown = true;
            sourceTargets.add( sourceTarget );
        }
        return sourceTargets;
    }

    // enumerate a task description using a source and target
    // task_expr such as in a CommunicationStmt. iterates through the
    // event list of a codegen_interpret processed send_stmt to
    // extract source target tuples
    public Vector enumerateTaskGroup( String sourceDescription,
                                      String targetDescription ){
        // parse the send_stmt
        PyObject node =
            doParse( sourceDescription + " sends a message to " + targetDescription,
                     "internal", "send_stmt" );

        Vector sourceTargets = new Vector();

        try{
            // attempt to process the send_stmt through process_node()
            // in codegen_interpret; this will fail when the task_expr
            // references external variables that are undefined in
            // process_node in which case a single tuple of (0,0) is
            // returned for source and target
	    try{
	        pyInterface.process_node( node );
	    }
	    catch( Exception e ){
	        // If the original was a receive statement, try again
	        // with the source and target reversed.
	        node =
		  doParse( targetDescription + " sends a message to " + sourceDescription,
			   "internal", "send_stmt" );
	        pyInterface.process_node( node );
	    }
            PyList eventLists = (PyList)pyInterface.get_eventlists();
            for( int i = 0; i < eventLists.__len__(); i++ ){
                PyObject eventList = (PyObject)eventLists.__finditem__( i );
                PyList events = (PyList)eventList.__getattr__( "events" );
                for( int j = 0; j < events.__len__(); j++ ){
                    PyObject event = (PyObject)events.__finditem__( j );
                    PyString operation = (PyString)event.__getattr__( "operation" );
                    PyList peers = (PyList)event.__getattr__( "peers" );
                    PyInteger target = (PyInteger)peers.__finditem__( 0 );

                    if( operation.toString().equals( "SEND" ) )
                        sourceTargets.add( new SourceTarget( i, target.getValue() ) );
                }
            }
        }
        catch( Exception e ){
            // failed so return one tuple (i,i) for each source and target
            System.err.println( "info: unable to enumerate task descriptions \""
				+ sourceDescription + "\" and \""
				+ targetDescription + "\"");

            for ( int i = 0; i < numTasks; i++ ) {
              SourceTarget sourceTarget = new SourceTarget( i, i );
              sourceTarget.unknown = true;
              sourceTargets.add( sourceTarget );
            }
        }
        return sourceTargets;
    }

    // added by PB
    public Vector enumerateCollectives(String stmtDescription, String stmtType) {


        // parse the stmt
        PyObject node = doParse( stmtDescription, "internal", stmtType );

        Vector collectives = new Vector();

        try{
            // attempt to process the stmt through process_node()
            // in codegen_interpret
            pyInterface.process_node( node );
            PyList eventLists = (PyList)pyInterface.get_eventlists();
            for( int i = 0; i < eventLists.__len__(); i++ ){
                PyObject eventList = (PyObject)eventLists.__finditem__( i );
                PyList events = (PyList)eventList.__getattr__( "events" );
                for( int j = 0; j < events.__len__(); j++ ){
                    if( events.__getitem__(j) != null) {
                        collectives.add( new Integer(i) );
                    }
                }
            }
        }
        catch( Exception e ){
            System.err.println( "info: unable to enumerate stmt description\n" );
            for ( int i = 0; i < numTasks; i++ ) {
              collectives.add( new Integer(i) );
            }
        }
        return collectives;
    }


    // verify a field by parsing it. field is the code to be
    // verified. type is the start type, e.g: "send_stmt", "expr",
    // etc. scopeVariables should contain the variables defined in the
    // relevant scope
    boolean verifyField( String field, String type, Vector scopeVariables ){

        // "-" is the marker used to indicate no change
        if( field.equals( "-" ) )
            return true;

        // attempt to verify the field by parsing it
        try{
            AST node;
            if( type.equals( "source_task" ) ){
                if( field.toLowerCase().matches( ".*all other task.*" ) )
                    throw new Exception();
                node = parse( field, "internal", "task_expr" );
            }
            else if( type.equals( "target_task" ) ){
                if( field.toLowerCase().matches( ".*all task.*" ) )
                    throw new Exception();
                node = parse( field, "internal", "task_expr" );
            }
            else
                node = parse( field, "internal", type );

            // check that each variable referenced was defined in the scope
            if( scopeVariables == null )
                return true;
            else
                return Utility.verifyScopeVariables( node, scopeVariables );
        }
        // parse failed so return false
        catch( Exception e ){
            return false;
        }
    }

    // show an error dialog with message and "OK" button
    void showErrorDialog( String message ){
        JOptionPane.showMessageDialog( container, message, "Error", JOptionPane.ERROR_MESSAGE );
    }

    // show the command-line options dialog
    void showComesFromsDialog(){
        comesFromsDialog.updateState();
    }

    // adjust the number of tasks displayed
    void setNumTasks( int numTasks ){
        this.numTasks = numTasks;

        // codegen_interpret has to know how many tasks there are
        pyInterface.set_numtasks( numTasks );

        // recursively adjust the number of tasks in all sub-components
        mainBlock.setNumTasks( numTasks );

        repaint();
    }

    int getNumTasks(){
        return numTasks;
    }

    // force all sub-components to resize
    public void resize(){
        mainBlock.setNumTasks( numTasks );
        repaint();
    }

    // return the selected components on a row by row basis
    private Vector getRowSelections( Vector selectedComponents ){
        Vector rowSelections = new Vector();

        // link all selected tasks to their parent task rows
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component
                = (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof Task ){
                TaskRow taskRow = (TaskRow)component.getParent();
                boolean found = false;
                RowSelection rowSelection = null;
                for( int j = 0; j < rowSelections.size(); j++ ){
                    rowSelection = (RowSelection)rowSelections.elementAt( j );
                    if( rowSelection.taskRow == taskRow ){
                        found = true;
                        break;
                    }
                }
                if( !found ){
                    rowSelection = new RowSelection();
                    rowSelection.tasks = new Vector();
                    rowSelection.taskRow = taskRow;
                    rowSelection.block = (Block)taskRow.getParent();
                    rowSelections.add( rowSelection );
                }
                rowSelection.tasks.add( component );
            }
        }
        return rowSelections;
    }

    // bring up the print dialog and print the program
    // (cf. http://www.apl.jhu.edu/~hall/java/Swing-Tutorial/Swing-Tutorial-Printing.html)
    public void print() {
        PrinterJob printJob = PrinterJob.getPrinterJob();
        printJob.setPrintable( this );
        if ( printJob.printDialog() )
          try {
            printJob.print();
          } catch( PrinterException pe ) {
            showErrorDialog( "Failed to print " + pe );
          }
    }

    // start the actual printing of the program
    // (cf. http://www.apl.jhu.edu/~hall/java/Swing-Tutorial/Swing-Tutorial-Printing.html)
    public int print(Graphics g, PageFormat pageFormat, int pageIndex) {
        if( pageIndex > 0 )
            return NO_SUCH_PAGE;
        else {
            // acquire and transform a page object
            Graphics2D g2d = (Graphics2D)g;
            g2d.setClip( null );

            // make the image as large as possible without spilling
            // into the page margins
            Rectangle mainBounds = mainBlock.getGlobalBounds();
            g2d.translate( pageFormat.getImageableX(), pageFormat.getImageableY() );
            double maxScaleX = pageFormat.getImageableWidth() / mainBounds.getWidth();
            double maxScaleY = pageFormat.getImageableHeight() / mainBounds.getHeight();
            double maxScale = maxScaleX < maxScaleY ? maxScaleX : maxScaleY;
            g2d.scale( maxScale, maxScale );
            g2d.translate( -mainBounds.getX(), -mainBounds.getY() );

            // force the entire program to redraw to the page object
            RepaintManager currentManager = RepaintManager.currentManager( this );
            currentManager.setDoubleBufferingEnabled( false );
            setAllSelected( false );
            cursor.setVisible( false );
            paintComponent( g2d );
            paintChildren( g2d );

            // set everything back to normal and return
            currentManager.setDoubleBufferingEnabled( true );
            cursor.setVisible( true );
            mainBlock.align();
            return PAGE_EXISTS;
        }
    }

    // save the program as a file
    void saveAs(){
        if( filePath != null )
            fileChooser.setSelectedFile( new File( filePath ) );

        fileChooser.showSaveDialog( container );
        File file = fileChooser.getSelectedFile();
        if( file != null ){
            filePath = file.getAbsolutePath();
            if( container instanceof JFrame )
                ((JFrame)container).setTitle( "coNCePTuaL GUI: " +
                                              file.getName() );
            save();
        }
    }

    // save the changes of the program to the existing file or
    // equivalent to saveAs() if unsaved
    void save(){
        if( filePath == null ){
            saveAs();
            return;
        }
        try{
            ProgramWriter programWriter = new ProgramWriter();
            programWriter.writeProgram( this, filePath );
            saved = true;
        }
        catch( IOException e ){
            showErrorDialog( "Unable to write file \"" + filePath + "\"" );
        }
    }

    // equivalent to save() but keeps trying until successful or canceled;
    // returns true if the program should exit, false if not
    boolean saveOnExit(){
        while ( !saved ) {
            if( filePath == null ){
                saveAs();
                if( filePath == null )
                    break;
                fileChooser.setSelectedFile( null );
                filePath = null;
            }
            else{
                try{
                    ProgramWriter programWriter = new ProgramWriter();
                    programWriter.writeProgram( this, filePath );
                    saved = true;
                }
                catch( IOException e ){
                    showErrorDialog( "Unable to write file \"" + filePath + "\"" );
                    filePath = null;
                }
            }
        }
        return saved;
    }

    // present the open dialog for opening a file
    void open(){
        fileChooser.showOpenDialog( container );
        File file = fileChooser.getSelectedFile();

        if( file != null ){
            open( file.getAbsolutePath() );
            if( container instanceof JFrame )
                ((JFrame)container).setTitle( "coNCePTuaL GUI: " +
                                              file.getName() );
        }
    }

    // open the file specified by filePath
    void open( String filePath ){
        ProgramReader programReader = new ProgramReader();
        try{
            this.filePath = null;
            programReader.readProgramFile( filePath, this );
            this.filePath = filePath;
            updateState();
            repaint();
        }
        catch( IOException e ){
            showErrorDialog( "Unable to read file \"" + filePath + "\"" );
        }
    }

    // update gui with string from text editor when run inside eclipse
    public void openWithString( String progString ) {
        ProgramReader programReader = new ProgramReader();
        try{

            programReader.readProgramString( progString, this );

            updateState();
            repaint();
        }
        catch( IOException e ){
            System.err.println( "internal error: unable to read program string" );
        }
    }

    // normalize the program by saving to a string then opening
    // program in string
    void normalize(){
        // save undo state
        pushState();

        try{
            ProgramWriter programWriter = new ProgramWriter();
            String buffer = programWriter.writeProgram( this, null );
            ProgramReader programReader = new ProgramReader();
            programReader.readProgramString( buffer, this );
            updateState();
            repaint();
        }
        catch( IOException e ){
            showErrorDialog( "Internal error: Unable to normalize the program" );
        }
    }

    // return the program string for updating text editor
    public String getProgramString() {
        // copy these lines from save()
        ProgramWriter programWriter = new ProgramWriter();
        try {
            progString = programWriter.writeProgram( this, filePath );
        } catch (IOException e) {
            return null;
        }
        return progString;
    }

    // create a new program consisting of two empty task rows
    // first is true if this is creating a program for the first time
    public void doNew( boolean first ){
        if( !first ){
            // save undo state
            pushState();
            clear();

            // Added by SDP: Reset the frame and save state.
            if( container instanceof JFrame )
                ((JFrame)container).setTitle( "coNCePTuaL GUI: <unsaved>" );
            saved = true;
            fileChooser.setSelectedFile( new File ( "" ) );
            filePath = null;
        }
        CommunicationStmt.resetDefaults();
        cursor.detach();
        /*
         * Removed by SDP: Adding two rows seems to have caused the
         * Loop button to crash after inserting a Synchronize between
         * the two rows.
         */
        //mainBlock.add( new TaskRow( this ) );
        //mainBlock.add( new TaskRow( this ) );
        mainBlock.add( cursor );
        filePath = null;

        updateState();
    }

    // get the cursor associated with this program
    public Cursor findCursor(){
        return cursor;
    }

    // save the selection state so more components can be added to it
    // in shift-dragging a selection
    public void setAlreadySelected(){
        alreadySelected = getAllSelected( new Vector() );
    }

    // cut the selected components, placing them into the paste buffer
    public void cutSelection(){
        // save undo state
        pushState();

        pasteComponents.clear();
        Vector selectedComponents = getAllSelected( new Vector() );

        // if the stmts are all in the same row, they may be cut so
        // that they can be pasted onto tasks
        boolean sameRowStmts = sameRowStmts( selectedComponents );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );

            // the component may have already been deselected
            // if it was inside a block
            if( !component.isSelected() )
                continue;

            if( component instanceof Block ){
                // deselect all components in the block so they won't
                // be cut twice
                component.setAllSelected( false );
                component.detach();
                pasteComponents.add( component );
            }
            else if( component instanceof TaskRow ){
                component.detach();
                pasteComponents.add( component );
            }
            else if( sameRowStmts && component instanceof Stmt ){
                component.detach();
                pasteComponents.add( component );
            }

        }
        setAllSelected( false );
        updateState();
        repaint();
    }

    // copy the selected components into the pasteComponents buffer
    public void copySelection(){
        pasteComponents.clear();
        Vector selectedComponents = getAllSelected( new Vector() );

        // if the stmts are all in the same row, they may be copied so
        // that they can be pasted onto tasks
        boolean sameRowStmts = sameRowStmts( selectedComponents );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );

            // the component may have already been deselected
            // if it was inside a block
            if( !component.isSelected() )
                continue;

            if( component instanceof Block ){
                component.setAllSelected( false );
                try{
                    pasteComponents.add( component.clone() );
                }
                catch( CloneNotSupportedException exception ){
                    System.err.println( "internal error: unable to clone component\n" );
                }
            }
            else if( component instanceof TaskRow ){
                try{
                    pasteComponents.add( component.clone() );
                }
                catch( CloneNotSupportedException exception ){
                    System.err.println( "internal error: unable to clone component\n" );
                }
            }
            else if( sameRowStmts && component instanceof Stmt ){
                try{
                    pasteComponents.add( component.clone() );
                }
                catch( CloneNotSupportedException exception ){
                    System.err.println( "internal error: unable to clone component\n" );
                }
            }
        }
        setAllSelected( false );
        updateState();
        repaint();
    }

    // paste the components in pasteComponents into the program
    // depending on the current selection state and contents of
    // pasteComponents
    public void paste(){
        // save undo state
        pushState();

        Vector selectedComponents = getAllSelected( new Vector() );

        // if only a task row is selected and pasteComponents contains
        // only stmts, all of which are from a single row, then allow
        // the stmts to be pasted onto the row
        if( selectedComponents.size() == 1 &&
            selectedComponents.elementAt( 0 ) instanceof TaskRow &&
            sameRowStmts( pasteComponents ) ){
            TaskRow taskRow = (TaskRow)selectedComponents.elementAt( 0 );
            Block parentBlock = (Block)taskRow.getParent();

            // if the next row is not a task row, then add one
            if( !(parentBlock.componentAt( taskRow.getID() + 1 ) instanceof
                  TaskRow) )
                parentBlock.insertAt( new TaskRow( this ), taskRow.getID()+1 );

            // paste the stmts onto the row
            for( int i = 0; i < pasteComponents.size(); i++ ){
                Stmt stmt = (Stmt)pasteComponents.elementAt( i );
                try{
                    taskRow.add( (Stmt)stmt.clone() );
                }
                catch( CloneNotSupportedException exception ){
                    System.err.println( "internal error: unable to clone component\n" );
                }
            }
        }

        // if tasks are selected and the stmts can be pasted onto the
        // tasks
        else if( enableTaskPasteStmts( selectedComponents, pasteComponents ) )
            taskPasteStmts( selectedComponents, pasteComponents );

        // components to be pasted are components other than
        // statements so paste them in at the cursor
        else{
            Block block = (Block)cursor.getParent();
            int insertPosition = block.findPosition( cursor );
            for( int i = 0; i < pasteComponents.size(); i++ ){
                AbstractComponent component =
                    (AbstractComponent)pasteComponents.elementAt( i );
                try{
                    block.insertAt( (AbstractComponent)component.clone(),
                                    insertPosition++ );
                }
                catch( CloneNotSupportedException exception ){
                    System.err.println( "internal error: unable to clone component\n" );
                }
            }
        }
        setAllSelected( false );
        updateState();
        repaint();
    }

    public void setMainMenu( MainMenu mainMenu ){
        this.mainMenu = mainMenu;
    }

    // undo by popping the last undo state off the stack
    public void undo(){
        popState();
        setAllSelected( false );
        updateState();
    }

    // push the current undo state onto the stack
    public void pushState(){
        try{
            ProgramState programState = new ProgramState();
            programState.comesFroms = (Vector)comesFroms.clone();
            programState.mainBlock = (Block)mainBlock.clone();
            programStates.add( programState );
            saved = false;
        }
        catch( CloneNotSupportedException exception ){
            System.err.println( "internal error: unable to clone component\n" );
        }
    }

    // pop the undo state from the stack
    public void popState(){
        if( programStates.size() == 0 )
            return;
        ProgramState lastState = (ProgramState)programStates.lastElement();
        cursor.detach();
        removeAll();
        mainBlock = lastState.mainBlock;
        add( mainBlock );
        cursor = mainBlock.findCursor();
        comesFroms = lastState.comesFroms;
        programStates.remove( lastState );
        updateState();
        repaint();
    }

    // update the dialogPane to display help contents depending on the
    // current program state as determined by which toolbar buttons
    // are active
    public void updateHelpPane(){
        JEditorPane editorPane = new JEditorPane();
        editorPane.setEditable( false );

        String text = "To enable:\n";

        if( !toolBar.isEnabledAddRow() )
            text += "  -Add Row: deselect all components.\n";

        if( !toolBar.isEnabledDelete() )
            text += "  -Delete: select one or more components.\n";

        if( !toolBar.isEnabledLoop() )
            text += "  -Loop: select one or more task rows or blocks.\n";

        if( !toolBar.isEnabledMeasure() )
            text += "  -Measure: select one or more task rows or blocks.\n";

        if( !toolBar.isEnabledCompute() )
            text += "  -Compute: select one or more tasks.\n";

        if( !toolBar.isEnabledCommunicate() )
            text += "  -Communicate: select tasks in two task rows.\n";

        if( !toolBar.isEnabledWait() )
            text += "  -Wait: move the cursor after an empty task row or select two or more tasks in it.\n";

        if( !toolBar.isEnabledExtend() )
            text += "  -Extend: select one or more communication or compute statements in the same task row.\n";

        if( !toolBar.isEnabledSynchronize() )
            text += "  -Synchronize: move the cursor after an empty task row or select two or more tasks in it.\n";

        if( !toolBar.isEnabledReduce() )
            text += "  -Reduce: move the cursor after an empty task row or select tasks in two consecutive task rows.\n";

        if( !toolBar.isEnabledMulticast() )
            text += "  -Multicast: move the cursor after an empty task row or select tasks in two consecutive task rows.\n";

        // force the text to the top
        for( int i = 0; i < 50; i++ )
            text += "\n";

        editorPane.setText( text );
        dialogPane.add( editorPane );
    }

    // clear the already selected components
    // alreadySelected is used when shift-dragging a selection
    public void clearAlreadySelected(){
        alreadySelected = new Vector();
    }

    // return true if components contains only stmts, all of which are
    // in the same row. used for determining if stmts in components
    // can be pasted onto tasks or a task row
    public boolean sameRowStmts( Vector components ){
        boolean sameRowStmts = true;
        TaskRow stmtParentRow = null;

        if( components.size() == 0 )
            sameRowStmts = false;

        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)components.elementAt( i );
            if( component instanceof Stmt ){
                if( stmtParentRow == null )
                    stmtParentRow = ((Stmt)component).getTaskRow();
                else if( stmtParentRow != ((Stmt)component).getTaskRow() ){
                    sameRowStmts = false;
                    break;
                }
            }
            else{
                sameRowStmts = false;
                break;
            }
        }
        return sameRowStmts;
    }

    // show the extend communication/computation pattern dialog
    public void showExtendDialog(){
        extendDialog.updateState();
    }

    // extend the selected communication/computation pattern,
    // repeating it every repeat tasks
    public void extendPattern( int repeat ){
        Vector selectedComponents = getAllSelected( new Vector() );
        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );

            // CommunicationStmt
            if( component instanceof CommunicationStmt ){
                CommunicationStmt stmt = (CommunicationStmt)component;

                TaskGroup taskGroup = stmt.getTaskGroup();

                // extract the source and target task number
                int sourceTask = Utility.getTask( taskGroup.toCodeSource() );
                int targetTask = Utility.getTask( taskGroup.toCodeTarget() );

                int s = sourceTask % repeat;
                int t = targetTask - sourceTask;
                if( repeat > 1 )
                    taskGroup.setSource( "tasks t such that t mod " +
                                         repeat + "=" + s );
                else
                    taskGroup.setSource( "all tasks t" );

                if( t == 0 )
                    taskGroup.setTarget( "tasks t" );
                else if( t > 0 )
                    taskGroup.setTarget( "tasks t+" + t );
                else
                    taskGroup.setTarget( "tasks t-" + -t );
            }
            // ComputeStmt
            else if( component instanceof ComputeStmt ){
                ComputeStmt stmt = (ComputeStmt)component;

                TaskGroup taskGroup = stmt.getTaskGroup();

                int task = Utility.getTask( taskGroup.toCodeSource() );
                int s = task % repeat;
                if( repeat > 1 )
                    taskGroup.setSource( "tasks t such that t mod " +
                                         repeat + "=" + s );
                else
                    taskGroup.setSource( "all tasks t" );
            }
        }
    }

    // determine if the toolbar button "Extend" should be enabled
    private boolean enableExtend( Vector selectedComponents ){
        if( selectedComponents.size() == 0 )
            return false;

        int type = 0;

        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );
            if( component instanceof CommunicationStmt && type < 2 ){
                type = 1;
                CommunicationStmt stmt = (CommunicationStmt)component;
                TaskGroup taskGroup = stmt.getTaskGroup();

                if( Utility.getTask( taskGroup.toCodeSource() ) < 0 )
                    return false;

                if( Utility.getTask( taskGroup.toCodeTarget() ) < 0 )
                    return false;
            }
            else if( component instanceof ComputeStmt && type == 0 ||
                     type == 2 ){
                type = 2;
                ComputeStmt stmt = (ComputeStmt)component;
                TaskGroup taskGroup = stmt.getTaskGroup();

                if( Utility.getTask( taskGroup.toCodeSource() ) < 0 )
                    return false;
            }
            else
                return false;
        }
        return true;
    }

    public void setScrollPane( AutoScrollPane scrollPane ){
        this.scrollPane = scrollPane;
        mainBlock.setScrollPane( scrollPane );
    }

    public AutoScrollPane getScrollPane(){
        return scrollPane;
    }

    // determine if the stmts in pasteComponents can be pasted onto
    // the tasks in selectedComponents
    public boolean enableTaskPasteStmts( Vector selectedComponents,
                                         Vector pasteComponents ){

        if( !sameRowStmts( pasteComponents ) )
            return false;

        if( selectedComponents.size() == 0 )
            return false;

        for( int i = 0; i < selectedComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)selectedComponents.elementAt( i );

            if( !(component instanceof Task) )
                return false;
        }

        for( int i = 0; i < pasteComponents.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)pasteComponents.elementAt( i );


            if( component instanceof CommunicationStmt ){
                CommunicationStmt stmt = (CommunicationStmt)component;
                TaskGroup taskGroup = stmt.getTaskGroup();

                if( Utility.getTask( taskGroup.toCodeSource() ) < 0 )
                    return false;

                if( Utility.getTask( taskGroup.toCodeTarget() ) < 0 )
                    return false;
            }
            else if( component instanceof ComputeStmt ){
                ComputeStmt stmt = (ComputeStmt)component;
                TaskGroup taskGroup = stmt.getTaskGroup();
                if( Utility.getTask( taskGroup.toCodeSource() ) < 0 )
                    return false;
            }
            else
                return false;
        }

        return true;
    }

    // paste the stmts in pasteComponents onto the selected tasks in
    // selectedComponents. should be called only if
    // enableTaskPasteStmts( selectedComponents, pasteComponents )
    // returned true
    public void taskPasteStmts( Vector selectedComponents,
                                Vector pasteComponents ){

        int originalStart = 0;
        for( int i = 0; i < pasteComponents.size(); i++ ){

            CommunicationStmt stmt =
                (CommunicationStmt)pasteComponents.elementAt( i );

            TaskGroup taskGroup = stmt.getTaskGroup();

            int originalSource = Utility.getTask( taskGroup.toCodeSource() );
            int originalTarget = Utility.getTask( taskGroup.toCodeTarget() );

            if( i == 0 )
                originalStart = originalSource;

            for( int j = 0; j < selectedComponents.size(); j++ ){
                Task task = (Task)selectedComponents.elementAt( j );

                TaskRow taskRow = (TaskRow)task.getParent();
                try{
                    CommunicationStmt newStmt = (CommunicationStmt)stmt.clone();

                    int source = task.getID() + originalSource - originalStart;

                    newStmt.setSourceGroup( "task " + source );
                    int targetTask = originalTarget +
                        source - originalSource;
                    newStmt.setTargetGroup( "task " + targetTask );
                    Block parentBlock = (Block)taskRow.getParent();
                    if( !(parentBlock.componentAt( taskRow.getID() + 1 )
                          instanceof TaskRow) )
                        parentBlock.insertAt( new TaskRow( this ),
                                              taskRow.getID()+1 );
                    taskRow.add( newStmt );
                }
                catch( CloneNotSupportedException exception ){
                    System.err.println( "internal error: failed to clone CommunicationStmt\n" );
                }
            }
        }
    }

    // the following methods get and set the comments that appear at
    // the very start or end of the program which could not be
    // attached to any other component

    public void setStartComments( String startComments ){
        this.startComments = startComments;
    }

    public void setEndComments( String endComments ){
        this.endComments = endComments;
    }

    public String getStartComments(){
        return startComments;
    }

    public String getEndComments(){
        return endComments;
    }

    // exit the GUI asking to save any unsaved changes
    public void exit(){
        if( saved || !haveFileAccess() )
            System.exit( 0 );
        else
            new ExitDialog( container, this, true );
    }

    // the following methods implement the KeyListener interface
    // and are triggered when the focus is in the Program component

    // triggered whenever a key is pressed and released
    public void keyTyped( KeyEvent event ){
        switch( event.getKeyChar() ){
        // link the delete key with the same action as the "Delete"
        // toolbar button
        case KeyEvent.VK_DELETE:
            deleteSelectedComponents();
            break;
        }
    }

    // triggered whenever a key is pressed
    public void keyPressed( KeyEvent event ){

    }

    // triggered whenever a key is released
    public void keyReleased( KeyEvent event ){

    }

    // returns true if firstComponent appears in the program before
    // secondComponent - used for determining if a CommunicationStmt
    // can be created directed from firstComponent to secondComponent
    public boolean appearsAfter( AbstractComponent firstComponent,
                                 AbstractComponent secondComponent ){
        AbstractComponent a = firstComponent;
        AbstractComponent b = secondComponent;

        // translate firstComponent and secondComponent into parent
        // TaskRow if they are stmts or tasks

        if( firstComponent instanceof Task )
            a = (AbstractComponent)firstComponent.getParent();
        else if( firstComponent instanceof Stmt )
            a = ((Stmt)firstComponent).getTaskRow();

        if( firstComponent instanceof Task )
            b = (AbstractComponent)secondComponent.getParent();
        else if( secondComponent instanceof Stmt )
            b = ((Stmt)secondComponent).getTaskRow();

            return appearsAfter( mainBlock, a, b );
    }

    // same as the above, but used internally, uses currentBlock to
    // recursively search through the program
    private boolean appearsAfter( Block currentBlock,
                                  AbstractComponent firstComponent,
                                  AbstractComponent secondComponent ){
        currentBlock.traverseReset();
        AbstractComponent component;
        while( (component = currentBlock.traverseNext()) != null ){
            if( component instanceof Block ){
                if( appearsAfter( (Block)component,
                                  firstComponent,
                                  secondComponent ) )
                    return true;
            }
            else if( firstComponent != null ){
                if( firstComponent == component )
                    firstComponent = null;
            }
            else if( secondComponent == component )
                return true;
        }
        return false;
    }

    public void clearDialogPane(){
        dialogPane.setEmpty( true );
    }

    // return a vector containing all tasks
    public Vector getAllTasks(){
        Vector allTasks = new Vector();
        for( int i = 0; i < numTasks; i++ )
            allTasks.add( new Integer( i ) );
        return allTasks;
    }

    // return the main menu
    public MainMenu getMainMenu() {
        return mainMenu;
    }

    // Say if we have access to the filesystem.
    public boolean haveFileAccess() {
        return fileChooser != null;
    }

    // Say whether we should include a File menu.
    public boolean useFileMenu() {
        if( !haveFileAccess() )
            // Don't include a File menu if we're denied access to the
            // filesystem.
            return false;
        if( container instanceof Frame && !( container instanceof JFrame ) )
            // Don't include a File menu when running from Eclipse.
            return false;
        return true;
    }
}
