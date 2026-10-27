`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 26.10.2026 22:47:39
// Design Name: 
// Module Name: filter_control
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////
// create filter control block simple

module filter_control#(
parameter N = 255 , 
parameter ACC_W = 40 , 
parameter COEFF_FILE = "coeff_bass.mem"
)
(
input wire clk,
input wire rst,
input wire in_valid,
input wire signed [15:0] x_in,
output reg out_valid,
output reg signed [15:0] out 
    );
    localparam AW= $clog2(N);
    localparam [1:0] S_IDLE = 2'b00, S_MAC = 2'b01 , S_DONE= 2'b10 ;
    reg signed [15:0] coeff [0: N-1] ;
    reg signed [15:0] ring_buf [0: N-1] ; 
    initial $readmemh(COEFF_FILE, coeff);
    reg [1:0] state;  
    reg [AW -1: 0] wptr ;
    reg [AW -1:0] ridx ; 
   // reg [AW:0] k ; // current index 
(* dont_touch = "true" *) reg [AW:0] k; // current index
    reg [AW:0] cnt ; // count for number of samples
    reg signed [ACC_W -1:0] acc ;
    
    // do not optimize
    /*
    wire signed [15:0] c_k = coeff[k[AW-1:0]] ;
    wire signed  [15:0] x_r = ring_buf[ridx] ;
    wire signed [31:0] prod = c_k * x_r ; 
   
    */
 reg signed [31:0] prod ; 
    reg signed [ACC_W-1:0] shifted ; 
    reg signed [15:0] x_r ; 
    reg signed [15:0] c_k ;
  
    always@(posedge clk) begin 
    c_k <= coeff[k[AW-1:0]];
    x_r <= ring_buf[ridx] ;
    prod <= c_k * x_r ;
   end
    wire signed [ACC_W -1:0] shifted = acc >>> 15 ; 
    wire signed [15:0] sat = (shifted >  32767)? 16'sd32767: 
    (shifted < -32768)? -16'sd32768: shifted[15:0]; // saturation
    always@(posedge clk) begin
    out_valid <= 1'b0 ;
    if(rst) begin 
    state <= S_IDLE; 
    k<=0 ; wptr <= 0; out<= 0; acc<= 0; cnt<=0 ; ridx <=0 ;
    end else begin
    case (state)
    S_IDLE: if(in_valid) begin
    ring_buf [wptr] <= x_in ;
    ridx <= wptr ;
    wptr <= (wptr == N-1)? 0: wptr +1;
    if(cnt != N) cnt = cnt + 1;
    k <= 0; 
    acc <= 0; 
    state <= S_MAC; 
    end
    S_MAC: begin 
    if(k < cnt + 1) begin 
    acc <= acc + prod ;
    end
    ridx <= (ridx ==0)? N-1: ridx - 1;
    if ( k == N) begin 
    state<= S_DONE;    
    end else begin k <= k+ 1 ; end
    end
    S_DONE: begin 
    out <= sat ;
    out_valid <= 1'b1; 
    state <= S_IDLE;
    end
    default: state <= S_IDLE;
    endcase
    
    end
    end
    
endmodule
