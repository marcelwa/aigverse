module top( x0 , x1 , y0 );
  input x0 , x1 ;
  output y0 ;
  wire n3 ;
  assign n3 = ~x0 & ~x1 ;
  assign y0 = ~n3 ;
endmodule
