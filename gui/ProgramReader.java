/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: program reader
 *
 * By Nick Moss <nickm@lanl.gov>
 * Improved and corrected by Paul Beinfest <beinfest@lanl.gov> 
 *
 * This class provides an interface for reading a coNCePTuaL program
 * from a file into the GUI's internal representation while
 * maintaining all the necessary information such that it can be saved
 * back in its original or modified form using
 * ProgramWriter. ProgramReader uses jython to call the coNCePTuaL
 * parser on an input file and walk the abstract syntax tree returned
 * by the parser and using the interface provided by Program, and
 * other components, to construct the GUI's internal representation.
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

import java.util.*;
import java.io.*;
import org.python.core.*;

public class ProgramReader {

    // Context contains the current Block being read
    public static class Context {
        public Block block;
    }

    // message alignment fields
    public class Alignment{
        public String alignment;
        public String units;
        public String mode;

        public Alignment(){
            alignment = "0";
            units = "bytes";
            mode = "unaligned";
        }
    }

    // message size fields
    public class ItemSize{
        String size;
        String units;
        
        public ItemSize(){
            size = "0";
            units = "bytes";
        }
    }

    private Program program;

    // contains CommunicationStmt's of receive_stmts
    // that have yet to be matched with a send_stmt
    private Vector pendingSends;
    
    // the comments returned by the lexer
    private PyDictionary comments;

    // the current line number used in attaching comments to
    // components
    private int line;

    // read a program from a file
    public void readProgramFile( String programFile, 
                                 Program program ) throws IOException {
        readProgramString( fileToString( programFile ), program );
    }

    // read a program from a string
    public void readProgramString( String programString, 
                                   Program program ) throws IOException {
        this.program = program;
        program.clear();
        program.detachCursor();
        if (comments != null) comments.clear();
        
        pendingSends = new Vector();

        // parse the program
        AST astRoot = 
            program.parse( programString, "internal", "program" );
        comments = program.getComments();
        
        program.setNumTasks( determineNumTasks( astRoot, 
                                                program.getNumTasks() ) );

        // read the comments that appear at the very beginning of the
        // file
        readStartComments( programString );

        read_program( astRoot );
        
        // read the remaining comments that appear at the end of the file
        readEndComments();
            
        program.attachCursor();
        
        // force the program to be resized on the number of tasks to
        // display
        program.resize();
    }

    // walk the AST to determine the number of tasks to display by
    // looking for constant task numbers, e.g: "task 13" - the number of
    // tasks to display is the max task number encountered or some
    // default minimum value passed in the initial call as numTasks
    private int determineNumTasks( AST node, int numTasks ){
        if( node.getType().equals( "task_expr" ) ){
            int task = Utility.getTask( node.getCode() );
            if( task >= numTasks )
                return task + 1;
            else
                return numTasks;
        }
        else{
            AST children[] = node.getChildren();
            for( int i = 0; i < children.length; i++ )
                numTasks = determineNumTasks( children[i], numTasks );
        }
        return numTasks;
    }
    
    // read a file into a string
    private String fileToString( String fileName ) throws IOException {
        StringBuffer stringBuffer = new StringBuffer( 1000 );
        BufferedReader reader = new BufferedReader( new FileReader( fileName ) );
        char[] buf = new char[1024];
        int numRead = 0;
        while( (numRead = reader.read(buf)) != -1 ){
            String readData = String.valueOf( buf, 0, numRead );
            stringBuffer.append( readData );
            buf = new char[1024];
        }
        reader.close();
        return stringBuffer.toString();
    }

    // the read_XXX() methods that follow are named corrseponding to
    // the type of AST they correspond to, if they do not directly
    // corrsepond to a type of AST they are named readXXX()

    private void read_program( AST node ){
        assert node.getType().equals( "program" );
        AST children[] = node.getChildren();

        // set context to the main block
        Block mainBlock = program.getMainBlock();
        Context context = new Context();
        context.block = mainBlock;

        for( int i = 0; i < children.length; i++ ){
            if( children[i].getType().equals( "header_decl_list" ) )
                read_header_decl_list( children[i] );
            else if( children[i].getType().equals( "top_level_stmt_list" ) )
                read_top_level_stmt_list( children[i], context );
            else
                assert false;
        }
    }

    private void read_header_decl_list( AST node ){
        assert node.getType().equals( "header_decl_list" );
        AST children[] = node.getChildren();
        for( int i = 0; i < children.length; i++ )
            read_header_decl( children[i] );
    }
    
    private void read_top_level_stmt_list( AST node, Context context ){
        assert node.getType().equals( "top_level_stmt_list" );
        AST children[] = node.getChildren();
        for( int i = 0; i < children.length; i++ )
            read_top_level_stmt( children[i], context );
    }
    
    private void read_top_level_stmt( AST node, Context context ){
        assert node.getType().equals( "top_level_stmt" );
        
        read_simple_stmt_list( node.getLeft(), context );
    }

    private void read_simple_stmt_list( AST node, Context context ){
        assert node.getType().equals( "simple_stmt_list" );
        
        AST children[] = node.getChildren();
        for( int i = 0; i < children.length; i++ )
            read_simple_stmt( children[i], context );
    }
    
    private void read_header_decl( AST node ){
        assert node.getType().equals( "header_decl" );
        AST children[] = node.getChildren();
        for( int i = 0; i < children.length; i++ ){
            if( children[i].getType().equals( "version_decl" ) )
                read_version_decl( children[i] );
            else if( children[i].getType().equals( "param_decl" ) )
                program.addComesFrom( read_param_decl( children[i] ) );
            else
                assert false;
        }
    }

    private void read_version_decl( AST node ){
        assert node.getType().equals( "version_decl" );
        String versions[] = node.getAttrArray();
        program.setVersion( versions[0] );
        // version[1] is currently ignored
    }

