/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: block
 *
 * By Nick Moss <nickm@lanl.gov>
 * Improved and corrected by Paul Beinfest <beinfest@lanl.gov> 
 *
 * A Block is a container holding a sequence of one or more
 * AbstractComponents such as TaskRow's or other Block's. The
 * statements that make up a coNCePTuaL program are stored in a
 * TaskRow so a Block is somewhat analogous to a series of
 * simple_stmts enclosed in curly braces.
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

public class Block extends AbstractComponent {

    // a vector containing the sub-components
    // in the order that they appear in the block
    protected Vector components;
    
    // blank space at the left and right of the block
    private static final int PADDING_X = 10;
    
    // blank space at the top and bottom of the block
    private static final int PADDING_Y = 15;

    // the amount of vertical blank space between each component
    public static final int COMPONENT_SPACING = 34;

    // the height of the block when it contains no components
    private static final int EMPTY_HEIGHT = 25;

    // the spacing between a component and the cursor
    private static final int CURSOR_SPACING = 15;

    // the program that this block is part of
    private Program program;
    
    // the current component position in calling traverseNext()
    private int traverseCursor;
    
    // the amount of extra top spacing a sub-class of Block requires
    // e.g: MeasureBlock requires a variable amount of space at the
    // top for each expression measured
    private int topSpacing;

    // dragStart is in local coordinates
    // set when a mouseDragged event is received
    Point dragStart;

    // construct a new Block
    public Block( Program program ){    
        components = new Vector();
        setBounds( 0, 0, 0, 0 );
        this.program = program;
        traverseCursor = 0;
        topSpacing = 10;
        dragStart = new Point();
        
        // add scroll pane as a listener to mouse events
        // originating in the block
        addMouseListener( program.getScrollPane() );
        addMouseMotionListener( program.getScrollPane() );
    }
    
    // add a component to the block
    public void add( AbstractComponent component ){
        components.add( component );
        super.add( component );
        align();
    }

    // remove component from the block
    public void remove( AbstractComponent component ){
        // if the component to be removed is a TaskRow then the
        // communication edges or collectives directed to it from the
        // TaskRow in the position before it must be deleted
        if( component instanceof TaskRow ){
            int position = findPosition( component );
            AbstractComponent previousRow = componentAt( position - 1 );
            if( previousRow != null && previousRow instanceof TaskRow )
                ((TaskRow)previousRow).clearCommunicationStmts();
        }
        components.remove( component );
        super.remove( component );
        align();
    }

    // remove all components from the block
    public void clear(){
        super.removeAll();
        components.clear();
    }

    // this method should be called internally whenever a
    // component is added or removed from the block.
    // it does the following: 
    //   -resizes the program block width
    //   -re-assigns ID's
    //   -re-aligns the components vertically
    //   -re-aligns the components horizontally with centering
    protected void align(){

        // determine the width of the block 
        // by the width of the widest component

        // this is the default width of a block with no components
        int maxWidth = program.getNumTasks() * 
            (Task.TASK_SIZE + TaskRow.TASK_SPACING) + TaskRow.PADDING_X*2;

        // find the widest component
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );

