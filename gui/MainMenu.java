/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: main menu
 *
 * By Nick Moss <nickm@lanl.gov>
 * Modifications for Eclipse by Paul Beinfest <beinfest@lanl.gov>
 *
 * This class maintains the main menu at the top of the frame or applet
 * and includes "File, "Edit", "Options", and "Advanced"
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
import java.io.*;

public class MainMenu implements ActionListener {

    // the root container (either a JFrame or JApplet)
    private Container container;

    private Program program;

    private JMenuBar menuBar;

    private JMenuItem copyItem;
    private JMenuItem cutItem;
    private JMenuItem pasteItem;
    private JMenuItem undoItem;

    public MainMenu( Container container, Program program ){
        this.container = container;
        this.program = program;

        createMenus();
    }

    public JMenuBar getMenuBar(){
        return menuBar;
    }

    // create the menu bar and all menus
    private void createMenus(){
        menuBar = new JMenuBar();

        // Create a File menu only when it makes sense to have one.
        if ( program.useFileMenu() )
            createFileMenu();
        createEditMenu();
        createOptionsMenu();
        createAdvancedMenu();

        menuBar.addMouseListener(new MouseListener() {

                public void mouseClicked(MouseEvent e) {
                        menuBar.requestFocus();
                }

                public void mousePressed(MouseEvent e) {
                }

                public void mouseReleased(MouseEvent e) {
                }

                public void mouseEntered(MouseEvent e) {
                }

                public void mouseExited(MouseEvent e) {
                }

        });

        //if( container instanceof JFrame )
        //    ((JFrame)container).setJMenuBar( menuBar );
        //else
        //    ((JApplet)container).setJMenuBar( menuBar );
    }

