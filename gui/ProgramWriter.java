/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: program writer
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class provides an interface for writing a coNCePTuaL program to a  
 * file from the GUI's internal representation.
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

import java.util.*;
import java.io.*;

import org.python.core.*;

public class ProgramWriter {

    // BufferWriter writes to a file or a string
    public class BufferWriter {
        // for writing to a string
        private String buffer;
        
        // for writing to the file
        private FileWriter fileWriter;
        
        // fileName is passed as null when writing to a string
        public BufferWriter( String fileName ) throws IOException {
            if( fileName != null )
                fileWriter = new FileWriter( fileName );
            else
                fileWriter = null;
            
            buffer = "";
        }

        // write string to either a string or file
        public void write( String string ) throws IOException {
            if( fileWriter == null )
                buffer += string;
            else
                fileWriter.write( string );
        }
        
        // get the string that has been written to
        public String getBuffer(){
            return buffer;
        }

        // close the file
        public void close() throws IOException {
            if( fileWriter != null )
                fileWriter.close();
        }

    }

    // the program to be read
    private Program program;

    private BufferWriter writer;

    // receives that have yet to be matched to sends
    private Vector pendingSends;

    // the last stmt written
    private Stmt lastStmt;

    // whether this is the first statement and should be capitalized
    private boolean firstStmt;

    public ProgramWriter(){
        lastStmt = null;
    }

    public String writeProgram( Program program, String fileName ) 
        throws IOException {
        
        this.program = program;

        pendingSends = new Vector();

        writer = new BufferWriter( fileName );

	if( program.getStartComments() != null )
	    writer.write( program.getStartComments() + "\n");

        writeHeader();
        writeBody();
        writer.close();

        return writer.getBuffer();
    }

    // header includes language version, options, and assertions
    private void writeHeader() throws IOException {
        writeLanguageVersion();
        writeComesFroms();
    }

    // write the main body of the program
    private void writeBody() throws IOException  {
        firstStmt = true;
        writeBlock( program.getMainBlock(), true, "" );
        if( lastStmt != null && lastStmt.getComment() != null )
            writer.write( " " + lastStmt.getComment() );
        writer.write( "\n" );
        if( program.getEndComments() != null )
            writer.write( program.getEndComments() );
    }

    // write block which may be a direct Block or a subclass of it
    // first is true if this is the first simple_stmt in the scope
    private void writeBlock( Block block, 
                             boolean first, 
                             String indent ) throws IOException {
        block.traverseReset();
        for( ;; ){
            AbstractComponent component = block.traverseNext();
            if( component == null )
                break;
            if( component instanceof Loop ){
                if( !first )
                    writer.write( " then\n" );
                writeLoop( (Loop)component, indent );
                first = false;
            }
            else if( component instanceof MeasureBlock ){
                if( !first )
                    writer.write( " then\n" );
                writeMeasureBlock( (MeasureBlock)component, indent );
                first = false;
            }
            else if( component instanceof IfBlock ){
                if( !first )
                    writer.write( " then\n" );
                writeIfBlock( (IfBlock)component, indent );
                first = false;
            }
            else if( component instanceof LetBlock ){
                if( !first )
                    writer.write( " then\n" );
                writeLetBlock( (LetBlock)component, indent );
                first = false;
            }
            else if( component instanceof TaskRow )
                first = writeTaskRow( (TaskRow)component, first, indent );
        }
    }

    private void writeLanguageVersion() throws IOException {
        writer.write( "Require language version \"" +
                      program.getVersion() + "\".\n\n" );
    }

    private void writeComesFroms() throws IOException {
        Vector comesFroms = program.getComesFroms();
        for( int i = 0; i < comesFroms.size(); i++ ){
            ComesFrom comesFrom = (ComesFrom)comesFroms.elementAt( i );
            writer.write( comesFrom.identifier + " is " +
                          "\"" + comesFrom.description + "\"" +
                          " and comes from \"" + comesFrom.longOption +
                          "\" or \"" + comesFrom.shortOption + 
                          "\" with default " + comesFrom.defaultValue );
            writer.write( ".\n" );
        }
        if( comesFroms.size() > 0 )
            writer.write( "\n" );
    }