    private ComesFrom read_param_decl( AST node ){
        
        assert node.getType().equals( "param_decl" );

        ComesFrom comesFrom = new ComesFrom();
        
        comesFrom.identifier = read_ident( node.getChild( 0 ) );
        comesFrom.description = read_string( node.getChild( 1 ) );
        comesFrom.longOption = read_string( node.getChild( 2 ) );
        comesFrom.shortOption = read_string( node.getChild( 3 ) );
        comesFrom.defaultValue = readExpr( node.getChild( 4 ) );
        comesFrom.lineNumber = node.getLineNumber();
        attachComments( comesFrom, node );

        return comesFrom;
    }

    private String readExpr( AST node ){
        return node.getCode();
    }

    private static String read_ident( AST node ){
        assert node.getType().equals( "ident" );
        return node.getAttr();
    }

    private String read_string( AST node ){
        assert node.getType().equals( "string" );
        String str = node.getAttr();
        // escape "
        str = str.replaceAll( "\"", "\\\\\"" );
        return str;
    }
    
    private void read_let_stmt( AST node, Context context ){
        assert node.getType().equals( "let_stmt" );
        
        LetBlock letBlock = new LetBlock( program );
        attachComments( letBlock, node );
        letBlock.setLineNumber( node.getLineNumber() );
        context.block.add( letBlock );

        letBlock.setCode( "let " + 
                          read_let_binding_list( node.getLeft(), letBlock ) +
                          " while" );

        // save context so it can be restored after adding LetBlock
        Block previousBlock = context.block;
        context.block = letBlock;

        read_simple_stmt( node.getRight(), context );

        // restore context
        context.block = previousBlock;

    }

    private String read_let_binding_list( AST node, LetBlock letBlock ){
        assert node.getType().equals( "let_binding_list" );
        AST children[] = node.getChildren();
        String code = "";
        for( int i = 0; i < children.length; i++ ){
            if( i > 0 )
                code += " and ";
            code += read_let_binding( children[i], letBlock );
        }
        return code;
    }

    private String read_let_binding( AST node, LetBlock letBlock ){
        assert node.getType().equals( "let_binding" );
        String ident = read_ident( node.getLeft() );

        // add variable to scope
        letBlock.addVariable( ident );

        String code =  ident + " be ";

        String attr = node.getAttr();
        if( attr.equals( "None" ) )
            code += readExpr( node.getRight() );
        else if( attr.equals( "" ) )    
            code += "a random task";
        else if( attr.equals( "E" ) )
            code += "a random task other than " + readExpr( node.getRight() );
        else if( attr.equals( "u" ) )
            code += "a random task less than " + readExpr( node.getRight() );
        else if( attr.equals( "uE" ) )
            code += "a random task less than " 
                + readExpr( node.getRight() ) + " but not " +
                readExpr( node.getChild( 2 ) );
        else if( attr.equals( "l" ) )
            code += "a random task greater than " 
                + readExpr( node.getRight() );
        else if( attr.equals( "lE" ) )
            code += "a random task greater than " 
                + readExpr( node.getRight() ) + " but not " +
                readExpr( node.getChild( 2 ) );
        else if( attr.equals( "LU" ) )
            code += "a random task in [" 
                + readExpr( node.getRight() ) + "," +
                readExpr( node.getChild( 2 ) ) + "]";
        else if( attr.equals( "LUE" ) )
            code += "a random task in [" 
                + readExpr( node.getRight() ) + "," +
                readExpr( node.getChild( 2 ) ) + "] but not " +
                readExpr( node.getChild( 3 ) );
        
        return code;
    }

    private void read_for_count( AST node, Context context ){
        assert node.getType().equals( "for_count" );
        Loop loop = new Loop( program );
        attachComments( loop, node );
        loop.setLineNumber( node.getLineNumber() );
        loop.setLoopType( Loop.LOOP_TYPE_REPETITIONS );

        String synch = node.getAttr();
        if( synch.equals( "synchronized" ) )
            loop.setSync( true );


        // save the previous block so context can be reset
        // at the end of the loop
        Block previousBlock = context.block;

        context.block.add( loop );
        context.block = loop;
        
        loop.setNumReps( readExpr( node.getLeft() ) );

        if( !(node.getRight().getType().equals( "simple_stmt" )) ){
                if (node.getChildren().length > 2) {
                    loop.setNumWarmups( readExpr( node.getRight() ) );
                    read_simple_stmt( node.getChild( 2 ), context );
                }
        }
        else
            read_simple_stmt( node.getRight(), context );
        
        // restore context
        context.block = previousBlock;
    }

    private void read_for_time( AST node, Context context ){
        assert node.getType().equals( "for_time" );
        Loop loop = new Loop( program );
        attachComments( loop, node );
        loop.setLineNumber( node.getLineNumber() );
        loop.setLoopType( Loop.LOOP_TYPE_TIMED );

        loop.setTime( readExpr( node.getLeft() ) );
        loop.setTimeUnits( read_time_unit( node.getRight() ) );
        
        // save context
        Block previousBlock = context.block;
        context.block.add( loop );
        context.block = loop;
        read_simple_stmt( node.getChild( 2 ), context );
        
        // restore context
        context.block = previousBlock;
    }

