/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: dialog pane
 *
 * By Nick Moss <nickm@lanl.gov>
 * Modifications for Eclipse by Paul Beinfest <beinfest@lanl.gov>
 *
 * This class maintains the dialog pane which is a detachable tool bar
 * that holds the various dialogs
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
import javax.swing.border.*;
import javax.swing.event.*;

public class DialogPane extends JToolBar {

    // the pane within the toolbar that actually holds the dialog
    private JPanel pane;

    // the toolbar is the parent container is used to allow the dialog
    // pane to be detached
    private JToolBar toolBar;

    // flag that determines if the dialog pane is empty and can be
    // used to display the help text
    private boolean isEmpty;

    public DialogPane(){
        super( "Dialog Pane" );
        pane = new JPanel();
        pane.setPreferredSize( new Dimension( 700, 280 ) );
        pane.setLayout( new BoxLayout( pane, BoxLayout.PAGE_AXIS ) );
        super.add( pane );
        isEmpty = true;
    }

    // remove all Swing components from the pane
    public void clear(){
        pane.removeAll();
    }

    // add component to pane and return it
    public Component add( Component component ){
        pane.add( component );
        return component;
    }

    protected void finalize(){
        // add glue at the bottom to force the components upward
        add( Box.createVerticalStrut( 280 ) );
        // force layout to be validated
        validate();
        repaint();
    }

    // calling setEmpty( true ) notifies the DialogPane that it
    // is no longer holding a dialog and the help text can be displayed
    public void setEmpty( boolean flag ){
        isEmpty = flag;
    }

    public boolean isEmpty(){
        return isEmpty;
    }

    // sets the default button for the pane
    // pressing enter causes the default button to be signalled
    public void setDefaultButton( JButton button ){
        try {
            pane.getRootPane().setDefaultButton( button );
        }
        catch( NullPointerException exception ){
            // we're running within Eclipse
        }
    }

}
