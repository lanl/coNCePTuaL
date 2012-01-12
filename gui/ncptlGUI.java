/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: coNCePTuaL GUI
 *
 * By Nick Moss <nickm@lanl.gov>
 * Modifications for Eclipse by Paul Beinfest <beinfest@lanl.gov>
 * Progress bar added by Scott Pakin <pakin@lanl.gov>
 *
 * This is the top-level class for constructing all the components of
 * the GUI
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

import javax.swing.*;
import java.awt.*;
import java.security.*;
import javax.swing.plaf.basic.*;
import java.awt.event.*;
import javax.swing.event.*;

public class ncptlGUI{

    DialogPane dialogPane;
    Program program;

    // the following class is only needed for the applet
    // version. extends method used to create a floating toolbar when
    // it is torn away allowing the window to be resized and attaching
    // the menu bar to the floating window. the menu bar is returned
    // to the applet when docked
    public class ResizableToolBarUI extends BasicToolBarUI {
        private JMenuBar menuBar;
        private JApplet applet;
        private Program program;

        protected RootPaneContainer createFloatingWindow( JToolBar toolbar ){
            JFrame frame = new JFrame( "coNCePTuaL GUI" );
            CloseWindowListener listener =
                new CloseWindowListener( program, applet );
            frame.addWindowListener( listener );
            frame.setJMenuBar( menuBar );
            applet.setJMenuBar( null );
            return frame;
        }

        public void setMenuBar( JMenuBar menuBar ){
            this.menuBar = menuBar;
        }

        public void setApplet( JApplet applet ){
            this.applet = applet;
        }

        public void setProgram( Program program ){
            this.program = program;
        }

    }

    public class CloseWindowListener implements WindowListener {

        Program program;
        Container container;

        public CloseWindowListener( Program program, Container container ){
            this.program = program;
            this.container = container;
        }

        public void windowClosing( WindowEvent event ){
            if ( program.haveFileAccess() )
                new ExitDialog( container, program, false );
        }

        public void windowClosed( WindowEvent event ){}
        public void windowOpened( WindowEvent event ){}
        public void windowIconified( WindowEvent event ){}
        public void windowDeiconified( WindowEvent event ){}
        public void windowActivated( WindowEvent event ){}
        public void windowDeactivated( WindowEvent event ){}
    }