    private void read_for_each( AST node, Context context ){
        assert node.getType().equals( "for_each" );
        Loop loop = new Loop( program );
        attachComments( loop, node );
        loop.setLineNumber( node.getLineNumber() );
        loop.setLoopType( Loop.LOOP_TYPE_FOR_EACH );

        loop.setSequenceName( read_ident( node.getChild( 0 ) ) );

        read_range_list( node.getChild( 1 ), loop );
        
        // save context
        Block previousBlock = context.block;
        context.block.add( loop );
        context.block = loop;
        read_simple_stmt( node.getChild( 2 ), context );
        
        // restore context
        context.block = previousBlock;
    }
    private void read_range_list( AST node, Loop loop ){
        assert node.getType().equals( "range_list" );
        AST children[] = node.getChildren();
        String sequence = "";

        for( int i = 0; i < children.length; i++ )
            loop.setSequence( i, read_range( children[i] ) );
    }

    private String read_range( AST node ){
        assert node.getType().equals( "range" );
        String code = node.getCode();
        
        // strip the trailing and leading braces and whitespace if any
        // because this field is represented internally w/o the braces
        if( code.matches( "\\{ .+ \\}" ) ) 
            return code.substring( 2, code.length() - 2 );
        else
            return code;
    }
    
    private void matchSendReceive( CommunicationStmt sendStmt, 
                                   Context context ){
        if( sendStmt.getUnsuspecting() ){
            for( int i = 0; i < pendingSends.size(); i++ ){
                CommunicationStmt pendingSend = 
                    (CommunicationStmt)pendingSends.elementAt( i );
                
                // find corresponding receive_stmt by matching source
                // and target tasks
                if( pendingSend.getTaskGroup().toCodeSource().equals( sendStmt.getTaskGroup().toCodeSource() ) &&
                    pendingSend.getTaskGroup().toCodeTarget().equals( sendStmt.getTaskGroup().toCodeTarget() ) ){
                    pendingSend.setMessageSize( sendStmt.getMessageSize() );
                    pendingSend.setMessageSizeUnits( sendStmt.getMessageSizeUnits() );
                    pendingSend.setSourceAsync( sendStmt.getSourceAsync() );
                    pendingSend.setSourceVerificationOrTouching( sendStmt.getSourceVerificationOrTouching() );
                    pendingSend.setSourceAlignment( sendStmt.getSourceAlignment() );
                    pendingSend.setSourceAlignmentUnits( sendStmt.getSourceAlignmentUnits() );
                    pendingSend.setSourceAlignmentMode( sendStmt.getSourceAlignmentMode() );
                    pendingSend.setSourceBuffer( sendStmt.getSourceBuffer() );
                    pendingSend.setSourceUniqueBuffer( sendStmt.getSourceUniqueBuffer() );
                    
                    TaskRow targetRow;
                    AbstractComponent lastComponent = 
                        context.block.componentAt( context.block.numComponents() - 1 );
                    if( lastComponent instanceof TaskRow && 
                        !((TaskRow)lastComponent).hasStmts() )
                        targetRow = (TaskRow)lastComponent;
                    else{
                        targetRow = new TaskRow( program );
                        context.block.add( targetRow );
                    }
                    pendingSend.setTargetRow( targetRow );
                    pendingSends.remove( pendingSend );
                    break;
                }
            }
        }
        else
//              ((CommunicationStmt)sendStmt).setTargetAsync(false);
            context.block.add( sendStmt ).getID();
    }

    private void read_simple_stmt( AST node, Context context ){
        assert node.getType().equals( "simple_stmt" );
        AST children[] = node.getChildren();
        for( int i = 0; i < children.length; i++ ){
            if( children[i].getType().equals( "send_stmt" ) ){
                CommunicationStmt stmt = read_send_stmt( children[i] );
                matchSendReceive( stmt, context );
            }
            else if( children[i].getType().equals( "receive_stmt" ) ){
                CommunicationStmt stmt = read_receive_stmt( children[i] );
                context.block.add( stmt );
                pendingSends.add( stmt );
            }
            else if( children[i].getType().equals( "mcast_stmt" ) ){
                MulticastStmt stmt = read_mcast_stmt( children[i] );
                context.block.add( stmt );
            }
            else if( children[i].getType().equals( "computes_for" ) ){
                ComputeStmt stmt = read_computes_for( children[i] );
                context.block.add( stmt );
            }
            else if( children[i].getType().equals( "sleeps_for" ) ){
                ComputeStmt stmt = read_sleeps_for( children[i] );
                context.block.add( stmt );
            }
            else if( children[i].getType().equals( "touch_stmt" ) ){
                ComputeStmt stmt = read_touch_stmt( children[i] );
                context.block.add( stmt );
            }
            else if( children[i].getType().equals( "reset_stmt" ) ){
                MeasureBlock block = read_reset_stmt( children[i] );
                context.block.add( block );
                context.block = block;
            }
            else if( children[i].getType().equals( "log_stmt" ) ){
                read_log_stmt( children[i], context );

                // the measure block is now closed so return to parent block
                AbstractComponent parent = 
                    (AbstractComponent)context.block.getParent();
                if( !(parent instanceof Program) )
                    context.block = (Block)parent;
            }
            else if( children[i].getType().equals( "log_flush_stmt" ) )
                read_log_flush_stmt( children[i], context );
            else if( children[i].getType().equals( "sync_stmt" ) )
                context.block.add( read_sync_stmt( children[i] ) );
            else if( children[i].getType().equals( "awaits_completion" ) )
                context.block.add( read_awaits_completion( children[i] ) );
            else if( children[i].getType().equals( "assert_stmt" ) )
                context.block.add( read_assert_stmt( children[i] ) );
            else if( children[i].getType().equals( "output_stmt" ) )
                context.block.add( read_output_stmt( children[i] ) );
            else if( children[i].getType().equals( "reduce_stmt" ) )
                context.block.add( read_reduce_stmt( children[i] ) );
            else if( children[i].getType().equals( "touch_buffer_stmt" ) )
                context.block.add( read_touch_buffer_stmt( children[i] ) );
            else if( children[i].getType().equals( "processor_stmt" ) )
                context.block.add( read_processor_stmt( children[i] ) );
            else if( children[i].getType().equals( "backend_stmt" ) )
                context.block.add( read_backend_stmt( children[i] ) );
            else if( children[i].getType().equals( "for_count" ) )
                read_for_count( children[i], context );
            else if( children[i].getType().equals( "for_each" ) )
                read_for_each( children[i], context );
            else if( children[i].getType().equals( "for_time" ) )
                read_for_time( children[i], context );
            else if( children[i].getType().equals( "if_stmt" ) )
                read_if_stmt( children[i], context );
            else if( children[i].getType().equals( "let_stmt" ) )
                read_let_stmt( children[i], context );
            else if( children[i].getType().equals( "simple_stmt_list" ) )
                read_simple_stmt_list( children[i], context );
            else
                assert false;
        }
    }

