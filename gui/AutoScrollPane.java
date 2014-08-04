/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: auto scroll pane
 *
 * By Nick Moss <nickm@lanl.gov>
 * Modifications for Eclipse by Paul Beinfest <beinfest@lanl.gov>
 *
 * This class extends JScrollPane to allow dragging within it to cause
 * the pane to scroll, e.g: dragging a selection rectangle or dragging
 * a communication statement from on task to another.
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

public class AutoScrollPane extends JScrollPane
    implements MouseListener, MouseMotionListener {

    // the number of pixels to scroll on each drag event
    private static final int SCROLL_DRAG = 10;

    // the number of pixels to scroll on clicking scroll arrows
    private static final int SCROLL_BAR_UNIT_INCREMENT = 50;

    // the number of pixels to scroll on clicking within the scroll bar
    private static final int SCROLL_BAR_BLOCK_INCREMENT = 100;

    // reference to our child component
    private JComponent childComponent;

    // construct a new AutoScrollPane containing child
    public AutoScrollPane( JComponent child ){
        super( child );
        childComponent = child;

        // set the scroll increments to the constants defined above
        getHorizontalScrollBar().setUnitIncrement( SCROLL_BAR_UNIT_INCREMENT );
        getVerticalScrollBar().setUnitIncrement( SCROLL_BAR_UNIT_INCREMENT );
        getHorizontalScrollBar().setBlockIncrement( SCROLL_BAR_BLOCK_INCREMENT );
        getVerticalScrollBar().setBlockIncrement( SCROLL_BAR_BLOCK_INCREMENT );
    }

    // called when mouse is dragged within the component
    public void mouseDragged( MouseEvent mouseEvent ){

        // get the source of the mouse event
        // and translate to global coordinates
        Object source = mouseEvent.getSource();
        Point mp;
        if( source instanceof AbstractComponent &&
            !(source instanceof Program) )
            mp = ((AbstractComponent)source).toGlobalPoint( mouseEvent.getX(), mouseEvent.getY() );
        else
            mp = new Point( mouseEvent.getX(), mouseEvent.getY() );

        // the viewport within the scroll pane
        JViewport viewport = getViewport();

        // the visible bounds
        Rectangle bounds = getBounds();

        // the size of the entire scroll pane
        Dimension viewSize = viewport.getViewSize();

        // the upper-left corner of the current view position
        Point p = viewport.getViewPosition();

        // horizontal scrolling

        // scroll right
        if( mp.x > p.x + bounds.width ){
            int remaining = viewSize.width - bounds.width - p.x;
            if( remaining > 0 ){
                p.x += Math.min( SCROLL_DRAG, remaining );
                viewport.setViewPosition( p );
            }
        }
        // scroll left
        else if( mp.x < p.x ){
            if( p.x > 0 ){
                p.x -= Math.min( SCROLL_DRAG, p.x );
                viewport.setViewPosition( p );
            }
        }

        // vertical scrolling

        // scroll down
        if( mp.y > p.y + bounds.height ){
            int remaining = viewSize.height - bounds.height - p.y;
            if( remaining > 0 ){
                p.y += Math.min( SCROLL_DRAG, remaining );
                viewport.setViewPosition( p );
            }
        }
        // scroll up
        else if( mp.y < p.y ){
            if( p.y > 0 ){
                p.y -= Math.min( SCROLL_DRAG, p.y );
                viewport.setViewPosition( p );
            }
        }
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
        childComponent.requestFocus();
    }

    // called when mouse button is released within the component
    public void mouseReleased( MouseEvent mouseEvent ){

    }

}
