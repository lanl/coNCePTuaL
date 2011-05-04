/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: abstract dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class is the base class for other dialogs named XXXDialog such
 * as CommunicationDialog or LoopDialog and defines the minimal
 * interface that a dialog must implement in order to interface with
 * the GUI
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
import java.awt.Container;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;

abstract public class AbstractDialog 
    implements ActionListener, WindowListener {
    
    // all dialogs need to interract with the program
    protected Program program;
    
    // base constructor
    public AbstractDialog( Program program ){   
        this.program = program;
    }
    
    // actionPerformed must be implemented to respond to events from
    // Swing components within the dialog
    abstract public void actionPerformed( ActionEvent event );

    // all dialogs must implement this method for updating their state
    // which typically depends on the current selection of components
    abstract public void updateState();

    // the following windowXXX() methods are not currently used
    // because the dialog resides in dialogPane and not a frame
    abstract public void windowClosing( WindowEvent event );

    public void windowClosed( WindowEvent event ){

    }

    public void windowOpened( WindowEvent event ){

    }

    public void windowIconified( WindowEvent event ){

    }

    public void windowDeiconified( WindowEvent event ){

    }
    
    public void windowActivated( WindowEvent event ){

    }
    
    public void windowDeactivated( WindowEvent event ){
        
    }
}