    private void read_if_stmt( AST node, Context context ){
        assert node.getType().equals( "if_stmt" );

        IfBlock ifBlock = new IfBlock( program );
        attachComments( ifBlock, node );
        ifBlock.setLineNumber( node.getLineNumber() );
        context.block.add( ifBlock );

        ifBlock.setCondition( readExpr( node.getLeft() ) );

        // save context
        Block previousBlock = context.block;

        context.block = ifBlock.getThenBlock();
        read_simple_stmt( node.getChild( 1 ), context );

        if( node.getChild( 2 ) != null ){
            context.block = ifBlock.getOtherwiseBlock();
            read_simple_stmt( node.getChild( 2 ), context );
        }

        // restore context
        context.block = previousBlock;
    }

    private OtherStmt read_processor_stmt( AST node ){
        assert node.getType().equals( "processor_stmt" );

        OtherStmt stmt = new OtherStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setCode( node.getCode() );
        stmt.setStmtType( "processor_stmt" );
        return stmt;
    }

    private void read_log_flush_stmt( AST node, Context context ){
        assert node.getType().equals( "log_flush_stmt" );

        // make sure that the last component in the current block is a loop
        // then set compute aggregates on the loop
        Loop loop = (Loop)context.block.componentAt( context.block.numComponents() - 1 );
        TaskGroup taskGroup = readTaskGroup( node.getLeft(), true );
        loop.setComputeAggregatesGroup( taskGroup );
    }

    private MeasureBlock read_reset_stmt( AST node ){
        assert node.getType().equals( "reset_stmt" );
        MeasureBlock block = new MeasureBlock( program );
        block.setTaskGroup( readTaskGroup( node.getLeft(), true ) );
        return block;
    }

    private void read_log_stmt( AST node, Context context ){
        assert node.getType().equals( "log_stmt" );

        MeasureBlock block;
        if( context.block instanceof MeasureBlock ){
            block = (MeasureBlock)context.block;
            block.setTaskGroup( readTaskGroup( node.getLeft(), true ) );
        }
        else{
            block = new MeasureBlock( program );
            block.setTaskGroup( readTaskGroup( node.getLeft(), true ) );
            block.setReset( false );
            context.block.add( block );
        }
        block.setLineNumber( node.getLineNumber() );
        read_log_expr_list( node.getRight(), block );
    }

    private OtherStmt read_touch_buffer_stmt( AST node ){
        assert node.getType().equals( "touch_buffer_stmt" );
        
        OtherStmt stmt = new OtherStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setCode( node.getCode() );
        stmt.setStmtType( "touch_buffer_stmt" );
        return stmt;
    }

    private OtherStmt read_output_stmt( AST node ){
        assert node.getType().equals( "output_stmt" );

        OtherStmt stmt = new OtherStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setCode( node.getCode() );
        stmt.setStmtType( "output_stmt" );
        return stmt;
    }

    private OtherStmt read_backend_stmt( AST node ){
        assert node.getType().equals( "backend_stmt" );
        
        OtherStmt stmt = new OtherStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setCode( node.getCode() );
        stmt.setStmtType( "backend_stmt" );
        return stmt;
    }

    private String read_string_or_expr_list( AST node ){
        assert node.getType().equals( "string_or_expr_list" );

        AST children[] = node.getChildren();
        String code = "";
        for( int i = 0; i < children.length; i++ ){
            if( i > 0 )
                code += " and ";
            if( children[i].getType().equals( "expr" ) )
                code += readExpr( children[i] );
            else if( children[i].getType().equals( "string_or_log_comment" ) )
                code += read_string_or_log_comment( children[i] );
            else
                assert false; 
        }
        return code;
    }

    private String read_string_or_log_comment( AST node ){
        assert node.getType().equals( "string_or_log_comment" );
        
        return "\"" + read_string( node.getLeft() ) + "\"";
    }

    private void read_log_expr_list( AST node, MeasureBlock block ){
        assert node.getType().equals( "log_expr_list" );

        AST children[] = node.getChildren();
        for( int i = 0; i < children.length; i++ )
            read_log_expr_list_elt( children[i], block );
    }

    private void read_log_expr_list_elt( AST node, MeasureBlock block ){
        assert node.getType().equals( "log_expr_list_elt" );
        
        MeasureExpression expression = new MeasureExpression();
        read_aggregate_expr( node.getLeft(), expression );
        read_string_or_log_comment( node.getRight(), expression );
        block.addMeasureExpression( expression );
    }

    private void read_aggregate_expr( AST node, MeasureExpression expression ){
        assert node.getType().equals( "aggregate_expr" );
        if( node.getAttr().equals( "no_aggregate" ) ){
            expression.aggregate = "";
            expression.expression = readExpr( node.getLeft() );
        }
        else{
            read_aggregate_func( node.getLeft(), expression );
            expression.expression = readExpr( node.getRight() );
        }
    }
    