            Rectangle componentBounds = component.getBounds();
            if( !(component instanceof Cursor) 
                && componentBounds.width > maxWidth )
                maxWidth = componentBounds.width;
        }
        
        // now align the components vertically and horizontally
        int blockWidth = maxWidth + PADDING_X * 2;
        int nextY = topSpacing + PADDING_Y;
        Rectangle blockBounds = getBounds();
        Cursor cursor = null;
        Rectangle cursorBounds = null;
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            AbstractComponent nextComponent = null;
            if( i < components.size() - 1 ){
                nextComponent = 
                    (AbstractComponent)components.elementAt( i + 1 );
            }
            
            // component width and height should already be set
            // only need to determine x and y relative to block
            // with centering against blockWidth
            Rectangle componentBounds = component.getBounds();
            component.setBounds( (blockWidth - componentBounds.width)/2,
                                 nextY,
                                 componentBounds.width,
                                 componentBounds.height );
            if( component instanceof Cursor ){
                cursor = (Cursor)component;
                cursorBounds = cursor.getBounds();
                nextY += (COMPONENT_SPACING + cursorBounds.height)/2;
            }
            else{
                if( nextComponent != null && 
                    nextComponent instanceof Cursor ){
                    cursorBounds = nextComponent.getBounds();
                    nextY += componentBounds.height + 
                        (COMPONENT_SPACING - cursorBounds.height)/2;
                }
                else
                    nextY += componentBounds.height + COMPONENT_SPACING;
                component.setID( i );
            }
        }

        int height = nextY;
        if( height < topSpacing + PADDING_Y + EMPTY_HEIGHT )
            height = topSpacing + PADDING_Y + EMPTY_HEIGHT;

        setBounds( blockBounds.x, blockBounds.y, blockWidth, height );
        
        // set the cursor width to the width of the block
        if( cursor != null ){
            Rectangle bounds = cursor.getBounds();
            bounds.width = maxWidth;
            cursor.setBounds( (blockWidth - bounds.width)/2, bounds.y, 
                              bounds.width, bounds.height );
        }

        // parent block now needs to be re-aligned too
        AbstractComponent parent = (AbstractComponent)getParent();
        if( parent instanceof Block )
            ((Block)parent).align();
    }

    // delegate method to recursively paint all stmts in the block
    public void paintStmts( Graphics graphics ){
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            component.paintStmts( graphics );
        }
    }
    
    // return component at index (skipping the cursor) or null if
    // index is invalid
    public AbstractComponent componentAt( int index ){
        if( index < 0 || index >= components.size() )
            return null;
        else if( (AbstractComponent)components.elementAt( index ) 
                 instanceof Cursor ){
            if( index == components.size() - 1 )
                return null;
            else
                return (AbstractComponent)components.elementAt( index + 1 );
        }
        else
            return (AbstractComponent)components.elementAt( index );
    }
    
    // find component position within the current block 
    // that the point (x,y), in local coordinates, corresponds to
    // returns -1 if the point is not contained in the component
    // skips the cursor in returing the index
    public int findPosition( int x, int y ){
        Rectangle bounds = getBounds();
        if( x > bounds.width || y > bounds.height )
            return -1;

        int j = 0;
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            Rectangle componentBounds = component.getBounds();
            if( componentBounds.y > y )
                break;
            if( !(component instanceof Cursor ) )
                j++;
        }
        return j;
    }

    // find the relative position (index) of the component
    // returns -1 if the component wasn't found in the block
    public int findPosition( AbstractComponent component ){
        return components.indexOf( component );
    }


    // insert the component at the specified index
    void insertAt( AbstractComponent component, int index ){
        components.insertElementAt( component, index );
        super.add( component );
        align();
    }

    // handle a mouse click
    public void mousePressed( MouseEvent mouseEvent ){
        dragStart.x = mouseEvent.getX();
        dragStart.y = mouseEvent.getY();

        // if shift or control is down, save the components already selected
        // else clear selection
        if( mouseEvent.isShiftDown() || mouseEvent.isControlDown() )
            program.setAlreadySelected();
        else
            program.clearAlreadySelected();
    }

    // handle a mouseDragged event
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

        // translate to global coordinates
        Point globalXY = toGlobalPoint( dragRect.x, dragRect.y );
        Rectangle globalDragRect = dragRect;
        globalDragRect.x = globalXY.x;
        globalDragRect.y = globalXY.y;
        
        // drag selection marquee
        program.dragSelection( globalDragRect );
    }

    // handle a mouseClicked event
    public void mouseClicked( MouseEvent mouseEvent ){
        int x = mouseEvent.getX();
        int y = mouseEvent.getY();

        // determine which statements need to be selected
        // only move the cursor if no statements were selected
        if( !clickSelectStmts( mouseEvent.isShiftDown() ||
                               mouseEvent.isControlDown(), x, y ) ){
            Cursor cursor = program.findCursor();
            if( !mouseEvent.isShiftDown() && !mouseEvent.isControlDown() ){
                if( cursor.isVisible() ){
                    int position = findPosition( x, y );
                    if( position >= 0 )
                        program.moveCursor( this, position );
                }
                else{
                    program.setAllSelected( false );
                    program.updateState();
                }
            }
        }
        else
            repaint();
    }

    // process a mouseReleaesed event
    // clear the selection marquee
    public void mouseReleased( MouseEvent mouseEvent ){
        program.dragSelection( null );
    }

    // recursively set the selection state of all sub-components
    public void setSelectAll( boolean flag ){
        setSelected( flag );
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            component.setSelectAll( flag );
        }
    }

    // recursively select all sub-components within the marquee
    public void selectRegion( Rectangle marquee ){
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            component.selectRegion( marquee );
        }
        super.selectRegion( marquee );
    }
    
    // the traverseXXX functions are primarily used by ProgramWriter
    // to traverse through all the components and write them to a file
    
    // reset the cursor to the first component
    public void traverseReset(){
        traverseCursor = 0;
    }
    
    // return the component at the traversal cursor
    // and advance to the next position
    // returns null when the end of the components vector has been reached
    public AbstractComponent traverseNext(){
        if( traverseCursor < components.size() ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( traverseCursor );
            traverseCursor++;
            return component;
        }
        else
            return null;
    }

    // add a SynchronizeStmt to the last TaskRow in the Block
    // creates and appends a TaskRow if needed
    public TaskRow add( SynchronizeStmt stmt ){
        AbstractComponent lastComponent = componentAt( numComponents() - 1 );

        // attempt to find an available TaskRow
        if( lastComponent != null && lastComponent instanceof TaskRow && 
            !((TaskRow)lastComponent).hasStmts() ){
            ((TaskRow)lastComponent).add( stmt );
            return (TaskRow)lastComponent;
        }
        else{
            // no available TaskRow was found so append one
            TaskRow row = new TaskRow( program );
            row.add( stmt );
            add( row );
            return row;
        }
    }

    // add a WaitStmt to the last TaskRow in the Block
    // creates and appends a TaskRow if needed
    public TaskRow add( WaitStmt stmt ){
        AbstractComponent lastComponent = componentAt( numComponents() - 1 );
        if( lastComponent != null && lastComponent instanceof TaskRow && 
            !((TaskRow)lastComponent).hasStmts() ){
            ((TaskRow)lastComponent).add( stmt );
            return (TaskRow)lastComponent;
        }
        else{
            TaskRow row = new TaskRow( program );
            row.add( stmt );
            add( row );
            return row;
        }
    }

    // add an OtherStmt to the last TaskRow in the Block
    // creates and appends a TaskRow if needed
    public TaskRow add( OtherStmt stmt ){
        AbstractComponent lastComponent = componentAt( numComponents() - 1 );
        if( lastComponent != null && lastComponent instanceof TaskRow && 
            !((TaskRow)lastComponent).hasStmts() ){
            ((TaskRow)lastComponent).add( stmt );
            return (TaskRow)lastComponent;
        }
        else{
            TaskRow row = new TaskRow( program );
            row.add( stmt );
            add( row );
            return row;
        }
    }

    // add a ReduceStmt to the last TaskRow in the Block
    // creates and appends up to two TaskRows as needed
    public TaskRow add( ReduceStmt stmt ){
        
        AbstractComponent lastComponent = null;

        if( components.size() > 0 )
            lastComponent = 
                (AbstractComponent)components.elementAt( components.size() - 1 );

        TaskRow taskRow = null;

        if( lastComponent != null && 
            lastComponent instanceof TaskRow &&
            !((TaskRow)lastComponent).hasStmts() )
            taskRow = (TaskRow)lastComponent;
        else{
            taskRow = new TaskRow( program );
            add( taskRow );
        }
        TaskRow nextRow = new TaskRow( program );
        add( nextRow );
        taskRow.add( stmt );
        return taskRow;
    }

    // add a MulticastStmt to the last TaskRow in the Block
    // creates and appends a new TaskRow if needed
    public TaskRow add( MulticastStmt stmt ){
        
        AbstractComponent lastComponent = null;
        
        if( components.size() > 0 )
            lastComponent = 
                (AbstractComponent)components.elementAt( components.size() - 1 );
        
        TaskRow taskRow = null;
        
        if( lastComponent != null && 
            lastComponent instanceof TaskRow &&
            !((TaskRow)lastComponent).hasStmts() )
            taskRow = (TaskRow)lastComponent;
        else{
            taskRow = new TaskRow( program );
            add( taskRow );
        }
        TaskRow nextRow = new TaskRow( program );
        add( nextRow );
        taskRow.add( stmt );
        return taskRow;
    }
    
    // searching upward in the block ...
    // add stmt which is a CommunicationStmt or ComputeStmt
    // to the first available task row that can accomodate it
    // ... one or two task rows may need to be created in the process
    public TaskRow add( Stmt stmt ){
        TaskGroup taskGroup = null;
        if( stmt instanceof ComputeStmt )
            taskGroup = ((ComputeStmt)stmt).getTaskGroup();
        else if( stmt instanceof CommunicationStmt )
            taskGroup = ((CommunicationStmt)stmt).getTaskGroup();
        else
            assert false;

        // get a vector of source and targets
        Vector sourceTargets = taskGroup.enumerate();

        // add source tasks to requiredTasks
        Vector requiredTasks = new Vector();
        for( int i = 0; i < sourceTargets.size(); i++ ){
            SourceTarget sourceTarget = 
                (SourceTarget)sourceTargets.elementAt( i );
            requiredTasks.add( new Integer( sourceTarget.source ) );
        }

        // this loop terminates with the position i at which
        // to add the statement
        // and adds any needed task rows at the appropriate position
        int i = components.size() - 1;

        // searching upward, lastOK is the last available task row
        // that could accomodate the stmt
        int lastOK = -1;
        Vector it = null;
        while( i >= 0 ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );

            // check if this task row is available
            if( component instanceof TaskRow ){
                TaskRow taskRow = (TaskRow)component;
                Vector allocatedTasks = taskRow.getAllocatedTasks();
                
                it = Utility.intersection( requiredTasks, 
                                                  allocatedTasks );
                if( it.size() == 0 && !taskRow.hasCollectives() ){
                    // this task row was available but continue
                    // searching upward
                    if( i > 0 )
                        lastOK = i;
                    // we have reached the top-most task row
                    else
                        break;
                }
                // this task row is not available so stop searching
                // and use the last available task row
                else if( lastOK > 0 ){
                    i = lastOK;
                    break;
                }
                // we have reached to top-most task row
                // without finding any available task rows
                // so they will need to be appended to the block
                else{
                    i = -1;
                    break;
                }
            }
            i--;
        }
        
        TaskRow destRow = null;
        // if no available task row was found
        if( i < 0 ){
            // check if the last component is a task row
            TaskRow lastRow = null;
            if( components.size() > 0 && 
                components.elementAt( components.size() - 1 ) 
                instanceof TaskRow )
                lastRow = 
                    (TaskRow)components.elementAt( components.size() - 1 );

            // check if the last row is available
            if( lastRow != null &&
                !lastRow.hasCollectives() && it.size() == 0)
                destRow = 
                    (TaskRow)components.elementAt( components.size() - 1 );
            // else add a new task row
            else{
                destRow = new TaskRow( program );
                add( destRow );
            }
            // if this is a communication statement and adding
            // to the last row, always add another row for target
            if( stmt instanceof CommunicationStmt )
                add( new TaskRow( program ) );
        }
        // found an available task row
        else{
            destRow = (TaskRow)components.elementAt( i );
            // check if a new task row needs to be inserted for target
            if( i == components.size() - 1 || !(components.elementAt( i + 1 ) 
                                                instanceof TaskRow) ) {
                TaskRow newRow = new TaskRow(program);
                components.insertElementAt( newRow, i+1  );
                super.add(newRow, null, i);
            }
        }
        destRow.add( stmt );
        return destRow;
    }

    // append to the vector selectedComponents all selected
    // sub-components contained in the component
    public Vector getAllSelected( Vector selectedComponents ){
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            selectedComponents = 
                component.getAllSelected( selectedComponents );
        }
        return selectedComponents;
    }

    // similar to getAllSelected(), but only return immediate selected
    // components in the block
    public Vector getSelected(){
        Vector selectedComponents = new Vector();
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            if( component.isSelected() )
                selectedComponents.add( component );
        }
        return selectedComponents;
    }

    // set the selection state of all sub-components
    public void setAllSelected( boolean flag ){
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            component.setAllSelected( flag );
        }
    }

    // when a click is registered in the block
    // this method is called to select or deselect
    // any statements that the point (x,y) corresponds to
    // returns true if any statements were selected or deselected
    // else false so that the caller can know if the click event is to be
    // processed further
    public boolean clickSelectStmts( boolean isShiftOrCtrlClick, 
                                     int x, int y ){
        boolean foundSelect = false;

        // x and y must be converted to global coordinates
        Rectangle globalBounds = getGlobalBounds();
        int xg = globalBounds.x + x;
        int yg = globalBounds.y + y;

        // loop through the components calling clickSelect() on each
        // stmt
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );

            // if the component is a task row, pass it and the following
            // row to CommunicationStmt.clickSelect()
            if( component instanceof TaskRow ){
                TaskRow sourceRow = (TaskRow)component;
                sourceRow.traverseReset();
                Stmt stmt;
                while( (stmt = sourceRow.traverseNext()) != null ){
                    if( stmt instanceof CommunicationStmt ){
                        CommunicationStmt communicationStmt = 
                            (CommunicationStmt)stmt;
                        TaskRow targetRow = 
                            (TaskRow)components.elementAt( i+1 );
                        if( communicationStmt.clickSelect( isShiftOrCtrlClick,
                                                           sourceRow, 
                                                           targetRow, 
                                                           xg, 
                                                           yg ) )
                            foundSelect = true;
                    }
                    // non-communication stmts don't require task rows
                    // passed to clickSelect()
                    else if( stmt.clickSelect( isShiftOrCtrlClick, xg, yg ) )
                        foundSelect = true;
                }
            }
        }
        return foundSelect;
    }
    
    // set the spacing added to the top of the block
    public void setTopSpacing( int topSpacing ){
        this.topSpacing = topSpacing;
    }

    // get the top scpaing associated with the block
    public int getTopSpacing(){
        return topSpacing;
    }

    // return the number of components contained in the block
    // (not counting the cursor)
    public int numComponents(){
        int count = 0;
        for( int i = 0; i < components.size(); i++ ){
            if( !(components.elementAt( i ) instanceof Cursor) )
                count++;
        }
        return count;
    }

    
    // take (remove all) components from block and add them to this block
    public void takeComponents( Block block ){
        while( block.components.size() > 0 ){
            AbstractComponent component = 
                (AbstractComponent)block.components.elementAt( 0 );
            component.detach();
            add( component );
        }
    }

    // resize to numTasks calls setNumTasks() recursively to 
    // redraw, re-enumerate TaskGroup's, etc.
    public void setNumTasks( int numTasks ){
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component =
                (AbstractComponent)components.elementAt( i );
            if( component instanceof Block )
                ((Block)component).setNumTasks( numTasks );
            else if( component instanceof TaskRow )
                ((TaskRow)component).setNumTasks( numTasks );
        }
        align();
    }
    
    // clone the block and all of its sub-components
    public Object clone() throws CloneNotSupportedException {
        Block block = new Block( program );
        
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            block.add( (AbstractComponent)component.clone() );
        }
        return block;
    }
    
    // find the cursor if it resides in the block, else return null
    public Cursor findCursor(){
        for( int i = 0; i < components.size(); i++ ){
            AbstractComponent component = 
                (AbstractComponent)components.elementAt( i );
            if( component instanceof Cursor )
                return (Cursor)component;
            else if( component instanceof Block ){
                Cursor cursor = ((Block)component).findCursor();
                if( cursor != null )
                    return cursor;
            }
        }
        return null;
    }

    // add as a listener to scrollPane so it can respond
    // to mouseDragged events to scroll the pane
    public void setScrollPane( AutoScrollPane scrollPane ){
        addMouseListener( scrollPane );
        addMouseMotionListener( scrollPane );
    }
    
}

