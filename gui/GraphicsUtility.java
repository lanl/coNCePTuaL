/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: graphics utility
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class contains shared utility methods for painting on a
 * Graphics object such as drawing arrows. It also contains shared style
 * definitions such as the selected components color, line strokes, etc.
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2011, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2011).  Los Alamos National Security, LLC.  This software
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

public class GraphicsUtility {

    private Graphics2D graphics2D;

    // constants for pre-defined stroke types
    static final int STROKE_NORMAL = 0;
    static final int STROKE_BOLD = 1;
    static final int STROKE_DASH = 2;
    static final int STROKE_BOLD_DASH = 3;
    static final int STROKE_HIGHLIGHT = 4;
    static final int STROKE_CURSOR = 5;

    public GraphicsUtility( Graphics graphics ){
        graphics2D = (Graphics2D)graphics;
    }

    public void setStroke( int type ){
        BasicStroke stroke = null;
        switch( type ){
        case STROKE_NORMAL:
            stroke = new BasicStroke( 1.0f, BasicStroke.CAP_BUTT,
                                      BasicStroke.JOIN_MITER, 1.0f,
                                      null, 0.0f );
            break;
        case STROKE_BOLD:
            stroke = new BasicStroke( 2.0f, BasicStroke.CAP_BUTT,
                                      BasicStroke.JOIN_MITER, 1.0f,
                                      null, 0.0f );
            break;
        case STROKE_DASH:
            float[] dash = {1.0f, 5.0f, 5.0f, 5.0f};
            stroke = new BasicStroke( 1.0f, BasicStroke.CAP_BUTT,
                                      BasicStroke.JOIN_MITER, 1.0f,
                                      dash, 0.0f );
            break;
        case STROKE_BOLD_DASH:
            float[] dash1 = {5.0f, 5.0f, 5.0f, 5.0f};
            stroke = new BasicStroke( 2.0f, BasicStroke.CAP_BUTT,
                                      BasicStroke.JOIN_MITER, 1.0f,
                                      dash1, 0.0f );
            break;

        case STROKE_HIGHLIGHT:
            stroke = new BasicStroke( 10.0f, BasicStroke.CAP_BUTT,
                                      BasicStroke.JOIN_MITER, 1.0f,
                                      null, 0.0f );
            break;
        case STROKE_CURSOR:
            float []dotDash = {10.0f, 5.0f, 5.0f, 5.0f};
            stroke = new BasicStroke( 4.0f, BasicStroke.CAP_BUTT,
                                      BasicStroke.JOIN_MITER, 1.0f,
                                      dotDash, 0.0f );
            break;
        }
        if( stroke != null )
            graphics2D.setStroke( stroke );
    }

    // draw an anti-aliased line from (x1,y1) to (x2,y2)
    public void drawLine( int x1, int y1, int x2, int y2 ){
        graphics2D.setRenderingHint( RenderingHints.KEY_ANTIALIASING,
                                     RenderingHints.VALUE_ANTIALIAS_ON );
        graphics2D.drawLine( x1, y1, x2, y2 ) ;
        graphics2D.setRenderingHint( RenderingHints.KEY_ANTIALIASING,
                                     RenderingHints.VALUE_ANTIALIAS_OFF );
    }

    // draw an anti-aliased arrow from (x1,y1) to (x2,y2)
    public void drawArrow( float width, int x1, int y1, int x2, int y2 )  {
        graphics2D.setRenderingHint( RenderingHints.KEY_ANTIALIASING,
                                     RenderingHints.VALUE_ANTIALIAS_ON );
        float theta = 0.423f;
        int[] xPoints = new int[3];
        int[] yPoints = new int[3];
        float[] vecLine = new float[2];
        float[] vecLeft = new float[2];
        float fLength;
        float th;
        float ta;
        float baseX, baseY;

        xPoints[0] = x2;
        yPoints[0] = y2;

        // build the line vector
        vecLine[0] = (float)xPoints[0] - x1;
        vecLine[1] = (float)yPoints[0] - y1;

        // build the arrow base vector - normal to the line
        vecLeft[0] = -vecLine[1];
        vecLeft[1] = vecLine[0];

        // setup length parameters
        fLength = (float)Math.sqrt( vecLine[0] * vecLine[0] +
                                    vecLine[1] * vecLine[1] );
        th = width / ( 2.0f * fLength );
        ta = width / ( 2.0f * ( (float)Math.tan( theta ) / 2.0f ) * fLength );

        // find the base of the arrow
        baseX = ((float)xPoints[0] - ta * vecLine[0]);
        baseY = ((float)yPoints[0] - ta * vecLine[1]);

        // build the points on the sides of the arrow
        xPoints[1] = (int)(baseX + th * vecLeft[0]);
        yPoints[1] = (int)(baseY + th * vecLeft[1]);
        xPoints[2] = (int)(baseX - th * vecLeft[0]);
        yPoints[2] = (int)(baseY - th * vecLeft[1]);

        graphics2D.drawLine( x1, y1, (int)baseX, (int)baseY );
        graphics2D.fillPolygon( xPoints, yPoints, 3 );
        graphics2D.setRenderingHint( RenderingHints.KEY_ANTIALIASING,
                                     RenderingHints.VALUE_ANTIALIAS_OFF );
    }

    // draw an anti-aliased oval
    public void drawOval( int x, int y, int width, int height ){
        graphics2D.setRenderingHint( RenderingHints.KEY_ANTIALIASING,
                                     RenderingHints.VALUE_ANTIALIAS_ON );
        graphics2D.drawOval( x, y, width, height );
        graphics2D.setRenderingHint( RenderingHints.KEY_ANTIALIASING,
                                     RenderingHints.VALUE_ANTIALIAS_OFF );
    }

    public void drawUnknownBox( String label,
                                boolean selected,
                                TaskRow sourceRow,
                                TaskRow targetRow ){
        Rectangle sourceBounds = sourceRow.getGlobalBounds();
        Rectangle bounds = new Rectangle();
        bounds.x = sourceBounds.x + TaskRow.PADDING_X;
        bounds.y = sourceBounds.y + sourceBounds.height + 5;
        bounds.width = sourceBounds.width - TaskRow.PADDING_X*2;
        bounds.height = sourceBounds.height - 5;

        if( selected ){
            graphics2D.setColor( getSelectedColor() );
            setStroke( GraphicsUtility.STROKE_HIGHLIGHT );
            graphics2D.fillRect( bounds.x, bounds.y,
                                  bounds.width, bounds.height );
            graphics2D.setColor( Color.black );
            setStroke( GraphicsUtility.STROKE_NORMAL );
        }

        graphics2D.drawRect( bounds.x, bounds.y,
                             bounds.width, bounds.height );
        graphics2D.drawString( label, sourceBounds.x + TaskRow.PADDING_X + 5,
                               sourceBounds.y + sourceBounds.height + 21 );
    }

    // this defines the highlight color for selected components
    static Color getSelectedColor(){
        return new Color( 0.65f, 0.65f, 0.65f );
    }

}