    private void read_string_or_log_comment( AST node, 
                                             MeasureExpression expression ){
        assert node.getType().equals( "string_or_log_comment" );
        
        expression.comment = read_string( node.getLeft() );
    }

    private void read_aggregate_func( AST node, MeasureExpression expression ){
        assert node.getType().equals( "aggregate_func" );
        String func = node.getAttr();
        if( func.equals( "ONLY" ) ){
            expression.aggregate = "the";
        }
        else if( func.equals( "mean" ) ){
            expression.aggregate = "the mean of";
        }
        else if( func.equals( "geometric_mean" ) ){
            expression.aggregate = "the geometric mean of";
        }
        else if( func.equals( "harmonic_mean" ) ){
            expression.aggregate = "the harmonic mean of";
        }
        else if( func.equals( "median" ) ){
            expression.aggregate = "the median of";
        }
        else if( func.equals( "stdev" ) ){
            expression.aggregate = "the standard deviation of";
        }
        else if( func.equals( "variance" ) ){
            expression.aggregate = "the variance of";
        }
        else if( func.equals( "sum" ) ){
            expression.aggregate = "the sum of";
        }
        else if( func.equals( "minimum" ) ){
            expression.aggregate = "the minimum of";
        }
        else if( func.equals( "maximum" ) ){
            expression.aggregate = "the maximum of";
        }
        else if( func.equals( "final" ) ){
            expression.aggregate = "the final";
        }
        else if( func.equals( "HISTOGRAM" ) ){
            expression.aggregate = "a histogram of";
        }
        else
            assert false;
    }

    private CommunicationStmt read_send_stmt( AST node ){
        assert node.getType().equals( "send_stmt" );
        
        CommunicationStmt commStmt = new CommunicationStmt( program );
        attachComments( commStmt, node );
        commStmt.setLineNumber( node.getLineNumber() );
        commStmt.clear();

        AST children[] = node.getChildren();

        // source
        TaskGroup taskGroup = readTaskGroup( children[0], true );
        commStmt.setSourceGroup( taskGroup.toCodeSource() );

        read_message_spec( children[1], commStmt, true );
        read_send_attrs( children[2], commStmt );

        // target
        taskGroup = readTaskGroup( children[3], false );
        commStmt.setTargetGroup( taskGroup.toCodeTarget() );
        
        read_message_spec( children[4], commStmt, false );

        read_receive_attrs( children[5], commStmt );
        
        return commStmt;
    }

    private CommunicationStmt read_receive_stmt( AST node ){
        assert node.getType().equals( "receive_stmt" );
        CommunicationStmt commStmt = new CommunicationStmt( program );
        attachComments( commStmt, node );
        commStmt.setLineNumber( node.getLineNumber() );
        commStmt.clear();
        
        AST children[] = node.getChildren();

        // source
        TaskGroup taskGroup = readTaskGroup( children[2], true );
        commStmt.setSourceGroup( taskGroup.toCodeSource() );
        
        read_receive_attrs( children[3], commStmt );

        commStmt.setUnsuspecting( true );

        // target
        taskGroup = readTaskGroup( children[0], false );
        commStmt.setTargetGroup( taskGroup.toCodeTarget() );
        
        read_message_spec( children[1], commStmt, false );
        
        return commStmt;
    }

    private TaskGroup readTaskGroup( AST node, boolean isSource ){
        TaskGroup taskGroup = new TaskGroup( program );
        if( isSource ){
            taskGroup.setSource( node.getCode() );
        }
        else
            taskGroup.setTarget( node.getCode() );
        return taskGroup;
    }

    private void read_message_spec( AST node, CommunicationStmt stmt, 
                                    boolean isSource ){
        assert node.getType().equals( "message_spec" );
        
        AST children[] = node.getChildren();

        if( isSource ){
            stmt.setMessageCount( read_item_count( children[0] ) );
            stmt.setSourceUniqueBuffer( read_unique( children[1] ) );
            ItemSize itemSize = read_item_size( children[2] );
            stmt.setMessageSize( itemSize.size );
            stmt.setMessageSizeUnits( itemSize.units );
            Alignment alignment = 
                read_message_alignment( children[3] );

            if( node.getAttr().equals( "1" ) && 
                alignment.mode.equals( "aligned" ) )
                alignment.mode = "misaligned";

            stmt.setSourceAlignment( alignment.alignment );
            stmt.setSourceAlignmentUnits( alignment.units );
            stmt.setSourceAlignmentMode( alignment.mode );

            stmt.setSourceVerificationOrTouching( read_touching_type( children[4]) );
            stmt.setSourceBuffer( read_buffer_number( children[7] ) );
        }
        else{
            stmt.setTargetUniqueBuffer( read_unique( children[1] ) );
            stmt.setTargetVerificationOrTouching( read_touching_type( children[4]) );
            
            Alignment alignment = 
                read_message_alignment( children[3] );

            if( node.getAttr().equals( "1" ) && 
                alignment.mode.equals( "aligned" ) )
                alignment.mode = "misaligned";

            stmt.setTargetAlignment( alignment.alignment );
            stmt.setTargetAlignmentUnits( alignment.units );
            stmt.setTargetAlignmentMode( alignment.mode );


            stmt.setTargetVerificationOrTouching( read_touching_type( children[4]) );

            stmt.setTargetBuffer( read_recv_buffer_number( children[7] ) );
        }
        
    }

    private String read_item_count( AST node ){
        assert node.getType().equals( "item_count" );
        if( node.getCode().toLowerCase().equals( "an" ) ||
            node.getCode().toLowerCase().equals( "a" ) )
            return "1";
        return node.getCode();
    }

