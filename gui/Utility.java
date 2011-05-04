/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: utility
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class contains miscellaneous static utility functions
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
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;
import java.util.*;

public class Utility {

    // treats a and b as sets and returns their intersection
    // relies on the equals() method to determine equality
    public static Vector intersection( Vector a, Vector b ){
        Vector r = new Vector();
        for( int i = 0; i < a.size(); i++ ){
            for( int j = 0; j < b.size(); j++ ){
                if( a.elementAt( i ).equals( b.elementAt( j ) ) )
                    r.add( a );
            }
        }
        return r;
    }

    // treats a and b as sets and returns their union
    public static Vector union( Vector a, Vector b ){
        Vector r = new Vector();

        for( int i = 0; i < a.size(); i++ )
            r.add( a.elementAt( i ) );

        for( int i = 0; i < b.size(); i++ )
            r.add( b.elementAt( i ) );

        return r;
    }

    // treats a and b as sets and returns their difference
    public static Vector difference( Vector a, Vector b ){
        Vector r = new Vector();

        for( int i = 0; i < a.size(); i++ ){
            boolean inB = false;
            for( int j = 0; j < b.size(); j++ ){
                if( a.elementAt( i ).equals( b.elementAt( j ) ) ){
                    inB = true;
                    break;
                }
            }
            if( !inB )
                r.add( a.elementAt( i ) );
        }
        return r;
    }

    // return the proper plural or singular form of word
    // based and the text that precedes it
    // word should always be passed in its plural form
    // e.g:
    // wordForm( "1", "megabytes" ) => "megabyte"
    // wordForm( "10", "megabytes" ) => "megabytes"
    // wordForm( "all tasks", "sends" ) => "send"
    // wordForm( "task 1" "sends" ) => "sends"

    public static String wordForm( String pretext, String word ){

        if( pretext.matches( "^\\d+$" ) ){
            if( pretext.equals( "1" ) ){
                return word.substring( 0, word.length() - 1 );
            }
            else
                return word;
        }
        else if( pretext.toLowerCase().matches( "tasks .*" ) ||
                 pretext.toLowerCase().matches( ".* tasks .*" ) ||
                 pretext.toLowerCase().matches( ".* tasks" ) )
            return word.substring( 0, word.length() - 1 );
        return word;
    }


    // return the singular form of pluralWord
    public static String toSingular( String pluralWord ){
        if( pluralWord.matches( ".+s" ) ){
            return pluralWord.substring( 0, pluralWord.length() - 1 );
        }
        return pluralWord;
    }

    // modifies text so that it is a lexical identifier
    // e.g: "message size" => "message_size"
    public static String toIdentifier( String text ){
        String out = "";

        if( Character.isDigit( text.charAt( 0 ) ) )
            out += "_";

        for( int i = 0; i < text.length(); i++ ){
            if( Character.isJavaIdentifierPart( text.charAt( i ) ) )
                out += text.charAt( i );
            else if( text.charAt( i ) == ' ' )
                out += "_";
        }
        return out;
    }

    // recursively walk the AST node
    // and verify that each ident node is contained in scopeVariables
    // else returns false
    public static boolean verifyScopeVariables( AST node,
                                                Vector scopeVariables ){

        if( node.getType().equals( "task_expr" ) )
            return true;

        if( node.getType().equals( "ident" ) ){
            boolean found = false;
            for( int i = 0; i < scopeVariables.size(); i++ ){
                String variable = (String)scopeVariables.elementAt( i );
                if( variable.equals( node.getAttr() ) ){
                    found = true;
                    break;
                }
            }
            if( !found )
                return false;
        }

        AST children[] = node.getChildren();
        for( int i = 0; i < children.length; i++ ){
            if( !verifyScopeVariables( children[i], scopeVariables ) )
                return false;
        }

        return true;
    }

    // given a list of tasks, generate the task description string
    // e.g: 1,5,8 => "tasks t such that t = 1 \/ t = 5 \/ t = 8"
    // numTasks is the total number of tasks in the program
    public static String getTaskDescription( int numTasks, Vector tasks ){
        if( tasks.size() == 1 ){
            Task task = (Task)tasks.elementAt( 0 );
            return "task " + task.getID();
        }
        else if( tasks.size() == numTasks )
            return "all tasks";
        else{
            String taskDescription = "tasks t such that t is in {";
            for( int i = 0; i < tasks.size(); i++ ){
                Task task = (Task)tasks.elementAt( i );
                if( i > 0 )
                    taskDescription += ", ";
                taskDescription += task.getID();
            }
            taskDescription += "}";
            return taskDescription;
        }
    }

    // returns true if bounds is sufficiently contained within marquee
    static public boolean marqueeSelects( Rectangle marquee, Rectangle bounds ){
        if( marquee.x < bounds.x + bounds.width &&
            marquee.x + marquee.width > bounds.x + bounds.width &&
            marquee.y < bounds.y + bounds.height &&
            marquee.y + marquee.height > bounds.y + bounds.height )
            return true;
        else
            return false;
    }

    // returns true if the line segment (p1,p2) intersects
    // the rectangle rect
    static public boolean intersects( Point p1, Point p2,
                                      Rectangle rect ){

        // top edge
        if( intersects( p1, p2, new Point( rect.x, rect.y ),
                        new Point( rect.x + rect.width, rect.y ) ) )
            return true;

        // bottom edge
        if( intersects( p1, p2, new Point( rect.x, rect.y + rect.height ),
                        new Point( rect.x + rect.width, rect.y + rect.height ) ) )
            return true;

        // left edge
        if( intersects( p1, p2, new Point( rect.x, rect.y ),
                        new Point( rect.x, rect.y + rect.height ) ) )
            return true;


        // right edge
        if( intersects( p1, p2, new Point( rect.x + rect.width, rect.y ),
                        new Point( rect.x + rect.width, rect.y + rect.height ) ) )
            return true;


        return false;
    }

    // return true if the line segments (p1,p2) and (p3,p4) intersect
    static public boolean intersects( Point p1, Point p2,
                                      Point p3, Point p4 ){
        double ua = (double)((p4.x-p3.x)*(p1.y-p3.y)-(p4.y-p3.y)*(p1.x-p3.x))/
            ((p4.y-p3.y)*(p2.x-p1.x)-(p4.x-p3.x)*(p2.y-p1.y));
        double ub = (double)((p2.x-p1.x)*(p1.y-p3.y)-(p2.y-p1.y)*(p1.x-p3.x))/
            ((p4.y-p3.y)*(p2.x-p1.x)-(p4.x-p3.x)*(p2.y-p1.y));

        if( ua > 0 && ua < 1 && ub > 0 && ub < 1 )
            return true;

        return false;
    }

    // return true if the point p is contained in the rectangle rect
    static public boolean contains( Rectangle rect, Point p ){
        if( p.x > rect.x && p.x < rect.x + rect.width &&
            p.y > rect.y && p.y < rect.y + rect.height )
            return true;
        return false;
    }

    // attempt to extract the task number from a task expression "task n"
    // returns -1 on failure
    static public int getTask( String taskDescription ){
        if( !taskDescription.toLowerCase().matches( "^task \\d+$" ) )
            return -1;

        return Integer.parseInt( taskDescription.substring( 5, taskDescription.length() ) );
    }

}
