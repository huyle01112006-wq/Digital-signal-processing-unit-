`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 27.10.2026 12:34:51
// Design Name: 
// Module Name: audio_quality_tb
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


module audio_equalizer_top #(
    parameter N            = 255,
    parameter GAIN_FRAC    = 8,
    parameter COEFF_BASS   = "coeff_bass.mem",
    parameter COEFF_MID    = "coeff_mid.mem",
    parameter COEFF_TREBLE = "coeff_treble.mem"
)(
    input  wire                clk,
    input  wire                rst,
    input  wire                in_valid,
    input  wire signed [15:0]  x_in,
    input  wire signed [15:0]  gain_bass,
    input  wire signed [15:0]  gain_mid,
    input  wire signed [15:0]  gain_treble,
    output wire                out_valid,
    output wire signed [15:0]  out
);
    wire f_vb, f_vm, f_vt;
    wire signed [15:0] f_b, f_m, f_t;

    filter_control #(.N(N), .COEFF_FILE(COEFF_BASS))   u_filter_bass
        (.clk(clk), .rst(rst), .in_valid(in_valid), .x_in(x_in), .out_valid(f_vb), .out(f_b));
    filter_control #(.N(N), .COEFF_FILE(COEFF_MID))    u_filter_mid
        (.clk(clk), .rst(rst), .in_valid(in_valid), .x_in(x_in), .out_valid(f_vm), .out(f_m));
    filter_control #(.N(N), .COEFF_FILE(COEFF_TREBLE)) u_filter_treble
        (.clk(clk), .rst(rst), .in_valid(in_valid), .x_in(x_in), .out_valid(f_vt), .out(f_t));

    // ---- 3 khoi Gain: dau vao la NGO RA BO LOC (f_*), khong phai x_in ----
    wire g_vb, g_vm, g_vt;
    wire signed [15:0] g_b, g_m, g_t;

    gain_control #(.GAIN_FRAC(GAIN_FRAC)) u_gain_bass
        (.clk(clk), .rst(rst), .in_valid(f_vb), .x_in(f_b), .gain_q(gain_bass),   .out_valid(g_vb), .out(g_b));
    gain_control #(.GAIN_FRAC(GAIN_FRAC)) u_gain_mid
        (.clk(clk), .rst(rst), .in_valid(f_vm), .x_in(f_m), .gain_q(gain_mid),    .out_valid(g_vm), .out(g_m));
    gain_control #(.GAIN_FRAC(GAIN_FRAC)) u_gain_treble
        (.clk(clk), .rst(rst), .in_valid(f_vt), .x_in(f_t), .gain_q(gain_treble), .out_valid(g_vt), .out(g_t));
    audio_mixer u_mixer
        (.clk(clk), .rst(rst), .a_in(g_b), .b_in(g_m), .c_in(g_t),
         .in_valid(g_vb), .out_valid(out_valid), .out(out));
endmodule