    private ItemSize read_item_size( AST node ){
        assert node.getType().equals( "item_size" );
        ItemSize itemSize = new ItemSize();

        // when message size is unspecified, use 0 bytes
        if( node.getLeft() == null ){
            itemSize.size = "0";
            itemSize.units = "bytes";
        }
        // e.g: "integer sized"
        else if( node.getLeft().getType().equals( "data_type" ) ){
            itemSize.size = "1";
            itemSize.units = read_data_type( node.getLeft() );
        }
        else{
            itemSize.size = readExpr( node.getLeft() );
            itemSize.units = read_data_multiplier( node.getRight() );
        }
        return itemSize;
    }

    private String read_data_multiplier( AST node ){
        assert node.getType().equals( "data_multiplier" );
        return node.getAttr().toLowerCase();
    }

    private void read_send_attrs( AST node, CommunicationStmt stmt ){
        assert node.getType().equals( "send_attrs" );

        String attrs[] = node.getAttrArray();
        for( int i = 0; i < attrs.length; i++ ){
            if( attrs[i].equals( "asynchronously" ) )
                stmt.setSourceAsync( true );
            else if( attrs[i].equals( "unsuspecting" ) )
                stmt.setUnsuspecting( true );
            else
                assert false;
        }
    }

    private void read_send_attrs( AST node, MulticastStmt stmt ){
        assert node.getType().equals( "send_attrs" );

        String attrs[] = node.getAttrArray();
        for( int i = 0; i < attrs.length; i++ ){
            if( attrs[i].equals( "asynchronously" ) )
                stmt.setAsync( true );
            else
                assert false;
        }
    }

    private void read_receive_attrs( AST node, CommunicationStmt stmt ){
        assert node.getType().equals( "receive_attrs" );
        
        String attrs[] = node.getAttrArray();
        for( int i = 0; i < attrs.length; i++ ){
            if( attrs[i].equals( "asynchronously" ) )
                stmt.setTargetAsync( true );
            else if( attrs[i].equals( "unsuspecting" ) )
                stmt.setUnsuspecting( true );
            else
                assert false;
        }
    }

    private boolean read_unique( AST node ){
        assert node.getType().equals( "unique" );

        if( node.getAttr().equals( "0" ) )
            return false;
        else
            return true;
    }

    private Alignment read_message_alignment( AST node ){
        assert node.getType().equals( "message_alignment" );

        if( node.getAttr().equals( "unspecified" ) ||
            node.getLeft() == null )
            return new Alignment();
        
        if( node.getLeft().getType().equals( "byte_count" ) )
            return readAlignment_byte_count( node.getLeft() );
        else if( node.getLeft().getType().equals( "data_type" ) )
            return readAlignment_data_type( node.getLeft() );
        else{
            assert false;
            return null;
        }
    }

    private Alignment readAlignment_data_type( AST node ){
        assert node.getType().equals( "data_type" );

        Alignment alignment = new Alignment();
        alignment.alignment = "1";
        String attr = node.getAttr().toLowerCase();
        if( attr.equals( "default" ) )
            alignment.mode = "unaligned";
        else {
            alignment.mode = "aligned";
            alignment.units = attr;
        }

        return alignment;
    }

    private Alignment readAlignment_byte_count( AST node ){
        assert node.getType().equals( "byte_count" );

        Alignment alignment = new Alignment();
        alignment.alignment = readExpr( node.getLeft() );
        alignment.units = read_data_multiplier( node.getRight() );
        alignment.mode = "aligned";
        return alignment;
    }
    
    private String read_touching_type( AST node ){
        assert node.getType().equals( "touching_type" );
        if( node.getLeft().getType().equals( "no_touching" ) )
            return read_no_touching( node.getLeft() );
        else if( node.getLeft().getType().equals( "touching" ) )
            return read_touching( node.getLeft() );
        else if( node.getLeft().getType().equals( "verification" ) )
            return read_verification( node.getLeft() );
        else{
            assert false;
            return null;
        }
    }
    
    private String read_no_touching( AST node ){
        assert( node.getType().equals( "no_touching" ) );
        return "without data touching";
    }

    private String read_touching( AST node ){
        assert( node.getType().equals( "touching" ) );
        return "with data touching";
    }

    private String read_verification( AST node ){
        assert( node.getType().equals( "verification" ) );
        return "with verification";
    }

    private String read_buffer_number( AST node ){
        assert( node.getType().equals( "buffer_number" ) );
        if( node.getAttr().equals( "implicit" ) )
            return "default";
        else
            return readExpr( node.getLeft() );
    }

    private String read_recv_buffer_number( AST node ){
        assert( node.getType().equals( "recv_buffer_number" ) );
        if( node.getAttr().equals( "implicit" ) )
            return "default";
        else
            return readExpr( node.getLeft() );
    }

    private ComputeStmt read_computes_for( AST node ){
        assert node.getType().equals( "computes_for" );

        ComputeStmt compStmt = new ComputeStmt( program );
        attachComments( compStmt, node );
        compStmt.setLineNumber( node.getLineNumber() );
        compStmt.setType( ComputeStmt.TYPE_COMPUTES_FOR );

        AST children[] = node.getChildren();
        
        // task group
        TaskGroup taskGroup = readTaskGroup( children[0], true );
        compStmt.setTaskGroup( taskGroup.toCodeSource() );

        // time expression
        String time = readExpr( children[1] );
        compStmt.setComputeTime( time );

        // time units
        String timeUnit = read_time_unit( children[2] );
        compStmt.setComputeTimeUnits( timeUnit );

        return compStmt;
    }

