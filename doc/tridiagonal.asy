/*
 * Draw a matrix with all but the tridiagonal grayed out
 * By Scott Pakin <pakin@lanl.gov>
 */

// Set some figure parameters.
real fsize = 10;               // Font size in points
real edge_len = 2*fsize - 2;   // Cell edge length in points
real matrix_size = 10;         // Matrix edge length in cells

// Shade "uninteresting" values.
for (int cell=0; cell<matrix_size*matrix_size; ++cell) {
  real x = cell % matrix_size;
  real inv_y = floor(cell / matrix_size);
  real y = matrix_size - inv_y - 1;
  if (abs(inv_y - x) > 1)
    fill(scale(edge_len)*shift(x,y)*unitsquare, gray(0.5));
}

// Draw the grid.
for (int row=0; row<matrix_size+1; ++row)
  draw((0, row*edge_len)--(matrix_size*edge_len, row*edge_len));
for (int col=0; col<matrix_size+1; ++col)
  draw((col*edge_len, 0)--(col*edge_len, matrix_size*edge_len));

// Fill in the numbers.
defaultpen(fontsize(fsize));
for (int cell=0; cell<matrix_size*matrix_size; ++cell) {
  real x = cell % matrix_size;
  real y = matrix_size - floor(cell / matrix_size) - 1;
  label(string(cell), (x*edge_len+edge_len/2, y*edge_len+edge_len/2));
}
