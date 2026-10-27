`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 27.10.2026 04:53:20
// Design Name: 
// Module Name: audio_mixer
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


module audio_mixer(
input wire clk ,
input wire rst ,
input wire [15:0] a_in,
input wire [15:0] b_in,
input wire [15:0] c_in,
input wire in_valid ,
output reg signed [15:0] out ,
output reg out_valid
    );
    wire signed [17:0] a_e = {{2{a_in[15]}}, a_in};
    wire signed [17:0] b_e = {{2{b_in[15]}}, b_in};
    wire signed [17:0] c_e = {{2{c_in[15]}}, c_in};
    wire signed [17:0] sum = a_e + b_e + c_e ;
    wire signed [15:0] sat = (sum > 18'sd 32767)? 16'sd32767: (sum < -18'sd 32768)? -32'sd32768: sum[15:0] ;
    always @(posedge clk) begin 
    if(rst) begin 
    out_valid <= 16'sd0 ; 
    out <= 1'b0 ; 
    end else begin 
    if(in_valid) out <= sat ; 
    out_valid <= in_valid ;    
    end
    end
endmodule