    // container is the root container of the GUI either a JFrame or JApplet
    public ncptlGUI( Container container ){

        // attempt to fix the flickering problem when running in Eclipse
        try {
            System.setProperty( "sun.awt.noerasebackground", "true" );
        } catch( NoSuchMethodError error ) {}
          catch( AccessControlException error ) {}

        Container pane;
        JToolBar mainToolBar = null;
        ResizableToolBarUI ui = null;
        if( container instanceof JApplet ){
            ui = new ResizableToolBarUI();
            ui.setApplet( (JApplet)container );
            mainToolBar = new JToolBar();
            mainToolBar.setUI( ui );
            //pane = ((JFrame)container).getContentPane();
            pane = ((JApplet)container).getContentPane();
            pane.add( mainToolBar );
            JPanel panel = new JPanel( new BorderLayout() );
            mainToolBar.add( panel );
            pane = panel;
        }
        // when running from Eclipse the container is a Frame
        else if (container instanceof Frame)
            pane = container;
        else if (container instanceof JFrame)
            pane = ((JFrame)container).getContentPane();
        else
            pane = null;

        program = new Program( container );

        // if the container is a JFrame, add ExitWindowListener to
        // exit the program gracefully on closing the window
        if( container instanceof JFrame )
            ((JFrame)container).addWindowListener( new ExitWindowListener( program ) );

        if( container instanceof JFrame ){
            ((JFrame)container).setSize( 740, 100 );
            ((JFrame)container).setVisible( true );
        }

        // pay the cost up front to construct various parse tables
        // that we'll need later on
        JPanel progressPanel = new JPanel( new BorderLayout() );
        progressPanel.setBorder( BorderFactory.createCompoundBorder( BorderFactory.createTitledBorder(" Initializing..." ),
                                                                     BorderFactory.createEmptyBorder( 5, 5, 5, 5 ) ) );
        pane.add( progressPanel );
        JProgressBar parseProgress = new JProgressBar( 0, 3 );
        parseProgress.setStringPainted( true );
        parseProgress.setForeground( GraphicsUtility.getSelectedColor() );
        parseProgress.setValue( 0 );
        progressPanel.add( parseProgress );
        pane.setVisible( true );
        program.parse( "task 0", "internal", "task_expr" );
        parseProgress.setValue( 1 );
        program.parse( "task 0 sends a message to task 1", "internal", "send_stmt" );
        parseProgress.setValue( 2 );
        program.parse( "task 0 sends a message to task 1", "internal", "program" );
        parseProgress.setValue( 3 );
        pane.remove( progressPanel );

        if( container instanceof JFrame )
            ((JFrame)container).setSize( 740, 800 );

        dialogPane = new DialogPane();

        pane.add( dialogPane, BorderLayout.SOUTH );

        program.setDialogPane( dialogPane );

        // create all of the dialogs and set them in the program
        CommunicationDialog communicationDialog =
            new CommunicationDialog( program, dialogPane );
        program.setCommunicationDialog( communicationDialog );

        ComputeDialog computeDialog = new ComputeDialog( program,
                                                         dialogPane );
        program.setComputeDialog( computeDialog );

        MeasureDialog measureDialog = new MeasureDialog( program,
                                                         dialogPane );
        program.setMeasureDialog( measureDialog );

        LoopDialog loopDialog = new LoopDialog( program,
                                                dialogPane );
        program.setLoopDialog( loopDialog );

        ReduceDialog reduceDialog = new ReduceDialog( program,
                                                      dialogPane );
        program.setReduceDialog( reduceDialog );

        SynchronizeDialog synchronizeDialog =
            new SynchronizeDialog( program, dialogPane );
        program.setSynchronizeDialog( synchronizeDialog );

        MulticastDialog multicastDialog =
            new MulticastDialog( program, dialogPane );
        program.setMulticastDialog( multicastDialog );

        WaitDialog waitDialog =
            new WaitDialog( program, dialogPane );
        program.setWaitDialog( waitDialog );

        LetDialog letDialog =
            new LetDialog( program, dialogPane );
        program.setLetDialog( letDialog );

        OtherDialog otherDialog =
            new OtherDialog( program, dialogPane );
        program.setOtherDialog( otherDialog );

        IfDialog ifDialog =
            new IfDialog( program, dialogPane );
        program.setIfDialog( ifDialog );

        SettingsDialog settingsDialog =
            new SettingsDialog( program, dialogPane );
        program.setSettingsDialog( settingsDialog );

        ExtendDialog extendDialog =
            new ExtendDialog( program, dialogPane );
        program.setExtendDialog( extendDialog );

        ComesFromsDialog comesFromsDialog =
            new ComesFromsDialog( program, dialogPane );
        program.setComesFromsDialog( comesFromsDialog );

        AutoScrollPane scrollPane = new AutoScrollPane( program );
        scrollPane.setPreferredSize( new Dimension( 700, 600 ) );

        program.addMouseListener( scrollPane );
        program.addMouseMotionListener( scrollPane );

        program.setScrollPane( scrollPane );

        pane.add( scrollPane, BorderLayout.CENTER );

        ToolBar toolBar = new ToolBar( program );

        program.setToolBar( toolBar );

        pane.add( toolBar.toolBar, BorderLayout.NORTH );

        MainMenu mainMenu = new MainMenu( container, program );

        if( container instanceof JFrame )
            ((JFrame)container).setJMenuBar( mainMenu.getMenuBar() );
        // do nothing if we're running from Eclipse
        else if (container instanceof Frame) {
                // do nothing
        }
        else if (container instanceof JApplet)
            ((JApplet)container).setJMenuBar( mainMenu.getMenuBar() );

        if( container instanceof JApplet ){
            MainMenu floatingMenu = new MainMenu( container, program );
            ui.setMenuBar( floatingMenu.getMenuBar() );
            ui.setProgram( program );
        }

        program.setMainMenu( mainMenu );

        // create a new empty program
        program.doNew( true );
    }

    public void loadParser(){
        new LoadDialog( dialogPane, program );
        program.updateState();
    }

    public Program getProgram() {
        return program;
    }

}
