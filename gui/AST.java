/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: AST
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * AST is a wrapper around a PyObject and defines an interface for
 * manipulating an abstract syntax tree returned by the coNCePTuaL
 * parser.
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

import org.python.core.*;

public class AST {

    // the PyObject that contains the actual AST node
    private PyObject pyObject;

    // the parent AST node - needed for performing an upward traversal
    private AST parent;

    // construct a new AST from a PyObject returned by the parser
    public AST( PyObject pyObject, AST parent ){
        this.pyObject = pyObject;
        this.parent = parent;
    }

    // return the first child
    public AST getLeft(){
        return getChild( 0 );
    }
    
    // return the second child
    public AST getRight(){
        return getChild( 1 );
    }

    // return the child at index
    // or null if index is invalid
    public AST getChild( int index ){
        PyList children = (PyList)pyObject.__getattr__( "kids" );
        if( index > children.__len__() - 1 )
            return null;
        else
            return new AST( children.__finditem__( index ), this );
    }
    
    // return an array containing all children
    public AST[] getChildren(){
        PyList childrenList = (PyList)pyObject.__getattr__( "kids" );
        int size = childrenList.__len__();
        AST children[] = new AST[size];
        for( int i = 0; i < size; i++ )
            children[i] = new AST( childrenList.__finditem__( i ), this );
        return children;
    } 

    // return the type field
    public String getType(){
        return pyObject.__getattr__( "type" ).toString();
    }
    
    // return the attribute field as a string
    public String getAttr(){
        PyObject attr = pyObject.__getattr__( "attr" );

        // if attr is a long, then remove trailing L
        if( attr instanceof PyLong ){
            String attrString = attr.toString();
            return attrString.substring( 0, attrString.length() - 1 );
        }
        else
            return pyObject.__getattr__( "attr" ).toString();
    }

    // return the attribute field as an array of strings
    public String[] getAttrArray(){
        PyList attrPyList = (PyList)pyObject.__getattr__( "attr" );
        int size = attrPyList.__len__();
        String attrList[] = new String[size];
        for( int i = 0; i < size; i++ )
            attrList[i] = attrPyList.__finditem__( i ).toString();
        return attrList;
    }
    
    // return the attribute as an integer
    public int getAttrInt(){
        PyInteger pyInteger = (PyInteger)pyObject.__getattr__( "attr" );
        return pyInteger.getValue();
    }

    // return the parent of this AST node
    // parent may be null
    public AST getParent(){
        return parent;
    }

    // return the printable field - code that corresponds to this AST
    // sub-tree
    public String getCode(){
        return pyObject.__getattr__( "printable" ).toString();
    }

    // return the line number that this AST starts on
    public int getLineNumber(){
        return ((PyInteger)pyObject.__getattr__( "lineno0" )).getValue();
    }
    
}