    private ComputeStmt read_sleeps_for( AST node ){
        assert node.getType().equals( "sleeps_for" );

        ComputeStmt compStmt = new ComputeStmt( program );
        attachComments( compStmt, node );
        compStmt.setLineNumber( node.getLineNumber() );
        compStmt.setType( ComputeStmt.TYPE_SLEEPS_FOR );

        AST children[] = node.getChildren();
        
        // task group
        TaskGroup taskGroup = readTaskGroup( children[0], true );
        compStmt.setTaskGroup( taskGroup );

        // time expression
        String time = readExpr( children[1] );
        compStmt.setSleepTime( time );

        // time units
        String timeUnit = read_time_unit( children[2] );
        compStmt.setSleepTimeUnits( timeUnit );

        return compStmt;
    }

    private ComputeStmt read_touch_stmt( AST node ){
        assert node.getType().equals( "touch_stmt" );

        ComputeStmt compStmt = new ComputeStmt( program );
        attachComments( compStmt, node );
        compStmt.setLineNumber( node.getLineNumber() );
        compStmt.setType( ComputeStmt.TYPE_TOUCHES_MEMORY );

        AST children[] = node.getChildren();
        
        // task group
        TaskGroup taskGroup = readTaskGroup( children[0], true );
        compStmt.setTaskGroup( taskGroup );
        
        // after the following, i points to the item_size child
        int i = 1;
        if( children[1].getType().equals( "expr" ) ){
            compStmt.setTouchCount( readExpr( children[1] ) );
            compStmt.setTouchCountUnits( read_data_type( children[2] ) );
            i = 3;
        }
        readTouch_item_size( children[i], compStmt );
        if( children[i+1].getLeft() == null )
            compStmt.setTouchTimes( "1" );
        else
            compStmt.setTouchTimes( readExpr( children[i+1].getLeft() ) );
        
        read_stride( children[i+2], compStmt );
        return compStmt;
    }

    private String read_time_unit( AST node ){
        assert node.getType().equals( "time_unit" );
        return node.getAttr().toLowerCase();
    }

    private String read_data_type( AST node ){
        assert node.getType().equals( "data_type" );
        return node.getAttr().toLowerCase();
    }
    
    private void readTouch_item_size( AST node, ComputeStmt stmt ){
        assert node.getType().equals( "item_size" );
        stmt.setTouchRegion( readExpr( node.getLeft() ) );
        stmt.setTouchRegionUnits( read_data_multiplier( node.getRight() ) );
    }

    private void read_stride( AST node, ComputeStmt stmt ){
        assert node.getType().equals( "stride" );
        String attr = node.getAttr().toLowerCase();

        if( attr.equals( "default" ) )
            stmt.setTouchStride( "default" );
        else if( attr.equals( "specified" ) ){
            stmt.setTouchStride( readExpr( node.getLeft() ) );
            stmt.setTouchStrideUnits( read_data_type( node.getRight() ) );
        }
        else
            assert false;
    }
    
    private SynchronizeStmt read_sync_stmt( AST node ){
        assert node.getType().equals( "sync_stmt" );
        SynchronizeStmt stmt = new SynchronizeStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setTaskGroup( readTaskGroup( node.getLeft(), true ) );
        return stmt;
    }

    private WaitStmt read_awaits_completion( AST node ){
        assert node.getType().equals( "awaits_completion" );
        WaitStmt stmt = new WaitStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setTaskGroup( readTaskGroup( node.getLeft(), true ) );
        return stmt;
    }

    private OtherStmt read_assert_stmt( AST node ){
        assert node.getType().equals( "assert_stmt" );
        OtherStmt stmt = new OtherStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setCode( "Assert that \"" + read_string( node.getLeft() ) +
                      "\" with " + readExpr( node.getRight() ) );
        stmt.setStmtType( "assert_stmt" );
        return stmt;
    }

