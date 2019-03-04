/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: dialog menu
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class extends JComboBox to provide an editable menu that is
 * used throughout the various dialogs. It doesn't allow duplicate
 * items to be added to the menu and has various presets for recurring
 * menu types such as task groups, message size units, etc.
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

public class DialogMenu extends JComboBox {

    public DialogMenu(){                
        
    }

    public DialogMenu( int width ){             

        // make the menu a fixed width so the layout
        // of the dialog is consistent
        Dimension dimension = getPreferredSize();
        dimension.width = width;
        setPreferredSize( dimension );
    }
 
    // add the item to the menu if it doesn't already exist
    public void addItem( Object item ){
        for( int i = 0; i < getItemCount(); i++ ){
            if( item.equals( getItemAt( i ) ) )
                return;
        }
        super.addItem( item );
    }
    
    
    // add all items in the vector items
    public void addItems( Vector items ){
        for( int i = 0; i < items.size(); i++ )
            addItem( items.elementAt( i ) );
    }
    
    // presets for size units
    public void addSizeUnits(){
        addItem( "bits" );
        addItem( "bytes" );
        addItem( "halfwords" );
        addItem( "words" );
        addItem( "integers" );
        addItem( "doublewords" );
        addItem( "quadwords" );
        addItem( "pages" );
        addItem( "kilobytes" );
        addItem( "megabytes" );
        addItem( "gigabytes" );
    }

    // presets for source tasks
    public void addSourceTaskDescriptions(){
        addItem( "all tasks" );
        addItem( "tasks t such that t is even" );
        addItem( "tasks t such that t is odd" );
    }

    // presets for target tasks
    public void addTargetTaskDescriptions(){
        addItem( "all other tasks" );
        addItem( "tasks t such that t is even" );
        addItem( "tasks t such that t is odd" );
    }

}

