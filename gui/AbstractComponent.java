/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: abstract component
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is the abstract base class for all components that make
 * up a program. Components deriving from AbstractComponent define
 * both a visual and data represention.
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
import java.util.*;

abstract public class AbstractComponent extends JComponent
    implements MouseListener, MouseMotionListener, Cloneable {

    // id is unique in its parent container
    private int id;

    // the line number corresponding to this component
    // if it was read in from a file else -1
    private int lineNumber;

    // true if the component is selected
    private boolean isSelected;

    // preCommments covers all comments read since the last
    // component that comments could be attached to
    private String preComments;

    // holds the comment that was on the same line as this component as
    // it was read in from the file
    private String comment;

    public AbstractComponent(){
        id = -1;
        lineNumber = -1;
        preComments = null;
        comment = null;

        // these two calls add listeners that call the mouseXXX()
        // methods below in order to respond to mouse events
        addMouseMotionListener( this );
        addMouseListener( this );
    }

    // translate this component's bounds into global coordinates
    // (relative to the Program component)
    public Rectangle getGlobalBounds(){
        AbstractComponent parent = (AbstractComponent)getParent();
        return parent.getGlobalBounds( getBounds() );
    }

    // translate the point (x,y) into global coordinates
    // (relative to the Program component)
    public Point toGlobalPoint( int x, int y ){
        Rectangle globalBounds = getGlobalBounds();
        Point point = new Point();
        point.x = globalBounds.x + x;
        point.y = globalBounds.y + y;
        return point;
    }

    // used internally to recursively determine global bounds
    private Rectangle getGlobalBounds( Rectangle localBounds ){
        // we have reached the root component
        if( this instanceof Program )
            return localBounds;

        // translate local coordinates into global coordinates
        // at the current level
        Rectangle nextBounds = getBounds();
        nextBounds.x += localBounds.x;
        nextBounds.y += localBounds.y;

        // retain the original width and height
        nextBounds.width = localBounds.width;
        nextBounds.height = localBounds.height;

        // get bounds relative to parent
        AbstractComponent parent = (AbstractComponent)getParent();
        return parent.getGlobalBounds( nextBounds );
    }

    // get component ID
    public int getID(){
        return id;
    }

    // set component ID
    public void setID( int id ){
        this.id = id;
    }

    // detach this component from its parent component
    public void detach(){
        AbstractComponent parent = (AbstractComponent)getParent();

        // only detach if not already detached
        if( parent != null )
            parent.remove( this );
    }

    // stub method for container classes to override in order to
    // remove a sub-component. needed because derived classes may need
    // to store references to component in specialized ways
    public void remove( AbstractComponent component ){
        super.remove( component );
    }

    // select or deselect this component subclasses typically override
    // this method to define extra functionality such as updating
    // dialogs whenever a component's selection state is modified
    public void setSelected( boolean flag ){
        isSelected = flag;
    }

    // set the selection state with none of the side-effects that
    // might accompany setSelected()
    public final void setSelectedOnly( boolean flag ){
        isSelected = flag;
    }

    // returns selection status of this component
    public boolean isSelected(){
        return isSelected;
    }

    // stub methods for mouse events
    // subclasses typically override one or more of these

    // called when mouse is dragged within the component
    public void mouseDragged( MouseEvent mouseEvent ){

    }

    // called when mouse is moved within the component
    public void mouseMoved( MouseEvent mouseEvent ){

    }

    // called when mouse is clicked within the component
    public void mouseClicked( MouseEvent mouseEvent ){

    }

    // called when mouse enters the component
    public void mouseEntered( MouseEvent mouseEvent ){

    }

    // called when mouse leaves the component
    public void mouseExited( MouseEvent mouseEvent ){

    }

    // called when mouse button is pressed within the component
    public void mousePressed( MouseEvent mouseEvent ){

    }

    // called when mouse button is released within the component
    public void mouseReleased( MouseEvent mouseEvent ){

    }

    // overriden by container classes to recursively set the selection
    // state of component itself and all sub-components
    public void setSelectAll( boolean flag ){
        isSelected = flag;
    }

    // sets selection state to true if the component bounds in global
    // coordinates are sufficiently contained in the marquee
    public void selectRegion( Rectangle marquee ){
        if( Utility.marqueeSelects( marquee, getGlobalBounds() ) )
            setSelected( true );
    }

    // overriden and used to recursively paint statements in container
    // classes
    public void paintStmts( Graphics graphics ){

    }

    // sets the program that this component is part of.
    // components typically need to interract with the program
    // directly such as updating dialogs when they are selected
    public void setProgram( Program program ){

    }

    // used to recursively obtain a vector of all selected components.
    // append to the vector selectedComponents the component itself
    // and all selected sub-components contained in the component.
    // overriden by container components
    public Vector getAllSelected( Vector selectedComponents ){
        if( isSelected )
            selectedComponents.add( this );
        return selectedComponents;
    }

    // overriden by container components. used to recursively set
    // the selection state of the component itself and all of its
    // sub-components
    public void setAllSelected( boolean flag ){
        setSelectedOnly( flag );
    }

    // overidden by components that define variables in a scope such
    // as Loop. recursively returns scope variables by getting scope
    // variables from parent who append scope variables from their
    // parent and so on until reaching the Program component
    public Vector getVariablesInScope( Vector variables ){
        AbstractComponent parent = (AbstractComponent)getParent();
        return parent.getVariablesInScope( variables );
    }

    // overidden by components that define variables in a scope such
    // as Loop. performs the same function as getVariablesInScope()
    // but also includes predeclared variables
    public Vector getAllVariablesInScope( Vector variables ){
        AbstractComponent parent = (AbstractComponent)getParent();
        return parent.getAllVariablesInScope( variables );
    }

    // clone this component
    // overriden by sub-classes that need to perform a deep copy
    // of their data structures
    public Object clone() throws CloneNotSupportedException {
        return super.clone();
    }

    // set the line number corresponding to this component
    // usually called in ProgramReader when the program is read
    // in from a file
    public void setLineNumber( int lineNumber ){
        this.lineNumber = lineNumber;
    }

    // get the line number associated with this component may return
    // -1 to indicate that there is no line number associated with
    // this component. this may happen if the component was created in
    // the GUI and not read from a file
    public int getLineNumber(){
        return lineNumber;
    }

    // set the preComments which cover all the comments since the last
    // component that comments could be attached to. preComments are
    // read in and attached to components in PrograReader and written
    // out by ProgramWriter
    public void setPreComments( String preComments ){
        this.preComments = preComments;
    }

    // set the comments that will be written out on the same
    // line by ProgramWriter
    public void setComment( String comment ){
        this.comment = comment;
    }

    // get preComments
    public String getPreComments(){
        return preComments;
    }

    // get comment
    public String getComment(){
        return comment;
    }

}