    // create the file menu and add it to the menu bar
    private void createFileMenu(){
        JMenu fileMenu = new JMenu( "File" );
        fileMenu.setMnemonic( KeyEvent.VK_F );

        JMenuItem newItem = new JMenuItem( "New" );
        newItem.setMnemonic( KeyEvent.VK_N );
        newItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_N, ActionEvent.CTRL_MASK ) );
        fileMenu.add( newItem );
        newItem.addActionListener( this );

        JMenuItem openItem = new JMenuItem( "Open..." );
        openItem.setMnemonic( KeyEvent.VK_O );
        openItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_O, ActionEvent.CTRL_MASK ) );
        fileMenu.add( openItem );
        openItem.addActionListener( this );

        JMenuItem saveItem = new JMenuItem( "Save" );
        saveItem.setMnemonic( KeyEvent.VK_S );
        saveItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_S, ActionEvent.CTRL_MASK ) );
        fileMenu.add( saveItem );
        saveItem.addActionListener( this );

        JMenuItem saveAsItem = new JMenuItem( "Save As..." );
        saveAsItem.setMnemonic( KeyEvent.VK_A );
        saveAsItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_A, ActionEvent.CTRL_MASK ) );
        fileMenu.add( saveAsItem );
        saveAsItem.addActionListener( this );

        JMenuItem printItem = new JMenuItem( "Print..." );
        printItem.setMnemonic( KeyEvent.VK_P );
        printItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_P, ActionEvent.CTRL_MASK ) );
        fileMenu.add( printItem );
        printItem.addActionListener( this );

        if( container instanceof JFrame ){
            JMenuItem quitItem = new JMenuItem( "Quit" );
            quitItem.setMnemonic( KeyEvent.VK_Q );
            quitItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_Q, ActionEvent.CTRL_MASK ) );
            fileMenu.add( quitItem );
            quitItem.addActionListener( this );
        }

        menuBar.add( fileMenu );
    }

    // create the edit menu and add it to the menu bar
    private void createEditMenu(){
        final JMenu editMenu = new JMenu( "Edit" );
        editMenu.setMnemonic( KeyEvent.VK_E );

        undoItem = new JMenuItem( "Undo" );
        undoItem.setMnemonic( KeyEvent.VK_Z );
        undoItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_Z, ActionEvent.CTRL_MASK ) );
        editMenu.add( undoItem );
        undoItem.addActionListener( this );

        editMenu.addSeparator();

        copyItem = new JMenuItem( "Copy" );
        copyItem.setMnemonic( KeyEvent.VK_C );
        copyItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_C, ActionEvent.CTRL_MASK ) );
        editMenu.add( copyItem );
        copyItem.addActionListener( this );

        cutItem = new JMenuItem( "Cut" );
        cutItem.setMnemonic( KeyEvent.VK_X );
        cutItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_X, ActionEvent.CTRL_MASK ) );
        editMenu.add( cutItem );
        cutItem.addActionListener( this );

        pasteItem = new JMenuItem( "Paste" );
        pasteItem.setMnemonic( KeyEvent.VK_V );
        pasteItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_V, ActionEvent.CTRL_MASK ) );
        editMenu.add( pasteItem );
        pasteItem.addActionListener( this );

        editMenu.addMouseListener(new MouseListener() {

                public void mouseClicked(MouseEvent e) {
                        editMenu.requestFocus();
                }

                public void mousePressed(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseReleased(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseEntered(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseExited(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

        });

        menuBar.add( editMenu );
    }

    // create the options menu and add it to the menu bar
    private void createOptionsMenu(){
        final JMenu optionsMenu = new JMenu( "Options" );
        optionsMenu.setMnemonic( KeyEvent.VK_O );

        JMenuItem settingsItem = new JMenuItem( "Settings..." );
        settingsItem.setMnemonic( KeyEvent.VK_E );
        settingsItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_E, ActionEvent.CTRL_MASK ) );
        optionsMenu.add( settingsItem );
        settingsItem.addActionListener( this );

        optionsMenu.addMouseListener(new MouseListener() {

                public void mouseClicked(MouseEvent e) {
                        optionsMenu.requestFocus();
                }

                public void mousePressed(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseReleased(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseEntered(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseExited(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

        });

        menuBar.add( optionsMenu );
    }


    // create the advanced meny and add it to the menu bar
    private void createAdvancedMenu(){
        final JMenu advancedMenu = new JMenu( "Advanced" );
        advancedMenu.setMnemonic( KeyEvent.VK_V );

        JMenuItem conditionalItem = new JMenuItem( "Add conditional..." );
        conditionalItem.setMnemonic( KeyEvent.VK_T );
        conditionalItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_T, ActionEvent.CTRL_MASK ) );
        advancedMenu.add( conditionalItem );
        conditionalItem.addActionListener( this );

        JMenuItem commandLineItem = new JMenuItem( "Command line options..." );
        commandLineItem.setMnemonic( KeyEvent.VK_L );
        commandLineItem.setAccelerator( KeyStroke.getKeyStroke( KeyEvent.VK_L, ActionEvent.CTRL_MASK ) );
        advancedMenu.add( commandLineItem );
        commandLineItem.addActionListener( this );

        advancedMenu.addMouseListener(new MouseListener() {

                public void mouseClicked(MouseEvent e) {
                        advancedMenu.requestFocus();
                }

                public void mousePressed(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseReleased(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseEntered(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

                public void mouseExited(MouseEvent e) {
                        // TODO Auto-generated method stub

                }

        });

        menuBar.add( advancedMenu );
    }

    // respond to selections in the menus
    public void actionPerformed( ActionEvent e ){
        String command = e.getActionCommand();

        if( command.equals( "New" ) )
            program.doNew( false );
        else if( command.equals( "Open..." ) )
            program.open();
        else if( command.equals( "Save" ) )
            program.save();
        else if( command.equals( "Copy" ) )
            program.copySelection();
        else if( command.equals( "Cut" ) )
            program.cutSelection();
        else if( command.equals( "Paste" ) )
            program.paste();
        else if( command.equals( "Save As..." ) )
            program.saveAs();
        else if( command.equals( "Print..." ) )
            program.print();
        else if( command.equals( "Settings..." ) )
            program.updateSettingsDialog();
        else if( command.equals( "Add conditional..." ) )
            program.addConditional();
        else if( command.equals( "Command line options..." ) )
            program.showComesFromsDialog();
        else if( command.equals( "Undo" ) )
            program.undo();
        else if( command.equals( "Quit" ) ){
            program.exit();
        }
    }

    // the following methods enable/disable various menu items and are
    // called when the state of the GUI changes

    public void enableCopy( boolean flag ){
        copyItem.setEnabled( flag );
    }

    public void enableCut( boolean flag ){
        cutItem.setEnabled( flag );
    }

    public void enablePaste( boolean flag ){
        pasteItem.setEnabled( flag );
    }

    public void enableUndo( boolean flag ){
        undoItem.setEnabled( flag );
    }

}
