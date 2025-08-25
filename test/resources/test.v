module top( y1, y2, a, b, c ) ;
  input a , b , c ;
  output y1;
  wire g0, g1 , g2 , g3 , g4 ;
  assign g0 = a ;
  assign g1 = ~c ;
  assign g3 = b ;
  assign g2 = g0 & g1 ;
  assign g4 = g3 | g2 ;
  assign y1 = g4 ;
endmodule
