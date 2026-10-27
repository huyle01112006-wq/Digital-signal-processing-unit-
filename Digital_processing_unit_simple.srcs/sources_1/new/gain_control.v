`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 27.10.2026 04:25:25
// Design Name: 
// Module Name: gain_control
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
// gain_frac = 8

module gain_control#(
parameter GAIN_FRAC = 8
)(
input wire clk ,
input wire rst ,
input wire signed [15:0] x_in ,
input wire in_valid ,
input wire signed [15:0] gain_q ,
output reg out_valid ,
output reg signed [15:0] out
    );
wire signed [31:0] prod = x_in * gain_q ;
wire signed [32:0] sh = prod >>> GAIN_FRAC; 
wire signed [15:0] sat = (sh > 32767)? 32'sd32767: ( sh < - 32768) ? -32'sd32768: sh[15:0];
always @(posedge clk) begin 

if(rst) begin 
out <= 16'sd0 ; 
out_valid <= 1'b0 ; 
end else begin
if(in_valid) out <= sat ; 
out_valid <= in_valid;
end
end
endmodule