    private void writeLoop( Loop loop, String indent ) throws IOException {
        if( loop.getPreComments() != null )
            writer.write( indent + loop.getPreComments() );

        writer.write( indent + capitalizeFirst( loop.toCode() ) + " {" );
        if( loop.getComment() != null )
            writer.write( " " + loop.getComment() );
        writer.write( "\n" );
        writeBlock( loop, true, indent + "  " );
        if( lastStmt != null && lastStmt.getComment() != null )
            writer.write( " " + lastStmt.getComment() );
        lastStmt = null;
        writer.write( "\n" + indent + "}" );

        // print compute aggregates code if defined
        String computeAggregatesCode = 
            capitalizeFirst( loop.toCodeComputeAggregates() );
        if( computeAggregatesCode != null )
            writer.write( " then " + computeAggregatesCode );
    }
    
    private void writeMeasureBlock( MeasureBlock measureBlock, 
                                    String indent ) throws IOException {
        if( measureBlock.getReset() )
            writer.write( indent + 
                          capitalizeFirst( measureBlock.toCodeReset() ) );

        lastStmt = null;
        writeBlock( measureBlock, false, indent );
        if( capitalizeFirst( measureBlock.toCodeLog() ) != null ){
            if( lastStmt != null || measureBlock.getReset() )
                writer.write( " then\n" );
            writer.write( indent + 
                          capitalizeFirst( measureBlock.toCodeLog() ) );
        }
    }

    private void writeIfBlock( IfBlock ifBlock,
                               String indent ) throws IOException {
        if( ifBlock.getPreComments() != null )
            writer.write( indent + ifBlock.getPreComments() );
        
        writer.write( indent + 
                      capitalizeFirst( ifBlock.toCode() ) + " then {" );

        if( ifBlock.getComment() != null )
            writer.write( " " + ifBlock.getComment() );
        writer.write( "\n" );
        
        writeBlock( ifBlock.getThenBlock(), true, indent + "  " );
        writer.write( "\n" + indent + "}" );
        Block otherwiseBlock = ifBlock.getOtherwiseBlock();
        if( otherwiseBlock.numComponents() > 0 ){
            writer.write( "\n" + indent + "otherwise {\n" );
            writeBlock( otherwiseBlock, true, indent + "  " );
            writer.write( "\n" + indent + "}" );
        }
    }

    private void writeLetBlock( LetBlock letBlock,
                                String indent ) throws IOException {
        if( letBlock.getPreComments() != null )
            writer.write( indent + letBlock.getPreComments() );

        writer.write( indent + 
                      capitalizeFirst( letBlock.toCode() ) + " {" );
        if( letBlock.getComment() != null )
            writer.write( " " + letBlock.getComment() );
        writer.write( "\n" );
        writeBlock( letBlock, true, indent + "  " );
        writer.write( "\n" + indent + "}" );
    }

    // write all the statements contained in a task row
    private boolean writeTaskRow( TaskRow taskRow, boolean first, String indent ) throws IOException {
        for( int i = 0; i < pendingSends.size(); i++ ){
            CommunicationStmt stmt = 
                (CommunicationStmt)pendingSends.elementAt( i );
            if( stmt.getTargetRow() == taskRow ){
                if( !first ){
                    writer.write( " then" );
                    if( lastStmt != null && lastStmt.getComment() != null )
                        writer.write( " " + lastStmt.getComment() );
                    writer.write( "\n" );
                }
                writer.write( indent + capitalizeFirst( stmt.toCode() ) );
                pendingSends.remove( stmt );
                first = false;
                i--;
                lastStmt = stmt;
            }
        }

        taskRow.traverseReset();
        for( ;; ){
            Stmt stmt = taskRow.traverseNext();
            if( stmt == null )
                break;
            if( !first ){
                writer.write( " then" );
                if( lastStmt != null && lastStmt.getComment() != null )
                    writer.write( " " + lastStmt.getComment() );
                writer.write( "\n" );
            }

            if( stmt instanceof CommunicationStmt &&
                ((CommunicationStmt)stmt).getTargetRow() != null ){
                if( stmt.getPreComments() != null )
                    writer.write( indent + stmt.getPreComments() );
                writer.write( indent + 
                              capitalizeFirst( ((CommunicationStmt)stmt).toCodeReceive() ) );
                pendingSends.add( stmt );
            }
            else{
                if( stmt.getPreComments() != null )
                    writer.write( indent + stmt.getPreComments() );
                writer.write( indent + capitalizeFirst( stmt.toCode() ) );
            }

            first = false;
            lastStmt = stmt;
        }
        return first;
    }

    private String capitalizeFirst( String code ){
        if( firstStmt ){
            firstStmt = false;
            return Character.toUpperCase( code.charAt( 0 ) ) +
                code.substring( 1 );
        }
        else
            return code;
    }
    
}