    private ReduceStmt read_reduce_stmt( AST node ){
        assert node.getType().equals( "reduce_stmt" );
        ReduceStmt stmt = new ReduceStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );
        stmt.setSourceGroup( readTaskGroup( node.getChild( 0 ), true ).toCodeSource() );
        read_reduce_message_spec( node.getChild( 1 ), stmt, true );
        read_reduce_message_spec( node.getChild( 2 ), stmt, false );
        stmt.setTargetGroup( readTaskGroup( node.getChild( 3 ), false ).toCodeTarget() );
        return stmt;
    }
    
    private void read_reduce_message_spec( AST node, ReduceStmt stmt, 
                                           boolean isSource ){
        assert node.getType().equals( "reduce_message_spec" );

        AST children[] = node.getChildren();

        if( isSource ){
            stmt.setSourceCount( read_item_count( children[0] ) );
            stmt.setSourceUniqueBuffer( read_unique( children[1] ) );
            
            Alignment alignment = 
                read_message_alignment( children[2] );

            if( node.getAttr().equals( "1" ) && 
                alignment.mode.equals( "aligned" ) )
                alignment.mode = "misaligned";

            stmt.setSourceAlignment( alignment.alignment );
            stmt.setSourceAlignmentUnits( alignment.units );
            stmt.setSourceAlignmentMode( alignment.mode );
            stmt.setSourceUnits( read_data_type( children[3] ) );
            if( read_touching_type( children[4] ).equals( "without data touching" ) )
                stmt.setSourceDataTouching( false );
            else
                stmt.setSourceDataTouching( true );
            stmt.setSourceBuffer( read_buffer_number( children[7] ) );
        }
        else{
            stmt.setTargetCount( read_item_count( children[0] ) );
            stmt.setTargetUniqueBuffer( read_unique( children[1] ) );

            Alignment alignment = 
                read_message_alignment( children[2] );

            if( node.getAttr().equals( "1" ) && 
                alignment.mode.equals( "aligned" ) )
                alignment.mode = "misaligned";

            stmt.setTargetAlignment( alignment.alignment );
            stmt.setTargetAlignmentUnits( alignment.units );
            stmt.setTargetAlignmentMode( alignment.mode );
            
            stmt.setTargetUnits( read_data_type( children[3] ) );
            
            if( read_touching_type( children[4] ).equals( "without data touching" ) )
                stmt.setTargetDataTouching( false );
            else
                stmt.setTargetDataTouching( true );


            stmt.setTargetBuffer( read_buffer_number( children[7] ) );
        }
            
        
    }

    
    private MulticastStmt read_mcast_stmt( AST node ){
        assert node.getType().equals( "mcast_stmt" );
        MulticastStmt stmt = new MulticastStmt( program );
        attachComments( stmt, node );
        stmt.setLineNumber( node.getLineNumber() );

        AST children[] = node.getChildren();
        
        // source
        stmt.setSourceGroup( readTaskGroup( children[0], true ).toCodeSource() );
        
        // message spec
        read_message_spec( children[1], stmt );

        // target
        TaskGroup targetGroup = readTaskGroup( children[2], false );
        stmt.setTargetGroup( targetGroup.toCodeTarget() );
        
        // send attrs
        read_send_attrs( children[3], stmt );
        
        return stmt;
    }

    private void read_message_spec( AST node, MulticastStmt stmt ){
        assert node.getType().equals( "message_spec" );
        
        AST children[] = node.getChildren();

        stmt.setCount( read_item_count( children[0] ) );
        stmt.setUniqueBuffer( read_unique( children[1] ) );
        ItemSize itemSize = read_item_size( children[2] );
        stmt.setMessageSize( itemSize.size );
        stmt.setMessageSizeUnits( itemSize.units );
        Alignment alignment = read_message_alignment( children[3] );

        if( node.getAttr().equals( "1" ) && 
            alignment.mode.equals( "aligned" ) )
            alignment.mode = "misaligned";

        stmt.setAlignment( alignment.alignment );
        stmt.setAlignmentUnits( alignment.units );
        stmt.setAlignmentMode( alignment.mode );
        
        stmt.setVerificationOrTouching( read_touching_type( children[4]) );
        stmt.setBuffer( read_buffer_number( children[7] ) );
    }

    private String read_func_call( AST node ){
        assert node.getType().equals( "func_call" );
        
        return node.getAttr().toLowerCase() + "(" + 
            readFuncParams( node.getLeft(), "" ) + ")";
    }

    private String readFuncParams( AST node, String code ){
        if( !code.equals( "" ) )
            code += ", ";

        if( node.getType().equals( "," ) )
            return code + readExpr( node.getLeft() ) + 
                ", " + readFuncParams( node.getRight(), code );
        else
            return code + readExpr( node );
        
    }

    private String read_ifelse_expr( AST node ){
        assert node.getType().equals( "ifelse_expr" );

        return readExpr( node.getLeft() ) + " if " +
            readExpr( node.getRight() ) + " otherwise " +
            readExpr( node.getChild( 2 ) );
    }

    private String read_real( AST node ){
        assert node.getType().equals( "real" );

        return "real(" + readExpr( node.getLeft() ) + ")";
    }

    // attach comments from current line number through line number
    // contained in node to component
    private void attachComments( AbstractComponent component, AST node ){
        String preComments = "";

        // attach the comments preceding the component
        while( line < node.getLineNumber() ){
            PyString pyString = 
                (PyString)comments.__finditem__( new PyInteger( line ) );
            if( pyString != null )
                preComments += pyString.toString() + "\n";

            line++;
        }

        // attach the comments occupying the same line
        if( !preComments.equals( "" ) )
            component.setPreComments( preComments );

        PyString pyString = 
            (PyString)comments.__finditem__( new PyInteger( line ) );
        if( pyString != null )
            component.setComment( pyString.toString() );
        line++;
    }
                

    // similar to the above, but attach comments to a comesFrom
    private void attachComments( ComesFrom comesFrom, AST node ){
        String preComments = "";
        while( line < node.getLineNumber() ){
            PyString pyString = 
                (PyString)comments.__finditem__( new PyInteger( line ) );
            if( pyString != null )
                preComments += pyString.toString() + "\n";
            line++;
        }
        if( !preComments.equals( "" ) )
            comesFrom.preComments = preComments;
        PyString pyString = 
            (PyString)comments.__finditem__( new PyInteger( line ) );
        if( pyString != null )
            comesFrom.comment = pyString.toString();
        line++;
    }

    // attach the comments that appear at the very beginning of the
    // program file to the program
    private void readStartComments( String programString ){
        program.setStartComments( null );
        
        line = 1;
        int i = 1;
        for( i = 1; i < programString.length(); i++ ){
            if( programString.charAt( i ) == '\n' ){
                if( programString.charAt( i - 1 ) == '\n' )
                    break;
                line++;
            }
        }
        if( i == programString.length() ){
            line = 1;
            return;
        }

        PyList keys = (PyList)comments.keys();
        keys.sort();
        String startComments = "";
        for( i = 0; i < keys.__len__(); i++ ){
            PyInteger key = (PyInteger)keys.__finditem__( i );
            if( key.getValue() < line ){
                PyString pyString = (PyString)comments.__finditem__( key );
                if( pyString != null )
                    startComments += pyString.toString() + "\n";
            }
        }
        if( !startComments.equals( "" ) )
            program.setStartComments( startComments );
    }

    // attach the remaining comments in the file to the program
    private void readEndComments(){
        program.setEndComments( null );
        
        PyList keys = (PyList)comments.keys();
        keys.sort();
        String endComments = "";
        for( int i = 0; i < keys.__len__(); i++ ){
            PyInteger key = (PyInteger)keys.__finditem__( i );
            if( key.getValue() >= line ){
                PyString pyString = (PyString)comments.__finditem__( key );
                if( pyString != null )
                    endComments += pyString.toString() + "\n";
            }
        }
        if( !endComments.equals( "" ) )
            program.setEndComments( endComments );
    }
    
}

